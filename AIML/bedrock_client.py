"""
NegotiateAI — AWS Bedrock client (Nova Micro default).

Single place for all Bedrock calls: negotiation mediator, document
review, settlement explainer. Model ID lives in api.config so swapping
to Claude Haiku 4.5 later is one env change.

Identity hiding: every system prompt declares the assistant as
"NegotiateAI mediator" and refuses model disclosure; _scrub() strips
any provider/model leak from raw output before it reaches clients.
"""
import json
import re
import threading

from api.config import settings


_client = None
_client_lock = threading.Lock()

# Exact reply when a user asks "what model are you".
IDENTITY_REFUSAL = "I can't disclose that for security reasons."

IDENTITY_RULE = (
    "You are the NegotiateAI mediator, an AI assistant inside the NegotiateAI "
    "MSME dispute-resolution platform. "
    "If asked what model you are, who made you, or about your underlying "
    f"model/provider, reply exactly: \"{IDENTITY_REFUSAL}\" "
    "Do not mention Nova, Claude, Anthropic, Amazon, Bedrock, or any model name."
)

# Belt-and-braces: strip leaks even if the model ignores the instruction.
_LEAK_RE = re.compile(
    r"\b(nova(?:\s*micro)?|claude(?:\s*[\d.]*)?(?:\s*haiku|\s*sonnet)?"
    r"|anthropic|amazon\s*bedrock|bedrock|titan|llama|mistral|qwen)\b",
    re.IGNORECASE,
)


def _scrub(text: str) -> str:
    """Replace provider/model mentions with neutral wording."""
    if not text:
        return text
    return _LEAK_RE.sub("the AI mediator", text)


def get_client():
    """Process-wide boto3 bedrock-runtime client (lazy, thread-safe)."""
    global _client
    if _client is not None:
        return _client
    with _client_lock:
        if _client is not None:
            return _client
        import boto3

        region = getattr(settings, "AWS_REGION_BEDROCK", "us-east-1") or "us-east-1"
        _client = boto3.client("bedrock-runtime", region_name=region)
        return _client


def is_enabled() -> bool:
    """True when Bedrock is configured (env USE_BEDROCK=true)."""
    return bool(getattr(settings, "USE_BEDROCK", False))


def converse(
    user_text: str,
    system: str = "",
    model: str = "",
    max_tokens: int = 0,
    temperature: float = 0.3,
) -> str:
    """One Bedrock converse call. Returns scrubbed text. Raises on failure."""
    model = model or getattr(settings, "BEDROCK_MEDIATOR_MODEL", "amazon.nova-micro-v1:0")
    max_tokens = max_tokens or int(getattr(settings, "BEDROCK_MAX_TOKENS", 400) or 400)
    full_system = f"{IDENTITY_RULE}\n\n{system}" if system else IDENTITY_RULE
    resp = get_client().converse(
        modelId=model,
        system=[{"text": full_system}],
        messages=[{"role": "user", "content": [{"text": user_text}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
    )
    raw = resp["output"]["message"]["content"][0]["text"]
    return _scrub(raw).strip()


def review_document(ocr_text: str, filename: str = "") -> dict:
    """Classify + extract a document via Bedrock. Returns strict dict."""
    model = getattr(settings, "BEDROCK_DOC_MODEL", "") or getattr(
        settings, "BEDROCK_MEDIATOR_MODEL", "amazon.nova-micro-v1:0"
    )
    system = (
        "You are an MSME document reviewer under the MSMED Act 2006. "
        "Classify into one of: invoice, purchase_order, delivery_receipt, "
        "contract, payment_receipt, bank_statement, correspondence, other. "
        "Extract amount (INR), invoice number, dates, parties, GSTIN. "
        "Flag missing seal/signature, amount mismatch, unreadable text. "
        "Return STRICT JSON only: "
        '{"doc_type": ..., "confidence": 0.0-1.0, "amount": number|null, '
        '"invoice_number": str|null, "dates": [], "parties": [], '
        '"is_valid": bool, "issues": [], "summary": "2-line summary"}. '
        f"{IDENTITY_RULE}"
    )
    raw = converse(
        f"Filename: {filename}\n\nOCR text:\n{ocr_text[:4000]}",
        system=system,
        model=model,
        max_tokens=600,
        temperature=0.1,
    )
    # Tolerate code fences around the JSON.
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return {
            "doc_type": "other",
            "confidence": 0.3,
            "amount": None,
            "invoice_number": None,
            "dates": [],
            "parties": [],
            "is_valid": False,
            "issues": ["Bedrock returned non-JSON output"],
            "summary": cleaned[:500],
            "_raw": cleaned[:1000],
        }
