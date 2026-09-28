#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
HRM_PYTHON="${HRM_PYTHON:-/home/daeyun/HRM_env/bin/python}"
HRM_CONFIG="${1:?Usage: bash scripts/fine_tune.sh config.json checkpoint.pt new_result_folder}"
HRM_CHECKPOINT="${2:?Parent checkpoint is required}"
HRM_OUTPUT="${3:?A new result folder is required}"
HRM_MODEL="$("$HRM_PYTHON" -c 'import sys,torch; print(torch.load(sys.argv[1],map_location="cpu",weights_only=True)["model"])' "$HRM_CHECKPOINT")"
"$HRM_PYTHON" -u train.py --config "$HRM_CONFIG" --output "$HRM_OUTPUT" --models "$HRM_MODEL" --init-checkpoint "$HRM_CHECKPOINT"
"$HRM_PYTHON" -u predict.py --run "$HRM_OUTPUT" --device cuda
