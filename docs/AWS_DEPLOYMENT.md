# NegotiateAI — AWS Deployment Guide

> Grounded in the **current** codebase (audited Oct 2026), not the README.
> Every resource below is listed with its Free Tier eligibility and billing risk.

---

## 0. The honest headline first

The application's `.env` runs Module 4 with a **local Qwen model**
(`USE_LOCAL_MODEL=true`, `LOCAL_MODEL_ID=Qwen/Qwen2.5-1.5B-Instruct`, int8). Combined
with PyTorch, Transformers, Whisper, XGBoost/LightGBM and SHAP, the peak resident
memory is **well above 1 GB**.

> **A 1 GB AWS Free Tier micro instance (t3.micro / t4g.micro) CANNOT run all five
> modules with the local LLM enabled.** This is stated plainly rather than hidden.
> Choose one of the two paths in §2.

---

## 1. Current architecture (as-is)

```
React SPA (frontend/)                FastAPI (api/main.py)
  REACT_APP_API_URL ──────────►        /api/auth  /api/cases
  ws:// derived from API base ──►      /api/cases/{id}/voice|documents|predict|negotiate|settlement
                                       WS /api/cases/ws/{case_id}
                                          │
              ┌───────────────────────────┼───────────────────────────┐
        PostgreSQL (Supabase pooler)   Local disk (uploads/)     AIML/ models
        DATABASE_URL                   data/legal  data/chroma     models/*.pkl
```

- DB: PostgreSQL via `DATABASE_URL` (Supabase pooler, port 6543).
- Migrations: Alembic runs on startup (`api/main.py` lifespan) → `upgrade head`,
  falling back to `create_all()` on failure.
- Uploads: local filesystem (`UPLOAD_DIR=./uploads`) — **ephemeral in containers**.
- RAG: `AIML/legal_rag.py` uses ChromaDB + sentence-transformers when installed,
  else a stdlib keyword fallback. `chromadb`/`sentence_transformers` are **not**
  currently installed → keyword fallback is active.
- Module 3 models are pre-trained and present in `models/`.

---

## 2. Two deployment paths

### Path A — Free Tier compatible (recommended for cost safety)
Keep the API on a micro instance and **keep Module 4 on the existing external
LLM path** (`USE_EXTERNAL_LLM=true`) OR run Node 4 in its rule-based mode.
Set `USE_LOCAL_MODEL=false`. This preserves the API and DB functionality but
changes Module 4's generator — a conscious trade-off, documented.

### Path B — Preserve the local Qwen LLM (NOT Free Tier)
Requires a **larger, paid instance** (e.g. `t3.small` 2 GB minimum, `t3.medium`
4 GB recommended) to avoid OOM. The user has explicitly accepted this.

---

## 3. Resource table (estimated — see MODEL_MEMORY_REPORT section for method)

| Component | Path A (Free Tier) | Path B (local Qwen) |
|---|---|---|
| OS + Docker | ~200 MB | ~200 MB |
| Python + FastAPI + SQLAlchemy | ~150 MB | ~150 MB |
| PyTorch (CPU) | not loaded | ~400–800 MB |
| Module 1 (faster-whisper tiny, lazy) | 0 (stub) / ~150 MB when enabled | ~150 MB |
| Module 2 (Tesseract + DistilBERT lazy) | ~250 MB on demand | ~250 MB on demand |
| Module 3 (XGBoost + LightGBM + SHAP) | ~200 MB | ~200 MB |
| Module 4 (Qwen 1.5B int8) | 0 (external/rule-based) | ~1.5–2.5 GB |
| RAG (keyword) | ~30 MB | ~30 MB |
| **Estimated peak** | **~1.0–1.3 GB** | **~3–4.5 GB** |
| Fits 1 GB micro? | Marginal (1 worker) | **No** |

Real numbers must be confirmed with `docker stats` on the target instance before
committing (see §7).

---

## 4. AWS services, Free Tier eligibility and billing risk

| Service | Resource | Free Tier | Billing risk |
|---|---|---|---|
| **EC2** | t3.micro / t4g.micro, 1 worker | 750 h/mo (12 mo, new accounts) | Over 750 h, or any t3.small+ → charged hourly |
| **EBS** | 30 GB gp3 root | 30 GB (12 mo) | Snapshots + extra GB charged |
| **Elastic IP** | 1 attached to running instance | Free while attached | **Charged if unattached** — release it |
| **S3** | Frontend static site | 5 GB / 12 mo | New accounts only; after 12 mo billed |
| **CloudFront** | CDN for SPA | 1 TB / 12 mo | Billed after 12 mo |
| **RDS** | db.t3.micro Postgres | 750 h / 12 mo | **Recommended NOT to use** — prefer Supabase free tier (already wired) |
| **ECR** | Container registry | 500 MB/mo (12 mo) | Image > 500 MB billed |
| **NAT Gateway** | — | **NOT free** | **~$32/mo — do NOT create** |
| **ALB** | — | **NOT free** | **~$16/mo — avoid; use nginx on EC2** |
| **SageMaker / OpenSearch / ElastiCache** | — | varied | **Avoid** |

> ⚠️ Free Tier is account-age dependent. Verify in **Billing → Free Tier** console
> before provisioning. Do not assume something is free because the docs say so.

---

## 5. Recommended architecture (Path A)

```
Internet
  │
  ├── CloudFront ──► S3 (React build)          [static SPA]
  │
  └── EC2 t3.micro (single instance)
        └── nginx :80/:443  ──► 127.0.0.1:8000
              └── docker: gunicorn api.main:app --workers 1
                    └── Supabase Postgres (external, already configured)
```

No NAT Gateway. No ALB. No RDS. One instance, one worker.

---

## 6. Deployment steps (Path A)

```bash
# 1. Build & run locally first
docker build -t negotiateai:local .
docker run --env-file .env -p 8000:8000 negotiateai:local
curl -s localhost:8000/health        # expect {"status":"ok","database":"ok"}

# 2. On the EC2 box (Amazon Linux 2023 / Ubuntu 22.04)
sudo dnf install -y docker nginx      # ubuntu: apt-get
sudo systemctl enable --now docker nginx

# 3. Put the env file OUTSIDE the image
sudo mkdir -p /etc/negotiateai
sudo cp .env /etc/negotiateai/.env    # set real values; chmod 600
#   Required for Free Tier: USE_LOCAL_MODEL=false
#   ALLOWED_ORIGINS=["https://your-cloudfront-domain"]

# 4. Run the container (1 worker, restart on failure)
sudo docker run -d --name negotiateai --restart unless-stopped \
  --env-file /etc/negotiateai/.env -p 127.0.0.1:8000:8000 \
  negotiateai:local

# 5. nginx reverse proxy (WebSocket upgrade headers REQUIRED)
```

`/etc/nginx/conf.d/negotiateai.conf`:

```nginx
server {
    listen 80;
    server_name _;
    client_max_body_size 25m;      # uploads up to MAX_FILE_SIZE_MB

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;      # WebSocket
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;                      # long AI turns
    }
}
```

Set `PROXY_COUNT=1` in `.env` so FastAPI trusts `X-Forwarded-*`.

**Frontend:** `npm run build` in `frontend/`, set `REACT_APP_API_URL=https://<host>`
at build time, upload `build/` to S3, serve via CloudFront.

---

## 7. Mandatory measurement before go-live

```bash
# Peak RAM + CPU under load
docker stats negotiateai
# Expect Path A peak < ~1.2 GB on a 1 GB box → upgrade if it OOMs.
```

Do NOT run `--workers 2`. Each worker loads its own copy of PyTorch + the model.

---

## 8. Rollback

```bash
# Keep the previous image tag
docker tag negotiateai:local negotiateai:prev
# Roll back:
sudo docker stop negotiateai && sudo docker rm negotiateai
sudo docker run -d --name negotiateai --restart unless-stopped \
  --env-file /etc/negotiateai/.env -p 127.0.0.1:8000:8000 negotiateai:prev
```

DB rollback (Alembic): `alembic downgrade -1` — but confirm the revision first.

---

## 9. Backup

- **DB:** Supabase manages backups, but export weekly:
  `pg_dump "$DATABASE_URL" > backup_$(date +%F).sql`
- **Uploads:** if using S3, versioning on; if on-disk, snapshot the EBS volume.
- **Env:** store `/etc/negotiateai/.env` in a secrets manager — never in git.

---

## 10. Cost-safety checklist

- [ ] One t3.micro/t4g.micro, one worker.
- [ ] No NAT Gateway, no ALB, no RDS.
- [ ] Elastic IP **attached** (release when stopped).
- [ ] CloudWatch billing alarm at a low threshold (e.g. $1).
- [ ] Tag every resource: `project=negotiateai`.
- [ ] Stop the instance when not in use (stop ≠ delete; EBS still bills).
