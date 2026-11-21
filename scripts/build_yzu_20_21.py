# -*- coding: utf-8 -*-
"""
Generate high-res stem crops (q*_orig.png), matplotlib solution schematics (q*_sol.png),
standardized exam packs in `扬州大学已整理数据/{2021,2020}/`, and web-ready JSON + WebP assets
in `web/public/data/yzu-849/` for Yangzhou University 849 Hydraulics (2021 & 2020).
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
STD_ROOT = ROOT / "扬州大学已整理数据"
WEB_COURSE_DIR = ROOT / "web" / "public" / "data" / "yzu-849"


def render_deskewed_gray(pdf_path: Path, page_idx: int, angle_deg: float = 0.0, dpi: int = 300) -> Image.Image:
    doc = pymupdf.open(str(pdf_path))
    pix = doc[page_idx].get_pixmap(dpi=dpi)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples).convert("L")
    if abs(angle_deg) > 1e-4:
        img = img.rotate(angle_deg, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=255)
    return img


def clean_crop(img: Image.Image, box: tuple[int, int, int, int],
               erase_boxes: list[tuple[int, int, int, int]] | None = None,
               pad: int = 16) -> Image.Image:
    sub = img.crop(box).copy()
    arr = np.array(sub, dtype=np.uint8)
    if erase_boxes:
        for ex0, ey0, ex1, ey1 in erase_boxes:
            arr[ey0:ey1, ex0:ex1] = 255
    mask = arr < 210
    padded = np.pad(mask.astype(np.int32), 1, mode="constant", constant_values=0)
    neigh = sum(
        padded[1 + dy:1 + dy + mask.shape[0], 1 + dx:1 + dx + mask.shape[1]]
        for dy in (-1, 0, 1) for dx in (-1, 0, 1)
    )
    clean_mask = mask & (neigh >= 2)
    arr_clean = np.where(clean_mask, arr, 255).astype(np.uint8)
    ys, xs = np.where(clean_mask)
    if len(xs) > 0:
        arr_clean = arr_clean[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    out = np.full((arr_clean.shape[0] + 2 * pad, arr_clean.shape[1] + 2 * pad), 255, dtype=np.uint8)
    out[pad:pad + arr_clean.shape[0], pad:pad + arr_clean.shape[1]] = arr_clean
    return Image.fromarray(out, mode="L").convert("RGB")


def crop_all_stem_figures(fig_dir_2021: Path, fig_dir_2020: Path) -> None:
    pdf_2021 = RAW_DIR / "849-水力学（水）2021.pdf"
    p21_1 = render_deskewed_gray(pdf_2021, 0, angle_deg=0.64, dpi=300)
    p21_2 = render_deskewed_gray(pdf_2021, 1, angle_deg=1.74, dpi=300)

    crops_2021 = {
        "q07_orig.png": (p21_1, (720, 1940, 1700, 2265), [(390, 275, 580, 325)]),
        "q08_orig.png": (p21_2, (300, 415, 1180, 815), [(315, 355, 505, 400)]),
        "q09_orig.png": (p21_2, (1315, 395, 2175, 815), []),
        "q10_orig.png": (p21_2, (320, 1665, 1115, 2095), []),
        "q11_orig.png": (p21_2, (1285, 1555, 2080, 2175), []),
    }
    for fname, (im, box, eb) in crops_2021.items():
        clean_crop(im, box, eb, pad=16).save(fig_dir_2021 / fname)

    pdf_2020 = RAW_DIR / "849-水力学（水）2020.pdf"
    p20_1 = render_deskewed_gray(pdf_2020, 0, angle_deg=0.75, dpi=300)
    p20_2 = render_deskewed_gray(pdf_2020, 1, angle_deg=0.43, dpi=300)
    p20_3 = render_deskewed_gray(pdf_2020, 2, angle_deg=0.40, dpi=300)

    crops_2020 = {
        "q02_orig.png": (p20_1, (410, 1485, 995, 1968), [(180, 408, 368, 483)]),
        "q03_orig.png": (p20_1, (1180, 1470, 2070, 1855), []),
        "q04_orig.png": (p20_1, (325, 2635, 1215, 3095), [(340, 415, 530, 460)]),
        "q05_orig.png": (p20_1, (1450, 2610, 2120, 3095), []),
        "q06_orig.png": (p20_2, (585, 1105, 1020, 1555), []),
        "q07_orig.png": (p20_2, (1370, 1140, 1865, 1515), []),
        "q08_orig.png": (p20_2, (270, 2192, 1420, 2895), [(590, 0, 820, 22), (495, 638, 680, 703)]),
        "q09_orig.png": (p20_2, (1480, 2350, 2180, 2840), []),
        "q10_orig.png": (p20_3, (1330, 390, 2150, 895), [(310, 465, 505, 505)]),
    }
    for fname, (im, box, eb) in crops_2020.items():
        clean_crop(im, box, eb, pad=16).save(fig_dir_2020 / fname)


# ==============================================================================
# 2021 Solution Schematics (matplotlib, dpi=220, ZERO CJK inside $...$)
# ==============================================================================

def draw_2021_q04_sol(fig_dir: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.0), gridspec_kw={"width_ratios": [1.0, 1.15]})
    fig.patch.set_facecolor("white")

    # (a) Pitot-static tube
    ax1.add_patch(patches.Rectangle((0.4, 0.7), 4.2, 1.4, facecolor="#e0f2fe", alpha=0.6))
    ax1.plot([0.4, 4.6], [2.1, 2.1], color="#0f172a", lw=2.0)
    ax1.plot([0.4, 4.6], [0.7, 0.7], color="#0f172a", lw=2.0)

    # Static piezometer at x=1.6
    ax1.plot([1.54, 1.54], [2.1, 3.6], color="#334155", lw=1.4)
    ax1.plot([1.66, 1.66], [2.1, 3.6], color="#334155", lw=1.4)
    ax1.add_patch(patches.Rectangle((1.55, 2.1), 0.10, 0.75, facecolor="#38bdf8", alpha=0.8))

    # Pitot stagnation tube at x=2.9 bending left to x=2.35 at y=1.4
    ax1.plot([2.35, 2.90, 2.90], [1.44, 1.44, 3.85], color="#0f172a", lw=2.2)
    ax1.plot([2.35, 2.98, 2.98], [1.34, 1.34, 3.85], color="#0f172a", lw=1.4)
    ax1.add_patch(patches.Rectangle((2.89, 2.1), 0.09, 1.42, facecolor="#0284c7", alpha=0.85))

    ax1.annotate("", xy=(1.95, 1.39), xytext=(0.95, 1.39),
                 arrowprops=dict(arrowstyle="->", color="#0369a1", lw=1.8))
    ax1.text(1.35, 1.54, r"$u$", fontsize=11, color="#0369a1", ha="center")
    ax1.scatter([2.32], [1.39], color="#dc2626", s=26, zorder=5)
    ax1.text(2.26, 1.08, "驻点 A", fontsize=9.5, color="#dc2626", ha="center")

    ax1.plot([1.66, 3.55], [2.85, 2.85], color="#64748b", ls="--", lw=1.0)
    ax1.plot([2.98, 3.55], [3.52, 3.52], color="#64748b", ls="--", lw=1.0)
    ax1.annotate("", xy=(3.42, 3.52), xytext=(3.42, 2.85),
                 arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.5))
    ax1.text(3.52, 3.18, r"$\Delta h = \dfrac{u^2}{2g}$", fontsize=10, va="center", color="#dc2626")
    ax1.text(2.5, 0.25, "局部点流速：" + r"$u = \varphi\sqrt{2g\Delta h}$", fontsize=10, ha="center", color="#0f172a")
    ax1.set_title("（a）毕托管测局部点流速", fontsize=11, pad=6)
    ax1.set_xlim(0.2, 4.8)
    ax1.set_ylim(0.05, 4.05)
    ax1.axis("off")

    # (b) Venturi meter
    xs_top = [0.3, 1.4, 2.4, 3.1, 4.5, 5.1]
    ys_top = [1.95, 1.95, 1.62, 1.62, 1.95, 1.95]
    xs_bot = [0.3, 1.4, 2.4, 3.1, 4.5, 5.1]
    ys_bot = [0.85, 0.85, 1.18, 1.18, 0.85, 0.85]
    poly_pts = list(zip(xs_top, ys_top)) + list(zip(xs_bot[::-1], ys_bot[::-1]))
    ax2.add_patch(patches.Polygon(poly_pts, closed=True, facecolor="#e0f2fe", alpha=0.6))
    ax2.plot(xs_top, ys_top, color="#0f172a", lw=2.0)
    ax2.plot(xs_bot, ys_bot, color="#0f172a", lw=2.0)

    for px, ybase, ywat, lbl in [(1.0, 1.95, 3.55, "1"), (2.75, 1.62, 2.65, "2")]:
        ax2.plot([px - 0.06, px - 0.06], [ybase, 3.8], color="#334155", lw=1.3)
        ax2.plot([px + 0.06, px + 0.06], [ybase, 3.8], color="#334155", lw=1.3)
        ax2.add_patch(patches.Rectangle((px - 0.05, ybase), 0.10, ywat - ybase, facecolor="#38bdf8", alpha=0.8))
        ax2.plot([px, px], [0.72, 2.08], color="#dc2626", ls="-.", lw=1.1)
        ax2.text(px, 0.50, f"断面 {lbl}", fontsize=9.5, ha="center", color="#dc2626")

    ax2.plot([1.06, 3.55], [3.55, 3.55], color="#64748b", ls="--", lw=1.0)
    ax2.plot([2.81, 3.55], [2.65, 2.65], color="#64748b", ls="--", lw=1.0)
    ax2.annotate("", xy=(3.38, 3.55), xytext=(3.38, 2.65),
                 arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.5))
    ax2.text(3.48, 3.10, r"$h = \dfrac{v_2^2 - v_1^2}{2g}$", fontsize=10, va="center", color="#dc2626")
    ax2.annotate("", xy=(2.1, 1.40), xytext=(1.2, 1.40),
                 arrowprops=dict(arrowstyle="->", color="#0369a1", lw=1.8))
    ax2.text(2.75, 0.15, "断面平均流速：" + r"$v_1 = \mu\sqrt{\dfrac{2gh}{(A_1/A_2)^2 - 1}}$", fontsize=9.8, ha="center", color="#0f172a")
    ax2.set_title("（b）文丘里流量计测断面平均流速", fontsize=11, pad=6)
    ax2.set_xlim(0.1, 5.3)
    ax2.set_ylim(0.0, 4.05)
    ax2.axis("off")

    plt.tight_layout()
    fig.savefig(fig_dir / "q04_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2021_q07_sol(fig_dir: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.8, 4.2))
    fig.patch.set_facecolor("white")

    # (a) Free discharge
    ax1.plot([0.4, 0.4, 1.3, 1.3], [3.6, 1.4, 1.4, 3.6], color="#0f172a", lw=2.0)
    ax1.add_patch(patches.Rectangle((0.42, 1.42), 0.86, 1.78, facecolor="#bae6fd", alpha=0.6))
    ax1.plot([0.4, 1.3], [3.2, 3.2], color="#0284c7", lw=2.0)
    ax1.plot([1.3, 2.7, 4.0], [1.95, 1.88, 1.25], color="#0f172a", lw=2.0)
    ax1.plot([1.3, 2.7, 4.0], [1.75, 1.68, 1.05], color="#0f172a", lw=2.0)
    # HGL in (a): ends at outlet center (4.0, 1.15); constant hydraulic slope with small bend step at x=2.7
    ax1.plot([1.3, 1.3, 2.7, 2.7, 4.0], [3.20, 2.85, 2.08, 1.98, 1.15], color="#0284c7", ls="-.", lw=1.9, label="测压管水头线 H.G.L.")
    ax1.plot([1.3, 1.3, 2.7, 2.7, 4.0], [3.20, 3.08, 2.31, 2.21, 1.38], color="#dc2626", ls="--", lw=1.6, label="总水头线 E.G.L.")
    ax1.plot([1.3, 4.4], [3.2, 3.2], color="#64748b", ls=":", lw=1.1)
    ax1.plot([4.0, 4.4], [1.15, 1.15], color="#64748b", ls=":", lw=1.1)
    ax1.annotate("", xy=(4.25, 3.2), xytext=(4.25, 1.15),
                 arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.3))
    ax1.text(4.33, 2.18, r"$H$", fontsize=11, va="center")
    # Mark point K at x=2.3
    ax1.scatter([2.3], [1.80], color="#0f172a", s=22, zorder=5)
    ax1.annotate("", xy=(2.3, 2.30), xytext=(2.3, 1.80),
                 arrowprops=dict(arrowstyle="<->", color="#0284c7", lw=1.4))
    ax1.text(2.22, 2.06, r"$\dfrac{p_{K,a}}{\rho g}$", fontsize=9.5, ha="right", color="#0369a1")
    ax1.set_title("（a）自由出流：测压管水头线降至出口中心", fontsize=10.5, pad=6)
    ax1.legend(loc="lower left", fontsize=8.8, frameon=True)
    ax1.set_xlim(0.2, 4.7)
    ax1.set_ylim(0.5, 3.8)
    ax1.axis("off")

    # (b) Submerged discharge: shift entire water levels up by hs=0.55 relative to identical pipe!
    hs = 0.55
    ax2.plot([0.4, 0.4, 1.3, 1.3], [3.85, 1.4, 1.4, 3.85], color="#0f172a", lw=2.0)
    ax2.add_patch(patches.Rectangle((0.42, 1.42), 0.86, 1.78 + hs, facecolor="#bae6fd", alpha=0.6))
    ax2.plot([0.4, 1.3], [3.2 + hs, 3.2 + hs], color="#0284c7", lw=2.0)
    ax2.plot([1.3, 2.7, 4.0], [1.95, 1.88, 1.25], color="#0f172a", lw=2.0)
    ax2.plot([1.3, 2.7, 4.0], [1.75, 1.68, 1.05], color="#0f172a", lw=2.0)
    # Downstream tank
    ax2.plot([4.0, 4.0], [1.25, 2.05], color="#0f172a", lw=2.0)
    ax2.plot([4.0, 4.0, 4.95], [1.05, 0.85, 0.85], color="#0f172a", lw=2.0)
    ax2.add_patch(patches.Rectangle((4.01, 0.87), 0.92, (1.15 + hs) - 0.87, facecolor="#bae6fd", alpha=0.6))
    ax2.plot([4.0, 4.95], [1.15 + hs, 1.15 + hs], color="#0284c7", lw=2.0)

    # HGL in (b): meets downstream water level (1.15 + hs) smoothly; EGL drops vertically by v^2/(2g) at exit!
    ax2.plot([1.3, 1.3, 2.7, 2.7, 4.0],
             [3.20 + hs, 2.85 + hs, 2.08 + hs, 1.98 + hs, 1.15 + hs], color="#0284c7", ls="-.", lw=1.9)
    ax2.plot([1.3, 1.3, 2.7, 2.7, 4.0, 4.0],
             [3.20 + hs, 3.08 + hs, 2.31 + hs, 2.21 + hs, 1.38 + hs, 1.15 + hs], color="#dc2626", ls="--", lw=1.6)
    ax2.plot([1.3, 4.55], [3.2 + hs, 3.2 + hs], color="#64748b", ls=":", lw=1.1)
    ax2.annotate("", xy=(4.45, 3.2 + hs), xytext=(4.45, 1.15 + hs),
                 arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.3))
    ax2.text(4.52, 2.18 + hs, r"$z = H$", fontsize=10.2, va="center")
    # Submergence depth hs
    ax2.annotate("", xy=(4.22, 1.15 + hs), xytext=(4.22, 1.15),
                 arrowprops=dict(arrowstyle="<->", color="#16a34a", lw=1.4))
    ax2.text(4.26, 1.15 + 0.5 * hs, r"$h_s$", fontsize=9.5, va="center", color="#15803d")

    ax2.scatter([2.3], [1.80], color="#0f172a", s=22, zorder=5)
    ax2.annotate("", xy=(2.3, 2.30 + hs), xytext=(2.3, 1.80),
                 arrowprops=dict(arrowstyle="<->", color="#0284c7", lw=1.4))
    ax2.text(2.38, 2.08, r"$\dfrac{p_{K,b}}{\rho g} = \dfrac{p_{K,a}}{\rho g} + h_s$", fontsize=9.0, ha="left", color="#0369a1",
             bbox=dict(boxstyle="round,pad=0.12", facecolor="white", edgecolor="none", alpha=0.88))
    ax2.set_title("（b）淹没出流：流量相同，测压管水头整体抬高 " + r"$h_s$", fontsize=10.5, pad=6)
    ax2.set_xlim(0.2, 5.15)
    ax2.set_ylim(0.5, 4.05)
    ax2.axis("off")

    plt.tight_layout()
    fig.savefig(fig_dir / "q07_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2021_q09_sol(fig_dir: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.8, 4.4))
    fig.patch.set_facecolor("white")

    # Coordinates: C=(2.0, 0.0), B=(5.0, 3.0), center O=(2.0, 3.0), top lid y=4.5, eq free surface y=6.5
    theta = np.linspace(-0.5 * np.pi, 0.0, 120)
    arc_x = 2.0 + 3.0 * np.cos(theta)
    arc_y = 3.0 + 3.0 * np.sin(theta)

    for ax in (ax1, ax2):
        ax.plot([-0.5, 5.8], [6.5, 6.5], color="#0284c7", ls="-.", lw=1.6)
        ax.text(0.3, 6.68, "等效自由液面（高出箱顶 " + r"$h_1 = 2.0\,\mathrm{m}$" + "）", fontsize=9.2, color="#0369a1")
        ax.plot([0.0, 5.0], [4.5, 4.5], color="#0f172a", lw=2.0)
        ax.plot([0.0, 0.0], [0.0, 4.5], color="#0f172a", lw=2.0)
        ax.plot([0.0, 2.0], [0.0, 0.0], color="#0f172a", lw=2.0)
        ax.plot([5.0, 5.0], [3.0, 4.5], color="#0f172a", lw=2.0)
        ax.plot(arc_x, arc_y, color="#dc2626", lw=2.6)
        ax.text(5.15, 3.0, r"$B$", fontsize=10.5, va="center", fontweight="bold")
        ax.text(2.0, -0.38, r"$C$", fontsize=10.5, ha="center", fontweight="bold")
        ax.scatter([2.0], [3.0], color="#0f172a", s=22, zorder=5)
        ax.text(1.85, 3.12, r"$O$", fontsize=10, ha="right")

    # Left subplot: Horizontal projection & trapezoidal pressure diagram
    ax1.plot([2.0, 2.0], [0.0, 3.0], color="#7c3aed", ls="--", lw=1.8)
    # Trapezoid at x in [0.4, 2.0] for y in [0, 3]: top width proportional to 3.5, bottom to 6.5
    w_top, w_bot = 0.85, 1.58
    trap = patches.Polygon([[2.0, 3.0], [2.0 - w_top, 3.0], [2.0 - w_bot, 0.0], [2.0, 0.0]],
                           closed=True, facecolor="#fde68a", edgecolor="#d97706", alpha=0.65, lw=1.4)
    ax1.add_patch(trap)
    for yy in np.linspace(0.3, 2.7, 5):
        ww = w_bot + (w_top - w_bot) * (yy / 3.0)
        ax1.annotate("", xy=(2.0, yy), xytext=(2.0 - ww, yy),
                     arrowprops=dict(arrowstyle="->", color="#b45309", lw=1.1))
    ax1.annotate("", xy=(3.30, 1.95), xytext=(2.05, 1.95),
                 arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.4))
    ax1.text(3.35, 1.95, r"$P_x = 441.45\,\mathrm{kN}$", fontsize=10, va="center", color="#dc2626", fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.88))
    ax1.annotate("", xy=(5.55, 6.5), xytext=(5.55, 3.0),
                 arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.1))
    ax1.text(5.65, 4.75, r"$3.5\,\mathrm{m}$", fontsize=9.2, va="center")
    ax1.set_title("（a）铅直投影面梯形压强图与水平分力 " + r"$P_x$", fontsize=10.5, pad=6)
    ax1.set_xlim(-0.7, 6.5)
    ax1.set_ylim(-0.7, 7.2)
    ax1.axis("off")

    # Right subplot: Real pressure body Vz & resultant P
    pb_x = np.concatenate([[2.0, 5.0], arc_x[::-1], [2.0]])
    pb_y = np.concatenate([[6.5, 6.5], arc_y[::-1], [6.5]])
    ax2.fill(pb_x, pb_y, facecolor="#bae6fd", edgecolor="#0284c7", alpha=0.65, hatch="//", lw=1.4)
    ax2.plot([2.0, 2.0], [0.0, 6.5], color="#0369a1", ls="--", lw=1.3)
    ax2.plot([5.0, 5.0], [4.5, 6.5], color="#0369a1", ls="--", lw=1.3)
    ax2.text(3.5, 5.15, "实压力体 " + r"$V$" + "\n" + r"$= 52.71\,\mathrm{m^3}$",
             fontsize=9.6, ha="center", va="center", color="#0c4a6e",
             bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none", alpha=0.8))

    # Resultant arrow from O(2.0, 3.0) through arc at alpha=49.51 deg below horizontal
    ang = math.radians(49.51)
    x_hit = 2.0 + 3.0 * math.cos(ang)
    y_hit = 3.0 - 3.0 * math.sin(ang)
    ax2.annotate("", xy=(x_hit, y_hit), xytext=(2.0, 3.0),
                 arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.6))
    ax2.plot([2.0, 3.6], [3.0, 3.0], color="#64748b", ls=":", lw=1.2)
    ax2.text(2.68, 2.52, r"$\alpha = 49.5^{\circ}$", fontsize=9.8, color="#dc2626",
             bbox=dict(boxstyle="round,pad=0.12", facecolor="white", edgecolor="none", alpha=0.82))
    ax2.text(x_hit + 0.18, y_hit - 0.18, r"$P = 679.86\,\mathrm{kN}$", fontsize=10, color="#dc2626", fontweight="bold")
    ax2.annotate("", xy=(3.95, 2.25), xytext=(3.95, 3.85),
                 arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.2))
    ax2.text(4.06, 3.45, r"$P_z = 517.04\,\mathrm{kN}$", fontsize=9.5, color="#0369a1", fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.88))
    ax2.set_title("（b）实压力体（矩形 + 1/4 圆）与总压力 " + r"$P$", fontsize=10.5, pad=6)
    ax2.set_xlim(-0.7, 6.5)
    ax2.set_ylim(-0.7, 7.2)
    ax2.axis("off")

    plt.tight_layout()
    fig.savefig(fig_dir / "q09_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2021_q11_sol(fig_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    fig.patch.set_facecolor("white")

    th = math.radians(55)
    c, s = math.cos(th), math.sin(th)

    # Inclined flat plate passing through origin (0,0)
    L1, L2 = -2.2, 2.5
    ax.plot([L1 * c, L2 * c], [L1 * s, L2 * s], color="#0f172a", lw=3.0)
    for ll in np.linspace(L1 + 0.15, L2 - 0.15, 20):
        ax.plot([ll * c, ll * c + 0.22 * s], [ll * s, ll * s - 0.22 * c], color="#64748b", lw=1.0)

    # Incoming horizontal jet from left
    ax.plot([-3.2, -1.3], [0.32, 0.32], color="#0284c7", lw=1.8)
    ax.plot([-3.2, -1.3], [-0.32, -0.32], color="#0284c7", lw=1.8)
    ax.annotate("", xy=(-1.1, 0.0), xytext=(-2.9, 0.0),
                arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2.2))
    ax.text(-2.52, 0.50, "入射射流 " + r"$Q_0,\; v_0$", fontsize=10.2, ha="center", color="#0369a1")
    ax.plot([-1.1, 1.3], [0.0, 0.0], color="#64748b", ls="--", lw=1.2)
    ax.text(0.55, 0.18, r"$\theta$", fontsize=11.5, color="#0f172a")

    # Control volume dashed loop
    cv_pts = [[-1.5, -0.55], [-1.5, 0.55], [1.65 * c - 0.45 * s, 1.65 * s + 0.45 * c],
              [1.95 * c, 1.95 * s], [-1.75 * c, -1.75 * s], [-1.75 * c - 0.40 * s, -1.75 * s + 0.40 * c]]
    ax.add_patch(patches.Polygon(cv_pts, closed=True, facecolor="#e0f2fe", edgecolor="#0284c7", ls="--", lw=1.3, alpha=0.45))

    # Split flows along +S and -S
    ax.annotate("", xy=(1.85 * c - 0.18 * s, 1.85 * s + 0.18 * c),
                xytext=(0.75 * c - 0.18 * s, 0.75 * s + 0.18 * c),
                arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.0))
    ax.text(1.25 * c - 0.52 * s, 1.25 * s + 0.52 * c, r"$Q_1,\; v_1 = v_0$", fontsize=10, ha="right", color="#0369a1")

    ax.annotate("", xy=(-1.65 * c - 0.16 * s, -1.65 * s + 0.16 * c),
                xytext=(-0.70 * c - 0.16 * s, -0.70 * s + 0.16 * c),
                arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.0))
    ax.text(-1.25 * c - 0.48 * s, -1.25 * s + 0.48 * c, r"$Q_2,\; v_2 = v_0$", fontsize=10, ha="right", color="#0369a1")

    # S axis & normal reaction Rn / impact force F
    ax.annotate("", xy=(2.85 * c, 2.85 * s), xytext=(2.25 * c, 2.25 * s),
                arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.8))
    ax.text(2.92 * c, 2.92 * s, r"$S$", fontsize=11.5, fontweight="bold")

    # Normal reaction Rn on fluid (up-left) and impact force F on plate (down-right)
    ax.annotate("", xy=(-1.05 * s, 1.05 * c), xytext=(0.0, 0.0),
                arrowprops=dict(arrowstyle="->", color="#16a34a", lw=2.3))
    ax.text(-1.05 * s + 0.05, 1.05 * c + 0.22, "平板反力 " + r"$R_n$", fontsize=10, ha="center", color="#15803d")

    ax.annotate("", xy=(1.15 * s, -1.15 * c), xytext=(0.0, 0.0),
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.6))
    ax.text(1.22 * s, -1.18 * c, "冲击力 " + r"$F = \rho Q_0 v_0 \sin\theta$",
            fontsize=10.5, va="center", color="#dc2626", fontweight="bold")

    ax.set_xlim(-3.5, 3.2)
    ax.set_ylim(-2.1, 2.6)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q11_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2021_q12_sol(fig_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    fig.patch.set_facecolor("white")

    h = 2.0
    m = 1.0 / math.sqrt(3)  # 60 deg side slope -> regular half-hexagon!
    b = 2.0 * h * (math.sqrt(1 + m**2) - m)  # optimal bottom width

    x_bl, x_br = -0.5 * b, 0.5 * b
    x_tl, x_tr = -0.5 * b - m * h, 0.5 * b + m * h

    ax.add_patch(patches.Polygon([[x_tl, h], [x_bl, 0], [x_br, 0], [x_tr, h]],
                                 closed=True, facecolor="#e0f2fe", alpha=0.65))
    ax.plot([x_tl - 0.35, x_tl, x_bl, x_br, x_tr, x_tr + 0.35],
            [h, h, 0, 0, h, h], color="#0f172a", lw=2.4)
    ax.plot([x_tl, x_tr], [h, h], color="#0284c7", lw=2.0)

    # Inscribed semicircle centered at O(0, h) with radius R_c = h?
    # Wait: distance from midpoint of water surface O(0, h) to bottom y=0 is h,
    # and distance from O(0, h) to side slope (x - x_br) - m y = 0 -> x - m y - b/2 = 0:
    # |0 - m*h - b/2| / sqrt(1 + m^2) = (m*h + h*(sqrt(1+m^2) - m)) / sqrt(1+m^2) = h!!
    # YES! A semicircle centered at O(0, h) of radius r = h is tangent to bottom AND both side walls!
    # Wait: R = A / chi = h / 2, while the inscribed tangent circle centered at water surface midpoint has radius h!
    th = np.linspace(np.pi, 2 * np.pi, 180)
    ax.plot(h * np.cos(th), h + h * np.sin(th), color="#dc2626", ls="--", lw=1.8,
            label="以水面中点 O 为圆心、水深 h 为半径的相切半圆")
    ax.scatter([0.0], [h], color="#dc2626", s=28, zorder=5)
    ax.text(0.0, h + 0.16, r"$O$", fontsize=11, ha="center", color="#dc2626", fontweight="bold")

    # Normal from O(0, h) to right side wall
    nx = h / math.sqrt(1 + m**2)
    ny = -m * h / math.sqrt(1 + m**2)
    ax.annotate("", xy=(nx, h + ny), xytext=(0, h),
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=1.6))
    ax.text(0.55 * nx + 0.12, h + 0.55 * ny + 0.08, r"$h$", fontsize=10.5, color="#dc2626")

    # Dimension b and h
    ax.annotate("", xy=(x_br, -0.28), xytext=(x_bl, -0.28),
                arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.4))
    ax.text(0.0, -0.52, r"$b = 2h(\sqrt{1+m^2} - m)$", fontsize=10.2, ha="center", color="#0f172a")

    ax.annotate("", xy=(0.0, 0.0), xytext=(0.0, h),
                arrowprops=dict(arrowstyle="<->", color="#0369a1", lw=1.5))
    ax.text(-0.14, 0.5 * h, r"$h$", fontsize=11, ha="right", va="center", color="#0369a1")

    ax.text(x_tr - 0.15, 0.45 * h, "边坡 " + r"$1 : m$", fontsize=10, ha="left", color="#334155")
    ax.text(0.0, h + 0.52, "水力最佳梯形断面：" + r"$R = \dfrac{A}{\chi} = \dfrac{h}{2}$",
            fontsize=11, ha="center", color="#0f172a", fontweight="bold")

    ax.legend(loc="lower right", fontsize=8.8, frameon=True)
    ax.set_xlim(-2.9, 2.9)
    ax.set_ylim(-0.85, 2.75)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q12_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


# ==============================================================================
# 2020 Solution Schematics (matplotlib, dpi=220, ZERO CJK inside $...$)
# ==============================================================================

def draw_2020_q06_sol(fig_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.8, 4.6))
    fig.patch.set_facecolor("white")

    # Hinge B at (2.2, 1.4), vertical gate AB up to (2.2, 3.9), horizontal gate BC to (3.8, 1.4)
    bx, by = 2.2, 1.4
    L_draw = 1.6  # represents L = 1 m
    h_draw = 2.15  # represents h = 1.732 m

    # Upstream water & bottom chamber water
    ax.add_patch(patches.Rectangle((0.3, 0.4), bx - 0.3, by + h_draw - 0.4, facecolor="#e0f2fe", alpha=0.6))
    th = np.linspace(-0.5 * np.pi, 0.0, 80)
    ch_x = np.concatenate([[bx], bx + L_draw * np.cos(th), [bx]])
    ch_y = np.concatenate([[by], by + L_draw * np.sin(th), [by - L_draw]])
    ax.fill(ch_x, ch_y, facecolor="#e0f2fe", alpha=0.6)
    ax.plot(bx + L_draw * np.cos(th), by + L_draw * np.sin(th), color="#334155", lw=2.0)

    # Free surface
    ax.plot([0.3, bx], [by + h_draw, by + h_draw], color="#0284c7", lw=2.0)

    # L-gate ABC
    ax.add_patch(patches.Rectangle((bx, by), 0.14, h_draw + 0.35, facecolor="#cbd5e1", edgecolor="#0f172a", lw=2.0, zorder=4))
    ax.add_patch(patches.Rectangle((bx, by), L_draw, 0.14, facecolor="#cbd5e1", edgecolor="#0f172a", lw=2.0, zorder=4))
    ax.plot([bx + 0.14, bx + L_draw - 0.2], [by + 1.65, by + 0.14], color="#475569", lw=2.5, zorder=4)
    ax.scatter([bx], [by], s=65, facecolor="white", edgecolor="#0f172a", lw=2.2, zorder=6)
    ax.text(bx - 0.12, by - 0.18, "铰轴 " + r"$B$", fontsize=10.5, ha="right", fontweight="bold")
    ax.text(bx + 0.07, by + h_draw + 0.45, r"$A$", fontsize=11, ha="center", fontweight="bold")
    ax.text(bx + L_draw + 0.12, by + 0.07, r"$C$", fontsize=11, va="center", fontweight="bold")

    # Stop lip at C
    ax.plot([bx + L_draw - 0.05, bx + L_draw - 0.05, bx + L_draw + 0.45],
            [by + 0.16, by + 0.42, by + 0.42], color="#0f172a", lw=2.0)

    # Horizontal triangular pressure load on AB
    ax.add_patch(patches.Polygon([[bx, by + h_draw], [bx - 1.15, by], [bx, by]],
                                 closed=True, facecolor="#fde68a", edgecolor="#d97706", alpha=0.65, lw=1.4, zorder=5))
    y_px = by + h_draw / 3.0
    ax.annotate("", xy=(bx, y_px), xytext=(bx - 1.35, y_px),
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.5), zorder=6)
    ax.text(bx - 1.40, y_px + 0.12, r"$P_x = \dfrac{1}{2}\rho g h^2 b$", fontsize=10, ha="right", color="#dc2626", fontweight="bold")
    ax.text(bx - 1.40, y_px - 0.22, "力臂 " + r"$e_1 = \dfrac{h}{3}$", fontsize=9.5, ha="right", color="#b91c1c")

    # Vertical uniform upward pressure load on BC
    ax.add_patch(patches.Rectangle((bx + 0.05, by - 0.55), L_draw - 0.10, 0.55,
                                   facecolor="#bbf7d0", edgecolor="#16a34a", alpha=0.65, lw=1.4, zorder=5))
    x_pz = bx + 0.5 * L_draw
    ax.annotate("", xy=(x_pz, by), xytext=(x_pz, by - 0.95),
                arrowprops=dict(arrowstyle="->", color="#15803d", lw=2.5), zorder=6)
    ax.text(x_pz + 0.12, by - 0.88, r"$P_z = \rho g h L b$", fontsize=10, color="#15803d", fontweight="bold")
    ax.text(x_pz + 0.12, by - 1.18, "力臂 " + r"$e_2 = \dfrac{L}{2} = 0.5\,\mathrm{m}$", fontsize=9.5, color="#166534")

    ax.text(bx + 1.05, by + 1.85, "临界开启力矩平衡：\n" + r"$P_x \cdot \dfrac{h}{3} = P_z \cdot \dfrac{L}{2}$" + "\n" + r"$\Rightarrow h = \sqrt{3}\,L \approx 1.73\,\mathrm{m}$",
            fontsize=10, color="#0f172a", bbox=dict(boxstyle="round,pad=0.35", facecolor="#f8fafc", edgecolor="#cbd5e1"))

    ax.set_xlim(0.0, 5.4)
    ax.set_ylim(-0.35, 4.35)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q06_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2020_q07_sol(fig_dir: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.8, 4.4))
    fig.patch.set_facecolor("white")

    R = 2.0
    ang30 = math.radians(30)
    xE, yE = R * math.sin(ang30), -R * math.cos(ang30)  # (1.0, -1.732)
    h_tot = R - yE  # 3.732

    th_full = np.linspace(0, 2 * np.pi, 240)
    # Wetted arc from A(0, R) [angle pi/2] CCW to E(1, -1.732) [angle 5*pi/3 = 300 deg]
    th_wet = np.linspace(0.5 * np.pi, 5.0 * np.pi / 3.0, 180)

    for ax in (ax1, ax2):
        # Slope line tangent at E(1, -1.732) with angle 30 deg: y - yE = tan(30)*(x - xE)
        xs_sl = np.array([-2.8, 3.2])
        ys_sl = yE + math.tan(ang30) * (xs_sl - xE)
        ax.plot(xs_sl, ys_sl, color="#0f172a", lw=2.2)
        ax.plot([-2.8, -2.8], [ys_sl[0], 2.5], color="#0f172a", lw=2.2)
        ax.plot([-2.8, 0.0], [R, R], color="#0284c7", lw=2.0)
        ax.plot(R * np.cos(th_full), R * np.sin(th_full), color="#94a3b8", ls="--", lw=1.2)
        ax.plot(R * np.cos(th_wet), R * np.sin(th_wet), color="#dc2626", lw=2.6)
        ax.scatter([0, 0, -R, 0, xE], [0, R, 0, -R, yE], color="#0f172a", s=20, zorder=5)
        ax.text(0.12, 0.08, r"$O$", fontsize=10)
        ax.text(0.0, R + 0.18, r"$A$", fontsize=10, ha="center")
        ax.text(-R - 0.18, 0.0, r"$B$", fontsize=10, va="center", ha="right")
        ax.text(0.0, -R - 0.28, r"$C$", fontsize=10, ha="center")
        ax.text(xE + 0.15, yE - 0.18, r"$E$", fontsize=10)

    # Left subplot: Horizontal force Px projection from z_A to z_E
    ax1.plot([xE, xE], [yE, R], color="#7c3aed", ls="-.", lw=1.5)
    ax1.add_patch(patches.Polygon([[-2.55, R], [-2.55, yE], [-0.95, yE]],
                                  closed=True, facecolor="#fde68a", edgecolor="#d97706", alpha=0.65, lw=1.3))
    ax1.annotate("", xy=(-0.55, R - 2.0 * h_tot / 3.0), xytext=(-2.45, R - 2.0 * h_tot / 3.0),
                 arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.4))
    ax1.text(-1.55, 0.85, r"$P_x = \dfrac{1}{2}\rho g h^2 b$" + "\n" + r"$\approx 68.32\,\mathrm{kN}$",
             fontsize=9.6, ha="center", color="#991b1b", fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none", alpha=0.85))
    ax1.annotate("", xy=(2.15, R), xytext=(2.15, yE),
                 arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.3))
    ax1.text(2.26, 0.5 * (R + yE), r"$h = R(1 + \cos 30^{\circ})$" + "\n" + r"$= 3.732\,\mathrm{m}$",
             fontsize=9.2, va="center", color="#0f172a")
    ax1.set_title("（a）有效受压铅直投影高度 " + r"$h$" + " 与水平分力 " + r"$P_x$", fontsize=10.3, pad=6)
    ax1.set_xlim(-3.2, 4.15)
    ax1.set_ylim(-3.6, 2.8)
    ax1.set_aspect("equal")
    ax1.axis("off")

    # Right subplot: Net upward pressure body (left semicircle + 30 deg sector COE + trapezoid AOEF)
    th_semi = np.linspace(0.5 * np.pi, 1.5 * np.pi, 100)
    ax2.fill(np.concatenate([[0], R * np.cos(th_semi), [0]]),
             np.concatenate([[R], R * np.sin(th_semi), [-R]]),
             facecolor="#bae6fd", alpha=0.7, edgecolor="#0284c7", lw=1.2)
    th_sec = np.linspace(1.5 * np.pi, 5.0 * np.pi / 3.0, 40)
    ax2.fill(np.concatenate([[0], R * np.cos(th_sec), [0]]),
             np.concatenate([[0], R * np.sin(th_sec), [0]]),
             facecolor="#7dd3fc", alpha=0.75, edgecolor="#0284c7", lw=1.2)
    ax2.fill([0, xE, xE, 0], [0, yE, R, R],
             facecolor="#bbf7d0", alpha=0.65, edgecolor="#16a34a", lw=1.2)
    ax2.plot([0, xE], [R, R], color="#0284c7", ls="--", lw=1.4)
    ax2.text(xE, R + 0.18, r"$F$", fontsize=10, ha="center")

    ax2.annotate("", xy=(-0.3, 1.65), xytext=(-0.3, -0.35),
                 arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2.5))
    ax2.text(1.35, 1.25, "净铅垂压力体：\n半圆 + " + r"$30^{\circ}$" + "扇形 + 梯形\n" + r"$V \approx 10.20\,\mathrm{m^3}$" + "\n" + r"$P_z \approx 100.03\,\mathrm{kN}$（向上）",
             fontsize=9.2, color="#0c4a6e", bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#cbd5e1", alpha=0.92))
    ax2.set_title("（b）净虚压力体分块构成与铅垂分力 " + r"$P_z$", fontsize=10.3, pad=6)
    ax2.set_xlim(-3.2, 3.8)
    ax2.set_ylim(-3.6, 2.8)
    ax2.set_aspect("equal")
    ax2.axis("off")

    plt.tight_layout()
    fig.savefig(fig_dir / "q07_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2020_q09_sol(fig_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    fig.patch.set_facecolor("white")

    # Incoming jet along +x
    ax.add_patch(patches.Polygon([[-3.0, 0.32], [0.0, 0.32], [1.9, 1.42], [2.15, 1.00],
                                  [0.35, -0.05], [0.0, -0.05], [0.0, -1.85], [-0.28, -1.85],
                                  [-0.28, -0.32], [-3.0, -0.32]],
                                 closed=True, facecolor="#bae6fd", alpha=0.65))
    ax.plot([-3.0, -0.15, 1.9], [0.32, 0.32, 1.42], color="#0f172a", lw=1.8)
    ax.plot([-3.0, -0.28, -0.28], [-0.32, -0.32, -1.85], color="#0f172a", lw=1.8)
    ax.plot([0.35, 2.15], [-0.05, 1.00], color="#0f172a", lw=1.8)

    # Vertical plate on right of Q1
    ax.add_patch(patches.Rectangle((0.0, -1.85), 0.28, 1.80, facecolor="#cbd5e1", edgecolor="#0f172a", hatch="///", lw=1.8, zorder=5))
    ax.plot([-0.4, 1.8], [0.0, 0.0], color="#64748b", ls="-.", lw=1.2)
    ax.text(1.05, 0.18, r"$\theta = 30^{\circ}$", fontsize=10.5, color="#0f172a")

    ax.annotate("", xy=(-0.8, 0.0), xytext=(-2.6, 0.0),
                arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2.0))
    ax.text(-1.8, 0.50, r"$Q = 36\,\mathrm{L/s},\; v = 30\,\mathrm{m/s}$", fontsize=9.8, ha="center", color="#0369a1")

    ax.annotate("", xy=(-0.14, -1.75), xytext=(-0.14, -0.65),
                arrowprops=dict(arrowstyle="->", color="#0369a1", lw=1.8))
    ax.text(-0.42, -1.35, r"$Q_1 = 12\,\mathrm{L/s}$" + "\n" + r"$v_1 = 30\,\mathrm{m/s}$", fontsize=9.5, ha="right", color="#0369a1")

    ax.annotate("", xy=(1.85, 1.12), xytext=(0.65, 0.42),
                arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2.0))
    ax.text(0.82, 1.38, r"$Q_2 = 24\,\mathrm{L/s},\; v_2 = 30\,\mathrm{m/s}$", fontsize=9.8, ha="center", color="#0369a1")

    # Reaction Rx on fluid (-x) and impact force Fx on plate (+x)
    ax.annotate("", xy=(-0.95, -0.82), xytext=(0.0, -0.82),
                arrowprops=dict(arrowstyle="->", color="#16a34a", lw=2.2), zorder=6)
    ax.text(-1.02, -0.72, "板对水反力 " + r"$R_x$", fontsize=9.5, ha="right", color="#15803d")

    ax.annotate("", xy=(1.35, -0.82), xytext=(0.28, -0.82),
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.5), zorder=6)
    ax.text(1.42, -0.82, "射流作用力 " + r"$F_x = 456.46\,\mathrm{N}$", fontsize=10, va="center", color="#dc2626", fontweight="bold")

    # Coordinate axes placed cleanly at bottom right below Fx label
    ax.annotate("", xy=(2.95, -1.78), xytext=(2.25, -1.78), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.4))
    ax.annotate("", xy=(2.25, -1.18), xytext=(2.25, -1.78), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.4))
    ax.text(3.03, -1.78, r"$x$", fontsize=10.5, va="center")
    ax.text(2.25, -1.08, r"$y$", fontsize=10.5, ha="center")

    ax.set_xlim(-3.2, 3.55)
    ax.set_ylim(-2.1, 1.75)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q09_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2020_q10_sol(fig_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    fig.patch.set_facecolor("white")

    # Water tower on left
    ax.plot([0.5, 0.5, 1.8, 1.8], [3.7, 2.5, 2.5, 3.7], color="#0f172a", lw=2.0)
    ax.add_patch(patches.Rectangle((0.52, 2.52), 1.26, 0.88, facecolor="#bae6fd", alpha=0.65))
    ax.plot([0.5, 1.8], [3.4, 3.4], color="#0284c7", lw=2.0)

    # Original pipe A -> corner -> B -> C (outlet)
    ax.plot([0.95, 0.95, 6.4], [2.5, 0.8, 0.8], color="#0f172a", lw=2.4)
    # Parallel branch from A'(1.45, 2.5) to midpoint B(3.65, 0.8)
    ax.plot([1.45, 3.65], [2.5, 0.8], color="#dc2626", ls="--", lw=2.4, label="新增并联支管 " + r"$x = 42.09\,\mathrm{m}\;(Q_x = 0.743 Q_0)$")
    ax.scatter([3.65], [0.8], color="#0f172a", s=32, zorder=5)
    ax.text(3.30, 0.45, "中点节点 " + r"$B\;(l_1 = l_2 = 75\,\mathrm{m})$", fontsize=9.5, ha="center", fontweight="bold")
    ax.text(0.82, 1.55, r"$Q_1 = 0.557 Q_0$", fontsize=9.2, ha="right", color="#0369a1")
    ax.text(5.35, 0.45, "下游干管 " + r"$Q' = 1.30 Q_0$", fontsize=9.5, ha="center", color="#0f172a")

    # Hydraulic Grade Lines (datum y=0.8, H_draw = 2.6 -> y_surf = 3.4)
    # Original HGL: straight line from (0.95, 3.4) to (6.4, 0.8) (at B, y = 0.8 + 0.5*2.6 = 2.1)
    ax.plot([0.95, 3.65, 6.4], [3.4, 2.1, 0.8], color="#64748b", ls=":", lw=1.7, label="加管前测压管水头线（中点水头 " + r"$0.500 H$" + "）")
    # Modified HGL: at B, H_B = 0.845 H -> y_B = 0.8 + 0.845 * 2.6 = 2.997
    y_B_new = 0.8 + 0.845 * 2.6
    ax.plot([1.20, 3.65, 6.4], [3.4, y_B_new, 0.8], color="#0284c7", ls="-.", lw=2.1, label="加管后测压管水头线（节点水头 " + r"$H_B = 0.845 H$" + "）")

    ax.plot([1.8, 6.7], [3.4, 3.4], color="#94a3b8", ls=":", lw=1.0)
    ax.annotate("", xy=(3.65, 3.4), xytext=(3.65, y_B_new),
                arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.4))
    ax.text(3.75, 0.5 * (3.4 + y_B_new), r"$h_{f,AB} = 0.155 H$", fontsize=9.5, va="center", color="#dc2626")

    ax.annotate("", xy=(3.65, y_B_new), xytext=(3.65, 0.8),
                arrowprops=dict(arrowstyle="<->", color="#0284c7", lw=1.4))
    ax.text(3.78, 0.5 * (y_B_new + 0.8) + 0.25, r"$h_{f,BC} = 0.845 H$", fontsize=9.5, va="center", color="#0369a1",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.88))

    ax.legend(loc="upper right", fontsize=8.6, frameon=True)
    ax.set_xlim(0.1, 7.1)
    ax.set_ylim(0.2, 4.05)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q10_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2020_q13_sol(fig_dir: Path) -> None:
    fig = plt.figure(figsize=(9.2, 5.4))
    fig.patch.set_facecolor("white")
    gs = fig.add_gridspec(2, 3, height_ratios=[1.55, 1.0], hspace=0.28, wspace=0.18)

    # Top panel: Reynolds apparatus
    ax = fig.add_subplot(gs[0, :])
    # Supply tank with overflow weir
    ax.plot([0.6, 0.6, 2.5, 2.5], [3.4, 0.8, 0.8, 3.4], color="#0f172a", lw=2.0)
    ax.plot([1.15, 1.15], [0.8, 2.90], color="#0f172a", lw=1.8)
    ax.add_patch(patches.Rectangle((1.17, 0.82), 1.31, 2.08, facecolor="#bae6fd", alpha=0.6))
    ax.plot([1.15, 2.48], [2.90, 2.90], color="#0284c7", lw=2.0)
    ax.text(1.85, 2.25, "恒水头水箱\n（溢流稳压）", fontsize=8.8, ha="center", va="center", color="#0369a1", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.82))
    # Supply & overflow pipes
    ax.annotate("", xy=(2.28, 2.98), xytext=(2.28, 3.62), arrowprops=dict(arrowstyle="->", color="#0284c7", lw=1.7))
    ax.text(2.28, 3.72, "进水管", fontsize=9, ha="center")
    ax.plot([0.85, 0.85], [0.8, 0.3], color="#0f172a", lw=1.6)
    ax.text(0.85, 0.08, "溢流管", fontsize=9, ha="center", color="#475569")

    # Dye bottle & fine injector needle
    ax.add_patch(patches.Rectangle((1.42, 3.62), 0.46, 0.52, facecolor="#fecaca", edgecolor="#b91c1c", lw=1.5))
    ax.text(1.65, 4.24, "颜色水瓶", fontsize=9, ha="center", color="#b91c1c")
    ax.plot([1.65, 1.65, 2.75], [3.62, 1.45, 1.45], color="#dc2626", lw=1.5)
    ax.scatter([1.65], [3.32], color="#b91c1c", marker="s", s=22, zorder=5)
    ax.text(1.52, 3.32, "阀门 " + r"$K_2$", fontsize=8.6, ha="right", va="center", color="#b91c1c")

    # Bell-mouth horizontal glass tube
    ax.add_patch(patches.Rectangle((2.50, 1.30), 4.6, 0.30, facecolor="#e0f2fe", alpha=0.55))
    ax.plot([2.32, 2.52, 7.1], [1.75, 1.60, 1.60], color="#0f172a", lw=1.8)
    ax.plot([2.32, 2.52, 7.1], [1.15, 1.30, 1.30], color="#0f172a", lw=1.8)
    ax.plot([2.75, 6.45], [1.45, 1.45], color="#dc2626", lw=1.8)
    ax.text(4.65, 1.74, "透明玻璃实验圆管（喇叭口平顺进水）", fontsize=9.5, ha="center", color="#0f172a")
    ax.text(4.65, 1.02, "有色细流束", fontsize=9, ha="center", color="#dc2626")

    # Downstream control valve K1 & outflow into measuring tank
    vx = 6.65
    ax.plot([vx - 0.16, vx + 0.16, vx + 0.16, vx - 0.16, vx - 0.16],
            [1.68, 1.22, 1.68, 1.22, 1.68], color="#0f172a", lw=1.5)
    ax.plot([vx, vx], [1.45, 1.88], color="#0f172a", lw=1.5)
    ax.plot([vx - 0.12, vx + 0.12], [1.88, 1.88], color="#0f172a", lw=1.8)
    ax.text(vx, 2.02, "调节阀 " + r"$K_1$", fontsize=9.5, ha="center", fontweight="bold")
    ax.plot([7.1, 7.45, 7.45], [1.45, 1.45, 0.95], color="#0284c7", lw=2.0)
    ax.plot([7.2, 7.2, 7.8, 7.8], [0.95, 0.35, 0.35, 0.95], color="#0f172a", lw=1.6)
    ax.text(7.5, 0.08, "量水箱", fontsize=9, ha="center")

    ax.set_xlim(0.3, 8.2)
    ax.set_ylim(-0.05, 4.45)
    ax.axis("off")

    # Bottom 3 sub-panels: (a) Laminar, (b) Transitional, (c) Turbulent
    titles = [
        "（a）层流（" + r"$Re < Re_c$" + "）：平直清晰色线",
        "（b）过渡流：色线呈波形摆动",
        "（c）湍流（" + r"$Re > Re_c$" + "）：破裂混掺全管",
    ]
    for i, ttl in enumerate(titles):
        sub = fig.add_subplot(gs[1, i])
        sub.add_patch(patches.Rectangle((0.1, 0.25), 3.8, 0.50, facecolor="#f1f5f9", edgecolor="none"))
        sub.plot([0.1, 3.9], [0.75, 0.75], color="#0f172a", lw=1.8)
        sub.plot([0.1, 3.9], [0.25, 0.25], color="#0f172a", lw=1.8)
        xx = np.linspace(0.2, 3.8, 200)
        if i == 0:
            sub.plot(xx, np.full_like(xx, 0.50), color="#dc2626", lw=2.2)
        elif i == 1:
            yy = 0.50 + 0.11 * np.sin(5.5 * (xx - 0.2)) * np.clip((xx - 0.5) / 2.2, 0.15, 1.0)
            sub.plot(xx, yy, color="#dc2626", lw=2.0)
        else:
            sub.plot([0.2, 0.85], [0.50, 0.50], color="#dc2626", lw=2.0)
            sub.add_patch(patches.Rectangle((0.85, 0.27), 3.02, 0.46, facecolor="#fca5a5", alpha=0.65))
            rng = np.random.default_rng(42)
            pts_x = rng.uniform(0.95, 3.8, 65)
            pts_y = rng.uniform(0.30, 0.70, 65)
            sub.scatter(pts_x, pts_y, s=6, color="#dc2626", alpha=0.75)
        sub.set_title(ttl, fontsize=9.4, pad=4)
        sub.set_xlim(0.0, 4.0)
        sub.set_ylim(0.05, 0.95)
        sub.axis("off")

    fig.savefig(fig_dir / "q13_sol.png", dpi=220, facecolor="white", bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)


# ==============================================================================
# 2021 Exam Paper Structured Data (13 Questions, 150 Points)
# ==============================================================================

def build_2021_paper() -> dict:
    return {
        "year": 2021,
        "code": "849",
        "subject": "水力学（水）",
        "school": "扬州大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": True,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "全卷共 13 道题：一、简答题（第 1～7 题，7×8=56 分）；二、计算题（第 8～13 题，15+17+15+17+15+15=94 分）。",
            "结合第 9 题给定表压 $p_g = 1.962\\times 10^4\\,\\mathrm{Pa}$ 参数协调关系，计算统一取重力加速度 $g = 9.81\\,\\mathrm{m/s^2}$，水的密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$（解析同步附 $g = 9.80\\,\\mathrm{m/s^2}$ 对照结果）。"
        ],
        "sections": [
            {
                "id": "short",
                "title": "一、简答题",
                "description": "本大题共 7 小题，每小题 8 分，共 56 分。",
                "range": [1, 7],
                "scorePerQuestion": 8,
                "totalScore": 56
            },
            {
                "id": "calc",
                "title": "二、计算题",
                "description": "本大题共 6 小题（15+17+15+17+15+15 分），共 94 分。",
                "range": [8, 13],
                "totalScore": 94
            }
        ],
        "questions": [
            {
                "id": "yzu-849-2021-01",
                "year": 2021,
                "no": 1,
                "type": "short",
                "score": 8,
                "title": "水力学的三种基本研究方法及其优势与局限性分析",
                "stem": "水力学的研究方法有哪些？简要说明各方法的优势和局限性。",
                "note": "",
                "figures": [],
                "shortAnswer": "三大研究方法：理论分析法、科学实验法（原型观测与模型试验）、数值计算法（计算水力学）。三者在严密普适性、真实复杂边界复现与低成本高精度流场模拟上各有优劣、相辅相成。",
                "judgeAnswer": None,
                "answer": "水力学主要有**理论分析法**、**科学实验法**和**数值计算法**三种研究方法：\n\n1. **理论分析法**：\n   - **优势**：以经典力学守恒定律（质量、动量、能量守恒）为基础建立严密的数学解析方程，物理概念清晰、普适性强，能深刻揭示流动参数间的内在定量规律；\n   - **局限性**：面对高雷诺数湍流、复杂三维几何边界或多相掺气流动时，非线性偏微分方程组难以求得精确解析解，往往需引入理想化假定。\n2. **科学实验法**（含原型观测、水工模型试验及系统机理试验）：\n   - **优势**：直接观测真实水流现象，既能检验理论与数值成果的可靠性，又能结合量纲分析建立半经验公式，解决复杂工程边界水力问题；\n   - **局限性**：受试验场地、经费、周期及测试仪器精度制约，且缩尺模型试验难以同时满足所有相似准则（存在比尺效应）。\n3. **数值计算法**（计算水力学 / CFD）：\n   - **优势**：将控制微分方程离散求解，成本低、周期短、易于改变工况方案，能完整输出流场精细细节且不受模型比尺效应限制；\n   - **局限性**：给出的是离散近似解而非连续解析解，计算精度依赖网格质量、湍流封闭模型及边界条件，仍需物理试验资料率定和验证。",
                "analysis": "现代水力学的发展正是上述三种方法深度融合的过程：\n\n1. **理论分析法**通过建立连续性方程、欧拉方程、纳维—斯托克斯（N-S）方程及恒定总流三大方程，奠定了学科严密的逻辑骨架；但由于 N-S 方程存在强非线性对流惯性项且湍流脉动封闭困难，纯解析方法仅在层流、简单势流或一维总流简化下能获封闭解。\n2. **科学实验法**包含现场原型观测、实验室物理模型试验（遵循弗劳德或雷诺相似准则）及系统试验（如尼古拉兹圆管阻力试验），配合白金汉 $\\Pi$ 定理与量纲分析，提供了谢才—曼宁公式、局部阻力系数等关键工程参数，但耗资耗时且受限于相似律矛盾。\n3. **数值计算法**采用有限差分法（FDM）、有限体积法（FVM）或有限元法（FEM）求解离散控制方程，已成为现代水利工程优化设计的主力工具，但必须与理论分析及物理模型试验相互印证。",
                "analysisFigures": [],
                "pitfalls": "切忌漏掉“数值计算法（CFD）”而只答理论与实验两种方法！现代水力学教材均明确将理论分析、科学试验、数值模拟并列为三大基本研究途径，且每种方法必须按题干要求同时答出“优势”和“局限性”两方面。",
                "chapter": 1,
                "kps": ["水力学研究方法", "水力相似与数值模拟"],
                "method": "理论实验与数值模拟三元对比分析法",
                "difficulty": 1,
                "rubric": [
                    {"label": "完整列出理论分析法、科学实验法、数值计算法三种基本研究方法", "pts": 2},
                    {"label": "准确阐述理论分析法与科学实验法各自的优势和局限性（如非线性求解困难、模型比尺效应）", "pts": 4},
                    {"label": "准确阐述数值计算法的优势和局限性（离散近似解、依赖湍流模型与实验验证）", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2021-02",
                "year": 2021,
                "no": 2,
                "type": "short",
                "score": 8,
                "title": "静止液体压强分布规律的不同表达式及其物理意义",
                "stem": "试写出静止液体压强分布规律的不同表达式，并说明物理意义。",
                "note": "",
                "figures": [],
                "shortAnswer": "（1）压强形式 p = p0 + ρgh：任一点静水压强等于液面表面压强与单位面积上液柱重量之和；（2）水头（能量）形式 z + p/(ρg) = C：同种连通静止液体内各点位置水头与压强水头之和（单位重量液体总势能/测压管水头）处处相等。",
                "judgeAnswer": None,
                "answer": "重力作用下同种、连续、均质不可压缩静止液体的压强分布基本规律有以下常见表达式：\n\n1. **压强深度形式（力学表达式）**：\n\n$$\np = p_0 + \\rho g h = p_0 + \\gamma h\n$$\n\n- **物理意义**（静水力学角度）：静止液体内任意一点的静水压强 $p$，由自由液面（或基准液面）上的表面压强 $p_0$ 与该点以上单位水平截面积、高度为淹没水深 $h$ 的铅直液柱重量 $\\rho g h$ 两部分叠加而成。它同时体现了**帕斯卡定律**（表面压强 $p_0$ 等值向液体内部各点传递）以及静水压强随淹没深度 $h$ 呈线性增大的规律。\n\n2. **水头守恒形式（能量表达式）**：\n\n$$\nz + \\frac{p}{\\rho g} = C \\quad \\left(\\text{或}\\; z_1 + \\frac{p_1}{\\gamma} = z_2 + \\frac{p_2}{\\gamma}\\right)\n$$\n\n- **物理意义**（能量与几何角度）：\n  - **能量意义**：$z$ 为**位置水头**（单位重量液体相对基准面的位置势能），$\\frac{p}{\\rho g}$ 为**压强水头**（单位重量液体所具有的压强势能），二者之和 $z + \\frac{p}{\\rho g}$ 为**测压管水头**，表明同种连通静止液体中各点单位重量液体的总机械能（总势能）处处相等，位置势能与压强势能可相互等量转化；\n  - **几何意义**：静止液体内部任意点测压管液面上升的几何高程恒在同一水平面上（测压管水头线为水平直线），且静止重力液体的等压面（$p = \\text{const}$）必为水平面（$z = \\text{const}$）。",
                "analysis": "**补充说明（单位体积能量形式与一般欧拉静平衡微分式）**\n\n- 将水头形式两边同乘重度 $\\gamma = \\rho g$，可得单位体积能量形式：\n\n$$\n\\rho g z + p = C^{\\prime}\n$$\n\n其物理意义为单位体积静止液体的重力位能 $\\rho g z$ 与压强势能 $p$ 之和保持恒定。\n- 若液体除重力外还受其它质量力（如等加速直线运动或等角速旋转容器），则由欧拉流体静平衡微分方程描述：\n\n$$\n\\mathrm{d}p = \\rho (f_x\\,\\mathrm{d}x + f_y\\,\\mathrm{d}y + f_z\\,\\mathrm{d}z)\n$$\n\n仅受重力时 $f_x = f_y = 0, f_z = -g$，积分即退化为上述静水压强基本方程 $z + \\frac{p}{\\rho g} = C$。",
                "analysisFigures": [],
                "pitfalls": "阐述物理意义时务必区分量纲：在 $p = p_0 + \\rho g h$ 中各项单位为 $\\mathrm{Pa}$（$\\mathrm{N/m^2}$，单位面积受力或单位体积势能）；而在 $z + \\frac{p}{\\rho g} = C$ 中各项单位为 $\\mathrm{m}$（水柱高度，对应**单位重量**液体的势能），切忌将“单位重量”误写为“单位质量”！",
                "chapter": 2,
                "kps": ["静水压强基本方程", "位置水头与压强水头", "帕斯卡定律"],
                "method": "静水基本方程力学与能量双重阐释法",
                "difficulty": 1,
                "rubric": [
                    {"label": "正确写出压强形式 p = p0 + ρgh 并说明表面压强传递与单位面积液柱重量的力学意义", "pts": 4},
                    {"label": "正确写出水头形式 z + p/(ρg) = C 并说明位置水头、压强水头及单位重量总势能处处相等的能量/几何意义", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2021-03",
                "year": 2021,
                "no": 3,
                "type": "short",
                "score": 8,
                "title": "描述液体运动的两种方法（拉格朗日法与欧拉法）及水力学常用方法",
                "stem": "描述液体运动有哪些方法？水力学中常用的是哪种方法？",
                "note": "",
                "figures": [],
                "shortAnswer": "有拉格朗日法（质点系法）和欧拉法（流场法）两种方法；水力学中常用的是欧拉法。",
                "judgeAnswer": None,
                "answer": "流体力学与水力学中描述液体运动的方法主要有**拉格朗日法（Lagrange 法）**和**欧拉法（Euler 法）**两种，**水力学中常用的是欧拉法**。\n\n1. **拉格朗日法（质点跟踪法 / 随体法）**：\n   - 以个别流体质点为研究对象，用质点在初始时刻 $t_0$ 的坐标 $(a,b,c)$ 标记每一个流体质点，跟踪描述每一质点在运动全过程中的空间位置及运动要素随时间 $t$ 的变化规律，即 $\\vec{r} = \\vec{r}(a,b,c,t)$、$\\vec{u} = \\frac{\\partial \\vec{r}}{\\partial t}$。综合所有质点的运动即可获知整个液体系统的运动。\n2. **欧拉法（空间点考察法 / 流场法）**：\n   - 以流体所占据的空间区域（流场）内固定的空间点 $(x,y,z)$ 为观察对象，不追踪单个质点的去向，而是考察不同时刻流经各固定空间点的流体质点运动要素（流速、压强、密度等）的分布与变化规律，即 $\\vec{u} = \\vec{u}(x,y,z,t)$、$p = p(x,y,z,t)$。\n3. **水力学常用欧拉法的原因**：\n   - 流体质点极易变形与混掺，追踪海量单个质点轨迹在数学求解与实验测量上均极为困难；而工程水力学最关心的是固定断面或水工建筑物（闸坝、管道、桥墩）特定空间位置处的流速、水深、流量及动水压力分布，采用欧拉法建立控制体守恒方程与布置定点测流测压仪器最为直观简便。",
                "analysis": "**两种方法的内在数学联系（随体导数 / 全导数）**\n\n拉格朗日法中的质点加速度是同一质点速度对时间的偏导数，转换到欧拉空间变量 $(x,y,z,t)$ 下即为全导数（随体导数 $\\frac{\\mathrm{D}\\vec{u}}{\\mathrm{D}t}$）：\n\n$$\n\\vec{a} = \\frac{\\mathrm{d}\\vec{u}}{\\mathrm{d}t} = \\underbrace{\\frac{\\partial \\vec{u}}{\\partial t}}_{\\text{当地加速度}} + \\underbrace{(\\vec{u}\\cdot\\nabla)\\vec{u}}_{\\text{迁移加速度}}\n$$\n\n- 当地加速度反映流场的**非恒定性**（恒定流时 $\\frac{\\partial \\vec{u}}{\\partial t} = 0$）；\n- 迁移加速度反映流场的**空间非均匀性**（均匀流时 $(\\vec{u}\\cdot\\nabla)\\vec{u} = 0$）。",
                "analysisFigures": [],
                "pitfalls": "切勿将两种方法的自变量混淆：拉格朗日法的自变量是“质点初始标记 $(a,b,c)$ 和时间 $t$”（给出迹线）；欧拉法的自变量是“固定空间坐标 $(x,y,z)$ 和时间 $t$”（给出瞬时速度场与流线）。",
                "chapter": 3,
                "kps": ["拉格朗日法与欧拉法", "欧拉法恒定流定义"],
                "method": "质点跟踪与流场定点观察对比法",
                "difficulty": 1,
                "rubric": [
                    {"label": "准确写出描述液体运动的拉格朗日法和欧拉法，并说明拉格朗日法跟踪流体质点随时间变化的本质", "pts": 3},
                    {"label": "准确说明欧拉法考察固定空间点流场物理量分布与变化的本质", "pts": 3},
                    {"label": "明确回答水力学中常用欧拉法并简述其便于工程定点观测与数学建模的原因", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2021-04",
                "year": 2021,
                "no": 4,
                "type": "short",
                "score": 8,
                "title": "测量水流流速的两种常用方法及其测量原理",
                "stem": "请列举两种测量流速的方法，并简要说明测量原理。",
                "note": "",
                "figures": [],
                "shortAnswer": "（1）毕托管（皮托管）测局部点流速：利用迎流驻点动能完全转化为压能，由总水头管与测压管液柱高差 Δh 得 u = φ√(2gΔh)；（2）文丘里流量计测管道断面平均流速：利用渐缩喉管增速降压效应，结合伯努利方程与连续性方程由两断面测压管水头差 h 求得断面平均流速。",
                "judgeAnswer": None,
                "answer": "列举水力学中经典的两种流速测量方法及其原理如下（见解图 4）：\n\n1. **毕托管（Pitot tube，皮托管）测局部点流速**：\n   - **测量原理**：基于理想流体定常伯努利方程的**驻点滞止增压原理**。将直角细弯管前端迎流小孔对准待测点来流方向，流线在管口前缘形成滞止驻点 $A$（局部流速降为 $0$，动能转化为压强势能），使总压管液面上升至总水头高度 $h_{\\text{总}} = z + \\frac{p}{\\rho g} + \\frac{u^2}{2g}$；同时由侧壁静压孔（或并列测压管）测出同一点的测压管水头 $h_{\\text{静}} = z + \\frac{p}{\\rho g}$。两管液柱高度差 $\\Delta h = h_{\\text{总}} - h_{\\text{静}} = \\frac{u^2}{2g}$，计入仪器修正系数 $\\varphi$（约 $0.98\\sim 1.0$），即得该点流速：\n\n$$\nu = \\varphi \\sqrt{2g\\Delta h}\n$$\n\n2. **文丘里流量计（Venturi meter）测管道断面平均流速**（或旋桨式流速仪）：\n   - **测量原理**：基于**恒定总流伯努利方程与连续性方程**。文丘里管由进口直管断面 $1\\text{—}1$（面积 $A_1$）渐缩至喉管断面 $2\\text{—}2$（面积 $A_2 < A_1$），水流流经喉管时流速增大（$v_2 = \\frac{A_1}{A_2}v_1$）、压强降低，两断面产生测压管水头差 $h = \\left(z_1 + \\frac{p_1}{\\rho g}\\right) - \\left(z_2 + \\frac{p_2}{\\rho g}\\right)$。联立两断面能量方程与连续性方程并引入流量修正系数 $\\mu$（约 $0.95\\sim 0.98$），即可由实测液柱差 $h$ 求出管道断面平均流速：\n\n$$\nv_1 = \\mu \\sqrt{\\frac{2gh}{(A_1 / A_2)^2 - 1}}\n$$",
                "analysis": "**拓展补充：实验室与天然河道其它常用测速方法**\n\n除上述差压式水力测速法外，回答以下任一种现代或水文测速方法同样正确：\n- **旋桨式（转子式）流速仪**：利用水流动能冲击螺旋桨叶使其绕轴旋转，单位时间内旋桨转数 $n$ 与来流局部时均流速 $u$ 呈良好的线性关系 $u = a + b n$（$a,b$ 为检定常数），广泛用于明渠与天然河道测流；\n- **激光多普勒流速仪（LDV）/ 超声波多普勒流速仪（ADV）**：利用随流示踪微粒散射光波或声波产生的多普勒频移 $\\Delta f$ 与流体质点瞬时速度成正比的原理，实现非接触式（或高精度三维脉动）瞬时点流速测量。",
                "analysisFigures": [
                    {"src": "figures/q04_sol.png", "caption": "解图 4　（a）毕托管测局部点流速与（b）文丘里流量计测断面平均流速原理图"}
                ],
                "pitfalls": "回答毕托管原理时切忌说成“两根管测量压强差 $\\Delta p = \\frac{1}{2}\\rho u^2$”而漏掉倾斜管通用表述“测压管水头差 $\\Delta h$”；同时注意区分毕托管测的是**局部点流速 $u$**，而文丘里管测的是**过水断面平均流速 $v$**。",
                "chapter": 3,
                "kps": ["毕托管测速原理", "伯努利方程测流", "文丘里流量计"],
                "method": "动静水头转换与截面收缩差压测速法",
                "difficulty": 2,
                "rubric": [
                    {"label": "列举第一种测速方法（如毕托管）并准确阐明驻点总水头与静压水头之差求点流速的原理公式", "pts": 4},
                    {"label": "列举第二种测速方法（如文丘里管或旋桨流速仪/LDV）并准确说明其物理原理与计算关系", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2021-05",
                "year": 2021,
                "no": 5,
                "type": "short",
                "score": 8,
                "title": "曼宁公式等号两边的量纲和谐性分析与物理量单位限制要求",
                "stem": "试分析曼宁（Manning）公式等号两边各项量纲是否相同？应用曼宁公式计算时，对公式中物理量的单位有何限制要求？",
                "note": "",
                "figures": [],
                "shortAnswer": "若将糙率 n 视为无量纲纯数，曼宁公式等号两边量纲不相同（左边谢才系数为 L^(1/2)·T^(-1) 或流速为 L·T^(-1)，右边为 L^(1/6) 或 L^(2/3)，属经验公式，n 隐含量纲 T·L^(-1/3)）。直接查表取用常规糙率 n 计算时，长度必须用米（m），时间必须用秒（s）。",
                "judgeAnswer": None,
                "answer": "**（1）曼宁公式等号两边量纲分析**\n\n曼宁公式计算谢才系数 $C$ 及明渠/管流断面平均流速 $v$ 的标准形式为：\n\n$$\nC = \\frac{1}{n} R^{1/6}, \\qquad v = C\\sqrt{RJ} = \\frac{1}{n} R^{2/3} J^{1/2}\n$$\n\n工程实用中通常把壁面粗糙系数（糙率）$n$ 当作查表所得的无量纲纯数（不标单位），在此约定下**等号两边各项的量纲不相同**（属量纲不和谐经验公式）：\n- 水力坡度 $J$ 为无量纲量（$[J] = 1$）；\n- 谢才系数公式左边量纲为 $[C] = \\frac{[v]}{[R]^{1/2}} = \\mathrm{L^{1/2} T^{-1}}$，而右边若视 $[n]=1$ 则 $[R^{1/6}] = \\mathrm{L^{1/6}}$（同理流速公式左边 $[v] = \\mathrm{L T^{-1}}$，右边 $[R^{2/3} J^{1/2}] = \\mathrm{L^{2/3}}$），左右量纲不一致。\n- （注：若要使公式在理论上满足量纲齐次性，则必须认为粗糙系数 $n$ 本身并非无量纲量，而是隐含了 $[n] = \\mathrm{T L^{-1/3}}$、即 $\\mathrm{s/m^{1/3}}$ 的量纲，公式省去了包含重力加速度 $g^{1/2}$ 的转换因子。）\n\n**（2）应用曼宁公式计算时的单位限制要求**\n\n正因为工程水力学手册中的糙率 $n$ 数值是在**国际单位制（公制 SI：米—秒制）**下由实测资料率定出来的经验系数，直接代入常规表列 $n$ 值计算时，公式中各物理量的单位有严格限制：\n- **长度量**（水力半径 $R$、水深 $h$、湿周 $\\chi$ 等）**必须统一采用米（$\\mathrm{m}$）**，过水断面积 $A$ 必须采用平方米（$\\mathrm{m^2}$）；\n- **时间量**必须采用**秒（$\\mathrm{s}$）**；\n- 在此单位下算得的谢才系数 $C$ 单位为 $\\mathrm{m^{1/2}/s}$，流速 $v$ 单位为 $\\mathrm{m/s}$，流量 $Q$ 单位为 $\\mathrm{m^3/s}$（若改用厘米、毫米或英尺等其它单位，不能直接套用原式，例如英制 ft-s 下必须在分子乘以换算常数 $1.486$）。",
                "analysis": "**深入辨析谢才系数 $C$ 与达西阻力系数 $\\lambda$ 的量纲关系**\n\n对比达西—韦斯巴赫公式 $h_f = \\lambda \\frac{l}{4R}\\frac{v^2}{2g}$ 与谢才公式 $v = C\\sqrt{RJ}$ 可得：\n\n$$\nC = \\sqrt{\\frac{8g}{\\lambda}}\n$$\n\n由于沿程阻力系数 $\\lambda$ 是严格无量纲数，故谢才系数 $C$ 的量纲与 $\\sqrt{g}$ 完全相同，即 $[C] = [g]^{1/2} = \\mathrm{L^{1/2} T^{-1}}$。曼宁公式 $C = \\frac{1}{n}R^{1/6}$ 未显式写出 $\\sqrt{g}$，而是将 $g^{-1/2}$ 的量纲吸收进经验糙率 $n$ 中（使 $[n] = \\mathrm{L^{-1/3} T}$），这也是应用曼宁公式绝对不能随意混用 $\\mathrm{cm}$ 与 $\\mathrm{m}$ 的根本物理原因。",
                "analysisFigures": [],
                "pitfalls": "切忌误认为谢才系数 $C$ 是无量纲系数！由 $v = C\\sqrt{RJ}$ 立知 $[C] = \\mathrm{L^{1/2}T^{-1}}$（单位 $\\mathrm{m^{1/2}/s}$）。分析量纲时先将 $n$ 按工程惯例视作无量纲系数指出左右量纲不同，再点明 $n$ 实质隐含 $\\mathrm{T L^{-1/3}}$ 量纲，答题最为全面严密。",
                "chapter": 7,
                "kps": ["曼宁公式", "谢才公式", "量纲齐次性与单位制"],
                "method": "基本量纲分解与经验系数单位制核查法",
                "difficulty": 2,
                "rubric": [
                    {"label": "写出曼宁公式并导出两边量纲（左边 [C]=L^(1/2)T^(-1) 或 [v]=LT^(-1)，指出视 n 无量纲时两边量纲不同，n 隐含 TL^(-1/3)）", "pts": 4},
                    {"label": "明确说明应用曼宁公式查表取 n 计算时，水力半径 R、断面积 A 等长度量必须用米（m），时间必须用秒（s）", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2021-06",
                "year": 2021,
                "no": 6,
                "type": "short",
                "score": 8,
                "title": "实际液体层流与湍流（紊流）两类流态的核心区别",
                "stem": "简述层流和湍流有何不同？",
                "note": "",
                "figures": [],
                "shortAnswer": "两者在质点运动特征（分层有序无混掺 vs 随机脉动旋涡混掺）、速度压强脉动性、切应力构成（纯分子黏性切应力 vs 附加雷诺脉动切应力）、断面流速分布均匀度（旋转抛物面 vs 对数/指数扁平分布）、沿程水头损失与流速幂次关系（一次方 vs 1.75～2 次方）及发生雷诺数范围（Re < Rec vs Re > Rec）六方面存在本质不同。",
                "judgeAnswer": None,
                "answer": "层流（Laminar flow）和湍流（Turbulent flow，又称紊流）是实际黏性液体运动的两种本质不同的流态，主要区别如下：\n\n1. **流体质点运动形态与混掺特征不同**：\n   - **层流**：流体质点沿与管轴平行的方向作分层、有条不紊的平滑直线（或平顺流线）运动，相邻流层间仅发生相对滑动而无宏观质点横向混掺；\n   - **湍流**：流体质点除沿主流方向运动外，还伴随剧烈、无规则的三维横向随机脉动，流层间充满大小不等的旋涡并不断发生剧烈质量与动量混掺。\n2. **运动要素的时变脉动特性不同**：\n   - **层流**：在恒定边界条件下，空间任一点的流速和压强均恒定不变，无随机脉动；\n   - **湍流**：即使在恒定总流条件下（定常时均流），任一点的瞬时流速 $u = \\overline{u} + u^{\\prime}$ 和瞬时压强 $p = \\overline{p} + p^{\\prime}$ 均围绕时均值作高频随机脉动。\n3. **内部切应力（动量传递机制）不同**：\n   - **层流**：流层间仅存在由分子热运动动量交换引起的牛顿黏性切应力 $\\tau = \\mu \\frac{\\mathrm{d}u}{\\mathrm{d}y}$；\n   - **湍流**：除分子黏性切应力外，还存在由宏观流体微团横向脉动混掺产生的**附加切应力（雷诺应力）** $\\tau_t = -\\rho \\overline{u_x^{\\prime} u_y^{\\prime}}$，除贴壁黏性底层外 $\\tau_t$ 远大于分子黏性切应力。\n4. **过水断面流速分布形状不同**：\n   - **层流**：流速梯度变化缓和但分布不均，圆管层流呈旋转抛物面分布（管心最大流速 $u_{\\max} = 2v$）；\n   - **湍流**：强烈的横向动量交换削平了中心区流速差，使断面时均流速分布比层流**更加均匀扁平**（呈对数律或指数律分布，$u_{\\max} \\approx 1.2v$，近壁处流速梯度则急剧增大）。\n5. **沿程水头损失规律及存在条件不同**：\n   - **层流**：发生于小雷诺数区（圆管 $Re = \\frac{vd}{\\nu} < 2000$），沿程阻力系数 $\\lambda = \\frac{64}{Re}$ 与壁面粗糙度无关，沿程水头损失 $h_f$ 与平均流速 $v$ 的 **$1$ 次方**成正比；\n   - **湍流**：发生于较大雷诺数区（圆管 $Re > 2000$，工程常见绝大多数流动），$\\lambda = f(Re, \\Delta/d)$，沿程水头损失 $h_f$ 与平均流速 $v$ 的 **$1.75 \\sim 2$ 次方**成正比（阻力平方区与 $Re$ 无关、仅取决于相对粗糙度 $\\Delta/d$）。",
                "analysis": "**核心记忆脉络：从“微观无混掺 vs 宏观旋涡混掺”推导一切宏观差异**\n\n掌握层流与湍流的区别无需死记硬背，只需抓住**横向脉动混掺**这一物理根源：\n- 有了横向微团混掺 $\\implies$ 产生巨大的雷诺脉动切应力 $\\tau_t = -\\rho\\overline{u_x^{\\prime}u_y^{\\prime}}$ $\\implies$ 快慢流层间动量剧烈均化 $\\implies$ 核心区时均流速分布变扁平、近壁速度梯度激增 $\\implies$ 壁面摩阻及机械能涡流耗散大幅上升，使沿程水头损失从正比于 $v^1$ 跃升至正比于 $v^{1.75\\sim 2}$。",
                "analysisFigures": [],
                "pitfalls": "对比时切勿只写“层流整齐、湍流混乱”一句定性描述（8 分简答题至少需展开 4 个以上物理维度：质点轨迹与混掺、附加切应力机制、断面流速分布形状、沿程水头损失与流速次方关系、临界雷诺数判据）。",
                "chapter": 4,
                "kps": ["层流与紊流特征对比", "雷诺应力", "沿程水头损失规律", "下临界雷诺数"],
                "method": "流态微观混掺与宏观阻力多维对比法",
                "difficulty": 2,
                "rubric": [
                    {"label": "阐述质点运动轨迹与混掺特性差异（分层滑动无混掺 vs 随机脉动旋涡混掺）及时均脉动特性", "pts": 3},
                    {"label": "指出切应力机制（纯黏性切应力 vs 附加雷诺切应力）与圆管断面流速分布差异（抛物面 vs 均匀扁平）", "pts": 3},
                    {"label": "说明沿程水头损失规律（hf ∝ v vs hf ∝ v^(1.75~2)）及雷诺数判别条件（Re < 2000 vs Re > 2000）", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2021-07",
                "year": 2021,
                "no": 7,
                "type": "short",
                "score": 8,
                "title": "简单管道自由出流与淹没出流的流量及各相应点压强对比分析",
                "stem": "如图所示，两简单管道布置方式一样，出流形式不同，a 图为自由出流，b 图为淹没出流。若两管道的作用水头 $H$ 和 $z$，管长 $l$，管径 $d$ 及沿程阻力系数 $\\lambda$ 均相同，试问：\n\n（1）两管中通过的流量是否相同？为什么？\n\n（2）两管中各相应点的压强是否相同？为什么？",
                "note": "",
                "figures": [
                    {"src": "figures/q07_orig.png", "caption": "题 7 图　简单管道（a）自由出流与（b）淹没出流对比"}
                ],
                "shortAnswer": "（1）两管中通过的流量相同，因作用水头 H=z 相同，且自由出流的出口流速水头 αv²/(2g)≈v²/(2g) 恰好等于淹没出流进入下游水池的突然扩大局部水头损失 ζ出v²/(2g)=1.0×v²/(2g)，系统总阻抗相等；（2）两管中各相应点的压强不相同，b 管（淹没出流）各相应点压强均比 a 管大 ρghs（hs 为 b 管出口在下游水面下的淹没水深）。",
                "judgeAnswer": None,
                "answer": "**（1）两管中通过的流量相同（$Q_a = Q_b$）**。\n\n- **原因**：设两简单管道进口及弯折处的局部阻力系数之和为 $\\sum\\zeta$（因管道布置完全相同，$\\sum\\zeta$、$l$、$d$、$\\lambda$ 均相等），取动能修正系数 $\\alpha = 1.0$：\n  - 对（a）图**自由出流**，取上游水面与管道出口断面中心列能量方程：\n\n$$\nH = \\left(\\alpha + \\lambda\\frac{l}{d} + \\sum\\zeta\\right)\\frac{v_a^2}{2g} = \\left(1 + \\lambda\\frac{l}{d} + \\sum\\zeta\\right)\\frac{v_a^2}{2g}\n$$\n\n  - 对（b）图**淹没出流**，取上游水面与下游水池自由水面（流速趋于 $0$）列能量方程，计入有压管排入大水池的出口突然扩大局部水头损失系数 $\\zeta_{\\text{出}} = 1.0$：\n\n$$\nz = \\left(\\zeta_{\\text{出}} + \\lambda\\frac{l}{d} + \\sum\\zeta\\right)\\frac{v_b^2}{2g} = \\left(1 + \\lambda\\frac{l}{d} + \\sum\\zeta\\right)\\frac{v_b^2}{2g}\n$$\n\n  由于作用水头 $H = z$ 且两管系统总阻力系数完全相等，故管内平均流速 $v_a = v_b$，通过的流量 $Q_a = A v_a = A v_b = Q_b$ **完全相同**。\n\n**（2）两管中各相应点的压强不相同（淹没出流 b 管各点压强大于自由出流 a 管）**。\n\n- **原因**：设管道任一相应点 $K$ 高出管道出口断面中心的铅直高度为 $\\Delta z_K$，且 b 图管道出口中心淹没在下游水面以下的深度为 $h_s > 0$（见解图 7）。由 $K$ 断面至出口（或下游水面）列能量方程：\n  - 在（a）图中，出口通大气（相对压强为 $0$），测压管水头线终点落在**管道出口中心**，故 $K$ 点压强水头为 $\\frac{p_{K,a}}{\\rho g} = h_{w,K\\text{-出}} - \\Delta z_K$；\n  - 在（b）图中，出口淹没于下游水深 $h_s$ 处，测压管水头线终点落在高出出口 $h_s$ 的**下游水池自由液面**上，因 $Q_a = Q_b$，两管对应管段水头损失 $h_{w,K\\text{-出}}$ 相等，故 $K$ 点压强水头为：\n\n$$\n\\frac{p_{K,b}}{\\rho g} = h_s + h_{w,K\\text{-出}} - \\Delta z_K = \\frac{p_{K,a}}{\\rho g} + h_s > \\frac{p_{K,a}}{\\rho g}\n$$\n\n  即 b 管各相应点的动水压强均比 a 管高出下游淹没水深对应的静水压强 $\\rho g h_s$。",
                "analysis": "**从测压管水头线（H.G.L.）几何平移直观理解本题（见解图 7）**\n\n1. **流量等价性的物理本质**：自由出流时，单位重量水体携带 $\\frac{v^2}{2g}$ 的出口动能直接排入大气；淹没出流时，高速水股射入静止大水池，这部分 $\\frac{v^2}{2g}$ 的动能在下游水池旋涡混掺中全部耗散为出口局部损失 $h_{j,\\text{出}} = 1.0\\frac{v^2}{2g}$。只要有效总水头（a 图为上游水面至出口中心高差 $H$，b 图为上下游水面高差 $z$）相等，驱动管内水流的净能量完全一致，故 $Q_a = Q_b$。\n2. **压强差异的几何本质**：两管布置与流量均相同，意味着两管的**水力坡度与水头损失分布完全全等**；但 b 图为了在出口淹没深度为 $h_s$ 的前提下仍维持上下游水位差 $z = H$，其上下游液面相对于管道本身的几何高程整体抬高了 $h_s$，导致整条测压管水头线相对于管轴线平行上移了 $h_s$，故管内每一点压强均增大 $\\Delta p = \\rho g h_s$。",
                "analysisFigures": [
                    {"src": "figures/q07_sol.png", "caption": "解图 7　自由出流与淹没出流的总水头线（E.G.L.）及测压管水头线（H.G.L.）对比"}
                ],
                "pitfalls": "第（2）问极易因为看到“流量相同、水头损失相同”而误判“各点压强也相同”！切记动水压强取决于**测压管水头线与管道轴线之间的铅垂距离**：b 图测压管水头线终点锚定在下游水池水面而非管道出口中心，整体抬升了淹没深度 $h_s$。",
                "chapter": 6,
                "kps": ["简单管道自由出流与淹没出流", "测压管水头线与动水压强", "出口突然扩大局部损失"],
                "method": "短管出流能量方程与测压管水头线对比法",
                "difficulty": 3,
                "rubric": [
                    {"label": "分别列出自由出流（含出口动能 αv²/2g）与淹没出流（含出口局部损失 ζ出=1）流量公式，得出两管流量相同", "pts": 4},
                    {"label": "结合能量方程或测压管水头线终点位置差异，明确指出两管相应点压强不同（b 管比 a 管大 ρghs）并说明原因", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2021-08",
                "year": 2021,
                "no": 8,
                "type": "calc",
                "score": 15,
                "title": "活塞油缸环状窄缝牛顿内摩擦与润滑油运动黏度计算",
                "stem": "一活塞油缸如图所示。已知油缸内径 $D = 14\\,\\mathrm{cm}$，活塞直径 $d = 13.4\\,\\mathrm{cm}$，活塞长度 $s = 16\\,\\mathrm{cm}$，当拉动活塞的力 $F = 7.5\\,\\mathrm{N}$ 时，活塞的移动速度 $u = 0.5\\,\\mathrm{m/s}$，若油缸内润滑油的密度为 $860\\,\\mathrm{kg/m^3}$，试求润滑油的运动粘度系数 $\\nu$ 的大小。",
                "note": "",
                "figures": [
                    {"src": "figures/q08_orig.png", "caption": "题 8 图　活塞油缸环状间隙运动示意图"}
                ],
                "shortAnswer": "7.77×10⁻⁴ m²/s（或 7.77 cm²/s；若中间面积近似取 0.067 m² 则约为 7.79×10⁻⁴ m²/s）",
                "judgeAnswer": None,
                "answer": "润滑油的运动黏度系数 $\\nu \\approx 7.77 \\times 10^{-4}\\,\\mathrm{m^2/s}$（即 $7.77\\,\\mathrm{cm^2/s}$）。",
                "analysis": "**1. 计算活塞与油缸内壁间的单侧径向间隙厚度 $\\delta$ 及受剪侧面积 $A$**\n\n将各几何尺寸统一换算为国际单位（$\\mathrm{m}$）：$D = 0.14\\,\\mathrm{m}$，$d = 0.134\\,\\mathrm{m}$，$s = 0.16\\,\\mathrm{m}$。\n\n同心放置时，单侧环形油膜间隙厚度为：\n\n$$\n\\delta = \\frac{D - d}{2} = \\frac{0.14 - 0.134}{2} = 0.003\\,\\mathrm{m} = 3\\,\\mathrm{mm}\n$$\n\n活塞圆柱外表面与润滑油接触的受剪侧面积为：\n\n$$\nA = \\pi d s = \\pi \\times 0.134 \\times 0.16 = 0.02144\\pi \\approx 0.067356\\,\\mathrm{m^2}\n$$\n\n**2. 应用牛顿内摩擦定律求润滑油动力黏度 $\\mu$**\n\n因径向间隙极薄（$\\delta \\ll d$），间隙内油膜流速沿径向可视为线性分布：紧贴静止缸壁处流速为 $0$，紧贴活塞表面处流速为 $u = 0.5\\,\\mathrm{m/s}$，故法向速度梯度为 $\\frac{\\mathrm{d}u}{\\mathrm{d}y} \\approx \\frac{u}{\\delta}$。活塞匀速移动时，拉力 $F$ 与侧表面总黏性内摩擦力相平衡：\n\n$$\nF = \\tau A = \\mu A \\frac{u}{\\delta}\n$$\n\n解得润滑油动力黏度 $\\mu$：\n\n$$\n\\mu = \\frac{F \\delta}{A u} = \\frac{7.5 \\times 0.003}{0.067356 \\times 0.5} = \\frac{0.0225}{0.033678} \\approx 0.6681\\,\\mathrm{Pa\\cdot s}\n$$\n\n**3. 由运动黏度定义求 $\\nu$**\n\n已知润滑油密度 $\\rho = 860\\,\\mathrm{kg/m^3}$，故运动黏度系数为：\n\n$$\n\\nu = \\frac{\\mu}{\\rho} = \\frac{0.66809}{860} \\approx 7.7685 \\times 10^{-4}\\,\\mathrm{m^2/s} \\approx 7.77 \\times 10^{-4}\\,\\mathrm{m^2/s}\n$$\n\n（注：若中间步骤取 $\\pi \\approx 3.14$、$A \\approx 0.067\\,\\mathrm{m^2}$、$\\mu \\approx 0.67\\,\\mathrm{Pa\\cdot s}$，则算得 $\\nu \\approx 7.79 \\times 10^{-4}\\,\\mathrm{m^2/s}$，工程上均一致。）",
                "analysisFigures": [],
                "pitfalls": "1. 单侧径向油膜厚度 $\\delta = \\frac{D - d}{2} = 0.003\\,\\mathrm{m}$，切忌漏除以 $2$ 而直接代直径差 $D - d = 0.006\\,\\mathrm{m}$！\n2. 题干最后求的是**运动黏度 $\\nu$**（单位 $\\mathrm{m^2/s}$）而非动力黏度 $\\mu$（单位 $\\mathrm{Pa\\cdot s}$），求出 $\\mu$ 后切勿忘记除以油的密度 $\\rho = 860\\,\\mathrm{kg/m^3}$。",
                "chapter": 1,
                "kps": ["牛顿内摩擦定律", "动力黏度与运动黏度", "薄壁环缝线性速度分布"],
                "method": "薄壁间隙线性速度分布牛顿内摩擦法",
                "difficulty": 2,
                "rubric": [
                    {"label": "正确求出单侧油膜间隙厚度 δ = (D - d)/2 = 0.003 m 及活塞侧面积 A = πds ≈ 0.0674 m²", "pts": 4},
                    {"label": "应用牛顿内摩擦定律 F = μA(u/δ) 求出润滑油动力黏度 μ ≈ 0.668 Pa·s", "pts": 6},
                    {"label": "由运动黏度与动力黏度换算关系 ν = μ/ρ 求得 ν ≈ 7.77×10⁻⁴ m²/s", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2021-09",
                "year": 2021,
                "no": 9,
                "type": "calc",
                "score": 17,
                "title": "充满压力水的密封水箱对 1/4 圆弧二元曲面的静水总压力计算",
                "stem": "如图是一充满压力水的密封水箱，垂直图面方向的宽度 $b = 3\\,\\mathrm{m}$，高度 $h = 4.5\\,\\mathrm{m}$，其右侧下半部 $BC$ 段为半径 $r = 3\\,\\mathrm{m}$ 的 $1/4$ 圆弧。水箱顶部的压强由压力表指示为 $p_g = 1.962 \\times 10^4\\,\\mathrm{Pa}$。水的密度为 $\\rho = 1000\\,\\mathrm{kg/m^3}$。试求水对二元曲面 $BC$ 的压力的大小和方向。",
                "note": "",
                "figures": [
                    {"src": "figures/q09_orig.png", "caption": "题 9 图　充满压力水的密封水箱及 1/4 圆弧曲面 BC"}
                ],
                "shortAnswer": "总压力大小 P = 679.86 kN（水平分力 Px = 441.45 kN 向右，铅垂分力 Pz = 517.04 kN 向下），方向指向右下方、与水平面夹角 α = 49.5°，作用线通过 BC 圆弧圆心。",
                "judgeAnswer": None,
                "answer": "水对二元曲面 $BC$ 的静水总压力大小为 **$P = 679.86\\,\\mathrm{kN}$**（其中水平分力 $P_x = 441.45\\,\\mathrm{kN}$ 水平向右，铅垂分力 $P_z = 517.04\\,\\mathrm{kN}$ 铅直向下）；总压力方向**指向右下方，与水平面成 $\\alpha = 49.5^{\\circ}$ 角，且作用线通过 $BC$ 圆弧的圆心**。",
                "analysis": "**1. 将水箱顶部表压换算为等效自由液面高度 $h_1$**\n\n取重力加速度 $g = 9.81\\,\\mathrm{m/s^2}$，水箱顶盖处的压力表读数 $p_g = 1.962 \\times 10^4\\,\\mathrm{Pa}$ 折算为水柱高度：\n\n$$\nh_1 = \\frac{p_g}{\\rho g} = \\frac{1.962 \\times 10^4}{1000 \\times 9.81} = 2.00\\,\\mathrm{m}\n$$\n\n即可将密封有压水箱等效为自由液面 $1\\text{—}2$ 位于水箱顶盖上方 $h_1 = 2.00\\,\\mathrm{m}$ 处的敞口静水容器（见解图 9）：\n- 圆弧上端点 $B$ 在等效自由液面下的淹没深度：$h_B = h_1 + (h - r) = 2.00 + (4.5 - 3.0) = 3.50\\,\\mathrm{m}$；\n- 圆弧底端点 $C$ 在等效自由液面下的淹没深度：$h_C = h_1 + h = 2.00 + 4.5 = 6.50\\,\\mathrm{m}$。\n\n**2. 计算静水总压力的水平分力 $P_x$**\n\n曲面 $BC$ 在铅直平面上的投影面为高 $r = 3\\,\\mathrm{m}$、宽 $b = 3\\,\\mathrm{m}$ 的矩形，面积 $A_x = r b = 3 \\times 3 = 9.0\\,\\mathrm{m^2}$，投影矩形形心淹没水深为：\n\n$$\nh_c = \\frac{h_B + h_C}{2} = \\frac{3.50 + 6.50}{2} = 5.00\\,\\mathrm{m}\n$$\n\n水平分力大小（方向**水平向右**）：\n\n$$\nP_x = \\rho g h_c A_x = 1000 \\times 9.81 \\times 5.00 \\times 9.0 = 441450\\,\\mathrm{N} = 441.45\\,\\mathrm{kN}\n$$\n\n**3. 计算静水总压力的铅垂分力 $P_z$**\n\n水体位于曲面 $BC$ 上方（实压力体），压力体由曲面 $BC$、过 $B$ 和 $C$ 的两条铅垂线及上方等效自由液面 $1\\text{—}2$ 围成，其横断面由宽 $r = 3\\,\\mathrm{m}$、高 $h_B = 3.50\\,\\mathrm{m}$ 的上部矩形与下部半径 $r = 3\\,\\mathrm{m}$ 的 $1/4$ 圆面组成：\n\n$$\nV = \\left(r \\cdot h_B + \\frac{1}{4}\\pi r^2\\right) b = \\left(3 \\times 3.50 + \\frac{1}{4}\\pi \\times 3^2\\right) \\times 3 = (10.50 + 7.06858) \\times 3 \\approx 52.7058\\,\\mathrm{m^3}\n$$\n\n铅垂分力大小（实压力体，方向**铅直向下**）：\n\n$$\nP_z = \\rho g V = 1000 \\times 9.81 \\times 52.7058 = 517043.4\\,\\mathrm{N} \\approx 517.04\\,\\mathrm{kN}\n$$\n\n**4. 合成求总压力 $P$ 的大小、方向与作用线**\n\n$$\nP = \\sqrt{P_x^2 + P_z^2} = \\sqrt{441.45^2 + 517.043^2} \\approx 679.86\\,\\mathrm{kN}\n$$\n\n设合力 $P$ 与水平方向的夹角为 $\\alpha$：\n\n$$\n\\tan\\alpha = \\frac{P_z}{P_x} = \\frac{517.043}{441.45} \\approx 1.17124 \\implies \\alpha = \\arctan(1.17124) \\approx 49.51^{\\circ} \\approx 49.5^{\\circ}\n$$\n\n因圆柱曲面上各微元静水压力均沿法向背离水体指向圆弧外侧（作用线均汇交于圆弧圆心 $O$），故合力 $P$ 的作用线必**通过圆弧 $BC$ 的圆心 $O$，指向右下方（与水平面夹角 $49.5^{\\circ}$）**。\n\n（注：若取 $\\pi \\approx 3.14$ 则 $V = 52.695\\,\\mathrm{m^3}$，$P_z = 516.94\\,\\mathrm{kN}$，$P = 679.78\\,\\mathrm{kN}$；若取 $g = 9.80\\,\\mathrm{m/s^2}$ 则 $h_1 \\approx 2.002\\,\\mathrm{m}$，$P \\approx 679.42\\,\\mathrm{kN}$，$\\alpha = 49.5^{\\circ}$。）",
                "analysisFigures": [
                    {"src": "figures/q09_sol.png", "caption": "解图 9　1/4 圆弧曲面 BC 的等效自由液面、铅直投影压强图与实压力体合成"}
                ],
                "pitfalls": "1. 计算压力体体积 $V$ 时，压力体必须一直向上延伸至**等效自由液面 $1\\text{—}2$**（即矩形高为 $h_B = 2.0 + 1.5 = 3.5\\,\\mathrm{m}$），切忌只算到水箱顶盖（漏掉 $2.0\\,\\mathrm{m}$ 表压等效水头）！\n2. 回答二元圆柱曲面静水总压力“方向”时，除了给出倾角 $\\alpha = 49.5^{\\circ}$（指向右下），务必写明“**作用线通过圆弧圆心**”才能拿满步骤分。",
                "chapter": 2,
                "kps": ["平面与曲面静水总压力", "等效自由液面", "压力体体积计算"],
                "method": "等效自由液面+水平投影与铅垂压力体合成法",
                "difficulty": 3,
                "rubric": [
                    {"label": "求出水箱顶部表压对应的等效自由液面高度 h1 = pg/(ρg) = 2.0 m 及 B、C 点淹没水深", "pts": 3},
                    {"label": "求出铅直投影矩形形心水深 hc = 5.0 m 及水平分力 Px = ρghcAx = 441.45 kN（向右）", "pts": 5},
                    {"label": "正确计算实压力体体积 V ≈ 52.71 m³ 及铅垂分力 Pz = ρgV ≈ 517.04 kN（向下）", "pts": 5},
                    {"label": "合成求得总压力 P ≈ 679.86 kN、水平倾角 α ≈ 49.5°（指向右下）并指明作用线过圆心", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2021-10",
                "year": 2021,
                "no": 10,
                "type": "calc",
                "score": 15,
                "title": "压力喷水装置活塞推力计算（伯努利方程与连续性方程联立）",
                "stem": "有一压力喷水装置如图所示。已知活塞筒直径 $D = 20\\,\\mathrm{cm}$，喷水管直径 $d = 5\\,\\mathrm{cm}$，活塞筒中心至喷水管出口的高差 $H = 5\\,\\mathrm{m}$。当喷水高度 $h = 20\\,\\mathrm{m}$ 时，不计水头损失，求作用于活塞上的力 $P$。",
                "note": "",
                "figures": [
                    {"src": "figures/q10_orig.png", "caption": "题 10 图　活塞压力喷水装置示意图"}
                ],
                "shortAnswer": "4.60 kN（或 4599 N；若取 g=9.80 m/s² 则为 4.59 kN）",
                "judgeAnswer": None,
                "answer": "作用于活塞上的推力 $P \\approx 4.60\\,\\mathrm{kN}$（或 $4599\\,\\mathrm{N}$）。",
                "analysis": "**1. 由自由射流喷水高度求喷水管出口流速 $v_2$ 与活塞筒流速 $v_1$**\n\n以喷水管出口断面 $2\\text{—}2$ 所在水平面为基准面（$z_2 = 0$），取铅直自由射流最高点断面 $0\\text{—}0$（$z_0 = h = 20\\,\\mathrm{m}$，相对压强 $p_0 = 0$，顶端流速 $v_0 = 0$）。不计一切水头损失与空气阻力，对出口断面 $2\\text{—}2$（$p_2 = 0$）与最高点 $0\\text{—}0$ 列理想流体伯努利方程（取 $\\alpha = 1.0$，$g = 9.81\\,\\mathrm{m/s^2}$）：\n\n$$\n0 + 0 + \\frac{v_2^2}{2g} = h + 0 + 0 \\implies \\frac{v_2^2}{2g} = h = 20\\,\\mathrm{m}, \\quad v_2 = \\sqrt{2gh} = \\sqrt{2 \\times 9.81 \\times 20} \\approx 19.81\\,\\mathrm{m/s}\n$$\n\n由活塞筒断面 $1\\text{—}1$（$D = 0.20\\,\\mathrm{m}$）与喷嘴出口断面 $2\\text{—}2$（$d = 0.05\\,\\mathrm{m}$）之间的连续性方程 $v_1 A_1 = v_2 A_2$：\n\n$$\nv_1 = \\left(\\frac{d}{D}\\right)^2 v_2 = \\left(\\frac{5}{20}\\right)^2 v_2 = \\frac{1}{16} v_2 \\approx 1.238\\,\\mathrm{m/s}\n$$\n\n对应活塞筒内流速水头为：\n\n$$\n\\frac{v_1^2}{2g} = \\left(\\frac{1}{16}\\right)^2 \\frac{v_2^2}{2g} = \\frac{20}{256} = 0.078125\\,\\mathrm{m}\n$$\n\n**2. 列活塞筒断面至出口断面伯努利方程求筒内相对压强 $p_1$**\n\n由题 10 图知活塞筒轴线位于喷水管出口上方 $z_1 = H = 5\\,\\mathrm{m}$ 处，对断面 $1\\text{—}1$ 与断面 $2\\text{—}2$ 列伯努利方程：\n\n$$\nH + \\frac{p_1}{\\rho g} + \\frac{v_1^2}{2g} = 0 + 0 + \\frac{v_2^2}{2g}\n$$\n\n代入 $\\frac{v_2^2}{2g} = h = 20\\,\\mathrm{m}$ 解得活塞筒内水的相对压强 $p_1$：\n\n$$\n\\frac{p_1}{\\rho g} = h - H - \\frac{v_1^2}{2g} = 20 - 5 - 0.078125 = 14.921875\\,\\mathrm{m}\n$$\n\n$$\np_1 = \\rho g \\times 14.921875 = 1000 \\times 9.81 \\times 14.921875 \\approx 146383.6\\,\\mathrm{Pa} \\approx 146.38\\,\\mathrm{kPa}\n$$\n\n**3. 求作用于活塞上的推力 $P$**\n\n活塞右侧受水体表压 $p_1$，左侧通大气（相对压强为 $0$），活塞横截面积 $A_1 = \\frac{\\pi}{4}D^2 = \\frac{\\pi}{4} \\times 0.20^2 = 0.01\\pi \\approx 0.031416\\,\\mathrm{m^2}$，故所需水平推力为：\n\n$$\nP = p_1 A_1 = 146383.6 \\times 0.01\\pi \\approx 4598.8\\,\\mathrm{N} \\approx 4.60\\,\\mathrm{kN}\n$$\n\n（注：若取 $g = 9.80\\,\\mathrm{m/s^2}$，则 $p_1 \\approx 146.23\\,\\mathrm{kPa}$，$P \\approx 4594.1\\,\\mathrm{N} \\approx 4.59\\,\\mathrm{kN}$。）",
                "analysisFigures": [],
                "pitfalls": "1. 认准题 10 图几何高程关系：活塞筒中心比喷嘴出口**高** $H = 5\\,\\mathrm{m}$（$z_1 = +5\\,\\mathrm{m}$），这部分重力位能帮助射流喷高，因此活塞所需提供的压强水头近似为 $h - H = 15\\,\\mathrm{m}$，切勿把符号写反变成 $h + H = 25\\,\\mathrm{m}$！\n2. 活塞筒流速水头 $\\frac{v_1^2}{2g} \\approx 0.078\\,\\mathrm{m}$ 虽小但切勿在方程中无故漏写，应由连续性方程严谨保留。",
                "chapter": 3,
                "kps": ["恒定总流能量方程", "恒定总流连续性方程", "自由射流高度"],
                "method": "多断面伯努利方程与连续性方程联立求解法",
                "difficulty": 2,
                "rubric": [
                    {"label": "对喷嘴出口与射流最高点列能量方程求得 v2 = √(2gh) ≈ 19.81 m/s，并由连续性方程得 v1 = v2/16 ≈ 1.24 m/s", "pts": 5},
                    {"label": "对活塞筒断面与喷嘴出口列能量方程 H + p1/(ρg) + v1²/(2g) = v2²/(2g)，求得筒内表压 p1 ≈ 146.38 kPa", "pts": 5},
                    {"label": "由 P = p1·(πD²/4) 计算出作用于活塞上的推力 P ≈ 4.60 kN", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2021-11",
                "year": 2021,
                "no": 11,
                "type": "calc",
                "score": 17,
                "title": "水平自由射流冲击斜置固定平板的分流量与法向冲击力计算",
                "stem": "处于一水平面内的射流从喷嘴射出，冲击着一个与之成 $\\theta$ 角的斜置固定平板，如图所示。已知射流流量为 $Q_0$，流速大小为 $v_0$，液体密度为 $\\rho$，忽略水头损失，求沿 $S$ 方向的分流量 $Q_1$、$Q_2$ 及射流对平板的冲击力。",
                "note": "",
                "figures": [
                    {"src": "figures/q11_orig.png", "caption": "题 11 图　水平自由射流冲击斜置固定平板"}
                ],
                "shortAnswer": "Q1 = (1/2)Q0(1 + cosθ)，Q2 = (1/2)Q0(1 - cosθ)；射流对平板的冲击力大小 F = ρQ0v0·sinθ，方向垂直于平板指向板面。",
                "judgeAnswer": None,
                "answer": "沿平板两侧的分流量分别为：\n\n$$\nQ_1 = \\frac{1}{2}Q_0(1 + \\cos\\theta), \\qquad Q_2 = \\frac{1}{2}Q_0(1 - \\cos\\theta)\n$$\n\n射流对斜置固定平板的冲击力大小为：\n\n$$\nF = \\rho Q_0 v_0 \\sin\\theta\n$$\n\n方向**垂直于平板板面指向板内**（即图面右下方，与 $S$ 轴正交）。",
                "analysis": "**1. 由伯努利方程与连续性方程建立流速与流量关系**\n\n射流位于同一水平面内（各点位置高差 $\\Delta z = 0$），且暴露于大气中自由流动（射流冲击区外各渐变流断面 $0\\text{—}0$、$1\\text{—}1$、$2\\text{—}2$ 上的相对压强均为 $p_0 = p_1 = p_2 = 0$）。忽略水头损失时，由伯努利方程可知分流后两股水流的流速大小不变：\n\n$$\nv_1 = v_2 = v_0\n$$\n\n选取包含射流冲击分流区的控制体（见解图 11），由恒定不可压缩流动连续性方程得：\n\n$$\nQ_1 + Q_2 = Q_0 \\qquad (1)\n$$\n\n**2. 沿平板切向 $S$ 轴列动量方程求分流量 $Q_1$、$Q_2$**\n\n因忽略水头损失，平板壁面切向摩阻力可忽略不计（切向反力 $R_S = 0$），且控制体四周均通大气无压差外力。取动量修正系数 $\\beta_0 = \\beta_1 = \\beta_2 = 1.0$，沿题图所示平行于平板向上的 $S$ 轴列恒定总流动量方程：\n\n$$\n\\sum F_S = 0 = \\rho Q_1 v_1 + \\rho Q_2 (-v_2) - \\rho Q_0 (v_0 \\cos\\theta)\n$$\n\n将 $v_1 = v_2 = v_0$ 代入并约去 $\\rho v_0$，得：\n\n$$\nQ_1 - Q_2 = Q_0 \\cos\\theta \\qquad (2)\n$$\n\n联立式 $(1)$ 与式 $(2)$ 解得：\n\n$$\nQ_1 = \\frac{1}{2}Q_0(1 + \\cos\\theta), \\qquad Q_2 = \\frac{1}{2}Q_0(1 - \\cos\\theta)\n$$\n\n**3. 沿垂直于平板的法向 $n$ 轴列动量方程求冲击力 $F$**\n\n取垂直于平板指向板面内侧（右下方）为法向 $n$ 正方向，设平板对控制体水流的法向支撑反力为 $R_n$（方向沿 $-n$ 向外指）：出流断面 $1\\text{—}1$、$2\\text{—}2$ 均平行于平板，法向流速分量为 $0$；入流断面 $0\\text{—}0$ 在 $+n$ 方向的速度分量为 $v_0 \\sin\\theta$。列 $n$ 向动量方程：\n\n$$\n-R_n = 0 - \\rho Q_0 (v_0 \\sin\\theta) \\implies R_n = \\rho Q_0 v_0 \\sin\\theta\n$$\n\n由牛顿第三定律，射流对平板的冲击力 $F$ 与 $R_n$ 等值反向，故大小为 **$F = \\rho Q_0 v_0 \\sin\\theta$**，方向**垂直于平板指向板面**。\n\n（特例校核：当 $\\theta = 90^{\\circ}$ 正冲平板时，$Q_1 = Q_2 = \\frac{1}{2}Q_0$，$F = \\rho Q_0 v_0$；当 $\\theta = 0^{\\circ}$ 掠过平板时，$Q_1 = Q_0, Q_2 = 0, F = 0$，物理意义完全自洽。）",
                "analysisFigures": [
                    {"src": "figures/q11_sol.png", "caption": "解图 11　斜置平板自由射流控制体与切向/法向正交坐标分解"}
                ],
                "pitfalls": "建立坐标系时强烈建议直接选取**沿平板的切向 $S$ 与垂直平板的法向 $n$**（而非水平 $x$ 与竖直 $y$）：在 $(S,n)$ 正交系下，未知力 $R_n$ 在 $S$ 轴投影天然为零，一步即可解出 $Q_1 - Q_2 = Q_0\\cos\\theta$，计算量减半且绝不会漏项！",
                "chapter": 3,
                "kps": ["恒定总流动量方程", "自由射流分流规律", "恒定总流能量方程"],
                "method": "能量方程求流速+动量方程切法向正交分解法",
                "difficulty": 3,
                "rubric": [
                    {"label": "由水平自由射流能量方程指出 v1 = v2 = v0，并写出连续性方程 Q1 + Q2 = Q0", "pts": 4},
                    {"label": "沿平板切向 S 列动量方程得出 Q1 - Q2 = Q0·cosθ，联立解出 Q1、Q2 表达式", "pts": 7},
                    {"label": "沿平板法向列动量方程求得射流对平板冲击力大小 F = ρQ0v0·sinθ 并指明垂直指向板面", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2021-12",
                "year": 2021,
                "no": 12,
                "type": "proof",
                "score": 15,
                "title": "梯形明渠水力最佳断面宽深比条件推导与水力半径等于半水深证明",
                "stem": "推导梯形水力最佳断面宽深比应满足的条件，并证明梯形水力最佳断面的水力半径等于水深的一半",
                "note": "",
                "figures": [],
                "shortAnswer": "最佳宽深比 β = b/h = 2(√(1 + m²) - m)；代入 R = A/χ 化简即证 R = h/2。",
                "judgeAnswer": None,
                "answer": "梯形明渠水力最佳断面的宽深比 $\\beta = \\frac{b}{h}$ 应满足：\n\n$$\n\\beta = \\frac{b}{h} = 2\\left(\\sqrt{1 + m^2} - m\\right)\n$$\n\n其中 $b$ 为渠底宽度，$h$ 为水深，$m$ 为边坡系数；在该条件下水力半径恒满足 $R = \\frac{h}{2}$（证明过程见解析）。",
                "analysis": "**1. 建立梯形断面水力要素关系并明确极值条件**\n\n设梯形明渠底宽为 $b$，水深为 $h$，边坡系数为 $m$（见解图 12），则过水断面面积 $A$ 与湿周 $\\chi$ 分别为：\n\n$$\nA = (b + m h) h \\implies b = \\frac{A}{h} - m h\n$$\n\n$$\n\\chi = b + 2 h \\sqrt{1 + m^2}\n$$\n\n将 $b = \\frac{A}{h} - m h$ 代入湿周表达式，消去变量 $b$：\n\n$$\n\\chi(h) = \\frac{A}{h} + \\left(2\\sqrt{1 + m^2} - m\\right) h\n$$\n\n由明渠均匀流曼宁公式 $Q = \\frac{1}{n} A R^{2/3} i^{1/2} = \\frac{1}{n} \\frac{A^{5/3}}{\\chi^{2/3}} i^{1/2}$ 可知：当设计断面面积 $A$、粗糙系数 $n$、底坡 $i$ 及边坡系数 $m$ 一定时，要使渠道通过流量 $Q$ 最大（即水力最佳断面），等价于使湿周 $\\chi(h)$ 取得**极小值**。\n\n**2. 求导推导最佳宽深比条件 $\\beta = \\frac{b}{h}$**\n\n视 $A$、$m$ 为常数，令湿周 $\\chi$ 对水深 $h$ 的一阶导数为零：\n\n$$\n\\frac{\\mathrm{d}\\chi}{\\mathrm{d}h} = -\\frac{A}{h^2} + 2\\sqrt{1 + m^2} - m = 0 \\implies A = \\left(2\\sqrt{1 + m^2} - m\\right) h^2\n$$\n\n且二阶导数 $\\frac{\\mathrm{d}^2\\chi}{\\mathrm{d}h^2} = \\frac{2A}{h^3} > 0$，证实此时湿周 $\\chi$ 确取严格极小值。将 $A = (b + m h) h$ 代回上式：\n\n$$\n(b + m h) h = \\left(2\\sqrt{1 + m^2} - m\\right) h^2 \\implies b + m h = 2 h \\sqrt{1 + m^2} - m h\n$$\n\n两边同除以水深 $h$，即得梯形水力最佳断面宽深比应满足的条件：\n\n$$\n\\beta = \\frac{b}{h} = 2\\left(\\sqrt{1 + m^2} - m\\right)\n$$\n\n**3. 证明梯形水力最佳断面的水力半径 $R = \\frac{h}{2}$**\n\n将最佳宽深比关系 $b = 2 h \\left(\\sqrt{1 + m^2} - m\\right)$ 分别代入面积 $A$ 和湿周 $\\chi$：\n\n$$\nA_{\\text{佳}} = (b + m h) h = \\left[2\\left(\\sqrt{1 + m^2} - m\\right) + m\\right] h^2 = \\left(2\\sqrt{1 + m^2} - m\\right) h^2\n$$\n\n$$\n\\chi_{\\text{佳}} = b + 2 h \\sqrt{1 + m^2} = \\left[2\\left(\\sqrt{1 + m^2} - m\\right) + 2\\sqrt{1 + m^2}\\right] h = 2\\left(2\\sqrt{1 + m^2} - m\\right) h\n$$\n\n由于边坡系数 $m \\ge 0$ 时恒有 $2\\sqrt{1 + m^2} - m > 0$，两式相除得水力半径：\n\n$$\nR_{\\text{佳}} = \\frac{A_{\\text{佳}}}{\\chi_{\\text{佳}}} = \\frac{\\left(2\\sqrt{1 + m^2} - m\\right) h^2}{2\\left(2\\sqrt{1 + m^2} - m\\right) h} = \\frac{h}{2}\n$$\n\n即证梯形水力最佳断面的水力半径恒等于水深的一半（与边坡系数 $m$ 无关，当 $m=0$ 退化为矩形最佳断面时同样有 $\\frac{b}{h} = 2$、$R = \\frac{h}{2}$）。",
                "analysisFigures": [
                    {"src": "figures/q12_sol.png", "caption": "解图 12　水力最佳梯形断面的几何特征（以水面中点为圆心、水深 h 为半径的半圆与底及两侧边坡均相切）"}
                ],
                "pitfalls": "1. 求导 $\\frac{\\mathrm{d}\\chi}{\\mathrm{d}h} = 0$ 前，**必须先利用 $b = \\frac{A}{h} - m h$ 将底宽 $b$ 用常数面积 $A$ 和水深 $h$ 表出**，切忌把 $b$ 当作与 $h$ 无关的常数直接对 $\\chi = b + 2h\\sqrt{1+m^2}$ 求导！\n2. 最后约分时看清分子是 $h^2$、分母是 $2h$，约分结果为 $\\frac{h}{2}$（半水深），切勿笔误写成 $\\frac{b}{2}$。",
                "chapter": 7,
                "kps": ["水力最佳断面", "梯形明渠水力要素", "曼宁公式"],
                "method": "固定面积最小湿周微分极值推导法",
                "difficulty": 3,
                "rubric": [
                    {"label": "正确写出梯形断面面积 A = (b+mh)h 与湿周 χ = b + 2h√(1+m²)，消去 b 建立 χ(h) 表达式", "pts": 4},
                    {"label": "利用固定 A、m 下 dχ/dh = 0（或隐函数求导）推导出最佳宽深比 b/h = 2(√(1+m²) - m)", "pts": 6},
                    {"label": "将最佳宽深比代入 R = A/χ 严格约分化简证明 R = h/2", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2021-13",
                "year": 2021,
                "no": 13,
                "type": "calc",
                "score": 15,
                "title": "恒定平面势流的速度、迁移加速度及两流线间单宽流量计算",
                "stem": "有一恒定平面势流，已知 $\\varphi = 3xy$，求点 $(1, 3)$ 及 $(3, 3)$ 处的速度 $u_x$、$u_y$ 及加速度 $a_x$、$a_y$，并求通过这两点的流线之间的流量。",
                "note": "",
                "figures": [],
                "shortAnswer": "点(1,3)：ux=9，uy=3，ax=9，ay=27；点(3,3)：ux=9，uy=9，ax=27，ay=27；两流线间单宽流量 q = 12（SI 单位下分别为 m/s、m/s²、m²/s）。",
                "judgeAnswer": None,
                "answer": "采用速度势正梯度定义 $u_x = \\frac{\\partial\\varphi}{\\partial x}$、$u_y = \\frac{\\partial\\varphi}{\\partial y}$（国际单位制下）：\n\n1. **点 $(1, 3)$ 处**：$u_x = 9\\,\\mathrm{m/s}$，$u_y = 3\\,\\mathrm{m/s}$；$a_x = 9\\,\\mathrm{m/s^2}$，$a_y = 27\\,\\mathrm{m/s^2}$；\n2. **点 $(3, 3)$ 处**：$u_x = 9\\,\\mathrm{m/s}$，$u_y = 9\\,\\mathrm{m/s}$；$a_x = 27\\,\\mathrm{m/s^2}$，$a_y = 27\\,\\mathrm{m/s^2}$；\n3. **通过这两点的流线之间的单宽流量**：$q = 12\\,\\mathrm{m^2/s}$（即 $12\\,\\mathrm{m^3/(s\\cdot m)}$）。",
                "analysis": "**1. 由速度势函数 $\\varphi = 3xy$ 求两指定点处的流速分量**\n\n验证拉普拉斯方程：$\\nabla^2\\varphi = \\frac{\\partial^2\\varphi}{\\partial x^2} + \\frac{\\partial^2\\varphi}{\\partial y^2} = 0 + 0 = 0$，满足不可压缩平面势流条件。按水力学标准定义：\n\n$$\nu_x = \\frac{\\partial\\varphi}{\\partial x} = 3y, \\qquad u_y = \\frac{\\partial\\varphi}{\\partial y} = 3x\n$$\n\n分别代入两点坐标：\n- 在点 $M_1(1, 3)$ 处：$u_x(1,3) = 3 \\times 3 = 9\\,\\mathrm{m/s}$，$u_y(1,3) = 3 \\times 1 = 3\\,\\mathrm{m/s}$；\n- 在点 $M_2(3, 3)$ 处：$u_x(3,3) = 3 \\times 3 = 9\\,\\mathrm{m/s}$，$u_y(3,3) = 3 \\times 3 = 9\\,\\mathrm{m/s}$。\n\n**2. 计算两指定点处的欧拉加速度分量 $a_x$、$a_y$**\n\n因流动为恒定流，当地加速度 $\\frac{\\partial u_x}{\\partial t} = \\frac{\\partial u_y}{\\partial t} = 0$，全加速度等于迁移加速度：\n\n$$\na_x = u_x\\frac{\\partial u_x}{\\partial x} + u_y\\frac{\\partial u_x}{\\partial y} = (3y)\\times 0 + (3x)\\times 3 = 9x\n$$\n\n$$\na_y = u_x\\frac{\\partial u_y}{\\partial x} + u_y\\frac{\\partial u_y}{\\partial y} = (3y)\\times 3 + (3x)\\times 0 = 9y\n$$\n\n分别代入两点坐标：\n- 在点 $M_1(1, 3)$ 处：$a_x(1,3) = 9 \\times 1 = 9\\,\\mathrm{m/s^2}$，$a_y(1,3) = 9 \\times 3 = 27\\,\\mathrm{m/s^2}$；\n- 在点 $M_2(3, 3)$ 处：$a_x(3,3) = 9 \\times 3 = 27\\,\\mathrm{m/s^2}$，$a_y(3,3) = 9 \\times 3 = 27\\,\\mathrm{m/s^2}$。\n\n**3. 求流函数 $\\psi(x,y)$ 及通过两点的流线间单宽流量 $q$**\n\n由柯西—黎曼关系 $\\frac{\\partial\\psi}{\\partial y} = u_x = 3y$、$-\\frac{\\partial\\psi}{\\partial x} = u_y = 3x$，全微分积分求流函数：\n\n$$\n\\mathrm{d}\\psi = -u_y\\,\\mathrm{d}x + u_x\\,\\mathrm{d}y = -3x\\,\\mathrm{d}x + 3y\\,\\mathrm{d}y \\implies \\psi(x,y) = \\frac{3}{2}(y^2 - x^2) + C\n$$\n\n计算两点处的流函数值：\n\n$$\n\\psi(1, 3) = \\frac{3}{2}(3^2 - 1^2) + C = 12 + C, \\qquad \\psi(3, 3) = \\frac{3}{2}(3^2 - 3^2) + C = C\n$$\n\n故通过这两点的两条流线之间的单宽流量为：\n\n$$\nq = |\\psi(1, 3) - \\psi(3, 3)| = |12 - 0| = 12\\,\\mathrm{m^2/s}\n$$\n\n（注：若部分教材采用负梯度约定 $\\vec{u} = -\\nabla\\varphi$，则 $u_x, u_y$ 反号，而加速度 $a_x = 9x, a_y = 9y$ 与单宽流量大小 $q = 12\\,\\mathrm{m^2/s}$ 完全不变。）",
                "analysisFigures": [],
                "pitfalls": "1. 算出加速度代数式 $a_x = 9x$、$a_y = 9y$ 后，**必须将点 $(1,3)$ 和 $(3,3)$ 的坐标代入算出具体数值**（$(9, 27)$ 与 $(27, 27)$），切勿停留在含 $x,y$ 的字母式而丢分！\n2. 积分流函数时注意负号 $\\frac{\\partial\\psi}{\\partial x} = -u_y = -3x$（切勿误写成 $+3x$，否则与 $\\nabla^2\\psi = 0$ 矛盾）。",
                "chapter": 5,
                "kps": ["流函数与势函数", "欧拉法质点加速度", "柯西-黎曼条件"],
                "method": "势函数求导与流函数差值求流量法",
                "difficulty": 2,
                "rubric": [
                    {"label": "由 ux = ∂φ/∂x = 3y、uy = ∂φ/∂y = 3x 准确算出 (1,3) 和 (3,3) 两点处的速度分量", "pts": 5},
                    {"label": "由欧拉迁移加速度公式导出 ax = 9x、ay = 9y 并算出 (1,3) 和 (3,3) 两点处的加速度分量", "pts": 5},
                    {"label": "积分求出流函数 ψ = 1.5(y² - x²) + C，并由 |ψ1 - ψ2| 求得两流线间单宽流量 q = 12 m²/s", "pts": 5}
                ]
            }
        ]
    }


# ==============================================================================
# 2020 Exam Paper Structured Data (13 Questions, 150 Points)
# ==============================================================================

def build_2020_paper() -> dict:
    return {
        "year": 2020,
        "code": "849",
        "subject": "水力学（水）",
        "school": "扬州大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": True,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "全卷共 13 道题：一、简答题（第 1～5 题，5×8=40 分）；二、计算题（第 6～12 题，10+15+15+15+15+10+10=90 分）；三、综合题（第 13 题，20 分）。",
            "除特别说明外，计算统一取重力加速度 $g = 9.81\\,\\mathrm{m/s^2}$，水的密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$（解析同步附 $g = 9.80\\,\\mathrm{m/s^2}$ 对照结果）。"
        ],
        "sections": [
            {
                "id": "short",
                "title": "一、简答题",
                "description": "本大题共 5 小题，每小题 8 分，共 40 分。",
                "range": [1, 5],
                "scorePerQuestion": 8,
                "totalScore": 40
            },
            {
                "id": "calc",
                "title": "二、计算题",
                "description": "本大题共 7 小题（10+15+15+15+15+10+10 分），共 90 分。",
                "range": [6, 12],
                "totalScore": 90
            },
            {
                "id": "comp",
                "title": "三、综合题",
                "description": "本大题共 1 小题，20 分。",
                "range": [13, 13],
                "scorePerQuestion": 20,
                "totalScore": 20
            }
        ],
        "questions": [
            {
                "id": "yzu-849-2020-01",
                "year": 2020,
                "no": 1,
                "type": "short",
                "score": 8,
                "title": "液体粘性内摩擦力与固体接触面间干摩擦力的区别",
                "stem": "液体粘性引起的内摩擦力与固体间的摩擦力有何区别？",
                "note": "",
                "figures": [],
                "shortAnswer": "主要区别：（1）静止时液体无静摩擦力，仅相对运动时才有内摩擦力，而固体存在静摩擦力；（2）液体内摩擦力与接触面法向正压力无关，固体滑动摩擦力与法向正压力成正比；（3）液体总内摩擦力与接触面积成正比，固体摩擦力与表观接触面积无关；（4）液体内摩擦力与法向速度梯度及流体黏度成正比，固体滑动摩擦力在一定范围内与滑动速度大小基本无关而取决于表面粗糙度。",
                "judgeAnswer": None,
                "answer": "液体因粘性引起的内摩擦力（服从牛顿内摩擦定律 $T = \\mu A \\frac{\\mathrm{d}u}{\\mathrm{d}y}$）与固体接触面间的干摩擦力（服从库仑摩擦定律 $F_f = \\mu_s N$）存在以下四点本质区别：\n\n1. **静止状态下是否存在摩擦力不同**：\n   - **固体**：两固体相对静止但有相对运动趋势时即存在**静摩擦力**（且最大静摩擦力略大于动摩擦力）；\n   - **液体**：静止液体不能承受任何剪切力，当速度梯度 $\\frac{\\mathrm{d}u}{\\mathrm{d}y} = 0$ 时液体内摩擦力严格为零（**不存在静摩擦力**），粘性内摩擦力仅在流体发生相对剪切运动时才产生。\n2. **与接触面法向正压力（压强）的关系不同**：\n   - **固体**：滑动摩擦力 $F_f = \\mu_s N$ 与接触面上的**法向正压力 $N$ 成正比**；\n   - **液体**：在常温常压工程范围内，液体粘性内摩擦力**与流层间的法向动水压强 $p$ 基本无关**。\n3. **与接触面面积大小的关系不同**：\n   - **固体**：摩擦力大小与两固体的表观接触面积 $A$ **无关**；\n   - **液体**：相邻流层间的总内摩擦力 $T = \\tau A$ **与流层接触面积 $A$ 成正比**。\n4. **与相对运动速度及介质物性的关系不同**：\n   - **固体**：滑动摩擦力在一定速度范围内与相对滑动速度大小基本无关，主要取决于接触面材料与表面粗糙度；\n   - **液体**：层流内摩擦力与**法向速度梯度 $\\frac{\\mathrm{d}u}{\\mathrm{d}y}$（相对速度变化率）成正比**，且取决于液体物性参数动力黏度 $\\mu$（随温度升高，液体黏度 $\\mu$ 减小、内摩擦力减小）。",
                "analysis": "**公式对照助记表**\n\n直接写出两条基本物理定律，即可逐项对照导出全部四条差异，条理清晰且绝不遗漏：\n\n$$\n\\text{液体牛顿内摩擦定律：}\\; T = \\mu A \\frac{\\mathrm{d}u}{\\mathrm{d}y} \\qquad \\Longleftrightarrow \\qquad \\text{固体库仑干摩擦定律：}\\; F_f = \\mu_s N\n$$\n\n- 令 $\\frac{\\mathrm{d}u}{\\mathrm{d}y} = 0$ $\\implies T = 0$（液体无静摩擦）；\n- 观察 $N$：右式显含法向正压力 $N$，左式不含压强 $p$；\n- 观察 $A$：左式显含接触面积 $A$，右式不含面积 $A$；\n- 观察速度：左式正比于速度梯度 $\\frac{\\mathrm{d}u}{\\mathrm{d}y}$，右式在常规低速下与滑速无关。",
                "analysisFigures": [],
                "pitfalls": "切忌漏答“**静止液体无静摩擦力**”这一水静力学最根本的物理前提！正是因为静止液体内部切应力恒为零，静止液体的内力才只有垂直指向受压面的法向静水压强。",
                "chapter": 1,
                "kps": ["牛顿内摩擦定律", "液体黏性与固体摩擦对比"],
                "method": "牛顿内摩擦定律与库仑摩擦对比法",
                "difficulty": 1,
                "rubric": [
                    {"label": "指出静止状态下区别：固体有静摩擦力，而静止液体内部不存在静摩擦力（du/dy=0 时 τ=0）", "pts": 2},
                    {"label": "指出与法向正压力关系区别：固体摩擦力正比于法向正压力，液体内摩擦力与法向压强无关", "pts": 2},
                    {"label": "指出与接触面积关系区别：液体总内摩擦力正比于接触面积 A，固体摩擦力与接触面积无关", "pts": 2},
                    {"label": "指出与运动速度及物性关系区别：液体内摩擦力正比于速度梯度 du/dy 与黏度 μ，固体与滑速基本无关", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2020-02",
                "year": 2020,
                "no": 2,
                "type": "short",
                "score": 8,
                "title": "密闭水箱连通器测压管水位、气室压强及拆管出流判别分析",
                "stem": "如图所示的密闭水箱，用橡皮管从 $C$ 点连通容器 II，并在 $A$、$B$ 两点各接一测压管，试问：\n\n（1）$A$、$B$ 两测压管中的水位是否相平，如果相平，两点的压强是否相等？\n\n（2）把容器 II 提高一些后，$p_0$ 比原来增大还是减小？两个测压管中的水位变化如何？\n\n（3）堵塞 $A$、$B$ 处的测压管后，若将容器 II 逐渐下降，直至容器 II 中的水面正好与 $C$ 点在同一个水平面上，此时 $C$ 点压强为多大？这时若拆去连接的橡皮管，水箱内的水是否会从 $C$ 处流出来？",
                "note": "",
                "figures": [
                    {"src": "figures/q02_orig.png", "caption": "题 2 图　密闭水箱 I 与开口容器 II 连通及测压管布置"}
                ],
                "shortAnswer": "（1）A、B 两测压管水位相平（且与容器 II 水面齐平），但 A、B 两点压强不相等（pB > pA）；（2）提高容器 II 后 p0 增大，两测压管水位均升高且仍保持相平；（3）此时 C 点绝对压强等于当地大气压 pa（相对压强为 0），拆去橡皮管后水不会从 C 处流出。",
                "judgeAnswer": None,
                "answer": "**（1）$A$、$B$ 两测压管中的水位相平，但 $A$、$B$ 两点的压强不相等（$p_B > p_A$）**。\n- **原因**：水箱 I、两根开口测压管及容器 II 中装的是同一种连续、均质、静止的水，满足静水基本方程 $z + \\frac{p}{\\rho g} = \\text{const}$，即各点测压管水头处处相等，故 $A$、$B$ 两开口测压管中的自由液面必然**相平**（且与开口容器 II 的水面齐平）。但因两点几何高程 $z_A > z_B$，由 $\\frac{p_B - p_A}{\\rho g} = z_A - z_B > 0$ 可知 **$p_B > p_A$**，两点压强不相等。\n\n**（2）把容器 II 提高一些后，$p_0$ 比原来增大；两测压管中的水位均升高且仍保持相平**。\n- **原因**：容器 II 抬高瞬间其液面高于原测压管水头线，部分水由容器 II 经 $C$ 压入密闭水箱 I 及测压管内，使水箱 I 内液面上升、顶部密闭气室体积被压缩减小；由等温气体玻意耳定律知气室压强 **$p_0$ 增大**。重新达到静水平衡后，系统测压管水头 $z_{\\text{箱液面}} + \\frac{p_0}{\\rho g}$ 增大至与提高后的容器 II 新水面齐平，故**两个测压管中的水位均比原来升高，且依然彼此相平**。\n\n**（3）此时 $C$ 点绝对压强等于大气压强 $p_a$（相对压强为 $0$）；拆去橡皮管后水箱内的水不会从 $C$ 处流出来**。\n- **原因**：当开口容器 II 的自由水面降至与 $C$ 点位于同一水平面时，在连续静止水体中该水平面即为**等压面**，容器 II 液面通大气（绝对压强 $p_a$、表压 $0$），故 **$C$ 点绝对压强 $p_C = p_a$（相对压强 $p_{C,\\text{相}} = 0$）**，此时密闭水箱顶部已处于负压真空状态（$p_{0,\\text{绝}} = p_a - \\rho g h_{\\text{箱液面-}C} < p_a$）。拆去橡皮管后，$C$ 孔口内外压强均为大气压 $p_a$（内外无压差），外部大气压恰好托住箱内水柱与顶部真空吸力相平衡，故**水不会从 $C$ 处流出来**（设孔口细小不发生空气鼓泡置换）。",
                "analysis": "**核心概念辨析：测压管水头（水位）相等 $\\neq$ 静水压强相等**\n\n1. 在同种连通静止重力液体中，处处相等的是**测压管水头** $H_p = z + \\frac{p}{\\rho g}$（即开口测压管内液面自由上升所达到的高程），而某点本身的压强 $p = \\rho g (H_p - z)$ 还取决于该点位置高度 $z$，位置越低压强越大。\n2. 第（3）问是典型的负压水封（类似倒置量筒或马氏瓶、禽类自动饮水器原理）：当容器 II 下降时，水箱 I 内部分水流入容器 II 使顶部封闭气体膨胀降压形成真空度 $p_v = \\rho g h_{\\text{液面-}C}$，至容器 II 水面与 $C$ 同高时恰好有 $p_{0,\\text{绝}} + \\rho g h_{\\text{液面-}C} = p_a$，拆管前后 $C$ 点边界条件（压强等于 $p_a$）并未改变，静力平衡不被破坏，故水不外流。",
                "analysisFigures": [],
                "pitfalls": "1. 第（1）问切勿因“两测压管液面相平”就误答“$A$、$B$ 两点压强相等”——相平的是 $z + \\frac{p}{\\rho g}$，因 $z_A \\neq z_B$，必有 $p_A \\neq p_B$！\n2. 第（3）问写 $C$ 点压强时务必注明是“**相对压强为 $0$（或绝对压强等于当地大气压 $p_a$）**”，避免绝对压强与相对压强表述含糊。",
                "chapter": 2,
                "kps": ["静水压强基本方程", "测压管水头", "等压面性质", "真空度与负压平衡"],
                "method": "等压面静水压强递推法",
                "difficulty": 2,
                "rubric": [
                    {"label": "正确回答（1）两测压管水位相平，但因位置高度不同故 A、B 两点压强不相等（pB > pA）", "pts": 3},
                    {"label": "正确分析（2）提高容器 II 后箱顶气体压缩使 p0 增大，两测压管水位均升高且保持相平", "pts": 2},
                    {"label": "正确得出（3）C 点绝对压强等于大气压 pa（表压为 0），并说明内外无压差故拆管后水不会流出", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2020-03",
                "year": 2020,
                "no": 3,
                "type": "short",
                "score": 8,
                "title": "变截面串联有压管道的恒定/非恒定流、均匀/非均匀流与渐变/急变流判别",
                "stem": "如图所示，水流通过由两段等截面及一段变截面组成的管道，如果上游水位保持不变，试问：\n\n（1）当阀门 $T$ 开度一定，各段管中是恒定流还是非恒定流？各段管中为均匀流还是非均匀流？\n\n（2）当阀门 $T$ 逐渐关闭，这时管中为恒定流还是非恒定流？\n\n（3）在恒定流情况下，当判别第 II 段管中是渐变流还是急变流时，与该段管长有无关系？",
                "note": "",
                "figures": [
                    {"src": "figures/q03_orig.png", "caption": "题 3 图　由两段等截面管与一段变截面管组成的有压管道"}
                ],
                "shortAnswer": "（1）阀门开度一定时各段管均为恒定流；第 I、III 段（除局部进出口变径区外）为均匀流，第 II 段为非均匀流。（2）阀门逐渐关闭时管中为非恒定流。（3）与第 II 段管长有直接关系：管长较长则锥角小、流线近乎平行，为渐变流；管长很短则锥角大、流线急剧聚拢弯曲，为急变流。",
                "judgeAnswer": None,
                "answer": "**（1）当上游水位不变且阀门 $T$ 开度一定时**：\n- **时间维度**：系统上下游边界与管路阻力均不随时间变化，各空间点流速、压强满足 $\\frac{\\partial u}{\\partial t} = 0$、$\\frac{\\partial p}{\\partial t} = 0$，故**第 I、II、III 各段管中均为恒定流**；\n- **空间维度**：**第 I 段和第 III 段**为等直径长直圆管（除紧邻水箱进口、变径连接处及阀门附近的局部扰动区外），断面面积与平均流速沿程不变、流线为平行直线，属**均匀流**；**第 II 段**为圆锥渐缩变截面管，过水断面积沿程减小、流速沿程增大、流线彼此倾斜聚拢，属**非均匀流**。\n\n**（2）当阀门 $T$ 逐渐关闭时**：\n- 阀门局部阻力系数随时间不断增大，管内流量 $Q(t)$ 随时间减小，管道各空间点处的流速和动水压强均随时间发生改变（$\\frac{\\partial u}{\\partial t} \\neq 0$，$\\frac{\\partial p}{\\partial t} \\neq 0$），故**此时整条管道（各段管中）均为非恒定流**。\n\n**（3）恒定流下判别第 II 段是渐变流还是急变流，与该段管长有直接关系**：\n- 渐变流与急变流的判别依据是**流线间的夹角大小及流线曲率半径大小**。在第 II 段进出口管径 $d_{\\text{I}}$、$d_{\\text{III}}$ 已定的前提下，圆锥收缩半角满足 $\\tan\\frac{\\theta}{2} = \\frac{d_{\\text{I}} - d_{\\text{III}}}{2 l_{\\text{II}}}$：\n  - 若第 II 段**管长 $l_{\\text{II}}$ 较长**，则收缩锥角 $\\theta$ 很小，流线间夹角极小且近似平行直线，法向离心惯性力可忽略，过水断面上动水压强近似按静水压强规律分布，该段为**渐变流**；\n  - 若第 II 段**管长 $l_{\\text{II}}$ 很短**（趋近于突然缩小），则收缩角 $\\theta$ 很大，流线在短距离内急剧弯曲聚拢（甚至在下游入口发生局部收缩分离），不能忽略流线弯曲离心力，该段即为**急变流**。",
                "analysis": "**流态分类判别逻辑梳理**\n\n水力学对流动的分类采用互相独立的两个正交维度，答题时切忌混为一谈：\n1. **按运动要素是否随时间 $t$ 变化**：分为**恒定流**（$\\frac{\\partial}{\\partial t} = 0$）与**非恒定流**（$\\frac{\\partial}{\\partial t} \\neq 0$）——看上游水位和阀门开度是否随时间变动；\n2. **按运动要素是否随空间流程 $s$ 变化（流线是否为平行直线）**：分为**均匀流**（等截面顺直段）与**非均匀流**（变截面或弯曲段）；而非均匀流又进一步按流线弯曲程度与夹角缓急细分为**渐变流**和**急变流**。",
                "analysisFigures": [],
                "pitfalls": "第（3）问切勿不加分析直接答“渐缩管就是渐变流，与管长无关”！只有小锥角长渐缩管（一般锥角 $\\theta < 6^{\\circ}\\sim 8^{\\circ}$）才可视为渐变流；当进出口管径差固定而管长极短时，大锥角收缩流属于典型的急变流。",
                "chapter": 3,
                "kps": ["恒定流与非恒定流", "均匀流与非均匀流", "渐变流与急变流性质"],
                "method": "欧拉时空偏导数与流线几何特征分类法",
                "difficulty": 2,
                "rubric": [
                    {"label": "正确判别（1）各段均为恒定流，其中第 I、III 段为均匀流，第 II 段变截面管为非均匀流", "pts": 3},
                    {"label": "正确判别（2）阀门逐渐关闭过程中流量与流速随时间变化，管中为非恒定流", "pts": 2},
                    {"label": "明确回答（3）与第 II 段管长有关，并结合收缩角与流线夹角/曲率说明长管为渐变流、短管为急变流", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2020-04",
                "year": 2020,
                "no": 4,
                "type": "short",
                "score": 8,
                "title": "水箱下垂直有压管道出流与孔口自由水股各断面流速及压强计算对比",
                "stem": "如图所示，图（a）为水箱下管道出流，图（b）为水箱下孔口出流，试问：\n\n（1）在恒定流情况下，图（a）中垂直管中各断面的流速是否相等？压强是否相等？如果不相等，如何计算？\n\n（2）图（b）中水股各断面的流速是否相等？压强是否相等？如果不相等，如何计算？",
                "note": "",
                "figures": [
                    {"src": "figures/q04_orig.png", "caption": "题 4 图　（a）水箱下管道出流与（b）水箱下孔口自由水股出流"}
                ],
                "shortAnswer": "（1）图（a）等径垂直管中各断面平均流速相等（v = Q/A），压强不相等，由水箱液面至该断面列伯努利方程 pk = ρg[z液 - zk - αv²/(2g) - hw] 计算；（2）图（b）自由水股各断面压强相等（均等于大气压，相对压强为 0），流速不相等（向下不断加速），距水箱水面落差 y 处流速由伯努利方程 v = √[2g(y - hw)]（不计损失时 v = √[2g(H + z)]）计算。",
                "judgeAnswer": None,
                "answer": "**（1）图（a）水箱下等径垂直管道出流（恒定流）**：\n- **各断面的平均流速相等**：因垂直管管径不变（过水断面积 $A = \\text{const}$）且液体不可压缩，由连续性方程 $v = \\frac{Q}{A}$ 知垂直管各断面平均流速 $v$ 处处相等。\n- **各断面的压强不相等**：以水平出口管轴线为基准面（水箱水面高程为 $H$），对水箱自由液面（$z_0 = H, p_0 = 0, v_0 \\approx 0$）与垂直管内任一高程为 $z$ 的过水断面列恒定总流伯努利方程：\n\n$$\nH = z + \\frac{p}{\\rho g} + \\frac{\\alpha v^2}{2g} + h_{w0\\text{-}z} \\implies p = \\rho g \\left(H - z - \\frac{\\alpha v^2}{2g} - h_{w0\\text{-}z}\\right)\n$$\n\n（对垂直管内高差为 $\\Delta z = z_1 - z_2$ 的上下两断面，亦有 $\\frac{p_2 - p_1}{\\rho g} = (z_1 - z_2) - h_{f1\\text{-}2}$。）\n\n**（2）图（b）水箱底孔口铅直自由水股出流（恒定流）**：\n- **水股各断面的压强相等**：自由水股四周完全暴露于大气中且流线近似竖直平直，故水股各断面上的绝对压强均等于当地大气压 $p_a$（**相对压强处处相等且为 $p = 0$**）。\n- **水股各断面的流速不相等（沿程向下加速、水股变细）**：设某水股断面位于孔口下方铅直距离 $z$ 处（距水箱自由水面总落差为 $H + z$），不计空气阻力，对水箱自由液面与该水股断面列伯努利方程（设孔口局部水头损失为 $h_j$ 或孔口流速系数为 $\\varphi$）：\n  - 若忽略一切水头损失：$H + z = \\frac{v^2}{2g} \\implies v(z) = \\sqrt{2g(H + z)}$；\n  - 若计入孔口局部损失（孔口收缩断面流速 $v_c = \\varphi\\sqrt{2gH}$）：由收缩断面至下方落差 $z$ 处列能量方程得 $v(z) = \\sqrt{v_c^2 + 2gz} = \\sqrt{2g(\\varphi^2 H + z)}$。",
                "analysis": "**有压满管流 vs 无压自由水股的物理本质对比**\n\n本题极具启发性地对比了“刚性管壁约束”与“自由大气边界”对重力的不同响应机制：\n1. **图（a）有压等径垂直管**：刚性管壁限制了过水断面积 $A$ 不能收缩，连续性方程强制流速 $v = \\frac{Q}{A}$ 沿程恒定（重力无法使流体加速），于是流体下落释放的重力位能 $-\\rho g \\Delta z$ 除克服沿程摩阻外转化为**压强势能的变化**（注意：若下部水平管很短直接通大气，垂直管上部甚至会出现负压抽吸！）。\n2. **图（b）大气中自由水股**：外部大气边界强制压强 $p = 0$ 沿程恒定（压能无法改变），于是流体下落释放的重力位能全部转化为**动能的增加**，使流速 $v(z)$ 向下递增，同时由连续性方程 $A(z) = \\frac{Q}{v(z)}$ 导致自由水股横截面沿程向下逐渐收缩变细。",
                "analysisFigures": [],
                "pitfalls": "切忌将图（a）和图（b）混为一谈！图（a）是“**定面积 $\\Rightarrow$ 等流速、变压强**”；图（b）是“**定大气压 $\\Rightarrow$ 等压强（表压为零）、变流速（向下加速水股变细）**”。",
                "chapter": 3,
                "kps": ["恒定总流连续性方程", "恒定总流能量方程", "有压管流与自由射流对比"],
                "method": "连续性约束与大气压边界对比分析法",
                "difficulty": 2,
                "rubric": [
                    {"label": "准确回答（1）垂直有压管各断面流速相等、压强不等，并写出用伯努利方程计算各断面压强的公式", "pts": 4},
                    {"label": "准确回答（2）自由水股各断面流速不等、压强相等（相对压强为 0），并写出用伯努利方程计算流速的公式", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2020-05",
                "year": 2020,
                "no": 5,
                "type": "short",
                "score": 8,
                "title": "文丘里流量计测流原理及倾斜安装、反向流动可行性分析",
                "stem": "如图所示为一水平放置的文丘里流量计，管中水流由左向右流动。\n\n（1）简要说明文丘里流量计的测流原理；\n\n（2）若图中管轴线处于倾斜状态，文丘里流量计是否可以正常测流？为什么？\n\n（3）若图中管道内的水流方向变为由右向左，此时文丘里流量计是否可以正常测流？为什么？",
                "note": "",
                "figures": [
                    {"src": "figures/q05_orig.png", "caption": "题 5 图　文丘里流量计结构与测压管布置示意图"}
                ],
                "shortAnswer": "（1）利用渐缩喉管过水断面减小使流速增大、测压管水头降低，联立 1-1 与 2-2 断面能量方程和连续性方程，由实测测压管液柱高差 h 及流量修正系数 μ 求得流量；（2）倾斜放置时可以正常测流，因流量仅取决于两断面测压管水头差 h = (z1 + p1/γ) - (z2 + p2/γ)，与倾斜角无关；（3）水流改为由右向左时不能正常准确测流，因原大锥角收缩段反向变为急剧扩散段，引发严重边界层分离、涡流脉动与较大局部损失，使测压管 1 读数失真且原率定流量系数 μ 失效。",
                "judgeAnswer": None,
                "answer": "**（1）文丘里流量计的测流原理**：\n文丘里流量计由**收缩段、喉管和扩散段**串联组成。当水流流经断面缩小的喉管 $2\\text{—}2$（$A_2 < A_1$）时，流速增大（$v_2 > v_1$），动能增加而压能降低，使进口断面 $1\\text{—}1$ 与喉管断面 $2\\text{—}2$ 的测压管液面产生高度差 $h$。对 $1\\text{—}1$ 和 $2\\text{—}2$ 断面列理想流体伯努利方程与连续性方程（取 $\\alpha_1 = \\alpha_2 = 1.0$）：\n\n$$\n\\left(z_1 + \\frac{p_1}{\\rho g}\\right) - \\left(z_2 + \\frac{p_2}{\\rho g}\\right) = h = \\frac{v_2^2 - v_1^2}{2g}, \\qquad v_1 A_1 = v_2 A_2\n$$\n\n消去 $v_2$ 并引入考虑实际黏性水头损失的流量修正系数 $\\mu$（$\\mu \\approx 0.95 \\sim 0.98$），即可由实测液面差 $h$ 算出管道流量：\n\n$$\nQ = \\mu A_2 \\sqrt{\\frac{2gh}{1 - (A_2 / A_1)^2}} = \\mu \\frac{\\pi d_2^2}{4} \\sqrt{\\frac{2gh}{1 - (d_2 / d_1)^4}}\n$$\n\n**（2）管轴线处于倾斜状态时：可以正常测流**。\n- **原因**：无论文丘里管水平、倾斜还是铅直安装，两开口测压管的液面高度差恒直接等于两断面的**测压管水头差** $h = \\left(z_1 + \\frac{p_1}{\\rho g}\\right) - \\left(z_2 + \\frac{p_2}{\\rho g}\\right)$（位置高差 $z_1 - z_2$ 的变化自动由静水压强水头差补偿），推得的流量计算公式 $Q = K_v\\sqrt{h}$ 与管轴倾角完全无关。\n\n**（3）水流方向变为由右向左（反向流动）时：不可以正常测流**。\n- **原因**：文丘里管结构左右不对称——左侧**收缩段短而锥角大**（约 $20^{\\circ}$），右侧**扩散段长而锥角很小**（约 $5^{\\circ}\\sim 7^{\\circ}$），且测压管 $1$ 位于左端、测压管 $2$ 位于喉管。正向流动时 $1\\to 2$ 为顺压梯度加速收缩流，无分离、水头损失极小，流量系数 $\\mu$ 高而稳定；若水流反向（右 $\\to$ 左），水流从喉管 $2\\text{—}2$ 进入左侧原“收缩段”时变成**大锥角急剧扩散流**，在强逆压梯度下产生剧烈的**边界层分离与大尺度旋涡**，不仅造成很大的局部水头损失（此时 $h = \\frac{v_2^2 - v_1^2}{2g} - h_{w2\\text{-}1}$，使液面差 $h$ 大幅减小，原率定系数 $\\mu$ 完全失效），而且旋涡尾迹直接冲击断面 $1\\text{—}1$ 导致流态急变、测压管 $1$ 水位剧烈脉动失真，故工程上严禁反向测流（仅在假想无黏理想流体忽略一切分离损失的纯理论模型下公式才看似无方向性）。",
                "analysis": "**深入理解文丘里流量计“短急缩、长缓扩”的不对称水力设计**\n\n1. **为什么正向收缩段可以做得较短（锥角约 $20^{\\circ}$）？** 因为收缩流中流速沿程增大、压强沿程降低（$\\frac{\\mathrm{d}p}{\\mathrm{d}s} < 0$，顺压梯度），流体微团受压差推动加速，边界层变薄且紧贴管壁不分离，能量损失极小。\n2. **为什么正向扩散段必须做得细长平缓（锥角仅 $5^{\\circ}\\sim 7^{\\circ}$）？** 因为扩散流减速增压（$\\frac{\\mathrm{d}p}{\\mathrm{d}s} > 0$，逆压梯度），近壁低速流体极易受阻倒流诱发边界层脱体分离。一旦把文丘里管反装（或水流反向），原 $20^{\\circ}$ 收缩段被迫充当扩散段，正好踩中大角度扩散分离禁区，丧失测量精度与稳定性。",
                "analysisFigures": [],
                "pitfalls": "第（3）问极易掉入“理想伯努利方程代数可逆”的思维陷阱而误答“可以正常测流”！实际水力学仪器必须考虑**逆压梯度边界层分离**及两测压断面间水头损失符号反转（正向 $h = \\Delta\\frac{v^2}{2g} + h_{w1\\text{-}2}$ vs 反向 $h = \\Delta\\frac{v^2}{2g} - h_{w2\\text{-}1}$），这也正是所有文丘里流量计外壳上均铸有流向箭头的根本原因。",
                "chapter": 3,
                "kps": ["伯努利方程测流", "文丘里流量计", "边界层分离"],
                "method": "文丘里测压管水头差推导与边界层分离判别法",
                "difficulty": 3,
                "rubric": [
                    {"label": "联立 1-1 与 2-2 断面能量方程和连续性方程，完整推导出文丘里流量计测流公式", "pts": 3},
                    {"label": "明确回答倾斜状态可以正常测流，并说明流量仅取决于测压管水头差 h 而与管轴倾角无关", "pts": 2},
                    {"label": "明确回答水流由右向左时不能正常测流，并从大锥角反向急扩引发边界层分离、涡流损失及系数失效说明原因", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2020-06",
                "year": 2020,
                "no": 6,
                "type": "calc",
                "score": 10,
                "title": "直角型自动翻板闸门临界自动开启水深计算",
                "stem": "如图所示自动翻板门，试求：上游水深 $h$ 为多少时该门能够自动打开？假设忽略门重。",
                "note": "",
                "figures": [
                    {"src": "figures/q06_orig.png", "caption": "题 6 图　直角型自动翻板门构造示意图"}
                ],
                "shortAnswer": "h = √3 m ≈ 1.73 m（当 h > 1.73 m 时自动翻开）",
                "judgeAnswer": None,
                "answer": "当上游水深达到 $h = \\sqrt{3}\\,\\mathrm{m} \\approx 1.73\\,\\mathrm{m}$（即 $h > 1.73\\,\\mathrm{m}$）时，该自动翻板门能够自动打开。",
                "analysis": "**1. 直角翻板门受力结构与启闭机理分析**\n\n取垂直图面方向单位门宽 $b = 1\\,\\mathrm{m}$ 分析（受力见解图 6）。直角刚性翻板门 $ABC$ 绕角点铰轴 $B$ 转动，水平底板长 $L = \\overline{BC} = 1\\,\\mathrm{m}$，右端 $C$ 上方设有挡坎限制闸门逆时针上翘，下方弧形底室与上游水体连通（水深为 $h$）：\n- **铅直面板 $AB$ 受向右的水平静水总压力 $P_x$**（产生绕铰 $B$ **顺时针开启力矩**）：\n\n$$\nP_x = \\frac{1}{2}\\rho g h^2 b\n$$\n\n面板上压强呈三角形分布（水面处为 $0$，铰 $B$ 处为 $\\rho g h$），故压心位于铰轴 $B$ 上方力臂 $e_1 = \\frac{h}{3}$ 处。\n- **水平底板 $BC$ 受底室连通水体向上的均布静水总压力 $P_z$**（产生绕铰 $B$ **逆时针关闭力矩**）：\n\n$$\nP_z = \\rho g h (L b)\n$$\n\n底板处于同一水深 $h$ 水平面上，压强均匀分布为 $p = \\rho g h$，故合力作用在 $BC$ 中点，距铰轴 $B$ 的力臂为 $e_2 = \\frac{L}{2} = 0.5\\,\\mathrm{m}$。\n\n**2. 列绕铰轴 $B$ 的临界力矩平衡方程求解 $h$**\n\n忽略门重，当上游水深较小时，$M_{\\text{关}} > M_{\\text{开}}$，$C$ 端紧顶上方挡坎保持关闭；当水深升至临界开启水深 $h$ 时，$C$ 端挡坎反力恰减为零，顺时针开启力矩等于逆时针关闭力矩：\n\n$$\n\\sum M_B = 0 \\implies P_x \\cdot e_1 = P_z \\cdot e_2\n$$\n\n代入各物理量表达式：\n\n$$\n\\left(\\frac{1}{2}\\rho g h^2 b\\right) \\cdot \\frac{h}{3} = (\\rho g h L b) \\cdot \\frac{L}{2}\n$$\n\n约去公因式 $\\frac{1}{2}\\rho g h b$（$h > 0$），化简得：\n\n$$\n\\frac{h^2}{3} = L^2 \\implies h = \\sqrt{3}\\,L = \\sqrt{3} \\times 1\\,\\mathrm{m} \\approx 1.732\\,\\mathrm{m} \\approx 1.73\\,\\mathrm{m}\n$$\n\n当上游水深超过 $1.73\\,\\mathrm{m}$ 时，$M_{\\text{开}} > M_{\\text{关}}$，翻板门即绕铰 $B$ 顺时针自动翻倒泄洪。",
                "analysisFigures": [
                    {"src": "figures/q06_sol.png", "caption": "解图 6　直角自动翻板门绕铰 B 的静水压力分布与力矩平衡图"}
                ],
                "pitfalls": "1. 三角形压强分布合力作用点位于水面以下 $\\frac{2}{3}h$ 处，故相对于底部铰轴 $B$ 的力臂是 **$e_1 = \\frac{1}{3}h$**，切勿误代 $\\frac{2}{3}h$！\n2. 水平底板 $BC$ 承受均布向上水压 $\\rho g h$，其关闭力矩随 $h$ 成 $1$ 次方增长（$\\propto h$），而铅直板开启力矩随 $h$ 成 $3$ 次方增长（$\\propto h^3$），这正是低水位自封挡水、高水位自动翻开泄水的力学原理。",
                "chapter": 2,
                "kps": ["平面静水总压力", "压心与力矩平衡", "自动翻板闸门"],
                "method": "平面静水压力分块合成与绕铰力矩平衡法",
                "difficulty": 2,
                "rubric": [
                    {"label": "写出铅直板水平静水压力 Px = (1/2)ρgh²b 及其对铰 B 的力臂 e1 = h/3", "pts": 3},
                    {"label": "写出水平底板向上静水压力 Pz = ρghLb 及其对铰 B 的力臂 e2 = L/2 = 0.5 m", "pts": 3},
                    {"label": "列绕铰 B 的临界开启力矩平衡方程 Px·e1 = Pz·e2，解得 h = √3 m ≈ 1.73 m", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2020-07",
                "year": 2020,
                "no": 7,
                "type": "calc",
                "score": 15,
                "title": "30° 斜面上挡水圆柱体所受静水总压力的水平分力与铅垂分力计算",
                "stem": "如图所示，一直径 $D = 4\\,\\mathrm{m}$ 的圆柱在与水平面成 $30^{\\circ}$ 角的斜面上挡水，水面与圆柱顶齐平，试求作用在 $1\\,\\mathrm{m}$ 长圆柱上静水总压力的水平分力和铅垂分力。",
                "note": "",
                "figures": [
                    {"src": "figures/q07_orig.png", "caption": "题 7 图　30° 斜面上挡水圆柱体"}
                ],
                "shortAnswer": "水平分力 Px = 68.32 kN（水平向右；若取 g=9.80 m/s² 则为 68.25 kN）；铅垂分力 Pz = 100.03 kN（铅直向上；若取 g=9.80 m/s² 则为 99.92 kN）。",
                "judgeAnswer": None,
                "answer": "作用在 $1\\,\\mathrm{m}$ 长圆柱上静水总压力的：\n- **水平分力**：$P_x \\approx 68.32\\,\\mathrm{kN}$（方向**水平向右**；若取 $g = 9.80\\,\\mathrm{m/s^2}$ 则为 $68.25\\,\\mathrm{kN}$）；\n- **铅垂分力**：$P_z \\approx 100.03\\,\\mathrm{kN}$（方向**铅直向上**；若取 $g = 9.80\\,\\mathrm{m/s^2}$ 则为 $99.92\\,\\mathrm{kN}$）。",
                "analysis": "**1. 确定受压曲面范围及切点淹没水深 $h$**\n\n已知圆柱半径 $R = \\frac{D}{2} = 2\\,\\mathrm{m}$，计算长度 $b = 1\\,\\mathrm{m}$（几何与压力体关系见解图 7）。设圆柱圆心为 $O$，顶点为 $A$（与自由水面齐平），最左点为 $B$，最低点为 $C$，圆柱与倾角 $\\alpha = 30^{\\circ}$ 斜面的切点为 $E$，则受压弧面为 $A\\text{—}B\\text{—}C\\text{—}E$。\n\n因半径 $OE$ 垂直于 $30^{\\circ}$ 斜面，故 $OE$ 与铅垂向下方向夹角恰为 $30^{\\circ}$，切点 $E$ 在自由水面以下的铅直淹没水深为：\n\n$$\nh = R + R\\cos 30^{\\circ} = 2 + 2 \\times \\frac{\\sqrt{3}}{2} = 2 + \\sqrt{3} \\approx 3.7321\\,\\mathrm{m}\n$$\n\n**2. 计算静水总压力的水平分力 $P_x$**\n\n弧段 $ABC$（水深 $0 \\to 2R$）受向右水平压力，而底部折返弧段 $CE$（水深 $h \\to 2R$）位于圆心右侧、受向左水平压力，两段在水深 $[h, 2R]$ 区间的水平投影压力严格相消，故净有效铅直投影面即为自由水面至切点 $E$ 的矩形（高 $h = 3.7321\\,\\mathrm{m}$、宽 $b = 1\\,\\mathrm{m}$，形心水深 $h_c = \\frac{h}{2}$）。取 $g = 9.81\\,\\mathrm{m/s^2}$：\n\n$$\nP_x = \\rho g h_c (h b) = \\frac{1}{2}\\rho g h^2 b = \\frac{1}{2} \\times 1000 \\times 9.81 \\times (2 + \\sqrt{3})^2 \\times 1 \\approx 68318.3\\,\\mathrm{N} \\approx 68.32\\,\\mathrm{kN}\n$$\n\n方向**水平向右**。\n\n**3. 计算静水总压力的铅垂分力 $P_z$**\n\n分析各弧段铅垂压力体（过切点 $E$ 作铅垂线交自由水面延长线于 $F$）：\n- 上半弧 $AB$ 受向下的实压力体体积：$V_{\\text{下}} = b\\left(R^2 - \\frac{1}{4}\\pi R^2\\right)$；\n- 下部弧 $BCE$ 受向上的虚压力体体积：$V_{\\text{上}}$ 等于曲线 $BCE$、铅垂线 $EF$ 与自由水面线 $FA$ 所围总体积；\n- 将上下两部分叠加相减，左半侧矩形恰好消去，净向上的压力体横断面面积 $\\Omega$ 由三块简单几何图形组成（见解图 7b）：\n  1. 左侧半圆 $ABC$：$\\Omega_1 = \\frac{1}{2}\\pi R^2 = \\frac{1}{2}\\pi \\times 2^2 = 2\\pi \\approx 6.2832\\,\\mathrm{m^2}$；\n  2. 圆心角为 $30^{\\circ}$ 的扇形 $COE$：$\\Omega_2 = \\frac{30^{\\circ}}{360^{\\circ}}\\pi R^2 = \\frac{1}{12}\\pi \\times 2^2 = \\frac{\\pi}{3} \\approx 1.0472\\,\\mathrm{m^2}$；\n  3. 直角梯形 $AOEF$（上底 $\\overline{AO} = R = 2\\,\\mathrm{m}$，下底 $\\overline{FE} = h = 2 + \\sqrt{3}\\,\\mathrm{m}$，水平高 $R\\sin 30^{\\circ} = 1\\,\\mathrm{m}$）：\n\n$$\n\\Omega_3 = \\frac{1}{2}(R + h) R\\sin 30^{\\circ} = \\frac{1}{2}\\left(2 + 2 + \\sqrt{3}\\right) \\times 1 = 2 + \\frac{\\sqrt{3}}{2} \\approx 2.8660\\,\\mathrm{m^2}\n$$\n\n故净压力体体积 $V$ 与铅垂分力 $P_z$ 为：\n\n$$\nV = (\\Omega_1 + \\Omega_2 + \\Omega_3) b = (6.2832 + 1.0472 + 2.8660) \\times 1 \\approx 10.1964\\,\\mathrm{m^3}\n$$\n\n$$\nP_z = \\rho g V = 1000 \\times 9.81 \\times 10.1964 \\approx 100026.7\\,\\mathrm{N} \\approx 100.03\\,\\mathrm{kN}\n$$\n\n因下部向上虚压力体大于上部向下实压力体，净铅垂分力方向**铅直向上**。\n\n（注：若取 $\\pi \\approx 3.14$、$h \\approx 3.73\\,\\mathrm{m}$、$g = 9.81\\,\\mathrm{m/s^2}$，中间四舍五入得 $P_x \\approx 68.24\\,\\mathrm{kN}$、$V \\approx 10.19\\,\\mathrm{m^3}$、$P_z \\approx 99.96\\,\\mathrm{kN}$；若取 $g = 9.80\\,\\mathrm{m/s^2}$ 精确值为 $P_x = 68.25\\,\\mathrm{kN}$、$P_z = 99.92\\,\\mathrm{kN}$。）",
                "analysisFigures": [
                    {"src": "figures/q07_sol.png", "caption": "解图 7　30° 斜面上挡水圆柱的水平投影面高度与净铅垂压力体分块图"}
                ],
                "pitfalls": "1. **水平分力头号陷阱**：切忌误把整个圆柱直径 $D = 4\\,\\mathrm{m}$ 当作水平投影高度！圆柱底点 $C$ 右侧至切点 $E$ 的小弧段 $CE$ 同样浸在水中且受向左的水压力，抵消后净有效投影高度仅为水面至切点 $E$ 的铅直距离 $h = R(1 + \\cos 30^{\\circ}) \\approx 3.732\\,\\mathrm{m}$。\n2. **铅垂分力拆块技巧**：过圆心连接切点 $OE$，将右侧不规则曲边区域拆成“$30^{\\circ}$ 扇形 $COE$ + 直角梯形 $AOEF$”，无需任何微积分即可一步精确算出压力体体积！",
                "chapter": 2,
                "kps": ["平面与曲面静水总压力", "压力体体积计算", "折返曲面投影抵消"],
                "method": "等效自由液面+水平投影与铅垂压力体合成法",
                "difficulty": 4,
                "rubric": [
                    {"label": "正确求出切点 E 的淹没深度 h = R(1 + cos30°) ≈ 3.732 m 及向右水平分力 Px = (1/2)ρgh²b ≈ 68.32 kN", "pts": 6},
                    {"label": "正确将净压力体分解为半圆、30° 扇形与直角梯形三部分，算出净体积 V ≈ 10.20 m³", "pts": 5},
                    {"label": "算出铅垂分力大小 Pz = ρgV ≈ 100.03 kN 并明确指明 Px 水平向右、Pz 铅直向上", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2020-08",
                "year": 2020,
                "no": 8,
                "type": "calc",
                "score": 15,
                "title": "离心泵最大允许安装高程与带动水泵的动力机械功率计算",
                "stem": "如图所示用离心泵将湖水抽到水池，流量 $Q$ 为 $0.2\\,\\mathrm{m^3/s}$，湖面高程 $\\nabla_1$ 为 $85.0\\,\\mathrm{m}$，水池水面高程 $\\nabla_3$ 为 $105.0\\,\\mathrm{m}$；吸水管直径 $d_1$ 为 $500\\,\\mathrm{mm}$，长 $l_1$ 为 $10\\,\\mathrm{m}$，水泵的允许真空值 $h_v$ 为 $4.5\\,\\mathrm{m}$，吸水管底阀局部水头损失系数 $\\zeta_e = 2.5$，$90^{\\circ}$ 弯头局部水头损失系数 $\\zeta_b = 0.3$，水泵入口前的渐变收缩段局部水头损失系数 $\\zeta_g = 0.1$，吸水管沿程阻力系数 $\\lambda = 0.022$；压力管道采用铸铁管，其直径 $d_2$ 为 $500\\,\\mathrm{mm}$，长度 $l_2$ 为 $1000\\,\\mathrm{m}$，$n = 0.013$，压力管按长管计算，水泵效率 $\\eta = 70\\%$。试确定：\n\n（1）水泵最大允许安装高程 $\\nabla_2$；\n\n（2）带动水泵的动力机械功率。",
                "note": "",
                "figures": [
                    {"src": "figures/q08_orig.png", "caption": "题 8 图　离心泵抽水装置管路布置图"}
                ],
                "shortAnswer": "（1）水泵最大允许安装高程 ∇2 = 89.27 m；（2）动力机械功率 N = 64.42 kW（若取 g=9.80 m/s² 则为 64.35 kW）。",
                "judgeAnswer": None,
                "answer": "（1）水泵最大允许安装高程 $\\nabla_2 = 89.27\\,\\mathrm{m}$；\n\n（2）带动水泵的动力机械功率 $N \\approx 64.42\\,\\mathrm{kW}$（若取 $g = 9.80\\,\\mathrm{m/s^2}$ 则为 $64.35\\,\\mathrm{kW}$）。",
                "analysis": "**（1）确定水泵最大允许安装高程 $\\nabla_2$**\n\n吸水管内径 $d_1 = 0.50\\,\\mathrm{m}$，过水断面面积与管内平均流速为：\n\n$$\nA_1 = \\frac{\\pi}{4} d_1^2 = \\frac{\\pi}{4} \\times 0.50^2 \\approx 0.19635\\,\\mathrm{m^2}, \\qquad v_1 = \\frac{Q}{A_1} = \\frac{0.2}{0.19635} \\approx 1.0186\\,\\mathrm{m/s}\n$$\n\n取 $g = 9.81\\,\\mathrm{m/s^2}$、$\\alpha = 1.0$，吸水管流速水头及吸水管总水头损失 $h_{w1}$ 分别为：\n\n$$\n\\frac{v_1^2}{2g} = \\frac{1.0186^2}{2 \\times 9.81} \\approx 0.05288\\,\\mathrm{m}\n$$\n\n$$\nh_{w1} = \\left(\\lambda\\frac{l_1}{d_1} + \\zeta_e + \\zeta_b + \\zeta_g\\right)\\frac{v_1^2}{2g} = \\left(0.022 \\times \\frac{10}{0.50} + 2.5 + 0.3 + 0.1\\right) \\times 0.05288 = 3.34 \\times 0.05288 \\approx 0.1766\\,\\mathrm{m}\n$$\n\n对吸水湖面（高程 $\\nabla_1 = 85.0\\,\\mathrm{m}$，$p_1 = 0$，$v_0 \\approx 0$）与水泵进口断面（高程 $\\nabla_2$，最大允许真空高度 $h_v = -\\frac{p_s}{\\rho g} = 4.5\\,\\mathrm{m}$）列能量方程：\n\n$$\n\\nabla_1 = \\nabla_2 - h_v + \\frac{v_1^2}{2g} + h_{w1}\n$$\n\n解得最大允许吸水地形高度 $z_{s,\\max}$ 与最大允许安装高程 $\\nabla_2$：\n\n$$\nz_{s,\\max} = h_v - \\left(\\frac{v_1^2}{2g} + h_{w1}\\right) = 4.5 - (0.05288 + 0.1766) = 4.2705\\,\\mathrm{m} \\approx 4.27\\,\\mathrm{m}\n$$\n\n$$\n\\nabla_2 = \\nabla_1 + z_{s,\\max} = 85.0 + 4.27 = 89.27\\,\\mathrm{m}\n$$\n\n**（2）计算水泵总扬程 $H_p$ 与动力机械功率 $N$**\n\n铸铁压力管道直径 $d_2 = 0.50\\,\\mathrm{m}$，面积 $A_2 = A_1 = 0.19635\\,\\mathrm{m^2}$，流速 $v_2 = v_1 = 1.0186\\,\\mathrm{m/s}$，满管水力半径 $R_2 = \\frac{d_2}{4} = 0.125\\,\\mathrm{m}$，糙率 $n = 0.013$。压力管按长管计算（忽略压力管局部损失及出口流速水头），由谢才—曼宁公式求流量模数 $K_2$ 与沿程水头损失 $h_{f2}$：\n\n$$\nC_2 = \\frac{1}{n} R_2^{1/6} = \\frac{1}{0.013} \\times 0.125^{1/6} \\approx 54.393\\,\\mathrm{m^{1/2}/s}, \\qquad K_2 = A_2 C_2 \\sqrt{R_2} \\approx 3.7760\\,\\mathrm{m^3/s}\n$$\n\n$$\nh_{f2} = \\frac{Q^2}{K_2^2} l_2 = \\left(\\frac{0.2}{3.7760}\\right)^2 \\times 1000 \\approx 2.8055\\,\\mathrm{m} \\approx 2.81\\,\\mathrm{m}\n$$\n\n对湖面与水池水面列总流能量方程，水泵所需提供的总扬程为：\n\n$$\nH_p = (\\nabla_3 - \\nabla_1) + h_{w1} + h_{f2} = (105.0 - 85.0) + 0.1766 + 2.8055 = 22.9821\\,\\mathrm{m} \\approx 22.98\\,\\mathrm{m}\n$$\n\n已知水泵效率 $\\eta = 70\\%$，故带动水泵所需的动力机械功率（轴功率）为：\n\n$$\nN = \\frac{\\rho g Q H_p}{1000\\,\\eta} = \\frac{1000 \\times 9.81 \\times 0.2 \\times 22.9821}{1000 \\times 0.70} \\approx 64.42\\,\\mathrm{kW}\n$$\n\n（注：若取 $g = 9.80\\,\\mathrm{m/s^2}$，得 $N \\approx 64.35\\,\\mathrm{kW}$；若先算达西系数 $\\lambda_2 = \\frac{8g}{C_2^2}$ 四舍五入取 $\\lambda_2 \\approx 0.027$，则 $h_{f2} \\approx 2.86\\,\\mathrm{m}$、$N \\approx 64.57\\,\\mathrm{kW}$。）",
                "analysisFigures": [],
                "pitfalls": "1. 允许真空值 $h_v = 4.5\\,\\mathrm{m}$ 意味着泵入口压强水头为负值 $\\frac{p_s}{\\rho g} = -4.5\\,\\mathrm{m}$，且计算最大允许安装高程时切勿漏减泵入口流速水头 $\\frac{v_1^2}{2g}$！\n2. 动力机械功率即水泵轴功率，单位是**功率单位 $\\mathrm{kW}$（千瓦）**，切忌笔误写成力的单位 $\\mathrm{kN}$！",
                "chapter": 6,
                "kps": ["水泵最大允许安装高程", "水泵扬程与轴功率", "曼宁公式"],
                "method": "允许真空度定安装高程+长管扬程求功率",
                "difficulty": 4,
                "rubric": [
                    {"label": "算出吸水管流速 v1 ≈ 1.02 m/s、流速水头 0.053 m 及吸水管水头损失 hw1 ≈ 0.177 m", "pts": 4},
                    {"label": "列湖面至泵入口能量方程求得最大允许吸水高度 zs ≈ 4.27 m 及安装高程 ∇2 = 89.27 m", "pts": 4},
                    {"label": "由曼宁公式算出铸铁压力长管沿程水头损失 hf2 ≈ 2.81 m 及水泵总扬程 Hp ≈ 22.98 m", "pts": 4},
                    {"label": "由功率公式 N = ρgQHp/(1000η) 求得带动水泵的动力机械功率 N ≈ 64.42 kW", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2020-09",
                "year": 2020,
                "no": 9,
                "type": "calc",
                "score": 15,
                "title": "垂直平板截流部分自由射流的作用力与偏转角计算",
                "stem": "如图所示将一平板放置在自由射流之中，并且垂直于射流的轴线，该平板截去射流流量的一部分 $Q_1$，射流的其余部分偏转一角度 $\\theta$，已知：$v = 30\\,\\mathrm{m/s}$，$Q = 36\\,\\mathrm{L/s}$，$Q_1 = 12\\,\\mathrm{L/s}$，试求：\n\n（1）不计摩擦力时射流对平板的作用力；\n\n（2）射流的偏转角 $\\theta$ 值。",
                "note": "",
                "figures": [
                    {"src": "figures/q09_orig.png", "caption": "题 9 图　垂直平板部分截流与射流偏转平面图"}
                ],
                "shortAnswer": "（1）射流对平板的作用力大小 Fx = 456.46 N，方向沿原射流方向垂直指向平板（水平向右）；（2）射流偏转角 θ = 30°。",
                "judgeAnswer": None,
                "answer": "（1）不计摩擦力时射流对平板的作用力大小为 **$456.46\\,\\mathrm{N}$**，方向**沿 $x$ 轴正方向（水平向右，垂直指向平板板面）**；\n\n（2）射流的偏转角 **$\\theta = 30^{\\circ}$**。",
                "analysis": "**1. 由连续性方程与伯努利方程确定各股射流流量与流速**\n\n由题 9 图知流动位于水平面内（“平面图”，各点高差 $\\Delta z = 0$），且为大气中自由射流（各进出流渐变流断面相对压强均为 $0$）。不计摩擦与水头损失，由伯努利方程得各分支流速大小相等：\n\n$$\nv_1 = v_2 = v = 30\\,\\mathrm{m/s}\n$$\n\n将流量换算为国际单位：$Q = 36\\,\\mathrm{L/s} = 0.036\\,\\mathrm{m^3/s}$，$Q_1 = 12\\,\\mathrm{L/s} = 0.012\\,\\mathrm{m^3/s}$。由连续性方程得偏转支流流量：\n\n$$\nQ_2 = Q - Q_1 = 0.036 - 0.012 = 0.024\\,\\mathrm{m^3/s} \\quad (24\\,\\mathrm{L/s})\n$$\n\n**2. 先列 $y$ 轴（平行于平板）动量方程求偏转角 $\\theta$**\n\n选取包围分流区的控制体（见解图 9），按题图规定水平向右为 $+x$ 轴、平行于平板向上为 $+y$ 轴。因平板垂直于 $x$ 轴且不计板面切向摩擦力，故平板对水体仅有沿 $-x$ 方向的法向反力 $R_x$，而在 $y$ 轴方向无任何外力（$\\sum F_y = 0$）。取 $\\beta = 1.0$，列 $y$ 方向恒定总流动量方程：\n\n$$\n0 = \\rho Q_2 (v_2 \\sin\\theta) + \\rho Q_1 (-v_1) - \\rho Q \\cdot 0\n$$\n\n代入 $v_1 = v_2 = v$，解得射流偏转角 $\\theta$：\n\n$$\n\\sin\\theta = \\frac{Q_1}{Q_2} = \\frac{0.012}{0.024} = 0.5 \\implies \\theta = 30^{\\circ}\n$$\n\n**3. 再列 $x$ 轴（垂直于平板）动量方程求平板受力**\n\n沿 $+x$ 轴方向列恒定总流动量方程（出流 $Q_1$ 沿 $-y$ 方向，在 $x$ 轴速度分量为 $0$；出流 $Q_2$ 在 $+x$ 轴速度分量为 $v_2 \\cos\\theta$）：\n\n$$\n-R_x = \\rho Q_2 (v_2 \\cos\\theta) + \\rho Q_1 \\cdot 0 - \\rho Q v\n$$\n\n代入数值（$\\rho = 1000\\,\\mathrm{kg/m^3}$，$\\cos 30^{\\circ} = \\frac{\\sqrt{3}}{2}$）：\n\n$$\nR_x = \\rho v (Q - Q_2 \\cos 30^{\\circ}) = 1000 \\times 30 \\times \\left(0.036 - 0.024 \\times \\frac{\\sqrt{3}}{2}\\right) = 1080 - 360\\sqrt{3} \\approx 456.46\\,\\mathrm{N}\n$$\n\n$R_x > 0$ 表明平板对控制体水流的反力沿 $-x$ 方向（水平向左）。由牛顿第三定律，射流对平板的作用力 $F_x = R_x \\approx 456.46\\,\\mathrm{N}$，方向**沿 $+x$ 轴正方向（水平向右，垂直指向平板）**。",
                "analysisFigures": [
                    {"src": "figures/q09_sol.png", "caption": "解图 9　垂直平板部分截流控制体与 x、y 正交方向动量平衡图"}
                ],
                "pitfalls": "1. 虽然题干先问第（1）问“作用力”、后问第（2）问“偏转角 $\\theta$”，但 $x$ 向动量方程含有未知的 $\\cos\\theta$！解题时应**先列切向 $y$ 轴动量方程求出 $\\theta = 30^{\\circ}$，再代回法向 $x$ 轴动量方程求 $F_x$**。\n2. 流量给定单位为 $\\mathrm{L/s}$，代入动量方程前务必乘以 $10^{-3}$ 换算为 $\\mathrm{m^3/s}$！",
                "chapter": 3,
                "kps": ["恒定总流动量方程", "自由射流偏转与截流", "恒定总流连续性方程"],
                "method": "能量方程求流速+动量方程切法向正交分解法",
                "difficulty": 3,
                "rubric": [
                    {"label": "由连续性方程与能量方程确定 Q2 = Q - Q1 = 0.024 m³/s 及 v1 = v2 = v = 30 m/s", "pts": 3},
                    {"label": "沿平行平板的 y 轴列动量方程 0 = ρQ2v·sinθ - ρQ1v，解得 sinθ = 0.5、偏转角 θ = 30°", "pts": 6},
                    {"label": "沿垂直平板的 x 轴列动量方程求得射流对平板作用力 Fx ≈ 456.46 N 并指明方向水平向右", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2020-10",
                "year": 2020,
                "no": 10,
                "type": "calc",
                "score": 15,
                "title": "水塔长管并联加接同径支管使出口流量增加 30% 的支管长度计算",
                "stem": "如图所示管路系统，出口流入大气中，已知管长 $l = 150\\,\\mathrm{m}$，为了使出口流量增加 $30\\%$，如图中虚线所示加一根直径相同、材质相同的支管，支管的起始端接在水塔底部，终端接在原管道的中间点 $B$ 处，按长管计算，试求：该支管的长度 $x$。",
                "note": "",
                "figures": [
                    {"src": "figures/q10_orig.png", "caption": "题 10 图　水塔长管加接并联虚线支管系统示意图"}
                ],
                "shortAnswer": "x ≈ 42.09 m",
                "judgeAnswer": None,
                "answer": "该新增并联支管的长度 $x \\approx 42.09\\,\\mathrm{m}$。",
                "analysis": "**1. 建立加设支管前的原长管水头损失方程**\n\n因原管道与新增虚线支管的管径 $d$、材质粗糙度完全相同，设单位管长的比阻为常数 $s_0$（按长管计算，忽略局部水头损失与出口流速水头）。设水塔恒定总作用水头为 $H$，改造前单一管道（总长 $l = 150\\,\\mathrm{m}$）通过的流量为 $Q_0$，则有：\n\n$$\nH = s_0 l Q_0^2\n$$\n\n**2. 分析加设支管后的“先并联、后串联”管网水力关系**\n\n在原管道中间点 $B$ 处接入支管后，原管道被节点 $B$ 等分为上半段 $l_1 = \\frac{l}{2} = 75\\,\\mathrm{m}$ 和下半段 $l_2 = \\frac{l}{2} = 75\\,\\mathrm{m}$：其中**原管上半段（长 $l/2$，流量 $Q_1$）与新增支管（长 $x$，流量 $Q_x$）构成并联管路**，汇合于节点 $B$ 后经下半段干管（长 $l/2$）排入大气（水头线见解图 10）。\n\n改造后要求出口总流量增加 $30\\%$，即下游干管 $BC$ 流量为 $Q^{\\prime} = 1.30 Q_0$，故下半段干管沿程水头损失为：\n\n$$\nh_{f,BC} = s_0 \\frac{l}{2} (Q^{\\prime})^2 = s_0 \\frac{l}{2} (1.30 Q_0)^2 = \\frac{1.69}{2} s_0 l Q_0^2 = 0.845\\,H\n$$\n\n由总作用水头平衡 $H = h_{f,\\text{并}} + h_{f,BC}$，水塔至中间节点 $B$ 之间的并联管段水头损失为：\n\n$$\nh_{f,AB} = h_{f,x} = H - h_{f,BC} = (1 - 0.845)H = 0.155\\,H = 0.155\\,s_0 l Q_0^2\n$$\n\n**3. 由并联等水头损失与节点连续性方程求解支管长度 $x$**\n\n对原管上半段（长 $l/2$）应用水头损失关系：\n\n$$\ns_0 \\frac{l}{2} Q_1^2 = 0.155\\,s_0 l Q_0^2 \\implies Q_1 = \\sqrt{0.31}\\,Q_0 \\approx 0.55678\\,Q_0\n$$\n\n由节点 $B$ 流量连续性方程 $Q_1 + Q_x = Q^{\\prime} = 1.30 Q_0$，得新增支管分担的流量为：\n\n$$\nQ_x = Q^{\\prime} - Q_1 = \\left(1.30 - \\sqrt{0.31}\\right) Q_0 \\approx 0.74322\\,Q_0\n$$\n\n再对新增支管（长 $x$）应用并联水头损失方程 $s_0 x Q_x^2 = 0.155\\,s_0 l Q_0^2$，解得支管长度 $x$：\n\n$$\nx = \\frac{0.155\\,l}{\\left(1.30 - \\sqrt{0.31}\\right)^2} = \\frac{0.155 \\times 150}{0.743224^2} = \\frac{23.25}{0.55238} \\approx 42.0905\\,\\mathrm{m} \\approx 42.09\\,\\mathrm{m}\n$$\n\n（校验：并联段等效比阻 $S_{\\text{并}} = \\frac{s_0}{\\left(\\frac{1}{\\sqrt{75}} + \\frac{1}{\\sqrt{42.0905}}\\right)^2} = 13.7574\\,s_0$，总阻抗 $S_{\\text{总}} = (13.7574 + 75)s_0 = 88.7574\\,s_0$，流量比 $\\sqrt{\\frac{150}{88.7574}} = \\sqrt{1.6900} = 1.3000$，完全精确吻合！）",
                "analysisFigures": [
                    {"src": "figures/q10_sol.png", "caption": "解图 10　水塔串联—并联长管系统改造前后的测压管水头线与分流关系"}
                ],
                "pitfalls": "**本题头号致命误区**：加设虚线支管后，水塔至节点 $B$ 的**原管道上半段（长 $75\\,\\mathrm{m}$）依然畅通输水**，与新增支管形成**并联分流**（$Q_1 + Q_x = 1.3 Q_0$）！切忌误以为原上半段作废断流而将总流量 $1.3 Q_0$ 全部强塞进支管 $x$ 列串联方程 $H = s_0(x + l/2)(1.3 Q_0)^2$（那样会算出违背几何与并联水力规律的错误结果 $13.76\\,\\mathrm{m}$）。",
                "chapter": 6,
                "kps": ["并联与串联长管计算", "节点流量连续性", "长管水力坡度与节点水头"],
                "method": "长管并联分流与节点水头平衡分析",
                "difficulty": 4,
                "rubric": [
                    {"label": "写出改造前长管方程 H = s0·l·Q0²，并求出改造后下游半段水头损失 hf,BC = 0.845H", "pts": 4},
                    {"label": "得出上游并联段水头损失 hf,并 = 0.155H，求出原上半段分流流量 Q1 = √0.31·Q0 ≈ 0.557Q0", "pts": 5},
                    {"label": "由节点连续性得支管流量 Qx = (1.3 - √0.31)Q0，代入 s0·x·Qx² = 0.155H 解得 x ≈ 42.09 m", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2020-11",
                "year": 2020,
                "no": 11,
                "type": "calc",
                "score": 10,
                "title": "浆砌块石矩形断面长直明渠均匀流底坡计算",
                "stem": "有一浆砌块石的矩形断面长渠道，已知：底宽 $b = 3.2\\,\\mathrm{m}$，渠中水深 $h_0 = 1.6\\,\\mathrm{m}$，粗糙系数 $n = 0.025$，通过的流量 $Q = 6\\,\\mathrm{m^3/s}$，试求该渠道的底坡 $i$。",
                "note": "",
                "figures": [],
                "shortAnswer": "i ≈ 0.00116（或 1.16×10⁻³）",
                "judgeAnswer": None,
                "answer": "该矩形长渠道的底坡 $i \\approx 1.16 \\times 10^{-3}$（即 $0.00116$，约 $\\frac{1}{865}$）。",
                "analysis": "**1. 计算矩形明渠过水断面水力要素**\n\n矩形长直渠道中形成明渠恒定均匀流（正常水深 $h_0 = 1.6\\,\\mathrm{m}$，注意到 $\\frac{b}{h_0} = \\frac{3.2}{1.6} = 2$，恰为矩形水力最佳断面！）：\n- 过水断面面积：\n\n$$\nA = b h_0 = 3.2 \\times 1.6 = 5.12\\,\\mathrm{m^2}\n$$\n\n- 湿周（不含自由水面）：\n\n$$\n\\chi = b + 2 h_0 = 3.2 + 2 \\times 1.6 = 6.40\\,\\mathrm{m}\n$$\n\n- 水力半径：\n\n$$\nR = \\frac{A}{\\chi} = \\frac{5.12}{6.40} = 0.80\\,\\mathrm{m} \\quad \\left(= \\frac{h_0}{2}\\right)\n$$\n\n**2. 由谢才—曼宁公式求谢才系数 $C$ 与渠道底坡 $i$**\n\n由曼宁公式计算谢才系数 $C$：\n\n$$\nC = \\frac{1}{n} R^{1/6} = \\frac{1}{0.025} \\times 0.80^{1/6} = 40 \\times 0.96349 \\approx 38.54\\,\\mathrm{m^{1/2}/s}\n$$\n\n由明渠均匀流流量公式 $Q = A C \\sqrt{R i}$，反解渠道底坡 $i$：\n\n$$\ni = \\frac{Q^2}{A^2 C^2 R} = \\frac{n^2 Q^2}{A^2 R^{4/3}} = \\frac{0.025^2 \\times 6^2}{5.12^2 \\times 0.80^{4/3}} = \\frac{0.0225}{26.2144 \\times 0.74264} \\approx 1.1557 \\times 10^{-3} \\approx 1.16 \\times 10^{-3}\n$$",
                "analysisFigures": [],
                "pitfalls": "1. 计算明渠湿周 $\\chi$ 时只计渠底和两侧渠壁（$\\chi = b + 2h_0 = 6.40\\,\\mathrm{m}$），切忌把顶面自由水面宽度 $b$ 加进去！\n2. 反解底坡 $i$ 时注意 $Q = K\\sqrt{i}$ 两边需要**平方**（$i = Q^2 / K^2$），切勿漏掉平方。",
                "chapter": 7,
                "kps": ["曼宁公式", "谢才公式", "明渠均匀流底坡计算"],
                "method": "明渠均匀流谢才—曼宁公式直接反解法",
                "difficulty": 1,
                "rubric": [
                    {"label": "正确计算出矩形断面面积 A = 5.12 m²、湿周 χ = 6.40 m 及水力半径 R = 0.80 m", "pts": 4},
                    {"label": "由曼宁公式计算出谢才系数 C = (1/n)R^(1/6) ≈ 38.54 m^(1/2)/s（或流量模数 K ≈ 176.49 m³/s）", "pts": 3},
                    {"label": "代入明渠均匀流公式 Q = AC√(Ri) 解得渠道底坡 i ≈ 1.16×10⁻³", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2020-12",
                "year": 2020,
                "no": 12,
                "type": "calc",
                "score": 10,
                "title": "不可压缩平面势流待定常数确定与流场两点压强差计算",
                "stem": "已知平面流动的流速势函数 $\\varphi = 0.04x^3 + axy^2$，$x$，$y$ 单位为 $\\mathrm{m}$，$\\varphi$ 的单位为 $\\mathrm{m^2/s}$，试求：\n\n（1）常数 $a$；\n\n（2）点 $A(0,0)$ 和点 $B(3,4)$ 间的压强差，设流体的密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$。",
                "note": "",
                "figures": [],
                "shortAnswer": "（1）a = -0.12；（2）pA - pB = 4500 Pa（或 4.5 kPa，A 点压强高于 B 点）。",
                "judgeAnswer": None,
                "answer": "（1）常数 $a = -0.12$；\n\n（2）点 $A(0,0)$ 与点 $B(3,4)$ 间的压强差为 $p_A - p_B = 4500\\,\\mathrm{Pa} = 4.5\\,\\mathrm{kPa}$（即 $A$ 点压强比 $B$ 点高 $4500\\,\\mathrm{Pa}$）。",
                "analysis": "**（1）由不可压缩平面势流拉普拉斯方程求常数 $a$**\n\n流速势函数 $\\varphi(x,y) = 0.04x^3 + axy^2$ 对应的流速分量为：\n\n$$\nu_x = \\frac{\\partial\\varphi}{\\partial x} = 0.12x^2 + ay^2, \\qquad u_y = \\frac{\\partial\\varphi}{\\partial y} = 2axy\n$$\n\n不可压缩平面流动必须满足连续性微分方程 $\\frac{\\partial u_x}{\\partial x} + \\frac{\\partial u_y}{\\partial y} = 0$（即速度势满足拉普拉斯方程 $\\nabla^2\\varphi = 0$）：\n\n$$\n\\frac{\\partial^2\\varphi}{\\partial x^2} + \\frac{\\partial^2\\varphi}{\\partial y^2} = 0.24x + 2ax = (0.24 + 2a)x = 0\n$$\n\n上式对平面流场内任意 $x$ 恒成立，故系数必为零：\n\n$$\n0.24 + 2a = 0 \\implies a = -0.12\n$$\n\n**（2）求 $A(0,0)$ 与 $B(3,4)$ 两点流速大小并由伯努利方程计算压强差**\n\n将 $a = -0.12$ 代回流速分量表达式：\n\n$$\nu_x = 0.12(x^2 - y^2), \\qquad u_y = -0.24xy\n$$\n\n分别计算 $A$、$B$ 两点处的流速大小：\n- 在点 $A(0, 0)$ 处：$u_{xA} = 0$，$u_{yA} = 0 \\implies v_A = \\sqrt{u_{xA}^2 + u_{yA}^2} = 0\\,\\mathrm{m/s}$（驻点）；\n- 在点 $B(3, 4)$ 处：\n\n$$\nu_{xB} = 0.12 \\times (3^2 - 4^2) = -0.84\\,\\mathrm{m/s}, \\qquad u_{yB} = -0.24 \\times 3 \\times 4 = -2.88\\,\\mathrm{m/s}\n$$\n\n$$\nv_B = \\sqrt{(-0.84)^2 + (-2.88)^2} = \\sqrt{0.7056 + 8.2944} = \\sqrt{9.0000} = 3.0\\,\\mathrm{m/s}\n$$\n\n由于该势流不显含时间 $t$（恒定无旋理想流体流动），且位于水平面内（$z_A = z_B$），全流场任意两点间均满足拉格朗日—伯努利积分（不必局限于同一条流线）：\n\n$$\n\\frac{p_A}{\\rho} + \\frac{v_A^2}{2} = \\frac{p_B}{\\rho} + \\frac{v_B^2}{2}\n$$\n\n解得两点间的压强差：\n\n$$\np_A - p_B = \\frac{1}{2}\\rho (v_B^2 - v_A^2) = \\frac{1}{2} \\times 1000 \\times (3.0^2 - 0^2) = 4500\\,\\mathrm{Pa} = 4.5\\,\\mathrm{kPa}\n$$",
                "analysisFigures": [],
                "pitfalls": "1. 只要存在流速势函数 $\\varphi$，无旋条件 $\\omega_z = 0$ 已自动满足，求待定常数 $a$ 必须代**不可压缩连续性方程（拉普拉斯方程 $\\nabla^2\\varphi = 0$）**，切勿拿无旋条件兜圈子！\n2. 压强差的国际单位是 **$\\mathrm{Pa}$（$\\mathrm{N/m^2}$）或 $\\mathrm{kPa}$**，切勿与势函数单位 $\\mathrm{m^2/s}$ 混淆！",
                "chapter": 5,
                "kps": ["流函数与势函数", "拉普拉斯方程", "不可压缩连续性微分方程", "势流伯努利积分"],
                "method": "拉普拉斯方程定参数与势流伯努利求压差法",
                "difficulty": 2,
                "rubric": [
                    {"label": "写出流速分量 ux、uy 并代入连续性方程 ∂²φ/∂x² + ∂²φ/∂y² = 0 解得常数 a = -0.12", "pts": 4},
                    {"label": "求出 vA = 0、vB = 3.0 m/s，应用水平恒定势流伯努利方程算出压强差 pA - pB = 4500 Pa", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2020-13",
                "year": 2020,
                "no": 13,
                "type": "short",
                "score": 20,
                "title": "雷诺（Reynolds）液流型态试验装置示意图、主要试验步骤与试验结果",
                "stem": "1885 年雷诺（Reynolds）曾用试验揭示了实际液体运动存在两种液流型态，试绘出雷诺试验装置的示意图，并简要说明雷诺试验的主要步骤和结果。",
                "note": "",
                "figures": [],
                "shortAnswer": "装置包含溢流恒水头水箱、颜色水瓶与细注入针管、喇叭口水平透明玻璃实验管、尾端流量调节阀及量水箱（见解图 13）。步骤：静置稳压→微开阀门观察小流速下平直色线→逐步开大阀门观察色线波形摆动直至破裂混掺全管→反向关小阀门观察由湍流恢复层流。结果：揭示层流与湍流两种流态，发现湍流转层流的下临界流速小于层流转湍流的上临界流速，确立以无量纲下临界雷诺数 Rec = vcd/ν ≈ 2000 判别流态。",
                "judgeAnswer": None,
                "answer": "**1. 雷诺试验装置示意图**\n\n完整试验装置及三种典型流态色线现象如**解图 13** 所示，主要由五部分组成：\n① 带溢流稳压隔板的**高位恒水头供水水箱**（进水口与溢流管配合保持液面恒定）；\n② **有色液体（红墨水）贮瓶**、控制阀 $K_2$ 及伸入玻璃管进口轴线处的细注入针管（有色水密度与清水相同）；\n③ 带平顺喇叭形进口的**水平透明玻璃圆管**；\n④ 玻璃管末端的**流量调节阀门 $K_1$**；\n⑤ 出口下方的**量水箱（或计量容器与秒表，用于测定流量从而算出管内平均流速 $v$）**及水温计（查定运动黏度 $\\nu$）。\n\n**2. 雷诺试验的主要步骤**\n\n1. **充水稳压**：向水箱供水并保持微量溢流以稳定水位，关闭调节阀 $K_1$ 静置片刻消除水箱内初始扰动；\n2. **小流速层流观测**：微开尾端调节阀 $K_1$，同时开启有色水阀 $K_2$，使管内保持较小流速，可观察到透明玻璃管轴线上呈现出**一条笔直、边界清晰鲜明的有色细流束**，与周围清水互不混掺（解图 13a），同步测量流量与水温；\n3. **逐级增流转捩观测**：缓慢逐渐开大调节阀 $K_1$ 使管内流速递增——当流速增至某一数值时，有色细流束开始出现**规则的波形弯曲摆动**（过渡流，解图 13b）；继续开大阀门使流速超过上临界流速 $v_c^{\\prime}$ 时，有色流束突然完全破裂并迅速向四周剧烈扩散旋涡混掺，**使整根玻璃管内的水均匀着色**（湍流，解图 13c）；\n4. **反向减流回测**：再将调节阀 $K_1$ 由大逐步关小，使流速由大变小，观察有色水由全管混掺重新恢复为一条清晰直线流束的过程，测记对应的下临界流速 $v_c$。\n\n**3. 雷诺试验的主要结果与科学结论**\n\n1. **揭示两种基本流态**：证实实际黏性液体运动客观存在**层流**（分层有序滑动、无横向混掺）与**湍流 / 紊流**（质点随机脉动、旋涡剧烈混掺）两种截然不同的液流型态，以及介于其间的过渡流态；\n2. **流态转换的迟滞现象（上下临界流速不等）**：由层流转变为湍流时的**上临界流速 $v_c^{\\prime}$** 受外界扰动影响很大且不稳定，而由湍流恢复为层流时的**下临界流速 $v_c$** 数值更小（$v_c < v_c^{\\prime}$）且恒定可靠；\n3. **建立无量纲雷诺数判别准则**：变换不同管径 $d$、不同液体温度（不同运动黏度 $\\nu$）重复系统试验表明，流态转变并非单纯取决于流速 $v$，而是由惯性力与黏性力之比的无量纲组合数——**雷诺数 $Re = \\frac{vd}{\\nu}$** 唯一决定；工程上采用稳定的下临界雷诺数（圆管 $Re_c = \\frac{v_c d}{\\nu} \\approx 2000 \\sim 2300$）：当 $Re < Re_c$ 时恒为层流，当 $Re > Re_c$ 时一般为湍流。",
                "analysis": "**高分作图与答题得分要点提示**\n\n本题为 20 分压轴综合题，阅卷采分对装置图细节要求极严：\n1. **装置示意图五大必画要素**：① 水箱液面恒定标志（进水+溢流管）；② 颜色水瓶及对准管轴的细弯管针头；③ 玻璃管前端**喇叭口平顺进水段**（减小进口局部扰动）；④ **安装在玻璃管下游末端**的流量调节阀 $K_1$（若把调节阀画在玻璃管上游进口处，阀门局部旋涡会直接打碎色线，属于原则性装置错误！）；⑤ 三种流态色线对比小图（直线、波浪线、全管扩散）。\n2. **实验步骤不要漏掉“反向关小阀门”**：正是通过“先开大（层流 $\\to$ 湍流，测 $v_c^{\\prime}$）”与“再关小（湍流 $\\to$ 层流，测 $v_c$）”双向操作，雷诺才发现了 $v_c < v_c^{\\prime}$ 并选定稳定的下临界雷诺数 $Re_c$ 作为工程判据。",
                "analysisFigures": [
                    {"src": "figures/q13_sol.png", "caption": "解图 13　雷诺试验装置结构示意图及（a）层流、（b）过渡流、（c）湍流三种色线形态"}
                ],
                "pitfalls": "1. **画图头号大忌**：流量调节阀 $K_1$ **必须画在透明玻璃管的下游尾端**，绝对不能画在玻璃管上游入口处！\n2. **结果表述切勿漏掉雷诺数公式与上下临界流速对比**：除描述层流/湍流现象外，必须点明“湍流转层流的流速小于层流转湍流的流速（$v_c < v_c^{\\prime}$）”及判据 $Re = \\frac{vd}{\\nu}$。",
                "chapter": 4,
                "kps": ["雷诺实验装置与现象", "层流与紊流特征对比", "上临界与下临界雷诺数"],
                "method": "水力学经典机理实验装置—步骤—结论三段论法",
                "difficulty": 3,
                "rubric": [
                    {"label": "准确绘出包含恒水头水箱、颜色水注入管、透明玻璃管及下游尾端调节阀的雷诺试验装置示意图", "pts": 6},
                    {"label": "清晰叙述稳压、小流速层流色线、逐步开大阀门出现波形摆动与破裂混掺、以及反向关小阀门的完整步骤", "pts": 7},
                    {"label": "完整总结存在层流与湍流两种流态、下临界流速小于上临界流速（vc < vc'）及无量纲雷诺数判据 Re = vd/ν", "pts": 7}
                ]
            }
        ]
    }


# ==============================================================================
# Export Both Standardized Pack (`扬州大学已整理数据`) and Web Pack (`web/public/data`)
# ==============================================================================

def export_exam_pack(paper: dict, std_dir: Path) -> tuple[int, int]:
    year = int(paper["year"])
    std_fig_dir = std_dir / "figures"
    std_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write standardized JSON (`扬州大学已整理数据/<year>/<year>.json`)
    std_json_path = std_dir / f"{year}.json"
    std_json_path.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2. Write web-ready JSON + WebP figures (`web/public/data/yzu-849/`)
    web_paper = copy.deepcopy(paper)
    web_fig_dir = WEB_COURSE_DIR / "figures" / str(year)
    web_fig_dir.mkdir(parents=True, exist_ok=True)

    fig_count = 0
    for q in web_paper["questions"]:
        for key in ("figures", "analysisFigures"):
            new_list = []
            for fitem in q.get(key, []):
                raw_src = fitem["src"]
                src_png = std_fig_dir / Path(raw_src).name
                if not src_png.exists():
                    raise FileNotFoundError(f"Missing figure PNG: {src_png}")
                webp_name = f"{src_png.stem}.webp"
                dest_webp = web_fig_dir / webp_name
                im = Image.open(src_png)
                if im.mode not in ("RGB", "RGBA"):
                    im = im.convert("RGB")
                im.save(dest_webp, format="WEBP", quality=90, method=5)
                new_list.append({
                    "src": f"figures/{year}/{webp_name}",
                    "caption": fitem["caption"],
                })
                fig_count += 1
            q[key] = new_list

    web_json_path = WEB_COURSE_DIR / f"{year}.json"
    web_json_path.write_text(json.dumps(web_paper, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(web_paper["questions"]), fig_count


def main() -> None:
    dir_2021 = STD_ROOT / "2021"
    dir_2020 = STD_ROOT / "2020"
    fig_2021 = dir_2021 / "figures"
    fig_2020 = dir_2020 / "figures"
    fig_2021.mkdir(parents=True, exist_ok=True)
    fig_2020.mkdir(parents=True, exist_ok=True)

    print("1. Cropping 300 DPI deskewed stem figures from PDFs...")
    crop_all_stem_figures(fig_2021, fig_2020)

    print("2. Drawing 2021 matplotlib solution diagrams...")
    draw_2021_q04_sol(fig_2021)
    draw_2021_q07_sol(fig_2021)
    draw_2021_q09_sol(fig_2021)
    draw_2021_q11_sol(fig_2021)
    draw_2021_q12_sol(fig_2021)

    print("3. Drawing 2020 matplotlib solution diagrams...")
    draw_2020_q06_sol(fig_2020)
    draw_2020_q07_sol(fig_2020)
    draw_2020_q09_sol(fig_2020)
    draw_2020_q10_sol(fig_2020)
    draw_2020_q13_sol(fig_2020)

    print("4. Exporting standardized & web-ready JSON + WebP packs...")
    q21, f21 = export_exam_pack(build_2021_paper(), dir_2021)
    q20, f20 = export_exam_pack(build_2020_paper(), dir_2020)
    print(f"Done! 2021: {q21} questions, {f21} figures; 2020: {q20} questions, {f20} figures.")


if __name__ == "__main__":
    main()
