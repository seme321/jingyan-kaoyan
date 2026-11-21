# -*- coding: utf-8 -*-
"""
Parse `河海大学已整理真题/2022年河海大学814《水力学》考研真题及详细解析.docx` into standardized exam pack
`河海大学已整理数据/2022/2022.json` + `河海大学已整理数据/2022/figures/`, including independent
verification & sign-correction of Q27 (gate self-weight moment direction).
"""

import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parse_2024_2025 as base_parser

# Extend Greek/math symbol map for 2022 docx
base_parser.GREEK_AND_MATH_MAP["κ"] = r"\kappa "
base_parser.GREEK_AND_MATH_MAP["∑"] = r"\sum "

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent.parent
DOCX_PATH = ROOT / "河海大学已整理真题" / "2022年河海大学814《水力学》考研真题及详细解析.docx"
OUT_DIR = ROOT / "河海大学已整理数据" / "2022"
FIG_DIR = OUT_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


META_2022 = {
    1:  {"title": "均匀流定义与断面流速分布辨析", "chapter": 3, "kps": ["恒定流与均匀流判别", "断面流速分布"], "method": "概念偷换词辨析", "difficulty": 1},
    2:  {"title": "水跃基本方程的力学推导依据", "chapter": 8, "kps": ["明渠水跃与跃后水深", "恒定总流动量方程"], "method": "物理概念定义辨析", "difficulty": 1},
    3:  {"title": "静水压强各向同性与微元压力分量辨析", "chapter": 2, "kps": ["静水压强基本方程"], "method": "概念偷换词辨析", "difficulty": 2},
    4:  {"title": "双层不混溶静止液体单位势能比较", "chapter": 2, "kps": ["静水压强基本方程", "水头与能量量纲"], "method": "等压面静水压强递推法", "difficulty": 3},
    5:  {"title": "有压管流与明渠紊流流速分布规律对比", "chapter": 4, "kps": ["断面流速分布"], "method": "物理概念定义辨析", "difficulty": 2},
    6:  {"title": "明渠非恒定均匀流存在性判别", "chapter": 8, "kps": ["明渠非恒定流涌波", "明渠均匀流曼宁公式"], "method": "物理概念定义辨析", "difficulty": 2},
    7:  {"title": "明渠设计糙率取值偏大对过水能力的影响", "chapter": 7, "kps": ["明渠均匀流曼宁公式"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 2},
    8:  {"title": "均匀缓流发生的底坡条件", "chapter": 8, "kps": ["临界水深与临界底坡", "弗劳德数判急缓流"], "method": "物理概念定义辨析", "difficulty": 2},
    9:  {"title": "临界水深与临界底坡的影响因素", "chapter": 8, "kps": ["临界水深与临界底坡"], "method": "物理概念定义辨析", "difficulty": 2},
    10: {"title": "短管淹没出流转自由出流的流量变化", "chapter": 6, "kps": ["简单短管自由出流"], "method": "短管自由出流流量公式判别", "difficulty": 2},
    11: {"title": "达西—韦斯巴赫公式标准形式", "chapter": 4, "kps": ["达西-韦斯巴赫公式", "沿程水头损失规律"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "blank"},
    12: {"title": "圆管突然扩大局部水头损失计算", "chapter": 4, "kps": ["恒定总流连续性方程", "达西-韦斯巴赫公式"], "method": "核心基本概念记忆", "difficulty": 2, "subType": "mini-calc"},
    13: {"title": "射流冲击平板与曲面板流量比计算", "chapter": 3, "kps": ["恒定总流动量方程"], "method": "控制体正交分解矢量法", "difficulty": 3, "subType": "mini-calc"},
    14: {"title": "斜墙上斜靠圆柱体静水总压力计算", "chapter": 2, "kps": ["圆柱曲面静水总压力", "压力体图与虚压力体"], "method": "等效自由液面+水平投影与铅垂压力体合成法", "difficulty": 4, "subType": "mini-calc"},
    15: {"title": "水银压差计测压与圆管壁面切应力计算", "chapter": 4, "kps": ["U形水银压差计测压", "圆管均匀流切应力分布"], "method": "圆管切应力线性分布性质", "difficulty": 3, "subType": "mini-calc"},
    16: {"title": "紊流粗糙区沿程水头损失与流量的比例关系", "chapter": 4, "kps": ["紊流阻力分区", "达西-韦斯巴赫公式"], "method": "紊流光滑区布拉休斯幂次比例法", "difficulty": 1, "subType": "mini-calc"},
    17: {"title": "矩形自动翻板闸门临界开启转轴位置计算", "chapter": 2, "kps": ["平面静水总压力"], "method": "平面总压力形心法/分块合成法", "difficulty": 3, "subType": "mini-calc"},
    18: {"title": "水击波四阶段传播过程性质判别", "chapter": 6, "kps": ["有压管道水击(水锤)"], "method": "水击相长判别与儒氏公式", "difficulty": 2, "subType": "blank"},
    19: {"title": "斜面薄油膜木板匀速下滑重力计算", "chapter": 1, "kps": ["牛顿内摩擦定律"], "method": "分层液体切应力连续与速度叠加法", "difficulty": 2, "subType": "mini-calc"},
    20: {"title": "糙率大小对明渠临界底坡的影响", "chapter": 8, "kps": ["临界水深与临界底坡"], "method": "物理概念定义辨析", "difficulty": 2, "subType": "blank"},
    21: {"title": "利用测压管水头线判别虹吸管负压区", "chapter": 6, "kps": ["虹吸管水力计算", "总水头线与测压管水头线"], "method": "总水头线与测压管水头线判据", "difficulty": 2, "subType": "short-answer"},
    22: {"title": "按堰顶相对厚度判别堰流类型", "chapter": 9, "kps": ["堰流分类与基本流量公式"], "method": "堰流与闸孔出流判别及流量公式", "difficulty": 1, "subType": "mini-calc"},
    23: {"title": "底流消能水力计算的核心任务", "chapter": 10, "kps": ["底流消能判别", "水跃衔接形式"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "short-answer"},
    24: {"title": "闸基正交渗流流网点压强水头计算", "chapter": 11, "kps": ["平面渗流流网"], "method": "正交流网段数减一计数法", "difficulty": 3, "subType": "mini-calc"},
    25: {"title": "溢流坝重力相似模型原型单宽流量换算", "chapter": 13, "kps": ["弗劳德相似准则", "流量比尺换算"], "method": "弗劳德比尺幂次换算法", "difficulty": 2, "subType": "mini-calc"},
    26: {
        "title": "平板边界层抛物线流速分布与不同高度切应力计算",
        "chapter": 1,
        "kps": ["牛顿内摩擦定律"],
        "method": "分层液体切应力连续与速度叠加法",
        "difficulty": 2,
        "rubric": [
            {"label": "代入壁面无滑移 (0,0)、抛物线顶点 (1, 0.04) 及极值斜率为零条件求得 u(y) = -625y² + 50y", "pts": 6},
            {"label": "由 μ = ρν 求得动力黏度 μ = 1.0×10⁻³ Pa·s 并写出 τ = μ(du/dy) 表达式", "pts": 3},
            {"label": "求得 y = 0、2 cm、4 cm 三处切应力分别为 0.050 Pa、0.025 Pa、0 Pa（单位正确）", "pts": 6},
        ],
    },
    27: {
        "title": "双侧挡水倾斜矩形闸门启动最小钢绳拉力计算",
        "chapter": 2,
        "kps": ["平面静水总压力"],
        "method": "平面总压力形心法/分块合成法",
        "difficulty": 4,
        "rubric": [
            {"label": "求得左侧水体 ① 静水总压力 P1 = 981.0 kN 及对顶铰 A 的力臂 L1 = 32/15 m（逆时针压门力矩）", "pts": 7},
            {"label": "求得右侧水体 ② 静水总压力 P2 = 49.05 kN 及对顶铰 A 的力臂 L2 = 10/3 m（顺时针顶门力矩）", "pts": 6},
            {"label": "计入闸门自重 G 对顶铰 A 的逆时针压门力矩 G·(L/2)cos30°，按钢绳垂直门板最大力臂 L 求得 Tmin = 525.63 kN", "pts": 7},
        ],
    },
    28: {
        "title": "铅直平面内倾斜有压弯管水流作用力计算",
        "chapter": 3,
        "kps": ["恒定总流能量方程", "恒定总流动量方程", "弯管/底坎水流作用力"],
        "method": "能量方程求流量+控制体动量方程求反力",
        "difficulty": 3,
        "rubric": [
            {"label": "由连续性方程求流速 v ≈ 3.82 m/s，列 1-1 至 2-2 能量方程计入沿程与局部损失求得 p2 ≈ 45.92 kPa", "pts": 7},
            {"label": "取控制体列水平 x 向与铅垂 z 向动量方程（计入管内水重 G），求得管壁反力 Rx ≈ 87.84 N、Rz ≈ 283.87 N", "pts": 9},
            {"label": "合成水流对弯管作用力 R' ≈ 297.15 N 并指明方向（斜向右下方，与水平面夹角 72.8°）", "pts": 4},
        ],
    },
    29: {
        "title": "平坡矩形过水涵洞流量与顶板水平推力计算",
        "chapter": 3,
        "kps": ["恒定总流能量方程", "恒定总流动量方程", "弯管/底坎水流作用力"],
        "method": "能量方程求流量+控制体动量方程求反力",
        "difficulty": 3,
        "rubric": [
            {"label": "联立涵洞上下游断面连续性方程与能量方程（计入 hw = 0.1 m）求得 v2 ≈ 3.214 m/s 及流量 Q ≈ 6.94 m³/s", "pts": 7},
            {"label": "计算上下游断面静水总压力 P1、P2，列控制体水平动量方程求得涵洞顶板所受水平推力 R' ≈ 2.24 kN（水平向右）", "pts": 8},
        ],
    },
    30: {
        "title": "平面二维流场流函数、势函数求解与两点压强差计算",
        "chapter": 5,
        "kps": ["平面不可压缩流连续性方程", "无旋流判据", "流函数与速度势函数求解", "恒定总流能量方程"],
        "method": "不可压与无旋偏导检验+偏积分求原函数法",
        "difficulty": 2,
        "rubric": [
            {"label": "验证 ∂ux/∂x + ∂uy/∂y = 0 成立，积分求得流函数 ψ = (y² - x²)/2 + C", "pts": 5},
            {"label": "验证旋转角速度 ωz = 0 无旋条件成立，积分求得流速势函数 φ = xy + C（或 -xy + C）", "pts": 5},
            {"label": "由水平无旋定常流伯努利方程求得点 A(0,0) 与 B(1,1) 压强差 pA - pB = 800 Pa", "pts": 5},
        ],
    },
    31: {
        "title": "有压长管引水作用水头与下游水力最佳矩形明渠断面设计",
        "chapter": 7,
        "kps": ["明渠均匀流曼宁公式", "水力最佳断面", "长管串并联与三水池问题"],
        "method": "水力要素计算+曼宁公式+水力深度Fr判据",
        "difficulty": 3,
        "rubric": [
            {"label": "由相距 100 m 测压管水头差 1.5 m 求得长管水力坡度 J = 0.015 及管道总水头 H = 15 m", "pts": 4},
            {"label": "应用曼宁公式求得有压引水长管输送流量 Q ≈ 0.815 m³/s", "pts": 5},
            {"label": "结合矩形水力最佳断面条件 b = 2h（R = h/2）代入明渠曼宁公式解得 h ≈ 0.655 m、b ≈ 1.31 m", "pts": 6},
        ],
    },
}


def draw_corrected_q27_sol(dest_path: Path):
    """Draw corrected free-body & moment diagram for 2022 Q27 (T_min = 525.63 kN)."""
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    fig.patch.set_facecolor("white")

    th = np.radians(30.0)
    L = 4.0
    xA, yA = L * np.cos(th), L * np.sin(th)  # (3.464, 2.0)
    xB, yB = 0.0, 0.0

    # Floor & right vertical wall above A
    ax.plot([-1.2, 4.6], [0, 0], color="#64748b", lw=1.6)
    ax.plot([xA, xA], [yA, 3.3], color="#64748b", lw=1.6)

    # Normal unit vector from upper-left toward lower-right: (sin30, -cos30) = (0.5, -0.866)
    nx, ny = np.sin(th), -np.cos(th)
    # Upper-left trapezoid pressure prism (hA=4 -> 0.8, hB=6 -> 1.2)
    pA_top = (xA - 0.8 * nx, yA - 0.8 * ny)
    pB_top = (xB - 1.2 * nx, yB - 1.2 * ny)
    ax.add_patch(plt.Polygon([(xB, yB), (xA, yA), pA_top, pB_top],
                             closed=True, facecolor="#dbeafe", edgecolor="#2563eb", lw=1.3, alpha=0.8))

    # Lower-right triangle pressure prism on BC (L_BC = 2.0)
    xC, yC = 2.0 * np.cos(th), 2.0 * np.sin(th)
    pB_bot = (xB + 0.55 * nx, yB + 0.55 * ny)
    ax.add_patch(plt.Polygon([(xB, yB), (xC, yC), pB_bot],
                             closed=True, facecolor="#ffedd5", edgecolor="#ea580c", lw=1.3, alpha=0.85))

    # Gate bar AB and Hinge A
    ax.plot([xB, xA], [yB, yA], color="#0f172a", lw=5.0, zorder=5)
    ax.scatter([xA], [yA], s=95, facecolor="white", edgecolor="#0f172a", lw=2.2, zorder=6)
    ax.text(xA + 0.14, yA + 0.02, "顶铰 $A$", fontsize=11, fontweight="bold")
    ax.text(xB - 0.18, yB - 0.18, "$B$", fontsize=11, fontweight="bold")
    ax.text(0.55, 0.10, r"$\theta=30^\circ$", fontsize=9.5, color="#334155")

    # P1 vector at e1 = 7/15 L from B (L1 = 8/15 L from A) -> counterclockwise
    s1 = (7.0 / 15.0) * L
    x1, y1 = s1 * np.cos(th), s1 * np.sin(th)
    ax.annotate("", xy=(x1 - 0.04 * nx, y1 - 0.04 * ny), xytext=(x1 - 1.15 * nx, y1 - 1.15 * ny),
                arrowprops=dict(arrowstyle="->", color="#1d4ed8", lw=2.4), zorder=7)
    ax.text(x1 - 1.20 * nx - 0.05, y1 - 1.20 * ny + 0.05,
            r"$P_1 = 981.0\,\mathrm{kN}$（逆时针）" + "\n" + r"$L_1 = \frac{8}{15}L = 2.133\,\mathrm{m}$",
            fontsize=9.5, ha="right", color="#1e40af")

    # P2 vector at e2 = 2/3 m from B (L2 = 10/3 m from A) -> clockwise
    s2 = 2.0 / 3.0
    x2, y2 = s2 * np.cos(th), s2 * np.sin(th)
    ax.annotate("", xy=(x2 - 0.55 * nx, y2 - 0.55 * ny), xytext=(x2 + 0.48 * nx, y2 + 0.48 * ny),
                arrowprops=dict(arrowstyle="->", color="#ea580c", lw=2.3), zorder=7)
    ax.text(x2 + 0.52 * nx + 0.05, y2 + 0.52 * ny - 0.05,
            r"$P_2 = 49.05\,\mathrm{kN}$（顺时针）" + "\n" + r"$L_2 = \frac{10}{3}\,\mathrm{m}$",
            fontsize=9.5, ha="left", va="top", color="#c2410c")

    # Self-weight G at midpoint (L/2 = 2 m), straight down -> ALSO counterclockwise about A!
    xm, ym = 0.5 * xA, 0.5 * yA
    ax.annotate("", xy=(xm, ym - 0.95), xytext=(xm, ym),
                arrowprops=dict(arrowstyle="->", color="#334155", lw=2.4), zorder=7)
    ax.text(xm + 0.10, ym - 0.78,
            r"$G = 100\,\mathrm{kN}$（逆时针！）" + "\n" + r"$L_G = \frac{L}{2}\cos 30^\circ = \sqrt{3}\,\mathrm{m}$",
            fontsize=9.5, ha="left", va="center", color="#0f172a")

    # Cable tension T_min at B perpendicular to AB (up-left) -> clockwise
    ax.annotate("", xy=(xB - 1.18 * nx, yB - 1.18 * ny), xytext=(xB, yB),
                arrowprops=dict(arrowstyle="->", color="#15803d", lw=2.6), zorder=7)
    ax.text(xB - 1.22 * nx - 0.05, yB - 1.22 * ny + 0.02,
            r"$T_{\min} = 525.63\,\mathrm{kN}$" + "\n" + r"（最大力臂 $L = 4\,\mathrm{m}$，顺时针）",
            fontsize=10, ha="right", color="#15803d", fontweight="bold")

    ax.set_title("第 27 题：斜置平板闸门对顶铰 $A$ 的完整受力与力矩方向关系图", fontsize=11.5, pad=8)
    ax.set_xlim(-1.95, 4.75)
    ax.set_ylim(-0.95, 3.35)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(dest_path, dpi=220, facecolor="white")
    plt.close(fig)


def clean_prose(s: str) -> str:
    s = re.sub(r"随卷解析（随卷参考答案）", "原卷流网设定", s)
    s = re.sub(r"随卷参考答案\s*", "常见参考解答", s)
    return s.strip()


def main():
    with zipfile.ZipFile(DOCX_PATH) as zf:
        rels = {r.attrib["Id"]: r.attrib["Target"] for r in ET.fromstring(zf.read("word/_rels/document.xml.rels"))}
        body = ET.fromstring(zf.read("word/document.xml")).find("w:body", base_parser.NS)

        questions = {}
        analysis_buf = {k: [] for k in range(1, 32)}
        pitfalls_buf = {k: [] for k in range(1, 32)}

        part1 = False
        part2 = False
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

            if part1 and not part2 and ctag == "p":
                md, imgs = base_parser.paragraph_to_markdown(el, rels)
                md = clean_prose(md)
                if md.startswith(("一、", "二、", "三、")):
                    cur_q = None
                    idx += 1
                    continue

                m_q = re.match(r"^(\d{1,2})\.\s*(.+)$", md, flags=re.DOTALL)
                if m_q and 1 <= int(m_q.group(1)) <= 31:
                    qno = int(m_q.group(1))
                    stem_txt = m_q.group(2).strip()
                    score = 2
                    if qno <= 10:
                        qtype = "judge"
                        stem_txt = re.sub(r"[（(]\s*[）)]\s*$", "", stem_txt).strip()
                    elif qno <= 25:
                        qtype = "fill"
                    else:
                        qtype = "calc"
                        m_sc = re.search(r"[（(](\d+)\s*分[）)]\s*$", stem_txt)
                        score = int(m_sc.group(1)) if m_sc else 15
                        stem_txt = re.sub(r"[（(]\d+\s*分[）)]\s*$", "", stem_txt).strip()

                    questions[qno] = {
                        "id": f"2022-{qno:02d}",
                        "year": 2022,
                        "no": qno,
                        "type": qtype,
                        "score": score,
                        "title": META_2022[qno]["title"],
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
                    cap = f"题 {cur_q} 图"
                    if idx + 1 < len(children):
                        nxt = "".join(children[idx + 1].itertext()).strip()
                        if nxt.startswith("原卷附图"):
                            idx += 1
                    for i_im, media_rel in enumerate(imgs):
                        suf = "" if i_im == 0 else f"_{i_im+1}"
                        fname = f"q{cur_q:02d}_orig{suf}.png"
                        (FIG_DIR / fname).write_bytes(zf.read("word/" + media_rel))
                        questions[cur_q]["figures"].append({"src": f"figures/{fname}", "caption": cap})
                    idx += 1
                    continue

                if md and cur_q is not None and not md.startswith("原卷附图"):
                    questions[cur_q]["stem"] += "\n\n" + md
                idx += 1
                continue

            if part2 and ctag == "p":
                md, imgs = base_parser.paragraph_to_markdown(el, rels)
                md = clean_prose(md)
                if md.startswith(("一、", "二、", "三、")):
                    idx += 1
                    continue

                m_sol = re.match(r"^第\s*(\d{1,2})\s*题\s*【参考答案】\s*(.+)$", md)
                if m_sol:
                    cur_q = int(m_sol.group(1))
                    ans_txt = m_sol.group(2).strip()
                    questions[cur_q]["answer"] = ans_txt
                    questions[cur_q]["shortAnswer"] = ans_txt
                    if cur_q <= 10:
                        is_true = "√" in ans_txt.split("（")[0]
                        questions[cur_q]["judgeAnswer"] = is_true
                        questions[cur_q]["shortAnswer"] = "√" if is_true else "×"
                        questions[cur_q]["answer"] = "√（正确）" if is_true else "×（错误）"
                    idx += 1
                    continue

                if cur_q is None:
                    idx += 1
                    continue

                if imgs:
                    if idx + 1 < len(children):
                        nxt = "".join(children[idx + 1].itertext()).strip()
                        if nxt.startswith("解析分析附图"):
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

                if md.startswith(("【注意纠错】", "【重要纠错】", "【重要单位与题图辨析】")):
                    cleaned_pit = re.sub(r"^【[^】]+】", "", md).strip()
                    pitfalls_buf[cur_q].append(cleaned_pit)
                elif md:
                    analysis_buf[cur_q].append(md)

            idx += 1

    # Assemble questions 1..31
    final_questions = []
    for qno in range(1, 32):
        q = questions[qno]
        q["analysis"] = "\n\n".join(analysis_buf[qno]).strip()
        q["pitfalls"] = "\n\n".join(pitfalls_buf[qno]).strip()
        meta = META_2022[qno]
        q["chapter"] = meta["chapter"]
        q["kps"] = meta["kps"]
        q["method"] = meta["method"]
        q["difficulty"] = meta["difficulty"]
        if "subType" in meta:
            q["subType"] = meta["subType"]
        if "rubric" in meta:
            q["rubric"] = meta["rubric"]
        final_questions.append(q)

    # Override Q27 with physically exact sign-corrected gate moment solution & clean Matplotlib figure
    q27 = final_questions[26]
    draw_corrected_q27_sol(FIG_DIR / "q27_sol.png")
    q27["shortAnswer"] = "Tmin = 525.63 kN"
    q27["answer"] = "$T_{\\min} = 525.63\\,\\mathrm{kN}$"
    q27["analysis"] = (
        "**1. 求左侧水体 ① 对闸门的静水总压力 $P_1$ 及对顶铰 $A$ 的力臂 $L_1$**\n\n"
        "闸门铅垂投影高度为 $L\\sin 30^{\\circ} = 4 \\times 0.5 = 2.0\\,\\mathrm{m}$。因左侧水深 $H_1 = 6\\,\\mathrm{m} > 2.0\\,\\mathrm{m}$，闸门左侧全部淹没：\n\n"
        "- 门顶 $A$ 淹深 $h_A = H_1 - L\\sin 30^{\\circ} = 6 - 2 = 4.0\\,\\mathrm{m}$，门底 $B$ 淹深 $h_B = H_1 = 6.0\\,\\mathrm{m}$；\n"
        "- 形心淹深 $h_{c1} = \\frac{4 + 6}{2} = 5.0\\,\\mathrm{m}$，受压面积 $A_1 = bL = 5 \\times 4 = 20\\,\\mathrm{m^2}$；\n"
        "- 左侧静水总压力大小（垂直闸门指向右下方，绕顶铰 $A$ 产生**逆时针**压门力矩）：\n\n"
        "$$\nP_1 = \\rho g h_{c1} A_1 = 1000 \\times 9.81 \\times 5.0 \\times 20 = 981000\\,\\mathrm{N} = 981.0\\,\\mathrm{kN}\n$$\n\n"
        "- 梯形压强分布压心 $D_1$ 距底端 $B$ 的斜距为 $e_1 = \\frac{L}{3}\\cdot\\frac{2h_A + h_B}{h_A + h_B} = \\frac{4}{3}\\times\\frac{2\\times 4 + 6}{4 + 6} = \\frac{28}{15}\\,\\mathrm{m} = \\frac{7}{15}L$，故对顶铰 $A$ 的力臂为：\n\n"
        "$$\nL_1 = L - e_1 = 4 - \\frac{28}{15} = \\frac{32}{15}\\,\\mathrm{m} = \\frac{8}{15}L \\approx 2.1333\\,\\mathrm{m}\n$$\n\n"
        "**2. 求右侧水体 ② 对闸门的静水总压力 $P_2$ 及对顶铰 $A$ 的力臂 $L_2$**\n\n"
        "右侧水深 $H_2 = 1.0\\,\\mathrm{m} < 2.0\\,\\mathrm{m}$，仅下部浸水斜长 $L_{BC} = \\frac{H_2}{\\sin 30^{\\circ}} = 2.0\\,\\mathrm{m}$：\n\n"
        "- 受压面积 $A_2 = b L_{BC} = 5 \\times 2.0 = 10.0\\,\\mathrm{m^2}$，形心淹深 $h_{c2} = \\frac{H_2}{2} = 0.5\\,\\mathrm{m}$；\n"
        "- 右侧静水总压力大小（垂直闸门指向左上方，绕顶铰 $A$ 产生**顺时针**助开力矩）：\n\n"
        "$$\nP_2 = \\rho g h_{c2} A_2 = 1000 \\times 9.81 \\times 0.5 \\times 10.0 = 49050\\,\\mathrm{N} = 49.05\\,\\mathrm{kN}\n$$\n\n"
        "- 三角形压强分布压心 $D_2$ 距底端 $B$ 为 $e_2 = \\frac{1}{3}L_{BC} = \\frac{2}{3}\\,\\mathrm{m}$，对顶铰 $A$ 的力臂为：\n\n"
        "$$\nL_2 = L - e_2 = 4 - \\frac{2}{3} = \\frac{10}{3}\\,\\mathrm{m} \\approx 3.3333\\,\\mathrm{m}\n$$\n\n"
        "**3. 计入闸门自重 $G$ 对顶铰 $A$ 的力矩**\n\n"
        "由题图知，顶铰 $A$ 在右上方、门底 $B$ 在左下方，闸门质心位于铰链 $A$ 左侧，自重 $G = 100\\,\\mathrm{kN}$ 竖直向下作用于门板中点，与 $P_1$ 同向绕顶铰 $A$ 产生**逆时针**压门力矩，其水平力臂为：\n\n"
        "$$\nL_G = \\frac{L}{2}\\cos 30^{\\circ} = 2 \\times \\frac{\\sqrt{3}}{2} = \\sqrt{3}\\,\\mathrm{m} \\approx 1.7321\\,\\mathrm{m}\n$$\n\n"
        "**4. 对顶铰 $A$ 列力矩平衡求最小钢绳拉力 $T_{\\min}$**\n\n"
        "要向上拉起闸门，当钢绳拉力方向垂直于门板 $AB$ 向左上方拉动时，力臂达到最大值 $L_{T,\\max} = L = 4\\,\\mathrm{m}$（产生**顺时针**开启力矩），所需拉力最小。临界启动时底端 $B$ 支持力为零，由 $\\sum M_A = 0$：\n\n"
        "$$\nP_1 L_1 + G L_G - P_2 L_2 - T_{\\min} L = 0\n$$\n\n"
        "代入各力矩项：\n\n"
        "- $P_1 L_1 = 981.0 \\times \\frac{32}{15} = 2092.80\\,\\mathrm{kN\\cdot m}$\n"
        "- $G L_G = 100 \\times \\sqrt{3} = 173.205\\,\\mathrm{kN\\cdot m}$\n"
        "- $P_2 L_2 = 49.05 \\times \\frac{10}{3} = 163.50\\,\\mathrm{kN\\cdot m}$\n\n"
        "解得：\n\n"
        "$$\nT_{\\min} = \\frac{2092.80 + 173.205 - 163.50}{4} = \\frac{2102.505}{4} = 525.626\\,\\mathrm{kN} \\approx 525.63\\,\\mathrm{kN}\n$$"
    )
    q27["pitfalls"] = (
        "本题有三大高频失分陷阱：① 压心距底边 $B$ 为 $e_1 = \\frac{7}{15}L$，而对**顶铰 $A$** 的力臂应为 $L_1 = L - e_1 = \\frac{8}{15}L$，切勿代反；"
        "② 切勿漏计闸门自重 $G = 100\\,\\mathrm{kN}$；"
        "③ 判定力矩正负号时看清几何方位：门板位于顶铰 $A$ 的左下方，故向下的自重 $G$ 与左上侧水压力 $P_1$ 同为逆时针压门力矩（使所需提门拉力增大），切忌把 $G L_G$ 符号写反成减号！"
    )

    paper = {
        "year": 2022,
        "code": "814",
        "subject": "水力学",
        "school": "河海大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": False,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "统一取重力加速度 $g = 9.81\\,\\mathrm{m/s^2}$，水密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$。",
            "题型与分值：一、是非题（10×2=20 分）；二、填空题（15×2=30 分）；三、计算题（共 6 题，分别为 15、20、20、15、15、15 分，共 100 分）。"
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
                "title": "三、计算题",
                "description": "共 6 小题（15+20+20+15+15+15 分），共 100 分。",
                "range": [26, 31],
                "totalScore": 100
            }
        ],
        "questions": final_questions,
    }

    out_json = OUT_DIR / "2022.json"
    out_json.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote standardized HHU 2022 JSON ({len(final_questions)} questions) -> {out_json}")


if __name__ == "__main__":
    main()
