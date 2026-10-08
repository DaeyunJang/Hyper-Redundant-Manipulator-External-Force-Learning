#!/usr/bin/env bash
set -euo pipefail
HRM_PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
HRM_LOADED_DRIVER="$(sed -n 's/.*Module for x86_64  \([0-9.]*\).*/\1/p' /proc/driver/nvidia/version 2>/dev/null || true)"
HRM_LOCAL_DRIVER="$HRM_PROJECT_DIR/.runtime/nvidia-$HRM_LOADED_DRIVER"
if [[ -n "$HRM_LOADED_DRIVER" && -f "$HRM_LOCAL_DRIVER/libcuda.so.1" ]]; then
  export LD_LIBRARY_PATH="$HRM_LOCAL_DRIVER${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
exec "$HRM_PROJECT_DIR/env_hrm_force_estimation/bin/python" "$@"
