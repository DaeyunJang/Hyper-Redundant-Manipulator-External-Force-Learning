"""저장된 predict 결과 → 힘/ID 비교 Excel + 그림. 학습·추론·원본 CSV 재로딩 없음.

bash scripts/hrm_python.sh analysis.py results/predict/실행폴더
bash scripts/hrm_python.sh analysis.py 'results/predict/날짜시간_*'
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import glob
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


AXES = ("fx", "fy", "fz", "xyz")
GROUPS = {"all": set(range(1, 19)), "body": set(range(1, 18)), "tip": {18}}
STATES = ("all", "loaded", "unloaded")
MODE_STYLE = {"masked": "-", "class0": "--"}
INPUT_NAMES = {
    "cable_loadcell": "C+L", "cable_angle": "C+A", "loadcell_angle": "L+A",
    "cable_loadcell_angle": "C+L+A", "cable_loadcell_estimated_pose": "C+L+Estimated",
    "cable_loadcell_fk_tip_tf": "C+L+FK TF",
}


def read_json(path: Path, sources: list) -> object:
    raw = path.read_bytes()
    sources.append({"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()})
    return json.loads(raw)


def percent(numerator: float, denominator: float) -> float:
    return 100 * numerator / denominator if denominator else np.nan


def pool_force(files: list[dict], state: str = "all") -> dict:
    """파일별 RMSE를 표본 수와 제곱오차로 합친다. N=0은 평가 불가다."""
    prefix = "" if state == "all" else state + "_"
    supported = [(int(m[prefix + "force_support"]), m) for m in files]
    supported = [(n, m) for n, m in supported if n > 0]
    total = sum(n for n, _ in supported)
    result = {"n": total}
    for metric in ("rmse", "mae"):
        for axis in AXES:
            key = f"{metric}_{axis}_mN"
            if not total:
                result[key] = np.nan
                continue
            values = np.array([m.get(prefix + "force_" + key, np.nan) for _, m in supported], dtype=float)
            if not np.isfinite(values).all():
                raise ValueError(f"양수 force_support에 {prefix + key}가 없습니다.")
            weights = np.array([n for n, _ in supported])
            result[key] = float(np.sqrt(np.average(values ** 2, weights=weights)) if metric == "rmse"
                                else np.average(values, weights=weights))
    return result


def final_confusion(report: dict, mode: str) -> tuple[np.ndarray, np.ndarray]:
    """Masked의 위치 argmax / Class0의 ID0 포함 최종 출력."""
    saved = report["system_confusion" if mode == "class0" else "conditional_confusion"]
    labels = np.asarray(saved["labels"], dtype=int)
    matrix = np.asarray(saved["matrix"], dtype=np.int64)
    if not saved.get("available", True) or matrix.shape != (len(labels), len(labels)):
        raise ValueError(f"{mode}의 저장 혼동행렬이 없거나 크기가 맞지 않습니다.")
    return labels, matrix


def id_scores(labels: np.ndarray, matrix: np.ndarray, ids: set, tolerances: list[int]) -> dict:
    rows = np.isin(labels, list(ids)) & (labels > 0)
    counts = matrix[rows]
    support = counts.sum(axis=1)
    total = int(support.sum())
    distance = np.abs(labels[rows, None] - labels[None, :])
    result = {"n_loaded": total, "supported_ids": int((support > 0).sum())}
    for tolerance in tolerances:
        # ID0은 물리 위치가 아니므로 GT1과 가깝더라도 항상 실패다.
        hit = (counts * ((labels[None, :] > 0) & (distance <= tolerance))).sum(axis=1)
        result[f"hits_tol{tolerance}"] = int(hit.sum())
        result[f"accuracy_tol{tolerance}_pct"] = percent(hit.sum(), total)
        result[f"macro_tol{tolerance}_pct"] = float(100 * np.mean(hit[support > 0] / support[support > 0])) if total else np.nan
    for name, columns in (("id0", labels == 0), ("tip", labels == 18),
                          ("body", (labels >= 1) & (labels <= 17))):
        result[f"predicted_{name}_pct"] = percent(counts[:, columns].sum(), total)
    return result


def detection_scores(files: list[dict], mode: str) -> dict:
    """GT0 행은 원 접촉 ID를 잃으므로 body/tip 검출 통계는 파일별로 합친다."""
    if mode == "masked":
        return {"available": False}
    values = {name: sum(int(m["load_" + name]) for m in files) for name in ("tp", "fn", "tn", "fp")}
    tp, fn, tn, fp = (values[name] for name in ("tp", "fn", "tn", "fp"))
    return {"available": True, **values, "n_loaded": tp + fn, "n_unloaded": tn + fp,
            "loaded_recall_pct": percent(tp, tp + fn), "unloaded_recall_pct": percent(tn, tn + fp),
            "unloaded_false_positive_pct": percent(fp, tn + fp)}


def identifier(row: dict) -> str:
    return f"{row['mode']}__force_{row['force_model']}__location_{row['location_model']}"


def choose_models(comparison: pd.DataFrame, summary: dict, reports: dict) -> tuple[set, set]:
    # Force는 predict가 저장한 validation 선택을 그대로 사용한다.
    force = {identifier(row) for row in summary["best_by_mode"].values()}
    available = comparison[comparison.apply(lambda row: identifier(row) in reports, axis=1)].copy()
    for column in ("location_macro_recall", "location_validation_ce", "force_rmse_xyz_mN"):
        available[column] = pd.to_numeric(available[column], errors="coerce")
    available = available[np.isfinite(available.location_macro_recall)]
    ordered = available.sort_values(
        ["location_macro_recall", "location_validation_ce", "force_rmse_xyz_mN", "force_model", "location_model"],
        ascending=[False, True, True, True, True], na_position="last")
    location = {identifier(row) for row in ordered.groupby("mode", sort=False).head(1).to_dict("records")}
    if not force or not force.issubset(reports) or not location:
        raise ValueError("저장된 validation 모델 선택을 확인할 수 없습니다.")
    return force, location


def analyze_run(folder: Path, force_files: list[str], tolerances: list[int], tables: dict, matrices: list) -> None:
    sources = []
    metrics = read_json(folder / "metrics.json", sources)
    if "all_combinations" not in metrics:
        raise ValueError("--train-dir로 predict한 전조합 결과 폴더를 지정하세요. 단일 checkpoint 결과는 지원하지 않습니다.")
    manifest = read_json(folder / "workbook_manifest.json", sources)
    inputs = read_json(folder / "input_manifest.json", sources)
    summary = read_json(folder / "summary.json", sources)
    comparison_path = folder / "comparison.csv"
    sources.append({"path": str(comparison_path), "sha256": hashlib.sha256(comparison_path.read_bytes()).hexdigest()})
    comparison = pd.read_csv(comparison_path)
    reports = metrics["all_combinations"]
    force_best, id_best = choose_models(comparison, summary, reports)
    sheets = manifest["model_sheets"]
    scopes = {item["force_scope"] for item in sheets}
    if len(scopes) != 1:
        raise ValueError("한 실행의 force_scope가 일관되지 않습니다.")
    force_scope = scopes.pop()
    name = re.sub(r"^\d{8}_\d{6}_?", "", folder.name) or folder.name
    run = str(folder)
    base = {"run": run, "input": name, "force_scope": force_scope}
    trial_map = {item["path"]: item for item in inputs}
    if force_files:
        missing = set(force_files) - {Path(path).name for path in trial_map}
        if missing:
            raise ValueError(f"{folder.name}: 요청한 force 파일이 없습니다: {sorted(missing)}")
    representative = {"force": set(), "location": set()}
    for item in sheets:
        force_model = item["model"] if item["branch"] == "force" else item["fixed_partner"]
        location_model = item["model"] if item["branch"] == "location" else item["fixed_partner"]
        representative[item["branch"]].add(identifier({"mode": item["mode"], "force_model": force_model,
                                                        "location_model": location_model}))
    tables["runs"].append({**base, "combinations": len(reports), "test_files": len(inputs),
        "force_file_filter": ", ".join(force_files) or "all saved test files",
        "input_columns": ", ".join(sheets[0]["input_columns"]), "window_samples": sheets[0]["window_samples"],
        "test_evaluation_scope": summary.get("test_evaluation_scope", "not recorded; independence not verified")})
    for item in inputs:
        tables["test_files"].append({**base, **{key: item.get(key) for key in
            ("path", "sha256", "effective_id", "rows", "source_rows_total", "dropped_rows", "prediction_endpoints")}})
    indexed = {identifier(row): row for row in comparison.to_dict("records")}
    for key, report in reports.items():
        row = indexed[key]
        model = {**base, "mode": row["mode"], "force_model": row["force_model"], "location_model": row["location_model"],
                 "selected_force": key in force_best, "selected_id": key in id_best,
                 "representative_force": key in representative["force"], "representative_id": key in representative["location"],
                 "checkpoint": report.get("checkpoint", row.get("bundle"))}
        tables["models"].append({**model, **{"validation_" + field: row.get(field) for field in
            ("force_rmse_xyz_mN", "location_macro_recall", "location_validation_ce", "force_best_epoch", "location_best_epoch")}})
        file_rows = [(path, trial_map[path]["effective_id"], values) for path, values in report["files"].items()]
        selected_files = [(p, segment, values) for p, segment, values in file_rows if not force_files or Path(p).name in force_files]
        labels, matrix = final_confusion(report, row["mode"])
        for group, ids in GROUPS.items():
            for state in STATES:
                score = {**model, "group": group, "load_state": state,
                         **pool_force([m for _, segment, m in selected_files if segment in ids], state)}
                tables["force"].append(score)
                if key in force_best:
                    tables["force_selected"].append(score)
            score = {**model, "group": group, **id_scores(labels, matrix, ids, tolerances)}
            tables["location"].append(score)
            detection = {**model, "group": group, **detection_scores([m for _, segment, m in file_rows if segment in ids], row["mode"])}
            tables["detection"].append(detection)
            if key in id_best:
                tables["id_selected"].append({**score, **{"detection_" + k: v for k, v in detection.items() if k not in model and k != "group"}})
        # ID/파일별 상세 표는 validation 선택 모델과 organized와 같은 대표분기다.
        if key in force_best | representative["force"]:
            for path, segment, values in selected_files:
                for state in STATES:
                    tables["force_by_file"].append({**model, "file": path, "contact_id": segment, "load_state": state,
                                                    **pool_force([values], state)})
            for segment in sorted({segment for _, segment, _ in selected_files}):
                for state in STATES:
                    tables["force_by_id"].append({**model, "contact_id": segment, "load_state": state,
                        **pool_force([m for _, sid, m in selected_files if sid == segment], state)})
        if key in id_best | representative["location"]:
            for segment in labels[labels > 0]:
                tables["id_by_id"].append({**model, "gt_id": int(segment), **id_scores(labels, matrix, {int(segment)}, tolerances)})
        if key in id_best:
            matrices.append((model, labels, matrix))
            for i, gt in enumerate(labels):
                for j, pred in enumerate(labels):
                    tables["confusion"].append({**model, "gt_id": int(gt), "predicted_id": int(pred),
                        "count": int(matrix[i, j]), "row_support": int(matrix[i].sum()),
                        "row_pct": percent(matrix[i, j], matrix[i].sum())})
    tables["sources"].extend({"run": run, **source} for source in sources)
    print(f"분석: {folder.name} / force_scope={force_scope} / {len(reports)}조합", flush=True)


def guide(force_files: list[str], tolerances: list[int]) -> pd.DataFrame:
    return pd.DataFrame([
        ("단위", "힘 mN, 정확도 %, n은 평가행 수. 빈 셀은 평가 불가이며 0 오차/0%가 아님."),
        ("힘 범위", "저장된 force_scope 사용. tip 학습의 body는 N=0. all_single_contact는 각 접촉점의 실측 힘을 평가."),
        ("힘 평가 파일", ", ".join(force_files) or "저장된 전체 test 파일. 특정 독립 실험만 보려면 --force-file 사용."),
        ("부하 구분", "저장 라벨 사용. 현재 YAML을 읽거나 문턱을 다시 적용하지 않음. 힘은 all/loaded/unloaded로 분리."),
        ("힘 pooling", "RMSE=sqrt(sum(N_file*RMSE_file^2)/sum N_file); MAE=sum(N_file*MAE_file)/sum N_file."),
        ("XYZ 오차", "3축 성분 전체의 RMSE/MAE. 힘 벡터 norm 오차나 각 축 RMSE의 산술평균이 아님."),
        ("ID 평가", "GT 유부하만 분모. Masked=ID1–18 argmax, Class0=최종 ID0–18 argmax. 예측0은 모든 tolerance에서 실패."),
        ("ID tolerance", f"{tolerances}: 예측ID>0 AND abs(예측ID-GT)<=n. 확률 합이 아닌 정답률. ±n 성공은 tip/body 구분 성공과 다름."),
        ("Macro", "지원행이 있는 GT ID별 성공률의 동일 가중 평균. micro accuracy는 전체 행 기준."),
        ("검출", "Class0의 TP/FN/TN/FP 및 유부하 검출률, 무부하 정답률. Masked 자체 검출은 평가 불가."),
        ("힘 모델 선택", "predict summary.json의 validation 힘 우선 선택 쌍 그대로. Test 최소 오차로 재선택하지 않음."),
        ("ID 모델 선택", "validation location_macro_recall 최대, CE/힘 RMSE/모델명 순 동률 처리. Class0 validation 점수는 ID0 제외 후보이며 test 보고는 최종 출력."),
        ("선택 모델", "force_selected와 id_selected는 서로 다른 bundle일 수 있음. 두 성능을 한 bundle의 결과로 합치지 말 것."),
        ("전체 조합", "models, force, location, detection 시트는 모든 저장 조합. force는 전체/body/tip × all/loaded/unloaded."),
        ("상세 및 대표모델", "force_by_file/force_by_id/id_by_id는 validation 선택 + organized와 동일한 고정 파트너 대표분기. representative_* 열로 선택."),
        ("혼동행렬", "ID validation 선택 모델. GT0 행은 Class0 무부하 전체; body/tip 무부하별 통계는 detection 시트."),
        ("ID 파일 범위", "ID는 모든 저장 test를 평가. --force-file은 힘 분석에만 적용; 저장 혼동행렬만으로 임의 파일별 ±n는 계산 불가."),
        ("비교 해석", "입력별 N과 학습 자료가 다를 수 있음. 공통행 비교/독립 세션 판정/중복 제거/여러 seed 통계는 수행하지 않음."),
        ("원자료", "행별 GT/예측은 기존 predictions.xlsx 및 organized Excel 사용. 이 파일은 집계 결과이며 모델을 다시 실행하지 않음."),
        ("추가 진단", "힘 크기별 ID 정확도, 공통 끝행 비교, 시계열 그림은 이 코드 범위 밖. 원본 행별 예측과 별도 분석이 필요."),
    ], columns=["항목", "설명"])


def write_excel(tables: dict, destination: Path) -> None:
    options = {"strings_to_formulas": False, "strings_to_urls": False}
    with pd.ExcelWriter(destination, engine="xlsxwriter", engine_kwargs={"options": options}) as writer:
        for name, frame in tables.items():
            # 점수는 왼쪽에, 긴 원본 경로와 선택 여부 등 출처 정보는 오른쪽에 둔다.
            preferred = ["input", "mode", "force_model", "location_model", "group", "load_state", "contact_id", "gt_id", "n", "n_loaded"]
            preferred += [f"{metric}_{axis}_mN" for metric in ("rmse", "mae") for axis in AXES]
            preferred += [column for column in frame.columns if column.startswith(("accuracy_tol", "macro_tol"))]
            front = [column for column in preferred if column in frame.columns]
            frame = frame[front + [column for column in frame.columns if column not in front]]
            frame.to_excel(writer, sheet_name=name, index=False)
            sheet = writer.sheets[name]
            sheet.freeze_panes(1, 0)
            if len(frame):
                sheet.autofilter(0, 0, len(frame), len(frame.columns) - 1)
            sheet.set_column(0, len(frame.columns) - 1, 19)
            if name == "guide":
                sheet.set_column(0, 0, 22)
                sheet.set_column(1, 1, 115, writer.book.add_format({"text_wrap": True}))
            else:
                for index, column in enumerate(frame.columns):
                    if column in ("run", "file", "path", "checkpoint", "input_columns"):
                        sheet.set_column(index, index, 32)


def plot_summary(tables: dict, output: Path, tolerances: list[int]) -> None:
    force = tables["force_selected"].query("group == 'all' and load_state == 'all'").reset_index(drop=True)
    location = tables["id_selected"].query("group == 'body'").reset_index(drop=True)
    runs = tables["runs"].run.tolist()
    colors = {run: plt.get_cmap("tab10")(i % 10) for i, run in enumerate(runs)}
    names = {}
    runs_table = tables["runs"]
    for index, row in enumerate(runs_table.itertuples(), 1):
        label = INPUT_NAMES.get(row.input, row.input)
        if runs_table.force_scope.nunique() > 1 or runs_table.input.duplicated(keep=False).any():
            label += f" [{index}: {row.force_scope}]"
        names[row.run] = label
    many_curves = len(location) > 6
    fig, axes = plt.subplots(2, 2, figsize=(max(13, len(force) * .95), 13 if many_curves else 11))
    x = np.arange(len(force))
    labels = [f"{names[r.run]}\n{r.mode}\nN={int(r.n):,}" for r in force.itertuples()]
    a, b, c, d = axes.flat
    a.bar(x, force.rmse_xyz_mN, color=[colors[r] for r in force.run])
    a.set(title="A. Force: XYZ RMSE (validation-selected force model)", ylabel="RMSE [mN]")
    a.set_xticks(x, labels, rotation=55, ha="right", fontsize=8)
    for i, value in enumerate(force.rmse_xyz_mN):
        if np.isfinite(value):
            a.annotate(f"{value:.2f}", (i, value), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8)
    for offset, axis in enumerate(AXES[:3]):
        b.bar(x + (offset - 1) * .25, force[f"rmse_{axis}_mN"], width=.25, label=axis.upper())
    b.set(title="B. Force: axis RMSE (same models / rows as A)", ylabel="RMSE [mN]")
    b.set_xticks(x, labels, rotation=55, ha="right", fontsize=8)
    b.legend()
    for row in location.to_dict("records"):
        c.plot(tolerances, [row[f"accuracy_tol{n}_pct"] for n in tolerances], MODE_STYLE[row["mode"]],
               marker="o", color=colors[row["run"]], label=f"{names[row['run']]} {row['mode']} (N={int(row['n_loaded']):,})")
    c.set(title="C. Body ID: final-output accuracy on GT-loaded rows", xlabel="Allowed segment error (±n)", ylabel="Accuracy [%]", ylim=(0, 105))
    c.set_xticks(tolerances)
    if many_curves:
        handles, legend_labels = c.get_legend_handles_labels()
        fig.legend(handles, legend_labels, fontsize=8, loc="lower center", bbox_to_anchor=(.5, .035), ncol=3)
    else:
        c.legend(fontsize=8, loc="best")
    detection = location[location["mode"].eq("class0")]
    xd = np.arange(len(detection))
    if len(detection):
        for shift, column, label in ((-.18, "loaded_recall_pct", "Loaded recall"), (.18, "unloaded_recall_pct", "Unloaded recall")):
            d.bar(xd + shift, detection["detection_" + column], width=.36, label=label)
        d.set_xticks(xd, [f"{names[r.run]}\nloaded N={int(r.n_loaded):,}\nunloaded N={int(r.detection_n_unloaded):,}" for r in detection.itertuples()],
                      rotation=30, ha="right", fontsize=8)
        d.legend(fontsize=9)
    else:
        d.text(.5, .5, "Masked has no load detector", transform=d.transAxes, ha="center")
    d.set(title="D. Class0: body-file load detection (ID-selected model)", ylabel="Recall [%]", ylim=(0, 115))
    d.set_yticks(range(0, 101, 20))
    for ax in axes.flat:
        ax.grid(axis="y", alpha=.2)
        ax.set_axisbelow(True)
    filters = tables["runs"].force_file_filter.unique()
    fig.suptitle("Saved test results | force training scope: " + ", ".join(tables["runs"].force_scope.unique()) +
                 "\nForce files: " + "; ".join(filters), fontsize=12)
    fig.text(.5, .008, "Force and ID models are selected separately on validation. N may differ across inputs. Class0 ID0 fails every ID tolerance.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .15 if many_curves else .025, 1, .94))
    fig.savefig(output / "force_and_id_summary.png", dpi=180)
    plt.close(fig)


def plot_confusions(matrices: list, output: Path) -> None:
    by_run = defaultdict(list)
    for model, labels, matrix in matrices:
        by_run[model["run"]].append((model, labels, matrix))
    for index, items in enumerate(by_run.values(), 1):
        fig, axes = plt.subplots(1, len(items), figsize=(9 * len(items), 8), squeeze=False, constrained_layout=True)
        for ax, (model, labels, matrix) in zip(axes.flat, items):
            rows = labels > 0
            support = matrix[rows].sum(axis=1)
            values = np.divide(100. * matrix[rows], support[:, None],
                               out=np.full(matrix[rows].shape, np.nan), where=support[:, None] > 0)
            cmap = plt.get_cmap("Blues").copy()
            cmap.set_bad("lightgray")
            img = ax.imshow(values, vmin=0, vmax=100, aspect="auto", cmap=cmap)
            ax.set_xticks(np.arange(len(labels)), labels)
            ax.set_yticks(np.arange(rows.sum()), [f"{sid} (N={n})" for sid, n in zip(labels[rows], support)])
            name = INPUT_NAMES.get(model["input"], model["input"])
            ax.set(title=f"{name} / {model['mode']} / force scope: {model['force_scope']}\nForce {model['force_model']} + ID {model['location_model']}",
                   xlabel="Predicted ID (0 = unloaded)", ylabel="GT contact ID on loaded rows")
            fig.colorbar(img, ax=ax, label="Within-GT-ID percentage [%]", shrink=.8)
        fig.savefig(output / f"id_confusion_{index:02d}_{items[0][0]['input']}.png", dpi=160)
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("predict_dirs", nargs="+", help="predict 결과 폴더 하나/여러 개 또는 따옴표로 감싼 glob")
    parser.add_argument("--output", type=Path, help="새 분석 폴더; 기본 results/analysis/날짜시간_comparison")
    parser.add_argument("--force-file", nargs="+", default=[], help="힘 평가에 포함할 CSV 파일명. 생략하면 전체 test; ID 평가는 전체 유지")
    parser.add_argument("--id-tolerances", nargs="+", type=int, default=[2, 3], help="기본 2 3; 정확 ID(0)와 ±1도 항상 계산")
    args = parser.parse_args()
    if any(n < 0 or n > 17 for n in args.id_tolerances):
        parser.error("ID tolerance는 0–17이어야 합니다.")
    tolerances = sorted({0, 1, *args.id_tolerances})
    folders = []
    for pattern in args.predict_dirs:
        matches = sorted(glob.glob(str(Path(pattern).expanduser())))
        if not matches:
            parser.error(f"결과 폴더를 찾을 수 없습니다: {pattern}")
        for path in matches:
            folder = Path(path).resolve()
            if not (folder / "metrics.json").is_file():
                parser.error(f"metrics.json이 있는 predict 실행 폴더를 지정하세요: {folder}")
            if folder not in folders:
                folders.append(folder)
    stamp = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d_%H%M%S_%f")
    output = (args.output or Path("results/analysis") / (stamp + "_comparison")).resolve()
    if output.exists():
        parser.error(f"기존 결과를 보존합니다. 새 --output 경로를 지정하세요: {output}")
    tables, matrices = defaultdict(list), []
    for folder in folders:
        analyze_run(folder, args.force_file, tolerances, tables, matrices)
    frames = {"guide": guide(args.force_file, tolerances), **{name: pd.DataFrame(rows) for name, rows in tables.items()}}
    output.mkdir(parents=True)
    write_excel(frames, output / "force_and_id_all_combinations.xlsx")
    plot_summary(frames, output, tolerances)
    plot_confusions(matrices, output)
    print(f"분석 완료: {output}")
    print("Excel: force_selected / id_selected → 선택 모델, force / location → 전체 조합, *_by_id → ID별 결과")


if __name__ == "__main__":
    main()
