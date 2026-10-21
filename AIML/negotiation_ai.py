"""
Module 4 — Real-Time Multilingual Negotiation AI
=================================================
Components:
  - RoBERTa sentiment analyser (detects deadlock / hostility in real time)
  - Game-theoretic bargaining strategy engine (Nash / Rubinstein framework)
  - LLM negotiation moderator (Qwen / local instruct model with RAG over legal corpus)

Data sources for fine-tuning:
  - MultiWOZ 2.4 negotiation dialogues:   https://huggingface.co/datasets/multi_woz_v22
  - CraigslistBargain dataset:            https://huggingface.co/datasets/craigslist_bargains
  - Indian legal dialogue corpus:         https://github.com/Legal-NLP-EkStep
  - IndicCorp v2 (for translation):       https://ai4bharat.org/indiccorp
  - GoEmotions (sentiment pre-training):  https://huggingface.co/datasets/go_emotions
"""

import json
import re
import time
import math
import asyncio
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Optional, AsyncGenerator
from enum import Enum

# Heavy imports (torch, transformers) are lazy — see
# NegotiationSentimentAnalyser.__init__ and _load_local_pipe() below.
# The Bedrock path (USE_BEDROCK=true) never loads them, so slim images
# without the ~2GB ML stack import and run this module fine.

from api.config import settings


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

    # ── Case-specific context (injected from DB) ──────────────────────────────
    description:         Optional[str]    = None   # voice transcript / case description
    dispute_type:        Optional[str]    = None   # e.g. "payment_delay"
    industry:            Optional[str]    = None   # e.g. "manufacturing"
    state:               Optional[str]    = None   # Indian state
    overdue_days:        Optional[int]    = None   # days payment is overdue
    claimant_name:       Optional[str]    = None
    respondent_name:     Optional[str]    = None
    document_summary:    Optional[str]    = None   # extracted text from uploaded docs

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
            from transformers import pipeline as hf_pipeline
            import torch

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
        best_val  = float("-inf")
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


# ─── Process-wide model singleton ─────────────────────────────────────────────
# The configured LLM checkpoint is loaded ONCE per process and shared by every
# NegotiationSession/case. Without this, each new case would re-load the whole
# model (1-2 min) on its first message.
import threading as _threading

_LOCAL_PIPE  = None
_PIPE_LOCK   = _threading.Lock()   # serialises generation
_LOAD_LOCK   = _threading.Lock()   # serialises loading (single-flight)
_PIPE_INFO: dict = {}


def _resolve_device_mode(torch) -> str:
    """'cuda' or 'cpu' — what LOCAL_MODEL_DEVICE asks for, minus wishful thinking."""
    mode = (getattr(settings, "LOCAL_MODEL_DEVICE", "auto") or "auto").strip().lower()
    if mode == "cpu":
        return "cpu"
    if mode == "cuda":
        if not torch.cuda.is_available():
            print("[Moderator] LOCAL_MODEL_DEVICE=cuda but CUDA is unavailable — using CPU.")
            return "cpu"
        return "cuda"
    return "cuda" if torch.cuda.is_available() else "cpu"


def _placement(model):
    """(blocks on GPU, blocks on CPU) from accelerate's placement map.

    accelerate records GPU placement as a bare int (0 for cuda:0) and offload as
    a string ("cpu" / "disk"), so both forms have to be understood — counting
    only "cuda*" strings reports every block as unplaced.
    """
    device_map = getattr(model, "hf_device_map", None)
    if not device_map:
        return (0, 0)
    gpu = cpu = 0
    for placement in device_map.values():
        if isinstance(placement, int) or str(placement).startswith("cuda"):
            gpu += 1
        elif str(placement) == "cpu":
            cpu += 1
    return (gpu, cpu)


def _max_new_tokens() -> int:
    """Per-turn generation cap (settings.LOCAL_MODEL_MAX_NEW_TOKENS)."""
    try:
        return max(32, int(getattr(settings, "LOCAL_MODEL_MAX_NEW_TOKENS", 128)))
    except (TypeError, ValueError):
        return 128


def _build_local_pipe():
    """Load the configured local model once per process (singleton).

    Default (LOCAL_MODEL_ID, e.g. Qwen2.5-1.5B-Instruct): a small standard
    instruct model that is fast on CPU. On CPU it is int8-dynamic-quantized
    (LOCAL_MODEL_QUANTIZE, default on) for ~2-3x faster inference and ~60%
    less memory; on CUDA it loads in fp16.

    Returns the cached pipeline (singleton — safe to call repeatedly).

    Blocking. Never call this from an async handler: use
    ensure_local_pipe_loaded() so a cold load cannot stall the event loop.
    """
    global _LOCAL_PIPE
    if _LOCAL_PIPE is not None:        # fast path — no lock contention
        return _LOCAL_PIPE

    # Single-flight. Without this, two messages arriving before the first load
    # finished each loaded a complete second copy of the model — two sets of
    # weights fighting for the same VRAM (which is what pushed the model onto
    # the CPU) and a duplicated "Some parameters are on the meta device..."
    # warning in the log.
    with _LOAD_LOCK:
        if _LOCAL_PIPE is not None:
            return _LOCAL_PIPE
        _LOCAL_PIPE = _load_local_pipe()
    return _LOCAL_PIPE


def _load_local_pipe():
    from transformers import AutoModelForCausalLM
    import torch

    model_id = (settings.LOCAL_MODEL_ID or "Qwen/Qwen2.5-1.5B-Instruct").strip()
    mode     = _resolve_device_mode(torch)
    on_gpu   = mode == "cuda"
    forced   = (getattr(settings, "LOCAL_MODEL_DEVICE", "auto") or "auto").strip().lower()
    print(f"[Moderator] Loading {model_id} ({mode})...")

    # device_map="auto": accelerate fills the GPU and spills whatever does not
    # fit to CPU rather than crashing. That keeps the mediator working when VRAM
    # is tight, but spilled layers are orders of magnitude slower — so report it
    # instead of letting a slow reply look like a hang. With
    # LOCAL_MODEL_DEVICE=cuda we ask for the GPU only: an outright OOM is much
    # easier to act on than a mystery slowdown.
    if on_gpu:
        free_gib   = round(torch.cuda.mem_get_info()[0] / (1024 ** 3), 1)
        device_map = "cuda:0" if forced == "cuda" else "auto"
        print(f"[Moderator] CUDA available — {free_gib} GiB free VRAM")
    else:
        device_map = None

    # bf16 on CPU unless we are about to int8-quantize. Two reasons:
    #   1. the oneDNN dynamic-int8 op requires float32 input, so quantizing a
    #      bf16 model raises "data type of input should be float";
    #   2. bf16 loads in ~3 GB vs ~6 GB for fp32 and (measured on this model)
    #      generates faster *and* in far better quality than int8.
    quantizing = (not on_gpu) and bool(settings.LOCAL_MODEL_QUANTIZE)
    if on_gpu:
        load_dtype, dtype_label = torch.float16, "fp16 on CUDA"
    elif quantizing:
        load_dtype, dtype_label = torch.float32, "fp32 on CPU (int8 to follow)"
    else:
        load_dtype, dtype_label = torch.bfloat16, "bf16 on CPU"
    print(f"[Moderator] Loading model weights ({dtype_label})...")
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map=device_map,
        # Always stream the weights: the legacy loader materialises the full
        # checkpoint at once, which on CPU peaked at ~9.2 GB for the 1.5B model
        # and OOM-killed the container before serving a single request.
        low_cpu_mem_usage=True,
        torch_dtype=load_dtype,
    )

    # ── int8 dynamic quantization (CPU only) ──────────────────────────────
    # Quantizes all nn.Linear layers to int8 at runtime: ~2-3x faster CPU
    # matmul and ~60% lower memory. Skipped on CUDA (fp16 already wins).
    if not on_gpu and settings.LOCAL_MODEL_QUANTIZE:
        print("[Moderator] Applying int8 dynamic quantization (CPU)...")
        model = torch.quantization.quantize_dynamic(
            model,
            {torch.nn.Linear},   # quantize all Linear layers
            dtype=torch.qint8,   # int8 weights
        )
        print("[Moderator] Quantization complete.")

    if on_gpu:
        n_gpu, n_cpu = _placement(model)
        if n_cpu:
            total = max(1, n_gpu + n_cpu)
            print(
                f"[Moderator] WARNING: {n_cpu}/{total} blocks ({round(100 * n_cpu / total)}%) "
                "were pushed to CPU because the model did not fit in VRAM. "
                "Replies will be slow. Free VRAM (close GPU-heavy apps such as "
                "browsers and game launchers), set LOCAL_MODEL_ID to a smaller "
                "model, or set LOCAL_MODEL_DEVICE=cpu for int8 on CPU."
            )
        else:
            print(f"[Moderator] All {n_gpu} blocks resident on GPU")

    from transformers import pipeline as _pipeline
    # Pass the tokenizer explicitly. Older transformers (<=4.46) cannot guess a
    # tokenizer from a model object and raise "Impossible to guess which
    # tokenizer to use", which would silently drop us to the rule-based path.
    pipe = _pipeline("text-generation", model=model, tokenizer=model_id)

    _PIPE_INFO.update({
        "model_id": model_id,
        "mode": mode,
        "max_new_tokens": _max_new_tokens(),
    })
    where = "int8-quantized CPU" if quantizing else \
            ("bf16 CPU" if not on_gpu else "CUDA")
    print(f"[Moderator] Model loaded successfully ({where}, max_new_tokens={_max_new_tokens()}).")
    return pipe


# Output shapes that mean the model has drifted off the mediator task and
# into scraped-web continuation. Every one of these was observed in real
# generations from the current prompt (e.g. "created with just one click at
# your own risk!", "khanacademy.com", "Error Code = kErrorLoadingVideo...").
_DEGENERATE_PATTERNS = [
    r"<\s*(br|/p|/div|p|div|span|/span|/a|a)\b",   # HTML markup
    r"https?://|www\.",                              # URLs
    r"&[a-z]+;|&#\d+;",                              # HTML entities
    r"=+ ?[><=]|<==|===>>",                           # ascii-art banners
    r"error\s*code\s*=|error\s*\d{3,}",              # error pages
    r"(click here|subscribe|unsubscribe|cookie|terms of service|privacy policy)",
    r"\b(support|info|sales)@[a-z0-9.-]+\b",          # scraped contact blocks
    r"khanacademy|youtube\.com|facebook\.com|twitter\.com|wordpress",
    r"please (try again later|contact (support|the admin))",
    # Web-form / forum boilerplate — observed verbatim in real generations.
    # These are plain English with no markup, so the patterns above miss them;
    # they are also far too specific to ever match a genuine mediator reply.
    r"spam filter|friendly neighborhood",
    r"submissions must contain|do not support anonymous",
    r"include all elements required|needs information including",
    r"do reply online|follow-up requests via",
    r"kindly do reply|contact you about your feedback",
    r"^(hi|hello|hey)[.!]?$",                         # non-answers
    r"^(sorry|apologies|i cannot|i can't|i'm sorry)\b.{0,10}$",
]
_DEGENERATE_RE = re.compile("|".join(f"(?:{p})" for p in _DEGENERATE_PATTERNS), re.I)


def looks_degenerate(text: str) -> bool:
    """True when a candidate is not a usable mediator reply.

    Catches both the classic failure modes (too short, token-repetition) and
    the observed one: fluent English that has nothing to do with the case,
    scraped from the model's pre-training web corpus. Any hit means retry
    with a tightened sampler, then fall back to the rule-based mediator.
    """
    if not text:
        return True
    stripped = text.strip()
    if len(stripped) < 40:                 # "(1)" / "N/A." fragments
        return True
    words = stripped.split()
    if len(words) < 8:
        return True
    if len(set(w.lower() for w in words)) / len(words) < 0.45:   # "1.500/1.500/..."
        return True
    if _DEGENERATE_RE.search(stripped):    # markup / URLs / error pages
        return True
    return False


async def ensure_local_pipe_loaded():
    """Load the model off the event loop, before a session needs it.

    Callers await this *before* constructing a NegotiationSession. A cold load
    takes 1-2 minutes: run on the event loop it does not just delay this request,
    it stalls every other one — and a loop that cannot answer uvicorn's WebSocket
    ping within its 20s default gets the socket closed, which is what silently
    swallowed negotiation messages. After the first call this is a dict lookup.
    """
    if _LOCAL_PIPE is not None:
        return _LOCAL_PIPE
    return await asyncio.to_thread(_build_local_pipe)


def _format_chat_prompt(tokenizer, prompt: str, system: str = None) -> str:
    """Format the mediator prompt using the model's chat template.

    The mediator persona MUST be a ``system`` message, not part of the user
    turn. Embedding it in the user turn (the previous behaviour) makes Qwen
    treat the whole block — persona, case facts and RAG dump — as *user input
    to be commented on*, so it happily continues with unrelated scraped-web
    text instead of role-playing the mediator.

    Standard instruct models (e.g. Qwen) expose a chat_template — use it so
    the model sees proper <|im_start|> markers and role tags.
    """
    system = system or SYSTEM_PROMPT
    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": prompt},
    ]
    template = getattr(tokenizer, "chat_template", None)
    if template:
        try:
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        except Exception:
            pass
    # Fallback for a tokenizer with no template: mirror the plain-text layout
    # but keep the roles explicit so the model still knows who is speaking.
    return f"{system}\n\n{prompt}"


async def _stream_tokens(pipe, formatted: str, max_new_tokens: int = None) -> AsyncGenerator[str, None]:
    """Run blocking generation on a worker thread and yield decoded text chunks.

    Uses AsyncTextIteratorStreamer + a worker thread so the event loop is never
    blocked during generation and tokens are streamed to clients as they
    arrive. The process-wide _PIPE_LOCK serialises generations across cases.

    Exceptions raised inside generate() are re-raised in the async consumer
    after the stream ends.
    """
    from transformers import AsyncTextIteratorStreamer

    if max_new_tokens is None:
        max_new_tokens = _max_new_tokens()
    tokenizer = pipe.tokenizer
    inputs    = tokenizer(formatted, return_tensors="pt").to(pipe.model.device)
    streamer  = AsyncTextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    error_holder: dict = {}

    def _produce():
        try:
            with _PIPE_LOCK:
                pipe.model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    streamer=streamer,
                    max_new_tokens=max_new_tokens,
                    do_sample=True,           # sampling, NOT greedy (fixes repetition loops)
                    temperature=0.6,          # model-card recommended value
                    top_k=50,                 # model-card recommended value
                    top_p=0.95,               # model-card recommended value
                    repetition_penalty=1.25,  # discourage repeating the same tokens
                    no_repeat_ngram_size=5,   # hard-block 5-gram repetition
                )
        except Exception as e:                # noqa: BLE001 — surfaced after the stream
            error_holder["error"] = e
        finally:
            # Always signal stream end so the consumer unblocks, even on crash.
            try:
                streamer.end()
            except Exception:
                pass

    task = asyncio.ensure_future(asyncio.to_thread(_produce))
    async for chunk in streamer:
        if chunk:
            yield chunk
    await task
    if "error" in error_holder:
        raise error_holder["error"]


# ─── Process-wide sentiment / RAG singletons ─────────────────────────────────
# These were previously rebuilt for every NegotiationSession (one per case),
# adding ~1-2s of model/retriever construction per new case. Build each once
# per process and share it, like the LLM pipe.
_SENTIMENT      = None
_SENTIMENT_LOCK = _threading.Lock()

_RAG_RETRIEVER      = None
_RAG_RETRIEVER_LOCK = _threading.Lock()


def _get_sentiment_analyser() -> "NegotiationSentimentAnalyser":
    global _SENTIMENT
    if _SENTIMENT is None:
        with _SENTIMENT_LOCK:
            if _SENTIMENT is None:
                _SENTIMENT = NegotiationSentimentAnalyser()
    return _SENTIMENT


def _get_rag_retriever():
    """Process-wide LegalRetriever singleton.

    Vector (chromadb ONNX) when chromadb is installed — this is what grounds
    the mediator's section citations in real statute text. Falls back to the
    TF-IDF keyword backend automatically (inside LegalRetriever) when
    chromadb is missing, so slim images without it still work.
    """
    global _RAG_RETRIEVER
    if _RAG_RETRIEVER is None:
        with _RAG_RETRIEVER_LOCK:
            if _RAG_RETRIEVER is None:
                from AIML.legal_rag import LegalRetriever
                _RAG_RETRIEVER = LegalRetriever()
    return _RAG_RETRIEVER


class NegotiationModerator:
    """
    LLM-powered negotiation moderator using bharatgenai/LegalParam.

    When use_rag=True (default), relevant legal provisions are retrieved from
    the corpus (data/legal/) via AIML.legal_rag.LegalRetriever and injected
    into the prompt, grounding citations in real law instead of hallucination.

    The model itself is a process-wide singleton (_build_local_pipe), so all
    cases share one loaded instance — it loads once per server start, not per
    case or per message.
    """

    def __init__(self, use_api: bool = False, use_local_hf: bool = False,
                 use_rag: bool = True):
        self.use_api = use_api
        self.use_local_hf = use_local_hf
        self.use_rag = use_rag
        self._rag = None          # lazily built LegalRetriever
        # Which engine produced the most recent reply: "bedrock", "local_hf",
        # or "rule_based". Surfaced as is_fallback so a client can tell a real
        # model reply apart from the deterministic template.
        self.last_source = "rule_based"
        # Recent mediator replies for this conversation — feeds the
        # anti-repetition check in _bedrock_reply (Nova sometimes re-sends a
        # near-identical reply across turns when the dialogue looks similar).
        self._recent_replies: deque = deque(maxlen=6)
        if self.use_local_hf:
            self.pipe = _build_local_pipe()  # singleton — returns cached instance after first call
        elif not use_api:
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

        # Build case-specific context from DB fields
        case_details = []
        if state.dispute_type:
            case_details.append(f"Dispute type: {state.dispute_type}")
        if state.industry:
            case_details.append(f"Industry: {state.industry}")
        if state.state:
            case_details.append(f"State: {state.state}")
        if state.overdue_days:
            case_details.append(f"Payment overdue by: {state.overdue_days} days")
        if state.claimant_name:
            case_details.append(f"Claimant: {state.claimant_name}")
        if state.respondent_name:
            case_details.append(f"Respondent: {state.respondent_name}")
        case_details_text = "\n".join(case_details) if case_details else "Not provided"

        description_text = state.description or "Not provided"
        doc_text = state.document_summary or "No documents uploaded"

        # RAG: retrieve relevant legal provisions for this case
        # (format_context already includes its own header, so inject raw)
        law_text = self._get_law_context(state, last_message)
        law_section = f"\n{law_text}" if law_text else ""

        # Safely format the Nash value — a missing/non-numeric value must not
        # crash prompt building (previously f"{...:,.0f}" would raise).
        nash = strategy_hints.get("nash_solution")
        nash_text = f"₹{nash:,.0f}" if isinstance(nash, (int, float)) else "N/A"

        # NOTE: SYSTEM_PROMPT is deliberately NOT inlined here. It is passed
        # to _format_chat_prompt() as a proper system message so the model
        # role-plays the mediator instead of reading the persona as user text.
        return f"""=== CASE FACTS (from claimant's submission) ===
{case_details_text}
Claim amount: ₹{state.claim_amount:,.0f}
Overall case description / voice transcript:
{description_text}

=== UPLOADED DOCUMENT SUMMARY ===
{doc_text}
{law_section}
=== NEGOTIATION STATUS ===
Predicted fair settlement range: ₹{state.predicted_range[0]:,.0f} – ₹{state.predicted_range[1]:,.0f}
Nash optimal settlement: {nash_text}
Settlement probability: {state.settlement_probability * 100:.0f}%
Phase: {state.phase.value} | Round: {state.round_number}

=== RECENT DIALOGUE ===
{history_text}

=== LAST MESSAGE ===
[{last_message.party.value.upper()}]: {last_message.text}
Sentiment detected: {last_message.sentiment.value if last_message.sentiment else 'neutral'}

=== YOUR TASK ===
You have full knowledge of this specific case. Respond as the impartial mediator using the
case facts, description, documents and retrieved law above. Reference specific details from the
case when relevant (e.g. mention the actual dispute type, overdue days, or amounts from documents).
When a party asks about an uploaded document, answer with the concrete values from the UPLOADED
DOCUMENT SUMMARY — invoice number, total amount, dates, parties — quoting them exactly as given,
and say so plainly if the document block does not contain what they asked for.
Cite the retrieved legal provisions by section number when they apply; never invent provisions
that are not in the RELEVANT LAW block.
Language: {language}. Be specific, helpful and brief (2-4 sentences).
Do not reveal internal strategy hints to parties.
"""

    def _get_law_context(self, state, last_message) -> str:
        """
        Retrieve relevant legal provisions for this case via RAG.

        Builds a query from the case fields plus the latest message, so both
        the steady-state dispute and the immediate question drive retrieval.
        Returns a formatted prompt block, or "" when RAG is disabled/unavailable
        or nothing relevant is found.
        """
        if not self.use_rag:
            return ""
        try:
            if self._rag is None:
                # Process-wide singleton — built once, shared by every session.
                # Vector mode (chromadb ONNX) when available; the facade falls
                # back to TF-IDF keyword automatically when chromadb is absent.
                self._rag = _get_rag_retriever()
            description = " ".join(filter(None, [
                state.description or "",
                last_message.text or "",
            ]))
            results = self._rag.retrieve_law_for_case(
                dispute_type=state.dispute_type,
                overdue_days=state.overdue_days,
                industry=state.industry,
                description=description or None,
                k=3,
            )
            return self._rag.format_context(results) if results else ""
        except Exception as e:
            print(f"[Moderator] RAG retrieval failed: {e}")
            return ""

    def generate_response_sync(self, state, last_message, strategy_hints):
        """Rule-based mediator — no external API call."""
        lo, hi    = state.predicted_range
        mid       = strategy_hints.get("midpoint") or (lo + hi) / 2
        nash      = strategy_hints.get("nash_solution") or mid
        move      = strategy_hints.get("mediator_move", "facilitate")
        agreement = state.agreement_amount

        def inr(v): return f"₹{v:,.0f}" if v else "—"

        if move == "close" and agreement:
            return (
                f"Excellent — both parties have converged near {inr(agreement)}. "
                f"This sits within the predicted band ({inr(lo)}–{inr(hi)}). "
                "I will now prepare the settlement agreement for review and signatures."
            )
        if move == "suggest_mediator_proposal":
            return (
                "I notice an impasse. Allow me to formally propose "
                f"{inr(nash)} — this is the point where both parties gain more than "
                "formal adjudication would deliver. Please respond with 'accept' or 'revise'."
            )
        if last_message.sentiment == SentimentLabel.HOSTILE or move == "de-escalate":
            return (
                "I hear the frustration — this delay is genuinely difficult. "
                "Let's refocus on numbers: the fair settlement window for similar "
                f"MSMED cases is {inr(lo)} to {inr(hi)}. Can each side share their "
                "absolute floor so we can test whether an overlap exists?"
            )
        if state.last_claimant_offer and state.last_respondent_offer and \
           abs(state.last_claimant_offer - state.last_respondent_offer) <= state.claim_amount * 0.10:
            return (
                f"We are very close — the gap is only {inr(abs(state.last_claimant_offer - state.last_respondent_offer))}. "
                f"I recommend both sides meet at {inr(mid)} and close this amicably today."
            )
        if last_message.offer is not None:
            return (
                f"Thank you — a concrete offer of {inr(last_message.offer)} is now on the table. "
                f"For reference, our data suggests a fair Nash equilibrium near {inr(nash)}. "
                "The other party may accept, reject, or counter-offer."
            )
        if state.round_number > 3:
            return (
                "I've observed that extended negotiation increases costs for both sides. "
                f"MSMED Act Section 18 conciliation exists precisely to avoid this. "
                f"My data-driven recommendation remains near {inr(mid)}. "
                "Shall we test this number with both parties?"
            )
        return (
            f"Thank you for sharing that. Based on similar cases, the settlement range "
            f"is {inr(lo)}–{inr(hi)}. I would encourage the next proposal to stay "
            "within or near this band to accelerate resolution."
        )

    # ── Anti-repetition ─────────────────────────────────────────────────────
    @staticmethod
    def _is_repetition(candidate: str, previous, threshold: float = 0.62) -> bool:
        """True when `candidate` substantially reuses any earlier reply.

        Normalized SequenceMatcher catches near-verbatim repeats and lightly
        reworded copies of the same mediator turn. stdlib-only, <1ms for the
        short 2-4 sentence replies it compares. Replies under 40 chars are
        never flagged (too short to judge).
        """
        from difflib import SequenceMatcher

        cand = (candidate or "").lower().strip()
        if len(cand) < 40:
            return False
        for prev in previous or ():
            prev = (prev or "").lower().strip()
            if len(prev) >= 40 and SequenceMatcher(None, cand, prev).ratio() >= threshold:
                return True
        return False

    BEDROCK_SYSTEM = (
        "You are an impartial MSME mediation expert under the MSMED Act 2006 "
        "(Sections 15-18: payment liability, compound interest, MSEFC process). "
        "Reply in 2-4 sentences using the case facts, documents and retrieved "
        "law in the prompt. Cite section numbers only from the RELEVANT LAW "
        "block; never invent provisions. Propose the Nash/midpoint figure "
        "when an impasse exists. Do not reveal strategy hints. "
        "Never repeat a sentence or line you have already said earlier in this "
        "conversation; when revisiting a point, rephrase it in fresh wording."
    )

    async def _bedrock_reply(
        self,
        state: NegotiationState,
        last_message: Message,
        strategy_hints: dict,
        language: str = "en",
    ):
        """One Bedrock turn, or None when disabled/unavailable.

        Shared by the REST path (generate_response) and the WebSocket path
        (generate_response_stream) so the two can never diverge again. The
        streaming path previously had no Bedrock branch at all and fell
        straight through to the rule-based template, which is why the live
        chat showed canned text while the REST endpoint used the model.
        """
        try:
            from api.config import settings as _settings

            if not bool(getattr(_settings, "USE_BEDROCK", False)):
                return None

            from AIML.bedrock_client import converse as _bedrock_converse

            prompt = self._build_prompt(state, last_message, strategy_hints, language)
            _model    = _settings.BEDROCK_MEDIATOR_MODEL
            _max_tok  = int(getattr(_settings, "BEDROCK_MAX_TOKENS", 400) or 400)
            _reply = await asyncio.to_thread(
                _bedrock_converse, prompt, self.BEDROCK_SYSTEM,
                _model, _max_tok, 0.3,
            )
            # One explicit rephrase retry if this turn copies an earlier
            # reply; if the retry is still a copy we accept it rather than
            # loop (a repeated reply beats no reply).
            if self._is_repetition(_reply, list(self._recent_replies)):
                print("[Moderator] Reply repeated an earlier one — rephrasing", flush=True)
                _reply = await asyncio.to_thread(
                    _bedrock_converse,
                    prompt + "\n\nIMPORTANT: Your previous attempt repeated an "
                             "earlier reply almost word-for-word. Reply with a "
                             "completely different sentence structure and fresh "
                             "wording; do not reuse the earlier phrasing.",
                    self.BEDROCK_SYSTEM,
                    _model, _max_tok, 0.3,
                )
            self._recent_replies.append(_reply)
            self.last_source = "bedrock"
            return _reply
        except Exception as e:
            # Keep the deterministic reply available, but record why so the
            # caller reports is_fallback instead of passing template text off
            # as model output.
            self.last_source = "rule_based"
            print(f"[Moderator] Bedrock failed ({e}) — falling through", flush=True)
            return None

    async def generate_response(
        self,
        state: NegotiationState,
        last_message: Message,
        strategy_hints: dict,
        language: str = "en",
    ) -> str:
        # ── Bedrock path (fast, ~1-2s) — checked FIRST so USE_BEDROCK=true
        # never pays the local-model cost even when use_local_hf is also set.
        _reply = await self._bedrock_reply(state, last_message, strategy_hints, language)
        if _reply:
            return _reply

        if self.use_local_hf:
            prompt = self._build_prompt(state, last_message, strategy_hints, language)

            # Format with the model's chat template (Qwen etc.) or the legacy
            # <user>/<assistant> markers LegalParam was trained with.
            formatted = _format_chat_prompt(self.pipe.tokenizer, prompt)

            # The pipeline is a process-wide singleton shared by all cases —
            # serialise calls so concurrent messages can't corrupt generation.
            # ── Generation ─────────────────────────────────────────────────
            # Greedy decoding (do_sample=False) gets stuck repeating a single
            # token on this CPU model (e.g. "1.500/1.500/1.500/..."). Use
            # sampling with the model-card parameters + a repetition penalty
            # and a hard ngram block so we always get coherent multi-sentence
            # replies instead of an infinite loop.
            for _attempt in range(3):
                # Tighten the sampler on every retry. The first pass uses the
                # model-card defaults; later passes drop the temperature and
                # raise the repetition penalty, which is what pulls a drifted
                # model back onto the mediator task.
                if _attempt == 0:
                    temperature, top_p, rep = 0.6, 0.95, 1.25
                elif _attempt == 1:
                    temperature, top_p, rep = 0.3, 0.85, 1.40
                else:
                    temperature, top_p, rep = 0.1, 0.70, 1.50

                with _PIPE_LOCK:
                    output = self.pipe(
                        formatted,
                        max_new_tokens=_max_new_tokens(),   # enough for a full 2-4 sentence response
                        do_sample=True,           # sampling, NOT greedy (fixes repetition loops)
                        temperature=temperature,
                        top_k=50,                 # model-card recommended value
                        top_p=top_p,
                        repetition_penalty=rep,   # discourage repeating the same tokens
                        no_repeat_ngram_size=5,   # hard-block 5-gram repetition (kills "1.500/...")
                        return_full_text=False,   # return only the newly generated text
                    )

                # Plain text-generation output format: [{'generated_text': '...'}]
                candidate = output[0]['generated_text']
                candidate = candidate.replace("<assistant>", "").strip()

                # Accept only a reply that is coherent, on-task and clean of
                # markup/URLs/scraped-web artefacts; otherwise retry tighter,
                # then fall back.
                if not looks_degenerate(candidate):
                    if _attempt:
                        print(f"[Moderator] Accepted on attempt {_attempt + 1}.")
                    self.last_source = "local_hf"
                    return candidate
                print(
                    f"[Moderator] Rejected generation (attempt {_attempt + 1}/3): "
                    f"{candidate[:90]!r}",
                    flush=True,
                )

            # Degenerate-output guard: fall back to the deterministic
            # rule-based mediator rather than serve scraped-web text.
            return self.generate_response_sync(state, last_message, strategy_hints)

        return self.generate_response_sync(state, last_message, strategy_hints)

    async def generate_response_stream(
        self,
        state: NegotiationState,
        last_message: Message,
        strategy_hints: dict,
        language: str = "en",
    ) -> AsyncGenerator[str, None]:
        """Async generator of mediator reply text chunks.

        With the local model this streams tokens as they are generated (the
        event loop stays free — generation runs on a worker thread). The
        rule-based responder yields its whole short reply in one chunk.

        The caller decides whether the streamed output is acceptable; a
        degenerate reply can be replaced with generate_response_sync().
        """
        self.last_source = "rule_based"
        # ── Bedrock first, exactly like generate_response() ────────────────
        # Nova has no token stream here, so the whole reply is yielded as one
        # chunk. Without this branch the WS/stream path skipped the model
        # entirely and served the deterministic template.
        _reply = await self._bedrock_reply(state, last_message, strategy_hints, language)
        if _reply:
            yield _reply
            return

        if self.use_local_hf:
            prompt = self._build_prompt(state, last_message, strategy_hints, language)
            formatted = _format_chat_prompt(self.pipe.tokenizer, prompt)
            self.last_source = "local_hf"
            async for chunk in _stream_tokens(self.pipe, formatted):
                yield chunk
            return
        yield self.generate_response_sync(state, last_message, strategy_hints)


# ─── Main Negotiation Session ─────────────────────────────────────────────────

class NegotiationSession:
    """
    Orchestrates a full negotiation session.
    Call process_message() for each party turn.
    """

    def __init__(self, state: NegotiationState, language: str = "en",
                 use_local_hf: bool = False, use_api: bool = False,
                 use_rag: bool = True):
        self.state      = state
        self.language   = language
        self.sentiment  = _get_sentiment_analyser()   # process-wide singleton
        self.strategy   = BargainingStrategyEngine()
        self.moderator  = NegotiationModerator(
            use_api=use_api, use_local_hf=use_local_hf, use_rag=use_rag
        )

    async def process_message(
        self,
        party:      Party,
        text:       str,
        offer:      Optional[float] = None,
    ) -> dict:
        """Process one party's message. Returns mediator response + state update."""

        msg, strategy_hints = self._prepare_turn(party, text, offer)
        self.moderator.last_source = "rule_based"
        mediator_text = await self.moderator.generate_response(
            self.state, msg, strategy_hints, self.language
        )
        return self._build_result(mediator_text, msg, strategy_hints)

    async def process_message_stream(
        self,
        party:      Party,
        text:       str,
        offer:      Optional[float] = None,
    ) -> AsyncGenerator:
        """Streaming variant of process_message().

        Yields, in order:
          1. dict  — metadata (mediator_response="") for the mediator_started frame
          2. str   — text chunks of the mediator reply as they are generated
          3. dict  — the final result dict (full mediator_response + metadata)
        """
        msg, strategy_hints = self._prepare_turn(party, text, offer)

        # Metadata first so the client can show phase/round immediately.
        yield self._build_result("", msg, strategy_hints)

        chunks = []
        async for chunk in self.moderator.generate_response_stream(
            self.state, msg, strategy_hints, self.language
        ):
            chunks.append(chunk)
            yield chunk

        full = "".join(chunks).strip()
        # Degenerate/empty guard — replace with the deterministic responder.
        # Uses the same checks as the non-streaming path (markup, URLs, error
        # pages, spam boilerplate, too short, token repetition), not just the
        # length/variety pair: scraped-web text passes those two easily.
        if looks_degenerate(full):
            full = self.moderator.generate_response_sync(self.state, msg, strategy_hints)
            # The reply shown to the client is now the template, so the flag
            # must say so even though the model call itself succeeded.
            self.moderator.last_source = "rule_based"

        yield self._build_result(full, msg, strategy_hints)

    def _prepare_turn(
        self,
        party:  Party,
        text:   str,
        offer:  Optional[float],
    ) -> tuple[Message, dict]:
        """Shared analysis for sync and streaming paths: sentiment, offer
        tracking, deadlock/ZOPA detection and game-theory strategy hints."""
        # 1. Sentiment analysis
        sentiment_label, _ = self.sentiment.analyse(text)

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

        # 7. Round counter
        self.state.round_number += 1

        return msg, strategy_hints

    def _build_result(
        self,
        mediator_text:  str,
        msg:            Message,
        strategy_hints: dict,
    ) -> dict:
        """Assemble the standard result dict both paths return."""
        source = getattr(self.moderator, "last_source", "rule_based")
        return {
            "mediator_response":    mediator_text,
            "ai_source":            source,
            "is_fallback":          source == "rule_based",
            "sentiment_detected":   msg.sentiment.value if msg.sentiment else "neutral",
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
