"""
Negotiation chat route — triggers Module 4 (NegotiationSession).
POST /api/cases/{case_id}/negotiate  — REST endpoint to send a message; get AI mediator response
GET  /api/cases/{case_id}/messages   — Retrieve full chat history
WS   /api/cases/ws/{case_id}        — Real-Time WebSocket Endpoint (Phase 3)
"""

import asyncio
import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from api.database import get_db
from api.models.case import Case, Message, CaseStatus, CASE_WITH_CONTEXT
from api.models.user import User
from api.schemas.case import NegotiateRequest, NegotiateResponse, MessageOut
from api.auth import get_current_user
from api.ws_manager import manager
from api.config import settings

router = APIRouter(prefix="/api/cases", tags=["Negotiation"])

_SESSIONS: dict = {}          # in-memory session cache; swap for Redis in production
_SESSION_LAST_ACCESS: dict = {}  # case_id -> monotonic timestamp (for pruning)
_SESSION_TTL_SECONDS = 30 * 60   # idle sessions are dropped after 30 minutes
_SESSION_MAX = settings.NEGOTIATION_SESSION_CACHE_MAX  # hard cap on cached sessions

# Neutral mediator fallback used when the AI module is unavailable or errors.
# Shared by the REST and WebSocket paths (previously duplicated in four places).
_FALLBACK_RESULT = {
    "mediator_response":  "Thank you for your message. The AI mediator is analyzing the terms.",
    "sentiment_detected": "neutral",
    "phase":              "bargaining",
    "round":              1,
    "agreement_reached":  False,
    "agreement_amount":   None,
    "strategy_hints":     {},
    # Marks this as the neutral fallback (Module 4 unavailable/errored) rather
    # than a real mediator turn. Clients must check this before trusting the
    # text as AI-generated. Real results from the session leave it unset (False).
    "is_fallback":        True,
}


def _prune_sessions():
    """Drop idle/oldest sessions so _SESSIONS can't grow without bound."""
    now = time.monotonic()
    for cid in [c for c, t in _SESSION_LAST_ACCESS.items() if now - t > _SESSION_TTL_SECONDS]:
        _SESSIONS.pop(cid, None)
        _SESSION_LAST_ACCESS.pop(cid, None)
    if len(_SESSIONS) > _SESSION_MAX:
        overflow = len(_SESSIONS) - _SESSION_MAX
        for cid in sorted(_SESSION_LAST_ACCESS, key=_SESSION_LAST_ACCESS.get)[:overflow]:
            _SESSIONS.pop(cid, None)
            _SESSION_LAST_ACCESS.pop(cid, None)


def _touch_session(case_id: str):
    _SESSION_LAST_ACCESS[case_id] = time.monotonic()


def _commit_with_retry(db: Session, retries: int = 2):
    """Commit with a small retry on dropped DB connections.

    Supabase's pooler / NAT / Wi-Fi can kill a connection mid-request
    ("server closed the connection unexpectedly"). pool_pre_ping only
    validates a connection at checkout, so it can't save one that dies
    mid-transaction. We roll back and retry — the retry checks out a
    fresh connection, which pre_ping then validates (transparent reconnect).
    """
    for attempt in range(retries + 1):
        try:
            db.commit()
            return
        except OperationalError:
            db.rollback()
            if attempt >= retries:
                raise


def _get_or_create_session(case: Case):
    try:
        from AIML.negotiation_ai import NegotiationSession, NegotiationState
        from api.config import settings

        use_local = settings.USE_LOCAL_MODEL   # env: USE_LOCAL_MODEL=true
        _prune_sessions()
        _touch_session(case.id)

        # Build document summary from all uploaded docs for this case. Needed by
        # both branches below (an existing session gets its summary refreshed).
        doc_summary = None
        if hasattr(case, "documents") and case.documents:
            parts = []
            for doc in case.documents:
                fields = doc.key_fields if isinstance(doc.key_fields, dict) else {}
                if not doc.extracted_text and not fields:
                    continue
                # Structured extraction first: the mediator answers "what does my
                # invoice say" from these values, and Module 2 already pulled them
                # out. Raw OCR follows as supporting text (truncated — an OCR dump
                # of several pages would otherwise crowd out the case facts).
                facts = []
                if fields.get("invoice_number"):
                    facts.append(f"number={fields['invoice_number']}")
                if fields.get("amount"):
                    facts.append(f"amount=INR {fields['amount']:,}")
                if fields.get("dates"):
                    facts.append("dates=" + ", ".join(str(d) for d in fields["dates"][:3]))
                if fields.get("parties"):
                    facts.append("parties=" + ", ".join(str(p) for p in fields["parties"][:3]))
                if fields.get("summary"):
                    facts.append(f"summary={fields['summary']}")
                header = f"[{doc.doc_type or doc.filename}: {doc.filename}]"
                body = ("; ".join(facts) if facts else "")
                if doc.extracted_text:
                    body = f"{body}\nOCR text: {doc.extracted_text[:800]}" if body else (
                        f"OCR text: {doc.extracted_text[:800]}"
                    )
                parts.append(f"{header}\n{body}")
            if parts:
                doc_summary = "\n\n".join(parts)

        if case.id not in _SESSIONS:
            # Only needed to seed a brand-new session. These used to be resolved
            # on every message, costing two extra SELECTs per message whose
            # results were then discarded for any session already cached.
            claimant_name   = case.claimant.full_name   if case.claimant   else None
            respondent_name = case.respondent.full_name if case.respondent else None

            state = NegotiationState(
                case_id               = case.id,
                claim_amount          = case.claim_amount or 100_000,
                predicted_range       = (
                    case.settlement_range_low  or (case.claim_amount or 100_000) * 0.6,
                    case.settlement_range_high or (case.claim_amount or 100_000) * 0.9,
                ),
                settlement_probability = case.settlement_probability or 0.65,
                # ── Case-specific context ──────────────────────────────────
                description      = case.description,
                dispute_type     = str(case.dispute_type.value) if case.dispute_type else None,
                industry         = case.industry,
                state            = case.state,
                overdue_days     = case.overdue_days,
                claimant_name    = claimant_name,
                respondent_name  = respondent_name,
                document_summary = doc_summary,
            )
            _SESSIONS[case.id] = NegotiationSession(
                state, language="en",
                use_local_hf=use_local,
                use_api=settings.USE_EXTERNAL_LLM,
                use_rag=True,
            )
        else:
            # Update mutable fields in case new docs were uploaded since session started
            session = _SESSIONS[case.id]
            session.state.description      = case.description
            session.state.document_summary = doc_summary

        return _SESSIONS[case.id]
    except ImportError:
        return None


def _party_from_user(case: Case, user: User) -> str:
    if case.claimant_id == user.id:
        return "claimant"
    if case.respondent_id == user.id:
        return "respondent"
    raise HTTPException(status_code=403, detail="You are not a party to this case")


@router.post("/{case_id}/negotiate", response_model=NegotiateResponse)
async def send_message(
    case_id:      str,
    payload:      NegotiateRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Send a negotiation message via REST API. Module 4 returns a mediator response."""
    # _get_or_create_session() reads the case's documents and parties; load them
    # with the case so the session lookup doesn't emit a lazy SELECT per
    # relationship.
    case = (
        db.query(Case)
        .options(*CASE_WITH_CONTEXT)
        .filter(Case.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    party_str = _party_from_user(case, current_user)
    if case.status in (CaseStatus.draft, CaseStatus.submitted):
        case.status = CaseStatus.in_progress

    # Warm the local model BEFORE the session is built and off the event loop.
    # NegotiationSession's constructor loads the model on first use; doing that
    # here (in a worker thread) instead of inside the loop means a 1-2 minute
    # cold load can no longer stall every other request — including the
    # WebSocket pings whose 20s timeout was closing the client's socket.
    from api.config import settings as _settings
    if _settings.USE_LOCAL_MODEL:
        try:
            from AIML.negotiation_ai import ensure_local_pipe_loaded
            await ensure_local_pipe_loaded()
        except ImportError:
            pass

    session = _get_or_create_session(case)

    # End the read transaction BEFORE the AI call. SQLAlchemy releases the
    # connection back to the pool on commit, so no connection sits idle in an
    # open transaction during slow model inference. (An idle-in-transaction
    # connection during generation is what Supabase's pooler / NAT kills,
    # producing "server closed the connection unexpectedly" on the final
    # commit.) The writes after the AI call check out a fresh connection,
    # which pool_pre_ping then validates.
    db.commit()

    if session:
        try:
            from AIML.negotiation_ai import Party
            party_enum = Party.CLAIMANT if party_str == "claimant" else Party.RESPONDENT
            # Run CPU-bound model inference in a thread to avoid blocking the
            # event loop — keeps WebSocket connections alive during generation.
            result = await asyncio.to_thread(
                lambda: asyncio.run(session.process_message(party_enum, payload.text, payload.offer))
            )
        except Exception as exc:
            print(
                f"[Negotiation/REST] mediator failed "
                f"({type(exc).__name__}: {exc})",
                flush=True,
            )
            result = _FALLBACK_RESULT
    else:
        result = _FALLBACK_RESULT

    db.add(Message(case_id=case_id, party=party_str, text=payload.text,
                   offer=payload.offer, sentiment=result.get("sentiment_detected"),
                   phase=result.get("phase"), round_num=result.get("round")))
    db.add(Message(case_id=case_id, party="mediator", text=result["mediator_response"],
                   phase=result.get("phase"), round_num=result.get("round")))

    if result.get("agreement_reached") and result.get("agreement_amount"):
        case.agreement_amount = result["agreement_amount"]
        case.status           = CaseStatus.agreement

    _commit_with_retry(db)

    # If active WebSocket connections exist, broadcast event
    await manager.broadcast_public(case_id, {
        "type": "chat_message",
        "sender": party_str,
        "text": payload.text,
        "offer": payload.offer,
        "mediator_response": result["mediator_response"]
    })

    return result


@router.websocket("/ws/{case_id}")
async def websocket_negotiation(
    websocket: WebSocket,
    case_id: str,
    party: str = "claimant",  # Passed as query param: /api/cases/ws/{case_id}?party=claimant
    db: Session = Depends(get_db)
):
    """
    Real-Time Bi-Directional Negotiation WebSocket.
    Manages live chat, AI mediator public responses, and party-specific private strategy hints.
    """
    party_str = party.lower()
    if party_str not in ("claimant", "respondent"):
        await websocket.close(code=4000, reason="Invalid party. Must be 'claimant' or 'respondent'")
        return

    await manager.connect(websocket, case_id, party_str)

    try:
        while True:
            # 1. Receive JSON message from connected party
            data = await websocket.receive_json()

            # Live typing indicator (frontend debounces these): relay to the
            # room and return — it is never persisted and never reaches the
            # mediator, so it must not fall through to the offer/text path.
            if data.get("type") == "typing":
                await manager.broadcast_public(case_id, {
                    "type": "typing",
                    "sender": party_str,
                    "is_typing": bool(data.get("is_typing", True)),
                })
                continue

            text = data.get("text", "")
            offer = data.get("offer")

            if not text:
                continue

            # 2. Fetch case from database
            #    Eager-load what _get_or_create_session() below needs. Note the
            #    commit just after this expires all loaded instances, so on the
            #    first message of a case the relationships get re-read anyway;
            #    on every later message (status already in_progress, no commit)
            #    this is what keeps it to one round trip.
            case = (
                db.query(Case)
                .options(*CASE_WITH_CONTEXT)
                .filter(Case.id == case_id)
                .first()
            )
            if case and case.status in (CaseStatus.draft, CaseStatus.submitted):
                case.status = CaseStatus.in_progress
                db.commit()

            # 3. Broadcast incoming user message to all public room listeners
            await manager.broadcast_public(case_id, {
                "type": "user_message",
                "sender": party_str,
                "text": text,
                "offer": offer
            })

            # 4. Invoke Module 4 (NegotiationSession)
            #    Warm the model first, in a worker thread: constructing the
            #    session triggers the load, and blocking this loop for the
            #    duration of it is what made the client's socket die (uvicorn
            #    closes a WebSocket whose ping goes unanswered for 20s) — so
            #    messages vanished with no reply and no error.
            from api.config import settings as _settings
            if case and _settings.USE_LOCAL_MODEL:
                try:
                    from AIML.negotiation_ai import ensure_local_pipe_loaded
                    await ensure_local_pipe_loaded()
                except ImportError:
                    pass

            session = _get_or_create_session(case) if case else None

            # Release the DB connection BEFORE the AI call (same rationale as
            # in send_message — don't hold an idle-in-transaction connection
            # during slow model inference; pre_ping reconnects on next use).
            if case:
                db.commit()

            result = _FALLBACK_RESULT
            if session:
                try:
                    from AIML.negotiation_ai import Party
                    party_enum = Party.CLAIMANT if party_str == "claimant" else Party.RESPONDENT
                    # Stream the mediator reply: metadata first (mediator_started),
                    # then text chunks as they are generated (mediator_token), then
                    # the final authoritative frame (mediator_response). Only the
                    # first metadata event is broadcast as mediator_started; the
                    # final result dict just carries the full text for persistence.
                    streaming_started = False
                    async for event in session.process_message_stream(party_enum, text, offer):
                        if isinstance(event, str):
                            await manager.broadcast_public(case_id, {
                                "type": "mediator_token",
                                "text": event,
                            })
                        elif not streaming_started:
                            streaming_started = True
                            result = event
                            await manager.broadcast_public(case_id, {
                                "type": "mediator_started",
                                "sentiment": event.get("sentiment_detected"),
                                "phase": event.get("phase"),
                                "round": event.get("round"),
                                "agreement_reached": event.get("agreement_reached"),
                                "agreement_amount": event.get("agreement_amount"),
                            })
                        else:
                            result = event  # final dict — full text, no extra frame
                except Exception as exc:
                    # Never swallow this. Previously a broken mediator looked
                    # exactly like a slow one: the room silently received the
                    # neutral template and nothing reached CloudWatch.
                    print(
                        f"[Negotiation/WS] mediator failed "
                        f"({type(exc).__name__}: {exc})",
                        flush=True,
                    )
                    result = _FALLBACK_RESULT
            else:
                result = _FALLBACK_RESULT

            # Save messages to database persistence
            if case:
                db.add(Message(case_id=case_id, party=party_str, text=text,
                               offer=offer, sentiment=result.get("sentiment_detected"),
                               phase=result.get("phase"), round_num=result.get("round")))
                db.add(Message(case_id=case_id, party="mediator", text=result["mediator_response"],
                               phase=result.get("phase"), round_num=result.get("round")))

                if result.get("agreement_reached") and result.get("agreement_amount"):
                    case.agreement_amount = result["agreement_amount"]
                    case.status           = CaseStatus.agreement

                _commit_with_retry(db)

            # 5. Broadcast Mediator's Public Response to the room
            await manager.broadcast_public(case_id, {
                "type": "mediator_response",
                "sender": "mediator",
                "text": result["mediator_response"],
                "sentiment": result.get("sentiment_detected"),
                "phase": result.get("phase"),
                "round": result.get("round"),                "agreement_reached": result.get("agreement_reached"),
                "agreement_amount": result.get("agreement_amount"),
                # Which engine produced this text and whether it is the neutral
                # template. The chat UI is the primary consumer, so it needs the
                # same honest signal the REST response already carries.
                "ai_source": result.get("ai_source"),
                "is_fallback": bool(result.get("is_fallback", False)),
            })




            # 6. Send Private Party-Specific Strategy Hints (Crucial Novelty!)
            hints = result.get("strategy_hints", {})
            if party_str in hints:
                await manager.send_private(case_id, party_str, {
                    "type": "private_hint",
                    "recipient": party_str,
                    "hint": hints[party_str]
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, case_id)
    except Exception as e:
        manager.disconnect(websocket, case_id)


@router.get("/{case_id}/messages", response_model=List[MessageOut])
def get_messages(
    case_id:      str,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Return the full negotiation chat history for a case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.claimant_id != current_user.id and case.respondent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")
    # Query the messages directly rather than walking case.messages: the
    # relationship pulls the whole collection into the session's identity map
    # and the ordering then had to be redone in Python. Ordering in the database
    # keeps this to a single statement and leaves the ORM graph untouched.
    return (
        db.query(Message)
        .filter(Message.case_id == case_id)
        .order_by(Message.timestamp)
        .all()
    )
