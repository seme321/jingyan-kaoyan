# -*- coding: utf-8 -*-
"""
Generate stem figures (q*_orig.png), solution schematic figures (q*_sol.png),
standardized exam packs in `扬州大学已整理数据/{2023,2022}/`, and web-ready JSON + WebP
assets in `web/public/data/yzu-849/` for Yangzhou University 849 Hydraulics (2023 & 2022).
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


def trim_and_pad(img: Image.Image, pad: int = 16, thresh: int = 225, bg_clean: int = 238) -> Image.Image:
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
# 2023 STEM FIGURES (300 DPI crop from native PDF) & SOLUTION DIAGRAMS
# ==============================================================================

def build_2023_figures(fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(RAW_DIR / "849-水力学（水）2023.pdf")
    crops = [
        ("q03_orig.png", 0, (75, 376, 302, 463)),
        ("q07_orig.png", 0, (328, 313, 499, 463)),
        ("q08_orig.png", 1, (70, 98, 264, 234.8)),   # y0=98 excludes top page border line
        ("q09_orig.png", 1, (328, 117, 498, 234.8)),
        ("q10_orig.png", 1, (58, 353, 282, 541.2)),
        ("q11_orig.png", 1, (287, 394, 529, 541.2)),
    ]
    for fname, pno, rect in crops:
        pix = doc[pno].get_pixmap(dpi=300, clip=pymupdf.Rect(*rect))
        im = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        out = trim_and_pad(im, pad=16, thresh=230, bg_clean=242)
        out.save(fig_dir / fname)

    draw_2023_q03_sol(fig_dir / "q03_sol.png")
    draw_2023_q07_sol(fig_dir / "q07_sol.png")
    draw_2023_q08_sol(fig_dir / "q08_sol.png")
    draw_2023_q10_sol(fig_dir / "q10_sol.png")
    draw_2023_q11_sol(fig_dir / "q11_sol.png")


def draw_2023_q03_sol(out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.8, 4.3))
    fig.patch.set_facecolor("white")

    # Tank on left
    ax.plot([0.5, 0.5, 2.0, 2.0], [3.6, 0.7, 0.7, 1.15], color="#0f172a", lw=2.0)
    ax.plot([2.0, 2.0], [1.35, 3.6], color="#0f172a", lw=2.0)
    ax.add_patch(patches.Rectangle((0.52, 0.72), 1.46, 2.48, facecolor="#bae6fd", alpha=0.55))
    ax.plot([0.5, 2.0], [3.20, 3.20], color="#0284c7", lw=2.0)
    ax.text(1.25, 3.32, "恒定水位", fontsize=9.5, ha="center", color="#0369a1", fontweight="bold")

    # Pipe geometry: chamber -> contraction at A -> B -> C -> rise to D -> E -> drop to F
    # Pipe centerline y=1.25 for A,B,C; rises at x=5.3 to y=2.35 for D,E; drops at x=7.4 to y=1.05 (F)
    pipe_pts_x = [2.0, 2.8, 2.8, 3.8, 3.8, 5.2, 5.2, 7.4, 7.4]
    ax.plot([2.0, 2.8], [1.35, 1.35], color="#0f172a", lw=1.8)
    ax.plot([2.0, 2.8], [1.15, 1.15], color="#0f172a", lw=1.8)
    ax.add_patch(patches.Rectangle((2.8, 1.05), 1.0, 0.40, facecolor="#e0f2fe", edgecolor="#0f172a", lw=1.8))
    # Narrow pipe from x=3.8 to 5.2 at y=1.25 (half-width 0.09)
    ax.add_patch(patches.Rectangle((3.8, 1.16), 1.4, 0.18, facecolor="#e0f2fe", edgecolor="none"))
    ax.plot([3.8, 5.15], [1.34, 1.34], color="#0f172a", lw=1.8)
    ax.plot([3.8, 5.33], [1.16, 1.16], color="#0f172a", lw=1.8)
    # Vertical rise x=5.24 (from 1.25 to 2.35)
    ax.add_patch(patches.Rectangle((5.15, 1.16), 0.18, 1.28, facecolor="#e0f2fe", edgecolor="none"))
    ax.plot([5.15, 5.15], [1.34, 2.44], color="#0f172a", lw=1.8)
    ax.plot([5.33, 5.33], [1.16, 2.26], color="#0f172a", lw=1.8)
    # Top siphon horizontal segment D-E (x=5.15..7.45, y=2.35)
    ax.add_patch(patches.Rectangle((5.15, 2.26), 2.30, 0.18, facecolor="#e0f2fe", edgecolor="none"))
    ax.plot([5.15, 7.45], [2.44, 2.44], color="#0f172a", lw=1.8)
    ax.plot([5.33, 7.27], [2.26, 2.26], color="#0f172a", lw=1.8)
    # Downward outlet leg to F (x=7.36, y=2.35 down to 1.10)
    ax.add_patch(patches.Rectangle((7.27, 1.10), 0.18, 1.25, facecolor="#e0f2fe", edgecolor="none"))
    ax.plot([7.27, 7.27], [2.26, 1.10], color="#0f172a", lw=1.8)
    ax.plot([7.45, 7.45], [2.44, 1.10], color="#0f172a", lw=1.8)
    ax.annotate("", xy=(7.36, 0.65), xytext=(7.36, 1.10),
                arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.0))

    # Points A, B, C, D, E, F
    pts = [
        ("A", 3.92, 1.25, (3.92, 1.48)),
        ("B", 4.48, 1.25, (4.48, 1.48)),
        ("C", 5.05, 1.25, (5.00, 1.48)),
        ("D", 5.85, 2.35, (5.85, 2.56)),
        ("E", 6.95, 2.35, (6.95, 2.56)),
        ("F", 7.36, 1.12, (7.64, 1.08)),
    ]
    for lbl, px, py, (tx, ty) in pts:
        ax.scatter([px], [py], color="#0f172a", s=22, zorder=6)
        ax.text(tx, ty, f"${lbl}$", fontsize=11, fontweight="bold", ha="center", color="#0f172a")

    # Total head line (E.G.L.) and Piezometric head line (H.G.L.)
    egl_x = [2.0, 2.8, 3.8, 3.92, 4.48, 5.05, 5.85, 6.95, 7.36]
    egl_y = [3.20, 3.08, 2.95, 2.75, 2.62, 2.52, 2.28, 2.02, 1.72]
    # H.G.L. dips sharply at vena contracta A (local acceleration vc > vB), recovers at B, drops below pipe at E!
    hgl_x = [2.0, 2.8, 3.72, 3.92, 4.48, 5.05, 5.85, 6.95, 7.36]
    hgl_y = [3.02, 2.90, 2.86, 1.82, 2.02, 1.92, 1.68, 1.42, 1.12]

    ax.plot(egl_x, egl_y, color="#dc2626", lw=2.0, label="总水头线 (E.G.L.)")
    ax.plot(hgl_x, hgl_y, color="#0284c7", ls="--", lw=2.0, label="测压管水头线 (H.G.L.)")

    # Highlight annotations
    ax.annotate("收缩断面增速降压\n" + r"$p_A < p_B$ 可成立", xy=(3.92, 1.82), xytext=(2.85, 2.08),
                fontsize=8.8, color="#0369a1", ha="center",
                arrowprops=dict(arrowstyle="->", color="#0284c7", lw=1.2))
    ax.annotate("虹吸管顶段负压\n" + r"$p_E < 0 = p_F$ 可成立", xy=(6.95, 1.42), xytext=(6.15, 0.78),
                fontsize=8.8, color="#dc2626", ha="center",
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=1.2))
    ax.text(5.75, 3.15, r"$D$ 高于 $C$ 且顺流有损 $\Rightarrow p_C > p_D$ 恒成立",
            fontsize=9.2, color="#7c2d12", bbox=dict(boxstyle="round,pad=0.25", fc="#ffedd5", ec="#ea580c", lw=1.0))

    ax.legend(loc="upper left", bbox_to_anchor=(0.24, 0.99), frameon=True, fontsize=9)
    ax.set_xlim(0.3, 8.1)
    ax.set_ylim(0.5, 3.75)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2023_q07_sol(out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.8, 4.8))
    fig.patch.set_facecolor("white")

    # Pressure vessel
    ax.plot([2.0, 2.0, 4.6, 4.6], [4.2, 0.6, 0.6, 4.2], color="#0f172a", lw=2.2)
    theta = np.linspace(0.22 * np.pi, 0.78 * np.pi, 60)
    ax.plot(3.3 + 1.52 * np.cos(theta), 3.35 + 1.12 * np.sin(theta), color="#0f172a", lw=2.2)

    # Water inside vessel (from y=0.6 to y=3.35)
    ax.add_patch(patches.Rectangle((2.02, 0.62), 2.56, 2.73, facecolor="#bae6fd", alpha=0.55))
    ax.plot([2.0, 4.6], [3.35, 3.35], color="#0284c7", lw=2.0)
    ax.text(3.3, 3.75, r"气体相对压强 $p_0 = \rho_{Hg}\,g\,h_1$", fontsize=9.8, ha="center", color="#0f172a")
    ax.text(3.3, 2.15, "水", fontsize=11, ha="center", color="#0369a1", fontweight="bold")

    # Right U-tube (gas manometer)
    # Tap at y=3.60; inner leg x=5.1, outer leg x=5.6; bottom at y=2.55
    # Inner Hg interface y=2.85 ( plane 1-1 ); outer Hg meniscus y=3.20 (h1=2.0 cm)
    ax.plot([4.6, 5.18, 5.18, 5.52, 5.52], [3.68, 3.68, 2.65, 2.65, 3.68], color="#0f172a", lw=1.6)
    ax.plot([4.6, 5.02, 5.02, 5.68, 5.68], [3.54, 3.54, 2.48, 2.48, 3.68], color="#0f172a", lw=1.6)
    # Mercury fill in right U-tube
    hg_r = patches.Polygon([[5.03, 2.85], [5.17, 2.85], [5.17, 2.64], [5.53, 2.64], [5.53, 3.22], [5.67, 3.22], [5.67, 2.49], [5.03, 2.49]],
                           closed=True, facecolor="#475569", edgecolor="#0f172a", lw=1.0, zorder=4)
    ax.add_patch(hg_r)
    ax.plot([4.90, 5.95], [2.85, 2.85], color="#dc2626", ls="--", lw=1.4, zorder=5)
    ax.text(5.98, 2.85, "等压面 1—1", fontsize=9, va="center", color="#dc2626")
    ax.annotate("", xy=(5.82, 3.22), xytext=(5.82, 2.85), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.2))
    ax.text(5.90, 3.05, r"$h_1=2\,\mathrm{cm}$", fontsize=9, va="center", color="#0f172a")

    # Left U-tube (bottom water manometer)
    # Tap at y=1.55; inner leg x=1.50, outer leg x=0.98; inner water-Hg interface y=1.05 (plane 2-2); outer Hg y=1.65 (h3=22.0 cm)
    ax.plot([2.0, 1.42, 1.42, 1.06, 1.06], [1.62, 1.62, 0.72, 0.72, 1.92], color="#0f172a", lw=1.6)
    ax.plot([2.0, 1.58, 1.58, 0.90, 0.90], [1.48, 1.48, 0.56, 0.56, 1.92], color="#0f172a", lw=1.6)
    # Water in left inner leg from tap down to y=1.05
    ax.add_patch(patches.Polygon([[2.0, 1.61], [1.43, 1.61], [1.43, 1.05], [1.57, 1.05], [1.57, 1.49], [2.0, 1.49]],
                                 closed=True, facecolor="#bae6fd", alpha=0.7, zorder=3))
    hg_l = patches.Polygon([[1.43, 1.05], [1.57, 1.05], [1.57, 0.57], [0.91, 0.57], [0.91, 1.65], [1.05, 1.65], [1.05, 0.71], [1.43, 0.71]],
                           closed=True, facecolor="#475569", edgecolor="#0f172a", lw=1.0, zorder=4)
    ax.add_patch(hg_l)
    ax.plot([0.65, 2.75], [1.05, 1.05], color="#dc2626", ls="--", lw=1.4, zorder=5)
    ax.text(0.62, 1.05, "等压面 2—2", fontsize=9, ha="right", va="center", color="#dc2626")

    ax.annotate("", xy=(0.74, 1.65), xytext=(0.74, 1.05), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.2))
    ax.text(0.68, 1.35, r"$h_3=22\,\mathrm{cm}$", fontsize=9, ha="right", va="center", color="#0f172a")

    # Dimension H and h2 inside tank
    ax.plot([2.45, 2.75], [1.55, 1.55], color="#334155", lw=1.0)
    ax.annotate("", xy=(2.60, 3.35), xytext=(2.60, 1.55), arrowprops=dict(arrowstyle="<->", color="#0284c7", lw=1.5))
    ax.text(2.68, 2.45, r"$H=248\,\mathrm{cm}$", fontsize=9.8, va="center", color="#0369a1", fontweight="bold")
    ax.annotate("", xy=(2.60, 1.55), xytext=(2.60, 1.05), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.3))
    ax.text(2.68, 1.30, r"$h_2=24\,\mathrm{cm}$", fontsize=9.2, va="center", color="#334155")

    ax.set_xlim(-0.25, 6.85)
    ax.set_ylim(0.35, 4.65)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2023_q08_sol(out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    fig.patch.set_facecolor("white")

    # Scale: 1 unit = 1 m. Dam base: upstream toe x=0, heel kink x=4, crest left x=4, crest right x=6, downstream kink (y=24) x=6, downstream toe x=18
    dam_xy = [[0, 0], [4, 8], [4, 28], [6, 28], [6, 24], [18, 0]]
    ax.add_patch(patches.Polygon(dam_xy, closed=True, facecolor="#e2e8f0", edgecolor="#0f172a", lw=2.0, zorder=4))

    # Upstream real pressure body Vz1 (x in [0, 4], y from sloped face to 26)
    vz1_xy = [[0, 0], [4, 8], [4, 26], [0, 26]]
    ax.add_patch(patches.Polygon(vz1_xy, closed=True, facecolor="#bae6fd", edgecolor="#0284c7", lw=1.5, hatch="///", alpha=0.65, zorder=3))
    ax.plot([-9, 4], [26, 26], color="#0284c7", lw=1.8)

    # Downstream real pressure body Vz2 (x in [15, 18], y from sloped face to 6)
    vz2_xy = [[15, 6], [18, 0], [18, 6]]
    ax.add_patch(patches.Polygon(vz2_xy, closed=True, facecolor="#bae6fd", edgecolor="#0284c7", lw=1.5, hatch="\\\\\\", alpha=0.65, zorder=3))
    ax.plot([15, 24], [6, 6], color="#0284c7", lw=1.8)

    # Upstream horizontal hydrostatic pressure triangle at x = -8.5 .. -2.0
    ax.add_patch(patches.Polygon([[-2.0, 0], [-8.5, 0], [-2.0, 26]], closed=True,
                                 facecolor="#fde68a", edgecolor="#d97706", lw=1.4, alpha=0.65))
    ax.annotate("", xy=(-2.0, 8.67), xytext=(-8.2, 8.67), arrowprops=dict(arrowstyle="->", color="#b45309", lw=2.3))
    ax.text(-5.5, 12.2, "上游水平推力\n" + r"$P_{x1}=3312.4\,\mathrm{kN}$", fontsize=9.2, ha="center", color="#92400e", fontweight="bold")

    # Downstream horizontal hydrostatic pressure triangle at x = 19.5 .. 22.0
    ax.add_patch(patches.Polygon([[19.5, 0], [22.2, 0], [19.5, 6]], closed=True,
                                 facecolor="#fde68a", edgecolor="#d97706", lw=1.4, alpha=0.65))
    ax.annotate("", xy=(19.5, 2.0), xytext=(23.2, 2.0), arrowprops=dict(arrowstyle="->", color="#b45309", lw=2.0))
    ax.text(22.5, 9.2, "下游有水时水平推力\n" + r"$P_{x2}=176.4\,\mathrm{kN}$", fontsize=9.0, ha="center", color="#92400e")

    # Vertical pressure body arrows
    ax.annotate("", xy=(2.0, 11.0), xytext=(2.0, 20.0), arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.3), zorder=6)
    ax.text(-0.3, 28.0, r"上游实压力体 $V_{z1}=88\,\mathrm{m^3}$" + "\n" + r"$P_{z1}=862.4\,\mathrm{kN}$（向下）",
            fontsize=9.2, ha="center", color="#b91c1c", fontweight="bold")

    ax.annotate("", xy=(16.8, 2.5), xytext=(16.8, 11.5), arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.1), zorder=6)
    ax.text(18.5, 14.2, r"下游实压力体 $V_{z2}=9\,\mathrm{m^3}$" + "\n" + r"$P_{z2}=88.2\,\mathrm{kN}$（向下）",
            fontsize=9.0, ha="center", color="#b91c1c")

    # Ground line
    ax.plot([-9.5, 25.5], [0, 0], color="#0f172a", lw=2.4)
    ax.text(0, -2.3, r"$4\,\mathrm{m}$", fontsize=9.2, ha="left", color="#334155")
    ax.text(12, -2.3, r"$12\,\mathrm{m}$（水下水平投影 $3\,\mathrm{m}$）", fontsize=9.2, ha="center", color="#334155")

    ax.set_xlim(-10.0, 26.5)
    ax.set_ylim(-3.8, 31.5)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2023_q10_sol(out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 4.3))
    fig.patch.set_facecolor("white")

    # Schematic horizontal positions: 0-0 tank (x=0.8), pump 1-2 (x=3.0), 3-3 upper tank (x=6.8)
    ax.add_patch(patches.Rectangle((0.35, 0.3), 1.05, 0.5, facecolor="#bae6fd", edgecolor="#0f172a", lw=1.6))
    ax.text(0.68, 0.92, r"低水池 $z=0$", fontsize=9.0, ha="center", color="#0369a1")

    ax.add_patch(patches.Rectangle((6.4, 3.05), 1.3, 0.65, facecolor="#bae6fd", alpha=0.6))
    ax.plot([6.4, 6.4, 7.7, 7.7], [3.85, 3.05, 3.05, 3.85], color="#0f172a", lw=1.8)
    ax.plot([6.4, 7.7], [3.45, 3.45], color="#0284c7", lw=1.8)
    ax.text(7.05, 3.55, r"高水池 $z_0=20\,\mathrm{m}$", fontsize=9.2, ha="center", color="#0369a1")

    # Suction & discharge pipes + pump circle at (3.0, 1.35)
    ax.plot([1.22, 1.22, 2.82], [0.55, 1.35, 1.35], color="#334155", lw=3.0)
    ax.plot([3.18, 5.5, 6.4], [1.35, 3.20, 3.20], color="#334155", lw=2.6)
    pump = patches.Circle((3.0, 1.35), 0.20, facecolor="#fef08a", edgecolor="#0f172a", lw=2.0, zorder=6)
    ax.add_patch(pump)
    ax.text(3.0, 1.35, "泵", fontsize=9.5, ha="center", va="center", fontweight="bold", zorder=7)
    ax.text(3.05, 0.92, r"$h_s=3\,\mathrm{m}$", fontsize=9.0, ha="center", color="#334155")

    # Energy grade line (E.G.L.)
    ax.plot([0.95, 2.82], [0.80, 0.64], color="#dc2626", lw=2.0)
    ax.plot([2.82, 3.18], [0.64, 3.82], color="#16a34a", lw=2.4, ls="-")
    ax.plot([3.18, 6.40], [3.82, 3.45], color="#dc2626", lw=2.0, label="总水头线 (E.G.L.)")
    ax.axhline(0.80, xmin=0.05, xmax=0.45, color="#94a3b8", ls=":", lw=1.2)

    # Annotations for H, p2/rg, hw2
    ax.annotate("", xy=(2.55, 3.82), xytext=(2.55, 0.64),
                arrowprops=dict(arrowstyle="<->", color="#16a34a", lw=1.8))
    ax.text(2.45, 2.25, "水泵扬程\n" + r"$H = z_0 + h_{w1} + h_{w2}$" + "\n" + r"$\approx 21.62\,\mathrm{m}$",
            fontsize=9.3, ha="right", va="center", color="#15803d", fontweight="bold")

    ax.annotate("", xy=(3.42, 3.80), xytext=(3.42, 1.35),
                arrowprops=dict(arrowstyle="<->", color="#0284c7", lw=1.4))
    ax.text(3.52, 3.12, r"$\dfrac{p_2}{\rho g}+\dfrac{v_2^2}{2g}\approx 18.45\,\mathrm{m}$",
            fontsize=9.0, va="center", color="#0369a1")

    ax.annotate("", xy=(6.15, 3.82), xytext=(6.15, 3.45),
                arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.4))
    ax.text(6.05, 3.92, r"$h_{w2}\approx 1.45\,\mathrm{m}$", fontsize=9.0, ha="right", color="#dc2626")

    ax.legend(loc="lower right", frameon=True, fontsize=9.2)
    ax.set_xlim(0.2, 8.0)
    ax.set_ylim(0.1, 4.25)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2023_q11_sol(out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.8, 4.6))
    fig.patch.set_facecolor("white")

    th = np.radians(30.0)
    ex = np.array([np.cos(th), np.sin(th)])
    ez = np.array([-np.sin(th), np.cos(th)])
    c0 = np.array([1.6, 1.2])
    L = 3.1
    c1 = c0
    c2 = c0 + L * ex

    # Conical reducer control volume polygon
    r1, r2 = 0.52, 0.26
    poly_cv = [c1 - r1 * ez, c2 - r2 * ez, c2 + r2 * ez, c1 + r1 * ez]
    ax.add_patch(patches.Polygon(poly_cv, closed=True, facecolor="#bae6fd", edgecolor="#0f172a", lw=2.0, alpha=0.75))

    p_start = c1 - 0.8 * ex
    p_end = c2 + 1.0 * ex
    ax.plot([p_start[0], p_end[0]], [p_start[1], p_end[1]], color="#475569", ls="-.", lw=1.2)

    # Axes indicator shifted right so P2 label stays completely clear
    orig_ax = np.array([6.05, 3.20])
    ax.annotate("", xy=orig_ax + 0.78 * ex, xytext=orig_ax, arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.6))
    ax.annotate("", xy=orig_ax + 0.78 * ez, xytext=orig_ax, arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.6))
    ax.text(*(orig_ax + 0.86 * ex), r"$x$", fontsize=11, fontweight="bold")
    ax.text(*(orig_ax + 0.86 * ez), r"$z$", fontsize=11, fontweight="bold")

    # Force P1 at section 1-1 (+x)
    p1_tail = c1 - 1.15 * ex
    ax.annotate("", xy=c1, xytext=p1_tail, arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.4))
    ax.text(p1_tail[0] - 0.05, p1_tail[1] + 0.35, r"$P_1 = 15.39\,\mathrm{kN}$", fontsize=9.5, color="#0369a1", ha="center", fontweight="bold")

    # Force P2 at section 2-2 (-x)
    p2_tail = c2 + 0.95 * ex
    ax.annotate("", xy=c2, xytext=p2_tail, arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.2))
    ax.text(p2_tail[0] + 0.05, p2_tail[1] - 0.34, r"$P_2 = 3.40\,\mathrm{kN}$", fontsize=9.5, color="#0369a1", ha="center", fontweight="bold")

    # Gravity G at center cm (vertically downward)
    cm = 0.5 * (c1 + c2)
    ax.annotate("", xy=(cm[0], cm[1] - 1.25), xytext=cm, arrowprops=dict(arrowstyle="->", color="#ea580c", lw=2.2))
    ax.text(cm[0] + 0.14, cm[1] - 1.12, r"$G = 2.00\,\mathrm{kN}$" + "\n" + r"($G\sin 30^{\circ}=1.00\,\mathrm{kN}$)",
            fontsize=9.2, color="#c2410c", va="center")

    # Pipe reaction on water: Rx (-x) and Rz (+z)
    rx_tip = cm - 0.92 * ex + 0.16 * ez
    rx_tail = cm + 0.16 * ez
    ax.annotate("", xy=rx_tip, xytext=rx_tail, arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.3))
    ax.text(1.42, 2.28, r"管壁对水 $R_x=10.89\,\mathrm{kN}$", fontsize=9.2, color="#dc2626", ha="center")

    rz_tip = cm + 1.08 * ez
    ax.annotate("", xy=rz_tip, xytext=cm, arrowprops=dict(arrowstyle="->", color="#16a34a", lw=2.3))
    ax.text(rz_tip[0] - 0.05, rz_tip[1] + 0.14, r"管壁对水 $R_z=1.73\,\mathrm{kN}$", fontsize=9.2, color="#15803d", ha="center")

    # Summary box for anchor block thrust R' = -R
    ax.text(0.42, 3.68, "镇墩所受水流推力（牛顿第三定律）：\n"
            + r"$R_x^{\prime} = 10.89\,\mathrm{kN}$（沿 $+x$ 斜向上）" + "\n"
            + r"$R_z^{\prime} = 1.73\,\mathrm{kN}$（沿 $-z$ 垂直管轴斜向下）",
            fontsize=9.2, color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.35", fc="#f8fafc", ec="#94a3b8", lw=1.1))

    # Horizontal ground line showing theta = 30 deg
    ax.plot([0.5, 3.2], [0.74, 0.74], color="#334155", lw=1.4)
    ax.text(1.35, 0.82, r"$\theta=30^{\circ}$", fontsize=9.5, color="#334155")

    ax.set_xlim(0.2, 7.15)
    ax.set_ylim(0.45, 4.45)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


# ==============================================================================
# 2022 STEM FIGURES & SOLUTION DIAGRAMS
# ==============================================================================

def build_2022_figures(fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(RAW_DIR / "849-水力学（水）2022.pdf")
    pix1 = doc[0].get_pixmap(dpi=300)
    im1 = Image.frombytes("RGB", [pix1.width, pix1.height], pix1.samples)

    # q09_orig and q10_orig are clean high-contrast 300 DPI crops from Page 1
    out09 = trim_and_pad(im1.crop((430, 2550, 1250, 3090)), pad=16, thresh=195, bg_clean=228)
    out09.save(fig_dir / "q09_orig.png")
    out10 = trim_and_pad(im1.crop((1350, 2550, 2120, 3090)), pad=16, thresh=195, bg_clean=228)
    out10.save(fig_dir / "q10_orig.png")

    # q11_orig and q14_orig had faint broken strokes in the PDF scan -> redraw cleanly in matplotlib!
    draw_2022_q11_orig(fig_dir / "q11_orig.png")
    draw_2022_q14_orig(fig_dir / "q14_orig.png")

    # Solution figures for 2022
    draw_2022_q02_sol(fig_dir / "q02_sol.png")
    draw_2022_q09_sol(fig_dir / "q09_sol.png")
    draw_2022_q11_sol(fig_dir / "q11_sol.png")
    draw_2022_q14_sol(fig_dir / "q14_sol.png")
    draw_2022_q15_sol(fig_dir / "q15_sol.png")


def draw_2022_q11_orig(out_path: Path) -> None:
    """Clean engineering redraw of 题11图 (horizontal symmetric Y-bifurcation)."""
    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    fig.patch.set_facecolor("white")

    th = np.radians(30.0)
    # Main pipe: x in [0.9, 3.5], half-width r1 = 0.36, centered at y=0
    r1 = 0.36
    r2 = 0.24
    # Geometry intersections:
    # Outer wall y = +r1 meets upper branch top wall: (x - 3.5)*sin(th) - (y - 0)*cos(th) = -r2
    # Let centerline branch vertex be at (3.6, 0). Upper branch unit vector eu=(cos30, sin30), normal nu=(-sin30, cos30)
    vtx = np.array([3.6, 0.0])
    eu = np.array([np.cos(th), np.sin(th)])
    nu = np.array([-np.sin(th), np.cos(th)])
    ed = np.array([np.cos(th), -np.sin(th)])
    nd = np.array([np.sin(th), np.cos(th)])  # pointing up-right into upper wedge

    # Upper outer corner where y = r1 meets vtx + t*eu + r2*nu: r1 = t*sin30 + r2*cos30 => t = (r1 - r2*cos30)/sin30
    t_out = (r1 - r2 * np.cos(th)) / np.sin(th)
    p_up_in = vtx + t_out * eu + r2 * nu  # (x_kink, r1)
    L_br = 2.55
    p_up_top_end = vtx + L_br * eu + r2 * nu
    p_up_bot_end = vtx + L_br * eu - r2 * nu
    # Inner crotch where y = 0 meets vtx + t_in*eu - r2*nu: 0 = t_in*sin30 - r2*cos30 => t_in = r2*cot30
    t_in = r2 * np.cos(th) / np.sin(th)
    p_crotch = vtx + t_in * eu - r2 * nu  # (x_crotch, 0)

    # Main pipe walls
    ax.plot([1.0, p_up_in[0]], [r1, r1], color="#0f172a", lw=2.0)
    ax.plot([1.0, p_up_in[0]], [-r1, -r1], color="#0f172a", lw=2.0)
    # Left break S-curve
    ys_s = np.linspace(-r1, r1, 80)
    ax.plot(1.0 + 0.06 * np.sin(2 * np.pi * ys_s / (2 * r1)), ys_s, color="#0f172a", lw=1.8)
    ax.plot(1.0 - 0.06 * np.sin(2 * np.pi * ys_s[:40] / (2 * r1)), ys_s[:40], color="#0f172a", lw=1.4)

    # Upper & lower branch walls
    ax.plot([p_up_in[0], p_up_top_end[0]], [p_up_in[1], p_up_top_end[1]], color="#0f172a", lw=2.0)
    ax.plot([p_crotch[0], p_up_bot_end[0]], [0.0, p_up_bot_end[1]], color="#0f172a", lw=2.0)
    ax.plot([p_up_in[0], p_up_top_end[0]], [-p_up_in[1], -p_up_top_end[1]], color="#0f172a", lw=2.0)
    ax.plot([p_crotch[0], p_up_bot_end[0]], [0.0, -p_up_bot_end[1]], color="#0f172a", lw=2.0)
    ax.plot([p_up_top_end[0], p_up_bot_end[0]], [p_up_top_end[1], p_up_bot_end[1]], color="#0f172a", lw=1.8)
    ax.plot([p_up_top_end[0], p_up_bot_end[0]], [-p_up_top_end[1], -p_up_bot_end[1]], color="#0f172a", lw=1.8)

    # Centerlines
    ax.plot([0.85, 4.95], [0.0, 0.0], color="#334155", ls="-.", lw=1.2)
    ax.plot([vtx[0], (vtx + (L_br + 0.15) * eu)[0]], [0.0, (vtx + (L_br + 0.15) * eu)[1]], color="#334155", ls="-.", lw=1.2)
    ax.plot([vtx[0], (vtx + (L_br + 0.15) * ed)[0]], [0.0, (vtx + (L_br + 0.15) * ed)[1]], color="#334155", ls="-.", lw=1.2)

    # Flow arrows
    ax.annotate("", xy=(1.55, 0.0), xytext=(0.65, 0.0), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.8))
    ax.text(0.58, 0.0, r"$q_V$", fontsize=13, ha="right", va="center")
    p_arr_u1 = vtx + (L_br + 0.02) * eu
    p_arr_u2 = vtx + (L_br + 0.55) * eu
    ax.annotate("", xy=p_arr_u2, xytext=p_arr_u1, arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.8))
    ax.annotate("", xy=(p_arr_u2[0], -p_arr_u2[1]), xytext=(p_arr_u1[0], -p_arr_u1[1]), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.8))

    # Pressure gauge pM on main pipe
    gx = 1.95
    ax.plot([gx - 0.05, gx - 0.05], [r1, r1 + 0.30], color="#0f172a", lw=1.6)
    ax.plot([gx + 0.05, gx + 0.05], [r1, r1 + 0.30], color="#0f172a", lw=1.6)
    circ = patches.Circle((gx, r1 + 0.48), 0.18, facecolor="white", edgecolor="#0f172a", lw=1.8, zorder=5)
    ax.add_patch(circ)
    ax.plot([gx - 0.06, gx + 0.10], [r1 + 0.42, r1 + 0.56], color="#0f172a", lw=1.6, zorder=6)
    ax.text(gx + 0.25, r1 + 0.45, r"$p_M$", fontsize=13, va="center")

    # Diameter labels d1, d2, d3
    dx1 = 2.55
    ax.annotate("", xy=(dx1, r1), xytext=(dx1, -r1), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.3))
    ax.text(dx1 - 0.08, 0.06, r"$d_1$", fontsize=11.5, ha="right", va="center")

    mid_u = vtx + 1.55 * eu
    ax.annotate("", xy=mid_u + r2 * nu, xytext=mid_u + (r2 + 0.35) * nu, arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.3))
    ax.annotate("", xy=mid_u - r2 * nu, xytext=mid_u - (r2 + 0.35) * nu, arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.3))
    ax.text(mid_u[0] - 0.02, mid_u[1] + 0.02, r"$d_2$", fontsize=11, ha="center", va="center",
            bbox=dict(boxstyle="square,pad=0.05", fc="white", ec="none"))

    mid_d = vtx + 1.55 * ed
    nd_perp = np.array([-np.sin(th), -np.cos(th)])
    ax.annotate("", xy=mid_d + r2 * nd_perp, xytext=mid_d + (r2 + 0.35) * nd_perp, arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.3))
    ax.annotate("", xy=mid_d - r2 * nd_perp, xytext=mid_d - (r2 + 0.35) * nd_perp, arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.3))
    ax.text(mid_d[0] - 0.02, mid_d[1] - 0.02, r"$d_3$", fontsize=11, ha="center", va="center",
            bbox=dict(boxstyle="square,pad=0.05", fc="white", ec="none"))

    # Angle alpha arc between +x axis and lower branch centerline
    ang_arc = patches.Arc((vtx[0], 0.0), 2.1, 2.1, angle=0, theta1=-30, theta2=0, color="#0f172a", lw=1.4)
    ax.add_patch(ang_arc)
    ax.text(vtx[0] + 1.15, -0.30, r"$\alpha$", fontsize=12.5, ha="center", va="center")

    # Coordinate axes O-xy at bottom left
    ox, oy = 0.55, -1.45
    ax.annotate("", xy=(ox + 0.95, oy), xytext=(ox, oy), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.6))
    ax.annotate("", xy=(ox, oy + 0.85), xytext=(ox, oy), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.6))
    ax.text(ox + 1.02, oy, r"$x$", fontsize=12, va="center")
    ax.text(ox, oy + 0.92, r"$y$", fontsize=12, ha="center")
    ax.text(ox - 0.10, oy - 0.12, r"$O$", fontsize=11, ha="right", va="top")

    ax.set_xlim(0.15, 6.45)
    ax.set_ylim(-1.75, 1.85)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2022_q14_orig(out_path: Path) -> None:
    """Clean engineering redraw of 题14图 (WES overflow dam profile & elevations)."""
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    fig.patch.set_facecolor("white")

    # Dam profile helper function y_dam(x) for x >= 2.2
    def dam_y(x_arr: np.ndarray) -> np.ndarray:
        out = np.zeros_like(x_arr, dtype=float)
        m1 = (x_arr >= 2.2) & (x_arr <= 2.48)
        m2 = (x_arr > 2.48) & (x_arr <= 5.0)
        out[m1] = 1.95 - 0.30 * ((2.48 - x_arr[m1]) / 0.28) ** 2
        # Cosine S-curve ogee chute from (2.48, 1.95) down smoothly to tangent at (5.0, 0.0)
        t2 = (x_arr[m2] - 2.48) / (5.0 - 2.48)
        out[m2] = 1.95 * 0.5 * (1.0 + np.cos(np.pi * t2))
        return out

    ax.plot([0.2, 2.2], [0.0, 0.0], color="#0f172a", lw=2.3)
    ax.plot([2.2, 2.2], [0.0, 1.65], color="#0f172a", lw=2.3)
    xs_crest = np.linspace(2.2, 5.0, 160)
    ax.plot(xs_crest, dam_y(xs_crest), color="#0f172a", lw=2.3)
    ax.plot([5.0, 7.9], [0.0, 0.0], color="#0f172a", lw=2.3)

    # Free water surface: starts flat at 2.65 (22.80m), draws down smoothly to 1.95 + 0.42 = 2.37 at crest x=2.48,
    # then rides strictly ABOVE dam_y(x) with thinning supercritical sheet thickness 0.42 -> 0.18 at toe!
    xs_up = np.linspace(0.2, 2.48, 90)
    t_up = np.clip((xs_up - 0.85) / (2.48 - 0.85), 0.0, 1.0)
    ys_up = 2.65 - 0.28 * (t_up ** 2.2)

    xs_chute = np.linspace(2.48, 5.25, 110)
    t_ch = np.clip((xs_chute - 2.48) / (5.0 - 2.48), 0.0, 1.0)
    thickness = 0.42 - 0.24 * (t_ch ** 0.85)
    ys_chute = dam_y(xs_chute) + thickness

    ax.plot(np.concatenate([xs_up, xs_chute[1:]]), np.concatenate([ys_up, ys_chute[1:]]), color="#0f172a", lw=1.5)
    ax.plot([5.25, 5.52], [ys_chute[-1], ys_chute[-1] + 0.11], color="#0f172a", lw=1.5)

    # Tailwater level at right: 17.80m (y=0.92)
    ax.plot([6.6, 8.1], [0.92, 0.92], color="#0f172a", lw=1.6)

    def draw_elev(x_tri: float, y_line: float, text_str: str, line_span=None, ripples: bool = False):
        if line_span is not None:
            ax.plot([line_span[0], line_span[1]], [y_line, y_line], color="#0f172a", lw=1.4)
        h_tri = 0.18
        w_tri = 0.11
        ax.plot([x_tri, x_tri - w_tri, x_tri + w_tri, x_tri],
                [y_line, y_line + h_tri, y_line + h_tri, y_line], color="#0f172a", lw=1.3)
        ax.text(x_tri + 0.15, y_line + 0.04, text_str, fontsize=11, va="bottom", color="#0f172a")
        if ripples:
            ax.plot([x_tri - 0.12, x_tri + 0.12], [y_line - 0.08, y_line - 0.08], color="#0f172a", lw=1.0)
            ax.plot([x_tri - 0.06, x_tri + 0.06], [y_line - 0.15, y_line - 0.15], color="#0f172a", lw=1.0)

    draw_elev(0.55, 2.65, r"$22.80\,\mathrm{m}$", ripples=True)
    draw_elev(1.35, 1.95, r"$21.00\,\mathrm{m}$", line_span=(1.10, 2.42), ripples=False)
    draw_elev(0.85, 0.00, r"$15.00\,\mathrm{m}$", ripples=False)
    draw_elev(5.75, 0.00, r"$15.00\,\mathrm{m}$", ripples=False)
    draw_elev(7.10, 0.92, r"$17.80\,\mathrm{m}$", ripples=True)

    ax.set_xlim(0.05, 8.30)
    ax.set_ylim(-0.20, 3.05)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2022_q02_sol(out_path: Path) -> None:
    """Pitot-static velocity measurement schematic for 2022 Q2."""
    fig, ax = plt.subplots(figsize=(7.6, 4.0))
    fig.patch.set_facecolor("white")

    # Open channel / pipe flow background
    ax.add_patch(patches.Rectangle((0.5, 0.6), 6.6, 1.8, facecolor="#e0f2fe", alpha=0.65))
    ax.plot([0.5, 7.1], [2.4, 2.4], color="#0284c7", lw=2.0)
    ax.plot([0.5, 7.1], [0.6, 0.6], color="#0f172a", lw=2.2)

    # Uniform incoming flow arrows
    for yy in [0.95, 1.45, 1.95]:
        ax.annotate("", xy=(1.85, yy), xytext=(0.85, yy), arrowprops=dict(arrowstyle="->", color="#0284c7", lw=1.6))
    ax.text(1.35, 2.12, r"来流速度 $u$", fontsize=10, ha="center", color="#0369a1")

    # Static piezometer tube at x=3.1 (vertical opening flush/perpendicular to flow)
    ax.plot([3.03, 3.03], [1.45, 3.55], color="#0f172a", lw=1.8)
    ax.plot([3.17, 3.17], [1.45, 3.55], color="#0f172a", lw=1.8)
    ax.add_patch(patches.Rectangle((3.04, 1.45), 0.12, 0.95, facecolor="#38bdf8", alpha=0.75))
    ax.text(3.10, 3.66, "测压管（静压孔）", fontsize=9.5, ha="center", color="#334155")

    # Pitot L-shaped total head tube at x=5.0, tip facing upstream to x=4.35 at y=1.45 (stagnation point A)
    ax.plot([4.35, 4.93, 4.93], [1.52, 1.52, 3.65], color="#0f172a", lw=1.8)
    ax.plot([4.35, 5.07, 5.07], [1.38, 1.38, 3.65], color="#0f172a", lw=1.8)
    ax.add_patch(patches.Rectangle((4.94, 1.45), 0.12, 1.75, facecolor="#0284c7", alpha=0.75))
    ax.scatter([4.28], [1.45], color="#dc2626", s=30, zorder=6)
    ax.text(4.22, 1.22, r"驻点 $A$ ($u_A=0$)", fontsize=9.5, ha="right", color="#dc2626", fontweight="bold")
    ax.text(5.00, 3.76, "毕托管（总压孔）", fontsize=9.5, ha="center", color="#0369a1", fontweight="bold")

    # Head annotations h1, h2, Delta h = u^2 / (2g)
    ax.plot([3.17, 5.75], [2.40, 2.40], color="#64748b", ls="--", lw=1.1)
    ax.plot([5.07, 5.75], [3.20, 3.20], color="#dc2626", ls="--", lw=1.2)
    ax.annotate("", xy=(5.55, 3.20), xytext=(5.55, 2.40), arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.6))
    ax.text(5.68, 2.80, r"$\Delta h = h_2 - h_1 = \dfrac{u^2}{2g}$" + "\n" + r"$u = \varphi\sqrt{2g\Delta h}$",
            fontsize=10, va="center", color="#b91c1c", fontweight="bold")

    ax.annotate("", xy=(2.75, 2.40), xytext=(2.75, 1.45), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.2))
    ax.text(2.66, 1.92, r"$h_1=\dfrac{p}{\rho g}$", fontsize=9.2, ha="right", va="center", color="#334155")

    ax.set_xlim(0.3, 7.55)
    ax.set_ylim(0.4, 4.05)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2022_q09_sol(out_path: Path) -> None:
    """Inclined rectangular gate hydrostatic pressure & center of pressure diagram."""
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    fig.patch.set_facecolor("white")

    # Water surface at y=4.0; inclined plane at 45 deg passing through O=(4.6, 4.0) down-left: y = x - 0.6
    ax.plot([0.15, 5.0], [4.0, 4.0], color="#0284c7", lw=2.0)
    ax.text(1.6, 4.12, "自由水面", fontsize=9.5, color="#0369a1", fontweight="bold")
    ax.scatter([4.6], [4.0], color="#0f172a", s=24, zorder=5)
    ax.text(4.72, 4.05, r"$O$", fontsize=11, fontweight="bold")

    # Inclined wall from (1.2, 0.6) to (4.6, 4.0); gate occupies (1.2, 0.6) to (2.4, 1.8)
    ax.plot([2.4, 4.6], [1.8, 4.0], color="#334155", lw=1.6)
    ax.plot([1.2, 2.4], [0.6, 1.8], color="#0f172a", lw=5.0, solid_capstyle="round", zorder=5)
    ax.plot([1.2, 4.9], [0.6, 0.6], color="#334155", lw=1.8)
    ax.plot([2.4, 4.9], [1.8, 1.8], color="#334155", lw=1.4)

    # Centroid C at midpoint (1.8, 1.2), Center of pressure D slightly lower at (1.66, 1.06)
    c_pt = np.array([1.80, 1.20])
    d_pt = np.array([1.66, 1.06])
    ax.scatter([c_pt[0]], [c_pt[1]], color="#0284c7", s=34, zorder=6)
    ax.scatter([d_pt[0]], [d_pt[1]], color="#dc2626", s=38, zorder=7)
    ax.text(c_pt[0] + 0.16, c_pt[1] - 0.03, r"形心 $C$ ($h_c=8\,\mathrm{m}$)", fontsize=9.2, color="#0369a1")
    ax.text(d_pt[0] + 0.16, d_pt[1] - 0.24, r"压心 $D$ ($h_D=8.02\,\mathrm{m}$)", fontsize=9.2, color="#dc2626", fontweight="bold")

    # Trapezoidal hydrostatic pressure prism normal to gate
    n_ul = np.array([-np.sqrt(0.5), np.sqrt(0.5)])
    p_top = np.array([2.4, 1.8]) + 0.72 * n_ul
    p_bot = np.array([1.2, 0.6]) + 1.02 * n_ul
    ax.add_patch(patches.Polygon([[2.4, 1.8], [1.2, 0.6], p_bot, p_top], closed=True,
                                 facecolor="#fde68a", edgecolor="#d97706", lw=1.4, alpha=0.65))

    # Resultant force P acting at D perpendicular to gate
    p_tail = d_pt + 1.15 * n_ul
    ax.annotate("", xy=d_pt, xytext=p_tail, arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.5), zorder=7)
    ax.text(p_tail[0] + 0.55, p_tail[1] + 0.22, r"$P = 313.60\,\mathrm{kN}$", fontsize=10, color="#b91c1c", ha="center", fontweight="bold")

    # Depth H=8 m to centroid C shifted left so P arrow and text stay clear
    ax.plot([0.22, 1.80], [1.20, 1.20], color="#64748b", ls="--", lw=1.1)
    ax.annotate("", xy=(0.32, 4.0), xytext=(0.32, 1.20), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.3))
    ax.text(0.40, 2.85, r"$H=8\,\mathrm{m}$", fontsize=9.8, va="center")

    # Angle alpha = 45 deg
    arc = patches.Arc((2.4, 1.8), 1.1, 1.1, angle=0, theta1=0, theta2=45, color="#0f172a", lw=1.3)
    ax.add_patch(arc)
    ax.text(3.12, 2.02, r"$\alpha=45^{\circ}$", fontsize=9.8)

    ax.set_xlim(0.05, 5.2)
    ax.set_ylim(0.35, 4.45)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2022_q11_sol(out_path: Path) -> None:
    """Control volume force & momentum diagram for 2022 Q11 horizontal bifurcation."""
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    fig.patch.set_facecolor("white")

    th = np.radians(30.0)
    eu = np.array([np.cos(th), np.sin(th)])
    ed = np.array([np.cos(th), -np.sin(th)])
    nu = np.array([-np.sin(th), np.cos(th)])

    vtx = np.array([3.0, 0.0])
    r1, r2 = 0.38, 0.25
    t_out = (r1 - r2 * np.cos(th)) / np.sin(th)
    t_in = r2 * np.cos(th) / np.sin(th)
    L_cv = 1.65
    p_u_in = vtx + t_out * eu + r2 * nu
    p_u_top = vtx + L_cv * eu + r2 * nu
    p_u_bot = vtx + L_cv * eu - r2 * nu
    p_crotch = vtx + t_in * eu - r2 * nu

    cv_pts = [
        [1.55, r1], p_u_in, p_u_top, p_u_bot, p_crotch,
        [p_u_bot[0], -p_u_bot[1]], [p_u_top[0], -p_u_top[1]], [p_u_in[0], -p_u_in[1]], [1.55, -r1]
    ]
    ax.add_patch(patches.Polygon(cv_pts, closed=True, facecolor="#bae6fd", edgecolor="#0284c7", lw=2.0, alpha=0.72))
    ax.plot([1.55, 1.55], [-0.52, 0.52], color="#dc2626", ls="--", lw=1.6)
    ax.text(1.55, 0.60, "1—1 断面", fontsize=9.5, ha="center", color="#dc2626")

    # P1 arrow (+x)
    ax.annotate("", xy=(1.55, 0.0), xytext=(0.60, 0.0), arrowprops=dict(arrowstyle="->", color="#b45309", lw=2.4))
    ax.text(0.92, 0.22, r"$P_1 = 19.79\,\mathrm{kN}$", fontsize=9.5, ha="center", color="#92400e", fontweight="bold")

    # P2 and P3 inward normal pressure forces along -eu and -ed (labels placed cleanly beyond arrow tails!)
    c2 = vtx + L_cv * eu
    c3 = vtx + L_cv * ed
    tail2 = c2 + 0.85 * eu
    tail3 = c3 + 0.85 * ed
    ax.annotate("", xy=c2, xytext=tail2, arrowprops=dict(arrowstyle="->", color="#b45309", lw=2.2))
    ax.text(tail2[0] + 0.06, tail2[1] + 0.08, r"$P_2 = 8.72\,\mathrm{kN}$" + "\n" + r"($x$ 分量 $-P_2\cos 30^{\circ}$)",
            fontsize=9.0, ha="left", va="bottom", color="#92400e")

    ax.annotate("", xy=c3, xytext=tail3, arrowprops=dict(arrowstyle="->", color="#b45309", lw=2.2))
    ax.text(tail3[0] + 0.06, tail3[1] - 0.08, r"$P_3 = 8.72\,\mathrm{kN}$" + "\n" + r"($x$ 分量 $-P_3\cos 30^{\circ}$)",
            fontsize=9.0, ha="left", va="top", color="#92400e")

    # Pipe wall reaction Rx on water (-x, leftward) & water force Fx on pipe (+x, rightward)
    ax.annotate("", xy=(2.45, 0.0), xytext=(3.45, 0.0), arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.5))
    ax.text(2.95, -0.22, r"管壁对水 $R_x = 4.72\,\mathrm{kN}$（向左）", fontsize=9.2, ha="center", color="#dc2626", fontweight="bold")

    ax.text(0.50, -1.25, "水流对分岔管作用力：\n" + r"$F_x = 4.72\,\mathrm{kN}$（水平向右，沿 $+x$ 方向），$F_y = 0$",
            fontsize=9.5, color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.32", fc="#f0fdf4", ec="#16a34a", lw=1.2))

    ax.set_xlim(0.30, 6.85)
    ax.set_ylim(-1.65, 1.75)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2022_q14_sol(out_path: Path) -> None:
    """Overflow dam downstream repelled hydraulic jump (hc'' = 3.27 m > ht = 2.80 m) diagram."""
    fig, ax = plt.subplots(figsize=(8.0, 4.0))
    fig.patch.set_facecolor("white")

    def dam_y(x_arr: np.ndarray) -> np.ndarray:
        out = np.zeros_like(x_arr, dtype=float)
        m1 = (x_arr >= 1.6) & (x_arr <= 1.85)
        m2 = (x_arr > 1.85) & (x_arr <= 3.6)
        out[m1] = 2.0 - 0.25 * ((1.85 - x_arr[m1]) / 0.25) ** 2
        t2 = (x_arr[m2] - 1.85) / (3.6 - 1.85)
        out[m2] = 2.0 * 0.5 * (1.0 + np.cos(np.pi * t2))
        return out

    ax.plot([0.3, 8.2], [0.0, 0.0], color="#0f172a", lw=2.3)
    xs_dam = np.linspace(1.6, 3.6, 120)
    ys_dam = dam_y(xs_dam)
    ax.plot([1.6, 1.6], [0.0, 1.75], color="#0f172a", lw=2.2)
    ax.plot(xs_dam, ys_dam, color="#0f172a", lw=2.2)
    ax.add_patch(patches.Polygon([[1.6, 0.0]] + list(zip(xs_dam, ys_dam)) + [[3.6, 0.0]],
                                 closed=True, facecolor="#cbd5e1", alpha=0.7))

    # Water surface strictly above dam face: upstream 2.60 -> 2.38 at crest 1.85 -> rides above dam to hc=0.18 at x=3.85
    xs_up = np.linspace(0.3, 1.85, 60)
    t_up = np.clip((xs_up - 0.75) / (1.85 - 0.75), 0.0, 1.0)
    ys_up = 2.60 - 0.22 * (t_up ** 2.1)

    xs_ch = np.linspace(1.85, 3.85, 80)
    t_ch = np.clip((xs_ch - 1.85) / (3.6 - 1.85), 0.0, 1.0)
    ys_ch = dam_y(xs_ch) + (0.38 - 0.20 * (t_ch ** 0.85))

    xs_jump = np.array([3.85, 4.55, 5.15, 5.45, 5.75, 6.15, 6.55, 8.10])
    ys_jump = np.array([0.18, 0.20, 0.23, 0.46, 0.73, 0.90, 0.95, 0.95])
    xs_all = np.concatenate([xs_up, xs_ch[1:], xs_jump[1:]])
    ys_all = np.concatenate([ys_up, ys_ch[1:], ys_jump[1:]])
    ax.plot(xs_all, ys_all, color="#0284c7", lw=2.1)

    # Dashed line for required conjugate depth hc'' = 3.27 m (y = 1.18 > 0.95)
    ax.plot([3.65, 7.95], [1.18, 1.18], color="#dc2626", ls="--", lw=1.6)
    ax.text(5.85, 1.26, r"跃后共轭水深 $h_c^{\prime\prime} = 3.27\,\mathrm{m} > h_t = 2.80\,\mathrm{m}$",
            fontsize=9.6, ha="center", color="#dc2626", fontweight="bold")

    # Contracted depth annotation at x=4.00
    ax.annotate("", xy=(4.00, 0.19), xytext=(4.00, 0.68), arrowprops=dict(arrowstyle="->", color="#0369a1", lw=1.4))
    ax.text(4.15, 0.73, r"收缩水深 $h_c=0.458\,\mathrm{m}$", fontsize=9.0, ha="center", color="#0369a1")

    # Tailwater depth ht = 2.80 m
    ax.annotate("", xy=(7.55, 0.95), xytext=(7.55, 0.0), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.3))
    ax.text(7.65, 0.48, r"$h_t=2.80\,\mathrm{m}$", fontsize=9.2, va="center")

    ax.text(5.65, 2.15, "判别结论：发生远驱式水跃，高速急流直接冲刷护坦\n必须修建消力池等消能设施！",
            fontsize=9.5, ha="center", color="#7c2d12",
            bbox=dict(boxstyle="round,pad=0.32", fc="#ffedd5", ec="#ea580c", lw=1.1))

    ax.set_xlim(0.2, 8.5)
    ax.set_ylim(-0.18, 2.85)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2022_q15_sol(out_path: Path) -> None:
    """Experimental apparatus schematic for measuring full-open valve local loss coeff zeta."""
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    fig.patch.set_facecolor("white")

    # Constant-head supply tank with overflow weir on left
    ax.plot([0.4, 0.4, 2.1, 2.1], [3.6, 0.9, 0.9, 1.32], color="#0f172a", lw=2.0)
    ax.plot([2.1, 2.1], [1.52, 3.6], color="#0f172a", lw=2.0)
    ax.plot([0.85, 0.85], [0.9, 3.15], color="#0f172a", lw=1.8)
    ax.add_patch(patches.Rectangle((0.86, 0.92), 1.22, 2.23, facecolor="#bae6fd", alpha=0.6))
    ax.plot([0.85, 2.1], [3.15, 3.15], color="#0284c7", lw=2.0)
    # Supply pipe & overflow drain
    ax.annotate("", xy=(1.55, 3.20), xytext=(1.55, 3.75), arrowprops=dict(arrowstyle="->", color="#0284c7", lw=1.8))
    ax.text(1.55, 3.82, "持续供水", fontsize=9, ha="center", color="#0369a1")
    ax.annotate("", xy=(0.62, 0.40), xytext=(0.62, 0.90), arrowprops=dict(arrowstyle="->", color="#64748b", lw=1.4))
    ax.text(0.62, 0.22, "溢流管", fontsize=8.8, ha="center", color="#475569")
    ax.text(1.48, 2.45, "恒水头\n溢流水箱", fontsize=9.2, ha="center", color="#0f172a")

    # Horizontal uniform test pipe (y in [1.32, 1.52], x from 2.1 to 7.6)
    ax.add_patch(patches.Rectangle((2.1, 1.32), 5.5, 0.20, facecolor="#e0f2fe", edgecolor="none"))
    ax.plot([2.1, 7.6], [1.52, 1.52], color="#0f172a", lw=1.8)
    ax.plot([2.1, 7.6], [1.32, 1.32], color="#0f172a", lw=1.8)

    # Three piezometers: 1 (x=3.1), 2 (x=4.4), 3 (x=6.1); test valve FULLY OPEN at x=5.0
    p_data = [(3.1, 2.95, "测压管 1", r"$h_1$"), (4.4, 2.70, "测压管 2", r"$h_2$"), (6.1, 2.02, "测压管 3", r"$h_3$")]
    for px, ph, name_lbl, h_lbl in p_data:
        ax.plot([px - 0.05, px - 0.05], [1.52, 3.25], color="#334155", lw=1.3)
        ax.plot([px + 0.05, px + 0.05], [1.52, 3.25], color="#334155", lw=1.3)
        ax.add_patch(patches.Rectangle((px - 0.04, 1.52), 0.08, ph - 1.52, facecolor="#38bdf8", alpha=0.8))
        ax.text(px, 3.33, name_lbl, fontsize=9, ha="center", color="#0f172a")
        ax.text(px + 0.14, ph + 0.10, h_lbl, fontsize=9.5, color="#0369a1", fontweight="bold")

    # Piezometric head line (H.G.L.) showing slope J on 1-2 and sudden drop hj at test valve!
    ax.plot([2.5, 3.1, 4.4, 4.95], [3.065, 2.95, 2.70, 2.594], color="#0284c7", ls="--", lw=1.7)
    ax.plot([5.05, 6.1, 6.8], [2.222, 2.02, 1.885], color="#0284c7", ls="--", lw=1.7, label="测压管水头线")
    ax.annotate("", xy=(5.0, 2.22), xytext=(5.0, 2.60), arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.5))
    ax.text(5.12, 2.45, r"$h_j=\zeta\dfrac{v^2}{2g}$", fontsize=9.2, va="center", color="#dc2626", fontweight="bold")

    # Test valve (fully open, green) at x=5.0
    tvx = 5.0
    ax.add_patch(patches.Polygon([[tvx - 0.15, 1.60], [tvx + 0.15, 1.24], [tvx + 0.15, 1.60], [tvx - 0.15, 1.24]],
                                 closed=True, facecolor="#bbf7d0", edgecolor="#15803d", lw=1.6, zorder=6))
    ax.text(tvx, 1.72, "待测新型阀门\n（保持全开）", fontsize=8.8, ha="center", color="#15803d", fontweight="bold")

    # Downstream flow-regulating valve at x=7.05
    rvx = 7.05
    ax.add_patch(patches.Polygon([[rvx - 0.14, 1.58], [rvx + 0.14, 1.26], [rvx + 0.14, 1.58], [rvx - 0.14, 1.26]],
                                 closed=True, facecolor="#fecaca", edgecolor="#b91c1c", lw=1.5, zorder=6))
    ax.text(rvx, 1.72, "流量调节阀", fontsize=8.8, ha="center", color="#b91c1c")

    # Lengths l1 and l2 below pipe
    ax.annotate("", xy=(4.4, 1.05), xytext=(3.1, 1.05), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.3))
    ax.text(3.75, 0.82, r"参考直管段 $l_1$", fontsize=9, ha="center", color="#334155")
    ax.annotate("", xy=(6.1, 1.05), xytext=(4.4, 1.05), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.3))
    ax.text(5.25, 0.82, r"含阀测试段 $l_2$", fontsize=9, ha="center", color="#334155")

    # Outlet into volumetric measuring tank at right
    ax.plot([7.6, 7.85, 7.85], [1.52, 1.52, 1.05], color="#0f172a", lw=1.8)
    ax.plot([7.6, 7.70, 7.70], [1.32, 1.32, 1.05], color="#0f172a", lw=1.8)
    ax.add_patch(patches.Rectangle((7.35, 0.35), 0.95, 0.55, facecolor="#bae6fd", edgecolor="#0f172a", lw=1.6))
    ax.text(7.82, 0.12, r"量水箱测 $Q$", fontsize=9.2, ha="center", color="#0369a1", fontweight="bold")

    ax.set_xlim(0.2, 8.55)
    ax.set_ylim(0.0, 4.05)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


# ==============================================================================
# 2023 EXAM DATA (13 questions, totalScore = 150)
# ==============================================================================

def build_2023_paper() -> dict:
    return {
        "year": 2023,
        "code": "849",
        "subject": "水力学（水）",
        "school": "扬州大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": True,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "全卷共 13 道题：第 1～6 题为机理分析与基础判别题（6×8 = 48 分），第 7～13 题为综合计算与公式推导题（12×1 + 15×6 = 102 分）。",
            "除特别说明外，计算统一取重力加速度 $g = 9.80\\,\\mathrm{m/s^2}$，水的密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$，水银密度 $\\rho_{\\text{汞}} = 13600\\,\\mathrm{kg/m^3}$（解析同步附 $g = 9.81\\,\\mathrm{m/s^2}$ 对照结果）。"
        ],
        "sections": [
            {
                "id": "short",
                "title": "一、机理分析与简答题",
                "description": "第 1～6 题，每题 8 分，共 48 分。",
                "range": [1, 6],
                "scorePerQuestion": 8,
                "totalScore": 48
            },
            {
                "id": "calc",
                "title": "二、计算与推导题",
                "description": "第 7～13 题（第 7 题 12 分，第 8～13 题每题 15 分），共 102 分。",
                "range": [7, 13],
                "totalScore": 102
            }
        ],
        "questions": [
            {
                "id": "yzu-849-2023-01",
                "year": 2023,
                "no": 1,
                "type": "short",
                "score": 8,
                "title": "牛顿内摩擦定律在湍流中的适用性辨析",
                "stem": "牛顿内摩擦定律是否适用于湍流？为什么？",
                "note": "",
                "figures": [],
                "shortAnswer": "直接用时均流速梯度形式 τ = μ(dū/dy) 不适用于湍流（除紧贴固壁的黏性底层外）。因为湍流中除分子热运动引起的黏性切应力 τ_l 外，流体微团剧烈横向脉动混掺产生远大于 τ_l 的附加湍流切应力（雷诺切应力 τ_t = -ρu'v'），总切应力 τ = μ(dū/dy) - ρu'v'。",
                "judgeAnswer": None,
                "answer": "**不适用**（准确地说，直接以时均流速梯度表示的牛顿内摩擦定律 $\\tau = \\mu\\frac{\\mathrm{d}\\bar{u}}{\\mathrm{d}y}$ 不能描述湍流核心区的总切应力，仅在紧贴壁面的极薄黏性底层内近似适用）。\n\n**原因**：\n1. 牛顿内摩擦定律 $\\tau = \\mu\\frac{\\mathrm{d}u}{\\mathrm{d}y}$ 反映的是层流状态下流体各流层互不混杂、仅靠**分子热运动动量交换**所产生的黏性切应力；\n2. 在湍流中，流体质点除沿主流方向运动外，还存在剧烈的三维随机**脉动与横向混掺**。高速流层微团跃入低速流层、低速流层微团跃入高速流层，造成宏观流体微团间的强烈动量交换，从而在时均黏性切应力 $\\tau_l = \\mu\\frac{\\mathrm{d}\\bar{u}}{\\mathrm{d}y}$ 之外产生数值大得多的**附加湍流切应力（雷诺应力）** $\\tau_t = -\\rho\\overline{u^{\\prime}v^{\\prime}}$；\n3. 湍流总切应力为 $\\tau = \\tau_l + \\tau_t = \\mu\\frac{\\mathrm{d}\\bar{u}}{\\mathrm{d}y} - \\rho\\overline{u^{\\prime}v^{\\prime}} = (\\mu + \\mu_t)\\frac{\\mathrm{d}\\bar{u}}{\\mathrm{d}y}$，其中涡黏度 $\\mu_t$ 不是流体的物性常数，而是随流动状态与空间位置而变，故牛顿内摩擦定律不再直接适用于湍流。",
                "analysis": "**1. 层流与湍流切应力物理机制的本质差异**\n\n- **层流状态**：流线平行规整，相邻流层无宏观流体微团交换，切应力完全源于微观分子热运动跨越流层的动量输运，服从牛顿内摩擦定律：\n\n$$\n\\tau_l = \\mu \\frac{\\mathrm{d}u}{\\mathrm{d}y}\n$$\n\n其中动力黏度 $\\mu$ 仅取决于流体种类和温度（物性参数）。\n\n- **湍流状态**：瞬时流速分解为时均流速与脉动流速 $u = \\bar{u} + u^{\\prime}$，$v = \\bar{v} + v^{\\prime}$。经雷诺时均化处理后，平行流动的湍流总切应力由两部分叠加而成：\n\n$$\n\\tau = \\mu \\frac{\\mathrm{d}\\bar{u}}{\\mathrm{d}y} - \\rho \\overline{u^{\\prime}v^{\\prime}}\n$$\n\n**2. 分区讨论（答题加分点）**\n\n- 在**湍流核心区**：宏观涡团脉动极为剧烈，雷诺切应力 $\\tau_t = -\\rho\\overline{u^{\\prime}v^{\\prime}} \\gg \\tau_l$，分子黏性项甚至可以忽略，显然不能直接套用 $\\tau = \\mu\\frac{\\mathrm{d}\\bar{u}}{\\mathrm{d}y}$；若仿照牛顿公式引入布辛涅斯克（Boussinesq）涡黏系数写成 $\\tau = (\\mu + \\rho \\varepsilon_m)\\frac{\\mathrm{d}\\bar{u}}{\\mathrm{d}y}$，由于 $\\varepsilon_m$ 取决于流场结构而非物性，实质上已非牛顿内摩擦定律。\n- 在紧贴固壁的**黏性底层**（$\\delta_0$ 极薄层）内：受壁面限制法向脉动趋于零（$v^{\\prime} \\to 0$，$-\\rho\\overline{u^{\\prime}v^{\\prime}} \\to 0$），流动恢复准层流特征，此处切应力仍可由 $\\tau_0 = \\mu \\left.\\frac{\\mathrm{d}\\bar{u}}{\\mathrm{d}y}\\right|_{y=0}$ 计算。",
                "analysisFigures": [],
                "pitfalls": "切忌只写“不适用”三个字而不写出湍流总切应力表达式 $\\tau = \\mu\\frac{\\mathrm{d}\\bar{u}}{\\mathrm{d}y} - \\rho\\overline{u^{\\prime}v^{\\prime}}$！点明“微观分子动量交换 vs 宏观微团脉动混掺（雷诺切应力）”以及“黏性底层内局部适用”能确保拿满 8 分。",
                "chapter": 1,
                "kps": ["牛顿内摩擦定律", "雷诺切应力", "黏性底层"],
                "method": "分子黏性应力与湍流雷诺应力机理对比法",
                "difficulty": 2,
                "rubric": [
                    {"label": "明确指出牛顿内摩擦定律（时均形式）不适用于湍流主体区（仅黏性底层近似适用）", "pts": 2},
                    {"label": "阐明湍流存在剧烈横向脉动与宏观微团动量交换，产生远大于黏性应力的附加雷诺切应力", "pts": 3},
                    {"label": "正确写出湍流总切应力公式 τ = μ(dū/dy) - ρu'v' 并说明涡黏度非流体物性常数", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2023-02",
                "year": 2023,
                "no": 2,
                "type": "short",
                "score": 8,
                "title": "测压管水头常数规律 z + p/(ρg) = C 在水静力学与水动力学中的成立条件",
                "stem": "试阐述压强分布规律 $z + p/(\\rho g) = C$ 分别在水静力学和水动力学中成立的条件。",
                "note": "",
                "figures": [],
                "shortAnswer": "水静力学条件：①液体处于绝对静止状态；②质量力只有重力；③均质不可压缩（ρ=常数）且同种连通液体。水动力学条件：在均质不可压缩液体仅受重力作用的基础上，研究对象限于均匀流或渐变流的同一过水断面上（流线近似为平行直线，法向加速度为零，全空间不为同一常数但同一过水断面上为常数）。",
                "judgeAnswer": None,
                "answer": "**（1）在水静力学中成立的条件**（全连通静止流场处处为同一常数 $C$）：\n① 液体处于**绝对静止**状态（各点速度及加速度均为零，无黏性切应力）；\n② 作用在液体上的**质量力只有重力**（$f_x = 0,\\; f_y = 0,\\; f_z = -g$）；\n③ 液体为**均质不可压缩流体**（密度 $\\rho = \\text{const}$）；\n④ 所考察各点位于**同一种连续连通**的液体内部。\n\n**（2）在水动力学中成立的条件**（在**同一过水断面上**为常数 $C$，不同过水断面间 $C$ 一般随流程改变）：\n① 液体为**均质不可压缩流体**（$\\rho = \\text{const}$），且**质量力只有重力**；\n② 流动为**均匀流**（或近似为**渐变流**），所考察各点必须位于**同一个过水断面**上（过水断面垂直于平行直线流束，沿断面方向流线无弯曲、无发散，法向流线曲率半径 $R \\to \\infty$ 且法向速度与法向加速度为零，沿断面方向无黏性切应力分量）。",
                "analysis": "**1. 从欧拉平衡微分方程推导水静力学条件**\n\n流体平衡微分方程为 $\\mathrm{d}p = \\rho (f_x\\,\\mathrm{d}x + f_y\\,\\mathrm{d}y + f_z\\,\\mathrm{d}z)$。仅当流体**静止**（无切应力与惯性力）、**质量力仅有重力**（$f_x = f_y = 0,\\; f_z = -g$）时，化为 $\\mathrm{d}p = -\\rho g\\,\\mathrm{d}z$；再结合**均质不可压缩**（$\\rho = \\text{const}$）并在**同种连通液体**中积分，方可得全流场统一的静水压强基本规律：\n\n$$\nz + \\frac{p}{\\rho g} = C\n$$\n\n（若容器做等加速直线运动或等角速旋转运动，存在非零惯性质量力，则相对平衡液体不再满足 $z + p/(\\rho g) = C$。）\n\n**2. 从流线法向动力学方程推导水动力学条件**\n\n在运动液体中，沿垂直于流线的自然坐标法向 $n$（取过水断面内任意方向 $l$），动力学微分方程为：\n\n$$\n-\\frac{\\partial}{\\partial n}\\left(z + \\frac{p}{\\rho g}\\right) = \\frac{1}{g}\\left(\\frac{\\partial u_n}{\\partial t} + \\frac{u_s^2}{r}\\right) - \\frac{h_{fn}^{\\prime}}{1}\n$$\n\n当流动为仅受重力作用的均质不可压缩**均匀流（或渐变流）**时，流线为平行直线（曲率半径 $r \\to \\infty$，离心惯性力 $u_s^2/r = 0$），且法向分速 $u_n = 0$（当地法向加速度及法向摩阻均为零），故沿垂直于流线的**同一过水断面**积分即得：\n\n$$\nz + \\frac{p}{\\rho g} = C(s)\n$$\n\n注意：在水动力学实际黏性流体中，由于沿流向存在流速水头变化与沿程水头损失 $h_f$，不同过水断面上的常数 $C(s)$ 沿流向递减（急变流断面如堰顶、弯道、闸孔出口附近流线急剧弯曲，$z + p/(\\rho g) \\neq C$）。",
                "analysisFigures": [],
                "pitfalls": "1. 水静力学部分极易漏掉“**连通同种液体**”与“**质量力只有重力**（排除相对平衡状态）”；\n2. 水动力学部分必须强调“**在同一过水断面上**”这一空间限定！切勿误以为均匀流整个流场三维空间内 $z + p/(\\rho g)$ 都相等（沿流向是有水头损失降落的）。",
                "chapter": 3,
                "kps": ["静水压强基本方程", "渐变流过水断面压强分布", "质量力与流线曲率"],
                "method": "平衡微分方程与流线法向方程条件对比法",
                "difficulty": 2,
                "rubric": [
                    {"label": "完整答出水静力学四要素：绝对静止、质量力仅有重力、均质不可压缩、同种连通液体", "pts": 4},
                    {"label": "完整答出水动力学条件：均质不可压、仅受重力、均匀流或渐变流的同一过水断面上（流线平直无法向加速度）", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2023-03",
                "year": 2023,
                "no": 3,
                "type": "short",
                "score": 8,
                "title": "变截面虹吸出流管道各特征点动水压强高低定性判别",
                "stem": "有一如图所示输水管道，水箱内水位保持不变，试问：\n\n（1）$A$ 点的压强能否比 $B$ 点低？为什么？\n\n（2）$C$ 点的压强能否比 $D$ 点低？为什么？\n\n（3）$E$ 点的压强能否比 $F$ 点低？为什么？",
                "note": "",
                "figures": [
                    {"src": "figures/q03_orig.png", "caption": "题 3 图　恒定水位水箱输水管道特征点位置"}
                ],
                "shortAnswer": "（1）能，A 位于突然缩小进口后的收缩断面处，流束强烈收缩使 vA > vB，动能转化为压能使 B 处扩压恢复若大于局部损失则 pA < pB；（2）不能，C、D 管径相同（vC=vD），但 D 位置高程高于 C（zD > zC）且顺流有水头损失 hw>0，故必有 pC > pD；（3）能，F 为通大气出口（pF=0），E 位于虹吸管高程最高段，当下降段位能差大于 E-F 水头损失时 E 点出现负压（真空），故 pE < pF。",
                "judgeAnswer": None,
                "answer": "**（1）$A$ 点的压强能比 $B$ 点低（$p_A < p_B$ 可以成立）**。\n原因：由图可知，$A$ 点紧靠粗管突然缩小进入细管的进口段，水流因惯性发生流束收缩（形成收缩断面），有效过流面积 $A_c < A_B$，故收缩处流速 $v_A > v_B$；从 $A$ 到 $B$ 流束重新扩散贴壁减速，部分动能重新转化为压能。只要动能恢复量 $\\frac{v_A^2 - v_B^2}{2g}$ 大于 $A\\text{—}B$ 间的局部扩散水头损失 $h_{w,A\\text{-}B}$，由能量方程即有 $\\frac{p_B - p_A}{\\rho g} = \\frac{v_A^2 - v_B^2}{2g} - h_{w,A\\text{-}B} > 0$，故 $p_A < p_B$。\n\n**（2）$C$ 点的压强不能比 $D$ 点低（必有 $p_C > p_D$）**。\n原因：$C$、$D$ 所在细管管径相同，由连续性方程知 $v_C = v_D$。对 $C$、$D$ 列能量方程得 $\\frac{p_C - p_D}{\\rho g} = (z_D - z_C) + h_{w,C\\text{-}D}$；因 $D$ 点位置高程明显高于 $C$ 点（$z_D - z_C > 0$），且水流由 $C$ 流向 $D$ 必有水头损失 $h_{w,C\\text{-}D} > 0$，两正项叠加恒大于零，故 $p_C$ 恒大于 $p_D$，绝不可能比 $D$ 点低。\n\n**（3）$E$ 点的压强能比 $F$ 点低（$p_E < p_F$ 可以成立）**。\n原因：$F$ 点位于管道出口断面，直接通大气，其相对压强 $p_F = 0$；$E$ 点与 $F$ 点所在管段管径相同（$v_E = v_F$），列 $E\\text{—}F$ 能量方程得 $\\frac{p_E}{\\rho g} = \\frac{p_F}{\\rho g} - (z_E - z_F) + h_{w,E\\text{-}F} = -(z_E - z_F) + h_{w,E\\text{-}F}$。因 $E$ 位于虹吸驼峰顶部，$z_E > z_F$，只要高差 $(z_E - z_F) > h_{w,E\\text{-}F}$，$E$ 点即处于真空负压状态（$p_E < 0 = p_F$）。",
                "analysis": "以管轴各点建立实际液体恒定总流伯努利方程（总水头线与测压管水头线变化见解图 3）：\n\n$$\nz_1 + \\frac{p_1}{\\rho g} + \\frac{\\alpha_1 v_1^2}{2g} = z_2 + \\frac{p_2}{\\rho g} + \\frac{\\alpha_2 v_2^2}{2g} + h_{w,1\\text{-}2}\n$$\n\n**1. $A$ 点与 $B$ 点压强比较（局部收缩断面效应）**\n\n- 细管进口为直角突然缩小边界，$A$ 点恰位于进口流束收缩断面附近，而 $B$ 点位于下游流束已恢复满管均匀分布的直管段上，两者同高程（$z_A = z_B$）：\n\n$$\n\\frac{p_B - p_A}{\\rho g} = \\frac{v_A^2 - v_B^2}{2g} - h_{w,A\\text{-}B}\n$$\n\n- 设细管断面积为 $A_0$，收缩系数 $\\varepsilon \\approx 0.62\\sim 0.64$，则 $v_A = v_B / \\varepsilon$，而突缩局部损失主要产生于收缩断面 $A$ 至恢复断面 $B$ 的包达（Borda）扩散段：$h_{w,A\\text{-}B} = \\frac{(v_A - v_B)^2}{2g}$。代入上式化简：\n\n$$\n\\frac{p_B - p_A}{\\rho g} = \\frac{v_A^2 - v_B^2 - (v_A - v_B)^2}{2g} = \\frac{v_B(v_A - v_B)}{g} > 0 \\implies p_A < p_B\n$$\n\n严格定量证明了进口收缩断面 $A$ 处的压强必然低于下游恢复断面 $B$ 处的压强！\n\n**2. $C$ 点与 $D$ 点压强比较（升坡等径管段）**\n\n- $C$、$D$ 处均为满管直管渐变流断面且管径相等，$v_C = v_D$：\n\n$$\n\\frac{p_C - p_D}{\\rho g} = (z_D - z_C) + h_{w,C\\text{-}D}\n$$\n\n- 图中 $z_D > z_C$，且顺水流方向水头损失 $h_{w,C\\text{-}D} > 0$，故 $p_C - p_D > 0$ 恒成立，$p_C$ 不可能低于 $p_D$。\n\n**3. $E$ 点与 $F$ 点压强比较（虹吸下降段抽吸负压）**\n\n- 出口断面 $F$ 通大气（$p_F = 0$），且等径管 $v_E = v_F$：\n\n$$\n\\frac{p_E - p_F}{\\rho g} = h_{w,E\\text{-}F} - (z_E - z_F)\n$$\n\n- 竖直下降段管长较短、高差 $z_E - z_F$ 显著大于局部弯头与短管沿程损失 $h_{w,E\\text{-}F}$，故 $p_E < p_F = 0$（$E$ 点产生真空负压）。",
                "analysisFigures": [
                    {"src": "figures/q03_sol.png", "caption": "解图 3　输水管道总水头线与测压管水头线变化及各点压强对比"}
                ],
                "pitfalls": "第（1）问极易粗心看作普通水平等径直管而误答“不能（以为顺流必降压）”！务必仔细观察题 3 图中 $A$ 点恰处于粗管突缩进细管的进口端——突缩进口存在著名的“流束收缩增速降压、随后扩压恢复”现象，用包达公式可严格证得 $p_B - p_A = \\rho v_B(v_A - v_B) > 0$。",
                "chapter": 3,
                "kps": ["恒定总流能量方程", "突然缩小局部损失与收缩断面", "虹吸管真空负压"],
                "method": "伯努利方程位能动能损失三项对比判别法",
                "difficulty": 3,
                "rubric": [
                    {"label": "结合进口突然缩小流束收缩增速（vA > vB）及扩压恢复分析得出 pA 能低于 pB", "pts": 3},
                    {"label": "由等径 vC = vD、位置高程 zD > zC 及顺流损失 hw > 0 论证 pC 不能低于 pD", "pts": 2},
                    {"label": "由出口通大气 pF = 0、虹吸顶 zE > zF 且位能降大于 E-F 损失论证 pE 能低于 pF（呈负压）", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2023-04",
                "year": 2023,
                "no": 4,
                "type": "short",
                "score": 8,
                "title": "应用伯努利能量方程解释两张平行薄纸间吹气靠拢现象",
                "stem": "试用能量方程式解释现象：向两张靠得很近的薄纸吹气，两张纸不是彼此分开，而是彼此靠拢。",
                "note": "",
                "figures": [],
                "shortAnswer": "吹气时两纸内侧夹缝间空气流速 v 大幅增大，而纸张外侧静止空气流速约为 0；同一水平高程下由伯努利能量方程 z + p/(ρg) + v²/(2g) = C 可知，流速大处压强小，故两纸内侧动压强 p_内 显著低于外侧大气压强 p_a，内外表面压强差产生指向内侧的合力推动两纸彼此靠拢。",
                "judgeAnswer": None,
                "answer": "**机理解释**：\n1. 当向两张靠得很近的薄纸中间吹气时，两纸外侧的空气基本处于静止状态，流速 $v_{\\text{外}} \\approx 0$，压强等于周围环境大气压强 $p_{\\text{外}} = p_a$；\n2. 两纸内侧夹缝间形成高速气流（流速 $v_{\\text{内}}$ 很大）。忽略空气微小重力位能变化与短程能量损失，对流场应用伯努利能量方程：\n\n$$\nz + \\frac{p}{\\rho g} + \\frac{v^2}{2g} = C \\implies p + \\frac{1}{2}\\rho v^2 = p_a\n$$\n\n3. 由方程可见，同一总能水平下**流速越大的地方动压强越小**。由于内侧气流速度 $v_{\\text{内}} > 0$，故两纸内侧气体压强降低为：\n\n$$\np_{\\text{内}} = p_a - \\frac{1}{2}\\rho v_{\\text{内}}^2 < p_a = p_{\\text{外}}\n$$\n\n4. 每张薄纸外表面所受大气压力均大于内表面所受气流压力（$\\Delta p = p_{\\text{外}} - p_{\\text{内}} = \\frac{1}{2}\\rho v_{\\text{内}}^2 > 0$），在指向夹缝中心的气压差合力作用下，两张薄纸向中间靠拢；且越靠拢狭缝越窄、流速越高、低压吸力越强。",
                "analysis": "**从流管连续性与能量守恒双重视角深化分析**\n\n1. **能量转换关系**：气体在低马赫数下可视为不可压缩流体（$\\rho \\approx \\text{const}$）。取吹气前总压或远场静止大气为基准，沿流线列理想气体伯努利方程（水平高程 $z_{\\text{内}} = z_{\\text{外}}$）：\n\n$$\n\\frac{p_{\\text{内}}}{\\rho g} + \\frac{v_{\\text{内}}^2}{2g} = \\frac{p_a}{\\rho g} + 0 \\implies p_a - p_{\\text{内}} = \\frac{1}{2}\\rho v_{\\text{内}}^2 > 0\n$$\n\n表明内侧气流增加的单位体积动能 $\\frac{1}{2}\\rho v_{\\text{内}}^2$ 是由静压能降低转化而来的，从而在两纸之间形成负相对压强区（低压区）。\n\n2. **正反馈吸合效应**：一旦两纸在压差 $\\Delta F = (p_a - p_{\\text{内}})A$ 驱动下开始向内微移，两纸间距减小，由连续性原理 $Q = A v$ 知狭缝风速进一步增大，内侧压强进一步下降，直至两纸贴合（这也是航海中两船近距离并行易发生“船吸碰撞”事故的同一水动力学原理）。",
                "analysisFigures": [],
                "pitfalls": "答题时必须明确写出伯努利能量方程式 $z + \\frac{p}{\\rho g} + \\frac{v^2}{2g} = C$（题目明确要求“试用能量方程式解释”！），并对比“纸内侧流速大、压强小于大气压”与“纸外侧流速为零、压强等于大气压”两侧边界，切勿只定性写一句“流速大压强小”而漏列方程。",
                "chapter": 3,
                "kps": ["伯努利方程物理意义", "流速与动压强转换关系"],
                "method": "伯努利方程动能压能转化分析法",
                "difficulty": 1,
                "rubric": [
                    {"label": "正确写出伯努利能量方程式 z + p/(ρg) + v²/(2g) = C（或 p + ρv²/2 = C）", "pts": 3},
                    {"label": "结合方程说明两纸内侧吹气流速大故压强低于大气压，外侧空气静止压强等于大气压", "pts": 3},
                    {"label": "指出薄纸内外表面存在指向内侧的压差合力，故两纸彼此靠拢而非分开", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2023-05",
                "year": 2023,
                "no": 5,
                "type": "calc",
                "score": 8,
                "title": "等流量等流速圆管与正方形有压管道雷诺数计算及流态判别",
                "stem": "两个有压直管道，断面形状分别为圆形和正方形，通过的流量均为 $10^{-5}\\,\\mathrm{m^3/s}$，液体的运动粘度均为 $10^{-6}\\,\\mathrm{m^2/s}$，两管道断面平均流速相等，圆管的直径为 $0.015\\,\\mathrm{m}$，试分别判断两管道的液流型态是层流还是湍流？",
                "note": "",
                "figures": [],
                "shortAnswer": "圆管雷诺数 Re = 848.8 < 2000（或水力半径雷诺数 Re_R = 212.2 < 500），为层流；正方形管当量直径雷诺数 Re_de = 752.3 < 2000（或水力半径雷诺数 Re_R = 188.1 < 500），亦为层流。",
                "judgeAnswer": None,
                "answer": "圆管与正方形管道内的液流型态**均为层流**（圆管 $Re \\approx 848.8 < 2000$；正方形管按当量直径计 $Re_{d_e} \\approx 752.3 < 2000$，按水力半径计 $Re_R \\approx 188.1 < 500$）。",
                "analysis": "**1. 圆管流速与流态判别**\n\n已知圆管直径 $d = 0.015\\,\\mathrm{m}$，流量 $Q = 10^{-5}\\,\\mathrm{m^3/s}$，运动黏度 $\\nu = 10^{-6}\\,\\mathrm{m^2/s}$。圆管过水断面积与断面平均流速为：\n\n$$\nA_{\\text{圆}} = \\frac{\\pi}{4}d^2 = \\frac{\\pi}{4} \\times 0.015^2 \\approx 1.7671 \\times 10^{-4}\\,\\mathrm{m^2}\n$$\n\n$$\nv = \\frac{Q}{A_{\\text{圆}}} = \\frac{10^{-5}}{1.7671 \\times 10^{-4}} \\approx 0.05659\\,\\mathrm{m/s}\n$$\n\n计算圆管雷诺数：\n\n$$\nRe_{\\text{圆}} = \\frac{v d}{\\nu} = \\frac{0.05659 \\times 0.015}{10^{-6}} = \\frac{4 Q}{\\pi d \\nu} \\approx 848.8\n$$\n\n因 $Re_{\\text{圆}} = 848.8 < Re_k = 2000$（若用水力半径 $R_{\\text{圆}} = d/4$ 计，则 $Re_{R,\\text{圆}} = 212.2 < 500$），故**圆管内液流为层流**。\n\n**2. 正方形有压管道几何尺寸与流态判别**\n\n因两管流量 $Q$ 相等且断面平均流速 $v$ 相等，故正方形管道过水断面积与圆管相等：\n\n$$\nA_{\\text{方}} = a^2 = A_{\\text{圆}} = 1.7671 \\times 10^{-4}\\,\\mathrm{m^2} \\implies a = \\sqrt{A_{\\text{圆}}} = \\frac{\\sqrt{\\pi}}{2}d \\approx 0.01329\\,\\mathrm{m}\n$$\n\n满流正方形管道的湿周 $\\chi_{\\text{方}} = 4a$，水力半径与当量直径 $d_e = 4R$ 分别为：\n\n$$\nR_{\\text{方}} = \\frac{A_{\\text{方}}}{\\chi_{\\text{方}}} = \\frac{a^2}{4a} = \\frac{a}{4} \\approx 3.323 \\times 10^{-3}\\,\\mathrm{m}, \\qquad d_e = 4 R_{\\text{方}} = a \\approx 0.01329\\,\\mathrm{m}\n$$\n\n非圆有压管道采用水力半径雷诺数 $Re_R$（下临界值 $Re_{Rk} = 500$）或当量直径雷诺数 $Re_{d_e}$（下临界值 $Re_k = 2000$）判别：\n\n$$\nRe_{R,\\text{方}} = \\frac{v R_{\\text{方}}}{\\nu} = \\frac{0.05659 \\times 3.323 \\times 10^{-3}}{10^{-6}} \\approx 188.1 < 500\n$$\n\n$$\n\\left(\\text{等价地：}Re_{d_e,\\text{方}} = \\frac{v d_e}{\\nu} = 4 Re_{R,\\text{方}} \\approx 752.3 < 2000\\right)\n$$\n\n故**正方形管道内液流同样为层流**。",
                "analysisFigures": [],
                "pitfalls": "非圆断面有压管计算雷诺数时，特征长度必须采用**水力半径 $R = A/\\chi$**（对应临界雷诺数 $Re_{Rk} = 500$）或**水力当量直径 $d_e = 4R$**（对应临界雷诺数 $Re_k = 2000$）！正方形满管的当量直径 $d_e = 4(a^2/4a) = a$ 恰好等于边长 $a$，但切记不可将特征长度与临界值混搭（如用 $R$ 却拿去和 $2000$ 比较，虽本题均小于 $500$ 不改结论，但概念扣分）。",
                "chapter": 4,
                "kps": ["雷诺数与流态判别", "非圆管水力半径与当量直径"],
                "method": "水力半径与当量直径雷诺数流态判别法",
                "difficulty": 2,
                "rubric": [
                    {"label": "求出圆管断面积与流速 v ≈ 0.0566 m/s，算得 Re_圆 ≈ 848.8 < 2000 判为层流", "pts": 4},
                    {"label": "由等流量等流速求得方管边长 a ≈ 0.0133 m、水力半径 R = a/4（或 de = a）", "pts": 2},
                    {"label": "算得方管 Re_R ≈ 188.1 < 500（或 Re_de ≈ 752.3 < 2000），正确判为层流", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2023-06",
                "year": 2023,
                "no": 6,
                "type": "short",
                "score": 8,
                "title": "用恒定总流能量方程证明明渠均匀流只能在顺坡渠道中形成",
                "stem": "试用能量方程式分析解释，为什么说只有在顺坡渠道中有可能形成均匀流，在平坡和逆坡渠道中不可能形成均匀流？",
                "note": "",
                "figures": [],
                "shortAnswer": "对明渠相距 L 的两断面列能量方程，均匀流要求 h1=h2、v1=v2，化简得 z1 - z2 = hf，即底坡 i = (z1-z2)/L = hf/L = J。因实际黏性水流运动必消耗机械能（沿程水头损失 hf > 0，水力坡度 J > 0），故必有底坡 i = J > 0（顺坡）；平坡（i=0）和逆坡（i<0）无法满足 i = J > 0，不可能形成均匀流。",
                "judgeAnswer": None,
                "answer": "**推导与证明**：\n在明渠中沿水流方向任取间距为 $L$ 的两个过水断面 $1\\text{—}1$ 和 $2\\text{—}2$，以水平面为基准面列实际液体恒定总流能量方程式：\n\n$$\nz_1 + h_1 + \\frac{\\alpha_1 v_1^2}{2g} = z_2 + h_2 + \\frac{\\alpha_2 v_2^2}{2g} + h_w\n$$\n\n假定渠道中形成**明渠均匀流**，根据均匀流定义，水深、断面形状尺寸、流速分布及断面平均流速沿程均保持不变，且无局部水头损失，即：\n\n$$\nh_1 = h_2 = h_0, \\qquad v_1 = v_2 = v_0, \\qquad \\alpha_1 = \\alpha_2, \\qquad h_w = h_f\n$$\n\n代入能量方程式消去相等项，得：\n\n$$\nz_1 - z_2 = h_f\n$$\n\n将上式两端同除以流段水平（或沿渠底）长度 $L$，注意到渠底坡度定义为 $i = \\frac{z_1 - z_2}{L}$、水力坡度（总水头线坡度）定义为 $J = \\frac{h_f}{L}$，即得均匀流基本关系：\n\n$$\ni = J = \\frac{h_f}{L}\n$$\n\n**结论分析**：\n- 实际液体皆具黏滞性，只要发生流动就必然克服边界摩阻做功而产生正的沿程水头损失（$h_f > 0$），因此水力坡度恒满足 **$J > 0$**；\n- 要使 $i = J$ 成立，渠底坡度必须满足 **$i > 0$（即 $z_1 > z_2$，顺坡 / 正坡渠道）**，其物理实质是水体重力沿流向的位能降落恰好抵消沿程摩阻能量消耗；\n- 在**平坡渠道（$i = 0$）**和**逆坡渠道（$i < 0$）**中，$i \\le 0$ 而 $J > 0$，恒有 $i \\neq J$，重力沿流向无推进分力甚至阻碍流动，只能靠水深或流速沿程改变（消耗断面比能）来维持流动，故绝不可能形成均匀流。",
                "analysis": "**补充力学视角印证（辅助理解）**\n\n除能量方程视角外，从沿流向控制体动量平衡亦可直观印证：均匀流加速度为零、上下游断面静水压力相等抵消，故沿流向合力平衡要求水体重力沿渠底分力 $\\rho g A L \\sin\\theta$ 与渠壁摩擦阻力 $\\tau_0 \\chi L$ 严格平衡（$\\rho g A L i = \\tau_0 \\chi L > 0$）。在平坡（$\\sin\\theta = 0$）或逆坡（$\\sin\\theta < 0$）中，重力分力为零或向后，与向后的摩阻力同向叠加，水体必然减速或水面跌落（形成 $H_2$、$A_2$ 或 $H_3$、$A_3$ 型非均匀渐变流水面曲线），无法维持等水深等流速。",
                "analysisFigures": [],
                "pitfalls": "本题题干明确限定“**试用能量方程式分析解释**”，务必先完整写出明渠两断面伯努利能量方程 $z_1 + h_1 + \\frac{\\alpha_1 v_1^2}{2g} = z_2 + h_2 + \\frac{\\alpha_2 v_2^2}{2g} + h_f$，再利用均匀流条件消去 $h$ 和 $\\frac{\\alpha v^2}{2g}$ 导出 $i = J > 0$，切忌只写受力分析而不写能量方程！",
                "chapter": 7,
                "kps": ["明渠均匀流形成条件", "恒定总流能量方程", "底坡与水力坡度关系"],
                "method": "明渠能量方程化简底坡水力坡度法",
                "difficulty": 2,
                "rubric": [
                    {"label": "正确列出明渠两断面恒定总流能量方程式 z1 + h1 + α1v1²/(2g) = z2 + h2 + α2v2²/(2g) + hf", "pts": 3},
                    {"label": "代入均匀流特征 h1=h2、v1=v2 导出 z1 - z2 = hf 即底坡等于水力坡度 i = J", "pts": 3},
                    {"label": "结合实际液体流动必有 hf > 0（J > 0）阐明仅 i > 0 顺坡可成均匀流，i ≤ 0 平坡逆坡不可能", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2023-07",
                "year": 2023,
                "no": 7,
                "type": "calc",
                "score": 12,
                "title": "双水银测压计密闭压力容器水深计算",
                "stem": "某压力容器，如图所示。容器上装有两个水银测压计，已知 $h_1 = 2.0\\,\\mathrm{cm}$，$h_2 = 24.0\\,\\mathrm{cm}$，$h_3 = 22.0\\,\\mathrm{cm}$，求水深 $H$。",
                "note": "",
                "figures": [
                    {"src": "figures/q07_orig.png", "caption": "题 7 图　装有两个水银测压计的压力容器"}
                ],
                "shortAnswer": "248.0 cm（即 2.48 m）",
                "judgeAnswer": None,
                "answer": "图中所求水深 $H = 248.0\\,\\mathrm{cm} = 2.48\\,\\mathrm{m}$。",
                "analysis": "**1. 由右侧水银测压计求容器顶部气体相对压强 $p_0$**\n\n右侧 U 形水银测压计右支开口通大气（相对压强为 $0$），左支连通容器上部密闭气体空间。忽略气体柱极小的自重压强差，过右侧 U 形管左支气—汞交界面作水平等压面 $1\\text{—}1$（见解图 7），由等压面性质得容器水面以上气体的相对压强：\n\n$$\np_0 = \\rho_{\\text{汞}} g h_1\n$$\n\n**2. 由左侧水银测压计列等压面方程求水深 $H$**\n\n左侧 U 形水银测压计左支开口通大气（相对压强为 $0$），右支连通容器下部水体。由题 7 图尺寸标注可知，容器内自由水面至测压管引出基准线的深度为 $H$，该基准线至左侧 U 形管右支水—汞交界面的竖直高度为 $h_2$，故水—汞交界面距容器内自由水面的总水柱高度为 $(H + h_2)$。\n\n在左侧连通水银中，过右支水—汞交界面作水平等压面 $2\\text{—}2$，左右两支在该等压面处压强相等：\n\n$$\np_0 + \\rho_{\\text{水}} g (H + h_2) = \\rho_{\\text{汞}} g h_3\n$$\n\n将 $p_0 = \\rho_{\\text{汞}} g h_1$ 代入上式，两边同除以 $\\rho_{\\text{水}} g$，并取水银相对密度 $S_{\\text{汞}} = \\frac{\\rho_{\\text{汞}}}{\\rho_{\\text{水}}} = 13.6$：\n\n$$\n13.6 h_1 + H + h_2 = 13.6 h_3\n$$\n\n整理并代入已知数据 $h_1 = 2.0\\,\\mathrm{cm}$，$h_2 = 24.0\\,\\mathrm{cm}$，$h_3 = 22.0\\,\\mathrm{cm}$：\n\n$$\nH = 13.6 (h_3 - h_1) - h_2 = 13.6 \\times (22.0 - 2.0) - 24.0 = 272.0 - 24.0 = 248.0\\,\\mathrm{cm} = 2.48\\,\\mathrm{m}\n$$\n\n（注：因方程两边重力加速度 $g$ 严格约去，无论取 $g = 9.80\\,\\mathrm{m/s^2}$ 或 $9.81\\,\\mathrm{m/s^2}$，结果精确恒为 $2.48\\,\\mathrm{m}$。）",
                "analysisFigures": [
                    {"src": "figures/q07_sol.png", "caption": "解图 7　双水银测压计等压面 1—1、2—2 选取与液柱平衡关系"}
                ],
                "pitfalls": "1. 右侧测压计连接的是上部气体空间，气体密度远小于水与水银，切勿把右侧管段按水柱计入压强；\n2. 认准题 7 图中 $H$ 与 $h_2$ 的起止标尺线：左侧 U 形管右支水—汞分界面位于自由水面以下 $(H + h_2)$ 处，故求 $H$ 时需减去 $h_2 = 24.0\\,\\mathrm{cm}$。",
                "chapter": 2,
                "kps": ["多液层压差计", "等压面性质", "静水压强基本方程"],
                "method": "等压面静水压强递推法",
                "difficulty": 2,
                "rubric": [
                    {"label": "由右侧水银计等压面求出容器顶部气体相对压强 p0 = ρ汞gh1（折算水柱头 27.2 cm）", "pts": 4},
                    {"label": "过左侧水银计水-汞交界面作等压面，正确列出平衡方程 p0 + ρ水g(H + h2) = ρ汞gh3", "pts": 5},
                    {"label": "代入 h1=2 cm、h2=24 cm、h3=22 cm 及 ρ汞/ρ水=13.6 解得 H = 248.0 cm（2.48 m）", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2023-08",
                "year": 2023,
                "no": 8,
                "type": "calc",
                "score": 15,
                "title": "混凝土重力坝在下游有水与无水两种工况下的水平与铅直水压力计算",
                "stem": "图示一混凝土重力坝，为了校核坝的稳定性，试分别计算当下游有水和下游无水两种情况下，作用于 $1\\,\\mathrm{m}$ 长坝体上水平方向的水压力和垂直方向的水压力。",
                "note": "",
                "figures": [
                    {"src": "figures/q08_orig.png", "caption": "题 8 图　混凝土重力坝上下游剖面尺寸与水位"}
                ],
                "shortAnswer": "（1）下游有水：水平总水压力 Px = 3136.00 kN（指向下游），垂直总水压力 Pz = 950.60 kN（竖直向下）；（2）下游无水：水平总水压力 Px' = 3312.40 kN（指向下游），垂直总水压力 Pz' = 862.40 kN（竖直向下）。（若取 g=9.81 m/s²，有水时 Px=3139.20 kN、Pz=951.57 kN；无水时 Px'=3315.78 kN、Pz'=863.28 kN）",
                "judgeAnswer": None,
                "answer": "取坝段计算宽度 $b = 1\\,\\mathrm{m}$，$g = 9.80\\,\\mathrm{m/s^2}$：\n\n**（1）当下游有水（$H_2 = 6\\,\\mathrm{m}$）时**：\n- 作用于坝体上**水平方向**的净水压力：$P_x = 3136.00\\,\\mathrm{kN}$，方向水平向右（指向下游）；\n- 作用于坝体上**垂直方向**的总水压力：$P_z = 950.60\\,\\mathrm{kN}$，方向竖直向下。\n\n**（2）当下游无水（$H_2 = 0$）时**：\n- 作用于坝体上**水平方向**的水压力：$P_x^{\\prime} = 3312.40\\,\\mathrm{kN}$，方向水平向右（指向下游）；\n- 作用于坝体上**垂直方向**的水压力：$P_z^{\\prime} = 862.40\\,\\mathrm{kN}$，方向竖直向下。\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则下游有水时 $P_x = 3139.20\\,\\mathrm{kN}$、$P_z = 951.57\\,\\mathrm{kN}$；下游无水时 $P_x^{\\prime} = 3315.78\\,\\mathrm{kN}$、$P_z^{\\prime} = 863.28\\,\\mathrm{kN}$。）",
                "analysis": "采用折面/曲面静水总压力的**水平投影法与铅垂压力体法**计算单位坝长（$b = 1\\,\\mathrm{m}$）受力（压力分布与实压力体见解图 8，取 $\\rho = 1000\\,\\mathrm{kg/m^3}$，$g = 9.80\\,\\mathrm{m/s^2}$）：\n\n**1. 上游坝面静水压力分量（水深 $H_1 = 26\\,\\mathrm{m}$）**\n\n- **上游水平分力 $P_{x1}$**：上游受压面在铅直面上的投影高度等于总水深 $H_1 = 26\\,\\mathrm{m}$，形心淹深 $h_{c1} = H_1 / 2 = 13\\,\\mathrm{m}$：\n\n$$\nP_{x1} = \\frac{1}{2}\\rho g H_1^2 b = \\frac{1}{2} \\times 1000 \\times 9.80 \\times 26^2 \\times 1 = 3312400\\,\\mathrm{N} = 3312.40\\,\\mathrm{kN}\\;(\\text{水平向右})\n$$\n\n- **上游铅直分力 $P_{z1}$**：上游坝面上部 $(26 - 8) = 18\\,\\mathrm{m}$ 为铅直墙面（无铅直水压力），下部高 $8\\,\\mathrm{m}$、底宽 $4\\,\\mathrm{m}$ 为迎水斜坡面。其上方水体为**实压力体**，断面呈直角梯形（上底 $18\\,\\mathrm{m}$、下底 $26\\,\\mathrm{m}$、高 $4\\,\\mathrm{m}$）：\n\n$$\nV_{z1} = \\frac{18 + 26}{2} \\times 4 \\times 1 = 88.0\\,\\mathrm{m^3}\n$$\n\n$$\nP_{z1} = \\rho g V_{z1} = 1000 \\times 9.80 \\times 88.0 = 862400\\,\\mathrm{N} = 862.40\\,\\mathrm{kN}\\;(\\text{竖直向下})\n$$\n\n**2. 下游有水时（水深 $H_2 = 6\\,\\mathrm{m}$）下游坝面静水压力分量**\n\n- **下游水平分力 $P_{x2}$**：\n\n$$\nP_{x2} = \\frac{1}{2}\\rho g H_2^2 b = \\frac{1}{2} \\times 1000 \\times 9.80 \\times 6^2 \\times 1 = 176400\\,\\mathrm{N} = 176.40\\,\\mathrm{kN}\\;(\\text{水平向左})\n$$\n\n- **下游铅直分力 $P_{z2}$**：由题 8 图几何尺寸知，下游斜坡面总竖直高度为 $18 + 6 = 24\\,\\mathrm{m}$，对应总水平底宽为 $12\\,\\mathrm{m}$，故下游坝坡坡率（水平∶竖直）为 $\\frac{12}{24} = 0.5$。当下游水深 $H_2 = 6\\,\\mathrm{m}$ 时，水下受压斜坡面的水平投影宽度为：\n\n$$\nb_2 = H_2 \\times \\frac{12}{24} = 6 \\times 0.5 = 3.0\\,\\mathrm{m}\n$$\n\n其上方水体为直角三角形**实压力体**，体积与向下铅直水压力为：\n\n$$\nV_{z2} = \\frac{1}{2} \\times b_2 \\times H_2 \\times 1 = \\frac{1}{2} \\times 3.0 \\times 6.0 \\times 1 = 9.0\\,\\mathrm{m^3}\n$$\n\n$$\nP_{z2} = \\rho g V_{z2} = 1000 \\times 9.80 \\times 9.0 = 88200\\,\\mathrm{N} = 88.20\\,\\mathrm{kN}\\;(\\text{竖直向下})\n$$\n\n**3. 两种工况下坝体合力汇总**\n\n1. **下游有水工况**：\n   - 水平方向合力（上下游水平推力相向抵减）：\n     $$P_x = P_{x1} - P_{x2} = 3312.40 - 176.40 = 3136.00\\,\\mathrm{kN}\\;(\\text{水平向右，指向下游})$$\n   - 垂直方向合力（上下游斜面均为实压力体，方向均竖直向下，同向相加）：\n     $$P_z = P_{z1} + P_{z2} = 862.40 + 88.20 = 950.60\\,\\mathrm{kN}\\;(\\text{竖直向下})$$\n\n2. **下游无水工况**（$P_{x2} = 0$，$P_{z2} = 0$）：\n   - 水平方向水压力：$P_x^{\\prime} = P_{x1} = 3312.40\\,\\mathrm{kN}$（水平向右，指向下游）；\n   - 垂直方向水压力：$P_z^{\\prime} = P_{z1} = 862.40\\,\\mathrm{kN}$（竖直向下）。",
                "analysisFigures": [
                    {"src": "figures/q08_sol.png", "caption": "解图 8　重力坝上下游水平静水压强分布与铅垂实压力体分解图"}
                ],
                "pitfalls": "1. 下游斜坡面总高是 $18 + 6 = 24\\,\\mathrm{m}$（而非 $18\\,\\mathrm{m}$）对应水平宽度 $12\\,\\mathrm{m}$，相似三角形求水下水平投影宽度时务必用 $b_2 = 6 \\times \\frac{12}{24} = 3\\,\\mathrm{m}$，切勿误算成 $6 \\times \\frac{12}{18} = 4\\,\\mathrm{m}$！\n2. 下游有水时，水平分力 $P_{x1}$ 与 $P_{x2}$ 方向相反相减，但铅直分力 $P_{z1}$ 与 $P_{z2}$ 均为压在坝坡上的实压力体，方向**同为竖直向下，应当相加**而非相减！",
                "chapter": 2,
                "kps": ["平面与曲面静水总压力", "压力体与铅直分力", "重力坝水压力计算"],
                "method": "水平投影与铅垂压力体分块合成法",
                "difficulty": 3,
                "rubric": [
                    {"label": "求出上游水平水压力 Px1 = 3312.40 kN 及上游梯形实压力体铅直力 Pz1 = 862.40 kN", "pts": 5},
                    {"label": "由几何相似比求出下游水下投影宽 b2 = 3 m，算得 Px2 = 176.40 kN、Pz2 = 88.20 kN", "pts": 5},
                    {"label": "正确合成下游有水（Px=3136.0 kN, Pz=950.6 kN）和无水（Px'=3312.4 kN, Pz'=862.4 kN）结果及方向", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2023-09",
                "year": 2023,
                "no": 9,
                "type": "proof",
                "score": 15,
                "title": "文丘里流量计理论流量与实际流量计算公式推导",
                "stem": "如图所示为文丘里流量计，已知被测管道直径为 $d_1$，喉管管径为 $d_2$，两测压管液面高度差为 $h$。试运用能量方程推导水管中流量的理论公式，并据此写出实际流量的计算公式。",
                "note": "",
                "figures": [
                    {"src": "figures/q09_orig.png", "caption": "题 9 图　文丘里（Venturi）流量计构造与测压管液面差"}
                ],
                "shortAnswer": "理论流量 Qt = [π d1² d2² / (4√(d1⁴ - d2⁴))]·√(2gh) = [(π/4)d2² / √(1 - (d2/d1)⁴)]·√(2gh)；实际流量 Q = μ Qt = μ[(π/4)d2² / √(1 - (d2/d1)⁴)]·√(2gh)（μ 为流量系数，一般 0.95～0.98）。",
                "judgeAnswer": None,
                "answer": "水管中流量的**理论公式**：\n\n$$\nQ_t = \\frac{\\frac{\\pi}{4}d_2^2}{\\sqrt{1 - \\left(\\frac{d_2}{d_1}\\right)^4}}\\sqrt{2gh} = \\frac{\\pi d_1^2 d_2^2}{4\\sqrt{d_1^4 - d_2^4}}\\sqrt{2gh}\n$$\n\n水管中流量的**实际计算公式**（引入文丘里流量计流量系数 $\\mu$）：\n\n$$\nQ = \\mu Q_t = \\frac{\\mu \\frac{\\pi}{4}d_2^2}{\\sqrt{1 - \\left(\\frac{d_2}{d_1}\\right)^4}}\\sqrt{2gh}\n$$",
                "analysis": "**1. 列理想液体伯努利能量方程**\n\n选取收缩段前的正常圆管过水断面 $1\\text{—}1$（直径 $d_1$，断面积 $A_1 = \\frac{\\pi}{4}d_1^2$）与喉管过水断面 $2\\text{—}2$（直径 $d_2$，断面积 $A_2 = \\frac{\\pi}{4}d_2^2$）。推导理论流量时，假定流体为理想不可压缩液体（忽略 $1\\text{—}2$ 间水头损失 $h_{w,1\\text{-}2} = 0$），且取动能修正系数 $\\alpha_1 = \\alpha_2 = 1.0$。以管轴中心线所在水平面为基准面（$z_1 = z_2 = 0$；即便管道倾斜布置，两测压管液面高程差亦恒等于测压管水头差），列能量方程：\n\n$$\nz_1 + \\frac{p_1}{\\rho g} + \\frac{v_{1t}^2}{2g} = z_2 + \\frac{p_2}{\\rho g} + \\frac{v_{2t}^2}{2g}\n$$\n\n由题 9 图知，两测压管液面高度差为：\n\n$$\nh = \\left(z_1 + \\frac{p_1}{\\rho g}\\right) - \\left(z_2 + \\frac{p_2}{\\rho g}\\right) = h_1 - h_2\n$$\n\n代入能量方程整理得：\n\n$$\n\\frac{v_{2t}^2 - v_{1t}^2}{2g} = h \\implies v_{2t}^2 - v_{1t}^2 = 2gh\n$$\n\n**2. 联立连续性方程导出理论流量公式 $Q_t$**\n\n由不可压缩恒定总流连续性方程：\n\n$$\nQ_t = A_1 v_{1t} = A_2 v_{2t} \\implies v_{1t} = \\frac{A_2}{A_1}v_{2t} = \\left(\\frac{d_2}{d_1}\\right)^2 v_{2t}\n$$\n\n代入速度平方差关系式解出喉管断面理论流速 $v_{2t}$：\n\n$$\nv_{2t}^2\\left[1 - \\left(\\frac{d_2}{d_1}\\right)^4\\right] = 2gh \\implies v_{2t} = \\frac{\\sqrt{2gh}}{\\sqrt{1 - \\left(\\frac{d_2}{d_1}\\right)^4}}\n$$\n\n乘以喉管过水断面积 $A_2 = \\frac{\\pi}{4}d_2^2$，即得文丘里流量计理论流量公式：\n\n$$\nQ_t = A_2 v_{2t} = \\frac{\\frac{\\pi}{4}d_2^2}{\\sqrt{1 - \\left(\\frac{d_2}{d_1}\\right)^4}}\\sqrt{2gh} = \\frac{\\pi d_1^2 d_2^2}{4\\sqrt{d_1^4 - d_2^4}}\\sqrt{2gh}\n$$\n\n**3. 修正得出实际流量计算公式 $Q$**\n\n实际黏性水流通过收缩段时存在沿程与局部水头损失 $h_{w,1\\text{-}2} > 0$，且断面流速分布不均匀（$\\alpha_1 \\neq \\alpha_2$），使实际流量略小于理论流量。引入无量纲**流量系数 $\\mu$**（由实验率定，因收缩段流线平顺无分离，通常高达 $\\mu = 0.95\\sim 0.98$）加以修正，得到实际流量计算公式：\n\n$$\nQ = \\mu Q_t = \\frac{\\mu \\frac{\\pi}{4}d_2^2}{\\sqrt{1 - \\left(\\frac{d_2}{d_1}\\right)^4}}\\sqrt{2gh}\n$$\n\n（工程上对于给定尺寸的文丘里流量计，常令流量计常数 $k = \\frac{\\mu \\frac{\\pi}{4}d_2^2}{\\sqrt{1 - (d_2/d_1)^4}}\\sqrt{2g}$，简写为 $Q = k\\sqrt{h}$。）",
                "analysisFigures": [],
                "pitfalls": "1. 面积比 $\\frac{A_2}{A_1} = \\left(\\frac{d_2}{d_1}\\right)^2$ 代入 $v_2^2 - v_1^2$ 平方后根号内是**四次方** $\\left(\\frac{d_2}{d_1}\\right)^4$，切勿误写成平方！\n2. 写实际流量公式时需说明引入流量系数 $\\mu$（$0 < \\mu < 1$）的物理原因是修正实际液体的水头损失 $h_w$ 与动能修正系数 $\\alpha$ 的影响。",
                "chapter": 3,
                "kps": ["伯努利方程测流", "文丘里流量计", "恒定总流连续性方程"],
                "method": "伯努利方程与连续性方程联立测流法",
                "difficulty": 2,
                "rubric": [
                    {"label": "对 1—1 与喉管 2—2 断面列理想伯努利方程并结合 h = (z1+p1/ρg)-(z2+p2/ρg) 导出 v2² - v1² = 2gh", "pts": 5},
                    {"label": "联立连续性方程 A1v1 = A2v2 消元推导得出理论流量公式 Qt", "pts": 6},
                    {"label": "考虑水头损失与流速分布不均引入流量系数 μ，正确写出实际流量公式 Q = μQt", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2023-10",
                "year": 2023,
                "no": 10,
                "type": "calc",
                "score": 15,
                "title": "由水泵出口表压强推求输水流量、水泵扬程与有效功率",
                "stem": "水泵装置如图所示，水泵安装高度 $h_s = 3\\,\\mathrm{m}$，高、低水池液面高差 $z_0 = 20\\,\\mathrm{m}$。吸水管的直径 $d_1 = 0.2\\,\\mathrm{m}$，长度 $l_1 = 4\\,\\mathrm{m}$，沿程阻力系数 $\\lambda_1 = 0.024$，总的局部水头损失系数 $\\zeta_1 = 6$；压力管的直径 $d_2 = 0.15\\,\\mathrm{m}$，长度 $l_2 = 50\\,\\mathrm{m}$，沿程阻力系数 $\\lambda_2 = 0.028$，总的局部水头损失系数 $\\zeta_2 = 8.5$。测得水泵出口的表压强 $p_2 = 1.8 \\times 10^5\\,\\mathrm{Pa}$。试计算水泵输水流量 $Q$，水泵扬程 $H$，水泵有效功率 $P$。",
                "note": "",
                "figures": [
                    {"src": "figures/q10_orig.png", "caption": "题 10 图　水泵抽水装置管路与高低水池布置图"}
                ],
                "shortAnswer": "Q ≈ 0.0223 m³/s（22.3 L/s），水泵扬程 H ≈ 21.62 m，水泵有效功率 P ≈ 4.72 kW（若取 g=9.81 m/s²，则 Q ≈ 0.0222 m³/s，H ≈ 21.59 m，P ≈ 4.69 kW）",
                "judgeAnswer": None,
                "answer": "取 $g = 9.80\\,\\mathrm{m/s^2}$：\n- 水泵输水流量：$Q \\approx 0.0223\\,\\mathrm{m^3/s}$（即 $22.30\\,\\mathrm{L/s}$）；\n- 水泵扬程：$H \\approx 21.62\\,\\mathrm{m}$；\n- 水泵有效功率：$P \\approx 4.72\\,\\mathrm{kW}$。\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $Q \\approx 0.0222\\,\\mathrm{m^3/s}$，$H \\approx 21.59\\,\\mathrm{m}$，$P \\approx 4.69\\,\\mathrm{kW}$。）",
                "analysis": "**1. 对压力管段（断面 $2\\text{—}2$ 至高水池液面 $3\\text{—}3$）列能量方程求流量 $Q$**\n\n以低水池自由液面 $0\\text{—}0$ 为基准面（$z = 0$），则水泵出口断面 $2\\text{—}2$ 中心高程 $z_2 = h_s = 3\\,\\mathrm{m}$，高水池自由液面 $3\\text{—}3$ 高程 $z_3 = z_0 = 20\\,\\mathrm{m}$，液面表压强 $p_3 = 0$，流速 $v_3 \\approx 0$。取动能修正系数 $\\alpha_2 = 1.0$，$g = 9.80\\,\\mathrm{m/s^2}$，压力管总局部损失系数 $\\zeta_2 = 8.5$（含出口淹没局部损失），列 $2\\text{—}2$ 至 $3\\text{—}3$ 的恒定总流能量方程（能量水头线见解图 10）：\n\n$$\nh_s + \\frac{p_2}{\\rho g} + \\frac{v_2^2}{2g} = z_0 + 0 + 0 + \\left(\\lambda_2 \\frac{l_2}{d_2} + \\zeta_2\\right)\\frac{v_2^2}{2g}\n$$\n\n计算水泵出口表压强水头与压力管总阻力系数：\n\n$$\n\\frac{p_2}{\\rho g} = \\frac{1.8 \\times 10^5}{1000 \\times 9.80} \\approx 18.3673\\,\\mathrm{m}\n$$\n\n$$\nK_{\\zeta 2} = \\lambda_2 \\frac{l_2}{d_2} + \\zeta_2 = 0.028 \\times \\frac{50}{0.15} + 8.5 = 9.3333 + 8.5 = 17.8333\n$$\n\n代入能量方程解出压力管流速水头与平均流速 $v_2$：\n\n$$\n(K_{\\zeta 2} - 1)\\frac{v_2^2}{2g} = \\frac{p_2}{\\rho g} - (z_0 - h_s) \\implies 16.8333 \\times \\frac{v_2^2}{2g} = 18.3673 - (20 - 3) = 1.3673\\,\\mathrm{m}\n$$\n\n$$\n\\frac{v_2^2}{2g} = \\frac{1.3673}{16.8333} \\approx 0.08123\\,\\mathrm{m} \\implies v_2 = \\sqrt{2 \\times 9.80 \\times 0.08123} \\approx 1.2618\\,\\mathrm{m/s}\n$$\n\n由此求得水泵输水流量 $Q$：\n\n$$\nQ = A_2 v_2 = \\frac{\\pi}{4}d_2^2 v_2 = \\frac{\\pi}{4} \\times 0.15^2 \\times 1.2618 \\approx 0.02230\\,\\mathrm{m^3/s} = 22.30\\,\\mathrm{L/s}\n$$\n\n**2. 计算吸水管与压力管水头损失，求水泵总扬程 $H$**\n\n- 压力管总水头损失 $h_{w2}$：\n\n$$\nh_{w2} = K_{\\zeta 2}\\frac{v_2^2}{2g} = 17.8333 \\times 0.08123 \\approx 1.4486\\,\\mathrm{m}\n$$\n\n- 吸水管平均流速 $v_1$ 与总水头损失 $h_{w1}$：\n\n$$\nv_1 = \\frac{Q}{A_1} = v_2 \\left(\\frac{d_2}{d_1}\\right)^2 = 1.2618 \\times \\left(\\frac{0.15}{0.20}\\right)^2 \\approx 0.7098\\,\\mathrm{m/s}\n$$\n\n$$\nh_{w1} = \\left(\\lambda_1 \\frac{l_1}{d_1} + \\zeta_1\\right)\\frac{v_1^2}{2g} = \\left(0.024 \\times \\frac{4}{0.2} + 6\\right)\\times \\frac{0.7098^2}{2 \\times 9.80} = 6.48 \\times 0.02570 \\approx 0.1665\\,\\mathrm{m}\n$$\n\n对低水池液面 $0\\text{—}0$ 与高水池液面 $3\\text{—}3$ 列全系统总流能量方程，得水泵扬程 $H$：\n\n$$\n0 + H = z_0 + h_{w1} + h_{w2} \\implies H = 20 + 0.1665 + 1.4486 = 21.6151\\,\\mathrm{m} \\approx 21.62\\,\\mathrm{m}\n$$\n\n**3. 计算水泵有效功率 $P$**\n\n水泵有效功率（输出水功率，题目未涉及泵效率 $\\eta$）为：\n\n$$\nP = \\rho g Q H = 1000 \\times 9.80 \\times 0.02230 \\times 21.6151 \\approx 4723.2\\,\\mathrm{W} \\approx 4.72\\,\\mathrm{kW}\n$$\n\n（注：若将 $\\zeta_2 = 8.5$ 视为不含管口入池局部损失 $\\zeta_{\\text{出}} = 1.0$，则 $v_2 = \\sqrt{2g \\times 1.3673 / 17.8333} = 1.226\\,\\mathrm{m/s}$，$Q = 0.0217\\,\\mathrm{m^3/s}$，$H = 21.60\\,\\mathrm{m}$，$P = 4.59\\,\\mathrm{kW}$；工程标准表述“总的局部水头损失系数”已包含出口损失，以 $Q = 0.0223\\,\\mathrm{m^3/s}$、$P = 4.72\\,\\mathrm{kW}$ 为准。）",
                "analysisFigures": [
                    {"src": "figures/q10_sol.png", "caption": "解图 10　水泵抽水系统总水头线与水泵扬程构成示意图"}
                ],
                "pitfalls": "1. 列 $2\\text{—}2$ 至 $3\\text{—}3$ 能量方程时，切记出口断面 $2\\text{—}2$ 的位置高程为 $z_2 = h_s = 3\\,\\mathrm{m}$（而非 $0$），故有效位差是 $z_0 - h_s = 17\\,\\mathrm{m}$ 而非 $20\\,\\mathrm{m}$！\n2. 左端切勿遗漏水泵出口断面本身的动能项 $\\frac{v_2^2}{2g}$，移项后系数为 $(\\lambda_2 l_2 / d_2 + \\zeta_2 - 1)$；\n3. 求水泵总扬程 $H$ 时必须包含吸水管段的水头损失 $h_{w1}$，且“有效功率”即水功率 $P = \\rho g Q H$。",
                "chapter": 6,
                "kps": ["水泵扬程与轴功率", "有压管路水力计算", "恒定总流能量方程"],
                "method": "分段能量方程求流量与水泵扬程功率法",
                "difficulty": 3,
                "rubric": [
                    {"label": "对泵出口 2—2 至高水池液面 3—3 列能量方程求得 v2 ≈ 1.26 m/s 及流量 Q ≈ 0.0223 m³/s", "pts": 6},
                    {"label": "计算吸水管损失 hw1 ≈ 0.17 m、压力管损失 hw2 ≈ 1.45 m，求得水泵总扬程 H ≈ 21.62 m", "pts": 5},
                    {"label": "由有效功率公式 P = ρgQH 求得 P ≈ 4.72 kW", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2023-11",
                "year": 2023,
                "no": 11,
                "type": "calc",
                "score": 15,
                "title": "倾斜管路渐缩段镇墩作用力计算",
                "stem": "如图所示管路渐变段剖面图，已知管轴线与水平面夹角 $\\theta = 30^{\\circ}$，渐变段长度 $l = 10\\,\\mathrm{m}$，渐变段中水体重量 $G = 2\\,\\mathrm{kN}$；进水管过水断面面积 $A_1 = 0.0314\\,\\mathrm{m^2}$，流速 $v_1 = 1\\,\\mathrm{m/s}$，表压强水头 $p_1/(\\rho g) = 50\\,\\mathrm{m}$ 水柱高；出水管过水断面面积 $A_2 = 0.00785\\,\\mathrm{m^2}$；不计水头损失，试求：固定渐变段管路镇墩所受的作用力 $R_x^{\\prime}$，$R_z^{\\prime}$。",
                "note": "",
                "figures": [
                    {"src": "figures/q11_orig.png", "caption": "题 11 图　倾斜管路渐变段与镇墩受力坐标系剖面图"}
                ],
                "shortAnswer": "Rx' = 10.89 kN（沿 +x 轴斜向上，即顺水流方向），Rz' = 1.73 kN（沿 -z 轴垂直管轴斜向下；若取 g=9.81 m/s² 则 Rx' = 10.90 kN，Rz' = 1.73 kN）",
                "judgeAnswer": None,
                "answer": "取 $g = 9.80\\,\\mathrm{m/s^2}$，按题 11 图给定正交坐标系 $(x, z)$，固定渐变段管路镇墩所受的作用力为：\n- 沿管轴方向分力：$R_x^{\\prime} = 10.89\\,\\mathrm{kN}$（方向沿 $+x$ 轴斜向上，即顺水流方向；若取 $g = 9.81\\,\\mathrm{m/s^2}$ 则为 $10.90\\,\\mathrm{kN}$）；\n- 垂直管轴方向分力：$R_z^{\\prime} = 1.73\\,\\mathrm{kN}$（精确值 $\\sqrt{3}\\,\\mathrm{kN} \\approx 1.732\\,\\mathrm{kN}$，方向沿 $-z$ 轴垂直于管轴斜向下）。",
                "analysis": "**1. 由连续性方程求流量 $Q$ 与出口断面流速 $v_2$**\n\n$$\nQ = A_1 v_1 = 0.0314 \\times 1 = 0.0314\\,\\mathrm{m^3/s}\n$$\n\n$$\nv_2 = \\frac{Q}{A_2} = \\frac{0.0314}{0.00785} = 4.0\\,\\mathrm{m/s}\n$$\n\n**2. 由能量方程求出口断面表压强水头与两端静水总压力**\n\n以进口断面 $1\\text{—}1$ 形心所在水平面为基准面，则出口断面 $2\\text{—}2$ 形心相对基准面的铅直高程为 $\\Delta h = l \\sin\\theta = 10 \\times \\sin 30^{\\circ} = 5.0\\,\\mathrm{m}$。不计水头损失，取 $\\alpha_1 = \\alpha_2 = 1.0$，$g = 9.80\\,\\mathrm{m/s^2}$，列 $1\\text{—}1$ 至 $2\\text{—}2$ 能量方程：\n\n$$\n0 + \\frac{p_1}{\\rho g} + \\frac{v_1^2}{2g} = l\\sin\\theta + \\frac{p_2}{\\rho g} + \\frac{v_2^2}{2g}\n$$\n\n解得出口断面表压强水头：\n\n$$\n\\frac{p_2}{\\rho g} = 50 - 5.0 + \\frac{1^2 - 4^2}{2 \\times 9.80} = 45.0 - \\frac{15}{19.6} \\approx 44.2347\\,\\mathrm{m}\n$$\n\n两端过水断面上的动水总压力分别为：\n\n$$\nP_1 = \\rho g \\left(\\frac{p_1}{\\rho g}\\right) A_1 = 1000 \\times 9.80 \\times 50 \\times 0.0314 = 15386\\,\\mathrm{N} = 15.386\\,\\mathrm{kN}\n$$\n\n$$\nP_2 = \\rho g \\left(\\frac{p_2}{\\rho g}\\right) A_2 = 1000 \\times 9.80 \\times 44.2347 \\times 0.00785 \\approx 3403.0\\,\\mathrm{N} = 3.403\\,\\mathrm{kN}\n$$\n\n**3. 对渐变段水体控制体列 $x$、$z$ 向动量方程求镇墩受力**\n\n取 $1\\text{—}1$ 至 $2\\text{—}2$ 断面间水体为控制体（见解图 11）。按题 11 图所示方向，设管壁（镇墩）对水体的反作用力为 $R_x$（指向 $-x$ 方向）和 $R_z$（指向 $+z$ 方向），水体重力 $G = 2\\,\\mathrm{kN} = 2000\\,\\mathrm{N}$ 竖直向下，分解到斜坐标系得 $G_x = -G\\sin 30^{\\circ} = -1.000\\,\\mathrm{kN}$，$G_z = -G\\cos 30^{\\circ} = -1.732\\,\\mathrm{kN}$。取 $\\beta_1 = \\beta_2 = 1.0$：\n\n- **沿管轴 $+x$ 方向动量方程**：\n\n$$\nP_1 - P_2 - G\\sin 30^{\\circ} - R_x = \\rho Q (v_2 - v_1)\n$$\n\n其中动量通量差 $\\rho Q (v_2 - v_1) = 1000 \\times 0.0314 \\times (4.0 - 1.0) = 94.2\\,\\mathrm{N} = 0.0942\\,\\mathrm{kN}$，解得：\n\n$$\nR_x = 15.386 - 3.403 - 1.000 - 0.0942 = 10.8888\\,\\mathrm{kN} \\approx 10.89\\,\\mathrm{kN}\n$$\n\n- **垂直管轴 $+z$ 方向动量方程**（法向进出流速分量为零）：\n\n$$\nR_z - G\\cos 30^{\\circ} = 0 \\implies R_z = 2 \\times \\cos 30^{\\circ} = \\sqrt{3}\\,\\mathrm{kN} \\approx 1.732\\,\\mathrm{kN}\n$$\n\n由牛顿第三定律（且忽略未给管壳自重），水流通过管壁作用于镇墩的推力与 $R_x$、$R_z$ 等值反向，即：\n- **$R_x^{\\prime} = 10.89\\,\\mathrm{kN}$**，方向沿 $+x$ 轴斜向上（顺水流方向）；\n- **$R_z^{\\prime} = 1.73\\,\\mathrm{kN}$**，方向沿 $-z$ 轴垂直管轴斜向下。",
                "analysisFigures": [
                    {"src": "figures/q11_sol.png", "caption": "解图 11　倾斜渐缩段水体控制体受力分解与镇墩反力示意图"}
                ],
                "pitfalls": "1. 题 11 图中坐标系 $(x, z)$ 是**随管道倾斜旋转的正交坐标系**（$x$ 沿管轴斜向上 $30^{\\circ}$，$z$ 垂直管轴斜向上），切忌误当成水平与铅直坐标系！\n2. 倾斜管道列能量方程时千万不要漏掉出口比进口升高的位置水头 $l\\sin 30^{\\circ} = 5.0\\,\\mathrm{m}$，动量方程中也切勿漏掉水体自重分力 $G\\sin 30^{\\circ}$ 和 $G\\cos 30^{\\circ}$！",
                "chapter": 3,
                "kps": ["闸门与弯管动水总压力", "恒定总流动量方程", "恒定总流能量方程"],
                "method": "能量方程求压强+控制体动量方程求镇墩力",
                "difficulty": 3,
                "rubric": [
                    {"label": "由连续性方程求出流量 Q = 0.0314 m³/s 及出口断面流速 v2 = 4.0 m/s", "pts": 3},
                    {"label": "计入位置高差 l·sin30° = 5 m 列能量方程求得 p2/(ρg) ≈ 44.23 m 及压力 P1=15.39 kN、P2=3.40 kN", "pts": 5},
                    {"label": "沿倾斜坐标轴分解重力 G，列 x、z 向动量方程求出 Rx=10.89 kN、Rz=1.73 kN", "pts": 5},
                    {"label": "应用牛顿第三定律明确镇墩所受作用力 Rx'、Rz' 的大小与方向", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2023-12",
                "year": 2023,
                "no": 12,
                "type": "calc",
                "score": 15,
                "title": "梯形断面引水渠道恒定均匀流实测糙率反算",
                "stem": "为了收集某引水渠道糙率的资料，经实测得渠中流量 $Q = 9.45\\,\\mathrm{m^3/s}$ 时，水深 $h = 1.20\\,\\mathrm{m}$；在长 $l = 200\\,\\mathrm{m}$ 的渠段内，水面降落 $\\Delta z = 0.16\\,\\mathrm{m}$。渠中水流近似为恒定均匀流。渠道横断面为梯形：底宽 $b = 7.0\\,\\mathrm{m}$，边坡系数 $m = 1.5$。试确定该渠道的糙率值。",
                "note": "",
                "figures": [],
                "shortAnswer": "n ≈ 0.030（精确计算值 0.0302）",
                "judgeAnswer": None,
                "answer": "该梯形引水渠道的糙率值为 $n \\approx 0.030$（保留四位小数为 $0.0302$）。",
                "analysis": "**1. 计算梯形过水断面水力要素（$A$、$\\chi$、$R$）**\n\n已知梯形渠道底宽 $b = 7.0\\,\\mathrm{m}$，边坡系数 $m = 1.5$，均匀流水深 $h = 1.20\\,\\mathrm{m}$：\n\n- 过水断面面积 $A$：\n\n$$\nA = (b + m h) h = (7.0 + 1.5 \\times 1.20) \\times 1.20 = 8.80 \\times 1.20 = 10.56\\,\\mathrm{m^2}\n$$\n\n- 湿周 $\\chi$：\n\n$$\n\\chi = b + 2 h \\sqrt{1 + m^2} = 7.0 + 2 \\times 1.20 \\times \\sqrt{1 + 1.5^2} = 7.0 + 2.40 \\times \\sqrt{3.25} \\approx 7.0 + 4.3267 = 11.3267\\,\\mathrm{m}\n$$\n\n- 水力半径 $R$：\n\n$$\nR = \\frac{A}{\\chi} = \\frac{10.56}{11.3267} \\approx 0.9323\\,\\mathrm{m}\n$$\n\n**2. 确定水力坡度 $J$ 与断面平均流速 $v$**\n\n因渠中水流近似为明渠恒定均匀流，总水头线坡度（水力坡度）$J$、水面坡度 $J_p$ 与渠底坡度 $i$ 相等：\n\n$$\nJ = i = \\frac{\\Delta z}{l} = \\frac{0.16}{200} = 0.0008 = 8.0 \\times 10^{-4}\n$$\n\n断面平均流速为：\n\n$$\nv = \\frac{Q}{A} = \\frac{9.45}{10.56} \\approx 0.8949\\,\\mathrm{m/s}\n$$\n\n**3. 由谢才—曼宁公式反求渠道糙率 $n$**\n\n根据明渠均匀流谢才公式 $v = C\\sqrt{R i}$ 与曼宁公式 $C = \\frac{1}{n}R^{1/6}$，联立得流量公式：\n\n$$\nQ = \\frac{1}{n} A R^{2/3} i^{1/2}\n$$\n\n解得渠道糙率值 $n$：\n\n$$\nn = \\frac{A R^{2/3} i^{1/2}}{Q} = \\frac{10.56 \\times 0.9323^{2/3} \\times \\sqrt{0.0008}}{9.45} = \\frac{10.56 \\times 0.9544 \\times 0.028284}{9.45} \\approx 0.03016 \\approx 0.030\n$$",
                "analysisFigures": [],
                "pitfalls": "1. 计算梯形湿周 $\\chi = b + 2h\\sqrt{1+m^2}$ 时，切勿误把水面宽 $B = b + 2mh$ 加进湿周（自由水面与空气接触不计入湿周）！\n2. 曼宁糙率 $n$ 一般保留至小数点后三位有效工程精度（如 $0.014$、$0.025$、$0.030$），本题算得 $0.03016$ 即典型土质无护面引水渠的糙率 $n = 0.030$。",
                "chapter": 7,
                "kps": ["曼宁公式", "明渠均匀流特点", "梯形断面水力要素"],
                "method": "谢才—曼宁公式明渠均匀流反算糙率法",
                "difficulty": 2,
                "rubric": [
                    {"label": "正确计算梯形过水断面积 A = 10.56 m²、湿周 χ ≈ 11.33 m 及水力半径 R ≈ 0.932 m", "pts": 6},
                    {"label": "由均匀流三线平行关系求得水力坡度 i = J = Δz/l = 0.0008", "pts": 4},
                    {"label": "代入谢才—曼宁公式 Q = (1/n)AR^(2/3)i^(1/2) 反解得出渠道糙率 n ≈ 0.030", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2023-13",
                "year": 2023,
                "no": 13,
                "type": "calc",
                "score": 15,
                "title": "已知平面流函数判别速度势函数是否存在",
                "stem": "已知平面流动的流函数为 $\\psi = 3xy + 2x^2$，判断是否有势函数存在，若有，求势函数。",
                "note": "",
                "figures": [],
                "shortAnswer": "无势函数存在（因为 ∇²ψ = ∂²ψ/∂x² + ∂²ψ/∂y² = 4 ≠ 0，即旋转角速度 ωz ≠ 0，该平面流动为有旋流，故不存在速度势函数）。",
                "judgeAnswer": None,
                "answer": "该平面流动为**有旋流动**（$\\nabla^2 \\psi = 4 \\neq 0$，旋转角速度 $\\omega_z \\neq 0$），故**不存在速度势函数**。",
                "analysis": "**1. 由流函数 $\\psi$ 导出平面流速分量 $u_x$、$u_y$**\n\n对于不可压缩平面流动，已知流函数 $\\psi(x, y) = 3xy + 2x^2$，流速分量与流函数的关系为：\n\n$$\nu_x = \\frac{\\partial \\psi}{\\partial y} = \\frac{\\partial (3xy + 2x^2)}{\\partial y} = 3x\n$$\n\n$$\nu_y = -\\frac{\\partial \\psi}{\\partial x} = -\\frac{\\partial (3xy + 2x^2)}{\\partial x} = -3y - 4x\n$$\n\n（注：若教材采用反号约定 $u_x = -\\frac{\\partial\\psi}{\\partial y} = -3x$、$u_y = \\frac{\\partial\\psi}{\\partial x} = 3y + 4x$，下述无旋性判别结论完全相同。）\n\n**2. 检验流动的无旋性（速度势函数 $\\varphi$ 存在的充要条件）**\n\n单连通区域内平面流场存在速度势函数 $\\varphi(x, y)$（满足 $u_x = \\frac{\\partial \\varphi}{\\partial x}$，$u_y = \\frac{\\partial \\varphi}{\\partial y}$，即使 $u_x\\,\\mathrm{d}x + u_y\\,\\mathrm{d}y$ 成为全微分）的充要条件是**流动无旋**，即绕 $z$ 轴旋转角速度分量 $\\omega_z = 0$（等价于流函数满足拉普拉斯方程 $\\nabla^2 \\psi = 0$）：\n\n- **方法一（计算旋转角速度 $\\omega_z$）**：\n\n$$\n\\omega_z = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} - \\frac{\\partial u_x}{\\partial y}\\right) = \\frac{1}{2}\\left[\\frac{\\partial (-3y - 4x)}{\\partial x} - \\frac{\\partial (3x)}{\\partial y}\\right] = \\frac{1}{2}(-4 - 0) = -2 \\neq 0\n$$\n\n- **方法二（直接验证流函数拉普拉斯方程 $\\nabla^2 \\psi = 0$）**：\n\n$$\n\\frac{\\partial^2 \\psi}{\\partial x^2} + \\frac{\\partial^2 \\psi}{\\partial y^2} = \\frac{\\partial (3y + 4x)}{\\partial x} + \\frac{\\partial (3x)}{\\partial y} = 4 + 0 = 4 \\neq 0\n$$\n\n**3. 结论**\n\n因 $\\omega_z = -2 \\neq 0$（$\\nabla^2 \\psi = 4 \\neq 0$），微分式 $u_x\\,\\mathrm{d}x + u_y\\,\\mathrm{d}y = 3x\\,\\mathrm{d}x - (4x + 3y)\\,\\mathrm{d}y$ 不满足全微分条件（$\\frac{\\partial u_x}{\\partial y} = 0 \\neq \\frac{\\partial u_y}{\\partial x} = -4$），说明该流场为**不可压缩平面有旋流动**，因此**没有势函数存在**。",
                "analysisFigures": [],
                "pitfalls": "这是一道经典的“反向设问防套路题”！切忌不经无旋检验（$\\nabla^2 \\psi = 0$）就盲目对 $\\frac{\\partial \\varphi}{\\partial x} = u_x$ 偏积分去强凑 $\\varphi$——任何不可压缩平面流都存在流函数 $\\psi$，但**只有无旋流（$\\omega_z = 0$）才存在势函数 $\\varphi$**！",
                "chapter": 5,
                "kps": ["流函数与势函数", "有旋流与无旋流判别", "拉普拉斯方程"],
                "method": "流函数拉普拉斯无旋判据与柯西—黎曼积分法",
                "difficulty": 3,
                "rubric": [
                    {"label": "由流函数 ψ = 3xy + 2x² 正确求出平面流速分量 ux = 3x、uy = -3y - 4x", "pts": 5},
                    {"label": "写出势函数存在的无旋充要条件 ωz = (∂uy/∂x - ∂ux/∂y)/2 = 0（或 ∇²ψ = 0）", "pts": 5},
                    {"label": "算得 ∂uy/∂x - ∂ux/∂y = -4 ≠ 0（∇²ψ = 4 ≠ 0），明确判定为有旋流、无势函数存在", "pts": 5}
                ]
            }
        ]
    }


# ==============================================================================
# 2022 EXAM DATA (15 questions, totalScore = 150)
# ==============================================================================

def build_2022_paper() -> dict:
    return {
        "year": 2022,
        "code": "849",
        "subject": "水力学（水）",
        "school": "扬州大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": True,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "全卷分三大题共 15 小题：一、简答题（8×5 = 40 分）；二、计算题（6×15 = 90 分）；三、综合题（1×20 = 20 分）。",
            "除特别说明外，计算统一取重力加速度 $g = 9.80\\,\\mathrm{m/s^2}$，水的密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$（解析同步附 $g = 9.81\\,\\mathrm{m/s^2}$ 对照结果）。"
        ],
        "sections": [
            {
                "id": "short",
                "title": "一、简答题",
                "description": "本大题共 8 小题，每小题 5 分，共 40 分。",
                "range": [1, 8],
                "scorePerQuestion": 5,
                "totalScore": 40
            },
            {
                "id": "calc",
                "title": "二、计算题",
                "description": "本大题共 6 题，每题 15 分，共 90 分。",
                "range": [9, 14],
                "scorePerQuestion": 15,
                "totalScore": 90
            },
            {
                "id": "comp",
                "title": "三、综合题",
                "description": "本大题共 1 小题，20 分。",
                "range": [15, 15],
                "scorePerQuestion": 20,
                "totalScore": 20
            }
        ],
        "questions": [
            {
                "id": "yzu-849-2022-01",
                "year": 2022,
                "no": 1,
                "type": "short",
                "score": 5,
                "title": "运动黏度与动力黏度的换算关系、单位及量纲",
                "stem": "运动粘度和动力粘度存在什么关系，写出各自单位和量纲。",
                "note": "",
                "figures": [],
                "shortAnswer": "关系：ν = μ / ρ（运动黏度等于动力黏度与流体密度之比）。动力黏度 μ：国际单位 Pa·s（或 N·s/m²、kg/(m·s)），量纲 M·L⁻¹·T⁻¹（工程力制 F·T·L⁻²）；运动黏度 ν：国际单位 m²/s，量纲 L²·T⁻¹。",
                "judgeAnswer": None,
                "answer": "**1. 两者关系**：流体的运动黏度 $\\nu$ 等于动力黏度 $\\mu$ 与同温度下流体密度 $\\rho$ 的比值，即：\n\n$$\n\\nu = \\frac{\\mu}{\\rho}\n$$\n\n**2. 国际单位与量纲**：\n- **动力黏度 $\\mu$**：国际单位为 $\\mathrm{Pa\\cdot s}$（或写作 $\\mathrm{N\\cdot s/m^2}$、$\\mathrm{kg/(m\\cdot s)}$）；以质量系统 $[\\mathrm{M}, \\mathrm{L}, \\mathrm{T}]$ 表示量纲为 $\\mathrm{M\\,L^{-1}\\,T^{-1}}$（若以工程力系统 $[\\mathrm{F}, \\mathrm{L}, \\mathrm{T}]$ 表示则为 $\\mathrm{F\\,T\\,L^{-2}}$）。\n- **运动黏度 $\\nu$**：国际单位为 $\\mathrm{m^2/s}$；量纲仅含长度与时间（与运动学物理量同形，故称运动黏度），为 $\\mathrm{L^2\\,T^{-1}}$。",
                "analysis": "**由牛顿内摩擦定律验证单位与量纲**\n\n由 $\\tau = \\mu \\frac{\\mathrm{d}u}{\\mathrm{d}y}$ 得 $\\mu = \\frac{\\tau}{\\mathrm{d}u/\\mathrm{d}y}$：\n- 切应力 $\\tau$ 的单位为 $\\mathrm{N/m^2 = Pa}$，速度梯度 $\\frac{\\mathrm{d}u}{\\mathrm{d}y}$ 的单位为 $\\frac{\\mathrm{m/s}}{\\mathrm{m}} = \\mathrm{s^{-1}}$，故 $\\mu$ 的单位为 $\\mathrm{Pa\\cdot s} = \\mathrm{N\\cdot s/m^2} = \\mathrm{kg/(m\\cdot s)}$，量纲 $[\\mu] = \\frac{\\mathrm{M\\,L\\,T^{-2}\\,L^{-2}}}{\\mathrm{T^{-1}}} = \\mathrm{M\\,L^{-1}\\,T^{-1}}$；\n- 再除以密度 $\\rho$（单位 $\\mathrm{kg/m^3}$，量纲 $\\mathrm{M\\,L^{-3}}$），得 $[\\nu] = \\frac{[\\mu]}{[\\rho]} = \\frac{\\mathrm{M\\,L^{-1}\\,T^{-1}}}{\\mathrm{M\\,L^{-3}}} = \\mathrm{L^2\\,T^{-1}}$，单位为 $\\mathrm{m^2/s}$。",
                "analysisFigures": [],
                "pitfalls": "注意区分动力黏度单位是 $\\mathrm{N\\cdot s/m^2}$（即 $\\mathrm{Pa\\cdot s}$），切勿把分子分母写反或漏乘秒 $\\mathrm{s}$！写量纲时必须用标准指数形式 $\\mathrm{M\\,L^{-1}\\,T^{-1}}$ 和 $\\mathrm{L^2\\,T^{-1}}$，切勿把单位符号 $\\mathrm{m, s, kg}$ 误当作量纲符号。",
                "chapter": 1,
                "kps": ["液体黏滞性", "动力黏度与运动黏度", "物理量纲分析"],
                "method": "牛顿内摩擦定律量纲导出法",
                "difficulty": 1,
                "rubric": [
                    {"label": "正确写出运动黏度与动力黏度的关系式 ν = μ / ρ", "pts": 1},
                    {"label": "正确写出动力黏度 μ 的国际单位 Pa·s（N·s/m²）与量纲 M·L⁻¹·T⁻¹", "pts": 2},
                    {"label": "正确写出运动黏度 ν 的国际单位 m²/s 与量纲 L²·T⁻¹", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2022-02",
                "year": 2022,
                "no": 2,
                "type": "short",
                "score": 5,
                "title": "结合示意图简述毕托管（Pitot 管）测量点流速的原理",
                "stem": "试结合图形简述毕托管测流速的原理。",
                "note": "",
                "figures": [],
                "shortAnswer": "在待测点同时设置开口正对来流的毕托管（总压管）与开口平行于来流的测压管（静压管）：驻点 A 处流速滞止为零（uA=0），动能全部转化为压能，毕托管液面反映总水头 h2 = p/(ρg) + u²/(2g)；静压管液面仅反映静压强水头 h1 = p/(ρg)。由两管液面高度差 Δh = h2 - h1 = u²/(2g) 即可求得点流速 u = φ√(2gΔh)。",
                "judgeAnswer": None,
                "answer": "**毕托管测速原理（测速装置简图见解图 2）**：\n1. **构造布置**：将一根 $90^{\\circ}$ 弯折细管（总压管 / 毕托管）前端小孔正对来流方向置于待测点前缘，同时在同高程邻近处设置小孔垂直于流向（不阻滞水流）的普通测压管（或采用内外双层同轴毕托—静压管）；\n2. **能量转换与伯努利方程**：正对毕托管管口的流线在管口前缘驻点 $A$ 处受阻完全滞止，流速降为零（$u_A = 0$），流体质点原有的单位重量动能 $\\frac{u^2}{2g}$ 全部转化为驻点增压水头。对来流未扰动点与驻点 $A$ 列同高程理想伯努利方程：\n\n$$\n\\frac{p}{\\rho g} + \\frac{u^2}{2g} = \\frac{p_A}{\\rho g} + 0\n$$\n\n3. **液面高差求流速**：静压测压管液柱高度测量的是静压水头 $h_1 = \\frac{p}{\\rho g}$，毕托管液柱高度测量的是驻点总水头 $h_2 = \\frac{p_A}{\\rho g} = \\frac{p}{\\rho g} + \\frac{u^2}{2g}$。两管液面高度差 $\\Delta h = h_2 - h_1 = \\frac{u^2}{2g}$ 恰好等于该点流速水头，考虑管头绕流微扰引入校正系数 $\\varphi$（约 $0.98\\sim 1.00$），即得待测点实际流速：\n\n$$\nu = \\varphi\\sqrt{2 g \\Delta h} = \\varphi\\sqrt{2 g (h_2 - h_1)}\n$$",
                "analysis": "**关键物理概念强调**\n\n- 毕托管测量的是流场中**局部空间点流速 $u$**（而非管道断面平均流速 $v$，这是毕托管与文丘里流量计的核心区别！）；\n- 示意图必须画出两根对照液柱（或同轴管接压差计）：一根开口平行流线测静压水头 $h_1$，一根弯头正迎流线测总水头 $h_2$，并标出两者液面差 $\\Delta h = h_2 - h_1 = \\frac{u^2}{2g}$。",
                "analysisFigures": [
                    {"src": "figures/q02_sol.png", "caption": "解图 2　毕托管（总压管）与静压测压管组合测量点流速原理图"}
                ],
                "pitfalls": "切忌只画一根弯头总压管而漏画测静压的测压管！若无静压水头 $h_1 = p/(\\rho g)$ 作为减数（除非在自由液面极浅处已知水深），单靠一根总压管读数 $h_2$ 是无法分离出流速水头 $\\Delta h = h_2 - h_1$ 的。",
                "chapter": 3,
                "kps": ["毕托管测速原理", "驻点与总水头", "伯努利方程测流"],
                "method": "驻点滞止增压与总静压差测点速法",
                "difficulty": 2,
                "rubric": [
                    {"label": "正确画出包含正对来流总压管（驻点 A）与垂直流向静压管及液面高差 Δh 的原理简图", "pts": 2},
                    {"label": "结合伯努利方程阐明驻点流速为零、动能转化为压能，两管液面差 Δh = h2 - h1 = u²/(2g)", "pts": 2},
                    {"label": "写出点流速计算式 u = φ√(2gΔh)（或理论式 √(2gΔh)）", "pts": 1}
                ]
            },
            {
                "id": "yzu-849-2022-03",
                "year": 2022,
                "no": 3,
                "type": "short",
                "score": 5,
                "title": "水静力学基本公式中压强基准（绝对压强与相对压强）的一致性分析",
                "stem": "水静力学基本公式 $p = p_0 + \\rho g h$ 中，压强 $p$ 是相对压强还是绝对压强？或两者均可？为什么？",
                "note": "",
                "figures": [],
                "shortAnswer": "两者均可，但公式两端的 p 与液面压强 p0 必须采用同一压强计量基准（同为绝对压强或同为相对压强）。因为相对压强等于绝对压强减去当地大气压 pa，方程两边同减 pa 后完全等价。",
                "judgeAnswer": None,
                "answer": "**结论**：**两者均可**（既可以是绝对压强，也可以是相对压强），前提是公式左端的点压强 $p$ 与右端的液面压强 $p_0$ **必须采用同一种压强计量基准**（即同为绝对压强，或同为相对压强）。\n\n**原因证明**：\n绝对压强是以绝对真空为零点计量的压强，相对压强（表压强）是以当地大气压强 $p_a$ 为零点计量的压强，两者相差一个常数 $p_a$：\n\n$$\np_{\\text{绝}} = p_{\\text{相}} + p_a, \\qquad p_{0,\\text{绝}} = p_{0,\\text{相}} + p_a\n$$\n\n若以绝对压强写出水静力学基本公式：\n\n$$\np_{\\text{绝}} = p_{0,\\text{绝}} + \\rho g h\n$$\n\n将上式两端同时减去当地大气压强 $p_a$，$p_a$ 严格抵消，即得相对压强形式：\n\n$$\np_{\\text{绝}} - p_a = (p_{0,\\text{绝}} - p_a) + \\rho g h \\implies p_{\\text{相}} = p_{0,\\text{相}} + \\rho g h\n$$\n\n可见两种计量基准只是零点平移了 $p_a$，公式形式完全不变（特别地，当自由液面通大气时，$p_{0,\\text{相}} = 0$，相对压强简化为 $p_{\\text{相}} = \\rho g h$）。",
                "analysis": "**延伸提醒**：在水力学所有仅含压强差或两端同现一次压强的方程（如静水基本方程、不可压缩伯努利方程）中，绝对压强与相对压强均可通用，唯一铁律是**全式基准统一**，绝不可左端代相对压强而右端代绝对压强。",
                "analysisFigures": [],
                "pitfalls": "答题除了回答“两者均可”和写出 $p_{\\text{相}} = p_{\\text{绝}} - p_a$ 代入消去 $p_a$ 的过程外，务必强调一句限制条件：“**同一方程中 $p$ 与 $p_0$ 必须采用同一计量标准**”，否则逻辑不够严密。",
                "chapter": 2,
                "kps": ["绝对压强与相对压强", "静水压强基本方程"],
                "method": "压强零点平移消元验证法",
                "difficulty": 1,
                "rubric": [
                    {"label": "明确回答两者均可，并指出前提是 p 与 p0 必须采用同一压强基准", "pts": 2},
                    {"label": "利用 p绝 = p相 + pa 代入基本公式证明两边大气压 pa 相互抵消，形式完全不变", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2022-04",
                "year": 2022,
                "no": 4,
                "type": "short",
                "score": 5,
                "title": "均匀流过水断面上各点单位重量液体势能与总机械能的分布特性",
                "stem": "均匀流过水断面上，各点单位重量液体的势能是否为常数？各点单位重量液体的总机械能是否为常数？请分别说明理由。",
                "note": "",
                "figures": [],
                "shortAnswer": "（1）单位重量液体的势能（测压管水头 z + p/(ρg)）是常数，因均匀流流线为平行直线、法向加速度为零，同一过水断面上动水压强服从静水压强分布规律；（2）单位重量液体的总机械能（z + p/(ρg) + u²/(2g)）不是常数，因实际流体具有黏滞性，固壁处无滑移 u=0 而流束中心流速最大，各点动能 u²/(2g) 不相等。",
                "judgeAnswer": None,
                "answer": "**（1）均匀流同一过水断面上，各点单位重量液体的势能是常数**。\n**理由**：单位重量液体的总势能即测压管水头 $E_p = z + \\frac{p}{\\rho g}$（位置势能 $z$ 与压强势能 $\\frac{p}{\\rho g}$ 之和）。均匀流的流线为互相平行的直线，过水断面为平面，流体质点沿过水断面方向的速度分量和法向向心加速度均为零，仅受重力作用，因此同一过水断面上动水压强严格服从静水压强分布规律：\n\n$$\nz + \\frac{p}{\\rho g} = C\\;(\\text{常数})\n$$\n\n**（2）均匀流同一过水断面上，各点单位重量液体的总机械能不是常数**。\n**理由**：空间某点单位重量液体的总机械能为总水头 $e = z + \\frac{p}{\\rho g} + \\frac{u^2}{2g}$（其中 $u$ 为该点局部流速）。虽然同一过水断面上势能项 $z + \\frac{p}{\\rho g} = C$ 处处相等，但实际液体具有黏滞性，受固壁无滑移条件约束，断面上流速分布不均匀（管壁或渠底处 $u = 0$，向流束中心 $u$ 逐渐增大至 $u_{\\max}$），导致各点单位重量动能 $\\frac{u^2}{2g}$ 互不相等，故各点总机械能 $e = C + \\frac{u^2}{2g}$ 不是常数（中心最大、壁面最小）。",
                "analysis": "**概念辨析：点机械能 $e$ 与总流断面平均比能 $E$**\n\n- 对于过水断面上的**不同空间点**：点总水头 $e(y,z) = \\left(z + \\frac{p}{\\rho g}\\right) + \\frac{u^2(y,z)}{2g}$ 随点流速 $u$ 变化，不是常数；\n- 正是因为同一断面上各点 $e$ 不相等，在对整个过水断面流量积分求**断面平均单位重量总机械能**时，才必须引入动能修正系数 $\\alpha = \\frac{\\int_A u^3\\,\\mathrm{d}A}{v^3 A} > 1$，写为 $E = z + \\frac{p}{\\rho g} + \\frac{\\alpha v^2}{2g}$。",
                "analysisFigures": [],
                "pitfalls": "说明第二问理由时，公式中应写**空间点局部流速 $u$**（$\\frac{u^2}{2g}$ 随空间位置变化），切勿误写成已经对全断面平均过的常数 $\\frac{\\alpha v^2}{2g}$！",
                "chapter": 3,
                "kps": ["均匀流过水断面压强分布", "单位重量液体势能与总水头", "黏性流体流速分布"],
                "method": "势能静水分布与黏性流速梯度叠加分析法",
                "difficulty": 2,
                "rubric": [
                    {"label": "答出单位重量势能 z + p/(ρg) 是常数，并说明流线平行平直、服从静水压强分布规律", "pts": 2},
                    {"label": "答出单位重量总机械能 z + p/(ρg) + u²/(2g) 不是常数，并结合黏性流速分布不均（u 各点不同）说明理由", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2022-05",
                "year": 2022,
                "no": 5,
                "type": "short",
                "score": 5,
                "title": "输水管与输油管在等流速或等雷诺数条件下的 Re、hf 与 Rek 对比",
                "stem": "有两根 $d$、$l$、$\\Delta$ 及液体温度均相同的管道，一根输水，另一根输油，若断面平均流速 $v$ 相等，$Re$、$h_f$ 是否相等？若 $Re$ 相等，$v$、$h_f$ 是否相等？两管的 $Re_k$ 是否相等？",
                "note": "",
                "figures": [],
                "shortAnswer": "（1）v 相等时：因 ν水 ≠ ν油，Re 不相等；若两管均处于湍流阻力平方区（λ 仅取决于 Δ/d）则 hf 相等，处于其余流区则 λ 不同故 hf 不相等。（2）Re 相等时：由 v = Re·ν/d 知 v 不相等；虽 Re 与 Δ/d 均相同使 λ 相等，但因 v 不等，由 hf = λ(l/d)v²/(2g) 知 hf 不相等。（3）两管下临界雷诺数 Rek 相等（圆管均为 2000 左右）。",
                "judgeAnswer": None,
                "answer": "同温度下水与油的运动黏度不同（$\\nu_{\\text{油}} > \\nu_{\\text{水}}$），且两管 $d$、$l$、相对粗糙度 $\\frac{\\Delta}{d}$ 均相同：\n\n**（1）当断面平均流速 $v$ 相等时**：\n- **$Re$ 不相等**：由 $Re = \\frac{vd}{\\nu}$，$v, d$ 相同而 $\\nu_{\\text{水}} \\neq \\nu_{\\text{油}}$，故 $Re_{\\text{水}} > Re_{\\text{油}}$；\n- **$h_f$ 分流区讨论**：由达西公式 $h_f = \\lambda\\frac{l}{d}\\frac{v^2}{2g}$，若两管流动**均处于湍流粗糙管区（阻力平方区）**，则 $\\lambda = f\\left(\\frac{\\Delta}{d}\\right)$ 与 $Re$ 无关，两管 $\\lambda$ 相等，此时 **$h_f$ 相等**；若任一管处于层流区、过渡区、湍流光滑区或湍流过渡粗糙区，$\\lambda = f\\left(Re, \\frac{\\Delta}{d}\\right)$ 随 $Re$ 不同而异，此时 **$h_f$ 不相等**（$h_{f,\\text{油}} > h_{f,\\text{水}}$）。\n\n**（2）当雷诺数 $Re$ 相等时**：\n- **$v$ 不相等**：由 $v = \\frac{Re\\,\\nu}{d}$，$Re, d$ 相同而 $\\nu_{\\text{油}} > \\nu_{\\text{水}}$，故 $v_{\\text{油}} > v_{\\text{水}}$；\n- **$h_f$ 不相等**：因两管 $Re$ 与 $\\frac{\\Delta}{d}$ 均相等，由尼古拉兹/莫迪图知两管沿程阻力系数 $\\lambda$ 必相等，但 $h_f = \\lambda\\frac{l}{d}\\frac{v^2}{2g} \\propto v^2$，由于 $v$ 不相等，故 **$h_f$ 不相等**（$h_{f,\\text{油}} > h_{f,\\text{水}}$）。\n\n**（3）两管的临界雷诺数 $Re_k$ 相等**：\n圆管层流转捩为湍流的下临界雷诺数 $Re_k$ 是无量纲相似准则数（工程统一取 $Re_k = 2000$ 或 $2300$），仅取决于管道几何类型而与所输流体种类无关，故两管 **$Re_k$ 相等**。",
                "analysis": "**核心易混点梳理**\n\n- 莫迪图（Moody diagram）表明圆管沿程摩阻系数 $\\lambda = f\\left(Re, \\frac{\\Delta}{d}\\right)$：\n  - 等 $v$ 时，$\\frac{v^2}{2g}$ 相等，比的是 $\\lambda$ 是否相等——只有在**阻力平方区** $\\lambda$ 脱离 $Re$ 独立由 $\\frac{\\Delta}{d}$ 决定，才会出现 $h_f$ 相等的特例；\n  - 等 $Re$ 时，$\\lambda$ 严格相等，但 $\\frac{v^2}{2g} = \\frac{Re^2 \\nu^2}{2 g d^2}$ 因 $\\nu$ 不同而相差悬殊，故 $h_f$ 绝不相等。",
                "analysisFigures": [],
                "pitfalls": "第（1）问判断等流速下的 $h_f$ 时，千万不要漏掉“**若同处于阻力平方区则 $h_f$ 相等，其余各区 $h_f$ 不等**”这一关键分类讨论！这是尼古拉兹实验五区规律最经典的考点。",
                "chapter": 4,
                "kps": ["沿程与局部损失", "尼古拉兹实验与莫迪图", "雷诺数与临界雷诺数"],
                "method": "达西公式与莫迪图五区分类对比法",
                "difficulty": 3,
                "rubric": [
                    {"label": "v 相等时判出 Re 不等，并分阻力平方区（hf 相等）与其余流区（hf 不等）正确讨论 hf", "pts": 2},
                    {"label": "Re 相等时判出 v 不等、λ 虽相等但因 v² 不同故 hf 不相等", "pts": 2},
                    {"label": "明确指出下临界雷诺数 Rek 与流体种类无关，两管 Rek 相等（约 2000）", "pts": 1}
                ]
            },
            {
                "id": "yzu-849-2022-06",
                "year": 2022,
                "no": 6,
                "type": "short",
                "score": 5,
                "title": "明渠水流三种流态及其水深、流速与弗劳德数特征",
                "stem": "明渠水流存在哪几种流态？试从水深、流速等方面说明各流态的特征。",
                "note": "",
                "figures": [],
                "shortAnswer": "按重力影响（弗劳德数 Fr）分为急流、缓流、临界流三种流态（按黏性影响也可分层流与湍流，明渠通常为湍流）。设临界水深为 hk、临界流速及微波相对波速为 vk = c = √(gh)（矩形断面）：①缓流：h > hk，v < c，Fr < 1，干扰波能向上游传播；②临界流：h = hk，v = c，Fr = 1，断面比能最小，干扰波恰停滞不向上游传播；③急流：h < hk，v > c，Fr > 1，干扰波不能向上游传播。",
                "judgeAnswer": None,
                "answer": "明渠水流按重力与惯性力对比关系（弗劳德数 $Fr = \\frac{v}{\\sqrt{g\\bar{h}}}$）可分为**缓流、临界流、急流**三种流态（注：若按黏滞力与惯性力之比 $Re$ 亦可分为层流与湍流，工程明渠水流绝大多数为湍流）。设相应流量下的临界水深为 $h_k$、临界流速（等于重力浅水微波相对传播波速 $c = \\sqrt{g\\bar{h}}$）为 $v_k$，三种流态特征如下：\n\n1. **缓流（Subcritical flow）**：\n   - **水深特征**：实际水深大于临界水深（$h > h_k$）；\n   - **流速与波速特征**：断面平均流速小于临界流速及微波波速（$v < v_k$ 且 $v < c = \\sqrt{g\\bar{h}}$），弗劳德数 $Fr < 1$；\n   - **传播与控制特征**：表面微小扰动波能够逆流向上游传播（$v - c < 0$），下游边界条件影响上游水深（由下游控制）。\n\n2. **临界流（Critical flow）**：\n   - **水深特征**：实际水深等于临界水深（$h = h_k$）；\n   - **流速与波速特征**：断面平均流速等于临界流速及微波波速（$v = v_k = c = \\sqrt{g\\bar{h}}$），弗劳德数 $Fr = 1$；\n   - **比能与传播特征**：一定流量下断面比能 $E_s$ 取得最小值，微小扰动波向上游的绝对传播速度为零（停滞于原处）。\n\n3. **急流（Supercritical flow）**：\n   - **水深特征**：实际水深小于临界水深（$h < h_k$）；\n   - **流速与波速特征**：断面平均流速大于临界流速及微波波速（$v > v_k$ 且 $v > c = \\sqrt{g\\bar{h}}$），弗劳德数 $Fr > 1$；\n   - **传播与控制特征**：水深浅、流速急、动能占优，表面扰动波无法向上游传播（被水流冲向下游），流态受上游控制。",
                "analysis": "对于一般任意形状明渠断面，上述平均水深定义为 $\\bar{h} = \\frac{A}{B}$（$A$ 为过水断面面积，$B$ 为水面宽度）；对于宽度为 $b$ 的矩形明渠，$\\bar{h} = h$，临界水深 $h_k = \\sqrt[3]{\\frac{\\alpha q^2}{g}}$，$Fr = \\frac{v}{\\sqrt{gh}}$。",
                "analysisFigures": [],
                "pitfalls": "注意不要把“明渠急流、缓流、临界流（按 $Fr$ 划分）”与“有压管层流、湍流（按 $Re$ 划分）”混为一谈！题目明确提示“**从水深、流速等方面说明各流态的特征**”，正是考查 $h$ 与 $h_k$、$v$ 与波速 $\\sqrt{gh}$（即 $Fr$）的对比。",
                "chapter": 8,
                "kps": ["断面比能与临界水深", "急流缓流与临界流判别", "弗劳德数"],
                "method": "临界水深与浅水微波波速三态对比法",
                "difficulty": 1,
                "rubric": [
                    {"label": "完整答出明渠水流分为缓流、临界流、急流三种流态", "pts": 1},
                    {"label": "从水深（h 与 hk 大小关系）准确说明三种流态特征", "pts": 2},
                    {"label": "从流速与微波波速 √(gh)（Fr 与 1 的关系及扰动波传播特性）准确说明三种流态特征", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2022-07",
                "year": 2022,
                "no": 7,
                "type": "short",
                "score": 5,
                "title": "欧拉法三维液体运动 x 方向当地加速度、迁移加速度与总加速度表达式",
                "stem": "试写出三维液体运动的当地加速度、迁移加速度和总加速度表达式（只需写出 $x$ 方向）。",
                "note": "",
                "figures": [],
                "shortAnswer": "当地加速度 a_tx = ∂ux/∂t；迁移加速度 a_sx = ux(∂ux/∂x) + uy(∂ux/∂y) + uz(∂ux/∂z)；总加速度 ax = dux/dt = ∂ux/∂t + ux(∂ux/∂x) + uy(∂ux/∂y) + uz(∂ux/∂z)。",
                "judgeAnswer": None,
                "answer": "设三维欧拉流场的速度分量为 $u_x(x,y,z,t)$、$u_y(x,y,z,t)$、$u_z(x,y,z,t)$，则流体质点在 $x$ 方向的各加速度表达式分别为：\n\n1. **$x$ 方向当地加速度（时变加速度）**：\n\n$$\na_{tx} = \\frac{\\partial u_x}{\\partial t}\n$$\n\n2. **$x$ 方向迁移加速度（位变加速度 / 对流加速度）**：\n\n$$\na_{sx} = u_x \\frac{\\partial u_x}{\\partial x} + u_y \\frac{\\partial u_x}{\\partial y} + u_z \\frac{\\partial u_x}{\\partial z}\n$$\n\n3. **$x$ 方向总加速度（随体导数 / 物质导数）**：\n\n$$\na_x = \\frac{\\mathrm{d}u_x}{\\mathrm{d}t} = \\frac{\\partial u_x}{\\partial t} + u_x \\frac{\\partial u_x}{\\partial x} + u_y \\frac{\\partial u_x}{\\partial y} + u_z \\frac{\\partial u_x}{\\partial z}\n$$",
                "analysis": "**物理意义速记**：\n- 当地加速度 $\\frac{\\partial u_x}{\\partial t}$ 反映流场的**非恒定性**（恒定流中当地加速度恒为零）；\n- 迁移加速度 $u_x\\frac{\\partial u_x}{\\partial x} + u_y\\frac{\\partial u_x}{\\partial y} + u_z\\frac{\\partial u_x}{\\partial z}$ 反映流场的**空间非均匀性**（均匀流中迁移加速度恒为零）。",
                "analysisFigures": [],
                "pitfalls": "迁移加速度三项中被求偏导的函数全部是 **$u_x$**（即 $u_x\\frac{\\partial u_x}{\\partial x} + u_y\\frac{\\partial u_x}{\\partial y} + u_z\\frac{\\partial u_x}{\\partial z}$），切勿张冠李戴误写成散度形式 $u_x\\frac{\\partial u_x}{\\partial x} + u_y\\frac{\\partial u_y}{\\partial y} + u_z\\frac{\\partial u_z}{\\partial z}$！",
                "chapter": 5,
                "kps": ["欧拉法质点加速度", "当地加速度与迁移加速度", "随体导数"],
                "method": "欧拉速度场复合函数全求导法",
                "difficulty": 1,
                "rubric": [
                    {"label": "正确写出 x 方向当地加速度 ∂ux/∂t", "pts": 1},
                    {"label": "正确写出 x 方向三维迁移加速度 ux(∂ux/∂x) + uy(∂ux/∂y) + uz(∂ux/∂z)", "pts": 2},
                    {"label": "正确写出 x 方向总加速度 dux/dt 完整求和表达式", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2022-08",
                "year": 2022,
                "no": 8,
                "type": "short",
                "score": 5,
                "title": "建立多孔介质连续渗流模型的三个基本原则",
                "stem": "建立渗流模型的三个基本原则是什么？",
                "note": "",
                "figures": [],
                "shortAnswer": "①流量相等原则：通过渗流模型任一断面的流量等于实际多孔介质该断面孔隙通过的真实渗流流量；②动水压力（测压管水头）相等原则：同一作用面上渗流模型的动水压强（压力）与实际渗流相等；③阻力与能量损失相等原则：任一土体段内渗流模型所受阻力和水头损失与实际渗流相等。",
                "judgeAnswer": None,
                "answer": "用假想充满整个多孔介质空间（包括土颗粒骨架与孔隙）的连续水流（渗流模型）代替仅在微小曲折孔隙中运动的真实水流时，必须遵循以下**三个基本等效原则**：\n\n1. **流量相等原则**：通过渗流模型任一过水断面的体积流量 $Q$，必须与通过该断面孔隙的实际渗流流量严格相等（由此得出渗流模型断面平均流速 $v = Q/A$ 小于孔隙真实平均流速 $u = Q/A_v$，即 $v = n^{\\prime} u$）；\n2. **动水压力（压强）相等原则**：对于同一确定的作用面（或空间点），由渗流模型得出的动水压强（测压管水头）及总动水压力，必须与真实渗流在该面上的动水压强及动水压力相等；\n3. **水力阻力（水头损失）相等原则**：在任一相同体积土体控制段内，渗流模型水流所受的固体骨架阻力（以及消耗的水头损失 $h_f$），必须与实际渗流所受的阻力和水头损失相等。",
                "analysis": "**工程意义**：正是依靠上述“流量等效、压力等效、阻力损失等效”三大原则，才能避开追踪复杂无规孔隙通道的微观困难，将连续介质流体力学的连续性方程、能量方程与达西定律推广应用于整个渗流区域（仅动量与动能因 $v < u$ 存在微小差异，而在极低速渗流中动能项 $v^2/(2g) \\approx 0$ 可忽略不计）。",
                "analysisFigures": [],
                "pitfalls": "切记渗流模型保证的是**流量、动水压力、阻力（水头损失）**三者相等，而**不是流速相等**（渗流流速 $v = Q/A$ 比实际孔隙流速 $u$ 小，切勿把“流速相等”误答进三原则）！",
                "chapter": 10,
                "kps": ["渗流模型三原则", "达西定律", "渗流流速与真实孔隙流速"],
                "method": "多孔介质连续化等效三原则归纳法",
                "difficulty": 1,
                "rubric": [
                    {"label": "准确答出原则一：通过任一断面的渗流模型流量与实际渗流流量相等", "pts": 2},
                    {"label": "准确答出原则二：同一作用面上渗流模型的动水压力（压强）与实际渗流相等", "pts": 2},
                    {"label": "准确答出原则三：渗流模型的阻力（水头损失）与实际渗流相等", "pts": 1}
                ]
            },
            {
                "id": "yzu-849-2022-09",
                "year": 2022,
                "no": 9,
                "type": "calc",
                "score": 15,
                "title": "斜置矩形平板闸门静水总压力与压力中心位置计算",
                "stem": "如图所示为一斜置矩形闸门，已知闸门形心距水面 $H = 8\\,\\mathrm{m}$，倾角 $\\alpha = 45^{\\circ}$，矩形闸门高 $h = 2\\,\\mathrm{m}$（如图），宽 $b = 2\\,\\mathrm{m}$。试求：矩形闸门上的静水总压力和压力中心位置。",
                "note": "",
                "figures": [
                    {"src": "figures/q09_orig.png", "caption": "题 9 图　斜置矩形平板闸门尺寸与淹没深度"}
                ],
                "shortAnswer": "静水总压力 P = 313.60 kN（若取 g=9.81 m/s² 则为 313.92 kN），垂直于闸门面指向右下方；压力中心位于闸门对称轴上、形心 C 沿门面斜向下 e = 0.0295 m（2.95 cm）处，距水面沿斜面距离 yD = 11.34 m（竖直水深 hD = 8.02 m）。",
                "judgeAnswer": None,
                "answer": "取 $g = 9.80\\,\\mathrm{m/s^2}$：\n1. **矩形闸门上的静水总压力**：$P = 313.60\\,\\mathrm{kN}$（若取 $g = 9.81\\,\\mathrm{m/s^2}$ 则为 $313.92\\,\\mathrm{kN}$），方向垂直于闸门受压面指向右下方；\n2. **压力中心 $D$ 的位置**：位于矩形闸门纵向对称轴上、形心 $C$ 沿斜面以下 $e = 0.0295\\,\\mathrm{m}$（即 $2.95\\,\\mathrm{cm}$）处，沿斜面距水面交点 $O$ 的距离为 $y_D \\approx 11.34\\,\\mathrm{m}$，对应自由水面以下的铅直水深为 $h_D \\approx 8.02\\,\\mathrm{m}$（精确值 $8 + \\frac{1}{48}\\,\\mathrm{m} \\approx 8.021\\,\\mathrm{m}$）。",
                "analysis": "**1. 计算矩形闸门受压面积与静水总压力 $P$**\n\n由题 9 图尺寸标示可知，矩形闸门沿斜面方向的长度（门高）为 $h = 2\\,\\mathrm{m}$，门宽为 $b = 2\\,\\mathrm{m}$，故闸门受压面积为：\n\n$$\nA = b h = 2 \\times 2 = 4.0\\,\\mathrm{m^2}\n$$\n\n题目已直接给出闸门形心 $C$ 距自由水面的铅直淹没深度 $h_c = H = 8\\,\\mathrm{m}$。由任意平面静水总压力公式（取 $g = 9.80\\,\\mathrm{m/s^2}$）：\n\n$$\nP = p_c A = \\rho g H A = 1000 \\times 9.80 \\times 8 \\times 4.0 = 313600\\,\\mathrm{N} = 313.60\\,\\mathrm{kN}\n$$\n\n（若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $P = 1000 \\times 9.81 \\times 32 = 313.92\\,\\mathrm{kN}$。）方向垂直于斜置闸门平面指向门体（右下方，见解图 9）。\n\n**2. 计算压力中心 $D$ 的位置**\n\n延长闸门所在倾斜平面与自由水面相交于轴线 $O$，建立沿斜面向下的坐标轴 $Oy$（倾角 $\\alpha = 45^{\\circ}$）：\n\n- 闸门形心 $C$ 沿斜面距 $O$ 点的坐标 $y_C$：\n\n$$\ny_C = \\frac{H}{\\sin\\alpha} = \\frac{8}{\\sin 45^{\\circ}} = 8\\sqrt{2} \\approx 11.3137\\,\\mathrm{m}\n$$\n\n- 矩形闸门绕通过形心 $C$ 且平行于水面的水平轴的惯性矩 $I_C$：\n\n$$\nI_C = \\frac{b h^3}{12} = \\frac{2 \\times 2^3}{12} = \\frac{4}{3} \\approx 1.3333\\,\\mathrm{m^4}\n$$\n\n- 压力中心 $D$ 沿斜面向下偏离形心 $C$ 的偏心距 $e$ 及斜面坐标 $y_D$：\n\n$$\ne = y_D - y_C = \\frac{I_C}{y_C A} = \\frac{4/3}{8\\sqrt{2} \\times 4.0} = \\frac{1}{24\\sqrt{2}} = \\frac{\\sqrt{2}}{48} \\approx 0.02946\\,\\mathrm{m} \\approx 0.0295\\,\\mathrm{m}\n$$\n\n$$\ny_D = y_C + e = 11.3137 + 0.0295 \\approx 11.343\\,\\mathrm{m} \\approx 11.34\\,\\mathrm{m}\n$$\n\n- 折算为自由水面以下的铅直深度 $h_D$：\n\n$$\nh_D = y_D \\sin 45^{\\circ} = H + e \\sin 45^{\\circ} = 8 + \\frac{\\sqrt{2}}{48}\\times\\frac{\\sqrt{2}}{2} = 8 + \\frac{1}{48} \\approx 8.0208\\,\\mathrm{m} \\approx 8.02\\,\\mathrm{m}\n$$",
                "analysisFigures": [
                    {"src": "figures/q09_sol.png", "caption": "解图 9　斜置矩形闸门静水压强棱柱体、形心 C 与压力中心 D 位置图"}
                ],
                "pitfalls": "1. 静水总压力 $P$ 是力，单位务必写为 **$313.60\\,\\mathrm{kN}$**（切勿将力与压强混淆误写为 $\\mathrm{kPa}$）！\n2. 认准题干及题 9 图中 $H = 8\\,\\mathrm{m}$ 已经是**闸门形心 $C$ 距水面的深度**（无需再加 $h\\sin\\alpha / 2$），且图中尺寸 $h = 2\\,\\mathrm{m}$ 平行于闸门标注，即为斜面门长！",
                "chapter": 2,
                "kps": ["平面与曲面静水总压力", "压力中心计算", "截面惯性矩"],
                "method": "平面静水总压力解析法与平行移轴求压心法",
                "difficulty": 2,
                "rubric": [
                    {"label": "正确求得受压面积 A = 4 m² 及静水总压力 P = ρgHA = 313.60 kN（或 313.92 kN，单位 kN 正确）", "pts": 6},
                    {"label": "求出形心斜距 yC = 8√2 ≈ 11.314 m 及形心轴惯性矩 IC = bh³/12 = 4/3 m⁴", "pts": 5},
                    {"label": "由 yD = yC + IC/(yCA) 求出压力中心位置 yD ≈ 11.34 m（或水深 hD ≈ 8.02 m）", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2022-10",
                "year": 2022,
                "no": 10,
                "type": "calc",
                "score": 15,
                "title": "倾斜渐粗管水流方向判别、断面能量损失与流量计算",
                "stem": "有一倾斜放置的渐粗管如图所示，A-A 与 B-B 两过水断面形心点的高差为 $1.0\\,\\mathrm{m}$。断面 A-A 管径 $d_A = 200\\,\\mathrm{mm}$，形心点压强 $p_A = 68.5\\,\\mathrm{kPa}$。断面 B-B 管径 $d_B = 300\\,\\mathrm{mm}$，形心点压强 $p_B = 58\\,\\mathrm{kPa}$，断面平均流速 $V_B = 1.5\\,\\mathrm{m/s}$，试求：\n\n（1）管中水流的方向；\n\n（2）两断面之间的能量损失；\n\n（3）通过管道的流量。",
                "note": "注：原卷文字明确给出两断面形心高差为 1.0 m（原卷配图右侧误标为 0.1 m），本解严格以题干文字 1.0 m 为准，并在解析末附按 0.1 m 计算的对照结果。",
                "figures": [
                    {"src": "figures/q10_orig.png", "caption": "题 10 图　倾斜放置的渐粗管段"}
                ],
                "shortAnswer": "（1）水流方向由 A-A 流向 B-B；（2）两断面间能量损失 hw = 0.54 m（若按图中 0.1 m 计则为 1.44 m）；（3）通过管道的流量 Q ≈ 0.106 m³/s（106.0 L/s）。",
                "judgeAnswer": None,
                "answer": "取 $g = 9.80\\,\\mathrm{m/s^2}$：\n\n（1）管中水流方向：**由断面 A-A 流向断面 B-B**；\n\n（2）两断面之间的单位重量能量损失（水头损失）：$h_{w,A\\text{-}B} \\approx 0.54\\,\\mathrm{m}$（按题干高差 $1.0\\,\\mathrm{m}$ 计；若按原图误印高差 $0.1\\,\\mathrm{m}$ 计则为 $1.44\\,\\mathrm{m}$）；\n\n（3）通过管道的流量：$Q \\approx 0.106\\,\\mathrm{m^3/s}$（即 $106.0\\,\\mathrm{L/s}$）。",
                "analysis": "**1. 先由连续性方程计算管道流量 $Q$（第 3 问）及断面 A-A 平均流速 $V_A$**\n\n已知断面 B-B 管径 $d_B = 0.30\\,\\mathrm{m}$、平均流速 $V_B = 1.5\\,\\mathrm{m/s}$，通过管道的体积流量为：\n\n$$\nQ = A_B V_B = \\frac{\\pi}{4}d_B^2 V_B = \\frac{\\pi}{4} \\times 0.30^2 \\times 1.5 = 0.03375\\pi \\approx 0.10603\\,\\mathrm{m^3/s} \\approx 0.106\\,\\mathrm{m^3/s}\n$$\n\n断面 A-A 管径 $d_A = 0.20\\,\\mathrm{m}$，由不可压缩连续性方程 $A_A V_A = A_B V_B$ 求得流速 $V_A$：\n\n$$\nV_A = V_B \\left(\\frac{d_B}{d_A}\\right)^2 = 1.5 \\times \\left(\\frac{0.30}{0.20}\\right)^2 = 1.5 \\times 2.25 = 3.375\\,\\mathrm{m/s}\n$$\n\n**2. 分别计算 A-A 与 B-B 两断面的总水头（单位重量总机械能），判别水流方向（第 1 问）**\n\n以较低的断面 A-A 形心所在水平面为基准面，则 $z_A = 0$，依题干文字有 $z_B = 1.0\\,\\mathrm{m}$。取动能修正系数 $\\alpha_A = \\alpha_B = 1.0$，$g = 9.80\\,\\mathrm{m/s^2}$，计算两断面总水头 $E_A$ 与 $E_B$：\n\n$$\nE_A = z_A + \\frac{p_A}{\\rho g} + \\frac{V_A^2}{2g} = 0 + \\frac{68.5 \\times 10^3}{1000 \\times 9.80} + \\frac{3.375^2}{2 \\times 9.80} = 6.9898 + 0.5812 = 7.5710\\,\\mathrm{m}\n$$\n\n$$\nE_B = z_B + \\frac{p_B}{\\rho g} + \\frac{V_B^2}{2g} = 1.0 + \\frac{58 \\times 10^3}{1000 \\times 9.80} + \\frac{1.5^2}{2 \\times 9.80} = 1.0 + 5.9184 + 0.1148 = 7.0332\\,\\mathrm{m}\n$$\n\n由于实际黏性液体在无水泵外功输入时**只能由总机械能（总水头）高处流向总水头低处**，而 $E_A = 7.5710\\,\\mathrm{m} > E_B = 7.0332\\,\\mathrm{m}$，故管中水流方向**由断面 A-A 流向断面 B-B**。\n\n**3. 计算两断面之间的能量损失 $h_{w,A\\text{-}B}$（第 2 问）**\n\n由 A-A 至 B-B 恒定总流能量方程 $E_A = E_B + h_{w,A\\text{-}B}$，得单位重量液体的能量损失（水头损失）：\n\n$$\nh_{w,A\\text{-}B} = E_A - E_B = 7.5710 - 7.0332 = 0.5378\\,\\mathrm{m} \\approx 0.54\\,\\mathrm{m}\n$$\n\n（注：① 若取 $g = 9.81\\,\\mathrm{m/s^2}$，算得 $E_A = 7.5632\\,\\mathrm{m}$，$E_B = 7.0270\\,\\mathrm{m}$，$h_{w,A\\text{-}B} = 0.5362\\,\\mathrm{m} \\approx 0.54\\,\\mathrm{m}$；② 原卷配图右侧尺寸印为 $0.1\\,\\mathrm{m}$，若按 $z_B - z_A = 0.1\\,\\mathrm{m}$ 计算，则 $E_B = 6.1332\\,\\mathrm{m} < E_A$，流向依然为由 A-A 流向 B-B，水头损失为 $h_{w,A\\text{-}B} = 1.44\\,\\mathrm{m}$。）",
                "analysisFigures": [],
                "pitfalls": "1. **严禁仅凭压强大小（$p_A > p_B$）或测压管水头大小判别变径管流向！** 在渐扩管中流速水头转化为压能，完全可能出现顺流增压现象，唯一绝对可靠的判据是比较包含动能项的**总水头 $E = z + \\frac{p}{\\rho g} + \\frac{\\alpha V^2}{2g}$**！\n2. 注意各物理量单位：水头损失 $h_w$ 的单位是水柱米 **$\\\\mathrm{m}$**，流量 $Q$ 的单位是 **$\\\\mathrm{m^3/s}$**（切勿把两者笔误写成流速单位 $\\mathrm{m/s}$）。",
                "chapter": 3,
                "kps": ["恒定总流能量方程", "变径管水流方向判别", "恒定总流连续性方程"],
                "method": "总水头大小判别流向与恒定总流能量方程",
                "difficulty": 2,
                "rubric": [
                    {"label": "由连续性方程求出管道流量 Q ≈ 0.106 m³/s 及 A-A 断面流速 VA = 3.375 m/s", "pts": 5},
                    {"label": "正确计算两断面总水头 EA ≈ 7.57 m、EB ≈ 7.03 m，由 EA > EB 判明流向为 A-A 流向 B-B", "pts": 6},
                    {"label": "由水头差 EA - EB 求出两断面间能量损失 hw ≈ 0.54 m（单位 m 正确）", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2022-11",
                "year": 2022,
                "no": 11,
                "type": "calc",
                "score": 15,
                "title": "水平对称分岔管路水流对分管的作用力计算",
                "stem": "如图所示水平布置的分岔管路，干管直径 $d_1 = 600\\,\\mathrm{mm}$，支管直径 $d_2 = d_3 = 400\\,\\mathrm{mm}$，分岔角 $\\alpha = 30^{\\circ}$。已知分岔前断面的压力表读值 $p_M = 70\\,\\mathrm{kN/m^2}$，干管流量 $q_V = 0.6\\,\\mathrm{m^3/s}$，不计水头损失，试求水流对分管的作用力。",
                "note": "",
                "figures": [
                    {"src": "figures/q11_orig.png", "caption": "题 11 图　水平对称分岔管路俯视图"}
                ],
                "shortAnswer": "水流对分管的作用力大小 F = 4.72 kN，方向沿 +x 轴水平向右（y 方向分力 Fy = 0）。",
                "judgeAnswer": None,
                "answer": "水流对水平分岔管的作用力大小为 **$4.72\\,\\mathrm{kN}$**，方向沿 $+x$ 轴**水平向右**（横向分力 $F_y = 0$）。",
                "analysis": "**1. 由对称性与连续性方程计算干管、支管断面流速**\n\n分岔管路水平对称布置（$d_2 = d_3 = 0.40\\,\\mathrm{m}$，分岔角均为 $\\alpha = 30^{\\circ}$，且不计水头损失），故两支管流量相等：$q_{V2} = q_{V3} = \\frac{1}{2}q_V = 0.30\\,\\mathrm{m^3/s}$。\n\n- 干管（$d_1 = 0.60\\,\\mathrm{m}$）断面积与流速：\n\n$$\nA_1 = \\frac{\\pi}{4}d_1^2 = \\frac{\\pi}{4} \\times 0.60^2 = 0.09\\pi \\approx 0.28274\\,\\mathrm{m^2}, \\qquad v_1 = \\frac{q_V}{A_1} = \\frac{0.60}{0.09\\pi} \\approx 2.1221\\,\\mathrm{m/s}\n$$\n\n- 各支管（$d_2 = d_3 = 0.40\\,\\mathrm{m}$）断面积与流速：\n\n$$\nA_2 = A_3 = \\frac{\\pi}{4}d_2^2 = \\frac{\\pi}{4} \\times 0.40^2 = 0.04\\pi \\approx 0.12566\\,\\mathrm{m^2}, \\qquad v_2 = v_3 = \\frac{0.30}{0.04\\pi} \\approx 2.3873\\,\\mathrm{m/s}\n$$\n\n**2. 由水平无损能量方程求支管断面相对压强 $p_2 = p_3$**\n\n因管路水平布置（$z_1 = z_2 = z_3$）且不计水头损失（$h_w = 0$），取 $\\alpha = 1.0$，对分岔前断面 $1\\text{—}1$（$p_1 = p_M = 70\\,\\mathrm{kPa}$）与支管断面 $2\\text{—}2$ 列伯努利方程：\n\n$$\n\\frac{p_1}{\\rho g} + \\frac{v_1^2}{2g} = \\frac{p_2}{\\rho g} + \\frac{v_2^2}{2g} \\implies p_2 = p_1 + \\frac{1}{2}\\rho (v_1^2 - v_2^2)\n$$\n\n代入数值（注意 $\\rho$ 消去了 $g$ 的取值差异）：\n\n$$\np_2 = p_3 = 70000 + \\frac{1}{2} \\times 1000 \\times (2.1221^2 - 2.3873^2) = 70000 - 598.1 = 69401.9\\,\\mathrm{Pa} \\approx 69.40\\,\\mathrm{kPa}\n$$\n\n**3. 计算各控制断面动水总压力并列动量方程求管壁受力**\n\n截取断面 $1\\text{—}1$、$2\\text{—}2$、$3\\text{—}3$ 之间的分岔段水体为控制体（受力方向见解图 11）。各断面上外部水体对控制体的法向推力始终**垂直于各自过水断面指向控制体内部**：\n\n$$\nP_1 = p_1 A_1 = 70000 \\times 0.09\\pi \\approx 19792.0\\,\\mathrm{N} = 19.792\\,\\mathrm{kN}\\;(\\text{沿 }+x\\text{ 方向})\n$$\n\n$$\nP_2 = P_3 = p_2 A_2 = 69401.9 \\times 0.04\\pi \\approx 8721.3\\,\\mathrm{N} = 8.721\\,\\mathrm{kN}\\;(\\text{沿各支管轴线逆流斜向内！})\n$$\n\n设分岔管壁对水体的总反作用力分量为 $(R_x, R_y)$（假定沿坐标轴正向），取动量修正系数 $\\beta = 1.0$：\n\n- **$y$ 轴方向动量方程**：由上下严格对称，$-P_2\\sin 30^{\\circ} + P_3\\sin 30^{\\circ} + R_y = \\rho q_{V2} v_2\\sin 30^{\\circ} - \\rho q_{V3} v_3\\sin 30^{\\circ} = 0 \\implies R_y = 0$。\n- **$x$ 轴方向动量方程**（注意 $P_2$、$P_3$ 在 $x$ 轴上的投影均为 $-P_2\\cos 30^{\\circ}$！）：\n\n$$\nP_1 - 2 P_2 \\cos 30^{\\circ} + R_x = \\rho q_{V2} v_2 \\cos 30^{\\circ} + \\rho q_{V3} v_3 \\cos 30^{\\circ} - \\rho q_V v_1 = \\rho q_V (v_2 \\cos 30^{\\circ} - v_1)\n$$\n\n分别计算左端静压合力项与右端动量通量变化项：\n\n$$\nP_1 - 2 P_2 \\cos 30^{\\circ} = 19.7920 - 2 \\times 8.7213 \\times \\frac{\\sqrt{3}}{2} = 19.7920 - 15.1057 = 4.6863\\,\\mathrm{kN}\n$$\n\n$$\n\\rho q_V (v_2 \\cos 30^{\\circ} - v_1) = 1.0 \\times 0.60 \\times (2.3873 \\times 0.86603 - 2.1221) = 0.60 \\times (2.0675 - 2.1221) = -0.0328\\,\\mathrm{kN}\n$$\n\n解得管壁对水体的水平反作用力：\n\n$$\nR_x = -0.0328 - 4.6863 = -4.7191\\,\\mathrm{kN} \\approx -4.72\\,\\mathrm{kN}\n$$\n\n负号表明管壁对水体的作用力沿 $-x$ 轴方向（水平向左）。由牛顿第三定律，**水流对分管的作用力**为：\n\n$$\nF_x = -R_x = 4.72\\,\\mathrm{kN}\\;(\\text{方向沿 }+x\\text{ 轴水平向右}), \\qquad F_y = 0\n$$",
                "analysisFigures": [
                    {"src": "figures/q11_sol.png", "caption": "解图 11　水平对称分岔管控制体断面压力投影与动量平衡图"}
                ],
                "pitfalls": "**本题头号致命易错点**：支管出口过水断面 $2\\text{—}2$、$3\\text{—}3$ 与干管轴线并不平行，其法向动水总压力 $P_2$、$P_3$ 沿各支管轴线斜向内（与 $-x$ 轴夹角为 $\\alpha = 30^{\\circ}$），向 $x$ 轴投影时**必须乘以 $\\cos 30^{\\circ}$**（即 $-2 P_2 \\cos 30^{\\circ} = -15.11\\,\\mathrm{kN}$）！若漏乘 $\\cos 30^{\\circ}$ 误写为 $P_1 - 2P_2$，将导致结果严重偏小近一半（误算为 $2.38\\,\\mathrm{kN}$）。",
                "chapter": 3,
                "kps": ["闸门与弯管动水总压力", "恒定总流动量方程", "分叉管动量分析"],
                "method": "能量方程求压强+控制体动量方程求镇墩力",
                "difficulty": 3,
                "rubric": [
                    {"label": "由连续性及对称性求出干管流速 v1 ≈ 2.12 m/s 与两支管流速 v2 = v3 ≈ 2.39 m/s", "pts": 4},
                    {"label": "由水平伯努利方程求出支管压强 p2 ≈ 69.40 kPa 及各断面总压力 P1 ≈ 19.79 kN、P2 ≈ 8.72 kN", "pts": 5},
                    {"label": "正确计入支管压力投影 -2P2·cos30° 列 x 向动量方程，求得水流对分管作用力 4.72 kN（水平向右）", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2022-12",
                "year": 2022,
                "no": 12,
                "type": "calc",
                "score": 15,
                "title": "矩形断面混凝土渡槽明渠均匀流出口槽底高程计算",
                "stem": "有一矩形断面混凝土渡槽（$n = 0.014$），底宽 $b = 1.5\\,\\mathrm{m}$，槽长 $l = 116.5\\,\\mathrm{m}$。进口处槽底高程 $z_1 = 52.06\\,\\mathrm{m}$，当通过设计流量 $Q = 7.56\\,\\mathrm{m^3/s}$ 时，槽中均匀流水深 $h_0 = 1.7\\,\\mathrm{m}$，试求渡槽出口的底部高程 $z_2$。",
                "note": "",
                "figures": [],
                "shortAnswer": "51.58 m（槽底坡度 i ≈ 4.12×10⁻³，槽底高程降落 Δz = 0.48 m）",
                "judgeAnswer": None,
                "answer": "渡槽出口的底部高程 $z_2 = 51.58\\,\\mathrm{m}$。",
                "analysis": "**1. 计算矩形渡槽过水断面的水力要素**\n\n已知矩形断面底宽 $b = 1.5\\,\\mathrm{m}$，均匀流正常水深 $h_0 = 1.7\\,\\mathrm{m}$：\n\n- 过水断面面积 $A$：\n\n$$\nA = b h_0 = 1.5 \\times 1.7 = 2.55\\,\\mathrm{m^2}\n$$\n\n- 湿周 $\\chi$ 与水力半径 $R$：\n\n$$\n\\chi = b + 2 h_0 = 1.5 + 2 \\times 1.7 = 4.90\\,\\mathrm{m}, \\qquad R = \\frac{A}{\\chi} = \\frac{2.55}{4.90} \\approx 0.52041\\,\\mathrm{m}\n$$\n\n**2. 由明渠均匀流谢才—曼宁公式反求渡槽底坡 $i$**\n\n断面平均流速与谢才系数 $C$（采用曼宁公式，$n = 0.014$）分别为：\n\n$$\nv = \\frac{Q}{A} = \\frac{7.56}{2.55} \\approx 2.9647\\,\\mathrm{m/s}\n$$\n\n$$\nC = \\frac{1}{n} R^{1/6} = \\frac{1}{0.014} \\times 0.52041^{1/6} \\approx 71.4286 \\times 0.89685 \\approx 64.061\\,\\mathrm{m^{1/2}/s}\n$$\n\n由 $Q = A C \\sqrt{R i}$ 解得渡槽底坡 $i$：\n\n$$\ni = \\frac{Q^2}{A^2 C^2 R} = \\frac{n^2 v^2}{R^{4/3}} = \\frac{0.014^2 \\times 2.9647^2}{0.52041^{4/3}} = \\frac{1.7227 \\times 10^{-3}}{0.41858} \\approx 4.1156 \\times 10^{-3}\n$$\n\n**3. 计算槽底降落量与渡槽出口底部高程 $z_2$**\n\n在槽长 $l = 116.5\\,\\mathrm{m}$ 范围内，槽底高程降落量为：\n\n$$\n\\Delta z = i l = 4.1156 \\times 10^{-3} \\times 116.5 \\approx 0.4795\\,\\mathrm{m} \\approx 0.48\\,\\mathrm{m}\n$$\n\n故渡槽出口处的槽底高程为：\n\n$$\nz_2 = z_1 - \\Delta z = 52.06 - 0.48 = 51.58\\,\\mathrm{m}\n$$",
                "analysisFigures": [],
                "pitfalls": "1. 明渠均匀流必须布置为**顺坡**（$i > 0$，出口底高程低于进口底高程），因此 $z_2 = z_1 - i l = 51.58\\,\\mathrm{m}$，切勿加反写成 $52.06 + 0.48$！\n2. 矩形明渠湿周为底宽加两侧水深 $\\chi = b + 2h_0 = 4.90\\,\\mathrm{m}$，切勿多乘一次 $b$ 写成 $2(b + h_0)$。",
                "chapter": 7,
                "kps": ["曼宁公式", "明渠均匀流水力计算"],
                "method": "明渠均匀流曼宁公式求底坡与高程法",
                "difficulty": 2,
                "rubric": [
                    {"label": "求出矩形过水断面面积 A = 2.55 m²、湿周 χ = 4.90 m 及水力半径 R ≈ 0.520 m", "pts": 5},
                    {"label": "由谢才—曼宁公式 Q = (1/n)AR^(2/3)i^(1/2) 求出槽底坡度 i ≈ 4.12×10⁻³", "pts": 6},
                    {"label": "计算槽底降落 Δz = il ≈ 0.48 m，由 z2 = z1 - Δz 得出出口槽底高程 51.58 m", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2022-13",
                "year": 2022,
                "no": 13,
                "type": "calc",
                "score": 15,
                "title": "不可压缩平面势流证明与两点间单宽流量计算",
                "stem": "已知流速场 $u_x = 3(x^2 - y^2)$，$u_y = -6xy$。\n\n（1）证明此流动为不可压缩平面势流；\n\n（2）求通过 $(0, 0)$ 和 $(1, 1)$ 之间的流量。",
                "note": "",
                "figures": [],
                "shortAnswer": "（1）因 ∂ux/∂x + ∂uy/∂y = 6x - 6x = 0（满足不可压连续性）且 ωz = (∂uy/∂x - ∂ux/∂y)/2 = (-6y + 6y)/2 = 0（满足无旋性），故为不可压缩平面势流；（2）流函数 ψ = 3x²y - y³ + C，通过 (0,0) 与 (1,1) 之间的单宽流量 q = |ψ(1,1) - ψ(0,0)| = 2 m³/(s·m)（或无量纲数值 2）。",
                "judgeAnswer": None,
                "answer": "**（1）证明**：验证不可压缩连续性微分方程与无旋条件：\n- $\\frac{\\partial u_x}{\\partial x} + \\frac{\\partial u_y}{\\partial y} = 6x + (-6x) = 0$，满足不可压缩平面连续性方程；\n- $\\omega_z = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} - \\frac{\\partial u_x}{\\partial y}\\right) = \\frac{1}{2}\\left[-6y - (-6y)\\right] = 0$，满足无旋流动条件（存在速度势函数），故此流动为**不可压缩平面势流**。\n\n**（2）流量计算**：通过点 $(0,0)$ 和 $(1,1)$ 之间的单位宽度体积流量（单宽流量）为 **$q = 2\\,\\mathrm{m^3/(s\\cdot m)}$**（或数值 $2$）。",
                "analysis": "**（1）严格证明“不可压缩平面势流”需同时验证两个偏微分条件**\n\n已知平面二维速度场 $u_x = 3x^2 - 3y^2$，$u_y = -6xy$（$u_z = 0$）：\n\n1. **验证不可压缩性（连续性条件）**：\n\n$$\n\\frac{\\partial u_x}{\\partial x} = 6x, \\qquad \\frac{\\partial u_y}{\\partial y} = -6x \\implies \\frac{\\partial u_x}{\\partial x} + \\frac{\\partial u_y}{\\partial y} = 6x - 6x \\equiv 0\n$$\n\n表明流体微团体积膨胀率为零，流动满足不可压缩连续性微分方程。\n\n2. **验证有势性 / 无旋性（存在势函数条件）**：\n\n$$\n\\frac{\\partial u_y}{\\partial x} = -6y, \\qquad \\frac{\\partial u_x}{\\partial y} = -6y \\implies \\omega_z = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} - \\frac{\\partial u_x}{\\partial y}\\right) = \\frac{1}{2}(-6y + 6y) \\equiv 0\n$$\n\n表明全平面内旋转角速度恒为零（速度势函数为 $\\varphi = x^3 - 3xy^2 + C_1$）。综上，此流动是**不可压缩平面势流**。\n\n**（2）求通过点 $O(0,0)$ 和点 $A(1,1)$ 之间的单宽流量 $q$**\n\n- **方法一（积分求流函数 $\\psi$ 利用流函数差值物理意义）**：\n  由 $\\mathrm{d}\\psi = u_x\\,\\mathrm{d}y - u_y\\,\\mathrm{d}x$：\n\n$$\n\\mathrm{d}\\psi = 3(x^2 - y^2)\\,\\mathrm{d}y - (-6xy)\\,\\mathrm{d}x = 6xy\\,\\mathrm{d}x + (3x^2 - 3y^2)\\,\\mathrm{d}y = \\mathrm{d}(3x^2 y - y^3)\n$$\n\n  积分得流函数：\n\n$$\n\\psi(x, y) = 3x^2 y - y^3 + C\n$$\n\n  两流线间的流函数差绝对值即等于两点连线通过的单宽流量 $q$：\n\n$$\nq = |\\psi(1, 1) - \\psi(0, 0)| = |(3 \\times 1^2 \\times 1 - 1^3 + C) - (0 + C)| = |3 - 1| = 2\\,\\mathrm{m^3/(s\\cdot m)}\n$$\n\n- **方法二（直接沿直线段 $y = x,\\; x \\in [0, 1]$ 曲线积分校核）**：\n\n$$\nq = \\left|\\int_{(0,0)}^{(1,1)} (u_x\\,\\mathrm{d}y - u_y\\,\\mathrm{d}x)\\right| = \\left|\\int_0^1 \\left[3(x^2 - x^2) + 6x^2\\right]\\mathrm{d}x\\right| = \\int_0^1 6x^2\\,\\mathrm{d}x = \\left[2x^3\\right]_0^1 = 2\\,\\mathrm{m^3/(s\\cdot m)}\n$$",
                "analysisFigures": [],
                "pitfalls": "第（1）问证明“**不可压缩平面势流**”包含两个并列定语——“不可压缩”和“势流（无旋）”！极易只验证连续性方程 $\\frac{\\partial u_x}{\\partial x} + \\frac{\\partial u_y}{\\partial y} = 0$ 而**漏掉无旋性验证 $\\frac{\\partial u_y}{\\partial x} - \\frac{\\partial u_x}{\\partial y} = 0$**（不可压缩有旋流也满足连续性方程，但绝不是势流！）。",
                "chapter": 5,
                "kps": ["流函数与势函数", "不可压缩连续性微分方程", "有旋流与无旋流判别"],
                "method": "连续性与无旋性判据及流函数求单宽流量法",
                "difficulty": 3,
                "rubric": [
                    {"label": "验证 ∂ux/∂x + ∂uy/∂y = 6x - 6x = 0，证明流动满足不可压缩连续性条件", "pts": 4},
                    {"label": "验证 ωz = (∂uy/∂x - ∂ux/∂y)/2 = 0，证明流动无旋（存在势函数），从而完整证得不可压平面势流", "pts": 4},
                    {"label": "全微分积分求出流函数 ψ = 3x²y - y³ + C（或写出正确曲线积分式）", "pts": 4},
                    {"label": "由 |ψ(1,1) - ψ(0,0)| 算得通过 (0,0) 与 (1,1) 间的单宽流量 q = 2", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2022-14",
                "year": 2022,
                "no": 14,
                "type": "calc",
                "score": 15,
                "title": "矩形渠道溢流坝过堰单宽流量计算与下游底流消能设施判别",
                "stem": "如图所示，在矩形渠道上修建的溢流坝，溢流宽度等于渠底宽度，已知：上、下游渠底高程均为 $15.00\\,\\mathrm{m}$，坝顶高程为 $21.00\\,\\mathrm{m}$，设计洪水位为 $22.80\\,\\mathrm{m}$，当宣泄设计洪水时，流量系数 $m = 0.48$，流速系数 $\\varphi = 0.95$，下游水位为 $17.80\\,\\mathrm{m}$。试求：\n\n（1）按自由出流计算过堰单宽（$b = 1\\,\\mathrm{m}$）流量；\n\n（2）计算判别溢流堰下游是否需要修建消能设施。",
                "note": "",
                "figures": [
                    {"src": "figures/q14_orig.png", "caption": "题 14 图　矩形渠道溢流坝上下游水位与高程剖面图"}
                ],
                "shortAnswer": "（1）计入行近流速水头迭代得单宽流量 q ≈ 5.23 m³/(s·m)（若忽略行近流速水头近似为 5.13 m³/(s·m)）；（2）坝趾收缩水深 hc ≈ 0.458 m，跃后共轭水深 hc'' ≈ 3.27 m > 下游水深 ht = 2.80 m，发生远驱式水跃，故必须修建消能设施。",
                "judgeAnswer": None,
                "answer": "取 $g = 9.80\\,\\mathrm{m/s^2}$：\n\n**（1）过堰单宽流量**：计入行近流速水头迭代得 $q \\approx 5.23\\,\\mathrm{m^3/(s\\cdot m)}$（若因高堰 $P_1/H > 3$ 忽略行近流速水头，则近似值 $q \\approx 5.13\\,\\mathrm{m^3/(s\\cdot m)}$）；\n\n**（2）消能设施判别**：坝下收缩断面水深 $h_c \\approx 0.458\\,\\mathrm{m}$，对应水跃跃后共轭水深 $h_c^{\\prime\\prime} \\approx 3.27\\,\\mathrm{m}$；因下游实际尾水深 $h_t = 2.80\\,\\mathrm{m} < h_c^{\\prime\\prime} = 3.27\\,\\mathrm{m}$，坝下将发生**远驱式水跃**，高速急流直接冲刷下游渠床，故**需要修建消能设施**（如修建消力池或消力坎）。",
                "analysis": "**（1）按自由出流计算过堰单宽流量 $q$**\n\n由题 14 图高程关系得：\n- 上、下游堰高：$P_1 = P_2 = 21.00 - 15.00 = 6.00\\,\\mathrm{m}$；\n- 堰顶水头：$H = 22.80 - 21.00 = 1.80\\,\\mathrm{m}$；\n- 下游尾水深：$h_t = 17.80 - 15.00 = 2.80\\,\\mathrm{m}$（因下游水位 $17.80\\,\\mathrm{m} <$ 坝顶高程 $21.00\\,\\mathrm{m}$，确为自由出流，淹没系数 $\\sigma_s = 1.0$）；\n- 溢流宽度等于渠底宽度，无侧向收缩，侧收缩系数 $\\varepsilon = 1.0$。\n\n过堰单宽流量基本公式（$b = 1\\,\\mathrm{m}$）为 $q = \\sigma_s \\varepsilon m \\sqrt{2g}\\,H_0^{3/2} = m\\sqrt{2g}\\,H_0^{3/2}$，其中堰前总水头 $H_0 = H + \\frac{\\alpha_0 v_0^2}{2g}$（取 $\\alpha_0 = 1.0$，$g = 9.80\\,\\mathrm{m/s^2}$），采用逐次逼近迭代求解：\n\n1. 初设 $H_0^{(0)} = H = 1.80\\,\\mathrm{m}$：\n\n$$\nq^{(1)} = 0.48 \\times \\sqrt{2 \\times 9.80} \\times 1.80^{3/2} = 0.48 \\times 4.4272 \\times 2.4150 \\approx 5.132\\,\\mathrm{m^3/(s\\cdot m)}\n$$\n\n2. 求行近流速 $v_0^{(1)}$ 与修正总水头 $H_0^{(1)}$：\n\n$$\nv_0^{(1)} = \\frac{q^{(1)}}{P_1 + H} = \\frac{5.132}{6.00 + 1.80} \\approx 0.6579\\,\\mathrm{m/s} \\implies H_0^{(1)} = 1.80 + \\frac{0.6579^2}{2 \\times 9.80} \\approx 1.8221\\,\\mathrm{m}\n$$\n\n3. 第二次迭代：\n\n$$\nq^{(2)} = 0.48 \\times \\sqrt{2 \\times 9.80} \\times 1.8221^{3/2} \\approx 5.227\\,\\mathrm{m^3/(s\\cdot m)}, \\qquad v_0^{(2)} = \\frac{5.227}{7.80} \\approx 0.6701\\,\\mathrm{m/s}\n$$\n\n$$\nH_0^{(2)} = 1.80 + \\frac{0.6701^2}{19.60} \\approx 1.8229\\,\\mathrm{m} \\implies q = 0.48 \\times 4.4272 \\times 1.8229^{3/2} \\approx 5.23\\,\\mathrm{m^3/(s\\cdot m)}\n$$\n\n迭代已收敛，故过堰单宽流量 $q = 5.23\\,\\mathrm{m^3/(s\\cdot m)}$（若取 $g = 9.81\\,\\mathrm{m/s^2}$ 同样为 $5.23\\,\\mathrm{m^3/(s\\cdot m)}$）。\n\n**（2）计算坝下收缩水深与跃后共轭水深，判别是否需设消能设施**\n\n以坝下水平渠底（高程 $15.00\\,\\mathrm{m}$）为基准面，上游相对下游渠底的总水头为：\n\n$$\nT_0 = P_2 + H_0 = 6.00 + 1.8229 = 7.8229\\,\\mathrm{m}\n$$\n\n对上游断面与坝趾收缩断面 $c\\text{—}c$ 列能量方程（引入溢流面流速系数 $\\varphi = 0.95$）：\n\n$$\nT_0 = h_c + \\frac{v_c^2}{2 g \\varphi^2} = h_c + \\frac{q^2}{2 g \\varphi^2 h_c^2}\n$$\n\n代入 $T_0 = 7.8229\\,\\mathrm{m}$，$q = 5.23\\,\\mathrm{m^3/(s\\cdot m)}$，$\\varphi = 0.95$：\n\n$$\n7.8229 = h_c + \\frac{5.23^2}{2 \\times 9.80 \\times 0.95^2 \\times h_c^2} = h_c + \\frac{1.5453}{h_c^2}\n$$\n\n迭代求解急流正根：初取 $h_c^{(0)} = \\frac{q}{\\varphi\\sqrt{2g T_0}} = 0.445\\,\\mathrm{m}$，代入 $h_c = \\sqrt{\\frac{1.5453}{7.8229 - h_c}}$ 两次即收敛于：\n\n$$\nh_c \\approx 0.458\\,\\mathrm{m}, \\qquad v_c = \\frac{q}{h_c} = \\frac{5.23}{0.458} \\approx 11.42\\,\\mathrm{m/s}\n$$\n\n计算收缩断面弗劳德数 $Fr_c$ 与矩形水平明渠水跃跃后共轭水深 $h_c^{\\prime\\prime}$（水跃衔接形势见解图 14）：\n\n$$\nFr_c = \\frac{v_c}{\\sqrt{g h_c}} = \\frac{11.42}{\\sqrt{9.80 \\times 0.458}} \\approx 5.39 > 1\n$$\n\n$$\nh_c^{\\prime\\prime} = \\frac{h_c}{2}\\left(\\sqrt{1 + 8 Fr_c^2} - 1\\right) = \\frac{0.458}{2}\\left(\\sqrt{1 + 8 \\times 5.39^2} - 1\\right) \\approx 3.27\\,\\mathrm{m}\n$$\n\n与下游实际水深 $h_t = 17.80 - 15.00 = 2.80\\,\\mathrm{m}$ 比较：\n\n$$\nh_t = 2.80\\,\\mathrm{m} < h_c^{\\prime\\prime} = 3.27\\,\\mathrm{m}\n$$\n\n（注：即便第 1 问忽略行近流速取 $q = 5.13\\,\\mathrm{m^3/(s\\cdot m)}$，算得 $h_c = 0.450\\,\\mathrm{m}$，$h_c^{\\prime\\prime} = 3.24\\,\\mathrm{m} > 2.80\\,\\mathrm{m}$，判别结论完全一致。）\n\n**结论**：因下游尾水深度小于跃后共轭水深（$h_t < h_c^{\\prime\\prime}$），水跃被推向下游，坝趾处发生危险的**远驱式水跃**，高速急流（$v_c \\approx 11.4\\,\\mathrm{m/s}$）直接贴底冲刷下游河床，因此**必须修建消力池等底流消能设施**！",
                "analysisFigures": [
                    {"src": "figures/q14_sol.png", "caption": "解图 14　溢流坝下游收缩水深、跃后共轭水深与尾水深对比（远驱式水跃）"}
                ],
                "pitfalls": "1. 求堰上水头 $H$ 和下游水深 $h_t$ 时要用高程相减（$H = 22.80 - 21.00 = 1.80\\,\\mathrm{m}$，$h_t = 17.80 - 15.00 = 2.80\\,\\mathrm{m}$，$T_0 = 6.00 + H_0 = 7.823\\,\\mathrm{m}$），切勿把高程直接当水深代入！\n2. 判别底流消能必须比较**尾水深 $h_t$ 与跃后共轭水深 $h_c^{\\prime\\prime}$**（$h_t < h_c^{\\prime\\prime}$ 为远驱式水跃，必须建消能设施；$h_t \\ge h_c^{\\prime\\prime}$ 为临界或淹没式水跃），切勿只求到临界水深 $h_k = 1.41\\,\\mathrm{m}$ 就停止！",
                "chapter": 9,
                "kps": ["堰流公式", "闸孔出流", "水跃方程", "底流消能判据"],
                "method": "堰流公式求流量+收缩水深共轭水跃判消能法",
                "difficulty": 4,
                "rubric": [
                    {"label": "确定堰上水头 H = 1.80 m、堰高 P = 6.00 m，应用自由堰流公式迭代求得单宽流量 q ≈ 5.23 m³/(s·m)", "pts": 5},
                    {"label": "以坝下渠底为基准列能量方程 T0 = hc + q²/(2gφ²hc²)，迭代求出坝趾收缩水深 hc ≈ 0.458 m", "pts": 5},
                    {"label": "由水跃共轭水深公式求出 hc'' ≈ 3.27 m，与下游水深 ht = 2.80 m 比较判出远驱式水跃并得出需建消能设施结论", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2022-15",
                "year": 2022,
                "no": 15,
                "type": "short",
                "score": 20,
                "title": "新型阀门全开状态局部阻力系数实验测试装置设计与原理步骤",
                "stem": "某企业生产出一新型阀门，请通过实验测试该阀门全开时的局部阻力系数。画出实验装置的示意图，并简要说明测试原理和主要步骤。",
                "note": "",
                "figures": [],
                "shortAnswer": "装置由恒水头溢流水箱、水平等径实验直管、上游参考直管段（设测压管 1、2，间距 l1）、装有全开待测新型阀门的测试段（设测压管 2、3，间距 l2，测压管 3 距阀后至少 8～10 倍管径以待流态恢复）、下游流量调节阀及量水箱组成。由 1—2 段测出单位管长沿程损失 J = (h1-h2)/l1，扣除 2—3 段沿程损失 l2·J 后得纯局部损失 hj = (h2-h3) - (l2/l1)(h1-h2)，结合实测流量 Q 算出 ζ = [π²gd⁴/(8Q²)]·[(h2-h3) - (l2/l1)(h1-h2)]，改变调节阀开度在阻力平方区多组测量取平均值。",
                "judgeAnswer": None,
                "answer": "**一、实验装置示意图（见解图 15）**\n\n实验系统依次由以下部分组成：\n1. **恒水头溢流供水水箱**（进水流量略大于实验流量并由溢流管排走多余水，维持上游水位恒定）；\n2. **水平等径圆管实验段**（内径为 $d$）：\n   - 上游经足够长进口稳定段后，设置无局部管件的**等径参考直管段 $1\\text{—}2$**（长度为 $l_1$，两端接测压管 1、测压管 2，用于同步实测该流量下的管道沿程水力坡度）；\n   - 紧接其后设置**含待测新型阀门的测试管段 $2\\text{—}3$**（总长度为 $l_2$，待测新型阀门始终**保持全开状态**；下游测压管 3 布置在阀后至少 $8d\\sim 10d$ 以外的流态恢复渐变流断面上）；\n3. **尾部流量调节阀**（安装在测压管 3 下游，专门用于调节实验流量，避免触动全开的待测阀门）；\n4. **流量量测装置**（体积量水箱配秒表，或高精度电磁流量计）。\n\n---\n\n**二、测试理论原理**\n\n因水平管道全程等径（$d_1 = d_2 = d_3 = d$，且断面 $1, 2, 3$ 均为充分发展的渐变流断面），由连续性方程知各断面平均流速及动能修正系数均相等：\n\n$$\nv_1 = v_2 = v_3 = v = \\frac{4Q}{\\pi d^2}, \\qquad \\alpha_1 = \\alpha_2 = \\alpha_3\n$$\n\n设测压管 1、2、3 的液面高程读数分别为 $h_1$、$h_2$、$h_3$：\n\n1. **对上游参考直管段 $1\\text{—}2$ 列恒定总流能量方程**（仅有沿程水头损失 $h_{f,1\\text{-}2}$）：\n\n$$\nh_1 + \\frac{\\alpha v^2}{2g} = h_2 + \\frac{\\alpha v^2}{2g} + \\lambda \\frac{l_1}{d}\\frac{v^2}{2g} \\implies h_1 - h_2 = \\lambda \\frac{l_1}{d}\\frac{v^2}{2g} \\quad (1)\n$$\n\n2. **对含全开待测阀门的测试段 $2\\text{—}3$ 列恒定总流能量方程**（包含管长 $l_2$ 的沿程损失 $h_{f,2\\text{-}3}$ 与待测阀门全开局部水头损失 $h_j = \\zeta \\frac{v^2}{2g}$）：\n\n$$\nh_2 + \\frac{\\alpha v^2}{2g} = h_3 + \\frac{\\alpha v^2}{2g} + \\lambda \\frac{l_2}{d}\\frac{v^2}{2g} + \\zeta \\frac{v^2}{2g} \\implies h_2 - h_3 = \\lambda \\frac{l_2}{d}\\frac{v^2}{2g} + \\zeta \\frac{v^2}{2g} \\quad (2)\n$$\n\n3. **联立式 (1)、(2) 消去未知沿程阻力系数 $\\lambda$**，分离出纯局部水头损失 $h_j$：\n\n$$\nh_j = \\zeta \\frac{v^2}{2g} = (h_2 - h_3) - \\frac{l_2}{l_1}(h_1 - h_2)\n$$\n\n代入 $v = \\frac{4Q}{\\pi d^2}$，解得待测新型阀门全开时的局部阻力系数计算公式：\n\n$$\n\\zeta = \\frac{2g h_j}{v^2} = \\frac{\\pi^2 g d^4}{8 Q^2}\\left[(h_2 - h_3) - \\frac{l_2}{l_1}(h_1 - h_2)\\right]\n$$\n\n---\n\n**三、主要实验步骤**\n\n1. **量测几何参数与排气调零**：准确测量实验管内径 $d$、参考段间距 $l_1$ 及测试段间距 $l_2$；将**待测新型阀门旋转至完全开启（全开）位置并锁定**；开启供水泵保持溢流水箱稳定溢流，排净管道及各测压管内的气泡（关死尾部调节阀校核三根测压管静水液面齐平）；\n2. **调节恒定流并同步读数**：打开**尾部流量调节阀**至某一较大开度（使管内处于高雷诺数湍流阻力平方区），待水流及各测压管液面完全稳定后，同步读取测压管液面高度 $h_1$、$h_2$、$h_3$，并用体积法（量水箱收集时间 $t$ 内水体体积 $W$，算得 $Q = W/t$）测定流量 $Q$；\n3. **多工况重复实验取均值**：保持待测新型阀门**全开不动**，仅改变尾部流量调节阀开度（在阻力平方区范围内改变 $4\\sim 6$ 组不同流量 $Q$），重复步骤 2 测算每组对应的 $\\zeta_i$，检验其恒定性并取算术平均值 $\\bar{\\zeta} = \\frac{1}{N}\\sum_{i=1}^N \\zeta_i$ 作为该新型阀门全开局部阻力系数的最终测定值。",
                "analysis": "**实验设计三大高分关键细节（区分优秀答卷与普通答卷的核心）**\n\n1. **为什么要增设参考直管段 $1\\text{—}2$？**\n   阀门局部水头损失无法在零距离内孤立测量，阀门前后两个测压断面间必然夹有一段管长 $l_2$，实测压差 $(h_2 - h_3)$ 中混有沿程摩阻损失 $h_{f,2\\text{-}3}$。利用同管径、同流量的参考段 $1\\text{—}2$ 实测水力坡度 $J = (h_1 - h_2)/l_1$，即可无须查表假设 $\\lambda$ 而精确扣除 $h_{f,2\\text{-}3} = (l_2/l_1)(h_1 - h_2)$！\n2. **为什么测压管 3 必须设在阀后 $(8\\sim 10)d$ 以外？**\n   水流流经阀门局部障碍后会产生边界层分离、主流收缩与回流旋涡区，局部能量耗散要一直持续到下游流束重新扩散充满全管、流速分布恢复正常才宣告结束。若测压管 3 离阀门太近（处于急变旋涡区内），不仅动水压强不服从静水分布，且动能尚未恢复，会导致测值严重失真。\n3. **为什么要单独设尾部流量调节阀？**\n   题目要求测“**阀门全开时**”的局部阻力系数 $\\zeta$，故实验全过程中待测新型阀门必须保持 $100\\%$ 全开，流量调节只能靠下游另设的控制阀完成！",
                "analysisFigures": [
                    {"src": "figures/q15_sol.png", "caption": "解图 15　新型阀门全开局部阻力系数测试实验装置与测压管水头线示意图"}
                ],
                "pitfalls": "1. 切忌在实验步骤中写“调节待测阀门的不同开度来测多组数据”！待测阀门开度一变，$\\zeta$ 就不再是“全开局部阻力系数”而变成不同开度的阀门阻力系数了，改变流量必须靠**下游独立的流量调节阀**！\n2. 切忌只装阀门前后两根测压管而漏掉扣除 $l_2$ 段的沿程水头损失（全开阀门本身的 $\\zeta$ 往往较小，不扣沿程损失会导致显著系统偏大误差）。",
                "chapter": 4,
                "kps": ["沿程与局部损失", "恒定流装置设计", "局部阻力系数实验测定"],
                "method": "等径参考段消去沿程损失测局部阻力系数法",
                "difficulty": 4,
                "rubric": [
                    {"label": "画出完整规范的实验装置示意图（含溢流恒水头水箱、参考段测压管 1-2、含全开待测阀段 2-3、尾部调节阀及量水设备）", "pts": 6},
                    {"label": "分别列出 1—2 参考段与 2—3 测试段的恒定总流能量方程，说明消去沿程阻力系数 λ 的原理", "pts": 5},
                    {"label": "结合连续性方程 v = 4Q/(πd²) 正确推导出 ζ = [π²gd⁴/(8Q²)]·[(h2-h3) - (l2/l1)(h1-h2)]", "pts": 5},
                    {"label": "条理清晰写出排气校零、锁定待测阀全开、用尾部阀调多组恒定流量读取 h1,h2,h3 与 Q 并取均值的实验步骤", "pts": 4}
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

    # 1. Write standardized pack JSON (`扬州大学已整理数据/<year>/<year>.json`)
    pack_json = pack_dir / f"{year}.json"
    pack_json.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[PACK] Wrote {pack_json} ({len(paper['questions'])} questions)")

    # 2. Convert PNG figures -> WebP (`web/public/data/yzu-849/figures/<year>/*.webp`)
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
                im = Image.open(src_png)
                if im.mode not in ("RGB", "RGBA"):
                    im = im.convert("RGBA")
                im.save(dest_webp, format="WEBP", quality=90, method=5)
                new_list.append({
                    "src": f"figures/{year}/{webp_name}",
                    "caption": fig["caption"]
                })
                fig_count += 1
            q[key] = new_list

    # 3. Write web-ready JSON (`web/public/data/yzu-849/<year>.json`)
    web_json = WEB_COURSE_DIR / f"{year}.json"
    web_json.write_text(json.dumps(web_paper, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[WEB]  Wrote {web_json} ({len(web_paper['questions'])} questions, {fig_count} WebP figures)")


def main() -> None:
    pack_2023 = PACK_ROOT / "2023"
    build_2023_figures(pack_2023 / "figures")
    paper_2023 = build_2023_paper()
    write_year_outputs(paper_2023, pack_2023)

    pack_2022 = PACK_ROOT / "2022"
    build_2022_figures(pack_2022 / "figures")
    paper_2022 = build_2022_paper()
    write_year_outputs(paper_2022, pack_2022)


if __name__ == "__main__":
    main()
