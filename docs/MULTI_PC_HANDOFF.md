# 다른 로컬 PC로 작업 인계

갱신: 2026-09-28. 이 문서는 파일/환경을 옮기는 방법이며 실제 전송을 수행한 기록은 아니다.

## 전달할 파일

| 대상 | 전달 목적 |
| --- | --- |
| 루트 AGENTS.md, CODEX_HANDOFF.md, docs/ 전체 | 작업 규칙, 최신 결정/미완료, 대화별 이력 |
| hrm_force/, configs/, scripts/, tests/, train.py, predict.py, model_zoo.py, requirements.txt, README.md, .gitignore | 구현과 재현 가능한 설정/검증 |
| datasets/의 필요한 녹화 폴더 전체 | 학습 및 평가 원본, 메타데이터/시간 복원에 필요한 토픽 CSV 포함 |
| results/의 사용할 실험 폴더 | 학습된 체크포인트, config/scaler/audit, 분할/성능/부모 이력 |

2026-09-28 확인 시 위 문서와 코드 상당수는 Git 미추적이었다. 파일이 현재 PC에 있다는
것과 원격 저장소에 있다는 것은 다르다. Git으로 전달할 경우 필요한 코드/문서가 실제
커밋·전달되었는지 확인한다. 이번 문서 작업에서 commit/push는 실행하지 않았다.
`datasets/`, `results/`는 .gitignore 대상이므로 별도 파일 복사가 필요하다.

가장 단순한 파일 인계는 저장소 작업 폴더와 필요한 데이터/실험 폴더를 함께 복사하는 것이다.
심볼릭 링크는 링크 대상이 옛 PC의 절대경로를 가리키는지 확인한다. 특히 과거
results/20260926_tip_body_v1/data_replay/에는 원본을 참조하는 링크가 있을 수 있다.
CSV를 다시 저장하거나 줄바꿈/메타데이터를 바꾸면 기존 체크포인트 hash 검사에 걸릴 수 있다.
데이터가 바뀌었다는 검사를 PC 이전 문제라고 생각하고 비활성화하지 않는다.

## 새 PC에서 읽을 내용

저장소 루트를 작업 폴더로 열고 다음 요청으로 시작할 수 있다.

> AGENTS.md와 CODEX_HANDOFF.md의 현재 요약, docs/WORK_LOG.md의 최신 기록을 읽어줘.
> docs/MULTI_PC_HANDOFF.md를 따라 이 PC의 Python 환경과 데이터/체크포인트 경로를 확인해줘.
> 실제 학습은 시작하지 말고 현재 상태와 다음 작업부터 알려줘.

AGENTS는 핵심 규칙, HANDOFF는 현재 상태와 과거 인계, WORK_LOG는 대화별 상세 기록이다.
새 세션에서 이전 대화가 제공된다고 가정하지 않고 파일의 기록을 사용한다.
Codex는 시작 시 프로젝트의 AGENTS.md를 지침으로 읽는다. 파일을 새로 옮기거나 바꾼 뒤에는
새 세션에서 확인한다. [OpenAI 공식 AGENTS.md 안내](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

## Python 환경

이 PC의 기준은 Python3.10.12, PyTorch2.7.1+cu126, RTX3060이었다. 다른 PC에서는 해당
Python 경로나 GPU를 가정하지 않는다. 설치는 현지 환경에 맞춰 진행하고 requirements.txt와
실험 폴더 pip_freeze.txt/environment.json을 참고한다. 기존 HRM_env는 system-site-packages도
사용했던 환경이라 requirements.txt만으로 모든 OS/GPU에서 동일 환경이 된다는 보장은 없다.

현지 가상환경을 준비한 뒤 Linux/bash 기준 다음처럼 사용한다. 경로는 실제 현지 값으로 바꾼다.

```bash
export HRM_PYTHON="/실제/가상환경/bin/python"
"$HRM_PYTHON" --version
"$HRM_PYTHON" -m pip check
"$HRM_PYTHON" -c 'import torch, numpy, pandas, matplotlib; print(torch.__version__, torch.cuda.is_available())'
"$HRM_PYTHON" -m unittest discover -s tests -v
```

새 PC에 Python3.10이 있고 새 환경을 만들기로 한 경우 `python3.10 -m venv /새/환경경로`를
사용할 수 있다. 설치 패키지와 GPU용 wheel은 현지 Python/OS/드라이버 호환성을 확인해 정한다.
가상환경 폴더를 그대로 복사해서 정상 작동한다고 가정하지 않는다. Windows에서는 실제 Python
실행 파일로 CLI를 직접 실행하거나 해당 .sh를 실행할 수 있는 bash 환경을 준비한다.

## 데이터 및 모델 경로

- 새 학습 입구는 configs/{tip,body}_force_folders.json. data_root=datasets가 저장소 루트
  기준으로 해석된다. DATASET_FOLDERS.md를 따라 trainsets/testsets에 녹화 전체를 배치한다.
- 2026-09-28 확인 시 trainsets의 sine-35deg-both_seg-id-18_right는 과거test여서 학습 준비가
  차단되었다. 새 PC에서 배치를 재확인하고 heldout 역할을 유지한다. 이번 작업에서 이동하지 않았다.
- 과거 날짜별 데이터 경로는 현재 폴더 배치와 다를 수 있다. 과거 config/체크포인트를
  덮어쓰지 않고, 새 학습에는 새 설정/결과 경로를 사용한다.
- 데이터 검사만: `"$HRM_PYTHON" train.py --config configs/tip_force_folders.json --output results/new_check --prepare-only`.
- 기존 모델에 새로운 testsets 평가: `predict.py --checkpoint 실제/checkpoint.pt --test-root datasets/testsets --output results/new_test`.
  이 기능은 학습 당시 원본의 절대경로 없이도 평가할 수 있지만 학습 이력/메타데이터 검사는 유지한다.
- 동일한 과거 데이터 재평가는 `--data-root`가 재배치 옵션이다. 목록 구조/바이트/복원 출처가
  맞아야 하며 이것을 다른 새 데이터를 넣는 옵션으로 쓰지 않는다. 경로가 담긴 과거 복원 출처
  때문에 검사가 실패할 수 있으므로 진단 없이 모든 hash 검사를 해제하지 않는다.
- 최소 checkpoint.pt만 복사하기보다 실험 폴더를 함께 복사한다. 특히 옛 checkpoint는
  부모 디렉터리의 dataset_audit.json으로 train/val/test 이력을 확인하는 경우가 있다.
- 초기 결과: results/20260926_tip_body_v1/{tip,body}/<model>/checkpoint.pt.
- front 추가학습: results/20260927_tip_front_finetune_v1/runs/<model>/<model>/checkpoint.pt.
  해당 RESULTS.md, selection.json, audit 및 부모 결과도 함께 보존한다.

## 현재 대기 중인 연구 작업

새 데이터 제공 후 초기 ID의 관측 반응/학습 지원 범위 비교 → 끝단 힘 개선 및 위치 전용
모델/세 구간 평가를 진행한다. 현재 body 공동 모델을 위치/힘 분리 모델로 오인하지 않는다.
무부하 실측값 보존, set-zero 누락 행/포함창 제외, 제어 시 XYZ에 -1 적용 등 합의는 AGENTS 참조.
성능 수치와 한계는 HANDOFF 현재 요약 및 실험 RESULTS.md를 따른다.

다른 PC에서 작업해도 매 요청의 WORK_LOG와 중요한 결정의 HANDOFF/AGENTS를 함께 갱신하고
다음 PC로 전달한다. 같은 결과 폴더를 여러 PC에서 동시에 덮어쓰지 않도록 새 실험명을 쓴다.
