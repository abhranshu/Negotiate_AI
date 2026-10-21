def _make_case(client, auth_headers):
    r = client.post(
        "/api/cases",
        json={"dispute_type": "delayed_payment", "claim_amount": 100000},
        headers=auth_headers,
    )
    return r.json()["id"]


def test_upload_and_list_document(client, auth_headers):
    case_id = _make_case(client, auth_headers)
    files = {"files": ("invoice.txt", b"Invoice INV-001 amount Rs. 100000 due 2025-01-01", "text/plain")}
    r = client.post(f"/api/cases/{case_id}/documents", files=files, headers=auth_headers)
    assert r.status_code == 200, r.text
    docs = r.json()
    assert isinstance(docs, list) and len(docs) == 1
    # The classifier may or may not succeed; the route must persist the doc.
    assert docs[0]["filename"] == "invoice.txt"

    r = client.get(f"/api/cases/{case_id}/documents", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_document_requires_auth(client, auth_headers):
    case_id = _make_case(client, auth_headers)
    files = {"files": ("x.txt", b"data", "text/plain")}
    r = client.post(f"/api/cases/{case_id}/documents", files=files)
    assert r.status_code == 401
