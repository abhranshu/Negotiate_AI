"""Module 1 — voice endpoint tests.

These tests explicitly assert the CURRENT behaviour: with ``USE_LOCAL_ASR=false``
the endpoint runs in stub mode. The purpose is to make the stub VISIBLE so it can
never be mistaken for real transcription in a passing test run.
"""
import io
import struct
import wave


def _make_case(client, auth_headers):
    r = client.post(
        "/api/cases",
        json={"dispute_type": "delayed_payment", "claim_amount": 100000},
        headers=auth_headers,
    )
    return r.json()["id"]


def _tiny_wav() -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(struct.pack("<" + "h" * 1600, *([0] * 1600)))
    return buf.getvalue()


def test_voice_upload_accepted(client, auth_headers):
    case_id = _make_case(client, auth_headers)
    files = {"file": ("voice.wav", _tiny_wav(), "audio/wav")}
    r = client.post(f"/api/cases/{case_id}/voice", files=files, headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["id"] == case_id


def test_voice_rejects_bad_extension(client, auth_headers):
    case_id = _make_case(client, auth_headers)
    files = {"file": ("notaudio.txt", b"hello", "text/plain")}
    r = client.post(f"/api/cases/{case_id}/voice", files=files, headers=auth_headers)
    assert r.status_code == 400


def test_voice_stub_mode_is_visible(client, auth_headers):
    """With USE_LOCAL_ASR=false the transcript is a demo stub.

    This locks the current behaviour in place so that when real ASR is enabled,
    this test fails and forces a conscious update rather than a silent change.
    """
    case_id = _make_case(client, auth_headers)
    files = {"file": ("voice.wav", _tiny_wav(), "audio/wav")}
    r = client.post(f"/api/cases/{case_id}/voice", files=files, headers=auth_headers)
    assert r.status_code == 200
    # Stub transcripts contain "Demo mode"; real transcripts would not.
    assert "Demo mode" in (r.json().get("description") or "")
