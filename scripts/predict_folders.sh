#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
HRM_PYTHON="${HRM_PYTHON:-/home/daeyun/HRM_env/bin/python}"
HRM_RUN="${1:?Usage: bash scripts/predict_folders.sh results/training_run [results/new_prediction]}"
HRM_OUTPUT="${2:-results/$(date +%Y%m%d_%H%M%S)_testsets}"
"$HRM_PYTHON" -u predict.py --run "$HRM_RUN" --test-root datasets/testsets \
  --output "$HRM_OUTPUT" --device "${HRM_DEVICE:-cpu}"
