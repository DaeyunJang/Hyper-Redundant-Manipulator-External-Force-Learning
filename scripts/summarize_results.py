#!/usr/bin/env python3
"""학습/테스트 비교 CSV를 합치고 validation 선택 기준의 한국어 보고서를 만든다."""
from __future__ import annotations

import argparse
from datetime import datetime
import os
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


PHASES = (("tip", "끝단 전용 모델"), ("body", "ID1~18 힘·위치 모델"))
KEY_METRICS = (
    "force_rmse_mN", "fx_rmse_mN", "fy_rmse_mN", "fz_rmse_mN", "vector_mae_mN",
    "load_f1", "load_false_positive_rate", "load_false_negative_rate",
    "location_accuracy_loaded", "location_gated_accuracy_loaded", "end_to_end_id_accuracy",
)


def read_comparison(path: Path, warnings: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["model"])
    try:
        frame = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        warnings.append(f"{path.parent.name}/{path.name}: 빈 파일이어서 제외했습니다.")
        return pd.DataFrame(columns=["model"])
    if "model" not in frame:
        raise ValueError(f"{path}: model 열이 없습니다.")
    if frame["model"].isna().any() or frame["model"].duplicated().any():
        raise ValueError(f"{path}: model은 결측 없이 한 모델당 한 행이어야 합니다.")
    return frame


def combine_phase(root: Path, phase: str) -> tuple[pd.DataFrame, list[str]]:
    warnings: list[str] = []
    training = read_comparison(root / phase / "training_comparison.csv", warnings)
    test = read_comparison(root / phase / "test_comparison.csv", warnings)
    if training.empty and test.empty:
        return pd.DataFrame(), warnings
    training_by_name = training.set_index("model")
    test_by_name = test.set_index("model")
    rows = []
    for model in sorted(set(training_by_name.index) | set(test_by_name.index)):
        # Checkpoint training statistics take precedence over repeated test-file metadata.
        # Test force/error/classification metrics never select the model.
        row = test_by_name.loc[model].to_dict() if model in test_by_name.index else {}
        if model in training_by_name.index:
            row.update(training_by_name.loc[model].to_dict())
        row.update({"phase": phase, "model": model,
                    "has_training_summary": model in training_by_name.index,
                    "has_test_metrics": model in test_by_name.index})
        per_id_path = root / phase / model / "test_predictions" / "per_id_metrics.csv"
        if per_id_path.exists():
            per_id = pd.read_csv(per_id_path)
            if "true_id" in per_id:
                tip_rows = per_id.loc[pd.to_numeric(per_id["true_id"], errors="coerce") == 18]
                if len(tip_rows) == 1:
                    for key in ("location_accuracy_loaded", "location_gated_accuracy_loaded", "location_n_loaded"):
                        row["id18_" + key] = tip_rows.iloc[0].get(key, np.nan)
        rows.append(row)
    frame = pd.DataFrame(rows)
    if "validation_loss" not in frame:
        frame["validation_loss"] = np.nan
    frame["validation_loss"] = pd.to_numeric(frame["validation_loss"], errors="coerce")
    frame["selected_by_validation"] = False
    finite = np.isfinite(frame["validation_loss"])
    if finite.any():
        # Alphabetical order resolves exactly equal validation losses reproducibly.
        best = frame.loc[finite].sort_values(["validation_loss", "model"], kind="stable").index[0]
        frame.loc[best, "selected_by_validation"] = True
        frame["validation_rank"] = frame["validation_loss"].where(finite).rank(method="min")
    else:
        frame["validation_rank"] = np.nan
        warnings.append(f"{phase}: 유한한 validation_loss가 없어 모델을 선택하지 않았습니다.")
    if training.empty:
        warnings.append(f"{phase}: training_comparison.csv가 없어 test CSV의 체크포인트 validation_loss만 사용했습니다. 전체 학습 모델의 완료 여부를 확인할 수 없습니다.")
    missing_test = int((~frame["has_test_metrics"]).sum())
    if missing_test:
        warnings.append(f"{phase}: 학습 결과가 있는 모델 중 {missing_test}개는 test 결과가 아직 없습니다.")
    return frame.sort_values(["validation_loss", "model"], na_position="last", kind="stable"), warnings


def number(value, digits: int = 2, percent: bool = False) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "—"
    if not np.isfinite(numeric):
        return "—"
    return f"{numeric * 100:.{digits}f}%" if percent else f"{numeric:.{digits}f}"


def metric(row: pd.Series, key: str, digits: int = 2, percent: bool = False) -> str:
    return number(row.get(key, np.nan), digits, percent)


def table(frame: pd.DataFrame, phase: str) -> list[str]:
    columns = ["모델", "Validation loss", "Test XYZ RMSE (mN)", "Fx / Fy / Fz RMSE (mN)", "하중 F1"]
    if phase == "body":
        columns += ["조건부 위치 정확도", "하중 판정 포함 위치 정확도"]
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in frame.iterrows():
        name = str(row["model"]) + (" **(선택)**" if row["selected_by_validation"] else "")
        values = [name, metric(row, "validation_loss", 5), metric(row, "force_rmse_mN"),
                  " / ".join(metric(row, f"f{axis}_rmse_mN") for axis in "xyz"), metric(row, "load_f1", 3)]
        if phase == "body":
            values += [metric(row, "location_accuracy_loaded", 1, True),
                       metric(row, "location_gated_accuracy_loaded", 1, True)]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def selected_report(row: pd.Series, phase: str, root: Path) -> list[str]:
    name = str(row["model"])
    lines = [f"Validation loss로 선택한 모델은 **{name}**입니다 "
             f"(loss {metric(row, 'validation_loss', 5)}, best epoch {metric(row, 'best_epoch', 0)})."]
    if not row["has_test_metrics"]:
        lines.append("이 모델의 test 평가는 아직 완료되지 않았습니다. 다른 모델의 test 성능으로 선택을 바꾸지 않았습니다.")
        return lines
    lines.append(
        f"고정한 test의 XYZ 성분 RMSE는 **{metric(row, 'force_rmse_mN')} mN**, "
        f"Fx/Fy/Fz RMSE는 **{metric(row, 'fx_rmse_mN')} / {metric(row, 'fy_rmse_mN')} / {metric(row, 'fz_rmse_mN')} mN**입니다. "
        f"평균 3D 벡터 오차는 {metric(row, 'vector_mae_mN')} mN이며, "
        f"평가 표본은 {metric(row, 'n_samples', 0)}개입니다.")
    lines.append(
        f"힘 임계값으로 판단한 하중 F1은 {metric(row, 'load_f1', 3)}, "
        f"무부하 오경보율은 {metric(row, 'load_false_positive_rate', 1, True)}, "
        f"유부하 미검출률은 {metric(row, 'load_false_negative_rate', 1, True)}입니다. "
        f"별도 load head F1은 {metric(row, 'load_head_f1', 3)}입니다.")
    if phase == "body":
        conditional_key = "id18_location_accuracy_loaded" if "id18_location_accuracy_loaded" in row else "location_accuracy_loaded"
        gated_key = "id18_location_gated_accuracy_loaded" if "id18_location_gated_accuracy_loaded" in row else "location_gated_accuracy_loaded"
        lines.append(
            f"실제 유부하 ID18 표본에서 **조건부 ID18 정확도는 {metric(row, conditional_key, 1, True)}**, "
            f"하중을 놓친 경우도 실패로 세는 **ID18 정확도는 {metric(row, gated_key, 1, True)}**입니다. "
            f"무부하의 기대 ID0까지 포함한 전체 출력 ID 정확도는 {metric(row, 'end_to_end_id_accuracy', 1, True)}입니다.")
        lines.append("이 test는 ID18 한 녹화이므로, ID1~17의 독립적인 위치 식별 성능이나 전체 위치 일반화를 입증하지 않습니다.")
    else:
        lines.append("끝단 전용 모델은 조건부 ID를 항상 18로 고정합니다. 이 모델의 ID18 일치는 학습된 위치 식별 성능이 아닙니다. 무부하 표시 ID는 0입니다.")
    lines.append(
        f"CPU 배치1 forward 지연 p50/p95/p99는 {metric(row, 'cpu_forward_p50_ms', 3)} / "
        f"{metric(row, 'cpu_forward_p95_ms', 3)} / {metric(row, 'cpu_forward_p99_ms', 3)} ms입니다. "
        "전처리·센서·버퍼링·기존 필터의 지연을 포함한 전체 지연은 아닙니다.")
    artifact = f"{phase}/{name}/test_predictions"
    lines.append(f"예측 CSV: [{name}]({artifact}/predictions.csv), "
                 f"[힘 곡선]({artifact}/force_timeseries.png), [하중 곡선]({artifact}/load_timeseries.png), "
                 f"[ID 혼동행렬]({artifact}/confusion.csv).")
    return lines


def plot_comparison(phase_frames: dict[str, pd.DataFrame], root: Path) -> None:
    """Plot fixed test metrics in validation order; missing results stay missing."""
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    normal_color, selected_color = "#4C78A8", "#E17827"

    def values(frame: pd.DataFrame, key: str) -> np.ndarray:
        if key not in frame:
            return np.full(len(frame), np.nan)
        return pd.to_numeric(frame[key], errors="coerce").to_numpy(dtype=float)

    def prepare_axis(ax, frame: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
        positions = np.arange(len(frame))
        names = [str(row["model"]) + (" *" if row["selected_by_validation"] else "")
                 for _, row in frame.iterrows()]
        colors = [selected_color if selected else normal_color
                  for selected in frame["selected_by_validation"]]
        ax.set_xticks(positions)
        ax.set_xticklabels(names, rotation=25, ha="right")
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
        return positions, colors

    for ax, phase in zip(axes[:2], ("tip", "body")):
        frame = phase_frames[phase]
        ax.set_title(f"{phase.upper()}: fixed-test XYZ component RMSE (lower is better)")
        error = values(frame, "force_rmse_mN")
        if frame.empty or not np.isfinite(error).any():
            ax.text(0.5, 0.5, "No test force results yet", transform=ax.transAxes,
                    ha="center", va="center", color="gray")
            ax.set_xticks([])
        else:
            positions, colors = prepare_axis(ax, frame)
            ax.bar(positions, error, color=colors, width=0.7)
            ax.set_ylim(bottom=0)
            for position, height in zip(positions, error):
                if np.isfinite(height):
                    ax.annotate(f"{height:.1f}", (position, height), xytext=(0, 3),
                                textcoords="offset points", ha="center", fontsize=8)
            ax.margins(y=0.15)
        ax.set_ylabel("RMSE [mN]")

    ax = axes[2]
    frame = phase_frames["body"]
    conditional = values(frame, "location_accuracy_loaded") * 100.0
    gated = values(frame, "location_gated_accuracy_loaded") * 100.0
    ax.set_title("BODY: location accuracy on true loaded test rows (higher is better)")
    if frame.empty or not (np.isfinite(conditional).any() or np.isfinite(gated).any()):
        ax.text(0.5, 0.5, "No test location results yet", transform=ax.transAxes,
                ha="center", va="center", color="gray")
        ax.set_xticks([])
    else:
        positions, colors = prepare_axis(ax, frame)
        ax.bar(positions - 0.19, conditional, width=0.36, color=colors)
        ax.bar(positions + 0.19, gated, width=0.36, color=colors,
               alpha=0.5, hatch="//", edgecolor="black", linewidth=0.4)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Accuracy [%]")
    ax.legend(handles=[Patch(facecolor=normal_color, label="Conditional location"),
                       Patch(facecolor=normal_color, alpha=0.5, hatch="//", edgecolor="black",
                             label="Location after load gating"),
                       Patch(facecolor=selected_color, label="Selected by validation loss (*)")],
              loc="upper right", fontsize=8)
    fig.suptitle("HRM model comparison | model order follows validation loss", fontsize=14)
    fig.text(0.5, 0.008,
             "Orange / * = validation-selected model; test metrics do not select the model. "
             "Tip ID18 is fixed, not learned.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.025, 1, 0.97))
    fig.savefig(root / "comparison.png", dpi=140)
    plt.close(fig)


def extended_report(root: Path, parent: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Keep optional continuation separate from the original 22-model comparison."""
    extended, warnings = combine_phase(root, "tip_extended")
    if extended.empty:
        return [], warnings
    parent_selected = parent.loc[parent["selected_by_validation"]].copy() if not parent.empty else pd.DataFrame()
    if not parent_selected.empty:
        parent_selected["comparison_role"] = "parent_validation_selected"
    extended = extended.copy()
    extended["comparison_role"] = "continued_training"
    parts = [frame for frame in (parent_selected, extended) if not frame.empty]
    comparison = pd.concat(parts, ignore_index=True, sort=False)
    comparison.to_csv(root / "extended_comparison.csv", index=False)
    lines = ["## 끝단 선택 모델 추가 학습", "",
             "추가 학습은 최초 11개 끝단/11개 body 비교와 분리해 기록했습니다. "
             "기존 비교표와 막대그래프의 모델 선택·정렬에는 후속 실험을 합치지 않습니다.", "",
             "| 실험 | 모델 | 실제 실행 epoch | 선택 epoch | Validation loss | Test XYZ RMSE (mN) |",
             "| --- | --- | --- | --- | --- | --- |"]
    for _, row in comparison.iterrows():
        label = "부모 실험" if row["comparison_role"] == "parent_validation_selected" else "추가 학습"
        lines.append(f"| {label} | {row['model']} | {metric(row, 'epochs_run', 0)} | "
                     f"{metric(row, 'best_epoch', 0)} | {metric(row, 'validation_loss', 6)} | "
                     f"{metric(row, 'force_rmse_mN')} |")
    lines.append("")
    for _, row in extended.iterrows():
        name = str(row["model"])
        if pd.notna(row.get("warm_start_checkpoint")):
            lines.extend([f"**{name}는 실제 {metric(row, 'epochs_run', 0)} epoch를 추가 실행했습니다.** "
                          "부모 체크포인트에서 시작하고 부모의 입력/힘 scaler를 고정했습니다.", ""])
            if row.get("best_epoch") == 0:
                lines.extend(["**선택 epoch 0은 추가 학습을 하지 않았다는 뜻이 아닙니다.** "
                              "추가 학습의 validation loss가 시작 체크포인트보다 개선되지 않아, "
                              "시작 가중치를 최종 결과로 유지했다는 뜻입니다. "
                              f"시작/최종 validation loss는 {metric(row, 'initial_validation_loss', 8)} / "
                              f"{metric(row, 'validation_loss', 8)}입니다.", ""])
        artifact = f"tip_extended/{name}"
        lines.extend([f"[{name} 학습 이력]({artifact}/history.csv) · "
                      f"[학습 메타데이터]({artifact}/training_summary.json) · "
                      f"[예측 CSV]({artifact}/test_predictions/predictions.csv)", ""])
    lines.extend(["같은 test를 다시 평가한 결과이므로 독립적인 새 test 검증은 아닙니다. "
                  "[부모/후속 비교 CSV](extended_comparison.csv)에 초기 validation loss와 "
                  "부모 체크포인트 정보도 보존했습니다.", ""])
    return lines, warnings


def summarize(root: Path) -> pd.DataFrame:
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"결과 디렉터리가 없습니다: {root}")
    phase_frames = {}
    warnings = []
    for phase, _ in PHASES:
        frame, phase_warnings = combine_phase(root, phase)
        phase_frames[phase] = frame
        warnings.extend(phase_warnings)
    present = [frame for frame in phase_frames.values() if not frame.empty]
    combined = pd.concat(present, ignore_index=True, sort=False) if present else pd.DataFrame(
        columns=["phase", "model", "validation_loss", "selected_by_validation", "has_test_metrics", *KEY_METRICS])
    combined.to_csv(root / "combined_comparison.csv", index=False)
    plot_comparison(phase_frames, root)
    extended_lines, extended_warnings = extended_report(root, phase_frames["tip"])
    warnings.extend(extended_warnings)
    now = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S KST")
    assumptions = Path(__file__).resolve().parents[1] / "docs" / "ASSUMPTIONS.md"
    assumptions_link = Path(os.path.relpath(assumptions, root)).as_posix()
    lines = ["# 외력 추정 실험 결과", "", f"갱신: {now}", "",
             "모델은 단계별 **validation_loss가 가장 작은 모델**로 선택했습니다. "
             "Test는 고정된 선택 모델과 전체 모델의 성능을 보고하는 데 사용하며 모델 선택·튜닝에는 쓰지 않습니다. "
             "아래 표도 validation loss 순서입니다. 끝단/body는 손실 항이 달라 validation loss를 단계 간 직접 비교하지 않습니다.", "",
             "공통 test는 학습에서 제외한 `sine-35deg-both_seg-id-18_right` 한 녹화입니다. "
             "XYZ RMSE는 모든 표본·세 축 성분의 평균 제곱 오차에 제곱근을 취한 값이며, "
             "평균 3D 벡터 오차와 구분합니다. 표의 —는 미실행 또는 분모가 없어 정의되지 않은 값입니다.", "",
             f"[통합 비교 CSV](combined_comparison.csv) · [비교 그래프](comparison.png) · [진행 중 정한 가정과 확인 필요 사항]({assumptions_link})", "",
             "![Validation 순서의 모델별 test 힘 오차와 위치 정확도](comparison.png)", ""]
    if (root / "DIAGNOSTICS.md").exists():
        lines.extend(["[상수 기준선·축별 실패·위치 오분류 상세 진단](DIAGNOSTICS.md)", ""])
    for phase, title in PHASES:
        frame = phase_frames[phase]
        lines.extend([f"## {title}", ""])
        if frame.empty:
            lines.extend(["학습/테스트 비교 CSV가 아직 없습니다. 이 단계는 완료로 기록하지 않습니다.", ""])
            continue
        lines.extend([f"모델 결과 {len(frame)}개, test 결과 {int(frame['has_test_metrics'].sum())}개입니다.", ""])
        selected = frame.loc[frame["selected_by_validation"]]
        if len(selected):
            for paragraph in selected_report(selected.iloc[0], phase, root):
                lines.extend([paragraph, ""])
        else:
            lines.extend(["유효한 validation loss가 없어 선택 모델을 지정하지 않았습니다.", ""])
        lines.extend(table(frame, phase))
        lines.extend(["", f"전체 열: [{phase} 학습 비교]({phase}/training_comparison.csv), "
                      f"[{phase} test 비교]({phase}/test_comparison.csv).", ""])
    lines.extend(extended_lines)
    lines.extend(["## 해석 시 확인할 한계", "",
                  "- Validation은 각 개발 녹화 앞 80%/뒤 20%를 나누고 경계 양쪽 2초를 제거한 시간 분할입니다. 같은 녹화 안의 분할이므로 독립 반복 실험 검증은 아닙니다.",
                  "- 무부하 범위는 사용자가 준 축별 ±1σ(Fx 45.4, Fy 43.6, Fz 72.9 mN)를 영점 중심으로 적용했습니다. 신뢰구간·교정된 접촉 정답이 아니며 작은 힘/노이즈 판정 오류가 포함될 수 있습니다.",
                  "- 측정된 Kalman aligned XYZ 및 연속 추론값을 0으로 덮어쓰지 않습니다. 세 축 모두 범위 안일 때 표시 힘·표시 ID만 0으로 처리합니다.",
                  "- `right_2`의 저장 ID1을 사용자 설명에 따라 학습용 ID18로 사용했습니다. 원본 라벨은 보존했으며 실제 접촉 위치의 사용자 확인이 필요합니다.",
                  "- 단일 seed 결과이며 물리 힘 교정, 반복 실험 간 불확실성, raw/Kalman 비교, 온라인 제어 검증은 완료한 것으로 해석하면 안 됩니다.",
                  "- 부드러운 예측 곡선 자체는 정확도나 응답 지연의 증명이 아닙니다. 원본 nearest 시간 정렬에는 최대 25 ms의 미래 측정값이 연결될 가능성이 있습니다.",
                  "- HRM 제어 연결 시 역정규화된 힘에 -1을 한 번 곱해야 합니다. 이번 학습과 평가는 저장된 aligned 부호를 유지합니다.", ""])
    if warnings:
        lines.extend(["## 미완료 또는 입력 확인 사항", ""])
        lines.extend("- " + warning for warning in warnings)
        lines.append("")
    (root / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    return combined


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_root", type=Path, help="tip/와 body/를 포함하는 날짜별 결과 디렉터리")
    args = parser.parse_args()
    result = summarize(args.results_root)
    print(f"{args.results_root / 'RESULTS.md'}: {len(result)}개 모델 결과 집계")


if __name__ == "__main__":
    main()
