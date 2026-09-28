#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
HRM_PYTHON="${HRM_PYTHON:-/home/daeyun/HRM_env/bin/python}"
HRM_RUN="${1:-results/$(date +%Y%m%d_%H%M%S)}"
mkdir -p "$HRM_RUN"
"$HRM_PYTHON" -u train.py --config configs/tip_force.json --output "$HRM_RUN/tip" --resume 2>&1 | tee "$HRM_RUN/tip_train.log"
"$HRM_PYTHON" -u predict.py --run "$HRM_RUN/tip" --device cuda 2>&1 | tee "$HRM_RUN/tip_predict.log"
"$HRM_PYTHON" -u train.py --config configs/body_force.json --output "$HRM_RUN/body" --resume 2>&1 | tee "$HRM_RUN/body_train.log"
"$HRM_PYTHON" -u predict.py --run "$HRM_RUN/body" --device cuda 2>&1 | tee "$HRM_RUN/body_predict.log"
"$HRM_PYTHON" scripts/summarize_results.py "$HRM_RUN"
"$HRM_PYTHON" scripts/check_results.py "$HRM_RUN"
