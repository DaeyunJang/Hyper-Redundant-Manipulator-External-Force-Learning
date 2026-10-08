#!/usr/bin/env bash
set -euo pipefail
HRM_PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HRM_PROJECT_DIR"
uv python install 3.10
if [[ ! -x env_hrm_force_estimation/bin/python ]]; then
  uv venv --python 3.10 env_hrm_force_estimation
fi
uv pip install --python env_hrm_force_estimation/bin/python torch==2.7.1 --index-url https://download.pytorch.org/whl/cu126
uv pip install --python env_hrm_force_estimation/bin/python -r requirements.txt
uv pip check --python env_hrm_force_estimation/bin/python
bash scripts/hrm_python.sh -c 'import torch; print("PyTorch:", torch.__version__, "CUDA available:", torch.cuda.is_available())'
