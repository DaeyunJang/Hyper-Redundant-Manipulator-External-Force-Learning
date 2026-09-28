#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
HRM_PYTHON="${HRM_PYTHON:-/home/daeyun/HRM_env/bin/python}"
HRM_TASK="${1:-tip}"
case "$HRM_TASK" in tip|body) ;; *) echo 'Usage: bash scripts/train_folders.sh [tip|body] [results/new_run]' >&2; exit 2;; esac
HRM_RUN="${2:-results/$(date +%Y%m%d_%H%M%S)_${HRM_TASK}_folders}"
"$HRM_PYTHON" -u train.py --config "configs/${HRM_TASK}_force_folders.json" \
  --output "$HRM_RUN" --models all
