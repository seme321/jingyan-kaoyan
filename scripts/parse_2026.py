# -*- coding: utf-8 -*-
"""
Parse `2026年河海大学814水力学真题及详细解析.docx` into structured JSON + LaTeX + WebP figures.
Designed to generalize cleanly to other years (2024, 2025, ...).
"""

import io
import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DOCX_PATH = ROOT / "河海大学已整理真题" / "2026年河海大学814水力学真题及详细解析.docx"
if not DOCX_PATH.exists():
    DOCX_PATH = ROOT / "2026年河海大学814水力学真题及详细解析.docx"
OUT_DATA_DIR = ROOT / "web" / "public" / "data"
OUT_FIG_DIR = OUT_DATA_DIR / "figures" / "2026"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}
W = "{" + NS["w"] + "}"
M = "{" + NS["m"] + "}"
R = "{" + NS["r"] + "}"

GREEK_AND_MATH_MAP = {
    "α": r"\alpha ",
    "β": r"\beta ",
    "γ": r"\gamma ",
    "δ": r"\delta ",
    "ζ": r"\zeta ",
    "θ": r"\theta ",
    "λ": r"\lambda ",
    "μ": r"\mu ",
    "ν": r"\nu ",
    "π": r"\pi ",
    "ρ": r"\rho ",
    "τ": r"\tau ",
    "φ": r"\varphi ",
    "χ": r"\chi ",
    "ψ": r"\psi ",
    "ω": r"\omega ",
    "Δ": r"\Delta ",
    "∂": r"\partial ",
    "∇": r"\nabla ",
    "∝": r"\propto ",
    "≈": r"\approx ",
    "≠": r"\neq ",
    "≤": r"\le ",
    "≥": r"\ge ",
    "≫": r"\gg ",
    "≪": r"\ll ",
    "⟹": r"\Longrightarrow ",
    "×": r"\times ",
    "·": r"\cdot ",
    "°": r"^{\circ}",
    "′": r"'",
    "\u2003": r"\quad ",
    "\u2009": r"\, ",
    "～": r"\sim ",
}

OPERATORS = {"tan", "sin", "cos", "arctan", "arcsin", "arccos", "ln", "log", "max", "min", "exp"}


def is_cjk_or_fullwidth(ch: str) -> bool:
    code = ord(ch)
    return (
        0x4E00 <= code <= 0x9FFF
        or 0x3000 <= code <= 0x303F
        or 0xFF00 <= code <= 0xFFEF
    )


def convert_math_text(txt: str, is_plain: bool = False) -> str:
    if not txt:
        return ""

    # Handle pure operator names when marked upright
    stripped = txt.strip()
    lead_space = r"\, " if txt.startswith(" ") and stripped else ""
    trail_space = r"\, " if txt.endswith(" ") and stripped and not txt.isspace() else ""

    if txt.isspace():
        return r"\, "

    if is_plain and stripped in OPERATORS:
        return f"{lead_space}\\{stripped} "

    # If plain upright unit/label without CJK and containing letters (e.g. " kN/m", "Pa·s", "Hg", "eq")
    if is_plain and any(c.isalpha() for c in stripped) and not any(is_cjk_or_fullwidth(c) for c in stripped):
        unit_body = stripped.replace("·", r"\cdot ")
        return f"{lead_space}\\mathrm{{{unit_body}}}{trail_space}"

    # Tokenize into CJK chunks vs math characters
    out = []
    i = 0
    n = len(txt)
    while i < n:
        ch = txt[i]
        if is_cjk_or_fullwidth(ch):
            j = i
            while j < n and (is_cjk_or_fullwidth(txt[j]) or txt[j] == " "):
                j += 1
            cjk_seg = txt[i:j].strip()
            if cjk_seg:
                out.append(f"\\text{{{cjk_seg}}}")
            i = j
        elif ch in GREEK_AND_MATH_MAP:
            out.append(GREEK_AND_MATH_MAP[ch])
            i += 1
        elif ch == "<":
            out.append(" < ")
            i += 1
        elif ch == ">":
            out.append(" > ")
            i += 1
        else:
            out.append(ch)
            i += 1
    res = "".join(out)
    # Recognize multi-letter hydraulic dimensionless numbers in italic math if needed (Fr, Re)
    return res


def omml_to_latex(el: ET.Element) -> str:
    tag = el.tag.split("}")[-1]

    if tag in ("oMathPara", "oMath", "e", "num", "den", "sub", "sup", "deg"):
        parts = [omml_to_latex(c) for c in el]
        return "".join(parts).strip()

    if tag in ("oMathParaPr", "rPr", "fPr", "radPr", "sSubPr", "sSupPr", "sSubSupPr", "dPr", "accPr", "naryPr", "ctrlPr"):
        return ""

    if tag == "r":
        sty_el = el.find("m:rPr/m:sty", NS)
        is_plain = sty_el is not None and sty_el.attrib.get(M + "val") == "p"
        t_el = el.find("m:t", NS)
        txt = t_el.text if (t_el is not None and t_el.text) else ""
        return convert_math_text(txt, is_plain=is_plain)

    if tag == "f":
        num = omml_to_latex(el.find("m:num", NS))
        den = omml_to_latex(el.find("m:den", NS))
        return f"\\frac{{{num}}}{{{den}}}"

    if tag == "rad":
        deg_hide = el.find("m:radPr/m:degHide", NS)
        hide = deg_hide is not None and deg_hide.attrib.get(M + "val") in ("1", "on", "true")
        deg_el = el.find("m:deg", NS)
        deg = omml_to_latex(deg_el) if (deg_el is not None and not hide) else ""
        base = omml_to_latex(el.find("m:e", NS))
        if deg:
            return f"\\sqrt[{deg}]{{{base}}}"
        return f"\\sqrt{{{base}}}"

    if tag == "sSub":
        base = omml_to_latex(el.find("m:e", NS))
        sub = omml_to_latex(el.find("m:sub", NS))
        return f"{{{base}}}_{{{sub}}}"

    if tag == "sSup":
        base = omml_to_latex(el.find("m:e", NS))
        sup = omml_to_latex(el.find("m:sup", NS))
        return f"{{{base}}}^{{{sup}}}"

    if tag == "sSubSup":
        base = omml_to_latex(el.find("m:e", NS))
        sub = omml_to_latex(el.find("m:sub", NS))
        sup = omml_to_latex(el.find("m:sup", NS))
        return f"{{{base}}}_{{{sub}}}^{{{sup}}}"

    if tag == "d":
        dpr = el.find("m:dPr", NS)
        beg = "("
        end = ")"
        if dpr is not None:
            b_el = dpr.find("m:begChr", NS)
            e_el = dpr.find("m:endChr", NS)
            if b_el is not None:
                beg = b_el.attrib.get(M + "val", "(")
            if e_el is not None:
                end = e_el.attrib.get(M + "val", ")")
        l_map = {"(": "(", "[": "[", "{": r"\{", "|": "|", "": "."}
        r_map = {")": ")", "]": "]", "}": r"\}", "|": "|", "": "."}
        l_tok = l_map.get(beg, beg)
        r_tok = r_map.get(end, end)
        es = [omml_to_latex(e_child) for e_child in el.findall("m:e", NS)]
        inner = ", ".join(es)
        return f"\\left{l_tok} {inner} \\right{r_tok}"

    if tag == "acc":
        chr_el = el.find("m:accPr/m:chr", NS)
        acc_chr = chr_el.attrib.get(M + "val", "⃗") if chr_el is not None else "⃗"
        base = omml_to_latex(el.find("m:e", NS))
        if acc_chr in ("⃗", "\u20d7"):
            return f"\\vec{{{base}}}"
        if acc_chr in ("̄", "\u0304", "¯"):
            return f"\\overline{{{base}}}"
        return f"\\hat{{{base}}}"

    if tag == "nary":
        chr_el = el.find("m:naryPr/m:chr", NS)
        op_chr = chr_el.attrib.get(M + "val", "∫") if chr_el is not None else "∫"
        op_cmd = {"∫": r"\int", "∑": r"\sum", "∏": r"\prod"}.get(op_chr, r"\int")
        sub_hide = el.find("m:naryPr/m:subHide", NS)
        sup_hide = el.find("m:naryPr/m:supHide", NS)
        s_hide = sub_hide is not None and sub_hide.attrib.get(M + "val") in ("1", "on", "true")
        p_hide = sup_hide is not None and sup_hide.attrib.get(M + "val") in ("1", "on", "true")
        sub_el = el.find("m:sub", NS)
        sup_el = el.find("m:sup", NS)
        sub = omml_to_latex(sub_el) if (sub_el is not None and not s_hide) else ""
        sup = omml_to_latex(sup_el) if (sup_el is not None and not p_hide) else ""
        body = omml_to_latex(el.find("m:e", NS))
        lim = ""
        if sub:
            lim += f"_{{{sub}}}"
        if sup:
            lim += f"^{{{sup}}}"
        return f"{op_cmd}{lim} {body}"

    raise ValueError(f"Unhandled OMML tag: {tag}")


def clean_latex(tex: str) -> str:
    # Tidy redundant whitespace
    tex = re.sub(r"[ \t]+", " ", tex).strip()
    # Fix OMML superscript degree & primes so KaTeX never sees double superscripts
    tex = tex.replace(r"^{^{\circ}}", r"^{\circ}")
    tex = tex.replace(r"^{''}", r"^{\prime\prime}")
    tex = tex.replace(r"^{'}", r"^{\prime}")
    # Clean `{x}_{1}` -> `x_{1}` when base is single ASCII char for cleaner reading
    tex = re.sub(r"\{([A-Za-z0-9])\}_", r"\1_", tex)
    tex = re.sub(r"\{([A-Za-z0-9])\}\^", r"\1^", tex)
    return tex


def paragraph_to_markdown(p: ET.Element, rels: dict) -> tuple[str, list[str]]:
    """Return (markdown_text, list_of_media_paths_in_paragraph)."""
    images = []
    for blip in p.findall(".//a:blip", NS):
        rid = blip.attrib.get(R + "embed")
        if rid and rid in rels:
            images.append(rels[rid])

    chunks = []
    for child in p:
        ctag = child.tag.split("}")[-1]
        if ctag == "r":
            txt = "".join(t.text or "" for t in child.findall(".//w:t", NS))
            chunks.append(txt)
        elif ctag == "oMath":
            tex = clean_latex(omml_to_latex(child))
            if tex:
                chunks.append(f"${tex}$")
        elif ctag == "oMathPara":
            omaths = child.findall("m:oMath", NS)
            tex = " \\quad ".join(clean_latex(omml_to_latex(om)) for om in omaths)
            if tex:
                chunks.append(f"\n\n$$\n{tex}\n$$\n\n")
        elif ctag == "hyperlink":
            txt = "".join(t.text or "" for t in child.findall(".//w:t", NS))
            chunks.append(txt)
    text = "".join(chunks).replace("\u200b", "").strip()
    return text, images


# Curated 814 metadata for all 30 questions of 2026
QUESTION_META = {
    1:  {"chapter": 2,  "kps": ["静水压强基本方程", "水头与能量量纲"], "method": "单位重量与单位体积量纲辨析", "difficulty": 2},
    2:  {"chapter": 8,  "kps": ["断面单位能量(比能)", "明渠渐变流能量变化"], "method": "比能沿程导数判别法", "difficulty": 2},
    3:  {"chapter": 4,  "kps": ["达西-韦斯巴赫公式", "紊流阻力分区", "断面流速分布"], "method": "概念偷换词辨析", "difficulty": 3},
    4:  {"chapter": 8,  "kps": ["明渠水面曲线定性分析", "急流减速水面线"], "method": "渐变流微分方程符号判别", "difficulty": 3},
    5:  {"chapter": 5,  "kps": ["欧拉法速度场", "当地加速度与迁移加速度", "恒定流与均匀流判别"], "method": "速度场偏导数判别法", "difficulty": 2},
    6:  {"chapter": 6,  "kps": ["恒定总流能量方程", "有压渐扩管压强变化"], "method": "伯努利方程多因素反例法", "difficulty": 2},
    7:  {"chapter": 1,  "kps": ["理想液体假设", "牛顿内摩擦定律"], "method": "物理概念定义辨析", "difficulty": 2},
    8:  {"chapter": 3,  "kps": ["断面平均流速", "流量与过水断面"], "method": "物理概念定义辨析", "difficulty": 1},
    9:  {"chapter": 8,  "kps": ["缓坡水面曲线(M1/M2/M3)", "断面单位能量(比能)"], "method": "比能沿程导数判别法", "difficulty": 2},
    10: {"chapter": 3,  "kps": ["流线与迹线", "恒定流运动特征"], "method": "物理概念定义辨析", "difficulty": 1},
    11: {"chapter": 1,  "kps": ["连续介质假设"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "blank"},
    12: {"chapter": 2,  "kps": ["平面静水总压力", "梯形断面静水压力计算"], "method": "平面总压力形心法/分块合成法", "difficulty": 2, "subType": "mini-calc"},
    13: {"chapter": 13, "kps": ["弗劳德相似准则", "流量比尺换算"], "method": "弗劳德比尺幂次换算法", "difficulty": 2, "subType": "mini-calc"},
    14: {"chapter": 3,  "kps": ["恒定总流动量方程", "弯管动量变化矢量"], "method": "控制体正交分解矢量法", "difficulty": 2, "subType": "mini-calc"},
    15: {"chapter": 6,  "kps": ["虹吸管水力计算", "真空高度(真空度)", "短管能量方程"], "method": "两段伯努利方程联立法", "difficulty": 3, "subType": "mini-calc"},
    16: {"chapter": 6,  "kps": ["简单短管自由出流", "作用水头与流量关系"], "method": "短管自由出流流量公式判别", "difficulty": 2, "subType": "short-answer"},
    17: {"chapter": 13, "kps": ["河工模型阻力相似", "糙率比尺与模型加糙"], "method": "模型试验工程措施分析", "difficulty": 2, "subType": "blank"},
    18: {"chapter": 8,  "kps": ["明渠渐变流基本微分方程", "总水头坡度与测压管坡度"], "method": "渐变流微分方程代数变形", "difficulty": 3, "subType": "mini-calc"},
    19: {"chapter": 10, "kps": ["底流消能判别", "水跃衔接形式", "矩形明渠共轭水深"], "method": "共轭水深与尾水深对比判据", "difficulty": 3, "subType": "short-answer"},
    20: {"chapter": 9,  "kps": ["平板闸孔出流判别", "闸孔自由出流流量公式"], "method": "闸孔流量公式直代法", "difficulty": 2, "subType": "mini-calc"},
    21: {"chapter": 4,  "kps": ["圆管均匀流切应力分布", "管轴对称边界条件"], "method": "圆管切应力线性分布性质", "difficulty": 2, "subType": "mini-calc"},
    22: {"chapter": 11, "kps": ["平面渗流流网", "达西定律与单宽渗流量"], "method": "正交流网段数减一计数法", "difficulty": 2, "subType": "mini-calc"},
    23: {"chapter": 4,  "kps": ["沿程水头损失规律", "梯级水电站水力开发原理"], "method": "能量方程与沿程损失对比分析", "difficulty": 2, "subType": "short-answer"},
    24: {"chapter": 6,  "kps": ["有压管道水击(水锤)", "直接与间接水击判别", "儒可夫斯基公式"], "method": "水击相长判别与儒氏公式", "difficulty": 2, "subType": "mini-calc"},
    25: {"chapter": 8,  "kps": ["明渠非恒定流涌波", "逆行正波(涨水波)"], "method": "闸门启闭四类涌波速判", "difficulty": 2, "subType": "short-answer"},
    26: {
        "chapter": 1,
        "kps": ["牛顿内摩擦定律", "双层液体平板剪切流"],
        "method": "分层液体切应力连续与速度叠加法",
        "difficulty": 3,
        "rubric": [
            {"label": "写出两液层线性速度梯度与牛顿内摩擦定律表达式", "pts": 6},
            {"label": "利用液-液交界面切应力相等求得界面速度 v = 0.1875 m/s", "pts": 8},
            {"label": "求得切应力 τ = 312.5 Pa 及所需水平拉力 F = τA = 50.0 N", "pts": 6},
        ],
    },
    27: {
        "chapter": 2,
        "kps": ["U形水银压差计测压", "圆柱曲面静水总压力", "压力体图与虚压力体"],
        "method": "等效自由液面+水平投影与铅垂压力体合成法",
        "difficulty": 4,
        "rubric": [
            {"label": "由水银压差计正确求得 C 点及圆心 O 点相对压强（或等效液面深度）", "pts": 6},
            {"label": "求得水平分力 Px = pO·Ax = 171.71 kN（水平向右）", "pts": 5},
            {"label": "正确分析虚压力体方向并求得铅垂分力 Pz = γVz = 12.33 kN（竖直向下）", "pts": 5},
            {"label": "合成总压力 P = 172.16 kN、夹角 α = 4.11°（右下方，作用线过圆心 O）", "pts": 4},
        ],
    },
    28: {
        "chapter": 3,
        "kps": ["恒定总流能量方程", "恒定总流动量方程", "明渠底坎水流作用力"],
        "method": "能量方程求流量+控制体动量方程求反力",
        "difficulty": 4,
        "rubric": [
            {"label": "由几何关系求得下游水深 h2 = h1 - Δh - a = 1.60 m", "pts": 4},
            {"label": "对 1—1、2—2 断面列能量方程解得流量 Q = 1.18 m³/s", "pts": 8},
            {"label": "取控制体列水平动量方程求得水流对坎底水平作用力 R' = 6.89 kN（向右）", "pts": 8},
        ],
    },
    29: {
        "chapter": 5,
        "kps": ["平面不可压缩流连续性方程", "无旋流判据", "流函数与速度势函数求解"],
        "method": "不可压与无旋偏导检验+偏积分求原函数法",
        "difficulty": 3,
        "rubric": [
            {"label": "检验 ∂u/∂x + ∂v/∂y = 0，判定存在流函数 ψ", "pts": 4},
            {"label": "积分求得流函数 ψ = -3/2 x² + 2xy + 3/2 y² + C1（或负号约定等价式）", "pts": 6},
            {"label": "检验旋转角速度 ωz = 0（∂v/∂x = ∂u/∂y = 3），判定存在速度势函数 φ", "pts": 4},
            {"label": "积分求得速度势函数 φ = x² + 3xy - y² + C2（或负号约定等价式）", "pts": 6},
        ],
    },
    30: {
        "chapter": 7,
        "kps": ["明渠均匀流曼宁公式", "梯形断面水力要素", "弗劳德数判急缓流", "明渠雷诺数判层紊流"],
        "method": "水力要素计算+曼宁公式+水力深度Fr判据",
        "difficulty": 3,
        "rubric": [
            {"label": "正确算出梯形过水面积 A=26 m²、湿周 χ=17.944 m、水力半径 R=1.449 m 及底坡 i=0.0004", "pts": 6},
            {"label": "由曼宁公式求得流速 v=1.024 m/s 与流量 Q=26.63 m³/s", "pts": 6},
            {"label": "用水力深度 h̄=A/B=1.529 m 求得 Fr=0.264 < 1，判为缓流", "pts": 4},
            {"label": "求得明渠雷诺数 ReR=1.48×10⁶ ≫ 500，判为紊流", "pts": 4},
        ],
    },
}


def export_webp(zf: zipfile.ZipFile, media_rel: str, dest_name: str) -> str:
    OUT_FIG_DIR.mkdir(parents=True, exist_ok=True)
    raw = zf.read("word/" + media_rel)
    img = Image.open(io.BytesIO(raw))
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    out_path = OUT_FIG_DIR / dest_name
    img.save(out_path, format="WEBP", quality=92, method=6)
    return f"data/figures/2026/{dest_name}"


def main():
    with zipfile.ZipFile(DOCX_PATH) as zf:
        rels_xml = ET.fromstring(zf.read("word/_rels/document.xml.rels"))
        rels = {r.attrib["Id"]: r.attrib["Target"] for r in rels_xml}
        doc_xml = ET.fromstring(zf.read("word/document.xml"))
        body = doc_xml.find("w:body", NS)

        # Parse quick-answer tables for concise summary answers
        short_answers = {}
        tables = body.findall("w:tbl", NS)
        if len(tables) >= 2:
            # Table 0: Judge 1..10
            rows0 = tables[0].findall("w:tr", NS)
            nums = ["".join(tc.itertext()).strip() for tc in rows0[0].findall("w:tc", NS)][1:]
            vals = ["".join(tc.itertext()).strip() for tc in rows0[1].findall("w:tc", NS)][1:]
            for k, v in zip(nums, vals):
                short_answers[int(k)] = v
            # Table 1: Q11..30 concise answers
            rows1 = tables[1].findall("w:tr", NS)[1:]
            for tr in rows1:
                cells = []
                for tc in tr.findall("w:tc", NS):
                    ps = [paragraph_to_markdown(p, rels)[0] for p in tc.findall("w:p", NS)]
                    cells.append(" ".join(x for x in ps if x).strip())
                if len(cells) >= 4:
                    if cells[0].isdigit():
                        short_answers[int(cells[0])] = cells[1]
                    if cells[2].isdigit():
                        short_answers[int(cells[2])] = cells[3]

        # Iterate body paragraphs
        paras = []
        for child in body:
            if child.tag.split("}")[-1] == "p":
                md, imgs = paragraph_to_markdown(child, rels)
                paras.append((md, imgs))

        # Split into Upper (stems) and Lower (detailed analyses)
        lower_start = next(i for i, (md, _) in enumerate(paras) if "真题参考答案与详细解析" in md)

        questions = {}
        calc_global_note = ""

        # --- Parse Upper Part (Stems + Original Exam Figures) ---
        cur_q = None
        i = 0
        while i < lower_start:
            md, imgs = paras[i]
            if md.startswith("注：除特别说明外"):
                calc_global_note = md
                i += 1
                continue

            m_q = re.match(r"^(\d{1,2})\.\s*(.+)$", md, flags=re.DOTALL)
            if m_q:
                qno = int(m_q.group(1))
                stem_text = m_q.group(2).strip()
                # Strip trailing （　　） on judge questions for cleaner stem display
                if qno <= 10:
                    stem_text = re.sub(r"[（(]\s*[）)]\s*$", "", stem_text).strip()
                qtype = "judge" if qno <= 10 else ("fill" if qno <= 25 else "calc")
                score = 2 if qno <= 25 else 20
                questions[qno] = {
                    "id": f"2026-{qno:02d}",
                    "year": 2026,
                    "no": qno,
                    "type": qtype,
                    "score": score,
                    "title": "",
                    "stem": stem_text,
                    "note": calc_global_note if qno >= 26 else "",
                    "figures": [],
                    "shortAnswer": short_answers.get(qno, ""),
                    "judgeAnswer": (short_answers.get(qno) == "√") if qno <= 10 else None,
                    "answer": "",
                    "analysis": "",
                    "analysisFigures": [],
                    "pitfalls": "",
                }
                cur_q = qno
                i += 1
                continue

            if imgs and cur_q is not None:
                # Look ahead for figure caption
                caption = ""
                if i + 1 < lower_start and paras[i + 1][0].startswith("图 "):
                    caption = re.sub(r"（原卷配图）$", "", paras[i + 1][0]).strip()
                    i += 1
                for idx_img, media_rel in enumerate(imgs):
                    fname = f"q{cur_q:02d}_orig{'' if idx_img == 0 else f'_{idx_img+1}'}.webp"
                    web_path = export_webp(zf, media_rel, fname)
                    questions[cur_q]["figures"].append({"src": web_path, "caption": caption})
            i += 1

        # --- Parse Lower Part (Titles, Answers, Detailed Analyses, Solution Figures, Pitfalls) ---
        cur_q = None
        cur_field = "analysis"  # 'analysis' | 'pitfalls'
        analysis_buf = {qno: [] for qno in range(1, 31)}
        pitfalls_buf = {qno: [] for qno in range(1, 31)}

        i = lower_start
        while i < len(paras):
            md, imgs = paras[i]

            # Ignore section banners
            if re.match(r"^[一二三]、.+详细解析", md) or md.startswith(("2026 年", "下篇：", "全卷参考答案", "（一）判断题", "（二）填空")):
                i += 1
                continue

            m_hdr = re.match(r"^第\s*(\d{1,2})\s*题[\s　]+(.+)$", md)
            if m_hdr:
                cur_q = int(m_hdr.group(1))
                questions[cur_q]["title"] = m_hdr.group(2).strip()
                cur_field = "analysis"
                i += 1
                continue

            if cur_q is None:
                i += 1
                continue

            if md.startswith("【参考答案】"):
                ans = md.replace("【参考答案】", "", 1).strip()
                questions[cur_q]["answer"] = ans
                i += 1
                continue

            if md.startswith("【详细解析】") or md.startswith("【解】"):
                cur_field = "analysis"
                body_txt = re.sub(r"^【(详细解析|解)】", "", md).strip()
                if body_txt:
                    analysis_buf[cur_q].append(body_txt)
                i += 1
                continue

            if md.startswith("【考点与易错提示】"):
                cur_field = "pitfalls"
                pit_txt = md.replace("【考点与易错提示】", "", 1).strip()
                if pit_txt:
                    pitfalls_buf[cur_q].append(pit_txt)
                i += 1
                continue

            if imgs:
                caption = ""
                if i + 1 < len(paras) and paras[i + 1][0].startswith("解图"):
                    caption = paras[i + 1][0].strip()
                    i += 1
                for idx_img, media_rel in enumerate(imgs):
                    fname = f"q{cur_q:02d}_sol{'' if idx_img == 0 else f'_{idx_img+1}'}.webp"
                    web_path = export_webp(zf, media_rel, fname)
                    fig_obj = {"src": web_path, "caption": caption}
                    questions[cur_q]["analysisFigures"].append(fig_obj)
                    # Insert inline figure marker or keep in analysisFigures (we also cross-link 解图 1 to Q2 & Q4!)
                    if cur_q == 9 and "同步图解第 2、4、9 题" in caption:
                        questions[2]["analysisFigures"].append(fig_obj)
                        questions[4]["analysisFigures"].append(fig_obj)
                i += 1
                continue

            if md:
                if cur_field == "pitfalls":
                    pitfalls_buf[cur_q].append(md)
                else:
                    analysis_buf[cur_q].append(md)
            i += 1

        # Assemble final list and attach metadata
        final_questions = []
        for qno in range(1, 31):
            q = questions[qno]
            q["analysis"] = "\n\n".join(analysis_buf[qno]).strip()
            q["pitfalls"] = "\n\n".join(pitfalls_buf[qno]).strip()
            meta = QUESTION_META[qno]
            q["chapter"] = meta["chapter"]
            q["kps"] = meta["kps"]
            q["method"] = meta["method"]
            q["difficulty"] = meta["difficulty"]
            if "subType" in meta:
                q["subType"] = meta["subType"]
            if "rubric" in meta:
                q["rubric"] = meta["rubric"]
            final_questions.append(q)

    paper_data = {
        "year": 2026,
        "code": "814",
        "subject": "水力学",
        "school": "河海大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": False,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟（3 小时），闭卷笔试。",
            "河海大学 814 水力学近年不允许使用计算器，模考建议全程手算。",
            "除特别说明外，统一取重力加速度 g = 9.81 m/s²，水的密度 ρ = 1000 kg/m³，运动黏度 ν = 1.0×10⁻⁶ m²/s。",
            "分值按 814 标准题型结构配置：一、判断题（10×2=20 分）；二、填空与简答题（15×2=30 分）；三、计算题（5×20=100 分）。",
        ],
        "sections": [
            {"id": "judge", "title": "一、判断题", "description": "共 10 小题，每小题 2 分，共 20 分。判断下列说法正误。", "range": [1, 10], "scorePerQuestion": 2, "totalScore": 20},
            {"id": "fill", "title": "二、填空与简答题", "description": "共 15 小题，每小题 2 分，共 30 分。", "range": [11, 25], "scorePerQuestion": 2, "totalScore": 30},
            {"id": "calc", "title": "三、计算题", "description": "共 5 小题，每小题 20 分，共 100 分。需写出完整公式、推导步骤与单位。", "range": [26, 30], "scorePerQuestion": 20, "totalScore": 100},
        ],
        "questions": final_questions,
    }

    OUT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUT_DATA_DIR / "2026.json"
    out_json.write_text(json.dumps(paper_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Also write exams index for future multi-year expansion (2024, 2025, ...)
    exams_index = {
        "availableYears": [
            {
                "year": 2026,
                "title": "2026 年河海大学 814 水力学考研真题",
                "questionCount": 30,
                "totalScore": 150,
                "figureCount": 19,
                "status": "ready",
                "dataFile": "data/2026.json",
            },
            {
                "year": 2025,
                "title": "2025 年河海大学 814 水力学考研真题",
                "questionCount": 30,
                "totalScore": 150,
                "figureCount": 27,
                "status": "planned",
                "dataFile": "data/2025.json",
            },
            {
                "year": 2024,
                "title": "2024 年河海大学 814 水力学考研真题",
                "questionCount": 30,
                "totalScore": 150,
                "figureCount": 31,
                "status": "planned",
                "dataFile": "data/2024.json",
            },
        ]
    }
    (OUT_DATA_DIR / "index.json").write_text(json.dumps(exams_index, ensure_ascii=False, indent=2), encoding="utf-8")

    # Verification assertions
    assert len(final_questions) == 30, f"Expected 30 questions, got {len(final_questions)}"
    total_pts = sum(q["score"] for q in final_questions)
    assert total_pts == 150, f"Expected 150 points, got {total_pts}"
    for q in final_questions:
        assert q["stem"], f"Empty stem in Q{q['no']}"
        assert q["title"], f"Empty title in Q{q['no']}"
        assert q["answer"], f"Empty answer in Q{q['no']}"
        assert q["analysis"], f"Empty analysis in Q{q['no']}"
        for field in ("stem", "answer", "analysis", "pitfalls", "shortAnswer"):
            val = q[field]
            # Check balanced braces inside math blocks
            for m in re.finditer(r"\$\$[\s\S]*?\$\$|\$[^$\n]+\$", val):
                expr = m.group(0)
                # Ignore escaped braces \{ \}
                clean_expr = expr.replace(r"\{", "").replace(r"\}", "")
                if clean_expr.count("{") != clean_expr.count("}"):
                    print(f"WARNING: Unbalanced braces in Q{q['no']} {field}: {expr}")

    orig_figs = sum(len(q["figures"]) for q in final_questions)
    sol_figs = sum(len(q["analysisFigures"]) for q in final_questions)
    print(f"SUCCESS: Parsed {len(final_questions)} questions ({total_pts} pts), {orig_figs} exam figures, {sol_figs} solution figure refs -> {out_json}")


if __name__ == "__main__":
    main()
