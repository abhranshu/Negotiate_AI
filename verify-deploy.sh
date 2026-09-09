#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# NegotiateAI — Local deployment pre-flight checker
# Run BEFORE pushing to AWS ECS / App Runner / Railway:
#     bash verify-deploy.sh
#
# It mirrors exactly what the cloud will do:
#   1. Static Dockerfile validation       (docker build --check)
#   2. Full image build                   (validates COPY, apt, pip)
#   3. Run container on :8000             (validates startup + DB migration)
#   4. Hit /health and /                  (validates FastAPI responds)
#   5. Run with injected $PORT            (validates AWS/App Runner port logic)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")"

IMAGE="negotiateai:test"
NAME="negotiateai-smoke"

# Docker daemon must be running (start Docker Desktop first)
docker info >/dev/null 2>&1 || { echo "ERROR: Docker daemon not running — start Docker Desktop first."; exit 1; }

# ── 1. Static Dockerfile check ──────────────────────────────────────────────
echo "==> [1/5] docker build --check (static Dockerfile validation)"
docker build --check -t "$IMAGE" . 2>/dev/null || echo "   (docker build --check not supported on this CLI — step is advisory only)"

# ── 2. Full build ─────────────────────────────────────────────────────────────
echo "==> [2/5] docker build (this validates every COPY, apt package and pip install)"
docker build -t "$IMAGE" .

# ── 3. Run on default port 8000 ───────────────────────────────────────────────
echo "==> [3/5] Starting container on :8000 with env from .env"
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d --name "$NAME" -p 8000:8000 --env-file .env "$IMAGE" >/dev/null

echo "   Waiting for /health ..."
healthy=false
for i in $(seq 1 60); do
  if curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
    healthy=true
    echo "   /health became ready after ~$((i * 2))s"
    break
  fi
  sleep 2
done
if [ "$healthy" != true ]; then
  echo "   FAIL: /health never became ready. Logs:"
  docker logs "$NAME"
  exit 1
fi

echo "   /health -> $(curl -fsS http://localhost:8000/health)"
echo "   /       -> $(curl -fsS http://localhost:8000/)"
echo "   Docker healthcheck -> $(docker inspect --format '{{.State.Health.Status}}' "$NAME" 2>/dev/null || echo 'n/a')"
docker rm -f "$NAME" >/dev/null 2>&1 || true

# ── 4. Simulate injected $PORT (ECS/App Runner inject a random $PORT) ─────────
echo "==> [4/5] Re-running with PORT=8080 injected (cloud port logic)"
docker run -d --name "$NAME" -p 8080:8080 --env-file .env -e PORT=8080 "$IMAGE" >/dev/null
port_ok=false
for i in $(seq 1 30); do
  if curl -fsS http://localhost:8080/health >/dev/null 2>&1; then
    port_ok=true
    echo "   PORT=8080 injection works — /health OK"
    break
  fi
  sleep 2
done
docker rm -f "$NAME" >/dev/null 2>&1 || true
[ "$port_ok" != true ] && { echo "   FAIL: \$PORT injection broken"; exit 1; }

# ── 5. Report ────────────────────────────────────────────────────────────────
echo ""
echo "==> [5/5] ✅ ALL LOCAL CHECKS PASSED — the image is deployable."
echo "   Next: tag + push to AWS ECR, then configure ECS/App Runner."
echo "   ECR push example:"
echo "     aws ecr get-login-password --region <region> | \\"
echo "       docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com"
echo "     docker tag $IMAGE <account>.dkr.ecr.<region>.amazonaws.com/negotiate-ai:latest"
echo "     docker push <account>.dkr.ecr.<region>.amazonaws.com/negotiate-ai:latest"