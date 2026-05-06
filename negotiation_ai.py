"""
Module 4 — Real-Time Multilingual Negotiation AI
=================================================
Components:
  - RoBERTa sentiment analyser (detects deadlock / hostility in real time)
  - Game-theoretic bargaining strategy engine (Nash / Rubinstein framework)
  - LLM negotiation moderator (LLaMA/Mistral with RAG over legal corpus)
  - IndicTrans2 real-time translation

Data sources for fine-tuning:
  - MultiWOZ 2.4 negotiation dialogues:   https://huggingface.co/datasets/multi_woz_v22
  - CraigslistBargain dataset:            https://huggingface.co/datasets/craigslist_bargains
  - Indian legal dialogue corpus:         https://github.com/Legal-NLP-EkStep
  - IndicCorp v2 (for translation):       https://ai4bharat.org/indiccorp
  - GoEmotions (sentiment pre-training):  https://huggingface.co/datasets/go_emotions
"""

import json
import time
import math
import asyncio
from dataclasses import dataclass, field, asdict
from typing import Optional, AsyncGenerator
from enum import Enum
from transformers import (
    pipeline as hf_pipeline,
    AutoTokenizer,
    AutoModelForCausalLM,
)
import torch


# ─── Types ───────────────────────────────────────────────────────────────────

class Party(Enum):
    CLAIMANT   = "claimant"
    RESPONDENT = "respondent"
    MEDIATOR   = "mediator"


class NegotiationPhase(Enum):
    OPENING    = "opening"
    ANCHORING  = "anchoring"
    BARGAINING = "bargaining"
    CLOSING    = "closing"
    DEADLOCK   = "deadlock"
    AGREEMENT  = "agreement"


class SentimentLabel(Enum):
    COOPERATIVE  = "cooperative"
    NEUTRAL      = "neutral"
    FRUSTRATED   = "frustrated"
    HOSTILE      = "hostile"
    CONCILIATORY = "conciliatory"


@dataclass
class Message:
    party:      Party
    text:       str
    language:   str
    timestamp:  float
    sentiment:  Optional[SentimentLabel] = None
    offer:      Optional[float]          = None   # INR amount if this is an offer


@dataclass
class NegotiationState:
    case_id:             str
    claim_amount:        float
    predicted_range:     tuple[float, float]
    settlement_probability: float

    phase:               NegotiationPhase = NegotiationPhase.OPENING
    round_number:        int              = 0
    last_claimant_offer: Optional[float]  = None
    last_respondent_offer: Optional[float]= None
    deadlock_streak:     int              = 0
    agreement_amount:    Optional[float]  = None
    messages:            list[Message]    = field(default_factory=list)
    strategy:            str              = "cooperative"   # "cooperative" | "firm" | "concessive"

    def zopa_exists(self) -> bool:
        """Zone of Possible Agreement: claimant willing to go lower than respondent's offer."""
        if self.last_claimant_offer and self.last_respondent_offer:
            return self.last_respondent_offer >= self.last_claimant_offer
        return False


# ─── Sentiment Analyser ───────────────────────────────────────────────────────

class NegotiationSentimentAnalyser:
    """
    Fine-tuned RoBERTa for negotiation-specific sentiment.
    Labels: cooperative, neutral, frustrated, hostile, conciliatory

    Base model: cardiffnlp/twitter-roberta-base-sentiment
    Fine-tune on: CraigslistBargain + MultiWOZ + GoEmotions
    Training: ~8000 annotated negotiation turns
    """

    # Keyword heuristics (fallback when model not available)
    SENTIMENT_KEYWORDS = {
        SentimentLabel.HOSTILE:      ["refuse", "unacceptable", "ridiculous", "fraud",
                                       "cheating", "absurd", "never", "lawsuit"],
        SentimentLabel.FRUSTRATED:   ["disappointed", "unfair", "unreasonable",
                                       "delays", "ignored", "waiting", "already paid"],
        SentimentLabel.CONCILIATORY: ["understand", "willing", "compromise", "fair",
                                       "flexible", "consider", "appreciate", "agree"],
        SentimentLabel.COOPERATIVE:  ["happy to", "certainly", "of course", "yes",
                                       "absolutely", "great", "thank you", "resolve"],
    }

    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment"):
        try:
            self.pipe = hf_pipeline(
                "text-classification",
                model=model_name,
                device=0 if torch.cuda.is_available() else -1,
            )
            self.use_model = True
        except Exception:
            print("[Sentiment] Model not loaded — using keyword heuristic")
            self.use_model = False

    def analyse(self, text: str) -> tuple[SentimentLabel, float]:
        text_lower = text.lower()

        # Keyword scoring (always computed as fallback/override)
        keyword_scores = {}
        for label, keywords in self.SENTIMENT_KEYWORDS.items():
            keyword_scores[label] = sum(1 for kw in keywords if kw in text_lower)

        if self.use_model:
            try:
                result = self.pipe(text[:512])[0]
                label  = result["label"]
                score  = result["score"]
                # Map model output to our labels
                if label == "LABEL_2" and score > 0.7:    # positive
                    return SentimentLabel.COOPERATIVE, score
                elif label == "LABEL_0" and score > 0.7:  # negative
                    return SentimentLabel.HOSTILE, score
                else:
                    return SentimentLabel.NEUTRAL, score
            except Exception:
                pass

        # Keyword fallback
        if not any(keyword_scores.values()):
            return SentimentLabel.NEUTRAL, 0.5

        best = max(keyword_scores, key=keyword_scores.get)
        total = sum(keyword_scores.values()) or 1
        return best, keyword_scores[best] / total

    def is_deadlock(self, recent_sentiments: list[SentimentLabel]) -> bool:
        """Deadlock if 3+ consecutive hostile/frustrated signals."""
        if len(recent_sentiments) < 3:
            return False
        last3 = recent_sentiments[-3:]
        return all(s in (SentimentLabel.HOSTILE, SentimentLabel.FRUSTRATED)
                   for s in last3)


# ─── Game-Theoretic Strategy Engine ──────────────────────────────────────────

class BargainingStrategyEngine:
    """
    Implements Rubinstein Alternating Offers + Nash Bargaining Solution.

    Theory:
    - Nash Bargaining: maximise (u_claimant - d_c) * (u_respondent - d_r)
      where d = disagreement payoff (BATNA)
    - Rubinstein: with patience factors δ_c, δ_r, equilibrium offer is:
        claimant offer  = (1 - δ_r) / (1 - δ_c * δ_r) * surplus
        respondent share= δ_c * (1 - δ_r) / (1 - δ_c * δ_r) * surplus
    """

    def __init__(self):
        # Patience factors (0=impatient, 1=infinitely patient)
        # In MSME context: larger claimants more patient (more resources)
        self.PATIENCE = {
            "micro":  0.70,
            "small":  0.78,
            "medium": 0.85,
            "large":  0.90,
        }

    def nash_solution(
        self,
        claim_amount:       float,
        claimant_batna:     float,   # Best Alternative To Negotiated Agreement
        respondent_batna:   float,   # BATNA for respondent (cost of litigation)
        surplus_range:      tuple[float, float],
    ) -> float:
        """Nash Bargaining Solution — maximises product of surplus gains."""
        low, high = surplus_range
        # Discretise and compute Nash product
        best_val  = -np.inf if False else float("-inf")
        best_offer = low
        for candidate in [low + (high - low) * t / 100 for t in range(101)]:
            claimant_gain   = candidate - claimant_batna
            respondent_gain = (claim_amount - candidate) - respondent_batna
            if claimant_gain > 0 and respondent_gain > 0:
                nash_product = math.log(claimant_gain) + math.log(respondent_gain)
                if nash_product > best_val:
                    best_val  = nash_product
                    best_offer = candidate
        return best_offer

    def rubinstein_offer(
        self,
        total_surplus:      float,
        proposer_size:      str,
        responder_size:     str,
        round_number:       int,
    ) -> float:
        """
        Rubinstein alternating offers equilibrium.
        Returns the share the proposer should ask for.
        """
        delta_p = self.PATIENCE.get(proposer_size, 0.75)
        delta_r = self.PATIENCE.get(responder_size, 0.75)

        # Equilibrium share for proposer
        share = (1 - delta_r) / (1 - delta_p * delta_r)
        # Decrease slightly each round (time pressure / impatience)
        discount = delta_p ** round_number
        return total_surplus * share * discount

    def compute_counteroffers(
        self,
        state:              NegotiationState,
        claimant_size:      str = "micro",
        respondent_size:    str = "medium",
    ) -> dict:
        """
        Returns recommended offers/moves for the mediator to suggest.
        """
        claim   = state.claim_amount
        p_low, p_high = state.predicted_range

        # BATNAs: cost of going to court
        claimant_batna   = p_low * 0.6   # expect 60% recovery via MSEFC
        respondent_batna = p_high * 1.2  # litigation costs 20% premium

        nash = self.nash_solution(claim, claimant_batna, respondent_batna, (p_low, p_high))

        # Rubinstein offer from claimant perspective
        surplus = p_high - p_low
        r_offer = self.rubinstein_offer(
            surplus, claimant_size, respondent_size, state.round_number
        )
        claimant_target   = p_low + r_offer
        respondent_target = p_high - r_offer * 0.5

        return {
            "nash_solution":       round(nash, 2),
            "suggested_claimant_ask":   round(min(claimant_target, claim), 2),
            "suggested_respondent_bid": round(max(respondent_target, p_low * 0.7), 2),
            "midpoint":                round((claimant_target + respondent_target) / 2, 2),
        }


# ─── LLM Negotiation Moderator ───────────────────────────────────────────────

SYSTEM_PROMPT = """You are NegotiateAI — an impartial AI mediator specialising in Indian MSME payment disputes under the MSMED Act 2006. Your role is to:
1. Keep both parties calm and focused on resolution
2. Reframe positional statements into interest-based language
3. Suggest face-saving compromises when deadlock occurs
4. Cite relevant MSMED Act provisions (Sections 15–23) when helpful
5. Never take sides — remain strictly neutral
6. Keep responses concise (2–4 sentences maximum per turn)
7. If a party is hostile, acknowledge their frustration before redirecting

Current case context will be provided in each message."""


class NegotiationModerator:
    """
    LLM-powered negotiation moderator.

    Production: fine-tune Mistral-7B-Instruct on Indian legal negotiation dialogues
    Quick start: use via Anthropic API or Ollama locally

    Fine-tuning data: curate ~500 MSEFC-style negotiation transcripts
    with annotated mediator responses. Label: mediator_move ∈
    {reframe, validate, suggest_compromise, cite_law, summarise, close}
    """

    def __init__(self, use_api: bool = True):
        self.use_api = use_api
        if not use_api:
            # Local Mistral via Ollama (run: ollama pull mistral)
            self.model_name = "mistral"

    def _build_prompt(
        self,
        state: NegotiationState,
        last_message: Message,
        strategy_hints: dict,
        language: str = "en",
    ) -> str:
        history_text = "\n".join(
            f"[{m.party.value.upper()}]: {m.text}"
            for m in state.messages[-6:]  # last 6 turns
        )
        return f"""{SYSTEM_PROMPT}

=== CASE CONTEXT ===
Claim amount: ₹{state.claim_amount:,.0f}
Predicted settlement range: ₹{state.predicted_range[0]:,.0f} – ₹{state.predicted_range[1]:,.0f}
Nash optimal settlement: ₹{strategy_hints.get('nash_solution', 'N/A'):,.0f}
Phase: {state.phase.value}
Round: {state.round_number}

=== RECENT DIALOGUE ===
{history_text}

=== LAST MESSAGE ===
[{last_message.party.value.upper()}]: {last_message.text}
Sentiment detected: {last_message.sentiment.value if last_message.sentiment else 'neutral'}

=== YOUR TASK ===
Respond as the impartial mediator. Language: {language}.
If the conversation is in a language other than English, respond in that language.
Be brief (2–4 sentences). Do not reveal internal strategy hints to parties.
"""

    async def generate_response(
        self,
        state: NegotiationState,
        last_message: Message,
        strategy_hints: dict,
        language: str = "en",
    ) -> str:
        prompt = self._build_prompt(state, last_message, strategy_hints, language)

        if self.use_api:
            return await self._call_anthropic_api(prompt)
        else:
            return await self._call_ollama(prompt)

    async def _call_anthropic_api(self, prompt: str) -> str:
        """Use Claude via API as negotiation moderator backbone."""
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model":      "claude-sonnet-4-20250514",
                    "max_tokens": 300,
                    "messages":   [{"role": "user", "content": prompt}],
                },
                timeout=15.0,
            )
            data = resp.json()
            return data["content"][0]["text"]

    async def _call_ollama(self, prompt: str) -> str:
        """Local Mistral via Ollama."""
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://localhost:11434/api/generate",
                json={"model": self.model_name, "prompt": prompt, "stream": False},
                timeout=30.0,
            )
            return resp.json()["response"]


# ─── Main Negotiation Session ─────────────────────────────────────────────────

class NegotiationSession:
    """
    Orchestrates a full negotiation session.
    Call process_message() for each party turn.
    """

    def __init__(self, state: NegotiationState, language: str = "en"):
        self.state      = state
        self.language   = language
        self.sentiment  = NegotiationSentimentAnalyser()
        self.strategy   = BargainingStrategyEngine()
        self.moderator  = NegotiationModerator(use_api=True)

    async def process_message(
        self,
        party:      Party,
        text:       str,
        offer:      Optional[float] = None,
    ) -> dict:
        """Process one party's message. Returns mediator response + state update."""

        # 1. Sentiment analysis
        sentiment_label, sentiment_conf = self.sentiment.analyse(text)

        msg = Message(
            party     = party,
            text      = text,
            language  = self.language,
            timestamp = time.time(),
            sentiment = sentiment_label,
            offer     = offer,
        )
        self.state.messages.append(msg)

        # 2. Update offers
        if offer:
            if party == Party.CLAIMANT:
                self.state.last_claimant_offer   = offer
            else:
                self.state.last_respondent_offer = offer

        # 3. Deadlock detection
        recent_sentiments = [
            m.sentiment for m in self.state.messages[-4:]
            if m.sentiment is not None
        ]
        if self.sentiment.is_deadlock(recent_sentiments):
            self.state.phase          = NegotiationPhase.DEADLOCK
            self.state.deadlock_streak += 1
        else:
            self.state.deadlock_streak = 0

        # 4. Check for ZOPA (agreement zone)
        if self.state.zopa_exists():
            self.state.phase = NegotiationPhase.AGREEMENT
            self.state.agreement_amount = (
                (self.state.last_claimant_offer + self.state.last_respondent_offer) / 2
            )

        # 5. Strategy hints from game theory
        strategy_hints = self.strategy.compute_counteroffers(self.state)

        # 6. Adapt mediator strategy
        if self.state.deadlock_streak >= 2:
            strategy_hints["mediator_move"] = "suggest_mediator_proposal"
        elif sentiment_label == SentimentLabel.HOSTILE:
            strategy_hints["mediator_move"] = "de-escalate"
        elif self.state.phase == NegotiationPhase.AGREEMENT:
            strategy_hints["mediator_move"] = "close"
        else:
            strategy_hints["mediator_move"] = "facilitate"

        # 7. Generate moderator response
        self.state.round_number += 1
        mediator_text = await self.moderator.generate_response(
            self.state, msg, strategy_hints, self.language
        )

        return {
            "mediator_response":    mediator_text,
            "sentiment_detected":   sentiment_label.value,
            "phase":                self.state.phase.value,
            "round":                self.state.round_number,
            "strategy_hints":       strategy_hints,
            "agreement_reached":    self.state.phase == NegotiationPhase.AGREEMENT,
            "agreement_amount":     self.state.agreement_amount,
        }


# ─── Quick test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    state = NegotiationState(
        case_id              = "MSEFC-2024-001",
        claim_amount         = 450_000,
        predicted_range      = (300_000, 420_000),
        settlement_probability = 0.72,
    )
    session = NegotiationSession(state, language="en")

    async def demo():
        # Simulate a short negotiation
        turns = [
            (Party.CLAIMANT,   "We are owed ₹4,50,000 for 120 days. This is completely unacceptable.",   450_000),
            (Party.RESPONDENT, "There were quality issues with the delivery. We can only offer ₹2,50,000.", 250_000),
            (Party.CLAIMANT,   "Quality issues? Everything was delivered as per PO. I want full payment.",  430_000),
            (Party.RESPONDENT, "We can consider ₹3,20,000 if you acknowledge the delay.",                  320_000),
        ]
        for party, text, offer in turns:
            result = await session.process_message(party, text, offer)
            print(f"\n[{party.value.upper()}]: {text}")
            print(f"[MEDIATOR]: {result['mediator_response']}")
            print(f"  Phase: {result['phase']} | Sentiment: {result['sentiment_detected']}")
            if result["agreement_reached"]:
                print(f"  ✓ Agreement at ₹{result['agreement_amount']:,.0f}")
                break

    asyncio.run(demo())
