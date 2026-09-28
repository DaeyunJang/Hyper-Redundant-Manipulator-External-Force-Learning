#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
HRM_PYTHON="${HRM_PYTHON:-/home/daeyun/HRM_env/bin/python}"
HRM_RUN="${1:?Usage: bash scripts/predict_all.sh results/YYYYMMDD_HHMMSS}"
for task in tip body; do
  "$HRM_PYTHON" -u predict.py --run "$HRM_RUN/$task" --device cuda
 done
"$HRM_PYTHON" scripts/summarize_results.py "$HRM_RUN"
"$HRM_PYTHON" scripts/check_results.py "$HRM_RUN"
