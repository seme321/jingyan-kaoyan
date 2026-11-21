# -*- coding: utf-8 -*-
"""
Generate stem figures (300 DPI crops `q*_orig.png`), Matplotlib solution schematics (`q*_sol.png`),
standardized exam packs (`扬州大学已整理数据/{2013,2012}/{year}.json` + `figures/`), and web-ready
JSON + WebP assets (`web/public/data/yzu-849/{2013,2012}.json` + `figures/{2013,2012}/*.webp`)
for Yangzhou University 849 Hydraulics (2013 & 2012).

Key independent verifications & fixes over raw third-party reference handouts:
  - 2013 Q10 & 2012 Q04 (single_choice): Fixed erroneous option C -> A ("总水头线与自由水面线重合" is false;
    in uniform open-channel flow the H.G.L. coincides with the free surface and is parallel to the bed slope,
    whereas the E.G.L. lies αv²/(2g) above the free surface).
  - 2012 Q18 (fill #8): Fixed erroneous "保持不变" -> "沿程线性减小（降低）" (in real horizontal uniform pipe flow
    with friction loss hf = J·l > 0, piezometric pressure must decrease linearly along the flow).
  - 2012 Q24 (calc #2): Fixed force unit kN/m² -> kN (Px = 19.60 kN, Pz = 95.52 kN, P = 97.51 kN at g=9.80;
    19.62 / 95.62 / 97.61 kN at g=9.81, θ = 78.40° upward-right through cylinder center).
  - 2012 Q25 (calc #3): Derived exact two-run quadratic-zone relation (λL/d + ζ) = 6.321 (avg of 6.323 and 6.318
    at g=9.80; 6.327 at g=9.81), explicitly noting the omitted textbook friction factor λ = 0.03 -> ζ ≈ 0.32.
  - 2012 Q26 (calc #4): Resolved exam print typos ("465.48 kN" vs original textbook "456.48 N" = 1080 - 720*0.866):
    frictionless vertical plate yields Ry = 0 -> sin θ = Q1/Q2 = 12/24 = 0.5 -> θ = 30° (and Fx = 456.46 N),
    while documenting the literal x-momentum angle θ ≈ 31.4° if 465.48 N is substituted directly.
"""

import copy
import json
import math
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "扬州大学待处理数据"
PACK_ROOT = ROOT / "扬州大学已整理数据"
WEB_COURSE_DIR = ROOT / "web" / "public" / "data" / "yzu-849"


def trim_and_pad(img: Image.Image, pad: int = 16, thresh: int = 205, bg_clean: int = 232) -> Image.Image:
    rgb = img.convert("RGB")
    gray = np.array(rgb.convert("L"))
    mask = gray < thresh
    if not np.any(mask):
        return rgb
    ys, xs = np.where(mask)
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    cropped = np.array(rgb)[y0:y1, x0:x1].copy()
    cropped_g = gray[y0:y1, x0:x1]
    cropped[cropped_g > bg_clean] = 255
    h, w, _ = cropped.shape
    canvas = np.full((h + 2 * pad, w + 2 * pad, 3), 255, dtype=np.uint8)
    canvas[pad:pad + h, pad:pad + w] = cropped
    return Image.fromarray(canvas)


# ==============================================================================
# 2013 STEM CROPS (300 DPI) & MATPLOTLIB SOLUTION DIAGRAMS
# ==============================================================================

def build_2013_figures(fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(RAW_DIR / "849-水力学（水）2013.pdf")
    crops = [
        ("q04_orig.png", 0, (155, 412, 470, 505)),
        ("q05_orig.png", 0, (185, 543, 455, 650)),
        ("q22_orig.png", 2, (145, 185, 310, 316)),
        ("q23_orig.png", 2, (320, 195, 495, 312)),
        ("q25_orig.png", 2, (165, 412, 465, 485)),
        ("q26_orig.png", 3, (130, 62, 285, 212)),
        ("q27_orig.png", 3, (335, 102, 470, 198)),
        ("q28_orig.png", 3, (195, 384, 445, 468)),
        ("q29_orig.png", 3, (358, 520, 512, 603)),
    ]
    for fname, pno, rect in crops:
        pix = doc[pno].get_pixmap(dpi=300, clip=pymupdf.Rect(*rect))
        im = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        if fname == "q28_orig.png":
            arr = np.array(im)
            h_im, w_im, _ = arr.shape
            # Mask out stray top-left stem text ("是否满足要求。（15分）") without touching apex label "A"
            arr[0:int(0.11 * h_im), 0:int(0.46 * w_im)] = 255
            im = Image.fromarray(arr)
        trim_and_pad(im, pad=16, thresh=205, bg_clean=232).save(fig_dir / fname)

    draw_2013_q05_sol(fig_dir / "q05_sol.png")
    draw_2013_q26_sol(fig_dir / "q26_sol.png")
    draw_2013_q27_sol(fig_dir / "q27_sol.png")
    draw_2013_q28_sol(fig_dir / "q28_sol.png")
    draw_2013_q29_sol(fig_dir / "q29_sol.png")


def draw_2013_q05_sol(out_path: Path) -> None:
    """Superposition of left upward semicircle & right downward lower quarter-circle -> net upper quarter-circle (Option C)."""
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.6))
    fig.patch.set_facecolor("white")

    R = 1.0
    th_all = np.linspace(np.pi / 2, 3 * np.pi / 2, 160)
    th_up = np.linspace(np.pi / 2, np.pi, 90)
    th_dn = np.linspace(np.pi, 3 * np.pi / 2, 90)

    # Panel 1: Left water alone -> full semicircle upward
    ax = axes[0]
    poly_semi = [(0.0, R)] + [(R * np.cos(t), R * np.sin(t)) for t in th_all] + [(0.0, -R)]
    ax.add_patch(patches.Polygon(poly_semi, closed=True, facecolor="#dbeafe", edgecolor="#2563eb", lw=1.4, hatch="///", alpha=0.82))
    ax.plot(R * np.cos(th_all), R * np.sin(th_all), color="#0f172a", lw=2.6)
    ax.annotate("", xy=(-0.42, 0.55), xytext=(-0.42, -0.55), arrowprops=dict(arrowstyle="->", color="#1d4ed8", lw=2.4))
    ax.text(-0.42, -1.28, r"$\frac{1}{2}\pi R^2$（虚压力体，向上）", fontsize=9.2, ha="center", color="#1e40af")
    ax.set_title("1. 左侧水深 $h$ 单独作用", fontsize=10.2, pad=6)

    # Panel 2: Right water (depth h/2) -> lower quarter-circle downward
    ax = axes[1]
    poly_qdn = [(0.0, 0.0)] + [(R * np.cos(t), R * np.sin(t)) for t in th_dn] + [(0.0, -R)]
    ax.add_patch(patches.Polygon(poly_qdn, closed=True, facecolor="#fee2e2", edgecolor="#dc2626", lw=1.4, hatch="\\\\\\", alpha=0.82))
    ax.plot(R * np.cos(th_all), R * np.sin(th_all), color="#94a3b8", lw=1.4, ls="--")
    ax.plot(R * np.cos(th_dn), R * np.sin(th_dn), color="#0f172a", lw=2.6)
    ax.annotate("", xy=(-0.42, -0.78), xytext=(-0.42, -0.15), arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.4))
    ax.text(-0.42, -1.28, r"$\frac{1}{4}\pi R^2$（实压力体，向下）", fontsize=9.2, ha="center", color="#b91c1c")
    ax.set_title("2. 右侧水深 $h/2$ 单独作用", fontsize=10.2, pad=6)

    # Panel 3: Net superposition -> upper quarter-circle upward (Option C!)
    ax = axes[2]
    poly_qup = [(0.0, R)] + [(R * np.cos(t), R * np.sin(t)) for t in th_up] + [(0.0, 0.0)]
    ax.add_patch(patches.Polygon(poly_qup, closed=True, facecolor="#dcfce7", edgecolor="#16a34a", lw=1.5, hatch="///", alpha=0.85))
    ax.plot(R * np.cos(th_all), R * np.sin(th_all), color="#94a3b8", lw=1.3, ls="--")
    ax.plot(R * np.cos(th_up), R * np.sin(th_up), color="#0f172a", lw=2.6)
    ax.plot([-R, 0.0], [0.0, 0.0], color="#0f172a", lw=1.6)
    ax.annotate("", xy=(-0.42, 0.78), xytext=(-0.42, 0.14), arrowprops=dict(arrowstyle="->", color="#15803d", lw=2.6))
    ax.text(-0.42, -1.28, r"净压力体 $\frac{1}{4}\pi R^2$（向上，选 C）", fontsize=9.4, ha="center", color="#166534", fontweight="bold")
    ax.set_title("3. 左右叠加抵消下半圆结果", fontsize=10.2, pad=6)

    for ax in axes:
        ax.text(0.06, R, "$M$", fontsize=9.5, fontweight="bold")
        ax.text(0.06, -R - 0.05, "$N$", fontsize=9.5, fontweight="bold")
        ax.set_xlim(-1.35, 0.45)
        ax.set_ylim(-1.48, 1.25)
        ax.set_aspect("equal")
        ax.axis("off")

    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2013_q26_sol(out_path: Path) -> None:
    """Equal-pressure plane analysis for 2013 Q26 closed tank + sealed tube + U-tube mercury manometer."""
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    fig.patch.set_facecolor("white")

    # Main tank: x in [2.6, 4.6], y in [0.9, 3.0], dome above y=3.0, water surface at y=2.2
    ax.add_patch(patches.Rectangle((2.6, 0.9), 2.0, 1.3, facecolor="#e0f2fe", edgecolor="none", alpha=0.85))
    ax.plot([2.6, 2.6], [0.9, 3.0], color="#0f172a", lw=2.0)
    ax.plot([4.6, 4.6], [0.9, 3.0], color="#0f172a", lw=2.0)
    ax.plot([2.6, 4.6], [0.9, 0.9], color="#0f172a", lw=2.0)
    th_d = np.linspace(0, np.pi, 80)
    ax.plot(3.6 + 1.0 * np.cos(th_d), 3.0 + 0.55 * np.sin(th_d), color="#0f172a", lw=2.0)
    ax.plot([2.6, 4.6], [2.2, 2.2], color="#0284c7", lw=2.0)
    ax.text(3.6, 2.68, r"$p_c = 107.40\,\mathrm{kPa}$（绝压）", fontsize=9.5, ha="center", color="#0f172a", fontweight="bold")

    # Right sealed tube: x in [5.25, 5.45], water up to y=3.70, gas p0=78 kPa above
    ax.add_patch(patches.Rectangle((4.6, 1.05), 0.85, 0.16, facecolor="#e0f2fe", edgecolor="none"))
    ax.add_patch(patches.Rectangle((5.28, 1.05), 0.17, 2.65, facecolor="#bae6fd", edgecolor="none"))
    ax.plot([4.6, 5.28, 5.28], [1.21, 1.21, 4.25], color="#0f172a", lw=1.8)
    ax.plot([4.6, 5.45, 5.45], [1.05, 1.05, 4.25], color="#0f172a", lw=1.8)
    th_t = np.linspace(0, np.pi, 40)
    ax.plot(5.365 + 0.085 * np.cos(th_t), 4.25 + 0.12 * np.sin(th_t), color="#0f172a", lw=1.8)
    ax.plot([5.28, 5.45], [3.70, 3.70], color="#0284c7", lw=2.0)
    ax.text(5.56, 4.02, r"$p_0 = 78\,\mathrm{kPa}$（绝压）", fontsize=9.2, ha="left", color="#0369a1")

    # Dimension 3m on right
    ax.plot([4.65, 5.85], [2.20, 2.20], color="#64748b", lw=1.0, ls="--")
    ax.plot([5.48, 5.85], [3.70, 3.70], color="#64748b", lw=1.0, ls="--")
    ax.annotate("", xy=(5.72, 3.70), xytext=(5.72, 2.20), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.3))
    ax.text(5.80, 2.95, r"$h_{\mathrm{R}} = 3\,\mathrm{m}$", fontsize=9.2, va="center")

    # Left U-tube mercury manometer: right limb x=1.75 (meniscus at y=0.70), left limb x=1.05 (meniscus at y=1.25)
    ax.add_patch(patches.Rectangle((1.75, 0.70), 0.16, 0.90, facecolor="#bae6fd", edgecolor="none"))
    ax.add_patch(patches.Rectangle((1.75, 1.44), 0.85, 0.16, facecolor="#bae6fd", edgecolor="none"))
    # Mercury fill in U-tube
    ax.add_patch(patches.Rectangle((1.05, 0.28), 0.16, 0.97, facecolor="#475569", edgecolor="none"))
    ax.add_patch(patches.Rectangle((1.75, 0.28), 0.16, 0.42, facecolor="#475569", edgecolor="none"))
    ax.add_patch(patches.Rectangle((1.05, 0.28), 0.86, 0.16, facecolor="#475569", edgecolor="none"))
    # U-tube walls
    ax.plot([2.6, 1.75, 1.75], [1.60, 1.60, 0.44], color="#0f172a", lw=1.8)
    ax.plot([2.6, 1.91, 1.91, 1.05, 1.05], [1.44, 1.44, 0.28, 0.28, 1.75], color="#0f172a", lw=1.8)
    ax.plot([1.21, 1.21, 1.75], [1.75, 0.44, 0.44], color="#0f172a", lw=1.8)
    ax.text(1.13, 1.85, r"$p_a = 98\,\mathrm{kPa}$", fontsize=9.2, ha="center", color="#334155")

    # Equal pressure plane 1-1 at y=0.70 (lower mercury meniscus)
    ax.plot([0.55, 2.38], [0.70, 0.70], color="#dc2626", lw=1.8, ls="--", zorder=6)
    ax.text(1.42, 0.08, "等压面 1-1（同种连续水银）", fontsize=8.9, ha="center", color="#b91c1c", fontweight="bold")
    ax.annotate("", xy=(1.48, 0.67), xytext=(1.48, 0.22),
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=1.2, ls=":"), zorder=6)

    # Dimensions 3m and dh on left
    ax.plot([2.05, 2.55], [2.20, 2.20], color="#64748b", lw=1.0, ls="--")
    ax.annotate("", xy=(2.22, 2.20), xytext=(2.22, 0.70), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.3))
    ax.text(2.28, 1.90, r"$3\,\mathrm{m}$", fontsize=9.0, ha="left")

    ax.annotate("", xy=(0.82, 1.25), xytext=(0.82, 0.70), arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.5))
    ax.text(0.75, 0.98, r"$\Delta h = 0.291\,\mathrm{m}$", fontsize=9.2, ha="right", va="center", color="#b91c1c", fontweight="bold")

    ax.text(4.62, 0.16, r"等压面平衡：$p_c + \rho g(3\,\mathrm{m}) = p_a + \rho_{\mathrm{Hg}} g \Delta h$",
            fontsize=9.2, ha="center", color="#1e3a8a",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#f8fafc", edgecolor="#93c5fd"))

    ax.set_title("2013 年第 26 题：密闭容器气相压强与水银压差计等压面分析图", fontsize=11, pad=6)
    ax.set_xlim(0.0, 6.95)
    ax.set_ylim(-0.08, 4.55)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2013_q27_sol(out_path: Path) -> None:
    """Quarter-circle gate AB (R = H = 4 m, center O at bottom-right) real downward pressure body & resultant."""
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    fig.patch.set_facecolor("white")

    R = 2.4  # visual radius for 4 m
    ths = np.linspace(np.pi / 2, np.pi, 140)
    arc_x, arc_y = R * np.cos(ths), R * np.sin(ths)

    # Water background on left
    poly_w = [(-4.15, R), (0.0, R)] + list(zip(arc_x, arc_y)) + [(-4.15, 0.0)]
    ax.add_patch(patches.Polygon(poly_w, closed=True, facecolor="#e0f2fe", edgecolor="none", alpha=0.65))

    # Real downward pressure body directly above arc AB (x in [-R, 0])
    poly_pb = [(-R, R), (0.0, R)] + list(zip(arc_x, arc_y))
    ax.add_patch(patches.Polygon(poly_pb, closed=True, facecolor="#bfdbfe", edgecolor="#2563eb", lw=1.3, hatch="///", alpha=0.85))
    ax.text(-1.85, 2.08, "实压力体\n" + r"（$P_z$ 竖直向下）", fontsize=8.8, ha="center", va="center", color="#1e40af", fontweight="bold")

    # Floor, right vertical & quarter-circle gate AB
    ax.plot([-4.15, 0.0], [R, R], color="#0284c7", lw=2.0)
    ax.plot([-4.15, 0.0, 0.0], [0.0, 0.0, R], color="#0f172a", lw=2.0)
    ax.plot(arc_x, arc_y, color="#0f172a", lw=3.6, zorder=5)
    ax.add_patch(patches.Rectangle((-0.22, 0.0), 0.22, 0.22, fill=False, edgecolor="#0f172a", lw=1.2))
    ax.scatter([0.0], [0.0], color="#0f172a", s=34, zorder=6)
    ax.text(0.10, -0.14, "$O$（圆心）", fontsize=9.8, fontweight="bold")
    ax.text(0.08, R + 0.05, "$A$", fontsize=10.5, fontweight="bold")
    ax.text(-R - 0.16, -0.18, "$B$", fontsize=10.5, fontweight="bold")

    # Point of action D on arc AB at theta = 23.23 deg above negative x-axis!
    ang = np.radians(23.23)
    xD, yD = -R * np.cos(ang), R * np.sin(ang)
    ax.scatter([xD], [yD], color="#dc2626", s=48, zorder=8)
    ax.text(xD + 0.22, yD + 0.08, "$D$（压心）", fontsize=9.3, ha="left", va="bottom", color="#b91c1c", fontweight="bold")
    # Line of action from upper-left through D to O
    ax.plot([xD - 0.80 * np.cos(ang), 0.0], [yD + 0.80 * np.sin(ang), 0.0], color="#dc2626", lw=1.4, ls="--", zorder=6)
    ax.annotate("", xy=(xD + 1.05 * np.cos(ang), yD - 1.05 * np.sin(ang)), xytext=(xD, yD),
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.8), zorder=7)
    ax.text(0.18, 0.82,
            r"$P = 170.63\,\mathrm{kN}$（$g=9.80$）" + "\n"
            + r"$P_x = 156.80\,\mathrm{kN}\ (\rightarrow)$" + "\n"
            + r"$P_z = 67.30\,\mathrm{kN}\ (\downarrow)$" + "\n"
            + r"$\theta = 23.23^{\circ}$（指向圆心 $O$）",
            fontsize=9.2, color="#991b1b", ha="left", va="center",
            bbox=dict(boxstyle="round,pad=0.30", facecolor="#fef2f2", edgecolor="#fca5a5"))

    # Depth H=4m and hD=2.42m dimensions
    ax.annotate("", xy=(-3.88, R), xytext=(-3.88, 0.0), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.3))
    ax.text(-3.98, 0.5 * R, r"$H = R = 4\,\mathrm{m}$", fontsize=9.2, ha="right", va="center")

    ax.plot([xD, -2.65], [yD, yD], color="#64748b", lw=1.0, ls=":")
    ax.annotate("", xy=(-2.65, R), xytext=(-2.65, yD), arrowprops=dict(arrowstyle="<->", color="#b91c1c", lw=1.3))
    ax.text(-2.72, 0.5 * (R + yD) + 0.05, r"$h_D = 2.42\,\mathrm{m}$", fontsize=8.9, ha="right", va="center", color="#b91c1c")

    ax.set_title("2013 年第 27 题：1/4 圆弧闸门 AB 实压力体与静水总压力作用点分析图", fontsize=11, pad=6)
    ax.set_xlim(-5.15, 2.40)
    ax.set_ylim(-0.35, 2.85)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2013_q28_sol(out_path: Path) -> None:
    """Siphon with submerged exit: H.G.L. meets downstream water level smoothly; E.G.L. stays v^2/(2g) above and drops at exit."""
    fig, ax = plt.subplots(figsize=(8.8, 4.3))
    fig.patch.set_facecolor("white")

    # Upstream & downstream water levels
    z_up, z_dn = 2.30, 0.85
    # Dam / embankment profile
    ax.add_patch(patches.Polygon([(0.4, 0.0), (2.7, 3.15), (4.5, 3.15), (6.5, 0.55), (6.5, 0.0)],
                                 closed=True, facecolor="#f1f5f9", edgecolor="#64748b", lw=1.4))
    # Downstream basin
    ax.add_patch(patches.Rectangle((6.5, 0.15), 2.1, z_dn - 0.15, facecolor="#e0f2fe", edgecolor="none", alpha=0.75))
    ax.plot([6.5, 6.5, 8.6, 8.6], [1.35, 0.15, 0.15, 1.35], color="#0f172a", lw=1.8)
    ax.plot([0.1, 2.05], [z_up, z_up], color="#0284c7", lw=2.0)
    ax.plot([6.5, 8.6], [z_dn, z_dn], color="#0284c7", lw=2.0)
    ax.text(0.55, z_up + 0.10, "上游水面", fontsize=9.2, color="#0369a1")
    ax.text(7.75, z_dn + 0.10, "下游水面", fontsize=9.2, color="#0369a1")

    # Siphon pipe centerline: inlet (1.5, 1.65) -> bend1 (2.7, 3.30) -> bend2 A (4.4, 3.30) -> bend3 (6.2, 0.58) -> submerged exit (7.1, 0.58)
    px = [1.5, 2.7, 4.4, 6.2, 7.1]
    py = [1.65, 3.30, 3.30, 0.58, 0.58]
    ax.plot(px, py, color="#0f172a", lw=5.0, solid_capstyle="butt", zorder=4)
    ax.plot(px, py, color="#bae6fd", lw=2.4, solid_capstyle="butt", zorder=5)
    ax.scatter([4.4], [3.30], color="#dc2626", s=45, zorder=8)
    ax.text(4.45, 3.44, "$A$（最高最险断面）", fontsize=9.4, color="#b91c1c", fontweight="bold")

    # Physically accurate E.G.L. (green solid) and H.G.L. (purple dash-dot) for submerged exit (zeta_exit = 1.0):
    # Upstream tank EGL = HGL = z_up (2.30). Velocity head hv = 0.28.
    # Inlet loss drop = 0.22 -> EGL(inlet) = 2.08; HGL(inlet) = 1.80.
    # Along pipe, EGL slopes down monotonically; at submerged exit (x=7.1), HGL meets z_dn (0.85) smoothly from above,
    # while EGL stays hv=0.28 above HGL (at 1.13) and drops vertically by zeta2*hv = 0.28 to z_dn (0.85)!
    hv = 0.28
    ex = [0.2, 1.5, 1.5, 2.7, 4.4, 6.2, 7.1, 7.1, 8.5]
    ey = [z_up, z_up, 2.08, 1.84, 1.58, 1.24, z_dn + hv, z_dn, z_dn]
    hx = [1.5, 2.7, 4.4, 6.2, 7.1]
    hy = [2.08 - hv, 1.84 - hv, 1.58 - hv, 1.24 - hv, z_dn]
    ax.plot(ex, ey, color="#15803d", lw=2.2, zorder=6, label="总水头线 E.G.L.（出口竖直跌落 $\\zeta_2 v^2/(2g)$）")
    ax.plot(hx, hy, color="#7c3aed", lw=2.1, ls="-.", zorder=7, label="测压管水头线 H.G.L.（淹没出口平滑接下游水面）")

    # Negative pressure (vacuum) at apex A: vertical distance from A (3.30) down to HGL(A) (1.30)
    ax.annotate("", xy=(4.4, 1.32), xytext=(4.4, 3.24), arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.6))
    ax.text(4.26, 2.48,
            r"$A$ 点真空高度" + "\n" + r"$h_{vA} = 5.85\,\mathrm{m}$" + "\n" + r"（$< [h_v] = 9.98\,\mathrm{m}$）",
            fontsize=8.6, color="#991b1b", ha="right", va="center",
            bbox=dict(boxstyle="round,pad=0.22", facecolor="#fff1f2", edgecolor="#fda4af"), zorder=9)

    # Dimensions h1 = 3.5 m, h2 = 4.0 m
    ax.plot([1.0, 2.65], [3.30, 3.30], color="#64748b", lw=1.0, ls=":")
    ax.annotate("", xy=(1.25, 3.30), xytext=(1.25, z_up), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.3))
    ax.text(1.18, 0.5 * (3.30 + z_up), r"$h_1 = 3.5\,\mathrm{m}$", fontsize=9.0, ha="right", va="center")

    ax.plot([6.8, 7.9], [z_up, z_up], color="#64748b", lw=1.0, ls=":")
    ax.annotate("", xy=(7.45, z_up), xytext=(7.45, z_dn), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.3))
    ax.text(7.55, 0.5 * (z_up + z_dn), r"$h_2 = 4.0\,\mathrm{m}$", fontsize=9.0, ha="left", va="center")

    ax.set_title("2013 年第 28 题：虹吸管总水头线、测压管水头线与坝顶 A 断面真空校核图", fontsize=11, pad=6)
    ax.legend(loc="lower left", fontsize=8.4, framealpha=0.94)
    ax.set_xlim(0.0, 8.85)
    ax.set_ylim(-0.05, 3.80)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2013_q29_sol(out_path: Path) -> None:
    """Bifurcated river flow distribution diagram for 2013 Q29."""
    fig, ax = plt.subplots(figsize=(8.6, 3.6))
    fig.patch.set_facecolor("white")

    # Outer river banks + island
    ax.add_patch(patches.Polygon([(0.4, 0.7), (8.2, 0.7), (8.2, 1.45), (7.2, 1.45), (6.5, 2.75), (2.1, 2.75), (1.4, 1.45), (0.4, 1.45)],
                                 closed=True, facecolor="#e0f2fe", edgecolor="#0f172a", lw=2.0))
    ax.add_patch(patches.Polygon([(2.3, 1.45), (6.3, 1.45), (5.8, 2.20), (2.8, 2.20)],
                                 closed=True, facecolor="#f1f5f9", edgecolor="#0f172a", lw=1.8))
    ax.text(4.3, 1.80, "江心洲（分汊岛）", fontsize=9.2, ha="center", color="#475569")

    # Section 1-1 and Section 2-2
    ax.plot([1.0, 1.0], [0.45, 1.75], color="#dc2626", lw=1.8, ls="--")
    ax.plot([7.6, 7.6], [0.45, 1.75], color="#dc2626", lw=1.8, ls="--")
    ax.text(1.0, 1.92, r"断面 1-1" + "\n" + r"$\nabla_1 = 120.00\,\mathrm{m}$", fontsize=9.2, ha="center", color="#b91c1c", fontweight="bold")
    ax.text(7.6, 1.92, r"断面 2-2" + "\n" + r"$\nabla_2 = 119.87\,\mathrm{m}$", fontsize=9.2, ha="center", color="#b91c1c", fontweight="bold")

    # Flow arrows & values
    ax.annotate("", xy=(5.1, 2.48), xytext=(3.4, 2.48), arrowprops=dict(arrowstyle="->", color="#1d4ed8", lw=2.2))
    ax.text(4.3, 2.95, r"北汊（长而浅）：$l_1=6000\,\mathrm{m},\ K_1=9576\,\mathrm{m^3/s},\ Q_1 = 45.07\,\mathrm{m^3/s}$",
            fontsize=9.2, ha="center", color="#1e40af", fontweight="bold")

    ax.annotate("", xy=(5.1, 1.08), xytext=(3.4, 1.08), arrowprops=dict(arrowstyle="->", color="#15803d", lw=2.6))
    ax.text(4.3, 0.32, r"主槽（短而深）：$l_2=2500\,\mathrm{m},\ K_2=48681\,\mathrm{m^3/s},\ Q_2 = 354.93\,\mathrm{m^3/s}$",
            fontsize=9.2, ha="center", color="#166534", fontweight="bold")

    ax.text(0.45, 1.08, r"$Q=400$", fontsize=8.8, ha="left", va="center", color="#0f172a")
    ax.text(7.72, 1.08, r"$Q_1+Q_2=400$", fontsize=8.5, ha="left", va="center", color="#0f172a")

    ax.set_title("2013 年第 29 题：分汊矩形河道共用落差 $\\Delta Z = 0.133\\,\\mathrm{m}$ 与流量分配示意图", fontsize=11, pad=6)
    ax.set_xlim(0.1, 9.1)
    ax.set_ylim(0.05, 3.35)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


# ==============================================================================
# 2012 STEM CROPS (300 DPI) & MATPLOTLIB SOLUTION DIAGRAMS
# ==============================================================================

def build_2012_figures(fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(RAW_DIR / "849-水力学（水）2012.pdf")
    crops = [
        ("q10_orig.png", 1, (70, 68, 198, 128)),
        ("q23_orig.png", 1, (305, 490, 475, 635)),
        ("q24_orig.png", 2, (265, 92, 470, 198)),
        ("q25_orig.png", 2, (295, 305, 450, 428)),
        ("q26_orig.png", 2, (85, 480, 300, 648)),
    ]
    for fname, pno, rect in crops:
        pix = doc[pno].get_pixmap(dpi=300, clip=pymupdf.Rect(*rect))
        im = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        if fname == "q26_orig.png":
            arr = np.array(im)
            h_im, w_im, _ = arr.shape
            # Mask out stray top stem text sliver ("摩擦力，试求偏转角度 θ") above section "2-2"
            arr[0:int(0.052 * h_im), :] = 255
            im = Image.fromarray(arr)
        trim_and_pad(im, pad=16, thresh=205, bg_clean=232).save(fig_dir / fname)

    draw_2012_q23_sol(fig_dir / "q23_sol.png")
    draw_2012_q24_sol(fig_dir / "q24_sol.png")
    draw_2012_q25_sol(fig_dir / "q25_sol.png")
    draw_2012_q26_sol(fig_dir / "q26_sol.png")


def draw_2012_q23_sol(out_path: Path) -> None:
    """Closed tank with left sealed tube (p0, h0) and right open piezometer (pa, x)."""
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    fig.patch.set_facecolor("white")

    # Tank: x in [2.1, 4.3], y in [0.9, 2.8], water surface at y=1.95
    ax.add_patch(patches.Rectangle((2.1, 0.9), 2.2, 1.05, facecolor="#e0f2fe", edgecolor="none", alpha=0.85))
    ax.plot([2.1, 2.1, 4.3, 4.3, 2.1], [2.8, 0.9, 0.9, 2.8, 2.8], color="#0f172a", lw=2.0)
    ax.plot([2.1, 4.3], [1.95, 1.95], color="#0284c7", lw=2.0)
    ax.text(3.2, 2.38, r"$p_c = p_0 + \rho g h_0 = 107.91\,\mathrm{kPa}$", fontsize=9.2, ha="center", color="#0f172a", fontweight="bold")

    # Left sealed glass tube: x in [1.15, 1.35], water up to y=3.25 (h0 = 2m above 1.95)
    ax.add_patch(patches.Rectangle((1.15, 1.15), 0.95, 0.18, facecolor="#bae6fd", edgecolor="none"))
    ax.add_patch(patches.Rectangle((1.15, 1.15), 0.20, 2.10, facecolor="#bae6fd", edgecolor="none"))
    ax.plot([2.1, 1.35, 1.35], [1.33, 1.33, 3.85], color="#0f172a", lw=1.8)
    ax.plot([2.1, 1.15, 1.15], [1.15, 1.15, 3.85], color="#0f172a", lw=1.8)
    th = np.linspace(0, np.pi, 40)
    ax.plot(1.25 + 0.10 * np.cos(th), 3.85 + 0.14 * np.sin(th), color="#0f172a", lw=1.8)
    ax.plot([1.15, 1.35], [3.25, 3.25], color="#0284c7", lw=2.0)
    ax.text(1.02, 3.68, r"$p_0 = 88.29\,\mathrm{kPa}$" + "\n（顶端封闭）", fontsize=8.8, ha="right", color="#0369a1")

    # Right open piezometer: x in [5.25, 5.45], water up to y=2.65 (x = 1.01m above 1.95)
    ax.add_patch(patches.Rectangle((3.1, 0.35), 0.20, 0.55, facecolor="#bae6fd", edgecolor="none"))
    ax.add_patch(patches.Rectangle((3.1, 0.35), 2.35, 0.18, facecolor="#bae6fd", edgecolor="none"))
    ax.add_patch(patches.Rectangle((5.25, 0.35), 0.20, 2.30, facecolor="#bae6fd", edgecolor="none"))
    ax.plot([3.1, 3.1, 5.45, 5.45], [0.90, 0.35, 0.35, 3.35], color="#0f172a", lw=1.8)
    ax.plot([3.3, 3.3, 5.25, 5.25], [0.90, 0.53, 0.53, 3.35], color="#0f172a", lw=1.8)
    ax.plot([5.25, 5.45], [2.65, 2.65], color="#0284c7", lw=2.0)
    ax.text(5.35, 3.45, r"$p_a = 98\,\mathrm{kPa}$" + "\n（敞口通大气）", fontsize=8.8, ha="center", color="#334155")

    # Equal-pressure plane 0-0 at y=1.95 (tank water surface)
    ax.plot([0.85, 5.85], [1.95, 1.95], color="#dc2626", lw=1.6, ls="--", zorder=6)
    ax.text(3.2, 1.66, "等压面（与容器水面齐平）", fontsize=8.8, ha="center", color="#b91c1c", fontweight="bold")

    # Dimensions h0=2m and x
    ax.annotate("", xy=(0.90, 3.25), xytext=(0.90, 1.95), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.3))
    ax.text(0.82, 2.60, r"$h_0 = 2\,\mathrm{m}$", fontsize=9.0, ha="right", va="center")

    ax.annotate("", xy=(5.72, 2.65), xytext=(5.72, 1.95), arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.5))
    ax.text(5.80, 2.30, r"$x = 1.01\,\mathrm{m}$" + "\n" + r"（$p_a=98\,\mathrm{kPa}$）", fontsize=8.8, ha="left", va="center", color="#b91c1c", fontweight="bold")

    ax.set_title("2012 年计算第 1 题：封闭容器双测压管等压面静水压强分析图", fontsize=11, pad=6)
    ax.set_xlim(0.0, 7.05)
    ax.set_ylim(0.10, 4.20)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2012_q24_sol(out_path: Path) -> None:
    """Cylinder (d=2m, L=4m) on 60-deg slope: true circle, virtual upward pressure body, P = 97.51 kN at 78.4 deg."""
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    fig.patch.set_facecolor("white")

    R = 1.0
    # Tangent point T to 60-deg slope is at -30 deg: (R cos30, -R sin30) = (0.866, -0.5)
    # Water surface meets left side at 150 deg: (-0.866, +0.5) -> water level y_w = +0.5
    th_wet = np.linspace(5 * np.pi / 6, 11 * np.pi / 6, 140)
    xW, yW = R * np.cos(5 * np.pi / 6), R * np.sin(5 * np.pi / 6)   # (-0.866, 0.5)
    xT, yT = R * np.cos(11 * np.pi / 6), R * np.sin(11 * np.pi / 6) # (+0.866, -0.5)

    # Virtual upward pressure body (lower semicircle + right triangle up to y_w = 0.5)
    poly_vp = [(xW, yW), (xT, yW), (xT, yT)] + [(R * np.cos(t), R * np.sin(t)) for t in th_wet[::-1]]
    ax.add_patch(patches.Polygon(poly_vp, closed=True, facecolor="#ffedd5", edgecolor="#ea580c", lw=1.3, hatch="///", alpha=0.80))

    # Cylinder true circle & diameter WT
    ax.add_patch(patches.Circle((0.0, 0.0), R, fill=False, edgecolor="#0f172a", lw=2.6, zorder=5))
    ax.plot([xW, xT], [yW, yT], color="#475569", lw=1.4, ls="--", zorder=5)
    ax.scatter([0.0], [0.0], color="#0f172a", s=30, zorder=6)

    # Water surface & 60-deg inclined wall + horizontal floor
    ax.plot([-2.15, xW], [yW, yW], color="#0284c7", lw=2.2)
    ax.plot([xW, xT], [yW, yW], color="#ea580c", lw=1.5, ls="--")
    # Line tangent to circle at T with angle 60 deg: slope tan(60) = sqrt(3)
    s_vals = np.array([-0.85, 1.35])
    ax.plot(xT + s_vals * np.cos(np.radians(60)), yT + s_vals * np.sin(np.radians(60)), color="#0f172a", lw=2.4)
    y_floor = yT - 0.85 * np.sin(np.radians(60))
    x_foot = xT - 0.85 * np.cos(np.radians(60))
    ax.plot([-2.15, 2.05], [y_floor, y_floor], color="#0f172a", lw=2.2)
    ax.text(x_foot + 0.34, y_floor + 0.14, r"$60^{\circ}$", fontsize=9.8, color="#334155")

    # Force arrows at center O
    ax.annotate("", xy=(0.65, 0.0), xytext=(-0.98, 0.0), arrowprops=dict(arrowstyle="->", color="#1d4ed8", lw=2.3), zorder=7)
    ax.text(-1.08, -0.02, r"$P_x = 19.60\,\mathrm{kN}$", fontsize=9.2, ha="right", va="center", color="#1e40af", fontweight="bold")

    ax.annotate("", xy=(0.0, 1.48), xytext=(0.0, 0.0), arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.3), zorder=7)
    ax.text(-0.08, 1.32, r"$P_z = 95.52\,\mathrm{kN}$（虚压力体 $\uparrow$）", fontsize=9.2, ha="right", color="#b91c1c", fontweight="bold")

    ang_p = np.radians(78.40)
    ax.annotate("", xy=(1.62 * np.cos(ang_p), 1.62 * np.sin(ang_p)), xytext=(0.0, 0.0),
                arrowprops=dict(arrowstyle="->", color="#15803d", lw=2.8), zorder=8)
    ax.text(1.62 * np.cos(ang_p) + 0.08, 1.62 * np.sin(ang_p) - 0.05,
            r"合力 $P = 97.51\,\mathrm{kN}$（$g=9.80$）" + "\n" + r"（$g=9.81$ 时 $97.61\,\mathrm{kN}$，仰角 $78.4^{\circ}$）",
            fontsize=9.1, ha="left", va="center", color="#166534", fontweight="bold")

    ax.text(-1.55, yW + 0.12, r"水面（$h = d\cos 60^{\circ} = 1\,\mathrm{m}$）", fontsize=9.0, ha="center", color="#0369a1")

    ax.set_title("2012 年计算第 2 题：斜坡上圆筒虚压力体与静水总压力合力图", fontsize=11, pad=6)
    ax.set_xlim(-2.35, 2.75)
    ax.set_ylim(-1.42, 1.85)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2012_q25_sol(out_path: Path) -> None:
    """90-deg elbow local loss measurement schematic showing A-B piezometer drop hw = (lam*L/d + zeta)*v^2/(2g)."""
    fig, ax = plt.subplots(figsize=(8.2, 4.1))
    fig.patch.set_facecolor("white")

    # Supply tank
    ax.add_patch(patches.Rectangle((0.3, 1.15), 1.5, 1.85, facecolor="#e0f2fe", edgecolor="none", alpha=0.8))
    ax.plot([0.3, 0.3, 1.8, 1.8], [3.2, 1.15, 1.15, 1.45], color="#0f172a", lw=2.0)
    ax.plot([1.8, 1.8], [1.67, 3.2], color="#0f172a", lw=2.0)
    ax.plot([0.3, 1.8], [3.0, 3.0], color="#0284c7", lw=2.0)
    ax.text(1.05, 2.25, "可调水位\n供水箱", fontsize=9.2, ha="center", color="#0369a1")

    # Horizontal pipe A -> 90-deg bend -> vertical pipe B -> valve -> measuring tank
    ax.add_patch(patches.Rectangle((1.8, 1.45), 3.6, 0.22, facecolor="#bae6fd", edgecolor="none"))
    ax.add_patch(patches.Rectangle((5.18, 0.55), 0.22, 1.12, facecolor="#bae6fd", edgecolor="none"))
    ax.plot([1.8, 5.40, 5.40], [1.67, 1.67, 0.55], color="#0f172a", lw=2.0)
    ax.plot([1.8, 5.18, 5.18], [1.45, 1.45, 0.55], color="#0f172a", lw=2.0)
    ax.text(2.45, 1.25, "$A$", fontsize=10, fontweight="bold")
    ax.text(4.92, 0.90, "$B$", fontsize=10, fontweight="bold")
    ax.text(5.38, 1.78, r"$90^{\circ}$ 弯管（$\zeta$）", fontsize=9.2, ha="right", color="#b91c1c", fontweight="bold")

    # Piezometers A (x=2.45, height=2.75) and B (x=6.15, height=2.05)
    ax.add_patch(patches.Rectangle((2.40, 1.67), 0.10, 1.08, facecolor="#38bdf8", alpha=0.8))
    ax.plot([2.40, 2.40], [1.67, 3.05], color="#334155", lw=1.3)
    ax.plot([2.50, 2.50], [1.67, 3.05], color="#334155", lw=1.3)

    ax.add_patch(patches.Rectangle((5.40, 0.85), 0.75, 0.10, facecolor="#38bdf8", alpha=0.8))
    ax.add_patch(patches.Rectangle((6.05, 0.85), 0.10, 1.20, facecolor="#38bdf8", alpha=0.8))
    ax.plot([5.40, 6.05, 6.05], [0.95, 0.95, 3.05], color="#334155", lw=1.3)
    ax.plot([5.40, 6.15, 6.15], [0.85, 0.85, 3.05], color="#334155", lw=1.3)

    # Head difference hw
    ax.plot([2.50, 4.70], [2.75, 2.75], color="#dc2626", lw=1.2, ls="--")
    ax.plot([3.60, 6.05], [2.05, 2.05], color="#dc2626", lw=1.2, ls="--")
    ax.annotate("", xy=(4.15, 2.75), xytext=(4.15, 2.05), arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.6))
    ax.text(4.25, 2.40, r"$h_w = \left(\lambda\frac{L}{d} + \zeta\right)\frac{v^2}{2g}$", fontsize=9.8, va="center", color="#b91c1c", fontweight="bold")

    # Measuring tank at bottom
    ax.add_patch(patches.Rectangle((4.75, 0.08), 1.15, 0.35, facecolor="#bae6fd", edgecolor="#0f172a", lw=1.6))
    ax.text(6.02, 0.25, r"量水箱测 $Q = V/t$", fontsize=9.0, ha="left", va="center", color="#0369a1")

    ax.text(3.2, 0.32, r"等径管 $v_A = v_B \Rightarrow h_w = (200\lambda + \zeta)\frac{v^2}{2g}$" + "\n"
            + r"实测均值 $200\lambda + \zeta = 6.321$（取 $\lambda = 0.03 \Rightarrow \zeta \approx 0.32$）",
            fontsize=8.9, ha="center", color="#1e3a8a",
            bbox=dict(boxstyle="round,pad=0.26", facecolor="#f8fafc", edgecolor="#93c5fd"))

    ax.set_title("2012 年计算第 3 题：90° 弯管局部水头损失系数实验测定能量关系图", fontsize=11, pad=6)
    ax.set_xlim(0.0, 7.65)
    ax.set_ylim(-0.05, 3.35)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2012_q26_sol(out_path: Path) -> None:
    """Free horizontal jet partially intercepted by frictionless vertical plate (CV momentum diagram)."""
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    fig.patch.set_facecolor("white")

    # Incoming jet 0-0: x in [0.4, 3.8], y in [1.45, 2.05]
    # Split: lower Q1 (1/3) goes down along plate x in [3.55, 3.80], y in [0.3, 1.65];
    # upper Q2 (2/3) deflects at 30 deg upward-right from (3.8, 1.65..2.05)!
    th = np.radians(30.0)
    dx, dy = 2.4 * np.cos(th), 2.4 * np.sin(th)
    nx, ny = -np.sin(th), np.cos(th)
    w2 = 0.40

    poly_jet = [
        (0.4, 2.05), (3.55, 2.05),
        (3.8 + dx + w2 * nx, 1.65 + dy + w2 * ny),
        (3.8 + dx, 1.65 + dy),
        (3.8, 1.65), (3.8, 0.30), (3.55, 0.30), (3.55, 1.45), (0.4, 1.45),
    ]
    ax.add_patch(patches.Polygon(poly_jet, closed=True, facecolor="#bae6fd", edgecolor="#0284c7", lw=1.6, alpha=0.82))

    # Frictionless vertical flat plate (hatched) at x in [3.80, 4.02], y in [0.30, 1.65]
    ax.add_patch(patches.Rectangle((3.80, 0.30), 0.22, 1.35, facecolor="#cbd5e1", edgecolor="#0f172a", lw=1.8, hatch="///", zorder=5))
    ax.text(4.15, 0.98, "光滑竖直平板\n" + r"（不计摩擦 $R_y = 0$）", fontsize=9.0, ha="left", va="center", color="#0f172a")

    # Dashed control volume boundary & angle theta
    ax.plot([1.4, 1.4], [1.25, 2.25], color="#1d4ed8", lw=1.6, ls="--")
    ax.plot([3.35, 4.05], [0.55, 0.55], color="#1d4ed8", lw=1.6, ls="--")
    ax.plot([3.8, 5.45], [1.65, 1.65], color="#475569", lw=1.2, ls="--")
    ax.add_patch(patches.Arc((3.8, 1.65), 1.4, 1.4, angle=0, theta1=0, theta2=30, color="#dc2626", lw=1.6))
    ax.text(4.62, 1.82, r"$\theta = 30^{\circ}$", fontsize=10.2, color="#b91c1c", fontweight="bold")

    # Velocity & force vectors
    ax.annotate("", xy=(2.2, 1.75), xytext=(0.7, 1.75), arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2.3))
    ax.text(1.45, 2.34, r"来流 $Q = 36\,\mathrm{L/s},\ v = 30\,\mathrm{m/s}$", fontsize=9.2, ha="center", color="#0369a1")

    ax.annotate("", xy=(3.675, 0.15), xytext=(3.675, 1.05), arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2.1))
    ax.text(3.25, 0.45, r"$Q_1 = 12\,\mathrm{L/s}$" + "\n" + r"$v_1 = v$", fontsize=9.0, ha="right", va="center", color="#0369a1")

    ax.annotate("", xy=(3.8 + 2.2 * np.cos(th) + 0.18 * nx, 1.65 + 2.2 * np.sin(th) + 0.18 * ny),
                xytext=(3.8 + 1.0 * np.cos(th) + 0.18 * nx, 1.65 + 1.0 * np.sin(th) + 0.18 * ny),
                arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2.3))
    ax.text(5.45, 3.38, r"偏转射流 $Q_2 = 24\,\mathrm{L/s},\ v_2 = v$", fontsize=9.2, ha="center", color="#0369a1")

    # Normal wall reaction Rx (leftward on fluid) & fluid force Fx (rightward on plate)
    ax.annotate("", xy=(2.75, 1.20), xytext=(3.78, 1.20), arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.4), zorder=7)
    ax.text(2.68, 1.20, r"平板反力 $R_x$（纯法向）", fontsize=9.2, ha="right", va="center", color="#b91c1c", fontweight="bold")

    ax.text(3.52, -0.26,
            r"$y$ 向无摩擦：$\rho Q_2 v \sin\theta - \rho Q_1 v = 0 \Rightarrow \sin\theta = \frac{12}{24} = 0.5 \Rightarrow \theta = 30^{\circ}$" + "\n"
            + r"$x$ 向推力校核：$F_x = \rho Q v - \rho Q_2 v \cos 30^{\circ} = 456.46\,\mathrm{N}$",
            fontsize=8.8, ha="center", va="center", color="#1e3a8a",
            bbox=dict(boxstyle="round,pad=0.28", facecolor="#f8fafc", edgecolor="#93c5fd"))

    ax.set_title("2012 年计算第 4 题：水平自由射流局部截流控制体动量分析图", fontsize=11, pad=6)
    ax.set_xlim(0.2, 6.85)
    ax.set_ylim(-0.68, 3.65)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


# ==============================================================================
# 2013 EXAM DATA (30 questions, totalScore = 150)
# ==============================================================================

def build_2013_paper() -> dict:
    return {
        "year": 2013,
        "code": "849",
        "subject": "水力学（水）",
        "school": "扬州大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": True,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "全卷共 30 道题：一、单项选择题（10×2=20 分）；二、填空题（10 题 20 空，每空 1 分，共 20 分）；三、简答题（5×8=40 分）；四、计算题（15×4 + 10×1 = 70 分）。",
            "除特别说明外，计算取重力加速度 g = 9.80 m/s²（同步附 g = 9.81 m/s² 对照值），水密度 ρ = 1000 kg/m³，水银密度 ρHg = 13600 kg/m³，当地大气压参考同卷工程大气压 pa = 98 kPa。"
        ],
        "sections": [
            {
                "id": "single_choice",
                "title": "一、单项选择题",
                "description": "本大题共 10 小题，每小题 2 分，共 20 分。",
                "range": [1, 10],
                "scorePerQuestion": 2,
                "totalScore": 20
            },
            {
                "id": "fill",
                "title": "二、填空题",
                "description": "本大题共 10 小题（每题 2 空），每空格 1 分，共 20 分。",
                "range": [11, 20],
                "scorePerQuestion": 2,
                "totalScore": 20
            },
            {
                "id": "short",
                "title": "三、简答题",
                "description": "本大题分 5 小题，每小题 8 分，共 40 分。",
                "range": [21, 25],
                "scorePerQuestion": 8,
                "totalScore": 40
            },
            {
                "id": "calc",
                "title": "四、计算题",
                "description": "本大题分 5 小题（15+15+15+15+10 分），共 70 分。",
                "range": [26, 30],
                "totalScore": 70
            }
        ],
        "questions": [
            {
                "id": "yzu-849-2013-01",
                "year": 2013,
                "no": 1,
                "type": "single_choice",
                "score": 2,
                "title": "导致液体运动机械能损失的主要物理性质",
                "stem": "对液体运动机械能损失起主要作用的物理性质是（　）",
                "options": [
                    {"label": "A", "text": "易流性"},
                    {"label": "B", "text": "压缩性"},
                    {"label": "C", "text": "粘滞性"},
                    {"label": "D", "text": "密度"}
                ],
                "choiceAnswer": "C",
                "note": "",
                "figures": [],
                "shortAnswer": "C",
                "judgeAnswer": None,
                "answer": "C. 粘滞性",
                "analysis": "实际液体在运动过程中，相邻液层发生相对剪切变形时会因粘滞性（黏性）产生内摩擦力（切应力），克服粘性阻力和由此诱发的漩涡掺混做功将机械能不可逆地转化为热能，这就是水头损失的根本物理根源。故正确答案为 C。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 1,
                "kps": ["牛顿内摩擦定律"],
                "method": "牛顿内摩擦快拖慢方向判别法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2013-02",
                "year": 2013,
                "no": 2,
                "type": "single_choice",
                "score": 2,
                "title": "单位质量力的量纲判别",
                "stem": "与单位质量力具有相同量纲的物理量是（　）",
                "options": [
                    {"label": "A", "text": "速度"},
                    {"label": "B", "text": "质量"},
                    {"label": "C", "text": "压强"},
                    {"label": "D", "text": "加速度"}
                ],
                "choiceAnswer": "D",
                "note": "",
                "figures": [],
                "shortAnswer": "D",
                "judgeAnswer": None,
                "answer": "D. 加速度",
                "analysis": "单位质量力定义为作用在单位质量流体上的质量力，即 $\\vec{f}=\\frac{\\mathrm{d}\\vec{F}_m}{\\mathrm{d}m}$。由牛顿第二定律，力除以质量即为加速度，其量纲为 $[\\mathrm{L}\\,\\mathrm{T}^{-2}]$（如重力场中单位质量力即为重力加速度 $g$）。故正确答案为 D。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 1,
                "kps": ["牛顿内摩擦定律"],
                "method": "牛顿内摩擦定律量纲导出法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2013-03",
                "year": 2013,
                "no": 3,
                "type": "single_choice",
                "score": 2,
                "title": "由绝对压强水柱高换算真空度",
                "stem": "液体中某点的绝对压强为 $4\\,\\mathrm{m}$ 水柱压（当地大气压为 $98\\,\\mathrm{kN/m^2}$），则该点的真空度为（　）",
                "options": [
                    {"label": "A", "text": "$4\\,\\mathrm{m}$ 水柱压"},
                    {"label": "B", "text": "$6\\,\\mathrm{m}$ 水柱压"},
                    {"label": "C", "text": "$-4\\,\\mathrm{m}$ 水柱压"},
                    {"label": "D", "text": "$-6\\,\\mathrm{m}$ 水柱压"}
                ],
                "choiceAnswer": "B",
                "note": "",
                "figures": [],
                "shortAnswer": "B",
                "judgeAnswer": None,
                "answer": "B. $6\\,\\mathrm{m}$ 水柱压",
                "analysis": "当地大气压水柱高度为：\n\n$$\nh_a = \\frac{p_a}{\\rho g} = \\frac{98\\,\\mathrm{kN/m^2}}{9.8\\,\\mathrm{kN/m^3}} = 10\\,\\mathrm{m}\\text{ 水柱压}\n$$\n\n真空度（真空高度）定义为当地大气压与绝对压强之差（恒为正值）：\n\n$$\nh_v = h_a - h_{\\text{绝}} = 10 - 4 = 6\\,\\mathrm{m}\\text{ 水柱压}\n$$\n\n故正确答案为 B。",
                "analysisFigures": [],
                "pitfalls": "相对压强为负值（$-6\\,\\mathrm{m}$ 水柱压），而真空度 $p_v = p_a - p_{\\text{绝}}$ 定义为正值（$6\\,\\mathrm{m}$ 水柱压），切忌误选 D。",
                "chapter": 2,
                "kps": ["多液层压差计"],
                "method": "压强零点平移消元验证法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2013-04",
                "year": 2013,
                "no": 4,
                "type": "single_choice",
                "score": 2,
                "title": "双层不混溶油桶双测压管液面高度判别",
                "stem": "如图所示一油桶，内装轻油和重油，密度分别为 $\\rho_1$ 和 $\\rho_2$（$\\rho_1 < \\rho_2$），桶侧两测压管内液面应为（　）",
                "options": [
                    {"label": "A", "text": "图 A（两测压管液面均高于桶内自由液面）"},
                    {"label": "B", "text": "图 B（上层测压管与桶内自由液面齐平，下层测压管高于分界面但低于桶内自由液面）"},
                    {"label": "C", "text": "图 C（上层测压管低于自由液面，下层测压管更低）"},
                    {"label": "D", "text": "图 D（两测压管液面齐平且高于桶内自由液面）"}
                ],
                "choiceAnswer": "B",
                "note": "",
                "figures": [
                    {"src": "figures/q04_orig.png", "caption": "题 4 图　双层油桶及两根测压管示意图"}
                ],
                "shortAnswer": "B",
                "judgeAnswer": None,
                "answer": "B",
                "analysis": "设上层轻油厚度为 $h_1$，下层重油测压管接入点在两油交界面以下深度 $h_2$ 处。\n\n1. 上层短测压管直接与轻油 $\\rho_1$ 连通，管内充满轻油 $\\rho_1$，由连通器等压面原理，其液面必与油桶内轻油自由液面严格齐平；\n\n2. 下层长测压管与重油 $\\rho_2$ 连通，管内上升的液体为重油 $\\rho_2$。在接入口水平面上列静水压强平衡：\n\n$$\n\\rho_1 g h_1 + \\rho_2 g h_2 = \\rho_2 g H_2 \\implies H_2 = h_2 + \\frac{\\rho_1}{\\rho_2} h_1\n$$\n\n因轻油密度小于重油密度（$0 < \\rho_1/\\rho_2 < 1$），故 $h_2 < H_2 < h_2 + h_1$，即长测压管液面高于两油交界面，但低于油桶内自由液面。对照四图，只有图 B 正确。",
                "analysisFigures": [],
                "pitfalls": "容易误以为静止连通液体中所有测压管液面均与自由液面齐平；实际上只有当管内液体与桶内上方全层液体为同一种均质液体时才齐平，重油折算的轻油等效液柱高度更矮。",
                "chapter": 2,
                "kps": ["多液层压差计"],
                "method": "等压面静水压强递推法",
                "difficulty": 2
            },
            {
                "id": "yzu-849-2013-05",
                "year": 2013,
                "no": 5,
                "type": "single_choice",
                "score": 2,
                "title": "双侧不同水深半圆柱面 MN 的铅垂压力体图判别",
                "stem": "如图所示半圆曲面 $MN$，左侧水深为 $h$，右侧水深为 $h/2$，则 $MN$ 曲面上的净铅垂压力体图为（　）",
                "options": [
                    {"label": "A", "text": "图 A（完整半圆，方向向上）"},
                    {"label": "B", "text": "图 B（上半圆向上、下半圆向下）"},
                    {"label": "C", "text": "图 C（上方 1/4 圆，方向向上）"},
                    {"label": "D", "text": "图 D（下方 1/4 圆，方向向下）"}
                ],
                "choiceAnswer": "C",
                "note": "",
                "figures": [
                    {"src": "figures/q05_orig.png", "caption": "题 5 图　双侧挡水半圆曲面 MN 及压力体选项"}
                ],
                "shortAnswer": "C",
                "judgeAnswer": None,
                "answer": "C",
                "analysis": "采用左右两侧水体叠加原理（设半径 $R = h/2$，见解图 5）：\n\n1. 左侧水体（水深 $h = 2R$，位于凸半圆外侧）：上半圆弧受向下实压力体，下半圆弧受向上虚压力体，两者相抵后的净铅垂压力体为半径 $R$ 的完整半圆（面积 $\\frac{1}{2}\\pi R^2$，方向向上）；\n\n2. 右侧水体（水深 $h/2 = R$，位于凹半圆内侧下半部）：仅作用于下半 $1/4$ 圆弧，其正上方实体水柱恰为下半 $1/4$ 圆（面积 $\\frac{1}{4}\\pi R^2$，方向向下）；\n\n3. 左右叠加：右侧向下的下半 $1/4$ 圆实压力体与左侧向上的下半 $1/4$ 圆虚压力体完全抵消，最终剩余上方 $1/4$ 圆的净压力体（方向向上），与图 C 完全一致。",
                "analysisFigures": [
                    {"src": "figures/q05_sol.png", "caption": "解图 5　半圆曲面 MN 左右两侧压力体叠加抵消示意图"}
                ],
                "pitfalls": "切忌漏掉右侧水深 $h/2$ 产生的向下实压力体而错选 A。",
                "chapter": 2,
                "kps": ["平面与曲面静水总压力"],
                "method": "水平投影与铅垂压力体分块合成法",
                "difficulty": 3
            },
            {
                "id": "yzu-849-2013-06",
                "year": 2013,
                "no": 6,
                "type": "single_choice",
                "score": 2,
                "title": "表征某瞬时水流运动方向的曲线定义",
                "stem": "表征某瞬时水流运动方向的曲线为（　）",
                "options": [
                    {"label": "A", "text": "迹线"},
                    {"label": "B", "text": "流线"},
                    {"label": "C", "text": "总水头线"},
                    {"label": "D", "text": "测管水头线"}
                ],
                "choiceAnswer": "B",
                "note": "",
                "figures": [],
                "shortAnswer": "B",
                "judgeAnswer": None,
                "answer": "B. 流线",
                "analysis": "流线是欧拉法中某一瞬时在流场内绘出的光滑曲线，曲线上每一点的切线方向都与该瞬时该点流体质点的速度矢量方向一致；而迹线是拉格朗日法中同一流体质点在不同时刻运动所经过的空间轨迹。故正确答案为 B。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 3,
                "kps": ["伯努利方程测流"],
                "method": "平衡微分方程与流线法向方程条件对比法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2013-07",
                "year": 2013,
                "no": 7,
                "type": "single_choice",
                "score": 2,
                "title": "天然河道降水洪水的流动类型判别",
                "stem": "天然河道中，因降水引发的洪水，水流属于（　）",
                "options": [
                    {"label": "A", "text": "非恒定流"},
                    {"label": "B", "text": "恒定流"},
                    {"label": "C", "text": "均匀流"},
                    {"label": "D", "text": "有压流"}
                ],
                "choiceAnswer": "A",
                "note": "",
                "figures": [],
                "shortAnswer": "A",
                "judgeAnswer": None,
                "answer": "A. 非恒定流",
                "analysis": "降水引发的洪水演进过程中，河道各断面的水位、流量和流速均随时间发生显著的涨落变化（$\\partial/\\partial t \\neq 0$），且天然河道具有自由水面、断面不规则，故属于无压非恒定非均匀流。故正确答案为 A。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 3,
                "kps": ["明渠均匀流特点"],
                "method": "明渠均匀流特征与形成条件判别法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2013-08",
                "year": 2013,
                "no": 8,
                "type": "single_choice",
                "score": 2,
                "title": "实际液体流动方向的总水头判据",
                "stem": "液体流动规律总是（　）",
                "options": [
                    {"label": "A", "text": "从高处流向低处"},
                    {"label": "B", "text": "从压强大处流向压强小处"},
                    {"label": "C", "text": "从流速大处流向流速小处"},
                    {"label": "D", "text": "从单位机械能大处流向单位机械能小处"}
                ],
                "choiceAnswer": "D",
                "note": "",
                "figures": [],
                "shortAnswer": "D",
                "judgeAnswer": None,
                "answer": "D. 从单位机械能大处流向单位机械能小处",
                "analysis": "实际液体流动必然伴随能量耗散（水头损失 $h_w > 0$），由恒定总流能量方程 $E_1 = E_2 + h_w \\implies E_1 > E_2$，水流总是从单位重量液体总机械能（总水头）大处流向单位机械能小处，而非单由位置高程、压强或流速单独决定。故正确答案为 D。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 3,
                "kps": ["伯努利方程测流"],
                "method": "总水头大小判别流向与恒定总流能量方程",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2013-09",
                "year": 2013,
                "no": 9,
                "type": "single_choice",
                "score": 2,
                "title": "圆管水流下临界雷诺数取值",
                "stem": "圆管水流的下临界雷诺数约为（　）",
                "options": [
                    {"label": "A", "text": "200"},
                    {"label": "B", "text": "2000"},
                    {"label": "C", "text": "4000"},
                    {"label": "D", "text": "10000"}
                ],
                "choiceAnswer": "B",
                "note": "",
                "figures": [],
                "shortAnswer": "B",
                "judgeAnswer": None,
                "answer": "B. 2000",
                "analysis": "圆管满流由紊流转变为层流的下临界雷诺数比较稳定，工程水力学中通常取 $Re_k \\approx 2000$（或 $2320$）；四个选项中最符合的为 2000。故正确答案为 B。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 4,
                "kps": ["沿程与局部损失"],
                "method": "水力半径与当量直径雷诺数流态判别法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2013-10",
                "year": 2013,
                "no": 10,
                "type": "single_choice",
                "score": 2,
                "title": "明渠均匀流三线关系与运动特征辨析",
                "stem": "关于明渠均匀流，不正确的说法是（　）",
                "options": [
                    {"label": "A", "text": "总水头线与自由水面线重合"},
                    {"label": "B", "text": "过水断面上的流速分布沿程不变"},
                    {"label": "C", "text": "测压管水头线与底坡线平行"},
                    {"label": "D", "text": "等速、等深流"}
                ],
                "choiceAnswer": "A",
                "note": "",
                "figures": [],
                "shortAnswer": "A",
                "judgeAnswer": None,
                "answer": "A. 总水头线与自由水面线重合",
                "analysis": "明渠恒定均匀流的核心特征是过水断面形状尺寸、水深 $h$、断面平均流速 $v$ 及断面流速分布均沿程不变（等深、等速流，B、D 正确）。自由水面即测压管水头线，总水头线位于自由水面上方 $\\frac{\\alpha v^2}{2g}$ 处，三线（总水头线、测压管水头线/自由水面线、渠底坡线）互相平行（$J = J_p = i$，C 正确）。因此总水头线与自由水面线平行而不重合，A 说法不正确。故正确答案为 A。",
                "analysisFigures": [],
                "pitfalls": "与自由水面线重合的是测压管水头线，而不是总水头线（总水头线高出自由水面一个流速水头 $\\frac{\\alpha v^2}{2g}$）。",
                "chapter": 7,
                "kps": ["明渠均匀流特点"],
                "method": "明渠均匀流特征与形成条件判别法",
                "difficulty": 2
            },
            {
                "id": "yzu-849-2013-11",
                "year": 2013,
                "no": 11,
                "type": "fill",
                "subType": "blank",
                "score": 2,
                "title": "液体粘滞性随温度变化规律与运动粘滞系数量纲",
                "stem": "同一种液体，粘滞性随温度降低而________。液体运动粘滞系数的量纲为________。",
                "note": "",
                "figures": [],
                "shortAnswer": "增大；L²T⁻¹",
                "judgeAnswer": None,
                "answer": "增大；$\\mathrm{L^2 T^{-1}}$",
                "analysis": "液体粘滞性主要源于分子间内聚力，温度降低时分子热运动减弱、分子间吸引力增强，故液体粘滞性增大（与气体相反）。运动粘滞系数 $\\nu = \\mu / \\rho$ 的国际单位为 $\\mathrm{m^2/s}$，对应基本量纲为 $\\mathrm{L^2 T^{-1}}$。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 1,
                "kps": ["牛顿内摩擦定律"],
                "method": "牛顿内摩擦定律量纲导出法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2013-12",
                "year": 2013,
                "no": 12,
                "type": "fill",
                "subType": "mini-calc",
                "score": 2,
                "title": "工程大气压与压强及水柱高度换算",
                "stem": "$0.5$ 个工程大气压相当于________ $\\mathrm{kN/m^2}$，相当于________ $\\mathrm{m}$ 水柱高度。",
                "note": "",
                "figures": [],
                "shortAnswer": "49；5",
                "judgeAnswer": None,
                "answer": "$49$；$5$",
                "analysis": "水力学中 $1$ 个工程大气压（$1\\,\\mathrm{at} = 1\\,\\mathrm{kgf/cm^2}$）约为 $98\\,\\mathrm{kN/m^2}$，对应 $10\\,\\mathrm{m}$ 水柱高度。因此 $0.5$ 个工程大气压相当于 $0.5 \\times 98 = 49\\,\\mathrm{kN/m^2}$，相当于 $0.5 \\times 10 = 5\\,\\mathrm{m}$ 水柱高度。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 2,
                "kps": ["多液层压差计"],
                "method": "压强零点平移消元验证法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2013-13",
                "year": 2013,
                "no": 13,
                "type": "fill",
                "subType": "blank",
                "score": 2,
                "title": "测压管水头各项的物理名称",
                "stem": "测压管水头 $z + \\frac{p}{\\rho g}$ 中，$z$ 称为________水头，$\\frac{p}{\\rho g}$ 称为________水头。",
                "note": "",
                "figures": [],
                "shortAnswer": "位置；压强",
                "judgeAnswer": None,
                "answer": "位置；压强",
                "analysis": "在单位重量液体势能（测压管水头）$z + \\frac{p}{\\rho g}$ 中，$z$ 表示单位重量液体相对基准面的位能，称为位置水头；$\\frac{p}{\\rho g}$ 表示单位重量液体的压能，称为压强水头。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 2,
                "kps": ["多液层压差计"],
                "method": "压强零点平移消元验证法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2013-14",
                "year": 2013,
                "no": 14,
                "type": "fill",
                "subType": "blank",
                "score": 2,
                "title": "液体出现真空的绝对压强与相对压强判据",
                "stem": "当液体中某点的绝对压强小于________压强时，即其________压强为负值时，该点存在真空。",
                "note": "",
                "figures": [],
                "shortAnswer": "当地大气；相对",
                "judgeAnswer": None,
                "answer": "当地大气；相对",
                "analysis": "相对压强定义为绝对压强减去当地大气压强：$p = p_{\\text{绝}} - p_a$。当某点 $p_{\\text{绝}} < p_a$ 时，其相对压强 $p < 0$（负压），该点存在真空。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 2,
                "kps": ["多液层压差计"],
                "method": "压强零点平移消元验证法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2013-15",
                "year": 2013,
                "no": 15,
                "type": "fill",
                "subType": "blank",
                "score": 2,
                "title": "描述液体运动的拉格朗日法与欧拉法",
                "stem": "描述液体运动的方法有________法和________法两种。",
                "note": "",
                "figures": [],
                "shortAnswer": "拉格朗日；欧拉",
                "judgeAnswer": None,
                "answer": "拉格朗日；欧拉",
                "analysis": "流体运动学有两种基本描述方法：跟踪单个流体质点运动全过程的拉格朗日（Lagrange）法，以及研究空间固定点上各运动要素随时间分布规律的欧拉（Euler）法。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 5,
                "kps": ["流函数与势函数"],
                "method": "欧拉速度场复合函数全求导法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2013-16",
                "year": 2013,
                "no": 16,
                "type": "fill",
                "subType": "blank",
                "score": 2,
                "title": "水力坡度定义与理想液体水力坡度值",
                "stem": "水力坡度是指单位流动长度上的________。对于理想液体，水力坡度 $J =$ ________。",
                "note": "",
                "figures": [],
                "shortAnswer": "水头损失；0",
                "judgeAnswer": None,
                "answer": "水头损失（或总水头降落值）；$0$",
                "analysis": "水力坡度定义为单位流程长度上的水头损失（即总水头线沿程下降的坡度）：$J = -\\frac{\\mathrm{d}H}{\\mathrm{d}s} = \\frac{h_f}{l}$。理想液体无粘性、无能量损失（$h_f = 0$），故 $J = 0$。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 3,
                "kps": ["沿程与局部损失"],
                "method": "总水头大小判别流向与恒定总流能量方程",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2013-17",
                "year": 2013,
                "no": 17,
                "type": "fill",
                "subType": "blank",
                "score": 2,
                "title": "雷诺试验揭示的两种水流流态",
                "stem": "雷诺通过试验揭示了水流具有________与________两种不同的型态。",
                "note": "",
                "figures": [],
                "shortAnswer": "层流；紊流",
                "judgeAnswer": None,
                "answer": "层流；紊流",
                "analysis": "1883 年英国物理学家雷诺通过圆管示踪色线流动试验，清晰揭示了粘性流体运动存在层流（质点互不混掺、分层有序）与紊流（质点剧烈脉动混掺）两种截然不同的流态。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 4,
                "kps": ["沿程与局部损失"],
                "method": "水力半径与当量直径雷诺数流态判别法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2013-18",
                "year": 2013,
                "no": 18,
                "type": "fill",
                "subType": "blank",
                "score": 2,
                "title": "尼古拉兹试验研究对象与层流沿程损失流速幂次",
                "stem": "尼古拉兹试验研究的是________的变化规律，其研究表明，层流时沿程水头损失与断面平均流速的________次方成正比。",
                "note": "",
                "figures": [],
                "shortAnswer": "沿程水头损失系数 λ；一（1）",
                "judgeAnswer": None,
                "answer": "沿程水头损失系数 $\\lambda$（随 $Re$ 及相对粗糙度 $\\Delta/d$）；一（或 $1$）",
                "analysis": "尼古拉兹人工加糙圆管试验系统测定了沿程阻力系数 $\\lambda$ 随雷诺数 $Re$ 和相对粗糙度 $\\Delta/d$ 的五区变化规律。在层流区 $\\lambda = 64/Re \\propto v^{-1}$，代入达西公式 $h_f = \\lambda\\frac{l}{d}\\frac{v^2}{2g}$ 得 $h_f \\propto v^1$，即与断面平均流速的一次方成正比。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 4,
                "kps": ["沿程与局部损失"],
                "method": "达西公式与莫迪图五区分类对比法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2013-19",
                "year": 2013,
                "no": 19,
                "type": "fill",
                "subType": "blank",
                "score": 2,
                "title": "雷诺数增大时紊流三个阻力分区的演变顺序",
                "stem": "当管道尺寸及粗糙度一定时，随着流量（雷诺数）的不断加大，液流流区变化为紊流光滑区、________区和________区。",
                "note": "",
                "figures": [],
                "shortAnswer": "紊流过渡粗糙；紊流粗糙",
                "judgeAnswer": None,
                "answer": "紊流过渡粗糙（或过渡）；紊流粗糙（或阻力平方）",
                "analysis": "管道直径 $d$ 与绝对粗糙度 $\\Delta$ 固定时，随流量增大，雷诺数 $Re$ 不断增大，粘滞底层厚度 $\\delta$ 逐渐变薄，粗糙凸起依次由完全淹没变为部分露出再变为完全暴露，流区相应依次经历紊流光滑区、紊流过渡粗糙区和紊流粗糙区（阻力平方区）。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 4,
                "kps": ["沿程与局部损失"],
                "method": "达西公式与莫迪图五区分类对比法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2013-20",
                "year": 2013,
                "no": 20,
                "type": "fill",
                "subType": "blank",
                "score": 2,
                "title": "明渠底坡定义与均匀流形成的底坡条件",
                "stem": "明渠底坡 $i$ 和渠底线与水平线夹角 $\\theta$ 的关系为________。只有在________坡明渠中才有可能形成均匀流。",
                "note": "",
                "figures": [],
                "shortAnswer": "i = sin θ；顺（正）",
                "judgeAnswer": None,
                "answer": "$i = \\sin\\theta$；顺（或正）",
                "analysis": "明渠底坡定义为沿渠底单位流程长度渠底高程的降落值，即 $i = -\\frac{\\mathrm{d}z}{\\mathrm{d}s} = \\sin\\theta$。明渠均匀流要求重力沿渠底的分力与水流阻力相平衡（$i = J > 0$），故只有在底坡大于零的顺坡（正坡）棱柱形明渠中才有可能形成均匀流。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 7,
                "kps": ["明渠均匀流特点"],
                "method": "明渠均匀流特征与形成条件判别法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2013-21",
                "year": 2013,
                "no": 21,
                "type": "short",
                "score": 8,
                "title": "静水压强方向垂直指向受压面的力学证明",
                "stem": "为什么静水压强的方向只能是垂直指向受压面？",
                "note": "",
                "figures": [],
                "shortAnswer": "反证法：静止液体不能承受切应力（否则会发生剪切流动破坏静止状态），故应力切向分力必为零；又液体几乎不能承受拉力，故法向应力必为压应力并垂直指向受压面内部。",
                "judgeAnswer": None,
                "answer": "采用反证法从静止流体的物理力学性质证明：\n\n1. 证明静水压强必垂直于受压面（无切向分力）：\n假设作用于受压微元面上的静水压强 $\\vec{p}$ 不垂直于受压面，则可将其正交分解为垂直于受压面的法向分力 $p_n$ 和平行于受压面的切向分力 $p_\\tau$（切应力）。根据液体易流性，静止液体在任何微小的切应力作用下都会发生连续不断的剪切变形与相对流动，这与液体处于静止状态的前提相矛盾！因此必然有 $p_\\tau = 0$，静水压强只能垂直于受压面。\n\n2. 证明静水压强必指向受压面内部（为压应力而非拉应力）：\n假设法向分力 $p_n$ 背离受压面，即液体对受压面施加拉力。由于液体分子间抗拉能力极微弱、工程上不能承受拉力，一旦受拉液柱将拉断分离，同样无法维持连续静止状态。因此法向分力只能为压力，即垂直指向受压面（沿受压面内法线方向）。",
                "analysis": "本题是水静力学最基础的定理证明题，答题必须严格分成两层：（1）证“垂直”（用静止液体 $\\tau = 0$ 反证）；（2）证“指向受压面”（用液体不能受拉反证），缺一不可。",
                "analysisFigures": [],
                "pitfalls": "切忌只写“静止液体切应力为零所以垂直”，而漏掉证明“指向受压面内部（不能承受拉力）”导致被扣去一半分数。",
                "chapter": 2,
                "kps": ["平面与曲面静水总压力"],
                "method": "平衡微分方程与流线法向方程条件对比法",
                "difficulty": 2,
                "rubric": [
                    {"label": "假设静水压强存在切向分力 pτ，利用静止液体不能承受切应力（否则发生流动）反证 pτ = 0，得出方向必垂直于受压面", "pts": 4},
                    {"label": "利用液体不能承受拉力的特性反证法向分力不能背离受压面，得出方向必垂直指向受压面内部", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2013-22",
                "year": 2013,
                "no": 22,
                "type": "short",
                "score": 8,
                "title": "复式油—水银压差计各水平面等压面判别",
                "stem": "如图所示的复式压差计，试问：$A\\text{-}A$、$B\\text{-}B$、$C\\text{-}C$、$D\\text{-}D$、$C\\text{-}E$ 中哪个是等压面，哪个不是等压面？为什么？",
                "note": "",
                "figures": [
                    {"src": "figures/q22_orig.png", "caption": "题 22 图　复式水—油—水银压差计示意图"}
                ],
                "shortAnswer": "B-B 和 C-E 是等压面；A-A、C-C、D-D 不是等压面。判据：仅受重力作用的静止流体中，必须同时满足“水平面 + 同一种均质液体 + 互相连续连通”三个条件才是等压面。",
                "judgeAnswer": None,
                "answer": "在仅受重力作用的静止液体中，等压面必须同时满足三个条件：① 水平面；② 同一种均质液体；③ 液体互相连续连通。逐一判别五个水平面：\n\n1. $B\\text{-}B$ 面：是等压面。左侧 U 形管内 $B\\text{-}B$ 两点均处于同一种静止水银中，且下方由连续水银连通，满足等压面全部条件。\n\n2. $C\\text{-}E$ 面：是等压面。右侧 U 形管内 $C$ 点（油—水银分界面）与 $E$ 点均处于同一种静止水银中，且下方由连续水银连通，满足等压面全部条件。\n\n3. $A\\text{-}A$ 面：不是等压面。左侧管 $A$ 点位于水中，中间管 $A$ 点位于油—水银分界面处，在等压面 $B\\text{-}B$ 上方两管内分别为水和水银，不是同一种连续介质（$p_{A,\\text{左}} \\neq p_{A,\\text{右}}$）。\n\n4. $C\\text{-}C$ 面：不是等压面。虽然左 $C$ 与右 $C$ 均接触水银，但两管水银并不连续（被上方倒 U 形管中的油隔断）；在油的顶部等压面以下至 $C\\text{-}C$ 之间，左管有一段水银而右管全为油，故 $p_{C,\\text{左}} \\neq p_{C,\\text{右}}$。\n\n5. $D\\text{-}D$ 面：不是等压面。左 $D$ 位于油中，右 $D$ 位于水—水银交界面，在等压面 $C\\text{-}E$ 上方两管分别为油和水银，不是同一种连续介质。",
                "analysis": "判别复式压差计等压面时，务必核对“连续性”条件：$C\\text{-}C$ 虽然两端都在水银里，但中间被油隔断，属于“同种介质但不连续”，这是本题最具迷惑性的考点。",
                "analysisFigures": [],
                "pitfalls": "切忌因 $C\\text{-}C$ 两端都是水银就误判为等压面！两段水银分别位于左右两个独立的 U 形管中，中间被轻油隔开，并不连续连通。",
                "chapter": 2,
                "kps": ["多液层压差计"],
                "method": "等压面静水压强递推法",
                "difficulty": 2,
                "rubric": [
                    {"label": "明确写出仅受重力静止液体等压面的三要素：水平面、同一种均质液体、连续连通", "pts": 2},
                    {"label": "正确判定 B-B 与 C-E 为等压面并说明理由（分别由各自 U 形管内连续水银连通）", "pts": 3},
                    {"label": "正确判定 A-A、D-D（非同种介质）与 C-C（同种介质但不连续）均不是等压面并说明理由", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2013-23",
                "year": 2013,
                "no": 23,
                "type": "short",
                "score": 8,
                "title": "矩形明渠水流越过底坎三种水面形态的伯努利能量判别",
                "stem": "试简要证明图中所示具有底坎（高 $a$）的矩形断面渠道中的三种水流（a）、（b）、（c）是否可能发生。",
                "note": "",
                "figures": [
                    {"src": "figures/q23_orig.png", "caption": "题 23 图　具有底坎的矩形断面明渠三种水流示意图"}
                ],
                "shortAnswer": "（a）不可能；（b）不可能；（c）可能发生（当势能水面跌落 H - h 足以抵偿流速水头增量与水头损失之和时）。",
                "judgeAnswer": None,
                "answer": "取上游渠底为基准面（$z_1 = 0$，坎顶渠底高程 $z_2 = a$），设矩形渠宽为 $b$，在底坎上游渐变流断面 $1\\text{-}1$（水深 $h_1 = H + a$，水面高程 $Z_1 = H + a$）与坎顶断面 $2\\text{-}2$ 之间列恒定总流能量方程（$\\alpha_1 = \\alpha_2 = \\alpha$）：\n\n$$\nZ_1 + \\frac{\\alpha v_1^2}{2g} = Z_2 + \\frac{\\alpha v_2^2}{2g} + h_w \\implies h_w = (Z_1 - Z_2) + \\frac{\\alpha(v_1^2 - v_2^2)}{2g}\n$$\n\n真实水流从上游流向下游必须满足 $h_w \\ge 0$（对实际液体 $h_w > 0$）：\n\n1. 图（a）：坎顶水深 $h_2 = H$，水面高程 $Z_2 = a + H = Z_1$（势能不变）；由连续性方程 $Q = b(H+a)v_1 = bHv_2$，因过水面积缩小（$H+a > H$），必有 $v_2 > v_1$，动能水头增大。代入能量方程得：\n\n$$\nh_w = 0 + \\frac{\\alpha(v_1^2 - v_2^2)}{2g} < 0\n$$\n\n违背能量守恒定律（总机械能沿程凭空增加），故图（a）不可能发生。\n\n2. 图（b）：坎顶水深 $h_2 = H + a$，水面高程 $Z_2 = a + (H + a) = H + 2a > Z_1$（势能沿程增大 $a$）；同时 $A_2 = b(H+a) = A_1 \\implies v_2 = v_1$（动能不变）。代入能量方程得：\n\n$$\nh_w = (Z_1 - Z_2) + 0 = -a < 0\n$$\n\n总机械能沿程增加 $a$，故图（b）不可能发生。\n\n3. 图（c）：坎顶水深 $h_2 = h < H$，水面高程 $Z_2 = a + h < a + H = Z_1$（势能沿程减小 $H - h > 0$）；虽因面积减小使 $v_2 > v_1$（动能增大），但只要势能减小量能够补偿动能增加量与水头损失之和，即：\n\n$$\nH - h = \\frac{\\alpha(v_2^2 - v_1^2)}{2g} + h_w > 0\n$$\n\n则满足 $h_w > 0$（总水头沿程降低，这正是缓流过底坎时断面比能减小导致水面跌落的典型现象），故图（c）可能发生。",
                "analysis": "本题将恒定总流能量方程与连续性方程有机结合：先通过断面尺寸判断 $v_1$ 与 $v_2$ 的大小关系，再比较水面高程 $Z_1$ 与 $Z_2$，用 $h_w \\ge 0$ 一票否决违背能量守恒的流态。",
                "analysisFigures": [],
                "pitfalls": "注意基准面选取务必统一！题图上游水深总量为 $H + a$，坎顶底面已抬高 $a$，故图（b）坎顶水面高程为 $H + 2a$ 而非 $H + a$。",
                "chapter": 8,
                "kps": ["断面比能与临界水深", "伯努利方程测流"],
                "method": "伯努利方程位能动能损失三项对比判别法",
                "difficulty": 2,
                "rubric": [
                    {"label": "选定统一基准面正确写出 1-1 与 2-2 断面的恒定总流能量方程及连续性方程", "pts": 2},
                    {"label": "证明图（a）势能不变而动能增加（hw < 0），不可能发生", "pts": 2},
                    {"label": "证明图（b）动能不变而势能增加 a（hw = -a < 0），不可能发生", "pts": 2},
                    {"label": "证明图（c）水面跌落 H - h > 0 可补偿动能增量与水头损失，可能发生", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2013-24",
                "year": 2013,
                "no": 24,
                "type": "short",
                "score": 8,
                "title": "向两张薄纸间吹气靠拢现象的伯努利方程解释",
                "stem": "试用能量方程式解释现象：向两张靠得很近的薄纸吹气，两张纸不是彼此分开，而是彼此靠拢。",
                "note": "",
                "figures": [],
                "shortAnswer": "吹气时两纸间空气流速 v 增大，由水平伯努利方程 p/(ρg) + v²/(2g) = const 知纸间动压强 p 低于纸外侧静止大气压 pa，内外压差将两张纸向中间压拢。",
                "judgeAnswer": None,
                "answer": "在低速不可压缩空气流动中，忽略两纸间微小高度差与沿程能量损失，沿水平气流列理想流体恒定元流能量方程（伯努利方程）：\n\n$$\n\\frac{p}{\\rho g} + \\frac{v^2}{2g} = \\mathrm{const}\n$$\n\n1. 向两张薄纸中间吹气时，纸间狭缝处的空气流速 $v$ 显著增大，动能 $\\frac{v^2}{2g}$ 增大；\n\n2. 由伯努利方程可知，流束内动能增大必然伴随压能减小，故两纸内侧气流的动压强 $p$ 降低，小于当地大气压强 $p_a$（形成局部负压）；\n\n3. 与此同时，两张纸外侧的空气处于静止状态（$v_{\\text{外}} \\approx 0$），压强仍维持为当地大气压强 $p_a$。外侧大气压大于内侧气流压强（$p_a > p$），形成指向纸间中线的净压力差，因而把两张薄纸彼此压拢。",
                "analysis": "本题为经典的伯努利方程压能—动能转化应用，清晰写出方程并对比“内侧高速低压”与“外侧静止常压”即可得满分。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 3,
                "kps": ["伯努利方程测流"],
                "method": "伯努利方程动能压能转化分析法",
                "difficulty": 1,
                "rubric": [
                    {"label": "正确写出忽略高差与损失的水平伯努利方程 p/(ρg) + v²/(2g) = const", "pts": 3},
                    {"label": "说明吹气使两纸间空气流速增大、动压强降低至小于大气压 pa", "pts": 3},
                    {"label": "指出外侧静止空气保持大气压 pa > p，内外压差将两张薄纸向中间压拢", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2013-25",
                "year": 2013,
                "no": 25,
                "type": "short",
                "score": 8,
                "title": "水平等径管阀门关闭与开启时管轴两点压强大小分析",
                "stem": "如图所示，某水箱外接一等直径的水平输水管道，当阀门处于关闭和开启状态时，试分析管轴线上 $A$、$B$ 两点压强的相对大小。",
                "note": "",
                "figures": [
                    {"src": "figures/q25_orig.png", "caption": "题 25 图　水箱外接等径管道阀门关闭与开启状态"}
                ],
                "shortAnswer": "（a）阀门关闭时：水体静止，A、B 位于同一水平等压面上，pA = pB；（b）阀门开启时：等径恒定流 vA = vB、zA = zB，因存在沿程水头损失 hf,AB > 0，由能量方程得 pA > pB。",
                "judgeAnswer": None,
                "answer": "以水平管道中心轴线为基准面，则 $z_A = z_B = 0$。\n\n1. 阀门关闭状态（图 a）：\n管道内水体处于静止状态，且与水箱内水体连续连通。因 $A$、$B$ 两点位于同一连续静止水体的同一水平面上（即同一等压面），由水静力学基本方程得：\n\n$$\np_A = p_B = \\rho g H\n$$\n\n（其中 $H$ 为水箱水面至管轴线的淹深）。\n\n2. 阀门开启状态（图 b）：\n管道内形成恒定有压出流。因管道等直径，由连续性方程 $v_A A_A = v_B A_B$ 知 $v_A = v_B$，流速水头相等（$\\frac{\\alpha v_A^2}{2g} = \\frac{\\alpha v_B^2}{2g}$）。对 $A$、$B$ 两断面列恒定总流能量方程：\n\n$$\nz_A + \\frac{p_A}{\\rho g} + \\frac{\\alpha v_A^2}{2g} = z_B + \\frac{p_B}{\\rho g} + \\frac{\\alpha v_B^2}{2g} + h_{f,A\\text{-}B}\n$$\n\n消去相等的位置水头与流速水头后得：\n\n$$\n\\frac{p_A - p_B}{\\rho g} = h_{f,A\\text{-}B} > 0 \\implies p_A > p_B\n$$\n\n即由于水流由 $A$ 流向 $B$ 存在沿程水头损失，动水压强沿程降低，故 $p_A > p_B$。",
                "analysis": "对比静水（等压面 $p_A = p_B$）与动水（水平等径管沿程摩阻消耗压能 $p_A > p_B$），本质上考查水静力学与伯努利方程的衔接。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 3,
                "kps": ["伯努利方程测流", "沿程与局部损失"],
                "method": "启闭阀门静动水压差伯努利测速法",
                "difficulty": 1,
                "rubric": [
                    {"label": "阀门关闭时：由同种连续静止水体水平等压面条件得出 pA = pB", "pts": 3},
                    {"label": "阀门开启时：写出等径管连续性条件 vA = vB 及水平条件 zA = zB", "pts": 2},
                    {"label": "列出 A、B 断面恒定总流能量方程，因沿程水头损失 hf > 0 证得 pA > pB", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2013-26",
                "year": 2013,
                "no": 26,
                "type": "calc",
                "score": 15,
                "title": "密闭容器液面压强与 U 形水银测压计液面差计算",
                "stem": "图示为一密闭容器，两侧各装一测压管，右管上端封闭，其中水面高出容器水面 $3\\,\\mathrm{m}$，管内液面气体压强 $p_0$ 为 $78\\,\\mathrm{kPa}$（绝对压强）；左管为 U 形水银测压计，一端与容器连接，另一端与大气相通，其中水银面较低的一侧液面低于容器液面 $3\\,\\mathrm{m}$。\n\n求：（1）容器内液面压强 $p_c$；（2）左侧 U 形水银测压管内水银液面差 $\\Delta h$。",
                "note": "题干未单独标明当地大气压 $p_a$，参照同卷第 3 题取工程大气压 $p_a = 98\\,\\mathrm{kPa}$ 计算主解，同时提供标准大气压 $101.325\\,\\mathrm{kPa}$ 与 $100\\,\\mathrm{kPa}$ 对照结果。",
                "figures": [
                    {"src": "figures/q26_orig.png", "caption": "题 26 图　密闭容器与两侧测压管装置图"}
                ],
                "shortAnswer": "（1）pc = 107.40 kPa（绝压，g=9.80；g=9.81 为 107.43 kPa）；（2）Δh = 0.291 m（pa = 98 kPa；pa = 101.325 kPa 时为 0.266 m）",
                "judgeAnswer": None,
                "answer": "（1）容器内液面绝对压强 $p_c = 107.40\\,\\mathrm{kPa}$（取 $g = 9.81\\,\\mathrm{m/s^2}$ 时为 $107.43\\,\\mathrm{kPa}$；若按 $p_a = 98\\,\\mathrm{kPa}$ 折算为相对压强，则 $p_{c,\\text{相}} = 9.40\\,\\mathrm{kPa}$）；\n\n（2）左侧 U 形水银测压计液面差 $\\Delta h \\approx 0.291\\,\\mathrm{m}$（按同卷 $p_a = 98\\,\\mathrm{kPa}$；若按 $p_a = 100\\,\\mathrm{kPa}$ 得 $0.276\\,\\mathrm{m}$，按标准大气压 $p_a = 101.325\\,\\mathrm{kPa}$ 得 $0.266\\,\\mathrm{m}$）。",
                "analysis": "（1）求容器内液面绝对压强 $p_c$\n\n右侧封闭测压管内的水与容器内的水连续连通。取与容器水面齐平的水平面作为等压面（见解图 26），右侧测压管水面高出该水平面 $h_{\\text{右}} = 3\\,\\mathrm{m}$，由水静力学基本方程（全用绝对压强）：\n\n$$\np_c = p_0 + \\rho g h_{\\text{右}}\n$$\n\n取 $\\rho = 1000\\,\\mathrm{kg/m^3}$、$g = 9.80\\,\\mathrm{m/s^2}$：\n\n$$\np_c = 78\\times 10^3 + 1000\\times 9.80\\times 3 = 107400\\,\\mathrm{Pa} = 107.40\\,\\mathrm{kPa}\n$$\n\n（若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $p_c = 78 + 9.81\\times 3 = 107.43\\,\\mathrm{kPa}$。）\n\n（2）求左侧 U 形水银测压计液面差 $\\Delta h$\n\n取左侧 U 形水银测压计较低一侧（右支）的水银—水交界面作为等压面 $1\\text{-}1$（低于容器水面 $h_{\\text{左}} = 3\\,\\mathrm{m}$），左右两支在水银中连续连通，列绝对压强平衡方程：\n\n$$\np_c + \\rho g h_{\\text{左}} = p_a + \\rho_{\\text{Hg}} g \\Delta h\n$$\n\n解得：\n\n$$\n\\Delta h = \\frac{p_c + \\rho g h_{\\text{左}} - p_a}{\\rho_{\\text{Hg}} g}\n$$\n\n参照本卷第 3 题取当地工程大气压 $p_a = 98\\,\\mathrm{kPa}$、$\\rho_{\\text{Hg}} = 13600\\,\\mathrm{kg/m^3}$：\n\n- 当 $g = 9.80\\,\\mathrm{m/s^2}$ 时：\n\n$$\n\\Delta h = \\frac{107400 + 1000\\times 9.80\\times 3 - 98000}{13600\\times 9.80} = \\frac{38800}{133280} \\approx 0.291\\,\\mathrm{m}\n$$\n\n- 对照值：取 $g = 9.81\\,\\mathrm{m/s^2}$ 且 $p_a = 98\\,\\mathrm{kPa}$ 时 $\\Delta h = 0.2913\\,\\mathrm{m}$；若取 $p_a = 100\\,\\mathrm{kPa}$ 时 $\\Delta h \\approx 0.276\\,\\mathrm{m}$；若取标准大气压 $p_a = 101.325\\,\\mathrm{kPa}$ 时 $\\Delta h \\approx 0.266\\,\\mathrm{m}$。",
                "analysisFigures": [
                    {"src": "figures/q26_sol.png", "caption": "解图 26　密闭容器与 U 形水银测压计等压面静水压强平衡图"}
                ],
                "pitfalls": "本题核心易错点是“绝对压强与相对压强混用”：题目给出的 $p_0 = 78\\,\\mathrm{kPa}$ 是绝对压强，因而求出的 $p_c = 107.40\\,\\mathrm{kPa}$ 也是绝对压强，在左侧 U 形管列平衡时敞口端必须对应代入绝对大气压 $p_a$（而非 $0$）！",
                "chapter": 2,
                "kps": ["多液层压差计"],
                "method": "等压面静水压强递推法",
                "difficulty": 2,
                "rubric": [
                    {"label": "取容器水面为等压面列静水压强方程 pc = p0 + ρgh右，准确求得绝对压强 pc = 107.40 kPa（g=9.81 为 107.43 kPa）", "pts": 6},
                    {"label": "选左侧 U 形管较低水银面为等压面，统一用绝对压强列方程 pc + ρgh左 = pa + ρHg·g·Δh", "pts": 5},
                    {"label": "代入数值准确求得水银液面差 Δh ≈ 0.291 m（或按标准大气压 101.325 kPa 得 0.266 m）", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2013-27",
                "year": 2013,
                "no": 27,
                "type": "calc",
                "score": 15,
                "title": "1/4 圆弧形闸门 AB 静水总压力大小、方向与作用点计算",
                "stem": "求图中圆弧形闸门 $AB$ 所受静水总压力的大小、方向及作用点。已知水深 $H = 4\\,\\mathrm{m}$，闸门宽 $b = 2\\,\\mathrm{m}$。",
                "note": "",
                "figures": [
                    {"src": "figures/q27_orig.png", "caption": "题 27 图　1/4 圆弧形闸门 AB 示意图"}
                ],
                "shortAnswer": "P = 170.63 kN（g=9.80；g=9.81 为 170.81 kN），方向指向右下方、与水平面夹角 θ = 23.23°，作用线过圆心 O，与圆弧交点 D 位于水面下深度 hD = 2.42 m 处。",
                "judgeAnswer": None,
                "answer": "静水总压力大小 $P = 170.63\\,\\mathrm{kN}$（取 $g = 9.81\\,\\mathrm{m/s^2}$ 时为 $170.81\\,\\mathrm{kN}$）；方向指向右下方，与水平面夹角 $\\theta = 23.23^{\\circ}$；作用线通过圆弧圆心 $O$（右下直角点），与圆弧面的交点 $D$（压心）位于自由水面以下深度 $h_D = 2.42\\,\\mathrm{m}$ 处（距渠底高 $y_D = 1.58\\,\\mathrm{m}$）。",
                "analysis": "由题图直角标志知，$AB$ 为半径 $R = H = 4\\,\\mathrm{m}$ 的 $1/4$ 圆弧面，圆心 $O$ 位于右下角，水体在圆弧面 $AB$ 的左上方（见解图 27）。\n\n1. 求水平分力 $P_x$（水平向右）\n\n圆弧面 $AB$ 在铅垂面上的投影为高 $H = 4\\,\\mathrm{m}$、宽 $b = 2\\,\\mathrm{m}$ 的矩形，形心淹深 $h_c = H/2 = 2\\,\\mathrm{m}$，取 $g = 9.80\\,\\mathrm{m/s^2}$：\n\n$$\nP_x = \\rho g h_c A_x = 1000\\times 9.80\\times 2\\times (4\\times 2) = 156800\\,\\mathrm{N} = 156.80\\,\\mathrm{kN}\n$$\n\n（取 $g = 9.81\\,\\mathrm{m/s^2}$ 时 $P_x = 156.96\\,\\mathrm{kN}$。）\n\n2. 求铅垂分力 $P_z$（竖直向下）\n\n水体位于圆弧 $AB$ 正上方，实压力体断面为边长 $R = 4\\,\\mathrm{m}$ 的正方形扣除 $1/4$ 圆面积：\n\n$$\nV_z = \\left(R^2 - \\frac{1}{4}\\pi R^2\\right)b = \\left(4^2 - \\frac{\\pi}{4}\\times 4^2\\right)\\times 2 = (16 - 4\\pi)\\times 2 \\approx 6.8673\\,\\mathrm{m^3}\n$$\n\n$$\nP_z = \\rho g V_z = 1000\\times 9.80\\times 6.8673 = 67299\\,\\mathrm{N} \\approx 67.30\\,\\mathrm{kN}\n$$\n\n（取 $g = 9.81\\,\\mathrm{m/s^2}$ 时 $P_z = 67.37\\,\\mathrm{kN}$。）\n\n3. 合成总压力的大小、方向与作用点\n\n$$\nP = \\sqrt{P_x^2 + P_z^2} = \\sqrt{156.80^2 + 67.30^2} \\approx 170.63\\,\\mathrm{kN}\n$$\n\n（取 $g = 9.81\\,\\mathrm{m/s^2}$ 时 $P = 170.81\\,\\mathrm{kN}$。）\n\n合力方向指向右下方，与水平面夹角为：\n\n$$\n\\theta = \\arctan\\frac{P_z}{P_x} = \\arctan\\frac{67.30}{156.80} \\approx 23.23^{\\circ}\n$$\n\n因圆弧面上每一点的静水微元压力均垂直于圆弧面而指向圆心 $O$，故合力作用线必通过圆心 $O$。作用线与圆弧 $AB$ 的交点 $D$（压力作用点）位于自圆心 $O$ 向左上方仰角 $23.23^{\\circ}$ 处，其距渠底高度与距水面（$A$ 点）淹深分别为：\n\n$$\ny_D = R\\sin\\theta = 4\\sin 23.23^{\\circ} \\approx 1.58\\,\\mathrm{m}, \\qquad h_D = H - y_D = 4 - 1.58 = 2.42\\,\\mathrm{m}\n$$",
                "analysisFigures": [
                    {"src": "figures/q27_sol.png", "caption": "解图 27　1/4 圆弧形闸门实压力体、合力方向与压心 D 位置图"}
                ],
                "pitfalls": "圆弧曲面作用点不能用平面闸门的 $h_D = \\frac{2}{3}H$ 公式直接套算！应先利用“微元法向压力共点于圆心 $O$”确定合力过圆心，再由倾角 $\\theta$ 几何求出与圆弧的交点坐标 $h_D = R(1 - \\sin\\theta) = 2.42\\,\\mathrm{m}$。",
                "chapter": 2,
                "kps": ["平面与曲面静水总压力"],
                "method": "水平投影与铅垂压力体分块合成法",
                "difficulty": 3,
                "rubric": [
                    {"label": "计算铅垂投影面积与水平分力 Px = 156.80 kN（g=9.81 为 156.96 kN，方向向右）", "pts": 4},
                    {"label": "正确识别圆弧上方实压力体 Vz = (R² - πR²/4)b，求得铅垂分力 Pz = 67.30 kN（向下）", "pts": 5},
                    {"label": "合成总压力 P = 170.63 kN、求得倾角 θ = 23.23°（右下方）", "pts": 3},
                    {"label": "指明作用线过圆心 O，并求得与圆弧交点 D 淹深 hD = R(1 - sinθ) = 2.42 m", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2013-28",
                "year": 2013,
                "no": 28,
                "type": "calc",
                "score": 15,
                "title": "淹没出流虹吸管吸水流量与坝顶最大允许安装高度校核",
                "stem": "如图所示虹吸管总长 $l = 21\\,\\mathrm{m}$，坝顶 $A$ 点前管长 $\\Delta l = 8\\,\\mathrm{m}$，管内径 $d = 0.25\\,\\mathrm{m}$，坝顶管道中心与上游水面的高度差 $h_1 = 3.5\\,\\mathrm{m}$，二水面落差 $h_2 = 4\\,\\mathrm{m}$。设虹吸管沿程阻力系数 $\\lambda = 0.03$，进口局部阻力系数 $\\zeta_1 = 0.8$，出口局部阻力系数 $\\zeta_2 = 1$，三个 $45^{\\circ}$ 折管的局部阻力系数均为 $0.3$，试求虹吸管的吸水流量 $Q$。若当地大气压强 $p_a = 10^5\\,\\mathrm{Pa}$，水温 $t = 20\\,^{\\circ}\\mathrm{C}$，所对应的水的密度 $\\rho = 998\\,\\mathrm{kg/m^3}$，水的饱和压强 $p_s = 2.42\\times 10^3\\,\\mathrm{Pa}$，试判断虹吸管的安装高度是否满足要求。",
                "note": "",
                "figures": [
                    {"src": "figures/q28_orig.png", "caption": "题 28 图　越坝虹吸管布置与高程示意图"}
                ],
                "shortAnswer": "Q = 0.190 m³/s；坝顶允许安装高度 [h1] = 7.63 m > 3.5 m（或 A 点实际绝对压强 42.84 kPa >> ps = 2.42 kPa），安装高度满足要求。",
                "judgeAnswer": None,
                "answer": "（1）虹吸管吸水流量 $Q = 0.190\\,\\mathrm{m^3/s}$（断面平均流速 $v \\approx 3.88\\,\\mathrm{m/s}$）；\n\n（2）坝顶 $A$ 点最大允许安装高度 $[h_1] = 7.63\\,\\mathrm{m} > h_1 = 3.5\\,\\mathrm{m}$（对应 $A$ 点实际绝对压强 $p_A = 42.84\\,\\mathrm{kPa} \\gg p_s = 2.42\\,\\mathrm{kPa}$），故该虹吸管的安装高度满足不汽化要求。",
                "analysis": "1. 列上下游水池自由水面能量方程求流量 $Q$\n\n以下游水池自由水面为基准面，对上游水面 $1\\text{-}1$ 和下游水面 $2\\text{-}2$ 列恒定总流能量方程（两水面流速可忽略，$p_1 = p_2 = p_a$；出口为淹没出流，$\\zeta_2 = 1.0$ 已代表出口动能全部耗散的局部损失）：\n\n$$\nh_2 = \\left(\\lambda\\frac{l}{d} + \\zeta_1 + 3\\zeta_3 + \\zeta_2\\right)\\frac{v^2}{2g}\n$$\n\n计算总阻力系数：\n\n$$\n\\sum\\zeta = 0.03\\times\\frac{21}{0.25} + 0.8 + 3\\times 0.3 + 1.0 = 2.52 + 0.8 + 0.9 + 1.0 = 5.22\n$$\n\n取 $g = 9.80\\,\\mathrm{m/s^2}$，解得管内平均流速与流量：\n\n$$\nv = \\sqrt{\\frac{2g h_2}{5.22}} = \\sqrt{\\frac{2\\times 9.80\\times 4.0}{5.22}} = 3.876\\,\\mathrm{m/s} \\approx 3.88\\,\\mathrm{m/s}\n$$\n\n$$\nQ = \\frac{\\pi}{4}d^2 v = \\frac{\\pi}{4}\\times 0.25^2\\times 3.876 \\approx 0.190\\,\\mathrm{m^3/s}\n$$\n\n（取 $g = 9.81\\,\\mathrm{m/s^2}$ 时 $v = 3.877\\,\\mathrm{m/s}$，$Q = 0.190\\,\\mathrm{m^3/s}$。）\n\n2. 校核坝顶最险断面 $A$ 的安装高度\n\n以上游自由水面为基准面，对上游水面与坝顶下游侧最高点 $A$（前段管长 $\\Delta l = 8\\,\\mathrm{m}$，含进口 $\\zeta_1 = 0.8$ 及上游侧第 1 个 $45^{\\circ}$ 折管 $\\zeta_3 = 0.3$，见解图 28）列绝对压强形式的能量方程（$\\alpha = 1$）：\n\n$$\n\\frac{p_a}{\\rho g} = h_1 + \\frac{p_A}{\\rho g} + \\left(1 + \\lambda\\frac{\\Delta l}{d} + \\zeta_1 + \\zeta_3\\right)\\frac{v^2}{2g}\n$$\n\n其中 $A$ 点前局部及流速水头总系数为：\n\n$$\nK_A = 1 + 0.03\\times\\frac{8}{0.25} + 0.8 + 0.3 = 1 + 0.96 + 0.8 + 0.3 = 3.06\n$$\n\n流速水头 $\\frac{v^2}{2g} = \\frac{4.0}{5.22} = 0.7663\\,\\mathrm{m}$。为防止水流汽化断流，须满足 $p_A \\ge p_s = 2.42\\times 10^3\\,\\mathrm{Pa}$，由此求得最大允许安装高度 $[h_1]$：\n\n$$\n[h_1] = \\frac{p_a - p_s}{\\rho g} - K_A\\frac{v^2}{2g} = \\frac{10^5 - 2420}{998\\times 9.80} - 3.06\\times 0.7663 = 9.977 - 2.345 = 7.632\\,\\mathrm{m} \\approx 7.63\\,\\mathrm{m}\n$$\n\n（若将 $A$ 点处的第 2 个 $45^{\\circ}$ 折管也计入 $A$ 前损失，则 $K_A = 3.36$，$[h_1] = 7.40\\,\\mathrm{m}$；若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $[h_1] = 7.62\\,\\mathrm{m}$。）\n\n因实际安装高度 $h_1 = 3.5\\,\\mathrm{m} < [h_1] = 7.63\\,\\mathrm{m}$（对应 $A$ 点实际绝对压强 $p_A = 42.84\\,\\mathrm{kPa} \\gg p_s = 2.42\\,\\mathrm{kPa}$），故该虹吸管的安装高度完全满足要求。",
                "analysisFigures": [
                    {"src": "figures/q28_sol.png", "caption": "解图 28　虹吸管总水头线、测压管水头线与坝顶 A 断面真空校核图"}
                ],
                "pitfalls": "1. 淹没出流已给定出口局部阻力系数 $\\zeta_2 = 1.0$，在总水头差方程中切忌再额外多加一个流速水头项 $1$；\n2. 校核 $A$ 断面真空度时，必须保留 $A$ 断面自身的流速水头 $\\frac{v^2}{2g}$（系数中的 $1$），并且只能计入 $A$ 断面之前（$\\Delta l = 8\\,\\mathrm{m}$）的沿程与局部水头损失。",
                "chapter": 6,
                "kps": ["水泵最大允许安装高程", "水泵扬程与轴功率"],
                "method": "允许真空度定安装高程+长管扬程求功率",
                "difficulty": 3,
                "rubric": [
                    {"label": "列上下游自由水面能量方程，正确计入沿程、进口、3 个折管与淹没出口损失系数 Σζ = 5.22", "pts": 4},
                    {"label": "解得管内流速 v ≈ 3.88 m/s 及吸水流量 Q ≈ 0.190 m³/s", "pts": 4},
                    {"label": "列上游水面至坝顶 A 断面能量方程（计入 Δl = 8 m、ζ1、ζ3 及流速水头，KA = 3.06）", "pts": 4},
                    {"label": "代入 ρ = 998 kg/m³、pa = 10⁵ Pa、ps = 2.42 kPa 算得 [h1] ≈ 7.63 m > 3.5 m，判定满足要求", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2013-29",
                "year": 2013,
                "no": 29,
                "type": "calc",
                "score": 15,
                "title": "并联分汊矩形河道均匀流近似水位高程与流量分配计算",
                "stem": "如图所示有近似为矩形断面的分汊河道，已知：长度 $l_1 = 6000\\,\\mathrm{m}$，$l_2 = 2500\\,\\mathrm{m}$，宽度 $b_1 = 80\\,\\mathrm{m}$，$b_2 = 150\\,\\mathrm{m}$，水深 $h_1 = 2.2\\,\\mathrm{m}$，$h_2 = 4\\,\\mathrm{m}$，河床的粗糙系数 $n = 0.03$，当总流量 $Q = 400\\,\\mathrm{m^3/s}$ 时，$1\\text{-}1$ 断面处的水面高程为 $\\nabla_1 = 120.00\\,\\mathrm{m}$，试近似地按均匀流计算：\n\n（1）$2\\text{-}2$ 断面的水面高程 $\\nabla_2$；\n\n（2）流量分配 $Q_1$ 及 $Q_2$。",
                "note": "",
                "figures": [
                    {"src": "figures/q29_orig.png", "caption": "题 29 图　矩形断面分汊河道平面布置图"}
                ],
                "shortAnswer": "（1）∇2 = 119.87 m（落差 ΔZ = 0.133 m）；（2）Q1 = 45.07 m³/s，Q2 = 354.93 m³/s。",
                "judgeAnswer": None,
                "answer": "（1）$2\\text{-}2$ 断面的水面高程 $\\nabla_2 = 119.87\\,\\mathrm{m}$（准确值 $119.867\\,\\mathrm{m}$）；\n\n（2）两汊道流量分配分别为 $Q_1 = 45.07\\,\\mathrm{m^3/s}$，$Q_2 = 354.93\\,\\mathrm{m^3/s}$。",
                "analysis": "1. 计算两分汊河道的水力要素与流量模数 $K$\n\n对矩形断面河道，应用曼宁公式 $Q_k = K_k\\sqrt{i_k}$，其中流量模数 $K_k = \\frac{1}{n}A_k R_k^{2/3}$：\n\n- 上汊（河段 1）：\n\n$$\nA_1 = b_1 h_1 = 80\\times 2.2 = 176.0\\,\\mathrm{m^2}, \\qquad \\chi_1 = b_1 + 2h_1 = 80 + 4.4 = 84.4\\,\\mathrm{m}\n$$\n\n$$\nR_1 = \\frac{A_1}{\\chi_1} = \\frac{176.0}{84.4} = 2.0853\\,\\mathrm{m}, \\qquad K_1 = \\frac{1}{0.03}\\times 176.0\\times (2.0853)^{2/3} = 9575.7\\,\\mathrm{m^3/s}\n$$\n\n- 主汊（河段 2）：\n\n$$\nA_2 = b_2 h_2 = 150\\times 4.0 = 600.0\\,\\mathrm{m^2}, \\qquad \\chi_2 = b_2 + 2h_2 = 150 + 8.0 = 158.0\\,\\mathrm{m}\n$$\n\n$$\nR_2 = \\frac{A_2}{\\chi_2} = \\frac{600.0}{158.0} = 3.7975\\,\\mathrm{m}, \\qquad K_2 = \\frac{1}{0.03}\\times 600.0\\times (3.7975)^{2/3} = 48681.0\\,\\mathrm{m^3/s}\n$$\n\n2. 利用并联河道共用落差求 $2\\text{-}2$ 断面水面高程 $\\nabla_2$\n\n设 $1\\text{-}1$ 至 $2\\text{-}2$ 两断面之间的共用落差为 $\\Delta Z = \\nabla_1 - \\nabla_2$，则两汊道的水力坡度分别为 $i_1 = \\frac{\\Delta Z}{l_1}$、$i_2 = \\frac{\\Delta Z}{l_2}$。由分流连续性方程 $Q = Q_1 + Q_2$：\n\n$$\nQ = \\left(\\frac{K_1}{\\sqrt{l_1}} + \\frac{K_2}{\\sqrt{l_2}}\\right)\\sqrt{\\Delta Z}\n$$\n\n计算各项系数：\n\n$$\n\\frac{K_1}{\\sqrt{l_1}} = \\frac{9575.7}{\\sqrt{6000}} = 123.62\\,\\mathrm{m^{2.5}/s}, \\qquad \\frac{K_2}{\\sqrt{l_2}} = \\frac{48681.0}{\\sqrt{2500}} = 973.62\\,\\mathrm{m^{2.5}/s}\n$$\n\n代入总流量 $Q = 400\\,\\mathrm{m^3/s}$：\n\n$$\n(123.62 + 973.62)\\sqrt{\\Delta Z} = 1097.24\\sqrt{\\Delta Z} = 400 \\implies \\sqrt{\\Delta Z} = 0.36455\\,\\mathrm{m^{1/2}}\n$$\n\n$$\n\\Delta Z = 0.36455^2 = 0.1329\\,\\mathrm{m} \\approx 0.13\\,\\mathrm{m}\n$$\n\n故 $2\\text{-}2$ 断面水面高程为：\n\n$$\n\\nabla_2 = \\nabla_1 - \\Delta Z = 120.00 - 0.1329 = 119.867\\,\\mathrm{m} \\approx 119.87\\,\\mathrm{m}\n$$\n\n3. 求两汊道分配流量 $Q_1$、$Q_2$\n\n$$\nQ_1 = 123.62\\times 0.36455 = 45.07\\,\\mathrm{m^3/s}, \\qquad Q_2 = 973.62\\times 0.36455 = 354.93\\,\\mathrm{m^3/s}\n$$\n\n校核：$Q_1 + Q_2 = 45.07 + 354.93 = 400.00\\,\\mathrm{m^3/s}$，与总流量严格吻合。",
                "analysisFigures": [
                    {"src": "figures/q29_sol.png", "caption": "解图 29　分汊矩形河道共用落差与流量分配计算示意图"}
                ],
                "pitfalls": "两分汊河道长度不同，故水力坡度 $i_1 \\neq i_2$，相等的是两节点间的水位总落差 $\\Delta Z = i_1 l_1 = i_2 l_2$！",
                "chapter": 7,
                "kps": ["曼宁公式", "分叉管改装流量变化分析"],
                "method": "明渠均匀流曼宁公式求底坡与高程法",
                "difficulty": 3,
                "rubric": [
                    {"label": "准确计算两分汊河道过水面积、湿周、水力半径及流量模数 K1 ≈ 9575.7 m³/s、K2 ≈ 48681.0 m³/s", "pts": 5},
                    {"label": "由共用落差 ΔZ = i1·l1 = i2·l2 与 Q = Q1 + Q2 联立解得 ΔZ ≈ 0.133 m 及 ∇2 ≈ 119.87 m", "pts": 6},
                    {"label": "代回求得两汊道分配流量 Q1 ≈ 45.07 m³/s、Q2 ≈ 354.93 m³/s 并检验总和为 400 m³/s", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2013-30",
                "year": 2013,
                "no": 30,
                "type": "calc",
                "score": 10,
                "title": "由二维不可压缩势流速度势函数求解流函数",
                "stem": "已知不可压缩流体平面流动的速度势为 $\\varphi = x^2 - y^2 + x$，求流函数 $\\psi$。",
                "note": "",
                "figures": [],
                "shortAnswer": "ψ = 2xy + y + C（按 u = +∇φ；若按 u = -∇φ 约定则为 ψ = -2xy - y + C）。",
                "judgeAnswer": None,
                "answer": "流函数表达式为 $\\psi = 2xy + y + C$（按正梯度约定 $\\vec{u} = +\\nabla\\varphi$；若按负梯度约定 $\\vec{u} = -\\nabla\\varphi$ 则为 $\\psi = -2xy - y + C$，其中 $C$ 为任意常数）。",
                "analysis": "1. 检验拉普拉斯方程（不可压缩连续性条件）\n\n按正梯度定义 $u_x = \\frac{\\partial\\varphi}{\\partial x}$、$u_y = \\frac{\\partial\\varphi}{\\partial y}$，由 $\\varphi = x^2 - y^2 + x$ 求得速度分量：\n\n$$\nu_x = \\frac{\\partial\\varphi}{\\partial x} = 2x + 1, \\qquad u_y = \\frac{\\partial\\varphi}{\\partial y} = -2y\n$$\n\n检验连续性方程：\n\n$$\n\\frac{\\partial u_x}{\\partial x} + \\frac{\\partial u_y}{\\partial y} = 2 + (-2) = 0\n$$\n\n满足平面不可压缩流动条件，故必存在流函数 $\\psi$。\n\n2. 利用柯西—黎曼关系积分求解流函数 $\\psi$\n\n由流函数定义 $u_x = \\frac{\\partial\\psi}{\\partial y}$、$u_y = -\\frac{\\partial\\psi}{\\partial x}$，其全微分为：\n\n$$\n\\mathrm{d}\\psi = \\frac{\\partial\\psi}{\\partial x}\\mathrm{d}x + \\frac{\\partial\\psi}{\\partial y}\\mathrm{d}y = -u_y\\,\\mathrm{d}x + u_x\\,\\mathrm{d}y = 2y\\,\\mathrm{d}x + (2x + 1)\\,\\mathrm{d}y = \\mathrm{d}(2xy + y)\n$$\n\n两边积分即得：\n\n$$\n\\psi = 2xy + y + C\n$$\n\n（其中 $C$ 为积分常数。若采用负梯度定义 $u_x = -\\frac{\\partial\\varphi}{\\partial x} = -(2x+1)$、$u_y = -\\frac{\\partial\\varphi}{\\partial y} = 2y$，则同理求得 $\\psi = -2xy - y + C$。）",
                "analysisFigures": [],
                "pitfalls": "切忌忘记写积分常数 $+ C$，也注意核对全微分公式 $\\mathrm{d}\\psi = -u_y\\,\\mathrm{d}x + u_x\\,\\mathrm{d}y$ 中 $-u_y$ 的负号，防止把 $+2xy$ 误积成 $-2xy$。",
                "chapter": 5,
                "kps": ["流函数与势函数"],
                "method": "流函数拉普拉斯无旋判据与柯西—黎曼积分法",
                "difficulty": 2,
                "rubric": [
                    {"label": "由速度势函数求偏导得出速度分量 ux = 2x + 1、uy = -2y 并检验满足连续性方程", "pts": 4},
                    {"label": "写出流函数全微分关系 dψ = -uy dx + ux dy = 2y dx + (2x + 1) dy", "pts": 3},
                    {"label": "准确积分得出 ψ = 2xy + y + C（保留积分常数 C，或负梯度约定反号）", "pts": 3}
                ]
            }
        ]
    }


# ==============================================================================
# 2012 EXAM DATA (27 questions, totalScore = 150)
# ==============================================================================

def build_2012_paper() -> dict:
    return {
        "year": 2012,
        "code": "849",
        "subject": "水力学（水）",
        "school": "扬州大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": True,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "全卷共 27 道题：一、单项选择题（10×2=20 分）；二、填空题（8×3=24 分）；三、简答题（4×6=24 分）；四、计算题（15+15+16+18+18 = 82 分）。",
            "除特别说明外，计算取重力加速度 g = 9.80 m/s²（同步附 g = 9.81 m/s² 对照值），水密度 ρ = 1000 kg/m³，当地大气压参照同卷取 pa = 98 kPa。"
        ],
        "sections": [
            {
                "id": "single_choice",
                "title": "一、单项选择题",
                "description": "每小题 2 分，共 20 分。",
                "range": [1, 10],
                "scorePerQuestion": 2,
                "totalScore": 20
            },
            {
                "id": "fill",
                "title": "二、填空题",
                "description": "每空 3 分，共 24 分。",
                "range": [11, 18],
                "scorePerQuestion": 3,
                "totalScore": 24
            },
            {
                "id": "short",
                "title": "三、简答题",
                "description": "每小题 6 分，共 24 分。",
                "range": [19, 22],
                "scorePerQuestion": 6,
                "totalScore": 24
            },
            {
                "id": "calc",
                "title": "四、计算题",
                "description": "共 5 小题（15+15+16+18+18 分），共 82 分。",
                "range": [23, 27],
                "totalScore": 82
            }
        ],
        "questions": [
            {
                "id": "yzu-849-2012-01",
                "year": 2012,
                "no": 1,
                "type": "single_choice",
                "score": 2,
                "title": "按长管计的并联管道各支管水头损失关系",
                "stem": "按长管计的并联管道，各支管的（　）",
                "options": [
                    {"label": "A", "text": "流量相等"},
                    {"label": "B", "text": "切应力相等"},
                    {"label": "C", "text": "水力坡度相等"},
                    {"label": "D", "text": "沿程水头损失相等"}
                ],
                "choiceAnswer": "D",
                "note": "",
                "figures": [],
                "shortAnswer": "D",
                "judgeAnswer": None,
                "answer": "D. 沿程水头损失相等",
                "analysis": "并联管道各支管共用同一上游分流节点和同一下游汇流节点，两节点间总水头差相等；按长管计算时忽略局部水头损失与流速水头，故各支管的沿程水头损失必然相等（$h_{f1} = h_{f2} = \\cdots = H_A - H_B$）。因各支管长度不一定相同，故水力坡度 $J_i = h_{fi}/l_i$ 不一定相等。故正确答案为 D。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 6,
                "kps": ["分叉管改装流量变化分析"],
                "method": "长管并联分流与节点水头平衡分析",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2012-02",
                "year": 2012,
                "no": 2,
                "type": "single_choice",
                "score": 2,
                "title": "明渠均匀流形成的底坡条件",
                "stem": "在下列底坡渠道中，有可能产生明渠均匀流的底坡为（　）",
                "options": [
                    {"label": "A", "text": "平坡"},
                    {"label": "B", "text": "顺坡"},
                    {"label": "C", "text": "逆坡"},
                    {"label": "D", "text": "边坡"}
                ],
                "choiceAnswer": "B",
                "note": "",
                "figures": [],
                "shortAnswer": "B",
                "judgeAnswer": None,
                "answer": "B. 顺坡",
                "analysis": "明渠均匀流要求沿程重力分力与摩阻力平衡，即渠底坡度等于水力坡度 $i = J > 0$，因此只有在顺坡（正坡）棱柱形明渠中才可能产生均匀流；平坡（$i=0$）和逆坡（$i<0$）中都不可能形成均匀流。故正确答案为 B。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 7,
                "kps": ["明渠均匀流特点"],
                "method": "明渠均匀流特征与形成条件判别法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2012-03",
                "year": 2012,
                "no": 3,
                "type": "single_choice",
                "score": 2,
                "title": "由绝对压强与当地大气压计算真空度",
                "stem": "液体中某点的绝对压强为 $96.04\\,\\mathrm{kN/m^2}$（当地大气压为 $98\\,\\mathrm{kN/m^2}$），则该点的真空度为（　）",
                "options": [
                    {"label": "A", "text": "$-1.96\\,\\mathrm{kN/m^2}$"},
                    {"label": "B", "text": "$1.96\\,\\mathrm{kN/m^2}$"},
                    {"label": "C", "text": "$96.04\\,\\mathrm{kN/m^2}$"},
                    {"label": "D", "text": "$-96.04\\,\\mathrm{kN/m^2}$"}
                ],
                "choiceAnswer": "B",
                "note": "",
                "figures": [],
                "shortAnswer": "B",
                "judgeAnswer": None,
                "answer": "B. $1.96\\,\\mathrm{kN/m^2}$",
                "analysis": "真空度定义为当地大气压高出该点绝对压强的数值（恒为正值）：\n\n$$\np_v = p_a - p_{\\text{绝}} = 98 - 96.04 = 1.96\\,\\mathrm{kN/m^2}\n$$\n\n故正确答案为 B。",
                "analysisFigures": [],
                "pitfalls": "$-1.96\\,\\mathrm{kN/m^2}$ 是相对压强，真空度为正值 $+1.96\\,\\mathrm{kN/m^2}$，切勿误选 A。",
                "chapter": 2,
                "kps": ["多液层压差计"],
                "method": "压强零点平移消元验证法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2012-04",
                "year": 2012,
                "no": 4,
                "type": "single_choice",
                "score": 2,
                "title": "明渠均匀流三线关系与运动特性辨析",
                "stem": "关于明渠均匀流，不正确的说法是（　）",
                "options": [
                    {"label": "A", "text": "总水头线与自由水面线重合"},
                    {"label": "B", "text": "过水断面上的流速分布沿程不变"},
                    {"label": "C", "text": "测压管水头线与底坡线平行"},
                    {"label": "D", "text": "等速、等深流"}
                ],
                "choiceAnswer": "A",
                "note": "",
                "figures": [],
                "shortAnswer": "A",
                "judgeAnswer": None,
                "answer": "A. 总水头线与自由水面线重合",
                "analysis": "明渠均匀流中，过水断面流速分布沿程不变、水深与断面平均流速沿程相等（B、D 正确），自由水面线即测压管水头线且与渠底坡线平行（$J = J_p = i$，C 正确）；而总水头线位于自由水面上方一个流速水头 $\\frac{\\alpha v^2}{2g}$ 处，二者互相平行而绝不重合，故 A 说法错误。故正确答案为 A。",
                "analysisFigures": [],
                "pitfalls": "注意区分“测压管水头线与自由水面线重合”（正确）与“总水头线与自由水面线重合”（错误）。",
                "chapter": 7,
                "kps": ["明渠均匀流特点"],
                "method": "明渠均匀流特征与形成条件判别法",
                "difficulty": 2
            },
            {
                "id": "yzu-849-2012-05",
                "year": 2012,
                "no": 5,
                "type": "single_choice",
                "score": 2,
                "title": "平衡液体等压面的通用几何性质",
                "stem": "平衡液体中的等压面必为（　）",
                "options": [
                    {"label": "A", "text": "水平面"},
                    {"label": "B", "text": "斜平面"},
                    {"label": "C", "text": "旋转抛物面"},
                    {"label": "D", "text": "与质量力正交的面"}
                ],
                "choiceAnswer": "D",
                "note": "",
                "figures": [],
                "shortAnswer": "D",
                "judgeAnswer": None,
                "answer": "D. 与质量力正交的面",
                "analysis": "由欧拉液体平衡微分方程 $\\mathrm{d}p = \\rho(f_x\\,\\mathrm{d}x + f_y\\,\\mathrm{d}y + f_z\\,\\mathrm{d}z)$，在等压面上 $\\mathrm{d}p = 0$，即 $\\vec{f}\\cdot\\mathrm{d}\\vec{r} = 0$。这表明无论绝对平衡还是相对平衡，平衡液体中的等压面必然处处与质量力（单位质量力）矢量正交（水平面、斜平面、旋转抛物面仅分别为特定质量力场下的特例）。故正确答案为 D。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 2,
                "kps": ["多液层压差计"],
                "method": "平衡微分方程与流线法向方程条件对比法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2012-06",
                "year": 2012,
                "no": 6,
                "type": "single_choice",
                "score": 2,
                "title": "直观演示层流与紊流流态的经典试验",
                "stem": "能直观演示出水流的层流与紊流流态的试验是（　）",
                "options": [
                    {"label": "A", "text": "普朗特试验"},
                    {"label": "B", "text": "牛顿试验"},
                    {"label": "C", "text": "尼古拉兹试验"},
                    {"label": "D", "text": "雷诺试验"}
                ],
                "choiceAnswer": "D",
                "note": "",
                "figures": [],
                "shortAnswer": "D",
                "judgeAnswer": None,
                "answer": "D. 雷诺试验",
                "analysis": "雷诺试验通过玻璃管内注入颜色水丝直观展示了层流（色线成笔直细丝）和紊流（色线剧烈摆动迅速扩散充满全管）两种流态，并提出雷诺数作为流态判据。故正确答案为 D。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 4,
                "kps": ["沿程与局部损失"],
                "method": "水力半径与当量直径雷诺数流态判别法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2012-07",
                "year": 2012,
                "no": 7,
                "type": "single_choice",
                "score": 2,
                "title": "虹吸管顶部真空值的物理极限条件",
                "stem": "虹吸管顶部的真空值 $p_k$ 应（　）",
                "options": [
                    {"label": "A", "text": "$p_k < 0$"},
                    {"label": "B", "text": "$p_k = 10\\,\\mathrm{m}$ 水柱压"},
                    {"label": "C", "text": "$p_k < 10\\,\\mathrm{m}$ 水柱压"},
                    {"label": "D", "text": "$p_k > 10\\,\\mathrm{m}$ 水柱压"}
                ],
                "choiceAnswer": "C",
                "note": "",
                "figures": [],
                "shortAnswer": "C",
                "judgeAnswer": None,
                "answer": "C. $p_k < 10\\,\\mathrm{m}$ 水柱压",
                "analysis": "虹吸管顶部高出上游水面，管内为真空状态（$p_k > 0$）；同时受限于当地大气压约 $10\\,\\mathrm{m}$ 水柱压及水的饱和汽化压强，为避免液柱汽化断裂导致虹吸中断，顶部真空值绝不能达到或超过 $10\\,\\mathrm{m}$ 水柱压（工程中一般控制在 $7\\sim 8\\,\\mathrm{m}$ 水柱压以下），即必满足 $p_k < 10\\,\\mathrm{m}$ 水柱压。故正确答案为 C。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 6,
                "kps": ["水泵最大允许安装高程"],
                "method": "允许真空度定安装高程+长管扬程求功率",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2012-08",
                "year": 2012,
                "no": 8,
                "type": "single_choice",
                "score": 2,
                "title": "雷诺数的无量纲力学意义",
                "stem": "雷诺数是表征（　）",
                "options": [
                    {"label": "A", "text": "惯性力与粘滞力之比"},
                    {"label": "B", "text": "惯性力与重力之比"},
                    {"label": "C", "text": "水压力与粘滞力之比"},
                    {"label": "D", "text": "粘滞力与重力之比"}
                ],
                "choiceAnswer": "A",
                "note": "",
                "figures": [],
                "shortAnswer": "A",
                "judgeAnswer": None,
                "answer": "A. 惯性力与粘滞力之比",
                "analysis": "雷诺数 $Re = \\frac{\\rho v l}{\\mu} = \\frac{\\rho l^2 v^2}{\\mu v l}$ 物理上表征水流中惯性力与粘滞力（内摩擦力）的相对大小之比；而惯性力与重力之比由弗劳德数 $Fr$ 表征。故正确答案为 A。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 10,
                "kps": ["雷诺相似准则"],
                "method": "水力半径与当量直径雷诺数流态判别法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2012-09",
                "year": 2012,
                "no": 9,
                "type": "single_choice",
                "score": 2,
                "title": "有压输水管道水击波传播周期计算",
                "stem": "某输水管道长度 $L = 1000\\,\\mathrm{m}$，若发生水击时水击波速 $a = 1000\\,\\mathrm{m/s}$，则水击周期为（　）",
                "options": [
                    {"label": "A", "text": "1 秒"},
                    {"label": "B", "text": "2 秒"},
                    {"label": "C", "text": "3 秒"},
                    {"label": "D", "text": "4 秒"}
                ],
                "choiceAnswer": "D",
                "note": "",
                "figures": [],
                "shortAnswer": "D",
                "judgeAnswer": None,
                "answer": "D. 4 秒",
                "analysis": "水击波在管道内经历增压波上传、反射恢复波下传、减压波上传、反射恢复波下传四个阶段（总路程 $4L$）才完成一个完整的水击周期：\n\n$$\nT = \\frac{4L}{a} = \\frac{4\\times 1000}{1000} = 4\\,\\mathrm{s}\n$$\n\n故正确答案为 D。",
                "analysisFigures": [],
                "pitfalls": "务必区分“水击相长（$t_r = \\frac{2L}{a} = 2\\,\\mathrm{s}$）”与“水击周期（$T = \\frac{4L}{a} = 4\\,\\mathrm{s}$）”两个高频概念，切勿误选 B。",
                "chapter": 6,
                "kps": ["水泵扬程与轴功率"],
                "method": "允许真空度定安装高程+长管扬程求功率",
                "difficulty": 2
            },
            {
                "id": "yzu-849-2012-10",
                "year": 2012,
                "no": 10,
                "type": "single_choice",
                "score": 2,
                "title": "等底面积等水深不同形状容器底部静水总压力比较",
                "stem": "如图所示，两形状不同的盛水容器，其底面面积相等，水深相等，试比较两容器底部所受静水总压力 $P$ 的相对大小为（　）",
                "options": [
                    {"label": "A", "text": "$P_1 > P_2$"},
                    {"label": "B", "text": "$P_1 = P_2$"},
                    {"label": "C", "text": "$P_1 < P_2$"},
                    {"label": "D", "text": "无法确定"}
                ],
                "choiceAnswer": "B",
                "note": "原卷将本题配图标号误印为“题 17 图”，实为单项选择题第 10 题配图。",
                "figures": [
                    {"src": "figures/q10_orig.png", "caption": "题 10 图　两不同形状等底面积等水深盛水容器"}
                ],
                "shortAnswer": "B",
                "judgeAnswer": None,
                "answer": "B. $P_1 = P_2$",
                "analysis": "容器底部为水平受压平面，其上各点静水压强均匀相等 $p = \\rho g H$，故底面所受静水总压力为：\n\n$$\nP = pA = \\rho g H A\n$$\n\n因两容器均盛水（$\\rho$ 相同）、水深 $H$ 相等、底面积 $A$ 相等，故 $P_1 = P_2$（静水压强与容器侧壁形状及盛水总重无关，这就是著名的水静力学奇象）。故正确答案为 B。",
                "analysisFigures": [],
                "pitfalls": "容器 1 中装水量更多，但多出的那部分水重由倾斜侧壁向上承托，并不直接传递到底面上，故底部总压力仍严格等于 $\\rho g H A$。",
                "chapter": 2,
                "kps": ["平面与曲面静水总压力"],
                "method": "平面静水总压力解析法与平行移轴求压心法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2012-11",
                "year": 2012,
                "no": 11,
                "type": "fill",
                "subType": "mini-calc",
                "score": 3,
                "title": "矩形断面明渠水力半径计算",
                "stem": "某矩形断面渠道，底宽 $b = 4\\,\\mathrm{m}$，水深 $h = 2\\,\\mathrm{m}$，则其水力半径 $R =$ ________。",
                "note": "",
                "figures": [],
                "shortAnswer": "1 m",
                "judgeAnswer": None,
                "answer": "$1\\,\\mathrm{m}$",
                "analysis": "矩形明渠过水断面面积 $A = bh = 4\\times 2 = 8\\,\\mathrm{m^2}$，湿周 $\\chi = b + 2h = 4 + 2\\times 2 = 8\\,\\mathrm{m}$，故水力半径：\n\n$$\nR = \\frac{A}{\\chi} = \\frac{8}{8} = 1\\,\\mathrm{m}\n$$\n\n（注意此处恰满足矩形水力最佳断面条件 $b = 2h$，故 $R = h/2 = 1\\,\\mathrm{m}$。）",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 7,
                "kps": ["水力最佳断面"],
                "method": "明渠均匀流曼宁公式求底坡与高程法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2012-12",
                "year": 2012,
                "no": 12,
                "type": "fill",
                "subType": "blank",
                "score": 3,
                "title": "水力最佳断面湿周最小与过水能力最大关系",
                "stem": "当渠道的底坡、粗糙系数及过水断面面积一定时，湿周愈小则通过的流量________。",
                "note": "",
                "figures": [],
                "shortAnswer": "愈大（越大）",
                "judgeAnswer": None,
                "answer": "愈大（或越大）",
                "analysis": "由明渠均匀流曼宁公式 $Q = \\frac{1}{n} A R^{2/3} i^{1/2} = \\frac{1}{n} A^{5/3} \\chi^{-2/3} i^{1/2}$，当 $i$、$n$、$A$ 均一定时，流量 $Q$ 与湿周 $\\chi$ 的 $2/3$ 次方成反比。因此湿周 $\\chi$ 愈小，水力半径 $R = A/\\chi$ 愈大，水流摩擦边界阻力越小，通过的流量愈大。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 7,
                "kps": ["水力最佳断面", "曼宁公式"],
                "method": "明渠均匀流特征与形成条件判别法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2012-13",
                "year": 2012,
                "no": 13,
                "type": "fill",
                "subType": "blank",
                "score": 3,
                "title": "达西渗流渗透系数的量纲",
                "stem": "渗透系数 $k$ 的量纲为________。",
                "note": "",
                "figures": [],
                "shortAnswer": "LT⁻¹",
                "judgeAnswer": None,
                "answer": "$\\mathrm{L T^{-1}}$",
                "analysis": "由达西渗流定律 $v = kJ$，其中水力坡度 $J$ 为无量纲量，故渗透系数 $k$ 与渗流流速 $v$ 具有相同量纲，即 $[k] = [v] = \\mathrm{L T^{-1}}$（国际单位为 $\\mathrm{m/s}$）。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 10,
                "kps": ["达西定律"],
                "method": "多孔介质连续化等效三原则归纳法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2012-14",
                "year": 2012,
                "no": 14,
                "type": "fill",
                "subType": "blank",
                "score": 3,
                "title": "曲面静水总压力铅垂分力的压力体物理意义",
                "stem": "作用于曲面上静水总压力 $P$ 的垂直分力 $P_z$ 的大小就等于压力体内的________。",
                "note": "",
                "figures": [],
                "shortAnswer": "液体重量（水体重量）",
                "judgeAnswer": None,
                "answer": "液体重量（或水体重量 $\\rho g V_z$）",
                "analysis": "由二元曲面静水总压力理论，铅垂分力 $P_z = \\rho g V_z$，其大小等于由受压曲面、过曲面周界铅垂母线及自由液面（或等效自由液面）所围成的压力体内所含同种液体的重量。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 2,
                "kps": ["平面与曲面静水总压力"],
                "method": "水平投影与铅垂压力体分块合成法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2012-15",
                "year": 2012,
                "no": 15,
                "type": "fill",
                "subType": "blank",
                "score": 3,
                "title": "紊流粗糙区沿程阻力系数的决定因素",
                "stem": "紊流粗糙区的沿程水头损失系数 $\\lambda$ 与________有关。",
                "note": "",
                "figures": [],
                "shortAnswer": "相对粗糙度 Δ/d（或 Δ/r0）",
                "judgeAnswer": None,
                "answer": "相对粗糙度 $\\Delta/d$（或 $\\Delta/r_0$）",
                "analysis": "在紊流粗糙区（阻力平方区），粘滞底层厚度远小于壁面绝对粗糙度，粗糙凸起完全暴露于紊流核心区，沿程阻力系数 $\\lambda$ 不再与雷诺数 $Re$ 有关，仅是管壁相对粗糙度 $\\Delta/d$（或 $r_0/\\Delta$）的函数。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 4,
                "kps": ["沿程与局部损失"],
                "method": "达西公式与莫迪图五区分类对比法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2012-16",
                "year": 2012,
                "no": 16,
                "type": "fill",
                "subType": "blank",
                "score": 3,
                "title": "无涡流场速度势函数的存在性",
                "stem": "无涡流的流场中必存在________函数。",
                "note": "",
                "figures": [],
                "shortAnswer": "流速势（速度势）",
                "judgeAnswer": None,
                "answer": "流速势（或速度势）",
                "analysis": "无涡流（无旋流动）满足 $\\nabla\\times\\vec{u} = \\vec{0}$，由矢量分析定理，旋度为零的速度场必可表示为某一标量函数 $\\varphi$ 的梯度，即流场中必存在流速势（速度势）函数 $\\varphi$。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 5,
                "kps": ["流函数与势函数"],
                "method": "连续性与无旋性判据及流函数求单宽流量法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2012-17",
                "year": 2012,
                "no": 17,
                "type": "fill",
                "subType": "blank",
                "score": 3,
                "title": "渐变流同一过水断面上的静水压强分布特征",
                "stem": "在均匀流或非均匀渐变流的同一过水断面上，各点的________为一常数。",
                "note": "",
                "figures": [],
                "shortAnswer": "测压管水头（z + p/(ρg)）",
                "judgeAnswer": None,
                "answer": "测压管水头（即 $z + \\frac{p}{\\rho g}$）",
                "analysis": "在均匀流或渐变流的过水断面上，流线近似为平行直线、法向离心惯性加速度可忽略，故断面上服从静水压强分布规律，即同一过水断面上各点的测压管水头 $z + \\frac{p}{\\rho g} = \\mathrm{const}$。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 3,
                "kps": ["伯努利方程测流"],
                "method": "平衡微分方程与流线法向方程条件对比法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2012-18",
                "year": 2012,
                "no": 18,
                "type": "fill",
                "subType": "blank",
                "score": 3,
                "title": "水平恒定均匀有压管流动水压强沿程变化规律",
                "stem": "水平放置的管道，当管中水流为恒定均匀流时，动水压强沿程________。",
                "note": "",
                "figures": [],
                "shortAnswer": "线性减小（沿程降低）",
                "judgeAnswer": None,
                "answer": "线性减小（或沿程降低）",
                "analysis": "对于水平放置的等径圆管恒定均匀流，$z_1 = z_2$ 且 $v_1 = v_2$。沿流向列实际液体恒定总流能量方程：\n\n$$\nz_1 + \\frac{p_1}{\\rho g} + \\frac{\\alpha v_1^2}{2g} = z_2 + \\frac{p_2}{\\rho g} + \\frac{\\alpha v_2^2}{2g} + h_f \\implies p_1 - p_2 = \\rho g h_f = \\rho g J l > 0\n$$\n\n由于实际水流克服沿程粘性阻力不断消耗压能（水力坡度 $J = \\mathrm{const} > 0$），故水平管道恒定均匀流的动水压强沿程线性减小（降低）。",
                "analysisFigures": [],
                "pitfalls": "切忌把“明渠均匀流水深沿程不变”或“理想流体无损失”错误迁移到水平有压管流而填成“保持不变”！水平有压管流正是依靠沿程压降 $\\Delta p = \\rho g J l$ 驱动水流克服管壁摩阻力前进。",
                "chapter": 6,
                "kps": ["沿程与局部损失"],
                "method": "总水头大小判别流向与恒定总流能量方程",
                "difficulty": 2
            },
            {
                "id": "yzu-849-2012-19",
                "year": 2012,
                "no": 19,
                "type": "short",
                "score": 6,
                "title": "等面积正方形与圆形过水断面水力半径大小比较",
                "stem": "面积相等的正方形和圆形过水断面的水力半径哪个大，为什么？",
                "note": "",
                "figures": [],
                "shortAnswer": "圆形过水断面的水力半径更大（R圆 = √A / (2√π) ≈ 0.282√A > R正 = 0.25√A），因等面积封闭平面图形中圆的周长（湿周）最小。",
                "judgeAnswer": None,
                "answer": "圆形过水断面的水力半径更大。证明如下：\n\n设正方形和圆形满流过水断面的面积均为 $A$：\n\n1. 正方形过水断面：边长 $a = \\sqrt{A}$，湿周 $\\chi_{\\text{正}} = 4a = 4\\sqrt{A}$，水力半径为：\n\n$$\nR_{\\text{正}} = \\frac{A}{\\chi_{\\text{正}}} = \\frac{\\sqrt{A}}{4} = 0.25\\sqrt{A}\n$$\n\n2. 圆形过水断面：半径 $r = \\sqrt{A/\\pi}$，湿周 $\\chi_{\\text{圆}} = 2\\pi r = 2\\sqrt{\\pi A} \\approx 3.545\\sqrt{A}$，水力半径为：\n\n$$\nR_{\\text{圆}} = \\frac{A}{\\chi_{\\text{圆}}} = \\frac{\\sqrt{A}}{2\\sqrt{\\pi}} \\approx 0.282\\sqrt{A}\n$$\n\n因 $\\pi < 4 \\implies 2\\sqrt{\\pi} < 4$，即等面积封闭图形中圆的湿周最小，所以 $R_{\\text{圆}} > R_{\\text{正}}$（比值为 $2/\\sqrt{\\pi} \\approx 1.128$），圆形管道具有更优的过水经济性。",
                "analysis": "直接由水力半径定义 $R = A/\\chi$ 用同一面积 $A$ 表达两者的湿周并做代数对比，简洁明了。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 4,
                "kps": ["沿程与局部损失", "水力最佳断面"],
                "method": "水力半径与当量直径雷诺数流态判别法",
                "difficulty": 1,
                "rubric": [
                    {"label": "写出水力半径定义 R = A/χ，并分别导出等面积正方形 R正 = √A / 4", "pts": 2},
                    {"label": "正确导出等面积圆形水力半径 R圆 = √A / (2√π) ≈ 0.282√A", "pts": 2},
                    {"label": "通过比较湿周大小（2√π < 4）得出圆形水力半径更大的结论", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2012-20",
                "year": 2012,
                "no": 20,
                "type": "short",
                "score": 6,
                "title": "定流量圆管雷诺数随管径增大的变化规律",
                "stem": "当输水管的流量一定时，随管径的增大，雷诺数如何变化，为什么？",
                "note": "",
                "figures": [],
                "shortAnswer": "雷诺数减小。由连续性方程 v = 4Q/(πd²) 代入 Re = vd/ν = 4Q/(πdν)，流量 Q 与运动粘滞系数 ν 一定时，Re 与管径 d 成反比。",
                "judgeAnswer": None,
                "answer": "当输水管流量 $Q$（及水温对应的运动粘滞系数 $\\nu$）一定时，随管径 $d$ 的增大，雷诺数 $Re$ 减小。\n\n原因推导：\n\n1. 圆管过水面积 $A = \\frac{\\pi}{4}d^2$，由恒定流连续性方程得断面平均流速：\n\n$$\nv = \\frac{Q}{A} = \\frac{4Q}{\\pi d^2}\n$$\n\n2. 将 $v$ 代入圆管雷诺数定义式 $Re = \\frac{vd}{\\nu}$：\n\n$$\nRe = \\frac{vd}{\\nu} = \\frac{4Q}{\\pi d\\nu}\n$$\n\n可见当 $Q$、$\\nu$ 保持不变时，$Re \\propto \\frac{1}{d}$，虽然分子 $d$ 一次方增大，但流速 $v$ 随 $d^2$ 平方反比下降，综合效应使雷诺数与管径 $d$ 成反比，故管径增大时 $Re$ 减小。",
                "analysis": "切忌只盯住 $Re = vd/\\nu$ 的分子 $d$ 而误以为 $Re$ 增大！关键在于先把隐含随 $d$ 变化的 $v$ 用不变量 $Q$ 替换掉。",
                "analysisFigures": [],
                "pitfalls": "常见误区是忘记在定流量条件下 $v \\propto d^{-2}$，从而误判为 $Re$ 随 $d$ 增大而增大。",
                "chapter": 4,
                "kps": ["沿程与局部损失"],
                "method": "水力半径与当量直径雷诺数流态判别法",
                "difficulty": 1,
                "rubric": [
                    {"label": "明确给出结论：雷诺数 Re 随管径增大而减小", "pts": 2},
                    {"label": "写出连续性方程 v = 4Q/(πd²) 并代入雷诺数公式导出 Re = 4Q/(πdν)", "pts": 3},
                    {"label": "指出 Q、ν 一定时 Re 与管径 d 成反比关系", "pts": 1}
                ]
            },
            {
                "id": "yzu-849-2012-21",
                "year": 2012,
                "no": 21,
                "type": "short",
                "score": 6,
                "title": "流线不能相交的运动学机理证明",
                "stem": "流线为什么不能相交？",
                "note": "",
                "figures": [],
                "shortAnswer": "流线上任意一点的切线方向代表该瞬时该点流体质点的速度方向；若两条流线相交，则在交点处同一时刻同一质点将同时具有两个不同的速度方向，违背物理单值性（驻点或奇点除外）。",
                "judgeAnswer": None,
                "answer": "依据流线的定义采用反证法说明：\n\n1. 流线是在某一给定瞬时流场中绘制的曲线，其上任意一点的切线方向均与该瞬时该点流体质点的流速矢量方向相重合；\n\n2. 假设两条流线在流场某常规点相交，则在该交点处将同时存在两条不同的切线方向，这意味着同一时刻位于同一空间位置的流体质点竟然同时具有两个不同的运动速度方向；\n\n3. 根据连续介质单值速度场假设，同一瞬时空间任一点（除流速为零的驻点或源汇等数学奇点外）只能有唯一确定的速度矢量，因此流线不能相交（同理也不能突然折转）。",
                "analysis": "回答流线性质简答题时，补充说明“除流速为零的驻点及奇点外”能体现严谨的流体力学功底。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 3,
                "kps": ["流函数与势函数"],
                "method": "平衡微分方程与流线法向方程条件对比法",
                "difficulty": 1,
                "rubric": [
                    {"label": "准确给出流线定义：某瞬时曲线上各点切线方向与该点速度方向一致", "pts": 2},
                    {"label": "反证：若相交则交点处同一时刻存在两个不同切线（速度）方向，违背速度场单值唯一性", "pts": 3},
                    {"label": "补充说明驻点（v = 0）或源汇奇点等特殊情况除外", "pts": 1}
                ]
            },
            {
                "id": "yzu-849-2012-22",
                "year": 2012,
                "no": 22,
                "type": "short",
                "score": 6,
                "title": "渗透系数 k 值的三种确定方法及其优缺点对比",
                "stem": "渗透系数 $k$ 值的确定有哪几种方法？各自的优缺点是什么？",
                "note": "",
                "figures": [],
                "shortAnswer": "（1）经验公式/查表法：简便省费但精度粗糙；（2）室内渗流试验法（常水头/变水头法）：设备简单费用低，但取样易扰动原状土且代表性受限；（3）野外现场试验法（抽水/注水试验）：反映原状土层真实渗透性最准确，但工程量大、周期长、费用高。",
                "judgeAnswer": None,
                "answer": "工程水力学中确定土体渗透系数 $k$ 主要有三大类方法：\n\n1. 经验法（查阅土质经验表或采用哈森经验公式估算）\n- 优点：资料查找方便、无需现场或室内试验、快捷省费；\n- 缺点：仅反映同类土的平均统计范围，未考虑实际土层密实度与结构特征，精度较差，仅适用于初步规划与粗略估算。\n\n2. 室内试验测定法（常水头渗透仪法用于粗粒土，变水头渗透仪法用于细粒黏性土）\n- 优点：仪器设备简单、操作周期短、边界条件易于控制、费用较低；\n- 缺点：钻孔取样和制样过程易破坏原状土结构，且试样尺寸很小，难以反映天然土层的非均质性与裂隙特征，代表性较差。\n\n3. 野外现场测定法（现场抽水试验、压水/注水试验等）\n- 优点：直接在天然原状土层中测试，能综合反映含水层宏观结构、层理与裂隙的真实渗流特性，测定结果最具代表性与工程可靠性；\n- 缺点：需布设抽水井及观测井网，设备与施工工程量大、耗时长、测试费用高昂。",
                "analysis": "按“经验法—室内法—野外法”由简到繁、精度由粗到精、费用由低到高的逻辑条理作答，最易拿满 6 分。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 10,
                "kps": ["达西定律"],
                "method": "多孔介质连续化等效三原则归纳法",
                "difficulty": 2,
                "rubric": [
                    {"label": "完整列出经验法、室内试验测定法、野外现场测定法（抽水试验）三类方法", "pts": 2},
                    {"label": "准确简述经验法与室内试验法各自的优缺点（简便省费 vs 精度差/扰动原状土）", "pts": 2},
                    {"label": "准确简述野外现场测定法的优缺点（反映原状土真实性最准确 vs 设备复杂、费用高、耗时长）", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2012-23",
                "year": 2012,
                "no": 23,
                "type": "calc",
                "score": 15,
                "title": "封闭盛水容器水面压强与敞口测压管液面高差计算",
                "stem": "有一盛水的封闭容器，其上接有二根玻璃管，一管顶端封闭，其水面压强 $p_0 = 8.829\\,\\mathrm{N/cm^2}$，一管顶端敞开，水面与大气接触，如图所示。已知 $h_0 = 2\\,\\mathrm{m}$，求：\n\n（1）容器内的水面压强 $p_c$；\n\n（2）敞口管与容器内的水面高差 $x$。",
                "note": "注意 $p_0 = 8.829\\,\\mathrm{N/cm^2} = 88.29\\,\\mathrm{kPa} = 9.00\\times 9.81\\,\\mathrm{kPa}$ 为绝对压强；当地大气压参照本卷第 3 题取工程大气压 $p_a = 98\\,\\mathrm{kPa}$（同步附 $p_a = 98.1\\,\\mathrm{kPa}$ 及标准大气压 $101.325\\,\\mathrm{kPa}$ 对照值）。",
                "figures": [
                    {"src": "figures/q23_orig.png", "caption": "题 23 图　封闭盛水容器与双测压管装置图"}
                ],
                "shortAnswer": "（1）pc = 107.91 kPa（g=9.81；g=9.80 为 107.89 kPa）；（2）x = 1.01 m（pa = 98 kPa，g=9.81；pa = 98.1 kPa 恰为 1.00 m；pa = 101.325 kPa 为 0.671 m）。",
                "judgeAnswer": None,
                "answer": "（1）容器内水面绝对压强 $p_c = 107.91\\,\\mathrm{kPa}$（按 $g = 9.81\\,\\mathrm{m/s^2}$；按 $g = 9.80\\,\\mathrm{m/s^2}$ 为 $107.89\\,\\mathrm{kPa}$）；\n\n（2）敞口管高出容器内水面的高度差 $x = 1.01\\,\\mathrm{m}$（按 $p_a = 98\\,\\mathrm{kPa}$；按 $1\\,\\mathrm{at} = 98.1\\,\\mathrm{kPa}$ 恰得 $x = 1.00\\,\\mathrm{m}$；按标准大气压 $p_a = 101.325\\,\\mathrm{kPa}$ 得 $x = 0.671\\,\\mathrm{m}$）。",
                "analysis": "1. 单位换算与绝对压强识别\n\n左侧封闭管液面气体压强：\n\n$$\np_0 = 8.829\\,\\mathrm{N/cm^2} = 8.829\\times 10^4\\,\\mathrm{N/m^2} = 88.29\\,\\mathrm{kPa}\n$$\n\n因 $88.29\\,\\mathrm{kPa} = 9.00\\times 9.81\\,\\mathrm{kPa}$ 且小于大气压、同时敞口管液面高出容器水面，故 $p_0$ 为绝对压强（以下统一按绝对压强列式，并取与 $8.829$ 协调的 $g = 9.81\\,\\mathrm{m/s^2}$，同步附 $g = 9.80\\,\\mathrm{m/s^2}$ 结果）。\n\n2. 求容器内水面压强 $p_c$\n\n取与容器内水面齐平的水平面作为等压面（见解图 23），左侧封闭管与容器通过底部水体连续连通，且左管水面高出容器水面 $h_0 = 2\\,\\mathrm{m}$，由水静力学基本方程：\n\n$$\np_c = p_0 + \\rho g h_0 = 88.29\\times 10^3 + 1000\\times 9.81\\times 2 = 107910\\,\\mathrm{Pa} = 107.91\\,\\mathrm{kPa}\n$$\n\n（若取 $g = 9.80\\,\\mathrm{m/s^2}$，则 $p_c = 88.29 + 9.80\\times 2 = 107.89\\,\\mathrm{kPa}$。）\n\n3. 求敞口管与容器内水面高差 $x$\n\n右侧敞口管与容器底部水体连续连通，水面与大气接触（绝对压强为 $p_a$），在同一等压面上有：\n\n$$\np_c = p_a + \\rho g x \\implies x = \\frac{p_c - p_a}{\\rho g}\n$$\n\n- 参照本卷第 3 题取当地工程大气压 $p_a = 98\\,\\mathrm{kPa}$（$g = 9.81\\,\\mathrm{m/s^2}$）：\n\n$$\nx = \\frac{107.91 - 98.0}{9.81} = 1.010\\,\\mathrm{m} \\approx 1.01\\,\\mathrm{m}\n$$\n\n（若取 $g = 9.80\\,\\mathrm{m/s^2}$ 且 $p_a = 98.0\\,\\mathrm{kPa}$，则 $x = \\frac{107.89 - 98.0}{9.80} = 1.009\\,\\mathrm{m} \\approx 1.01\\,\\mathrm{m}$；若取 $1\\,\\mathrm{at} = 98.1\\,\\mathrm{kPa}$ 且 $g = 9.81\\,\\mathrm{m/s^2}$，则 $x = \\frac{107.91 - 98.1}{9.81} = 1.00\\,\\mathrm{m}$；若取标准物理大气压 $p_a = 101.325\\,\\mathrm{kPa}$，则 $x = \\frac{107.91 - 101.325}{9.81} = 0.671\\,\\mathrm{m}$。）",
                "analysisFigures": [
                    {"src": "figures/q23_sol.png", "caption": "解图 23　封闭盛水容器双玻璃测压管等压面分析图"}
                ],
                "pitfalls": "注意单位换算 $1\\,\\mathrm{N/cm^2} = 10^4\\,\\mathrm{Pa} = 10\\,\\mathrm{kPa}$，切勿误算成 $10^2\\,\\mathrm{Pa}$；同时左右两管均应统一使用绝对压强列式。",
                "chapter": 2,
                "kps": ["多液层压差计"],
                "method": "等压面静水压强递推法",
                "difficulty": 2,
                "rubric": [
                    {"label": "正确进行压强单位换算 p0 = 8.829 N/cm² = 88.29 kPa 并识别为绝对压强", "pts": 3},
                    {"label": "取容器水面为等压面列式 pc = p0 + ρgh0，求得 pc = 107.91 kPa（g=9.80 为 107.89 kPa）", "pts": 6},
                    {"label": "对右侧敞口管列等压面方程 pc = pa + ρgx，准确求得水面高差 x ≈ 1.01 m（pa = 98 kPa；或按 pa = 101.325 kPa 得 0.671 m）", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2012-24",
                "year": 2012,
                "no": 24,
                "type": "calc",
                "score": 15,
                "title": "60° 斜坡上静止圆筒所受静水总压力大小及方向计算",
                "stem": "有一圆筒，直径 $d = 2\\,\\mathrm{m}$，长度 $L = 4\\,\\mathrm{m}$，停止在一与水平成 $60^{\\circ}$ 角的斜坡上，水面位置如图所示，假定圆筒与斜坡之间不透水，求圆筒所受的静水总压力及方向。",
                "note": "",
                "figures": [
                    {"src": "figures/q24_orig.png", "caption": "题 24 图　停放在 60° 斜坡上的圆筒与水面位置"}
                ],
                "shortAnswer": "P = 97.51 kN（g=9.80；g=9.81 为 97.61 kN），方向指向右上方、与水平面夹角 θ = 78.40°，作用线通过圆筒轴心。",
                "judgeAnswer": None,
                "answer": "圆筒所受静水总压力大小为 $P = 97.51\\,\\mathrm{kN}$（取 $g = 9.81\\,\\mathrm{m/s^2}$ 时为 $97.61\\,\\mathrm{kN}$）；方向指向右上方，与水平面夹角 $\\theta = 78.40^{\\circ}$，作用线通过圆筒中心轴线。",
                "analysis": "由题图可知，水面与圆筒左侧交点至圆筒与 $60^{\\circ}$ 斜坡切点的连线恰为圆筒的一条直径（垂直于 $60^{\\circ}$ 斜坡），因此该直径与水平面夹角为 $30^{\\circ}$，圆筒浸水段为该斜直径下方的半圆柱面（见解图 24）。\n\n1. 求水平分力 $P_x$（水平向右）\n\n受压半圆柱面的铅垂投影高度为 $h = d\\cos 60^{\\circ} = 2\\times 0.5 = 1.0\\,\\mathrm{m}$，投影矩形面积 $A_x = hL = 1.0\\times 4.0 = 4.0\\,\\mathrm{m^2}$，形心淹深 $h_c = h/2 = 0.5\\,\\mathrm{m}$。取 $g = 9.80\\,\\mathrm{m/s^2}$：\n\n$$\nP_x = \\rho g h_c A_x = 1000\\times 9.80\\times 0.5\\times 4.0 = 19600\\,\\mathrm{N} = 19.60\\,\\mathrm{kN}\n$$\n\n（取 $g = 9.81\\,\\mathrm{m/s^2}$ 时 $P_x = 19.62\\,\\mathrm{kN}$。）\n\n2. 求铅垂分力 $P_z$（竖直向上）\n\n水体位于受压半圆柱面下方，形成向上的虚压力体：由斜直径上方至自由水面的直角三角形（直角边分别为 $d\\cos 60^{\\circ} = 1.0\\,\\mathrm{m}$ 与 $d\\sin 60^{\\circ} = \\sqrt{3}\\,\\mathrm{m}$）加上斜直径下方的半圆面积（$\\frac{1}{2}\\cdot\\frac{\\pi}{4}d^2 = \\frac{\\pi}{2}\\,\\mathrm{m^2}$）组成：\n\n$$\nV_z = \\left(\\frac{1}{2} d\\cos 60^{\\circ} \\cdot d\\sin 60^{\\circ} + \\frac{\\pi d^2}{8}\\right)L = \\left(\\frac{\\sqrt{3}}{2} + \\frac{\\pi}{2}\\right)\\times 4 = 2(\\sqrt{3} + \\pi) \\approx 9.7473\\,\\mathrm{m^3}\n$$\n\n$$\nP_z = \\rho g V_z = 1000\\times 9.80\\times 9.7473 = 95523\\,\\mathrm{N} \\approx 95.52\\,\\mathrm{kN}\n$$\n\n（取 $g = 9.81\\,\\mathrm{m/s^2}$ 时 $P_z = 95.62\\,\\mathrm{kN}$。）\n\n3. 合成静水总压力与方向\n\n$$\nP = \\sqrt{P_x^2 + P_z^2} = \\sqrt{19.60^2 + 95.52^2} \\approx 97.51\\,\\mathrm{kN}\n$$\n\n（取 $g = 9.81\\,\\mathrm{m/s^2}$ 时 $P = 97.61\\,\\mathrm{kN}$。）\n\n方向指向右上方，与水平面夹角为：\n\n$$\n\\theta = \\arctan\\frac{P_z}{P_x} = \\arctan\\frac{95.52}{19.60} \\approx 78.40^{\\circ}\n$$\n\n因圆柱面上所有微元压力均沿径向指向圆心，故合力作用线必通过圆筒轴心。",
                "analysisFigures": [
                    {"src": "figures/q24_sol.png", "caption": "解图 24　60° 斜坡圆筒虚压力体分解与静水总压力方向图"}
                ],
                "pitfalls": "1. 计算铅垂虚压力体时切勿漏掉斜直径上方至自由水面之间的直角三角形部分；\n2. 总压力的单位是力（$\\mathrm{kN}$），切忌误写成压强单位 $\\mathrm{kN/m^2}$！",
                "chapter": 2,
                "kps": ["平面与曲面静水总压力"],
                "method": "水平投影与铅垂压力体分块合成法",
                "difficulty": 3,
                "rubric": [
                    {"label": "确定受压半圆柱面铅垂投影高度 h = d·cos60° = 1.0 m，算得水平分力 Px = 19.60 kN（向右）", "pts": 4},
                    {"label": "正确构成虚压力体（直角三角形 + 下半圆）并算得 Vz ≈ 9.747 m³ 及向上铅垂分力 Pz = 95.52 kN", "pts": 6},
                    {"label": "合成总压力 P = 97.51 kN（单位正确）、求得仰角 θ = 78.40° 并指明作用线过圆心指向右上方", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2012-25",
                "year": 2012,
                "no": 25,
                "type": "calc",
                "score": 16,
                "title": "90° 弯管局部水头损失系数实验测定计算",
                "stem": "为测定 $90^{\\circ}$ 弯管的局部水头损失系数 $\\zeta$ 值，可采用如图所示的装置。已知 $AB$ 段管长 $L$ 为 $10\\,\\mathrm{m}$，管径 $d$ 为 $50\\,\\mathrm{mm}$，供水箱水位可调，今测得实验数据为：\n\n（1）当 $A$、$B$ 两测压管的水头差为 $62.9\\,\\mathrm{cm}$，测得经 $1\\,\\mathrm{min}$ 流入量水箱的水量为 $164.5\\,\\mathrm{L}$；\n\n（2）当 $A$、$B$ 两测压管的水头差为 $72.6\\,\\mathrm{cm}$，测得经 $1\\,\\mathrm{min}$ 流入量水箱的水量为 $176.8\\,\\mathrm{L}$。\n\n试求弯管的局部水头损失系数 $\\zeta$ 值。",
                "note": "注：原卷在印刷时遗漏了原教材例题中给定的管道沿程阻力系数 $\\lambda = 0.03$。解析先由两组实测数据严密导出通式 $\\zeta = 6.321 - 200\\lambda$，再代入原题常规值 $\\lambda = 0.03$ 求得 $\\zeta \\approx 0.32$。",
                "figures": [
                    {"src": "figures/q25_orig.png", "caption": "题 25 图　90° 弯管局部水头损失系数测定实验装置"}
                ],
                "shortAnswer": "两组实测总阻力系数均值 (λL/d + ζ) = 6.321（g=9.80；g=9.81 为 6.327），即 ζ = 6.321 - 200λ；代入原教材设定 λ = 0.03 得 ζ ≈ 0.32。",
                "judgeAnswer": None,
                "answer": "由两组实测数据算得 $AB$ 段总阻力系数 $\\lambda\\frac{L}{d} + \\zeta$ 分别为 $6.323$ 与 $6.318$（平均值 $6.321$，按 $g=9.81\\,\\mathrm{m/s^2}$ 为 $6.327$），即 $\\zeta = 6.321 - 200\\lambda$；代入原题沿程阻力系数 $\\lambda = 0.03$ 后，得两组 $\\zeta_1 = 0.323$、$\\zeta_2 = 0.318$，平均弯管局部水头损失系数 $\\bar{\\zeta} \\approx 0.32$。",
                "analysis": "1. 建立 $A$、$B$ 两断面能量方程\n\n因 $AB$ 段管道等径（$d = 0.05\\,\\mathrm{m}$），由连续性方程知 $v_A = v_B = v$，过水面积 $A = \\frac{\\pi}{4}d^2 = 1.9635\\times 10^{-3}\\,\\mathrm{m^2}$。对 $A$、$B$ 两断面列恒定总流能量方程（动能水头抵消）：\n\n$$\n\\left(z_A + \\frac{p_A}{\\rho g}\\right) - \\left(z_B + \\frac{p_B}{\\rho g}\\right) = h_w = h_f + h_j = \\left(\\lambda\\frac{L}{d} + \\zeta\\right)\\frac{v^2}{2g}\n$$\n\n其中 $L/d = 10 / 0.05 = 200$，故总阻力系数：\n\n$$\n\\Sigma\\zeta_{AB} = 200\\lambda + \\zeta = \\frac{2g h_w}{v^2}\n$$\n\n2. 代入两组实测数据计算（取 $g = 9.80\\,\\mathrm{m/s^2}$）\n\n- 第（1）组工况（$h_{w1} = 0.629\\,\\mathrm{m}$，$V_1 = 164.5\\,\\mathrm{L} = 0.1645\\,\\mathrm{m^3}$，$t = 60\\,\\mathrm{s}$）：\n\n$$\nQ_1 = \\frac{0.1645}{60} = 2.7417\\times 10^{-3}\\,\\mathrm{m^3/s}, \\qquad v_1 = \\frac{Q_1}{A} = 1.3963\\,\\mathrm{m/s}\n$$\n\n$$\n\\frac{v_1^2}{2g} = \\frac{1.3963^2}{2\\times 9.80} = 0.09947\\,\\mathrm{m} \\implies (200\\lambda + \\zeta)_1 = \\frac{0.629}{0.09947} = 6.323\n$$\n\n- 第（2）组工况（$h_{w2} = 0.726\\,\\mathrm{m}$，$V_2 = 176.8\\,\\mathrm{L} = 0.1768\\,\\mathrm{m^3}$，$t = 60\\,\\mathrm{s}$）：\n\n$$\nQ_2 = \\frac{0.1768}{60} = 2.9467\\times 10^{-3}\\,\\mathrm{m^3/s}, \\qquad v_2 = \\frac{Q_2}{A} = 1.5007\\,\\mathrm{m/s}\n$$\n\n$$\n\\frac{v_2^2}{2g} = \\frac{1.5007^2}{2\\times 9.80} = 0.11491\\,\\mathrm{m} \\implies (200\\lambda + \\zeta)_2 = \\frac{0.726}{0.11491} = 6.318\n$$\n\n（取 $g = 9.81\\,\\mathrm{m/s^2}$ 时两组结果分别为 $6.330$ 与 $6.325$，均值 $6.327$。）\n\n3. 确定弯管局部水头损失系数 $\\zeta$\n\n两组不同流量下的总阻力系数几乎完全相等（说明管道处于紊流阻力平方区，$\\lambda$ 为常数），均值为 $\\overline{200\\lambda + \\zeta} = 6.321$，即：\n\n$$\n\\zeta = 6.321 - 200\\lambda\n$$\n\n由于原卷漏印了该经典教材原题给出的管道沿程阻力系数 $\\lambda = 0.03$，代入 $\\lambda = 0.03$ 后即得：\n\n$$\n\\zeta_1 = 6.323 - 6.00 = 0.323, \\qquad \\zeta_2 = 6.318 - 6.00 = 0.318\n$$\n\n取算术平均值作为最终测定值：\n\n$$\n\\bar{\\zeta} = \\frac{0.323 + 0.318}{2} = 0.321 \\approx 0.32\n$$\n\n（若按手算截位 $v_1 \\approx 1.40\\,\\mathrm{m/s}$、$v_2 \\approx 1.50\\,\\mathrm{m/s}$、$g = 9.81\\,\\mathrm{m/s^2}$，则得 $\\zeta_1 \\approx 0.30$、$\\zeta_2 \\approx 0.33$，均值 $\\bar{\\zeta} \\approx 0.315 \\approx 0.32$。）",
                "analysisFigures": [
                    {"src": "figures/q25_sol.png", "caption": "解图 25　90° 弯管局部水头损失系数实验测定能量关系图"}
                ],
                "pitfalls": "由于 $L/d = 200$ 很大，沿程损失占总压差 $95\\%$ 左右，因此两组数据实测出的是 $200\\lambda + \\zeta = 6.321$ 这一固定组合，不能仅靠两个等价线性方程独立解出 $\\lambda$ 和 $\\zeta$；考场上遇到原卷漏印 $\\lambda$ 时，务必先写出严密关系式 $\\zeta = 6.321 - 200\\lambda$，再说明按常规管材 $\\lambda = 0.03$ 算得 $\\zeta \\approx 0.32$。",
                "chapter": 4,
                "kps": ["沿程与局部损失"],
                "method": "等径参考段消去沿程损失测局部阻力系数法",
                "difficulty": 3,
                "rubric": [
                    {"label": "对等径管段 A、B 列能量方程，正确建立测压管水头差与阻力系数关系 hw = (λL/d + ζ)v²/(2g)", "pts": 4},
                    {"label": "由两组体积流量数据准确求得 Q1、v1 ≈ 1.396 m/s 及 Q2、v2 ≈ 1.501 m/s", "pts": 4},
                    {"label": "算得两组总阻力系数 200λ + ζ = 6.323 与 6.318（均值 6.321），写出 ζ = 6.321 - 200λ", "pts": 4},
                    {"label": "指出阻力平方区取 λ = 0.03，解得 ζ1 ≈ 0.323、ζ2 ≈ 0.318 及均值 ζ ≈ 0.32", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2012-26",
                "year": 2012,
                "no": 26,
                "type": "calc",
                "score": 18,
                "title": "水平自由射流局部撞击光滑竖直平板偏转角度计算",
                "stem": "如图所示将一平板放置在水平面自由射流之中，并且垂直于射流的轴线，该平板截去射流流量的一部分 $Q_1$，射流的其余部分偏转一角度 $\\theta$。已知：$v = 30\\,\\mathrm{m/s}$，$Q = 36\\,\\mathrm{L/s}$，$Q_1 = 12\\,\\mathrm{L/s}$，现测得射流对平板的作用力为 $465.48\\,\\mathrm{kN}$（原卷误印，实应为 $456.48\\,\\mathrm{N}$），如不计摩擦力，试求偏转角度 $\\theta$ 值。",
                "note": "原卷将“$456.48\\,\\mathrm{N}$”误印为“$465.48\\,\\mathrm{kN}$”（百十位数字 5、6 颠倒且单位错写为 kN，因来流动量流率 $\\rho Q v$ 仅为 $1080\\,\\mathrm{N}$）。解析以光滑平板切向动量平衡给出严格精确解 $\\theta = 30^{\\circ}$（对应法向推力 $456.46\\,\\mathrm{N}$），同时给出直接代入 $465.48\\,\\mathrm{N}$ 的 $x$ 向动量对照值 $31.4^{\\circ}$。",
                "figures": [
                    {"src": "figures/q26_orig.png", "caption": "题 26 图　光滑竖直平板截流水平自由射流示意图"}
                ],
                "shortAnswer": "θ = 30°（由光滑平板切向无摩擦 Ry = 0 得 sinθ = Q1/Q2 = 12/24 = 0.5，且 x 向推力 Fx = 456.46 N；若按字面 465.48 N 代入 x 向动量方程得 θ ≈ 31.4°）。",
                "judgeAnswer": None,
                "answer": "偏转角度 $\\theta = 30^{\\circ}$（由光滑平板切向动量平衡 $R_y = 0$ 严格解得，并可校核法向作用力 $F_x = 456.46\\,\\mathrm{N}$，取 $\\cos 30^{\\circ}=0.866$ 时恰为 $456.48\\,\\mathrm{N}$；若保留原卷误印数字 $465.48\\,\\mathrm{N}$ 直接代入 $x$ 向动量方程，则得 $\\theta \\approx 31.4^{\\circ}$）。",
                "analysis": "1. 由连续性方程与伯努利方程确定分流流量与流速\n\n水平面内自由射流各出口均处于大气中（相对压强均为 $0$），不计摩阻水头损失与高差，由能量方程知各支射流流速相等：\n\n$$\nv_1 = v_2 = v = 30\\,\\mathrm{m/s}\n$$\n\n偏转射流 $2\\text{-}2$ 的流量为：\n\n$$\nQ_2 = Q - Q_1 = 36 - 12 = 24\\,\\mathrm{L/s} = 0.024\\,\\mathrm{m^3/s}\n$$\n\n2. 取控制体列水平面内 $y$ 方向（沿平板方向向上为正）动量方程\n\n由于平板竖直放置且光滑无摩擦，平板只能对水流施加垂直于板面的水平法向反力 $R_x$，在平行于板面的 $y$ 方向上外力合量为零（$R_y = 0$，见解图 26）。由 $y$ 方向恒定总流动量方程：\n\n$$\n0 = \\rho Q_2 v_2 \\sin\\theta + \\rho Q_1 (-v_1) - \\rho Q \\cdot 0\n$$\n\n因 $v_1 = v_2 = v$，消去 $\\rho v$ 即得：\n\n$$\n\\sin\\theta = \\frac{Q_1}{Q_2} = \\frac{12}{24} = 0.5 \\implies \\theta = 30^{\\circ}\n$$\n\n3. 用 $x$ 方向（沿来流方向向右为正）动量方程校核射流对平板的作用力\n\n设平板对控制体水流的水平向左反力为 $R_x$，列 $x$ 方向动量方程：\n\n$$\n-R_x = \\rho Q_2 (v_2 \\cos\\theta) + \\rho Q_1 \\cdot 0 - \\rho Q v\n$$\n\n故射流对平板的水平向右推力 $F_x = R_x$ 为：\n\n$$\nF_x = \\rho Q v - \\rho Q_2 v \\cos\\theta = 1000\\times 0.036\\times 30 - 1000\\times 0.024\\times 30\\cos\\theta = 1080 - 720\\cos\\theta\\,(\\mathrm{N})\n$$\n\n代入 $\\theta = 30^{\\circ}$ 校核：\n\n$$\nF_x = 1080 - 720\\times \\frac{\\sqrt{3}}{2} = 1080 - 623.54 = 456.46\\,\\mathrm{N}\n$$\n\n（若按手算近似 $\\cos 30^{\\circ} \\approx 0.866$，恰得 $1080 - 720\\times 0.866 = 456.48\\,\\mathrm{N}$！可见原卷所印“$465.48\\,\\mathrm{kN}$”系将“$456.48\\,\\mathrm{N}$”误印为数字颠倒且单位错写为 $\\mathrm{kN}$。若忽略 $y$ 向无摩擦条件而仅将单位修正后的字面数字 $465.48\\,\\mathrm{N}$ 代入 $x$ 向动量方程，则得 $\\cos\\theta = \\frac{1080 - 465.48}{720} = 0.8535 \\implies \\theta \\approx 31.4^{\\circ}$。）",
                "analysisFigures": [
                    {"src": "figures/q26_sol.png", "caption": "解图 26　光滑竖直平板截流水平自由射流控制体动量分析图"}
                ],
                "pitfalls": "本题最重要的物理洞察是“光滑平板无切向摩擦力 $\\implies R_y = 0$”，由此只需 $y$ 向动量方程即可直接避开原卷误印的力值而一步精准解出 $\\theta = 30^{\\circ}$！若用 $x$ 向动量方程直接代入 $465.48\\,\\mathrm{kN} = 465480\\,\\mathrm{N}$ 会立即算出 $|\\cos\\theta| > 600$ 的荒谬无解，此时应立刻识别出量级与印刷错误。",
                "chapter": 3,
                "kps": ["闸门与弯管动水总压力"],
                "method": "能量方程求流量+控制体动量方程求反力",
                "difficulty": 3,
                "rubric": [
                    {"label": "由连续性方程与能量方程确定 Q2 = Q - Q1 = 24 L/s 及自由射流等速条件 v1 = v2 = v = 30 m/s", "pts": 4},
                    {"label": "指出光滑平板不计摩擦时切向反力 Ry = 0，列出 y 向动量方程 0 = ρQ2v·sinθ - ρQ1v", "pts": 6},
                    {"label": "解得 sinθ = Q1/Q2 = 0.5 即偏转角 θ = 30°", "pts": 4},
                    {"label": "列 x 向动量方程 Fx = ρQv - ρQ2v·cosθ 校核推力为 456.46 N（并指出原卷 465.48 kN 印刷误差）", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2012-27",
                "year": 2012,
                "no": 27,
                "type": "calc",
                "score": 18,
                "title": "二维自由点涡速度场的连续性、无旋性与变形率判别",
                "stem": "已知平面速度场为：\n\n$$\nu_x = \\frac{ay}{x^2 + y^2}, \\qquad u_y = -\\frac{ax}{x^2 + y^2} \\qquad (a\\text{ 为非零常数})\n$$\n\n求解：\n\n（1）速度场描述的不可压缩液体流动是否可能；\n\n（2）如流动可能，判别运动是有旋还是无旋运动，流动是否有变形。",
                "note": "",
                "figures": [],
                "shortAnswer": "（1）除原点奇点 (0,0) 外处处满足不可压缩连续性方程，流动可能；（2）ωz = 0 为无旋运动（自由点涡）；存在非零线变形率 εxx = -εyy = -2axy/(x²+y²)² 与角变形率 εxy = a(x²-y²)/(x²+y²)²，故流动存在变形。",
                "judgeAnswer": None,
                "answer": "（1）在除原点 $(0,0)$ 奇点以外的整个平面内，满足不可压缩流体连续性方程 $\\frac{\\partial u_x}{\\partial x} + \\frac{\\partial u_y}{\\partial y} = 0$，故该不可压缩平面流动可能存在；\n\n（2）旋转角速度 $\\omega_z = 0$（且 $\\omega_x = \\omega_y = 0$），故为无旋运动（典型平面自由点涡）；线变形率 $\\varepsilon_{xx} = -\\varepsilon_{yy} = -\\frac{2axy}{(x^2+y^2)^2} \\neq 0$，角变形率 $\\varepsilon_{xy} = \\varepsilon_{yx} = \\frac{a(x^2-y^2)}{(x^2+y^2)^2} \\neq 0$，故流体微团既有线变形也有角变形。",
                "analysis": "（1）判别不可压缩流动是否可能（检验连续性微分方程）\n\n对 $x^2 + y^2 \\neq 0$ 的任意点，分别计算偏导数：\n\n$$\n\\frac{\\partial u_x}{\\partial x} = \\frac{0 - ay(2x)}{(x^2 + y^2)^2} = -\\frac{2axy}{(x^2 + y^2)^2}\n$$\n\n$$\n\\frac{\\partial u_y}{\\partial y} = \\frac{0 - (-ax)(2y)}{(x^2 + y^2)^2} = \\frac{2axy}{(x^2 + y^2)^2}\n$$\n\n代入平面不可压缩流体连续性方程：\n\n$$\n\\frac{\\partial u_x}{\\partial x} + \\frac{\\partial u_y}{\\partial y} = -\\frac{2axy}{(x^2 + y^2)^2} + \\frac{2axy}{(x^2 + y^2)^2} = 0\n$$\n\n连续性方程恒成立（除奇点 $(0,0)$ 外），因此该速度场描述的不可压缩平面流动是可能的。\n\n（2）判别有旋/无旋及流动变形情况\n\n先求交叉一阶偏导数：\n\n$$\n\\frac{\\partial u_x}{\\partial y} = \\frac{a(x^2 + y^2) - ay(2y)}{(x^2 + y^2)^2} = \\frac{a(x^2 - y^2)}{(x^2 + y^2)^2}\n$$\n\n$$\n\\frac{\\partial u_y}{\\partial x} = \\frac{-a(x^2 + y^2) - (-ax)(2x)}{(x^2 + y^2)^2} = \\frac{a(x^2 - y^2)}{(x^2 + y^2)^2}\n$$\n\n1. 旋转角速度判别：\n\n因平面流动 $u_z = 0$ 且 $u_x, u_y$ 不含 $z$，故 $\\omega_x = \\omega_y = 0$；绕 $z$ 轴旋转角速度为：\n\n$$\n\\omega_z = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} - \\frac{\\partial u_x}{\\partial y}\\right) = \\frac{1}{2}\\left[\\frac{a(x^2 - y^2)}{(x^2 + y^2)^2} - \\frac{a(x^2 - y^2)}{(x^2 + y^2)^2}\\right] = 0\n$$\n\n因此除原点奇点外，该运动处处为无旋运动（即典型自由点涡，切向速度 $u_\\theta = -a/r$）。\n\n2. 流动变形（线变形率与角变形率）判别：\n\n- 线变形率：\n\n$$\n\\varepsilon_{xx} = \\frac{\\partial u_x}{\\partial x} = -\\frac{2axy}{(x^2 + y^2)^2}, \\qquad \\varepsilon_{yy} = \\frac{\\partial u_y}{\\partial y} = \\frac{2axy}{(x^2 + y^2)^2}, \\qquad \\varepsilon_{zz} = 0\n$$\n\n- 角变形率：\n\n$$\n\\varepsilon_{xy} = \\varepsilon_{yx} = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} + \\frac{\\partial u_x}{\\partial y}\\right) = \\frac{a(x^2 - y^2)}{(x^2 + y^2)^2}, \\qquad \\varepsilon_{yz} = \\varepsilon_{zx} = 0\n$$\n\n因 $\\varepsilon_{xx}$、$\\varepsilon_{yy}$ 及 $\\varepsilon_{xy}$ 均不恒为零（$a \\neq 0$），故该流动虽为无旋运动，但流体微团在绕圆周公转过程中发生显著的线变形与剪切角变形（流动存在变形）。",
                "analysisFigures": [],
                "pitfalls": "本题是检验“无旋 ≠ 无变形”的绝佳经典例题！自由点涡流线虽为同心圆，但因流速随半径成反比（$u_\\theta \\propto 1/r$），流体微团一边发生纯剪切变形（$\\varepsilon_{xy} \\neq 0$），一边保持两对角线平均角速度为零（$\\omega_z = 0$），切勿误认为圆周运动就是有旋运动或无旋就无变形。",
                "chapter": 5,
                "kps": ["流函数与势函数"],
                "method": "连续性与无旋性判据及流函数求单宽流量法",
                "difficulty": 3,
                "rubric": [
                    {"label": "准确求出 ∂ux/∂x 与 ∂uy/∂y，验证连续性方程 ∂ux/∂x + ∂uy/∂y = 0（原点外），判定流动可能", "pts": 6},
                    {"label": "准确求出 ∂ux/∂y 与 ∂uy/∂x，算得 ωz = 0（且 ωx = ωy = 0），判定为无旋运动", "pts": 6},
                    {"label": "分别给出非零线变形率 εxx, εyy 与角变形率 εxy 表达式，得出流动存在线变形和角变形的结论", "pts": 6}
                ]
            }
        ]
    }


# ==============================================================================
# WRITE STANDARDIZED PACKS + WEB-READY JSON & WEBP ASSETS
# ==============================================================================

def write_year_outputs(paper: dict, pack_dir: Path) -> None:
    year = int(paper["year"])
    pack_dir.mkdir(parents=True, exist_ok=True)
    src_fig_dir = pack_dir / "figures"

    # 1. Standardized pack JSON (`扬州大学已整理数据/<year>/<year>.json`)
    pack_json = pack_dir / f"{year}.json"
    pack_json.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[PACK] Wrote {pack_json} ({len(paper['questions'])} questions, {sum(q['score'] for q in paper['questions'])} pts)")

    # 2. Convert PNG figures -> WebP (`web/public/data/yzu-849/figures/<year>/*.webp`, PIL quality=90, method=5)
    web_fig_dir = WEB_COURSE_DIR / "figures" / str(year)
    web_fig_dir.mkdir(parents=True, exist_ok=True)
    web_paper = copy.deepcopy(paper)

    fig_count = 0
    for q in web_paper["questions"]:
        for key in ("figures", "analysisFigures"):
            new_list = []
            for fig in q.get(key, []):
                raw_name = Path(fig["src"]).name
                src_png = src_fig_dir / raw_name
                if not src_png.exists():
                    raise FileNotFoundError(f"Missing source figure: {src_png}")
                webp_name = f"{Path(raw_name).stem}.webp"
                dest_webp = web_fig_dir / webp_name
                with Image.open(src_png) as im:
                    if im.mode not in ("RGB", "RGBA"):
                        im = im.convert("RGBA")
                    im.save(dest_webp, format="WEBP", quality=90, method=5)
                new_list.append({
                    "src": f"figures/{year}/{webp_name}",
                    "caption": fig["caption"]
                })
                fig_count += 1
            q[key] = new_list

    # 3. Web-ready JSON (`web/public/data/yzu-849/<year>.json`)
    web_json = WEB_COURSE_DIR / f"{year}.json"
    web_json.write_text(json.dumps(web_paper, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[WEB]  Wrote {web_json} ({len(web_paper['questions'])} questions, {fig_count} WebP figures)")


def main() -> None:
    pack_2013 = PACK_ROOT / "2013"
    build_2013_figures(pack_2013 / "figures")
    paper_2013 = build_2013_paper()
    write_year_outputs(paper_2013, pack_2013)

    pack_2012 = PACK_ROOT / "2012"
    build_2012_figures(pack_2012 / "figures")
    paper_2012 = build_2012_paper()
    write_year_outputs(paper_2012, pack_2012)


if __name__ == "__main__":
    main()
