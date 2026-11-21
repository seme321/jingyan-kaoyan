#!/usr/bin/env python3
"""
创意工坊 .jypack.zip 检验、导出与打包工具

用法示例：
  1. 检验并打包本地资源目录：
     python scripts/pack_workshop.py --src ./my_pack --out ./dist/my_pack.jypack.zip

  2. 将包内 PNG/JPG 图片自动转为 WebP 并重写引用后打包（需安装 Pillow）：
     python scripts/pack_workshop.py --src ./my_pack --out ./dist/my_pack.jypack.zip --to-webp

  3. 从内置题库导出一整门专业课为体验包：
     python scripts/pack_workshop.py --export-course hhu-814 --out ./hhu-814.jypack.zip

  4. 从内置题库导出单年真题补充包（exam 包）：
     python scripts/pack_workshop.py --export-course hhu-814 --year 2026 --out ./hhu-2026.jypack.zip
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

SAFE_PACK_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,47}$")
SAFE_COURSE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,31}$")
VALID_PACK_TYPES = {"course", "exam", "character"}
VALID_UNLOCK_MODES = {"direct", "gacha"}
VALID_Q_TYPES = {
    "judge",
    "single_choice",
    "multi_choice",
    "fill",
    "term",
    "short",
    "calc",
    "proof",
}
BANNED_TEXT_RE = re.compile(r"(?:\bOCR\b|待补充解析|占位图|placeholder)", re.IGNORECASE)
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
MAX_D1_BYTES = 15 * 1024 * 1024
FIXED_ZIP_TIME = (2025, 1, 1, 0, 0, 0)

REPO_ROOT = Path(__file__).resolve().parent.parent


def norm_rel(path_str: str) -> str:
    return path_str.replace("\\", "/").lstrip("./").lstrip("/")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dump_json_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def convert_images_to_webp(work_dir: Path) -> tuple[int, dict[str, str]]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "启用了 --to-webp 但未安装 Pillow，请先运行: pip install pillow"
        ) from exc

    replaced: dict[str, str] = {}
    for path in sorted(work_dir.rglob("*")):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext not in {".png", ".jpg", ".jpeg"}:
            continue
        rel_old = norm_rel(str(path.relative_to(work_dir)))
        target = path.with_suffix(".webp")
        rel_new = norm_rel(str(target.relative_to(work_dir)))
        with Image.open(path) as im:
            has_alpha = im.mode in ("RGBA", "LA") or (
                im.mode == "P" and "transparency" in im.info
            )
            converted = im.convert("RGBA" if has_alpha else "RGB")
            converted.save(target, "WEBP", quality=88, method=6)
        if target != path:
            path.unlink()
            replaced[rel_old] = rel_new

    if replaced:
        for json_path in work_dir.rglob("*.json"):
            text = json_path.read_text(encoding="utf-8")
            updated = text
            for old_rel, new_rel in replaced.items():
                updated = updated.replace(f'"{old_rel}"', f'"{new_rel}"')
                updated = updated.replace(f'"./{old_rel}"', f'"{new_rel}"')
            if updated != text:
                json_path.write_text(updated, encoding="utf-8")

    return len(replaced), replaced


def run_katex_validation(tex_items: list[tuple[str, str, bool]], web_dir: Path) -> list[str]:
    if not tex_items:
        return []
    katex_dir = web_dir / "node_modules" / "katex"
    if not katex_dir.exists():
        print("[提示] 未找到 web/node_modules/katex，跳过离线 KaTeX 渲染校验。")
        return []
    node_bin = shutil.which("node")
    if not node_bin:
        print("[提示] 未找到 node 可执行文件，跳过离线 KaTeX 渲染校验。")
        return []

    script = """
const fs = require('fs');
const katex = require(process.argv[1]);
const items = JSON.parse(fs.readFileSync(0, 'utf8'));
const errs = [];
for (const it of items) {
  try {
    katex.renderToString(it.tex, { displayMode: !!it.display, throwOnError: true, strict: false });
  } catch (e) {
    errs.push(`${it.label} KaTeX 语法错误 ("${String(it.tex).slice(0, 48)}"): ${e.message}`);
    if (errs.length >= 25) break;
  }
}
process.stdout.write(JSON.stringify(errs));
"""
    payload = [{"label": lbl, "tex": tex, "display": disp} for lbl, tex, disp in tex_items]
    proc = subprocess.run(
        [node_bin, "-e", script, str(katex_dir)],
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        encoding="utf-8",
        check=False,
    )
    if proc.returncode != 0:
        return [f"KaTeX 校验脚本执行失败: {proc.stderr.strip()}"]
    return json.loads(proc.stdout or "[]")


def extract_math_segments(label: str, text: Any, out: list[tuple[str, str, bool]], errs: list[str]) -> None:
    if not isinstance(text, str) or not text:
        return
    if BANNED_TEXT_RE.search(text):
        errs.append(f"{label} 含疑似占位词/禁用词（OCR / 占位图 / 待补充解析）")
    pattern = re.compile(r"\$\$([\s\S]*?)\$\$|\$([^$\n]+?)\$")
    for m in pattern.finditer(text):
        if m.group(1) is not None:
            out.append((label, m.group(1).strip(), True))
        else:
            out.append((label, m.group(2).strip(), False))


def validate_pack_dir(src_dir: Path, skip_katex: bool = False) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    stats: dict[str, Any] = {}
    tex_items: list[tuple[str, str, bool]] = []

    manifest_path = src_dir / "manifest.json"
    if not manifest_path.is_file():
        return ["缺少根目录 manifest.json 文件"], stats

    try:
        manifest = load_json(manifest_path)
    except Exception as exc:
        return [f"manifest.json 解析失败: {exc}"], stats

    if manifest.get("schemaVersion") != 1:
        errors.append("manifest.schemaVersion 必须为 1")

    pack_id = str(manifest.get("packId", "")).strip().lower()
    if not SAFE_PACK_ID_RE.match(pack_id):
        errors.append("manifest.packId 必须为 3~48 位小写字母、数字、连字符或下划线")

    pack_type = str(manifest.get("type", "")).strip()
    if pack_type not in VALID_PACK_TYPES:
        errors.append("manifest.type 必须为 course、exam 或 character")

    for req_key in ("name", "version", "author", "summary", "license"):
        if not str(manifest.get(req_key, "")).strip():
            errors.append(f"manifest.{req_key} 不能为空")

    unlock_mode = str(manifest.get("unlockMode", "direct")).strip()
    if unlock_mode not in VALID_UNLOCK_MODES:
        errors.append("manifest.unlockMode 必须为 direct 或 gacha")

    cover = manifest.get("cover")
    if cover:
        cover_rel = norm_rel(str(cover))
        if not (src_dir / cover_rel).is_file():
            errors.append(f"manifest.cover 指向的文件不存在: {cover_rel}")

    def file_exists(rel: str) -> bool:
        clean = norm_rel(rel)
        return bool(clean) and (src_dir / clean).is_file()

    if pack_type in ("course", "exam"):
        target_course_id = str(manifest.get("targetCourseId", "")).strip()
        if pack_type == "course":
            course_path = src_dir / "course.json"
            if not course_path.is_file():
                errors.append("整门专业课包（type=course）缺少 course.json")
            else:
                c = load_json(course_path)
                cid = str(c.get("id", "")).strip()
                if not SAFE_COURSE_ID_RE.match(cid):
                    errors.append("course.json id 必须为 2~32 位小写字母、数字或连字符")
                for field in ("name", "shortLabel", "school", "code", "subject"):
                    if not str(c.get(field, "")).strip():
                        errors.append(f"course.json 缺少必填字段 {field}")
                target_course_id = cid
        else:
            if not SAFE_COURSE_ID_RE.match(target_course_id):
                errors.append("单年试卷包（type=exam）必须在 manifest.json 中指定合法的 targetCourseId")

        valid_chapters: set[int] = set()
        chapters_path = src_dir / "chapters.json"
        if pack_type == "course" and not chapters_path.is_file():
            errors.append("整门专业课包（type=course）缺少 chapters.json")
        if chapters_path.is_file():
            ch_data = load_json(chapters_path)
            chs = ch_data.get("chapters")
            if not isinstance(chs, list) or len(chs) == 0:
                errors.append("chapters.json 的 chapters 数组不能为空")
            else:
                for ch in chs:
                    if isinstance(ch.get("chapter"), int):
                        valid_chapters.add(ch["chapter"])

        formulas_path = src_dir / "formulas.json"
        if formulas_path.is_file():
            fm_raw = load_json(formulas_path)
            fm_list = fm_raw if isinstance(fm_raw, list) else fm_raw.get("formulas", [])
            for fm in fm_list:
                ch_no = fm.get("chapter")
                if valid_chapters and ch_no not in valid_chapters:
                    errors.append(f"公式 {fm.get('id') or fm.get('name')} chapter={ch_no} 不在 chapters.json 中")
                if fm.get("latex"):
                    tex_items.append((f"公式 {fm.get('id') or fm.get('name')}", str(fm["latex"]), True))
                extract_math_segments(f"公式 {fm.get('id')}.variables", fm.get("variables"), tex_items, errors)
                extract_math_segments(f"公式 {fm.get('id')}.note", fm.get("note"), tex_items, errors)

        papers_dir = src_dir / "papers"
        paper_files = sorted(papers_dir.glob("*.json")) if papers_dir.is_dir() else []
        if not paper_files:
            errors.append("papers/ 目录下至少需要包含 1 份试卷 JSON（例如 papers/2024.json）")

        total_questions = 0
        referenced_figs: set[str] = set()
        for pf in paper_files:
            paper = load_json(pf)
            year = paper.get("year")
            if not isinstance(year, int) or year < 1990 or year > 2100:
                errors.append(f"{pf.name}: year 字段无效")
            questions = paper.get("questions")
            if not isinstance(questions, list) or len(questions) == 0:
                errors.append(f"{pf.name}: questions 数组不能为空")
                continue

            sections = paper.get("sections") or []
            if isinstance(sections, list) and sections:
                expected_start = 1
                sec_score_sum = 0
                for sec in sections:
                    rng = sec.get("range")
                    if (
                        not isinstance(rng, list)
                        or len(rng) != 2
                        or rng[0] != expected_start
                        or rng[1] < rng[0]
                    ):
                        errors.append(
                            f"{pf.name} section {sec.get('id')}: range {rng} 非法（应从 {expected_start} 起连续）"
                        )
                    else:
                        expected_start = rng[1] + 1
                    sec_score_sum += sec.get("totalScore", 0)
                if expected_start - 1 != len(questions):
                    errors.append(
                        f"{pf.name}: sections 覆盖终点 {expected_start - 1} != 题数 {len(questions)}"
                    )
                if sec_score_sum != paper.get("totalScore"):
                    errors.append(
                        f"{pf.name}: sections 分值总和 {sec_score_sum} != totalScore {paper.get('totalScore')}"
                    )

            q_score_sum = 0
            for idx, q in enumerate(questions):
                expected_no = idx + 1
                if q.get("no") != expected_no:
                    errors.append(f"{pf.name}: 第 {expected_no} 题 no 应为 {expected_no}（实际 {q.get('no')}）")
                q_type = q.get("type")
                if q_type not in VALID_Q_TYPES:
                    errors.append(f"{pf.name} Q{q.get('no')}: 不支持的题型 {q_type}")
                if q_type == "judge":
                    if not isinstance(q.get("judgeAnswer"), bool):
                        errors.append(f"{pf.name} Q{q.get('no')}: judge 题必须提供布尔值 judgeAnswer")
                elif q_type in ("single_choice", "multi_choice"):
                    opts = q.get("options") or []
                    if not isinstance(opts, list) or len(opts) < 2:
                        errors.append(f"{pf.name} Q{q.get('no')}: {q_type} 至少需要 2 个选项")
                    if not str(q.get("choiceAnswer") or "").strip():
                        errors.append(f"{pf.name} Q{q.get('no')}: {q_type} 缺少 choiceAnswer")
                    if q.get("judgeAnswer") is not None:
                        errors.append(f"{pf.name} Q{q.get('no')}: {q_type} 的 judgeAnswer 必须为 null")
                elif q.get("judgeAnswer") is not None:
                    errors.append(f"{pf.name} Q{q.get('no')}: 非判断题的 judgeAnswer 必须为 null")

                q_score = q.get("score", 0)
                q_score_sum += q_score
                if valid_chapters and q.get("chapter") not in valid_chapters:
                    errors.append(f"{pf.name} Q{q.get('no')}: chapter={q.get('chapter')} 不在 chapters.json 中")
                rubric = q.get("rubric") or []
                if q_type in ("short", "calc", "proof") and q_score >= 5 and not rubric:
                    errors.append(f"{pf.name} Q{q.get('no')}: {q_score} 分主观大题建议/必须配备 rubric 采分点")
                if isinstance(rubric, list) and rubric:
                    r_sum = sum(r.get("pts", 0) for r in rubric)
                    if r_sum != q_score:
                        errors.append(f"{pf.name} Q{q.get('no')}: rubric 总分 {r_sum} != 题分 {q_score}")
                    for r_idx, r in enumerate(rubric):
                        r_text = r.get("label") if isinstance(r.get("label"), str) and r.get("label").strip() else r.get("step")
                        if not isinstance(r_text, str) or not r_text.strip():
                            errors.append(f"{pf.name} Q{q.get('no')}.rubric[{r_idx}]: 缺少非空 label 文本")
                        else:
                            extract_math_segments(
                                f"{pf.name} Q{q.get('no')}.rubric[{r_idx}]",
                                r_text,
                                tex_items,
                                errors,
                            )
                for fig in q.get("figures") or []:
                    src = norm_rel(str(fig.get("src", "")))
                    if not file_exists(src):
                        errors.append(f"{pf.name} Q{q.get('no')}: 找不到配图 {src}")
                    else:
                        referenced_figs.add(src)
                for fig in q.get("analysisFigures") or []:
                    src = norm_rel(str(fig.get("src", "")))
                    if not file_exists(src):
                        errors.append(f"{pf.name} Q{q.get('no')}: 找不到解析配图 {src}")
                    else:
                        referenced_figs.add(src)

                q_lbl = f"{pf.name} Q{q.get('no')}"
                for field in ("title", "stem", "note", "shortAnswer", "answer", "analysis", "pitfalls"):
                    extract_math_segments(f"{q_lbl}.{field}", q.get(field), tex_items, errors)
                for opt in q.get("options") or []:
                    extract_math_segments(f"{q_lbl}.选项{opt.get('label')}", opt.get("text"), tex_items, errors)

            if q_score_sum != paper.get("totalScore"):
                errors.append(f"{pf.name}: 各题总分 {q_score_sum} != totalScore {paper.get('totalScore')}")
            for note in paper.get("examNotes") or []:
                extract_math_segments(f"{pf.name}.examNotes", note, tex_items, errors)
            total_questions += len(questions)

        stats = {
            "targetCourseId": target_course_id,
            "paperCount": len(paper_files),
            "questionCount": total_questions,
            "figureCount": len(referenced_figs),
        }

    elif pack_type == "character":
        char_path = src_dir / "characters.json"
        if not char_path.is_file():
            errors.append("角色包（type=character）缺少 characters.json")
        else:
            ch_json = load_json(char_path)
            sp_cards = ch_json.get("spCards") or []
            chars = ch_json.get("characters") or []
            if not sp_cards and not chars:
                errors.append("characters.json 中 spCards 与 characters 不能同时为空")

            for idx, sp in enumerate(sp_cards):
                sid = str(sp.get("id", "")).strip()
                if not sid or sid in {"sp:dafeyu", "sp:gemini"}:
                    errors.append(f"characters.json spCards[{idx}] id 非法或与内置看板娘冲突: {sid}")
                sprite = str(sp.get("sprite", ""))
                avatar = str(sp.get("avatar", "") or sprite)
                if not file_exists(sprite):
                    errors.append(f"SP 角色 {sp.get('name') or sid} 缺少立绘: {sprite}")
                if not file_exists(avatar):
                    errors.append(f"SP 角色 {sp.get('name') or sid} 缺少头像: {avatar}")
                poses = sp.get("poses") or {}
                if isinstance(poses, dict):
                    for pk, pv in poses.items():
                        if pv and not file_exists(str(pv)):
                            errors.append(f"SP 角色 {sp.get('name') or sid} 缺少姿态图({pk}): {pv}")

            for idx, ch in enumerate(chars):
                cid = str(ch.get("id", "")).strip()
                if not cid:
                    errors.append(f"characters.json characters[{idx}] 缺少 id")
                variants = ch.get("variants") or {}
                for vk in ("chibi", "medium", "standard"):
                    v = variants.get(vk)
                    if not isinstance(v, dict):
                        errors.append(f"角色 {ch.get('name') or cid} 缺少 {vk} 形态配置")
                        continue
                    sprite = str(v.get("sprite", ""))
                    avatar = str(v.get("avatar", "") or sprite)
                    sheet = str(v.get("sheet", "") or "")
                    if not file_exists(sprite):
                        errors.append(f"角色 {ch.get('name') or cid} ({vk}) 缺少立绘: {sprite}")
                    if not file_exists(avatar):
                        errors.append(f"角色 {ch.get('name') or cid} ({vk}) 缺少头像: {avatar}")
                    if sheet and not file_exists(sheet):
                        errors.append(f"角色 {ch.get('name') or cid} ({vk}) 缺少设定图: {sheet}")

            stats = {
                "spCardCount": len(sp_cards),
                "characterCount": len(chars),
                "unlockMode": unlock_mode,
            }

    if not skip_katex and tex_items:
        errors.extend(run_katex_validation(tex_items, REPO_ROOT / "web"))

    return errors, stats


def write_deterministic_zip(src_dir: Path, out_zip: Path) -> tuple[int, str, int]:
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    file_count = 0
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(src_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = norm_rel(str(path.relative_to(src_dir)))
            if not rel or rel.startswith("__MACOSX/") or path.name == ".DS_Store":
                continue
            zinfo = zipfile.ZipInfo(rel, date_time=FIXED_ZIP_TIME)
            zinfo.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zinfo, path.read_bytes())
            file_count += 1

    raw = out_zip.read_bytes()
    sha256 = hashlib.sha256(raw).hexdigest()
    return len(raw), sha256, file_count


def stage_exported_course(
    course_id: str,
    year_filter: int | None,
    stage_dir: Path,
    pack_id_override: str | None,
    version: str,
    author: str,
    license_text: str,
) -> None:
    data_root = REPO_ROOT / "web" / "public" / "data"
    courses_file = data_root / "courses.json"
    course_dir = data_root / course_id
    if not courses_file.is_file() or not course_dir.is_dir():
        raise FileNotFoundError(f"未找到内置科目数据目录: {course_dir}")

    courses_json = load_json(courses_file)
    course_meta = next((c for c in courses_json.get("courses", []) if c.get("id") == course_id), None)
    if not course_meta:
        raise ValueError(f"courses.json 中不存在科目 {course_id}")

    index_json = load_json(course_dir / "index.json")
    available = [y for y in index_json.get("availableYears", []) if y.get("status") == "ready"]
    if year_filter is not None:
        available = [y for y in available if y.get("year") == year_filter]
        if not available:
            raise ValueError(f"科目 {course_id} 中不存在 {year_filter} 年已就绪真题")

    papers_out_dir = stage_dir / "papers"
    papers_out_dir.mkdir(parents=True, exist_ok=True)
    copied_figs = 0

    for y_meta in available:
        data_file = norm_rel(str(y_meta.get("dataFile", f"{y_meta['year']}.json")))
        paper_src = course_dir / data_file
        if not paper_src.is_file():
            raise FileNotFoundError(f"找不到真题文件: {paper_src}")
        paper = load_json(paper_src)
        (papers_out_dir / f"{paper['year']}.json").write_bytes(dump_json_bytes(paper))

        for q in paper.get("questions", []):
            for fig in [*(q.get("figures") or []), *(q.get("analysisFigures") or [])]:
                src_rel = norm_rel(str(fig.get("src", "")))
                if not src_rel:
                    continue
                src_file = course_dir / src_rel
                if not src_file.is_file():
                    raise FileNotFoundError(f"找不到配图文件: {src_file}")
                dst_file = stage_dir / src_rel
                if not dst_file.exists():
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dst_file)
                    copied_figs += 1

    if year_filter is None:
        pack_type = "course"
        default_pack_id = f"{course_id}-pack"
        pack_name = course_meta["name"]
        summary = course_meta.get("description") or f"{pack_name} 全套真题与解析资源包。"
        (stage_dir / "course.json").write_bytes(dump_json_bytes(course_meta))
        chapters_src = course_dir / "chapters.json"
        if chapters_src.is_file():
            shutil.copy2(chapters_src, stage_dir / "chapters.json")
        formulas_src = course_dir / "formulas.json"
        if formulas_src.is_file():
            shutil.copy2(formulas_src, stage_dir / "formulas.json")
    else:
        pack_type = "exam"
        default_pack_id = f"{course_id}-{year_filter}"
        pack_name = f"{course_meta['shortLabel']} {year_filter} 年真题补充包"
        summary = f"从本地题库导出的 {course_meta['name']} {year_filter} 年真题与解析（附 {copied_figs} 张配图）。"

    manifest = {
        "schemaVersion": 1,
        "packId": (pack_id_override or default_pack_id).lower(),
        "type": pack_type,
        "name": pack_name,
        "version": version,
        "author": author,
        "license": license_text,
        "summary": summary,
        "tags": [course_meta.get("school", ""), course_meta.get("code", ""), course_meta.get("subject", "")],
        **({"targetCourseId": course_id} if pack_type == "exam" else {}),
    }
    manifest["tags"] = [t for t in manifest["tags"] if t]
    (stage_dir / "manifest.json").write_bytes(dump_json_bytes(manifest))


def main() -> int:
    parser = argparse.ArgumentParser(description="鲸研·水力学 创意工坊 .jypack.zip 检验与打包工具")
    src_group = parser.add_mutually_exclusive_group(required=True)
    src_group.add_argument("--src", type=Path, help="待打包的资源包根目录（需包含 manifest.json）")
    src_group.add_argument("--export-course", help="从 web/public/data 导出指定内置科目 ID（如 hhu-814）")

    parser.add_argument("--year", type=int, help="配合 --export-course 使用：仅导出单年试卷为 exam 包")
    parser.add_argument("--pack-id", help="覆盖导出时的 manifest.packId")
    parser.add_argument("--version", default="1.0.0", help="导出时写入的包版本号（默认 1.0.0）")
    parser.add_argument("--author", default="鲸研社区贡献者", help="导出时写入的作者署名")
    parser.add_argument("--license", default="仅供个人考研复习与学术交流使用（非商业）", help="导出时写入的许可声明")
    parser.add_argument("--out", type=Path, required=True, help="输出 .jypack.zip 文件路径")
    parser.add_argument("--to-webp", action="store_true", help="将包内 PNG/JPG 图片自动压缩转为 WebP")
    parser.add_argument("--skip-katex", action="store_true", help="跳过本地 Node KaTeX 语法校验")

    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="jypack_work_") as tmp_str:
        work_dir = Path(tmp_str)
        if args.src:
            src_resolved = args.src.resolve()
            if not src_resolved.is_dir():
                print(f"[错误] 找不到目录: {src_resolved}", file=sys.stderr)
                return 1
            shutil.copytree(src_resolved, work_dir, dirs_exist_ok=True)
        else:
            stage_exported_course(
                course_id=args.export_course.strip(),
                year_filter=args.year,
                stage_dir=work_dir,
                pack_id_override=args.pack_id,
                version=args.version,
                author=args.author,
                license_text=args.license,
            )

        if args.to_webp:
            converted_cnt, _ = convert_images_to_webp(work_dir)
            print(f"[图片优化] 已转换 {converted_cnt} 张 PNG/JPG 为 WebP 并更新 JSON 引用。")

        errors, stats = validate_pack_dir(work_dir, skip_katex=args.skip_katex)
        if errors:
            print(f"\n[校验失败] 发现 {len(errors)} 项问题：", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            return 1

        manifest = load_json(work_dir / "manifest.json")
        out_path = args.out.resolve()
        size_bytes, sha256, file_count = write_deterministic_zip(work_dir, out_path)
        size_mb = size_bytes / (1024 * 1024)
        hosting_hint = (
            "符合 D1 站内直传限制 (<= 15 MB)"
            if size_bytes <= MAX_D1_BYTES
            else "超过 15 MB，上架工坊需改用外链 HTTPS URL"
        )

        print("\n=== .jypack.zip 打包完成 ===")
        print(f"输出文件 : {out_path}")
        print(f"packId   : {manifest['packId']} ({manifest['type']}, v{manifest['version']})")
        print(f"包名称   : {manifest['name']}")
        print(f"统计信息 : {json.dumps(stats, ensure_ascii=False)}")
        print(f"包含文件 : {file_count} 个")
        print(f"压缩体积 : {size_bytes:,} bytes ({size_mb:.2f} MB) -> {hosting_hint}")
        print(f"SHA-256  : {sha256}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
