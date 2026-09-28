#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 || $# -gt 3 ]]; then
  echo "Usage: $0 NEW_OUTPUT [CONFIG] [PARENT_TIP_RUN]" >&2
  exit 2
fi
PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
HRM_PYTHON="${HRM_PYTHON:-/home/daeyun/HRM_env/bin/python}"
cd -- "$PROJECT_ROOT"
exec "$HRM_PYTHON" scripts/fine_tune_all.py \
  --output "$1" \
  --config "${2:-configs/tip_front_finetune_20260927.json}" \
  --parents "${3:-results/20260926_tip_body_v1/tip}"
