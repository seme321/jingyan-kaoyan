# -*- coding: utf-8 -*-
"""
One-command exam pack ingestion CLI:
Validates, normalizes LaTeX, converts PNG/JPG figures to WebP, writes `<year>.json`,
updates `<courseId>/index.json` and `courses.json`, and runs `scripts/validate_course.mjs`.

Example:
  python scripts/ingest_exam.py --course yzu-849 --json "扬州大学已整理数据/2024/2024.json" --figures "扬州大学已整理数据/2024/figures"
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = ROOT / "web" / "public" / "data"


def fix_common_latex_glitches(text: str) -> str:
    if not text:
        return text
    text = text.replace(r"^{^{\circ}}", r"^{\circ}")
    text = text.replace(r"^{\mathrm{^{\circ}}}", r"^{\circ}")
    text = re.sub(r"\^\{\s*'''\s*\}", r"^{\\prime\\prime\\prime}", text)
    text = re.sub(r"\^\{\s*''\s*\}", r"^{\\prime\\prime}", text)
    text = re.sub(r"\^\{\s*'\s*\}", r"^{\\prime}", text)
    return text


def process_figure_list(fig_list: list[dict], src_fig_dir: Path | None, dest_fig_dir: Path, year: int) -> list[dict]:
    out = []
    for fig in fig_list or []:
        raw_src = fig.get("src", "").strip()
        caption = fig.get("caption", "").strip()
        if not raw_src:
            continue

        # Locate source image if src_fig_dir provided
        candidate = None
        if src_fig_dir:
            p1 = src_fig_dir / Path(raw_src).name
            p2 = src_fig_dir.parent / raw_src
            if p1.exists():
                candidate = p1
            elif p2.exists():
                candidate = p2

        stem = Path(raw_src).stem
        webp_name = f"{stem}.webp"
        dest_file = dest_fig_dir / webp_name

        if candidate and candidate.exists():
            dest_fig_dir.mkdir(parents=True, exist_ok=True)
            img = Image.open(candidate)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA")
            img.save(dest_file, format="WEBP", quality=90, method=5)

        out.append({
            "src": f"figures/{year}/{webp_name}",
            "caption": caption,
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest standardized exam JSON + figures into web/public/data/<courseId>/")
    ap.add_argument("--course", required=True, help="Course ID in courses.json, e.g. hhu-814 or yzu-849")
    ap.add_argument("--json", required=True, help="Path to standardized <year>.json")
    ap.add_argument("--figures", default="", help="Optional folder containing raw PNG/JPG/WebP figures")
    args = ap.parse_args()

    course_dir = DATA_ROOT / args.course
    if not course_dir.exists():
        print(f"ERROR: Course folder not found: {course_dir}. Please initialize {args.course} first.")
        return 1

    src_json_path = Path(args.json).resolve()
    paper = json.loads(src_json_path.read_text(encoding="utf-8"))
    year = int(paper["year"])

    src_fig_dir = Path(args.figures).resolve() if args.figures else src_json_path.parent / "figures"
    dest_fig_dir = course_dir / "figures" / str(year)

    paper["examNotes"] = [fix_common_latex_glitches(n) for n in paper.get("examNotes", [])]

    fig_total = 0
    for idx, q in enumerate(paper["questions"], start=1):
        # Ensure globally unique question ID scoped by course if not already scoped
        if not str(q.get("id", "")).startswith(args.course) and args.course != "hhu-814":
            q["id"] = f"{args.course}-{year}-{q['no']:02d}"
        elif not q.get("id"):
            q["id"] = f"{year}-{q['no']:02d}"

        for field in ("title", "stem", "note", "shortAnswer", "answer", "analysis", "pitfalls"):
            if field in q and isinstance(q[field], str):
                q[field] = fix_common_latex_glitches(q[field])
        for opt in q.get("options") or []:
            opt["text"] = fix_common_latex_glitches(opt.get("text", ""))

        q["figures"] = process_figure_list(q.get("figures", []), src_fig_dir, dest_fig_dir, year)
        q["analysisFigures"] = process_figure_list(q.get("analysisFigures", []), src_fig_dir, dest_fig_dir, year)
        fig_total += len(q["figures"]) + len(q["analysisFigures"])

    out_json_path = course_dir / f"{year}.json"
    out_json_path.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding="utf-8")

    # Update <courseId>/index.json
    idx_path = course_dir / "index.json"
    idx_data = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {"availableYears": []}
    years_list = idx_data.get("availableYears", [])
    entry = {
        "year": year,
        "title": f"{year} 年{paper['school']} {paper['code']} {paper['subject']}考研真题",
        "questionCount": len(paper["questions"]),
        "totalScore": paper["totalScore"],
        "figureCount": fig_total,
        "status": "ready",
        "dataFile": f"{year}.json",
    }
    replaced = False
    for i, ym in enumerate(years_list):
        if ym["year"] == year:
            years_list[i] = entry
            replaced = True
            break
    if not replaced:
        years_list.append(entry)
    years_list.sort(key=lambda x: x["year"], reverse=True)
    idx_data["availableYears"] = years_list
    idx_path.write_text(json.dumps(idx_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Mark course as 'ready' in courses.json
    cat_path = DATA_ROOT / "courses.json"
    cat = json.loads(cat_path.read_text(encoding="utf-8"))
    for c in cat.get("courses", []):
        if c["id"] == args.course:
            c["status"] = "ready"
    cat_path.write_text(json.dumps(cat, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Ingested {args.course} {year}: {len(paper['questions'])} questions, {fig_total} figures -> {out_json_path}")

    # Run KaTeX + schema validator automatically
    res = subprocess.run(["node", str(ROOT / "scripts" / "validate_course.mjs"), "--course", args.course])
    return res.returncode


if __name__ == "__main__":
    sys.exit(main())
