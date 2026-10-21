def _make_case(client, auth_headers):
    r = client.post(
        "/api/cases",
        json={"dispute_type": "delayed_payment", "claim_amount": 150000},
        headers=auth_headers,
    )
    return r.json()["id"]


def test_ws_connect_and_typing(client, auth_headers):
    case_id = _make_case(client, auth_headers)
    with client.websocket_connect(f"/api/cases/ws/{case_id}?party=claimant") as ws:
        # On connect the manager broadcasts a presence update.
        first = ws.receive_json()
        assert first["type"] == "presence_update"

        ws.send_json({"type": "typing", "is_typing": True})
        typing = ws.receive_json()
        assert typing["type"] == "typing"
        assert typing["sender"] == "claimant"


def test_ws_invalid_party_closed(client, auth_headers):
    from starlette.websockets import WebSocketDisconnect

    case_id = _make_case(client, auth_headers)
    try:
        with client.websocket_connect(f"/api/cases/ws/{case_id}?party=hacker") as ws:
            ws.receive_json()
        assert False, "invalid party should have closed the socket"
    except WebSocketDisconnect:
        pass
