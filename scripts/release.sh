#!/usr/bin/env bash
set -Eeuo pipefail

: "${NAMESPACE:?NAMESPACE is required}"
: "${DEPLOYMENT:?DEPLOYMENT is required}"
: "${CONTAINER:?CONTAINER is required}"
: "${IMAGE:?IMAGE is required and should be pinned by digest}"

ROLLOUT_TIMEOUT="${ROLLOUT_TIMEOUT:-5m}"
PROMETHEUS_URL="${PROMETHEUS_URL:-}"
ERROR_RATE_QUERY="${ERROR_RATE_QUERY:-}"
MAX_ERROR_RATE="${MAX_ERROR_RATE:-0.02}"

rollback() {
  echo "Release gate failed; rolling back ${NAMESPACE}/${DEPLOYMENT}" >&2
  kubectl -n "$NAMESPACE" rollout undo "deployment/$DEPLOYMENT"
  kubectl -n "$NAMESPACE" rollout status "deployment/$DEPLOYMENT" --timeout="$ROLLOUT_TIMEOUT"
}
trap rollback ERR

kubectl -n "$NAMESPACE" set image "deployment/$DEPLOYMENT" "$CONTAINER=$IMAGE"
kubectl -n "$NAMESPACE" annotate "deployment/$DEPLOYMENT" \
  "deploypilot.io/released-at=$(date -u +%FT%TZ)" \
  "deploypilot.io/commit=${GIT_COMMIT:-unknown}" --overwrite
kubectl -n "$NAMESPACE" rollout status "deployment/$DEPLOYMENT" --timeout="$ROLLOUT_TIMEOUT"

if [[ -n "$PROMETHEUS_URL" && -n "$ERROR_RATE_QUERY" ]]; then
  value="$(curl --fail --silent --get "$PROMETHEUS_URL/api/v1/query" --data-urlencode "query=$ERROR_RATE_QUERY" | python -c 'import json,sys; d=json.load(sys.stdin); print(d["data"]["result"][0]["value"][1] if d["data"]["result"] else 0)')"
  python - "$value" "$MAX_ERROR_RATE" <<'PY'
import sys
actual, maximum = map(float, sys.argv[1:])
if actual > maximum:
    raise SystemExit(f"error-rate gate failed: {actual:.4f} > {maximum:.4f}")
print(f"error-rate gate passed: {actual:.4f} <= {maximum:.4f}")
PY
fi

trap - ERR
echo "Release verified: ${NAMESPACE}/${DEPLOYMENT} -> ${IMAGE}"
