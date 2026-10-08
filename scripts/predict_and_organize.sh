#!/usr/bin/env bash
# 전체 조합 test 예측이 성공하면 GT + 모델별 열 Excel을 이어서 생성합니다.
set -euo pipefail
if [[ $# -eq 0 || ${1:-} == --help ]]; then
  echo "사용법: bash scripts/predict_and_organize.sh TRAIN_DIR [새_OUTPUT_DIR] [--id-tolerance N]"
  echo "예: bash scripts/predict_and_organize.sh results/train/20261006_095933 --id-tolerance 2"
  if [[ ${1:-} == --help ]]; then exit 0; else exit 2; fi
fi
HRM_PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
HRM_TRAIN_DIR="$1"
shift
HRM_PREDICT_OUTPUT="$HRM_PROJECT_DIR/results/predict/$(date +%Y%m%d_%H%M%S)"
if [[ $# -gt 0 && $1 != --* ]]; then
  HRM_PREDICT_OUTPUT="$1"
  shift
fi
HRM_ORGANIZE_ARGS=()
if [[ $# -gt 0 ]]; then
  if [[ $# -ne 2 || $1 != --id-tolerance || ! ${2:-} =~ ^([0-9]|1[0-7])$ ]]; then
    echo "인자 오류: TRAIN_DIR [새_OUTPUT_DIR] [--id-tolerance N], N은 0–17 정수입니다." >&2
    exit 2
  fi
  HRM_ORGANIZE_ARGS=(--id-tolerance "$2")
fi
bash "$HRM_PROJECT_DIR/scripts/hrm_python.sh" "$HRM_PROJECT_DIR/predict.py" \
  --train-dir "$HRM_TRAIN_DIR" --output "$HRM_PREDICT_OUTPUT"
bash "$HRM_PROJECT_DIR/scripts/hrm_python.sh" "$HRM_PROJECT_DIR/organize_results.py" \
  "$HRM_PREDICT_OUTPUT/predictions.xlsx" "${HRM_ORGANIZE_ARGS[@]}"
