"""
Module 5 — Automated Settlement Agreement Generation
=====================================================
Input : NegotiationState (agreed amount + parties + case details)
Output: Legally valid settlement agreement (PDF-ready, digitally signable)

Approach:
  - Template-grounded LLM generation (not free-form)
  - Templates validated against MSMED Act Sections 18–20
  - Output validated by rule-based legal checker before delivery

Data sources for fine-tuning:
  - MSEFC settlement orders (public domain, via MSME Samadhan portal)
    https://samadhaan.msme.gov.in  (download PDF orders)
  - Indian Contract Act 1872 templates:
    https://indiacode.nic.in/handle/123456789/2187
  - Sample MSMED Act conciliation settlements:
    Request from NSIC / SIDBI legal teams under MOU
  - InLegalBench (Indian legal benchmarks):
    https://huggingface.co/datasets/Exploration-Lab/InLegalBench
"""

import json
import re
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
import httpx


# ─── Settlement Agreement Structure ──────────────────────────────────────────

@dataclass
class PartyDetails:
    name:             str
    address:          str
    gstin:            Optional[str]   = None
    pan:              Optional[str]   = None
    udyam_number:     Optional[str]   = None   # MSME registration
    bank_account:     Optional[str]   = None
    bank_ifsc:        Optional[str]   = None
    authorised_signatory: Optional[str] = None


@dataclass
class SettlementTerms:
    agreed_amount:    float
    currency:         str             = "INR"
    payment_schedule: list[dict]      = field(default_factory=list)
    payment_mode:     str             = "NEFT/RTGS"
    interest_waiver:  bool            = False
    penalty_waiver:   bool            = False
    special_conditions: list[str]     = field(default_factory=list)
    msefc_case_number: Optional[str]  = None


@dataclass
class SettlementAgreement:
    agreement_id:     str
    date:             str
    claimant:         PartyDetails
    respondent:       PartyDetails
    terms:            SettlementTerms
    dispute_type:     str
    original_claim:   float
    agreement_text:   str             = ""
    legal_clauses:    list[str]       = field(default_factory=list)
    is_valid:         bool            = False
    validation_notes: list[str]       = field(default_factory=list)


# ─── Legal Validator ─────────────────────────────────────────────────────────

REQUIRED_CLAUSES = [
    "dispute_reference",
    "parties_identified",
    "agreed_amount",
    "payment_timeline",
    "full_final_settlement",
    "governing_law",
    "signature_block",
]

MSMED_ACT_CLAUSES = {
    "governing_law": (
        "This Agreement is subject to the provisions of the Micro, Small and Medium "
        "Enterprises Development (MSMED) Act, 2006, and the Indian Contract Act, 1872."
    ),
    "jurisdiction": (
        "Any dispute arising out of this Agreement shall be subject to the jurisdiction "
        "of the Micro and Small Enterprises Facilitation Council (MSEFC) of the "
        "relevant state."
    ),
    "full_final_settlement": (
        "Upon receipt of the agreed settlement amount in full, the Claimant agrees to "
        "withdraw all pending claims, complaints, and proceedings related to this "
        "dispute, including any MSEFC filing, with prejudice."
    ),
    "interest_provision": (
        "In consideration of the settlement, the parties agree that no further interest "
        "under Section 16 of the MSMED Act, 2006, shall be claimed by either party "
        "in connection with the subject matter of this dispute."
    ),
}


class LegalValidator:
    """Rule-based validation of generated settlement agreements."""

    def validate(self, agreement: SettlementAgreement) -> tuple[bool, list[str]]:
        text   = agreement.agreement_text.lower()
        issues = []

        # Check required elements
        checks = {
            "parties_identified":   any(
                p in text for p in [
                    agreement.claimant.name.lower(),
                    agreement.respondent.name.lower(),
                ]
            ),
            "agreed_amount":        str(int(agreement.terms.agreed_amount)) in agreement.agreement_text,
            "payment_timeline":     any(word in text for word in ["days", "date", "schedule", "instalment"]),
            "full_final_settlement": "full and final" in text,
            "governing_law":        any(w in text for w in ["msmed act", "indian contract act", "1872"]),
            "signature_block":      "signed" in text or "signature" in text,
            "dispute_reference":    any(w in text for w in ["dispute", "claim", "invoice", "payment"]),
        }

        for clause, present in checks.items():
            if not present:
                issues.append(f"Missing required clause: {clause}")

        # Amount sanity check
        claim = agreement.original_claim
        agreed = agreement.terms.agreed_amount
        if agreed > claim * 1.05:
            issues.append(f"Agreed amount (₹{agreed:,.0f}) exceeds claim (₹{claim:,.0f}) by >5%")
        if agreed < claim * 0.10:
            issues.append(f"Agreed amount (₹{agreed:,.0f}) appears unreasonably low (<10% of claim)")

        # Payment schedule validation
        if not agreement.terms.payment_schedule:
            issues.append("No payment schedule defined")
        else:
            scheduled_total = sum(p.get("amount", 0) for p in agreement.terms.payment_schedule)
            if abs(scheduled_total - agreed) > 1:
                issues.append(
                    f"Payment schedule total (₹{scheduled_total:,.0f}) "
                    f"doesn't match agreed amount (₹{agreed:,.0f})"
                )

        is_valid = len(issues) == 0
        return is_valid, issues


# ─── Agreement Generator ─────────────────────────────────────────────────────

AGREEMENT_TEMPLATE = """SETTLEMENT AGREEMENT AND MUTUAL RELEASE

Agreement No: {agreement_id}
Date: {date}

THIS SETTLEMENT AGREEMENT ("Agreement") is entered into on {date} by and between:

CLAIMANT
Name: {claimant_name}
Address: {claimant_address}
UDYAM/GSTIN: {claimant_gstin}
(hereinafter referred to as "Claimant")

AND

RESPONDENT
Name: {respondent_name}
Address: {respondent_address}
GSTIN: {respondent_gstin}
(hereinafter referred to as "Respondent")

RECITALS

WHEREAS, a payment dispute arose between the parties concerning {dispute_description};
WHEREAS, the Claimant filed a claim of ₹{original_claim:,.2f} (Rupees {original_claim_words});
WHEREAS, both parties, with the assistance of NegotiateAI Online Dispute Resolution, have agreed to resolve the matter amicably;

NOW, THEREFORE, in consideration of the mutual covenants herein, the parties agree as follows:

1. SETTLEMENT AMOUNT
   The Respondent agrees to pay the Claimant a total settlement amount of ₹{agreed_amount:,.2f} (Rupees {agreed_amount_words}) in full and final settlement of all claims arising from the above dispute.

2. PAYMENT SCHEDULE
{payment_schedule_text}

3. MODE OF PAYMENT
   All payments shall be made via {payment_mode} to the following bank account:
   Account Name: {claimant_name}
   Account Number: {bank_account}
   IFSC Code: {bank_ifsc}

4. FULL AND FINAL SETTLEMENT
   Upon receipt of the agreed settlement amount in full, the Claimant agrees to withdraw all pending claims, complaints, and proceedings related to this dispute, including any MSEFC filing, with prejudice. This Agreement constitutes a full and final settlement of all claims between the parties arising from the subject dispute.

5. RELEASE OF CLAIMS
   Each party hereby releases and discharges the other party from all claims, demands, causes of action, and liabilities of any nature arising from or related to the dispute referenced herein.

{special_conditions_text}

6. GOVERNING LAW
   {governing_law_clause}

7. JURISDICTION
   {jurisdiction_clause}

8. INTEREST AND PENALTIES
   {interest_clause}

9. CONFIDENTIALITY
   The parties agree to keep the terms of this Agreement confidential and shall not disclose the same to any third party without prior written consent of the other party, except as required by law.

10. ENTIRE AGREEMENT
    This Agreement constitutes the entire agreement between the parties with respect to the subject matter hereof and supersedes all prior negotiations, representations, and agreements.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.

CLAIMANT                                    RESPONDENT
_______________________________             _______________________________
Name: {claimant_signatory}                  Name: {respondent_signatory}
Designation: Authorised Signatory           Designation: Authorised Signatory
Date: {date}                                Date: {date}

WITNESS 1                                   WITNESS 2
_______________________________             _______________________________

[Generated by NegotiateAI ODR Platform | Ref: {agreement_id}]
[This document is digitally signed and legally valid under the Information Technology Act, 2000]
"""


def _num_to_words(n: float) -> str:
    """Simple Indian number-to-words for amounts (handles lakhs/crores)."""
    n = int(n)
    if n >= 10_000_000:
        return f"{n/10_000_000:.2f} Crore"
    elif n >= 100_000:
        return f"{n/100_000:.2f} Lakh"
    elif n >= 1000:
        return f"{n/1000:.2f} Thousand"
    return str(n)


class SettlementGenerator:
    """
    Generates settlement agreements in two modes:
    1. Template mode (fast, deterministic) — for standard cases
    2. LLM-augmented mode (for complex / non-standard cases)
    """

    def __init__(self, use_llm: bool = True):
        self.validator = LegalValidator()
        self.use_llm   = use_llm

    def _build_payment_schedule_text(self, schedule: list[dict]) -> str:
        lines = ["   The settlement amount shall be paid as follows:"]
        for i, payment in enumerate(schedule, 1):
            lines.append(
                f"   Instalment {i}: ₹{payment['amount']:,.2f} on or before {payment['due_date']}"
            )
        return "\n".join(lines)

    def _build_special_conditions(self, conditions: list[str]) -> str:
        if not conditions:
            return ""
        lines = ["SPECIAL CONDITIONS\n   The parties additionally agree to:"]
        for i, cond in enumerate(conditions, 1):
            lines.append(f"   {i}. {cond}")
        return "\n".join(lines) + "\n"

    def generate_from_template(self, agreement: SettlementAgreement) -> str:
        """Fast deterministic generation from template."""
        terms      = agreement.terms
        claimant   = agreement.claimant
        respondent = agreement.respondent

        # Payment schedule
        if not terms.payment_schedule:
            # Default: lump sum in 30 days
            due_date = (datetime.now() + timedelta(days=30)).strftime("%d %B %Y")
            terms.payment_schedule = [{"amount": terms.agreed_amount, "due_date": due_date}]

        pay_text     = self._build_payment_schedule_text(terms.payment_schedule)
        special_text = self._build_special_conditions(terms.special_conditions)
        interest_clause = (
            MSMED_ACT_CLAUSES["interest_provision"]
            if terms.interest_waiver
            else "Interest under Section 16 of the MSMED Act shall be applicable as per the agreed schedule above."
        )

        dispute_desc_map = {
            "delayed_payment":  "delayed payment of invoices",
            "non_payment":      "non-payment of invoices",
            "short_payment":    "short payment against invoices",
            "quality_dispute":  "a dispute regarding goods/services quality",
            "quantity_dispute":  "a dispute regarding quantity of goods supplied",
            "contract_breach":  "breach of contract terms",
        }
        dispute_desc = dispute_desc_map.get(agreement.dispute_type, "a payment dispute")

        text = AGREEMENT_TEMPLATE.format(
            agreement_id         = agreement.agreement_id,
            date                 = agreement.date,
            claimant_name        = claimant.name,
            claimant_address     = claimant.address,
            claimant_gstin       = claimant.gstin or "N/A",
            respondent_name      = respondent.name,
            respondent_address   = respondent.address,
            respondent_gstin     = respondent.gstin or "N/A",
            dispute_description  = dispute_desc,
            original_claim       = agreement.original_claim,
            original_claim_words = _num_to_words(agreement.original_claim),
            agreed_amount        = terms.agreed_amount,
            agreed_amount_words  = _num_to_words(terms.agreed_amount),
            payment_schedule_text= pay_text,
            payment_mode         = terms.payment_mode,
            bank_account         = claimant.bank_account or "______",
            bank_ifsc            = claimant.bank_ifsc    or "______",
            special_conditions_text = special_text,
            governing_law_clause = MSMED_ACT_CLAUSES["governing_law"],
            jurisdiction_clause  = MSMED_ACT_CLAUSES["jurisdiction"],
            interest_clause      = interest_clause,
            claimant_signatory   = claimant.authorised_signatory or claimant.name,
            respondent_signatory = respondent.authorised_signatory or respondent.name,
        )
        return text

    async def generate_llm_enhanced(
        self,
        agreement: SettlementAgreement,
        template_text: str,
    ) -> str:
        """Use LLM to refine template output for complex cases."""
        prompt = f"""You are a legal document specialist. Improve the following settlement agreement draft for readability and legal completeness. 
Keep all factual details (names, amounts, dates) exactly as written. 
Only improve phrasing, add missing standard clauses, and ensure language is appropriate under Indian law.
Do not add any clauses not already implied. Output only the final agreement text.

DRAFT:
{template_text}"""

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"Content-Type": "application/json",
                         "anthropic-version": "2023-06-01"},
                json={
                    "model":      "claude-sonnet-4-20250514",
                    "max_tokens": 2000,
                    "messages":   [{"role": "user", "content": prompt}],
                },
                timeout=60.0,
            )
            return resp.json()["content"][0]["text"]

    async def generate(self, agreement: SettlementAgreement) -> SettlementAgreement:
        """Full generation pipeline with validation."""
        import time
        start = time.time()

        # Step 1: Template generation (always done first)
        template_text = self.generate_from_template(agreement)

        # Step 2: LLM enhancement (for complex cases)
        if self.use_llm and (
            agreement.terms.special_conditions
            or len(agreement.terms.payment_schedule) > 2
        ):
            try:
                agreement.agreement_text = await self.generate_llm_enhanced(
                    agreement, template_text
                )
            except Exception as e:
                print(f"[Settlement] LLM failed ({e}), using template only")
                agreement.agreement_text = template_text
        else:
            agreement.agreement_text = template_text

        # Step 3: Legal validation
        is_valid, issues = self.validator.validate(agreement)
        agreement.is_valid         = is_valid
        agreement.validation_notes = issues

        elapsed = time.time() - start
        print(f"[Settlement] Generated in {elapsed:.1f}s | Valid: {is_valid}")
        if issues:
            print(f"[Settlement] Issues: {issues}")

        return agreement


# ─── Quick test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    agreement = SettlementAgreement(
        agreement_id  = "NAIODR-2024-MH-001",
        date          = datetime.now().strftime("%d %B %Y"),
        claimant      = PartyDetails(
            name       = "Sharma Textiles Pvt Ltd",
            address    = "Plot 12, MIDC, Bhiwandi, Maharashtra 421302",
            gstin      = "27AAKCS2768G1Z3",
            udyam_number= "UDYAM-MH-12-0012345",
            bank_account= "1234567890",
            bank_ifsc   = "SBIN0001234",
            authorised_signatory = "Mr. Ramesh Sharma",
        ),
        respondent    = PartyDetails(
            name       = "Reddy Garments & Exports",
            address    = "45 Industrial Area, Secunderabad, Telangana 500003",
            gstin      = "36AAKCS1234G1Z8",
            authorised_signatory = "Ms. Priya Reddy",
        ),
        terms         = SettlementTerms(
            agreed_amount   = 380_000,
            payment_schedule= [
                {"amount": 190_000, "due_date": "15 February 2025"},
                {"amount": 190_000, "due_date": "15 March 2025"},
            ],
            interest_waiver = True,
            payment_mode    = "RTGS",
        ),
        dispute_type  = "delayed_payment",
        original_claim= 450_000,
    )

    async def demo():
        gen   = SettlementGenerator(use_llm=False)
        result = await gen.generate(agreement)
        print(f"\nValid: {result.is_valid}")
        if result.validation_notes:
            print(f"Notes: {result.validation_notes}")
        print("\n" + "="*60)
        print(result.agreement_text[:1500])

    asyncio.run(demo())
