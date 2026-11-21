# -*- coding: utf-8 -*-
"""
Parse `河海大学已整理真题/2023年河海大学814《水力学》考研真题及详细解析.docx` into standardized exam pack
`河海大学已整理数据/2023/2023.json` + `河海大学已整理数据/2023/figures/`.
"""

import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parse_2024_2025 as base_parser

# Extend OMML symbol mappings for 2023 docx
base_parser.GREEK_AND_MATH_MAP.update({
    "κ": r"\kappa ",
    "∑": r"\sum ",
    "∈": r"\in ",
    "Φ": r"\Phi ",
    "–": "-",
    "∫": r"\int ",
})

ROOT = Path(__file__).resolve().parent.parent
DOCX_PATH = ROOT / "河海大学已整理真题" / "2023年河海大学814《水力学》考研真题及详细解析.docx"
OUT_DIR = ROOT / "河海大学已整理数据" / "2023"
FIG_DIR = OUT_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


META_2023 = {
    1:  {"title": "理想液体剪切变形与切应力特性", "chapter": 1, "kps": ["理想液体假设", "牛顿内摩擦定律"], "method": "物理概念定义辨析", "difficulty": 1},
    2:  {"title": "紊流沿程阻力系数与流速关系辨析", "chapter": 4, "kps": ["紊流阻力分区", "达西-韦斯巴赫公式"], "method": "紊流光滑区布拉休斯幂次比例法", "difficulty": 2},
    3:  {"title": "紊流水力粗糙面定义判别", "chapter": 4, "kps": ["紊流阻力分区", "水力粗糙面定义"], "method": "物理概念定义辨析", "difficulty": 2},
    4:  {"title": "明渠临界水深的影响因素辨析", "chapter": 8, "kps": ["临界水深与临界底坡"], "method": "概念偷换词辨析", "difficulty": 2},
    5:  {"title": "恒定总流能量方程的渐变流断面条件", "chapter": 3, "kps": ["恒定总流能量方程"], "method": "物理概念定义辨析", "difficulty": 2},
    6:  {"title": "突然扩大波达公式的推导依据", "chapter": 4, "kps": ["恒定总流动量方程", "恒定总流能量方程"], "method": "物理概念定义辨析", "difficulty": 2},
    7:  {"title": "明渠非恒定流实测垂线对数流速分布辨析", "chapter": 4, "kps": ["普朗特混合长度理论", "断面流速分布"], "method": "物理概念定义辨析", "difficulty": 3},
    8:  {"title": "按相对堰顶厚度判别溢流堰类型", "chapter": 9, "kps": ["堰流分类与基本流量公式"], "method": "堰流与闸孔出流判别及流量公式", "difficulty": 1},
    9:  {"title": "等径有压弯折管总水头线与测压管水头线判别", "chapter": 6, "kps": ["总水头线与测压管水头线"], "method": "总水头线与测压管水头线判据", "difficulty": 2},
    10: {"title": "平坡接陡坡闸下水跃与水面曲线合理性判别", "chapter": 8, "kps": ["明渠水面曲线定性分析", "明渠水跃与跃后水深"], "method": "渐变流微分方程符号判别", "difficulty": 3},
    11: {"title": "水泵进口真空计读数与相对压强换算", "chapter": 2, "kps": ["真空高度(真空度)", "静水压强基本方程"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "mini-calc"},
    12: {"title": "线性剪切层流流速场的流函数求解", "chapter": 5, "kps": ["流函数与速度势函数求解"], "method": "不可压与无旋偏导检验+偏积分求原函数法", "difficulty": 2, "subType": "mini-calc"},
    13: {"title": "圆盘挖去内接正方形阴影平面静水压力中心计算", "chapter": 2, "kps": ["平面静水总压力"], "method": "平面总压力形心法/分块合成法", "difficulty": 3, "subType": "mini-calc"},
    14: {"title": "堰流弗劳德重力相似模型流量换算", "chapter": 13, "kps": ["弗劳德相似准则", "流量比尺换算"], "method": "弗劳德比尺幂次换算法", "difficulty": 1, "subType": "mini-calc"},
    15: {"title": "闸基渗流流网流速势函数与渗流流速计算", "chapter": 11, "kps": ["平面渗流流网", "达西定律与单宽渗流量"], "method": "正交流网段数减一计数法", "difficulty": 4, "subType": "mini-calc"},
    16: {"title": "由沿程水头损失与管壁切应力反求圆管管径", "chapter": 4, "kps": ["圆管均匀流切应力分布"], "method": "圆管切应力线性分布性质", "difficulty": 2, "subType": "mini-calc"},
    17: {"title": "铅直出流管流量与管长无关的临界水深条件", "chapter": 6, "kps": ["简单短管自由出流", "恒定总流能量方程"], "method": "短管自由出流流量公式判别", "difficulty": 3, "subType": "mini-calc"},
    18: {"title": "一维非恒定非均匀流场位变加速度计算", "chapter": 5, "kps": ["欧拉法速度场", "当地加速度与迁移加速度"], "method": "速度场偏导数判别法", "difficulty": 2, "subType": "mini-calc"},
    19: {"title": "由平板闸门动水总压力反求闸前水深", "chapter": 3, "kps": ["恒定总流动量方程", "平板闸孔出流判别"], "method": "能量方程求流量+控制体动量方程求反力", "difficulty": 3, "subType": "mini-calc"},
    20: {"title": "有压管道水击波完整传播周期计算", "chapter": 6, "kps": ["有压管道水击(水锤)"], "method": "水击相长判别与儒氏公式", "difficulty": 1, "subType": "mini-calc"},
    21: {"title": "等面积圆、正方与矩形有压管流量比计算", "chapter": 4, "kps": ["达西-韦斯巴赫公式", "水力最佳断面"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 3, "subType": "mini-calc"},
    22: {"title": "考虑不同动能修正系数的文丘里流量计计算", "chapter": 3, "kps": ["U形水银压差计测压", "恒定总流能量方程"], "method": "两段伯努利方程联立法", "difficulty": 3, "subType": "mini-calc"},
    23: {"title": "并联对称折管不同高程点动水压强大小判别", "chapter": 6, "kps": ["长管串并联与三水池问题", "恒定总流能量方程"], "method": "总水头线与测压管水头线判据", "difficulty": 2, "subType": "blank"},
    24: {"title": "多孔自由出流实用堰过流流量计算", "chapter": 9, "kps": ["堰流分类与基本流量公式", "平板闸孔出流判别"], "method": "堰流与闸孔出流判别及流量公式", "difficulty": 2, "subType": "mini-calc"},
    25: {"title": "尼古拉兹曲线光滑区水头损失与流速幂次关系", "chapter": 4, "kps": ["紊流阻力分区", "达西-韦斯巴赫公式"], "method": "紊流光滑区布拉休斯幂次比例法", "difficulty": 2, "subType: ": "blank"},
    26: {
        "title": "倾斜圆管内圆柱体等速下滑测定润滑油动力黏度",
        "chapter": 1,
        "kps": ["牛顿内摩擦定律", "环形/圆盘间隙黏性阻力矩"],
        "method": "分层液体切应力连续与速度叠加法",
        "difficulty": 2,
        "rubric": [
            {"label": "计算环形油膜间隙厚度 δ = (D - d)/2 = 0.5 mm 及圆柱侧面积 A = πdL", "pts": 6},
            {"label": "列出圆柱等速下滑沿管轴力平衡方程 G·sin45° = τ·πdL = μ(U/δ)πdL", "pts": 8},
            {"label": "代入数值准确解得润滑油动力黏性系数 μ ≈ 0.163 Pa·s（单位正确）", "pts": 6},
        ],
    },
    27: {
        "title": "带水银测压计密闭水箱下部圆柱体静水总压力计算",
        "chapter": 2,
        "kps": ["U形水银压差计测压", "圆柱曲面静水总压力", "压力体图与虚压力体"],
        "method": "等效自由液面+水平投影与铅垂压力体合成法",
        "difficulty": 4,
        "rubric": [
            {"label": "由水银测压计求得液面相对压强水头 h0 ≈ 1.00 m 及等效自由液面距圆心高差 Hp ≈ 2.90 m", "pts": 6},
            {"label": "识别受压圆弧段 AB，求得水平静水压力 Px ≈ 40.07 kN（或按 45° 斜径简算 39.83 kN，水平向右）", "pts": 6},
            {"label": "求得铅垂有效压力体体积与铅垂分力 Pz ≈ 55.78 kN（向上），合成总压力 P ≈ 68.68 kN 及仰角 54.3°", "pts": 8},
        ],
    },
    28: {
        "title": "水平面内 60° 渐缩弯管水流作用力计算",
        "chapter": 3,
        "kps": ["恒定总流连续性方程", "恒定总流能量方程", "恒定总流动量方程", "弯管/底坎水流作用力"],
        "method": "能量方程求流量+控制体动量方程求反力",
        "difficulty": 3,
        "rubric": [
            {"label": "求得 A、B 断面流速 vA = 3.183 m/s、vB = 5.659 m/s，列水平能量方程求得 pB ≈ 109.05 kPa", "pts": 7},
            {"label": "取弯管控制体列水平面 x、y 向动量方程求得水流对弯管分力 Fx ≈ 2.84 kN、Fy ≈ 2.16 kN", "pts": 9},
            {"label": "合成总作用力 F ≈ 3.57 kN 并指明方向（与 A 管来流方向夹角 37.23° 指向弯管外侧）", "pts": 4},
        ],
    },
    29: {
        "title": "平面二维流场角变形率、流函数与流速势函数求解",
        "chapter": 5,
        "kps": ["平面不可压缩流连续性方程", "无旋流判据", "流函数与速度势函数求解"],
        "method": "不可压与无旋偏导检验+偏积分求原函数法",
        "difficulty": 3,
        "rubric": [
            {"label": "求出一阶速度偏导数，算得平面微团角变形率 εxy = (∂uy/∂x + ∂ux/∂y)/2 = -2y（或 γxy = -4y）", "pts": 6},
            {"label": "验证连续性方程 ∂ux/∂x + ∂uy/∂y = 0 成立，偏积分求得流函数 ψ = x²y - y³/3 + C1", "pts": 7},
            {"label": "验证无旋条件 ωz = 0 成立，偏积分求得流速势函数 φ = x³/3 - xy² + C2（或负梯度定义反号）", "pts": 7},
        ],
    },
    30: {
        "title": "半圆深槽复式断面运河明渠均匀流总流量计算",
        "chapter": 7,
        "kps": ["梯形断面水力要素", "明渠均匀流曼宁公式"],
        "method": "水力要素计算+曼宁公式+水力深度Fr判据",
        "difficulty": 3,
        "rubric": [
            {"label": "按复式断面铅直虚线分割主槽与左右滩地（指明水体内部铅直分割线不计入湿周）", "pts": 4},
            {"label": "计算中间深槽区面积 A1 ≈ 80.55 m²、湿周 χ1 = 6π ≈ 18.85 m，由曼宁公式得 Q1 ≈ 387.26 m³/s", "pts": 8},
            {"label": "计算两侧对称滩地面积 A2 = 30 m²、湿周 χ2 ≈ 18.32 m、流量 Q滩 ≈ 152.17 m³/s，汇总得 Q ≈ 539.43 m³/s", "pts": 8},
        ],
    },
}
# Fix typo in key name of Q25
META_2023[25]["subType"] = "blank"
del META_2023[25]["subType: "]


def sanitize_2023_text(s: str) -> str:
    if not s:
        return s
    replacements = [
        ("真题讲解口径（判 √）：", "实验与工程实测口径（判 √）："),
        ("，讲解视频（BV1czsN6EEhN）明确据实测工程认识判为 √。", "，故按水力学实验实测规律判为 √。"),
        ("部分讲解视频（含 BV1czsN6EEhN）", "部分常见参考解答"),
        ("（亦为视频常见解法）", "（手算近似口径）"),
        ("讲解视频", "部分参考解答"),
        ("视频", "参考资料"),
        ("BV1czsN6EEhN", ""),
    ]
    for old, new in replacements:
        s = s.replace(old, new)
    return s.strip()


def normalize_stem_and_extract_note(stem: str, qtype: str) -> tuple[str, str]:
    notes = []
    # Extract editorial parenthetical remarks like （原回忆件...） or （原卷误印...） or （注：...）
    def repl_note(m: re.Match) -> str:
        notes.append(m.group(1).strip())
        return ""

    stem = re.sub(r"（((?:原回忆件|原卷误印|注：原卷误印|注：疑原回忆|注：图中标注)[^）]+)）", repl_note, stem)
    if qtype == "judge":
        stem = re.sub(r"[（(]\s*[）)]\s*$", "", stem).strip()
    elif qtype == "calc":
        stem = re.sub(r"[（(]\d+\s*分[）)]\s*$", "", stem).strip()
    elif qtype == "fill":
        # Normalize 4+ underscores outside math to standard 8 underscores
        parts = re.split(r"(\$[^$]+\$)", stem)
        for i in range(0, len(parts), 2):
            parts[i] = re.sub(r"_{3,}", "________", parts[i])
        stem = "".join(parts)

    return stem.strip(), "；".join(notes)


def main():
    with zipfile.ZipFile(DOCX_PATH) as zf:
        rels = {r.attrib["Id"]: r.attrib["Target"] for r in ET.fromstring(zf.read("word/_rels/document.xml.rels"))}
        body = ET.fromstring(zf.read("word/document.xml")).find("w:body", base_parser.NS)

        questions = {}
        analysis_buf = {k: [] for k in range(1, 31)}
        pitfalls_buf = {k: [] for k in range(1, 31)}

        part1 = False
        part2 = False
        sec_offset = 0  # 0 for judge, 10 for fill, 25 for calc
        cur_q = None

        children = list(body)
        idx = 0
        while idx < len(children):
            el = children[idx]
            ctag = el.tag.split("}")[-1]
            raw_txt = "".join(el.itertext()).strip()

            if ctag == "p" and raw_txt.startswith("第一部分："):
                part1 = True
                idx += 1
                continue
            if ctag == "p" and raw_txt.startswith("第二部分："):
                part2 = True
                cur_q = None
                idx += 1
                continue

            if ctag == "p" and raw_txt.startswith("一、是非题"):
                sec_offset = 0
                cur_q = None
                idx += 1
                continue
            if ctag == "p" and raw_txt.startswith("二、填空题"):
                sec_offset = 10
                cur_q = None
                idx += 1
                continue
            if ctag == "p" and raw_txt.startswith("三、解答题"):
                sec_offset = 25
                cur_q = None
                idx += 1
                continue

            # --- Part 1: Exam Stems ---
            if part1 and not part2 and ctag == "p":
                md, imgs = base_parser.paragraph_to_markdown(el, rels)
                md = sanitize_2023_text(md)

                m_q = re.match(r"^(\d{1,2})\.\s*(.+)$", md, flags=re.DOTALL)
                if m_q:
                    local_no = int(m_q.group(1))
                    qno = sec_offset + local_no
                    qtype = "judge" if qno <= 10 else ("fill" if qno <= 25 else "calc")
                    score = 2 if qno <= 25 else 20
                    stem_clean, note_txt = normalize_stem_and_extract_note(m_q.group(2).strip(), qtype)
                    questions[qno] = {
                        "id": f"2023-{qno:02d}",
                        "year": 2023,
                        "no": qno,
                        "type": qtype,
                        "score": score,
                        "title": META_2023[qno]["title"],
                        "stem": stem_clean,
                        "note": note_txt,
                        "figures": [],
                        "shortAnswer": "",
                        "judgeAnswer": None,
                        "answer": "",
                        "analysis": "",
                        "analysisFigures": [],
                        "pitfalls": "",
                    }
                    cur_q = qno
                    idx += 1
                    continue

                if imgs and cur_q is not None:
                    if idx + 1 < len(children) and "".join(children[idx + 1].itertext()).strip().startswith("原卷附图"):
                        idx += 1
                    for i_im, media_rel in enumerate(imgs):
                        suf = "" if i_im == 0 else f"_{i_im+1}"
                        fname = f"q{cur_q:02d}_orig{suf}.png"
                        (FIG_DIR / fname).write_bytes(zf.read("word/" + media_rel))
                        questions[cur_q]["figures"].append({"src": f"figures/{fname}", "caption": f"题 {cur_q} 图"})
                    idx += 1
                    continue

                if md and cur_q is not None and not md.startswith("原卷附图"):
                    extra_clean, extra_note = normalize_stem_and_extract_note(md, questions[cur_q]["type"])
                    questions[cur_q]["stem"] += "\n\n" + extra_clean
                    if extra_note:
                        questions[cur_q]["note"] = (
                            questions[cur_q]["note"] + "；" + extra_note if questions[cur_q]["note"] else extra_note
                        )
                idx += 1
                continue

            # --- Part 2: Solutions ---
            if part2 and ctag == "p":
                md, imgs = base_parser.paragraph_to_markdown(el, rels)
                md = sanitize_2023_text(md)

                m_sol = re.match(r"^第\s*(\d{1,2})\s*题\s*【参考答案】\s*(.+)$", md)
                if m_sol:
                    local_no = int(m_sol.group(1))
                    cur_q = sec_offset + local_no
                    ans_txt = m_sol.group(2).strip()
                    questions[cur_q]["answer"] = ans_txt
                    questions[cur_q]["shortAnswer"] = ans_txt
                    if cur_q <= 10:
                        is_true = "√" in ans_txt.split("（")[0]
                        questions[cur_q]["judgeAnswer"] = is_true
                        questions[cur_q]["shortAnswer"] = "√" if is_true else "×"
                        if "（" not in ans_txt:
                            questions[cur_q]["answer"] = "√（正确）" if is_true else "×（错误）"
                    idx += 1
                    continue

                if cur_q is None:
                    idx += 1
                    continue

                if imgs:
                    if idx + 1 < len(children) and "".join(children[idx + 1].itertext()).strip().startswith("解析分析附图"):
                        idx += 1
                    for i_im, media_rel in enumerate(imgs):
                        suf = "" if i_im == 0 else f"_{i_im+1}"
                        fname = f"q{cur_q:02d}_sol{suf}.png"
                        (FIG_DIR / fname).write_bytes(zf.read("word/" + media_rel))
                        questions[cur_q]["analysisFigures"].append(
                            {"src": f"figures/{fname}", "caption": f"第 {cur_q} 题解析示意图"}
                        )
                    idx += 1
                    continue

                if md.startswith("解析分析附图"):
                    idx += 1
                    continue

                if md.startswith("【详细解析】"):
                    md = md.replace("【详细解析】", "", 1).strip()

                if md.startswith(("【勘误说明】", "4. 勘误附注：")):
                    cleaned_pit = re.sub(r"^(?:【勘误说明】|4\.\s*勘误附注：)\s*", "", md).strip()
                    pitfalls_buf[cur_q].append(cleaned_pit)
                elif md and md != "【流网严格判读与题干数据勘误说明】" and md != "【多视角校核与争议辨析】":
                    analysis_buf[cur_q].append(md)

            idx += 1

    final_questions = []
    for qno in range(1, 31):
        q = questions[qno]
        q["analysis"] = "\n\n".join(analysis_buf[qno]).strip()
        q["pitfalls"] = "\n\n".join(pitfalls_buf[qno]).strip()
        meta = META_2023[qno]
        q["chapter"] = meta["chapter"]
        q["kps"] = meta["kps"]
        q["method"] = meta["method"]
        q["difficulty"] = meta["difficulty"]
        if "subType" in meta:
            q["subType"] = meta["subType"]
        if "rubric" in meta:
            q["rubric"] = meta["rubric"]
        final_questions.append(q)

    paper = {
        "year": 2023,
        "code": "814",
        "subject": "水力学",
        "school": "河海大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": False,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试，不允许使用计算器。",
            "除特别说明外，统一取重力加速度 $g = 9.81\\,\\mathrm{m/s^2}$，水密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$。",
            "题型与分值：一、是非题（10×2=20 分）；二、填空题（15×2=30 分）；三、解答题（5×20=100 分）。"
        ],
        "sections": [
            {
                "id": "judge",
                "title": "一、是非题",
                "description": "共 10 小题，每小题 2 分，共 20 分。",
                "range": [1, 10],
                "scorePerQuestion": 2,
                "totalScore": 20
            },
            {
                "id": "fill",
                "title": "二、填空题",
                "description": "共 15 小题，每小题 2 分，共 30 分。",
                "range": [11, 25],
                "scorePerQuestion": 2,
                "totalScore": 30
            },
            {
                "id": "calc",
                "title": "三、解答题",
                "description": "共 5 小题，每小题 20 分，共 100 分。",
                "range": [26, 30],
                "scorePerQuestion": 20,
                "totalScore": 100
            }
        ],
        "questions": final_questions,
    }

    out_json = OUT_DIR / "2023.json"
    out_json.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote standardized HHU 2023 JSON ({len(final_questions)} questions) -> {out_json}")


if __name__ == "__main__":
    main()
