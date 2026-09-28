# 실행 환경

확인일: 2026-09-26 (Asia/Seoul)

기존 `/home/daeyun/HRM_env`를 기본 환경으로 사용한다. 기존 환경을 재생성하거나
패키지를 설치/변경하지 않았다. 현재 데이터 분석용 기본 패키지는 사용 가능하지만,
PyTorch 기반 학습 환경 준비는 아직 완료되지 않았다.

```bash
source /home/daeyun/HRM_env/bin/activate
python --version
python -m pip check
```

자동 실행에서는 `/home/daeyun/HRM_env/bin/python`을 직접 사용한다.

| 항목 | 검사 결과 |
|---|---|
| Python | 3.10.12 |
| NumPy | 1.26.4 |
| pandas | 2.3.1 |
| SciPy | 1.14.1 |
| scikit-learn | 1.7.0 |
| Matplotlib | 3.5.1 |
| PyYAML | 5.4.1 |
| pytest | 6.2.5 |
| PyTorch | 미설치 (`ModuleNotFoundError`) |
| pip check | No broken requirements found. |

표에 있는 설치된 모듈은 실제 import에 성공했다. PyTorch가 없어 CUDA 접근과
GPU 연산은 검사하지 못했다. 모델 학습이나 데이터 분석은 실행하지 않았다.
`include-system-site-packages = true`인 기존 환경이므로 시스템 패키지도 참조한다.
환경 전체의 재현성이 확보된 lock 파일은 아직 없다.

추가 문서와 구현 요구를 확인한 뒤 PyTorch 버전 및 GPU 호환성을 확인하고
필요 의존성을 준비한다.

## 2026-09-26 학습 준비 완료

사용자 승인 후 기존 HRM_env에 PyTorch 2.7.1+cu126 및 해당 CUDA 런타임 의존성을
설치했다. NVIDIA GeForce RTX3060 12GB, 드라이버570.195.03에서 GPU tensor
forward/backward 성공. 설치 후 pip check 통과. 설치 명령은 다음과 같다.

```bash
/home/daeyun/HRM_env/bin/python -m pip install 'torch==2.7.1' --index-url https://download.pytorch.org/whl/cu126
```

기존 시스템 패키지는 제거하지 않았다. 결과 폴더에 pip_freeze.txt와 environment.json을
저장한다. 상단 표는 최초 점검 당시 기록이며 PyTorch 미설치 제한은 현재 해소됐다.
