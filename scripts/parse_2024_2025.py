# -*- coding: utf-8 -*-
"""
Parse 2024 & 2025 Hohai University 814 Hydraulics exam .docx files into
`web/public/data/2024.json` and `web/public/data/2025.json` + WebP figures,
and update `web/public/data/index.json` so 2024, 2025, 2026 are all live.
"""

import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "河海大学已整理真题"
OUT_DATA_DIR = ROOT / "web" / "public" / "data"

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
    "ε": r"\varepsilon ",
    "ζ": r"\zeta ",
    "θ": r"\theta ",
    "λ": r"\lambda ",
    "μ": r"\mu ",
    "ν": r"\nu ",
    "ξ": r"\xi ",
    "π": r"\pi ",
    "ρ": r"\rho ",
    "σ": r"\sigma ",
    "τ": r"\tau ",
    "φ": r"\varphi ",
    "χ": r"\chi ",
    "ψ": r"\psi ",
    "ω": r"\omega ",
    "Δ": r"\Delta ",
    "∂": r"\partial ",
    "∇": r"\nabla ",
    "−": "-",
    "±": r"\pm ",
    "∝": r"\propto ",
    "∼": r"\sim ",
    "～": r"\sim ",
    "≈": r"\approx ",
    "≠": r"\neq ",
    "≤": r"\le ",
    "≥": r"\ge ",
    "≫": r"\gg ",
    "≪": r"\ll ",
    "⋯": r"\cdots ",
    "←": r"\leftarrow ",
    "↑": r"\uparrow ",
    "→": r"\rightarrow ",
    "↓": r"\downarrow ",
    "⇒": r"\Rightarrow ",
    "⟹": r"\Longrightarrow ",
    "✓": r"\checkmark ",
    "×": r"\times ",
    "·": r"\cdot ",
    "°": r"^{\circ}",
    "∘": r"^{\circ}",
    "′": r"'",
    "\u2003": r"\quad ",
    "\u2005": r"\; ",
    "\u2009": r"\, ",
}

OPERATORS = {
    "tan", "sin", "cos", "cot", "arctan", "arcsin", "arccos",
    "ln", "log", "max", "min", "exp", "const", "lim",
}


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
    stripped = txt.strip()
    lead_space = r"\, " if txt.startswith((" ", "\u2009", "\u2005")) and stripped else ""
    trail_space = r"\, " if txt.endswith((" ", "\u2009", "\u2005")) and stripped and not txt.isspace() else ""

    if txt.isspace():
        return r"\, "

    if is_plain and stripped in OPERATORS:
        if stripped == "const":
            return f"{lead_space}\\mathrm{{const}}{trail_space}"
        return f"{lead_space}\\{stripped} "

    if is_plain and any(c.isalpha() for c in stripped) and not any(is_cjk_or_fullwidth(c) for c in stripped):
        # Convert special symbols inside plain runs (like −, ·, ×) safely
        unit_chars = []
        for ch in stripped:
            if ch == "·":
                unit_chars.append(r"\cdot ")
            elif ch == "−":
                unit_chars.append("-")
            elif ch in ("°", "∘"):
                unit_chars.append(r"^{\circ}")
            elif ch in GREEK_AND_MATH_MAP and ord(ch) > 127:
                unit_chars.append(GREEK_AND_MATH_MAP[ch])
            else:
                unit_chars.append(ch)
        unit_body = "".join(unit_chars)
        return f"{lead_space}\\mathrm{{{unit_body}}}{trail_space}"

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
                # Escape % or _ if any inside \text
                cjk_seg = cjk_seg.replace("%", r"\%").replace("_", r"\_")
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
        elif ch == "%":
            out.append(r"\%")
            i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def omml_to_latex(el: ET.Element | None) -> str:
    if el is None:
        return ""
    tag = el.tag.split("}")[-1]

    if tag in ("oMathPara", "oMath", "e", "num", "den", "sub", "sup", "deg", "lim", "box"):
        parts = [omml_to_latex(c) for c in el]
        return "".join(parts).strip()

    if tag in (
        "oMathParaPr", "rPr", "fPr", "radPr", "sSubPr", "sSupPr", "sSubSupPr",
        "dPr", "accPr", "naryPr", "ctrlPr", "barPr", "groupChrPr", "limLowPr", "boxPr"
    ):
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
        beg, end = "(", ")"
        if dpr is not None:
            b_el = dpr.find("m:begChr", NS)
            e_el = dpr.find("m:endChr", NS)
            if b_el is not None:
                beg = b_el.attrib.get(M + "val", "(")
            if e_el is not None:
                end = e_el.attrib.get(M + "val", ")")
        l_map = {"(": "(", "[": "[", "{": r"\{", "|": "|", "‖": r"\|", "": "."}
        r_map = {")": ")", "]": "]", "}": r"\}", "|": "|", "‖": r"\|", "": "."}
        l_tok = l_map.get(beg, beg)
        r_tok = r_map.get(end, end)
        es = [omml_to_latex(e_child) for e_child in el.findall("m:e", NS)]
        inner = ", ".join(es)
        return f"\\left{l_tok} {inner} \\right{r_tok}"

    if tag == "acc":
        chr_el = el.find("m:accPr/m:chr", NS)
        acc_chr = chr_el.attrib.get(M + "val", "⃗") if chr_el is not None else "⃗"
        base = omml_to_latex(el.find("m:e", NS))
        if acc_chr in ("⃗", "\u20d7", "→"):
            return f"\\vec{{{base}}}"
        if acc_chr in ("̄", "\u0304", "¯"):
            return f"\\overline{{{base}}}"
        if acc_chr in ("̇", "\u0307"):
            return f"\\dot{{{base}}}"
        return f"\\hat{{{base}}}"

    if tag == "bar":
        pos_el = el.find("m:barPr/m:pos", NS)
        pos = pos_el.attrib.get(M + "val", "top") if pos_el is not None else "top"
        base = omml_to_latex(el.find("m:e", NS))
        return f"\\underline{{{base}}}" if pos == "bot" else f"\\overline{{{base}}}"

    if tag == "groupChr":
        pos_el = el.find("m:groupChrPr/m:pos", NS)
        pos = pos_el.attrib.get(M + "val", "bot") if pos_el is not None else "bot"
        base = omml_to_latex(el.find("m:e", NS))
        return f"\\overbrace{{{base}}}" if pos == "top" else f"\\underbrace{{{base}}}"

    if tag == "limLow":
        base = omml_to_latex(el.find("m:e", NS))
        lim = omml_to_latex(el.find("m:lim", NS))
        if base.startswith(r"\underbrace") or base.startswith(r"\lim"):
            return f"{base}_{{{lim}}}"
        return f"{{{base}}}_{{{lim}}}"

    if tag == "nary":
        chr_el = el.find("m:naryPr/m:chr", NS)
        op_chr = chr_el.attrib.get(M + "val", "∫") if chr_el is not None else "∫"
        op_cmd = {"∫": r"\int", "∬": r"\iint", "∮": r"\oint", "∑": r"\sum", "∏": r"\prod"}.get(op_chr, r"\int")
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
    tex = re.sub(r"[ \t]+", " ", tex).strip()
    # Prevent double superscripts in KaTeX (e.g. 30^{^{\circ}}, R^{'}, h_c^{''})
    tex = tex.replace(r"^{^{\circ}}", r"^{\circ}")
    tex = tex.replace(r"^{\mathrm{^{\circ}}}", r"^{\circ}")
    tex = tex.replace(r"^{''' }", r"^{\prime\prime\prime}")
    tex = tex.replace(r"^{''}", r"^{\prime\prime}")
    tex = tex.replace(r"^{'}", r"^{\prime}")
    # Also handle prime inside superscripts like `{h_c}^{''}` or `R^{'}_x`
    tex = re.sub(r"\^\{\s*''\s*\}", r"^{\\prime\\prime}", tex)
    tex = re.sub(r"\^\{\s*'\s*\}", r"^{\\prime}", tex)
    tex = re.sub(r"\{([A-Za-z0-9])\}_", r"\1_", tex)
    tex = re.sub(r"\{([A-Za-z0-9])\}\^", r"\1^", tex)
    return tex


def sanitize_text(s: str) -> str:
    """Remove third-party video/creator references while keeping all technical discussions intact."""
    if not s:
        return s
    replacements = [
        ("视频讲解口径对照", "教材近似表述与严格判据对照"),
        ("视频计算对比说明（重要！）", "等势线与等势带审题辨析（重要！）"),
        ("精度对比说明", "手算精度对比说明"),
        ("细节核正（与视频结果对照）", "手算有效数字核正"),
        ("【易错提醒与视频笔误纠偏】", "【易错提醒】"),
        ("【高分踩分点与视频笔误纠偏】", "【高分采分点与易错提醒】"),
        ("【视频口径与考场回忆题辨析】", "【不同审题口径辨析】"),
        ("视频中主讲人（凤鸣）指出，", ""),
        ("因此视频暂按教材字面标作 √，但主讲人同时强调该题存在争议。", "因此若按教材字面近似可标 √，建议结合两种口径理解记忆。"),
        ("注：视频按教材近似表述标 √", "注：若按教材工程近似表述常标 √"),
        ("注：视频按“13 根等势线/12 个等势带”算得", "注：若按“13 根等势线/12 个等势带”口径则算得"),
        ("视频中主讲人将题干", "常见易错做法是将题干"),
        ("视频中主讲人误按", "部分参考解答误按"),
        ("视频中主讲人误写为", "常见笔误易写为"),
        ("视频中将", "若计算时将"),
        ("视频中仅求解了", "常规解法往往只求"),
        ("视频中计算", "若粗略计算"),
        ("视频约取", "粗略约取"),
        ("在 B 站原视频讲解中，老师依据", "另一种常见口径依据"),
        ("视频讲解", "另一种常见口径"),
        ("原视频板书中曾误把", "切勿误把"),
        ("原视频板书中曾口误/笔误写作", "切勿笔误写作"),
        ("讲解时补全", "此处补全"),
    ]
    for old, new in replacements:
        s = s.replace(old, new)
    return s.strip()


def paragraph_to_markdown(p: ET.Element, rels: dict) -> tuple[str, list[str]]:
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
    text = sanitize_text("".join(chunks).replace("\u200b", ""))
    return text, images


def table_to_markdown(tbl: ET.Element, rels: dict) -> str:
    rows = tbl.findall("w:tr", NS)
    rendered_rows = []
    for tr in rows:
        cells = []
        for tc in tr.findall("w:tc", NS):
            ps = [paragraph_to_markdown(p, rels)[0] for p in tc.findall("w:p", NS)]
            cells.append(" ".join(x for x in ps if x).strip())
        if any(cells):
            rendered_rows.append(" ｜ ".join(c for c in cells if c))
    return "\n\n".join(rendered_rows)


def export_webp(zf: zipfile.ZipFile, media_rel: str, year: int, dest_name: str) -> str:
    out_dir = OUT_DATA_DIR / "figures" / str(year)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = zf.read("word/" + media_rel)
    img = Image.open(io.BytesIO(raw))
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    out_path = out_dir / dest_name
    img.save(out_path, format="WEBP", quality=90, method=4)
    return f"data/figures/{year}/{dest_name}"


# ==============================================================================
# Curated Metadata for 2025 (Q1 - Q30)
# ==============================================================================
META_2025 = {
    1:  {"chapter": 5,  "kps": ["理想液体假设", "无旋流判据"], "method": "物理概念定义辨析", "difficulty": 3},
    2:  {"chapter": 2,  "kps": ["等压面性质", "U形管多液柱平衡"], "method": "等压面静水压强递推法", "difficulty": 2},
    3:  {"chapter": 6,  "kps": ["恒定总流能量方程", "阀门局部阻力与测压管水头"], "method": "总水头线与测压管水头线判据", "difficulty": 2},
    4:  {"chapter": 7,  "kps": ["明渠均匀流特征", "过水断面与铅垂断面区别"], "method": "概念偷换词辨析", "difficulty": 3},
    5:  {"chapter": 4,  "kps": ["动能修正系数", "层流与紊流流速分布对比"], "method": "物理概念定义辨析", "difficulty": 2},
    6:  {"chapter": 4,  "kps": ["圆管均匀流切应力分布"], "method": "圆管切应力线性分布性质", "difficulty": 1},
    7:  {"chapter": 4,  "kps": ["紊流阻力分区", "水力粗糙面定义"], "method": "物理概念定义辨析", "difficulty": 2},
    8:  {"chapter": 6,  "kps": ["总水头线与测压管水头线", "虹吸管水力计算"], "method": "总水头线与测压管水头线判据", "difficulty": 3},
    9:  {"chapter": 8,  "kps": ["明渠水面曲线定性分析", "逆坡与平坡壅水曲线"], "method": "渐变流微分方程符号判别", "difficulty": 3},
    10: {"chapter": 9,  "kps": ["实用堰流量系数", "堰顶负压效应"], "method": "堰流与闸孔出流判别及流量公式", "difficulty": 2},
    11: {"chapter": 2,  "kps": ["欧拉液体平衡微分方程"], "method": "核心基本概念记忆", "difficulty": 2, "subType": "blank"},
    12: {"chapter": 2,  "kps": ["变密度静水压强", "圆柱/抛物曲面铅垂总压力"], "method": "等效自由液面+水平投影与铅垂压力体合成法", "difficulty": 4, "subType": "mini-calc"},
    13: {"chapter": 2,  "kps": ["平面静水总压力", "压心与闸门自动开启条件"], "method": "平面总压力形心法/分块合成法", "difficulty": 3, "subType": "mini-calc"},
    14: {"chapter": 11, "kps": ["平面渗流流网", "闸底板扬压力计算"], "method": "正交流网段数减一计数法", "difficulty": 3, "subType": "mini-calc"},
    15: {"chapter": 6,  "kps": ["虹吸管水力计算", "真空高度(真空度)"], "method": "两段伯努利方程联立法", "difficulty": 2, "subType": "mini-calc"},
    16: {"chapter": 6,  "kps": ["长管串并联与三水池问题"], "method": "长管阻抗与多水池节点能量平衡", "difficulty": 3, "subType": "mini-calc"},
    17: {"chapter": 9,  "kps": ["堰流分类与基本流量公式", "平板闸孔出流判别"], "method": "堰流与闸孔出流判别及流量公式", "difficulty": 3, "subType": "mini-calc"},
    18: {"chapter": 3,  "kps": ["U形水银压差计测压", "恒定总流能量方程"], "method": "正反双向流动伯努利方程讨论法", "difficulty": 4, "subType": "mini-calc"},
    19: {"chapter": 4,  "kps": ["紊流阻力分区", "达西-韦斯巴赫公式"], "method": "紊流光滑区布拉休斯幂次比例法", "difficulty": 2, "subType": "mini-calc"},
    20: {"chapter": 7,  "kps": ["水力最佳断面", "明渠均匀流曼宁公式"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 3, "subType": "mini-calc"},
    21: {"chapter": 3,  "kps": ["恒定总流动量方程", "射流冲击圆锥阀受力"], "method": "控制体正交分解矢量法", "difficulty": 3, "subType": "mini-calc"},
    22: {"chapter": 13, "kps": ["弗劳德相似准则", "流量比尺换算"], "method": "弗劳德比尺幂次换算法", "difficulty": 1, "subType": "mini-calc"},
    23: {"chapter": 4,  "kps": ["普朗特混合长度理论", "紊流附加切应力"], "method": "核心基本概念记忆", "difficulty": 2, "subType": "short-answer"},
    24: {"chapter": 6,  "kps": ["有压管道水击(水锤)", "直接与间接水击判别"], "method": "水击相长判别与儒氏公式", "difficulty": 1, "subType": "mini-calc"},
    25: {"chapter": 5,  "kps": ["欧拉法速度场", "当地加速度与迁移加速度"], "method": "速度场偏导数判别法", "difficulty": 1, "subType": "blank"},
    26: {
        "chapter": 4,
        "kps": ["圆管层流哈根-泊肃叶定律", "圆管均匀流切应力分布", "牛顿内摩擦定律"],
        "method": "圆管切应力线性分布性质",
        "difficulty": 3,
        "rubric": [
            {"label": "由 r=0 极值条件与 r=r0 无滑移边界条件确定 u(r) = k(1 - r²/r0²)", "pts": 6},
            {"label": "由牛顿内摩擦定律求得 τ(r) = 2μkr / r0² 并正确画出线性分布图", "pts": 8},
            {"label": "正确画出微元液块剪切变形后的斜平行四边形及上下表面切应力方向（上左、下右）", "pts": 6},
        ],
    },
    27: {
        "chapter": 2,
        "kps": ["多液层静水压强", "圆柱曲面静水总压力", "力矩平衡求闭门力"],
        "method": "等效自由液面+水平投影与铅垂压力体合成法",
        "difficulty": 4,
        "rubric": [
            {"label": "由水银测压计与水层递推求得油面以下圆心 O 处相对压强", "pts": 6},
            {"label": "正确计算圆弧盖 OB 所受油的水平分力 Px 与铅垂分力 Pz（或利用合力过圆心性质）", "pts": 8},
            {"label": "对铰链 O 列力矩平衡方程求得水平闭门力 F ≈ 1.76 kN", "pts": 6},
        ],
    },
    28: {
        "chapter": 3,
        "kps": ["恒定总流能量方程", "恒定总流动量方程", "底流消能判别", "矩形明渠共轭水深"],
        "method": "能量方程求流量+控制体动量方程求反力",
        "difficulty": 4,
        "rubric": [
            {"label": "对堰前与收缩断面 c-c 列能量方程求得流速 vc0 与流量 Q", "pts": 6},
            {"label": "取控制体列水平动量方程求得水流对实用堰水平作用力 R ≈ 2.45×10⁴ kN（向下游）", "pts": 8},
            {"label": "求得收缩断面共轭水深 hc'' = 4.61 m > 3 m（远驱式水跃），判定需设消能设施", "pts": 6},
        ],
    },
    29: {
        "chapter": 5,
        "kps": ["平面流函数与流线", "无旋流判据", "单宽流量计算", "欧拉运动微分方程"],
        "method": "不可压与无旋偏导检验+偏积分求原函数法",
        "difficulty": 3,
        "rubric": [
            {"label": "由 ψ = (x²+y²)/2 判断流线为同心圆簇，由速度分量判出顺时针流向并作图", "pts": 5},
            {"label": "计算旋转角速度 ωz ≠ 0（∂v/∂x - ∂u/∂y = -2 ≠ 0），判定不存在速度势函数", "pts": 5},
            {"label": "求得 A、B 两点间单宽流量 q = |ψB - ψA| = 6 m²/s", "pts": 5},
            {"label": "指出有旋流不同流线间伯努利常数不同，判定 A、B 两点单位机械能不相等", "pts": 5},
        ],
    },
    30: {
        "chapter": 8,
        "kps": ["临界水深与临界底坡", "明渠水面曲线定性分析", "明渠均匀流曼宁公式", "断面单位能量(比能)"],
        "method": "渐变流微分方程符号判别",
        "difficulty": 4,
        "rubric": [
            {"label": "判定变坡点（平坡接陡坡）为控制断面 hc = 0.47 m，求得流量 Q ≈ 4.04 m³/s", "pts": 7},
            {"label": "由下游很远处正常水深 h02 = 0.40 m 代入曼宁公式反算糙率 n ≈ 0.015", "pts": 6},
            {"label": "定性绘出 H2 降水曲线接 S2 降水曲线，并指明比能 Es 在 H2 段沿程减小、在 S2 段沿程增大", "pts": 7},
        ],
    },
}

# ==============================================================================
# Curated Metadata for 2024 (Q1 - Q30)
# ==============================================================================
META_2024 = {
    1:  {"chapter": 1,  "kps": ["连续介质假设"], "method": "物理概念定义辨析", "difficulty": 1},
    2:  {"chapter": 2,  "kps": ["平面静水总压力", "形心与压心区别"], "method": "概念偷换词辨析", "difficulty": 2},
    3:  {"chapter": 3,  "kps": ["毕托管测速原理", "时均流速与瞬时流速"], "method": "物理概念定义辨析", "difficulty": 2},
    4:  {"chapter": 8,  "kps": ["明渠渐变流能量变化", "总水头与水位高程区别"], "method": "伯努利方程多因素反例法", "difficulty": 3},
    5:  {"chapter": 3,  "kps": ["层流与紊流分类", "渐变流与急变流分类"], "method": "物理概念定义辨析", "difficulty": 2},
    6:  {"chapter": 4,  "kps": ["雷诺数与流态判别", "尼古拉兹试验"], "method": "概念偷换词辨析", "difficulty": 2},
    7:  {"chapter": 4,  "kps": ["紊流阻力分区"], "method": "紊流光滑区布拉休斯幂次比例法", "difficulty": 2},
    8:  {"chapter": 4,  "kps": ["雷诺数与流态判别", "恒定总流连续性方程"], "method": "物理概念定义辨析", "difficulty": 2},
    9:  {"chapter": 6,  "kps": ["总水头线与测压管水头线"], "method": "总水头线与测压管水头线判据", "difficulty": 3},
    10: {"chapter": 8,  "kps": ["断面单位能量(比能)", "平坡明渠水面线"], "method": "比能沿程导数判别法", "difficulty": 2},
    11: {"chapter": 1,  "kps": ["牛顿内摩擦定律", "环形/圆盘间隙黏性阻力矩"], "method": "分层液体切应力连续与速度叠加法", "difficulty": 4, "subType": "mini-calc"},
    12: {"chapter": 2,  "kps": ["平面静水总压力", "压心与闸门自动开启条件"], "method": "平面总压力形心法/分块合成法", "difficulty": 4, "subType": "mini-calc"},
    13: {"chapter": 2,  "kps": ["静水压强基本方程", "多液层静水压强"], "method": "等压面静水压强递推法", "difficulty": 2, "subType": "mini-calc"},
    14: {"chapter": 3,  "kps": ["恒定总流能量方程", "恒定总流动量方程", "U形水银压差计测压"], "method": "能量方程求流量+控制体动量方程求反力", "difficulty": 3, "subType": "mini-calc"},
    15: {"chapter": 4,  "kps": ["雷诺数与流态判别", "圆管层流哈根-泊肃叶定律", "圆管均匀流切应力分布"], "method": "圆管切应力线性分布性质", "difficulty": 3, "subType": "mini-calc"},
    16: {"chapter": 5,  "kps": ["平面流函数与流线"], "method": "不可压与无旋偏导检验+偏积分求原函数法", "difficulty": 2, "subType": "blank"},
    17: {"chapter": 6,  "kps": ["简单短管自由出流", "总流机械能功率"], "method": "短管自由出流流量公式判别", "difficulty": 3, "subType": "blank"},
    18: {"chapter": 6,  "kps": ["长管串并联与三水池问题"], "method": "长管阻抗与多水池节点能量平衡", "difficulty": 3, "subType": "mini-calc"},
    19: {"chapter": 6,  "kps": ["虹吸管水力计算", "短管能量方程"], "method": "两段伯努利方程联立法", "difficulty": 2, "subType": "mini-calc"},
    20: {"chapter": 7,  "kps": ["梯形断面水力要素", "明渠均匀流曼宁公式"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 3, "subType": "mini-calc"},
    21: {"chapter": 8,  "kps": ["缓坡水面曲线(M1/M2/M3)", "断面单位能量(比能)"], "method": "比能沿程导数判别法", "difficulty": 2, "subType": "blank"},
    22: {"chapter": 8,  "kps": ["明渠水面曲线定性分析", "缓坡水面曲线(M1/M2/M3)"], "method": "渐变流微分方程符号判别", "difficulty": 3, "subType": "blank"},
    23: {"chapter": 9,  "kps": ["平板闸孔出流判别", "堰流分类与基本流量公式"], "method": "堰流与闸孔出流判别及流量公式", "difficulty": 3, "subType": "mini-calc"},
    24: {"chapter": 13, "kps": ["明渠水跃与跃后水深", "弗劳德相似准则", "流量比尺换算"], "method": "弗劳德比尺幂次换算法", "difficulty": 4, "subType": "mini-calc"},
    25: {"chapter": 11, "kps": ["平面渗流流网", "达西定律与单宽渗流量"], "method": "正交流网段数减一计数法", "difficulty": 2, "subType": "mini-calc"},
    26: {
        "chapter": 1,
        "kps": ["牛顿内摩擦定律", "环形/圆盘间隙黏性阻力矩"],
        "method": "分层液体切应力连续与速度叠加法",
        "difficulty": 2,
        "rubric": [
            {"label": "计算环形润滑油膜厚度 δ=(D-d)/2=0.5 mm 及接触侧面积 A=πDL", "pts": 4},
            {"label": "对圆柱壳列沿管轴方向平衡方程 T = F - G·sin60° 求得黏性摩阻力", "pts": 3},
            {"label": "由牛顿内摩擦定律 T = μA(u/δ) 解得动力黏度 μ ≈ 0.0585 Pa·s", "pts": 3},
        ],
    },
    27: {
        "chapter": 2,
        "kps": ["圆柱曲面静水总压力", "压力体图与虚压力体", "双侧液体合力叠加"],
        "method": "等效自由液面+水平投影与铅垂压力体合成法",
        "difficulty": 4,
        "rubric": [
            {"label": "分别计算曲面左、右两侧水平静水总压力 Px1、Px2 并求净水平分力 Px", "pts": 9},
            {"label": "正确分析左、右两侧铅垂压力体（勿漏右侧下半圆弧实压力体）求得净铅垂分力 Pz", "pts": 10},
            {"label": "合成总压力 P ≈ 88.53 kN、倾角 θ ≈ 30.5°（右上方，作用线过圆心 O）", "pts": 6},
        ],
    },
    28: {
        "chapter": 3,
        "kps": ["恒定总流能量方程", "恒定总流动量方程", "弯管/底坎水流作用力"],
        "method": "能量方程求流量+控制体动量方程求反力",
        "difficulty": 4,
        "rubric": [
            {"label": "由连续性方程求得进出口流速 v1=1.485 m/s、v2=3.342 m/s", "pts": 5},
            {"label": "列进出口能量方程求得出口断面压强 p2 及两端动水总压力 P1、P2", "pts": 8},
            {"label": "列 x、y 方向控制体动量方程（计入水重 G，注意 P2 方向）求得管壁反力 Rx、Ry", "pts": 11},
            {"label": "由牛顿第三定律给出水流对弯管合力 R' ≈ 55.98 N 及方向（向右偏下 12.75°）", "pts": 6},
        ],
    },
    29: {
        "chapter": 5,
        "kps": ["平面不可压缩流连续性方程", "无旋流判据", "流函数与速度势函数求解", "欧拉运动微分方程"],
        "method": "不可压与无旋偏导检验+偏积分求原函数法",
        "difficulty": 3,
        "rubric": [
            {"label": "检验 ∂ux/∂x + ∂uy/∂y = 0，偏积分求得流函数 ψ = 6xy + y³/3 - y²/2 - x²y + C", "pts": 6},
            {"label": "计算旋转角速度 ωz = 1/2 ≠ 0，判定流动有旋、不存在速度势函数", "pts": 4},
            {"label": "沿流线 y=0（或积分欧拉运动微分方程）求得 B(1,0) 处压强 pB = -12.5 kPa", "pts": 5},
        ],
    },
    30: {
        "chapter": 8,
        "kps": ["明渠均匀流曼宁公式", "弗劳德数判急缓流", "临界水深与跌坎水深", "长管水力计算"],
        "method": "水力要素计算+曼宁公式+水力深度Fr判据",
        "difficulty": 4,
        "rubric": [
            {"label": "由正常水深 h0=2 m 代入曼宁公式求得渠道恒定流量 Q ≈ 4.73 m³/s", "pts": 5},
            {"label": "求得临界水深 hc = 0.523 m < h0（或 Fr < 1），判定渠道发生缓流", "pts": 5},
            {"label": "缓流跌坎末端近似取临界水深（或 0.89hc），求得坎末端水位 ≈ 113.47 m", "pts": 5},
            {"label": "对甲乙两水槽长管列能量方程 H = (10.29 n² l / d^(16/3)) Q² 解得管径 d ≈ 1.40 m", "pts": 5},
        ],
    },
}


def parse_2025() -> dict:
    docx_path = SRC_DIR / "河海大学2025年814水力学考研真题及全解析_原图去水印版.docx"
    with zipfile.ZipFile(docx_path) as zf:
        rels = {r.attrib["Id"]: r.attrib["Target"] for r in ET.fromstring(zf.read("word/_rels/document.xml.rels"))}
        body = ET.fromstring(zf.read("word/document.xml")).find("w:body", NS)

        # Map 图 1..图 12 -> target question number
        fig_to_q = {
            1: 2, 2: 3, 3: 8, 4: 12, 5: 13, 6: 15,
            7: 16, 8: 18, 9: 21, 10: 27, 11: 28, 12: 30,
        }

        questions = {}
        deferred_figs = []
        part1_started = False
        part2_started = False
        part3_started = False

        # Quick-answer lookup
        short_answers = {}

        cur_q = None
        analysis_buf = {k: [] for k in range(1, 31)}
        pitfalls_buf = {k: [] for k in range(1, 31)}

        children = list(body)
        idx = 0
        while idx < len(children):
            el = children[idx]
            ctag = el.tag.split("}")[-1]
            raw_txt = "".join(el.itertext()).strip()

            # Detect major parts
            if ctag == "tbl" and raw_txt.startswith("第二部分"):
                part2_started = True
                idx += 1
                continue
            if ctag == "tbl" and raw_txt.startswith("第三部分"):
                part3_started = True
                cur_q = None
                idx += 1
                continue
            if not part1_started and ctag == "p" and raw_txt.startswith("一、是非题"):
                part1_started = True
                idx += 1
                continue

            # --- Part 1: Exam Stems & Original Figures ---
            if part1_started and not part2_started:
                if ctag == "tbl":
                    # Side-by-side figure table
                    blips = [rels.get(b.attrib.get(R + "embed")) for b in el.findall(".//a:blip", NS)]
                    caps = [m.group(0) for m in re.finditer(r"图\s*(\d+)", raw_txt)]
                    for media_rel, cap_str in zip(blips, caps):
                        fnum = int(re.search(r"\d+", cap_str).group(0))
                        target_q = fig_to_q.get(fnum)
                        if target_q and media_rel:
                            web_src = export_webp(zf, media_rel, 2025, f"q{target_q:02d}_orig.webp")
                            deferred_figs.append((target_q, {"src": web_src, "caption": f"图 {fnum}"}))
                    idx += 1
                    continue

                if ctag == "p":
                    md, imgs = paragraph_to_markdown(el, rels)
                    if md.startswith(("二、填空题", "三、计算题")):
                        cur_q = None
                        idx += 1
                        continue

                    m_q = re.match(r"^(\d{1,2})\.\s*(?:（\d+\s*分）)?\s*(.+)$", md, flags=re.DOTALL)
                    if m_q and 1 <= int(m_q.group(1)) <= 30:
                        qno = int(m_q.group(1))
                        stem_txt = m_q.group(2).strip()
                        if qno <= 10:
                            stem_txt = re.sub(r"[（(]\s*[）)]\s*$", "", stem_txt).strip()
                        qtype = "judge" if qno <= 10 else ("fill" if qno <= 25 else "calc")
                        score = 2 if qno <= 25 else 20
                        questions[qno] = {
                            "id": f"2025-{qno:02d}",
                            "year": 2025,
                            "no": qno,
                            "type": qtype,
                            "score": score,
                            "title": "",
                            "stem": stem_txt,
                            "note": "",
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
                        cap = ""
                        if idx + 1 < len(children) and "".join(children[idx + 1].itertext()).strip().startswith("图 "):
                            cap = "".join(children[idx + 1].itertext()).strip()
                            idx += 1
                        for media_rel in imgs:
                            web_src = export_webp(zf, media_rel, 2025, f"q{cur_q:02d}_orig.webp")
                            questions[cur_q]["figures"].append({"src": web_src, "caption": cap})
                        idx += 1
                        continue

                    if md and cur_q is not None and not md.startswith("图 "):
                        questions[cur_q]["stem"] += "\n\n" + md
                idx += 1
                continue

            # --- Part 2: Quick Answer Tables ---
            if part2_started and not part3_started:
                if ctag == "tbl":
                    rows = el.findall("w:tr", NS)
                    if len(rows) == 2 and "1" in "".join(rows[0].itertext()) and "10" in "".join(rows[0].itertext()):
                        nums = ["".join(tc.itertext()).strip() for tc in rows[0].findall("w:tc", NS)]
                        vals = ["".join(tc.itertext()).strip() for tc in rows[1].findall("w:tc", NS)]
                        for k_str, v_str in zip(nums, vals):
                            if k_str.isdigit():
                                qn = int(k_str)
                                short_answers[qn] = "√" if "√" in v_str else "×"
                    elif len(rows) > 2:
                        for tr in rows[1:]:
                            cells = [
                                " ".join(paragraph_to_markdown(p, rels)[0] for p in tc.findall("w:p", NS)).strip()
                                for tc in tr.findall("w:tc", NS)
                            ]
                            if len(cells) >= 4:
                                if cells[0].isdigit():
                                    short_answers[int(cells[0])] = cells[1]
                                if cells[2].isdigit():
                                    short_answers[int(cells[2])] = cells[3]
                            elif len(cells) == 2 and cells[0].isdigit():
                                short_answers[int(cells[0])] = cells[1]
                idx += 1
                continue

            # --- Part 3: Detailed Solutions ---
            if part3_started:
                if ctag == "tbl" and cur_q is not None:
                    pitfalls_buf[cur_q].append(table_to_markdown(el, rels))
                    idx += 1
                    continue

                if ctag == "p":
                    md, imgs = paragraph_to_markdown(el, rels)
                    if md.startswith(("一、", "二、", "三、")):
                        idx += 1
                        continue

                    m_sol = re.match(r"^第\s*(\d{1,2})\s*题（[^）]+）[\s　]*【答案】(.+)$", md)
                    if m_sol:
                        cur_q = int(m_sol.group(1))
                        ans_txt = m_sol.group(2).strip()
                        questions[cur_q]["answer"] = ans_txt
                        if cur_q <= 10:
                            # First symbol before any parenthetical note determines judgeAnswer
                            head = ans_txt.split("（")[0]
                            questions[cur_q]["judgeAnswer"] = ("√" in head)
                        idx += 1
                        continue

                    if cur_q is None:
                        idx += 1
                        continue

                    if md.startswith("【考点】"):
                        questions[cur_q]["title"] = md.replace("【考点】", "", 1).strip()
                        idx += 1
                        continue

                    if md.startswith("【详解】"):
                        body_md = md.replace("【详解】", "", 1).strip()
                        if body_md:
                            analysis_buf[cur_q].append(body_md)
                        idx += 1
                        continue

                    if md.startswith("【注】"):
                        pitfalls_buf[cur_q].append(md.replace("【注】", "", 1).strip())
                        idx += 1
                        continue

                    if imgs:
                        for i_img, media_rel in enumerate(imgs):
                            suf = "" if i_img == 0 else f"_{i_img+1}"
                            web_src = export_webp(zf, media_rel, 2025, f"q{cur_q:02d}_sol{suf}.webp")
                            questions[cur_q]["analysisFigures"].append(
                                {"src": web_src, "caption": f"第 {cur_q} 题解析附图"}
                            )
                        idx += 1
                        continue

                    if md:
                        analysis_buf[cur_q].append(md)
                idx += 1
                continue

            idx += 1

    for target_q, fig_obj in deferred_figs:
        questions[target_q]["figures"].append(fig_obj)

    final_q = []
    for qno in range(1, 31):
        q = questions[qno]
        q["shortAnswer"] = short_answers.get(qno, q["answer"])
        q["analysis"] = "\n\n".join(analysis_buf[qno]).strip()
        q["pitfalls"] = "\n\n".join(pitfalls_buf[qno]).strip()
        meta = META_2025[qno]
        q["chapter"] = meta["chapter"]
        q["kps"] = meta["kps"]
        q["method"] = meta["method"]
        q["difficulty"] = meta["difficulty"]
        if "subType" in meta:
            q["subType"] = meta["subType"]
        if "rubric" in meta:
            q["rubric"] = meta["rubric"]
        final_q.append(q)

    return {
        "year": 2025,
        "code": "814",
        "subject": "水力学",
        "school": "河海大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": False,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试，不允许使用计算器。",
            "卷首提供常用近似数值：√2 = 1.414，√3 = 1.732，√5 = 2.236，√(2×9.81) = 4.429，g = 9.81 m/s²；近似公式 (1+x)^(1/n) ≈ 1 + x/n。",
            "题型与分值：一、是非题（10×2=20 分）；二、填空题（15×2=30 分）；三、计算题（5×20=100 分）。",
        ],
        "sections": [
            {"id": "judge", "title": "一、是非题", "description": "共 10 小题，每小题 2 分，共 20 分。", "range": [1, 10], "scorePerQuestion": 2, "totalScore": 20},
            {"id": "fill", "title": "二、填空题", "description": "共 15 小题，每小题 2 分，共 30 分。", "range": [11, 25], "scorePerQuestion": 2, "totalScore": 30},
            {"id": "calc", "title": "三、计算题", "description": "共 5 小题，每小题 20 分，共 100 分。", "range": [26, 30], "scorePerQuestion": 20, "totalScore": 100},
        ],
        "questions": final_q,
    }


def parse_2024() -> dict:
    docx_path = SRC_DIR / "河海大学2024年814水力学考研真题及详细解析.docx"
    calc_scores = {26: 10, 27: 25, 28: 30, 29: 15, 30: 20}

    with zipfile.ZipFile(docx_path) as zf:
        rels = {r.attrib["Id"]: r.attrib["Target"] for r in ET.fromstring(zf.read("word/_rels/document.xml.rels"))}
        body = ET.fromstring(zf.read("word/document.xml")).find("w:body", NS)

        questions = {}
        part1_sec_offset = None
        part2_started = False
        part2_sec_offset = None
        cur_q = None

        analysis_buf = {k: [] for k in range(1, 31)}
        pitfalls_buf = {k: [] for k in range(1, 31)}

        children = list(body)
        idx = 0
        while idx < len(children):
            el = children[idx]
            ctag = el.tag.split("}")[-1]
            raw_txt = "".join(el.itertext()).strip()

            if ctag == "tbl" and raw_txt.startswith("第二部分"):
                part2_started = True
                cur_q = None
                idx += 1
                continue

            # --- Part 1: Exam Paper ---
            if not part2_started:
                if ctag == "p":
                    md, imgs = paragraph_to_markdown(el, rels)
                    if md.startswith("一、是非题"):
                        part1_sec_offset = 0
                        cur_q = None
                        idx += 1
                        continue
                    if md.startswith("二、填空题"):
                        part1_sec_offset = 10
                        cur_q = None
                        idx += 1
                        continue
                    if md.startswith("三、计算题"):
                        part1_sec_offset = 25
                        cur_q = None
                        idx += 1
                        continue

                    if part1_sec_offset is None:
                        idx += 1
                        continue

                    m_q = re.match(r"^(\d{1,2})\.\s*(.+)$", md, flags=re.DOTALL)
                    if m_q:
                        local_no = int(m_q.group(1))
                        qno = part1_sec_offset + local_no
                        stem_txt = m_q.group(2).strip()
                        if qno <= 10:
                            stem_txt = re.sub(r"[（(]\s*[）)]\s*$", "", stem_txt).strip()
                        qtype = "judge" if qno <= 10 else ("fill" if qno <= 25 else "calc")
                        score = 2 if qno <= 25 else calc_scores[qno]
                        questions[qno] = {
                            "id": f"2024-{qno:02d}",
                            "year": 2024,
                            "no": qno,
                            "type": qtype,
                            "score": score,
                            "title": "",
                            "stem": stem_txt,
                            "note": "",
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
                        m_fig = re.search(r"图\s*(\d+)", questions[cur_q]["stem"])
                        cap = f"图 {m_fig.group(1)}" if m_fig else f"第 {cur_q} 题配图"
                        for i_img, media_rel in enumerate(imgs):
                            suf = "" if i_img == 0 else f"_{i_img+1}"
                            web_src = export_webp(zf, media_rel, 2024, f"q{cur_q:02d}_orig{suf}.webp")
                            questions[cur_q]["figures"].append({"src": web_src, "caption": cap})
                        idx += 1
                        continue

                    if md and cur_q is not None:
                        questions[cur_q]["stem"] += "\n\n" + md
                idx += 1
                continue

            # --- Part 2: Detailed Solutions ---
            if part2_started:
                if ctag == "tbl":
                    if cur_q is not None:
                        tbl_md = table_to_markdown(el, rels)
                        if "易错" in raw_txt or "辨析" in raw_txt or "踩分点" in raw_txt or "采分点" in raw_txt:
                            pitfalls_buf[cur_q].append(tbl_md)
                        else:
                            analysis_buf[cur_q].append(tbl_md)
                    idx += 1
                    continue

                if ctag == "p":
                    md, imgs = paragraph_to_markdown(el, rels)
                    if md.startswith("一、是非题详细解析"):
                        part2_sec_offset = 0
                        cur_q = None
                        idx += 1
                        continue
                    if md.startswith("二、填空题详细解析"):
                        part2_sec_offset = 10
                        cur_q = None
                        idx += 1
                        continue
                    if md.startswith("三、计算题详细解析"):
                        part2_sec_offset = 25
                        cur_q = None
                        idx += 1
                        continue

                    if part2_sec_offset is None:
                        idx += 1
                        continue

                    # Match Judge/Fill solution header: `1. 连续介质假设  【答案】√（正确）`
                    m_jf = re.match(r"^(\d{1,2})\.\s*(.+?)\s*【答案】(.+)$", md)
                    if m_jf and part2_sec_offset in (0, 10):
                        cur_q = part2_sec_offset + int(m_jf.group(1))
                        questions[cur_q]["title"] = m_jf.group(2).strip()
                        ans_txt = m_jf.group(3).strip()
                        questions[cur_q]["answer"] = ans_txt
                        questions[cur_q]["shortAnswer"] = ans_txt
                        if cur_q <= 10:
                            questions[cur_q]["judgeAnswer"] = ("√" in ans_txt.split("（")[0])
                            questions[cur_q]["shortAnswer"] = "√" if questions[cur_q]["judgeAnswer"] else "×"
                        idx += 1
                        continue

                    # Match Calc solution header: `计算题 1（10 分）：圆柱壳沿倾斜管道外壁匀速上滑  【答案】...`
                    m_calc = re.match(r"^计算题\s*(\d)\s*（(\d+)\s*分）[：:]\s*(.+?)\s*【答案】(.+)$", md)
                    if m_calc and part2_sec_offset == 25:
                        cur_q = 25 + int(m_calc.group(1))
                        questions[cur_q]["score"] = int(m_calc.group(2))
                        questions[cur_q]["title"] = m_calc.group(3).strip()
                        ans_txt = m_calc.group(4).strip()
                        questions[cur_q]["answer"] = ans_txt
                        questions[cur_q]["shortAnswer"] = ans_txt
                        idx += 1
                        continue

                    if cur_q is None:
                        idx += 1
                        continue

                    if imgs:
                        cap = f"第 {cur_q} 题解析附图"
                        if idx + 1 < len(children):
                            nxt_txt = "".join(children[idx + 1].itertext()).strip()
                            if nxt_txt.startswith("解析附图"):
                                cap = sanitize_text(nxt_txt)
                                idx += 1
                        for i_img, media_rel in enumerate(imgs):
                            suf = "" if i_img == 0 else f"_{i_img+1}"
                            web_src = export_webp(zf, media_rel, 2024, f"q{cur_q:02d}_sol{suf}.webp")
                            questions[cur_q]["analysisFigures"].append({"src": web_src, "caption": cap})
                        idx += 1
                        continue

                    if md.startswith(("【解析】", "【解题思路】")):
                        body_md = re.sub(r"^【(解析|解题思路)】", "", md).strip()
                        if body_md:
                            analysis_buf[cur_q].append(body_md)
                        idx += 1
                        continue

                    if md.startswith("【说明】"):
                        pitfalls_buf[cur_q].append(md.replace("【说明】", "", 1).strip())
                        idx += 1
                        continue

                    if md and not md.startswith("解析附图"):
                        analysis_buf[cur_q].append(md)
                idx += 1

    final_q = []
    for qno in range(1, 31):
        q = questions[qno]
        q["analysis"] = "\n\n".join(analysis_buf[qno]).strip()
        q["pitfalls"] = "\n\n".join(pitfalls_buf[qno]).strip()
        meta = META_2024[qno]
        q["chapter"] = meta["chapter"]
        q["kps"] = meta["kps"]
        q["method"] = meta["method"]
        q["difficulty"] = meta["difficulty"]
        if "subType" in meta:
            q["subType"] = meta["subType"]
        if "rubric" in meta:
            q["rubric"] = meta["rubric"]
        final_q.append(q)

    return {
        "year": 2024,
        "code": "814",
        "subject": "水力学",
        "school": "河海大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": False,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "统一取重力加速度 g = 9.81 m/s²，水密度 ρ = 1000 kg/m³。",
            "题型与分值：一、是非题（10×2=20 分）；二、填空题（15×2=30 分）；三、计算题（共 5 题，分别为 10、25、30、15、20 分，共 100 分）。",
        ],
        "sections": [
            {"id": "judge", "title": "一、是非题", "description": "共 10 小题，每小题 2 分，共 20 分。", "range": [1, 10], "scorePerQuestion": 2, "totalScore": 20},
            {"id": "fill", "title": "二、填空题", "description": "共 15 小题，每小题 2 分，共 30 分。", "range": [11, 25], "scorePerQuestion": 2, "totalScore": 30},
            {"id": "calc", "title": "三、计算题", "description": "共 5 小题（10+25+30+15+20 分），共 100 分。", "range": [26, 30], "scorePerQuestion": 20, "totalScore": 100},
        ],
        "questions": final_q,
    }


def verify_paper(paper: dict):
    yr = paper["year"]
    qs = paper["questions"]
    assert len(qs) == 30, f"{yr}: expected 30 questions, got {len(qs)}"
    pts = sum(q["score"] for q in qs)
    assert pts == 150, f"{yr}: expected 150 pts, got {pts}"
    for q in qs:
        assert q["stem"], f"{yr} Q{q['no']} empty stem"
        assert q["title"], f"{yr} Q{q['no']} empty title"
        assert q["answer"], f"{yr} Q{q['no']} empty answer"
        assert q["analysis"], f"{yr} Q{q['no']} empty analysis"
        if q["type"] == "judge":
            assert isinstance(q["judgeAnswer"], bool), f"{yr} Q{q['no']} missing boolean judgeAnswer"


def main():
    p2025 = parse_2025()
    p2024 = parse_2024()
    verify_paper(p2025)
    verify_paper(p2024)

    OUT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DATA_DIR / "2025.json").write_text(json.dumps(p2025, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DATA_DIR / "2024.json").write_text(json.dumps(p2024, ensure_ascii=False, indent=2), encoding="utf-8")

    # Update index.json so 2026, 2025, and 2024 are all ready!
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
                "status": "ready",
                "dataFile": "data/2025.json",
            },
            {
                "year": 2024,
                "title": "2024 年河海大学 814 水力学考研真题",
                "questionCount": 30,
                "totalScore": 150,
                "figureCount": 31,
                "status": "ready",
                "dataFile": "data/2024.json",
            },
        ]
    }
    (OUT_DATA_DIR / "index.json").write_text(json.dumps(exams_index, ensure_ascii=False, indent=2), encoding="utf-8")

    f25 = sum(len(q["figures"]) + len(q["analysisFigures"]) for q in p2025["questions"])
    f24 = sum(len(q["figures"]) + len(q["analysisFigures"]) for q in p2024["questions"])
    print(f"SUCCESS: 2025 ({len(p2025['questions'])} Qs, {f25} figs) & 2024 ({len(p2024['questions'])} Qs, {f24} figs) generated and activated in index.json!")


if __name__ == "__main__":
    main()
