# -*- coding: utf-8 -*-
"""
Generate high-res 300 DPI cropped stem figures (q*_orig.png), clean matplotlib
solution schematics (q*_sol.png, dpi=220, ZERO CJK inside $...$), standardized
exam packs in `扬州大学已整理数据/{2015,2014}/`, and web-ready JSON + WebP assets in
`web/public/data/yzu-849/` for Yangzhou University 849 Hydraulics (2015 & 2014).

Strictly self-contained: does NOT touch index.json, courses.json, sw.js, HANDOFF.md, or other years.
"""

import copy
import json
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

VALID_CHAPTERS = set(range(1, 11))


def remove_small_specks(binary_ink: np.ndarray, min_pixels: int = 5) -> np.ndarray:
    """Remove isolated 1~4 px scan dust specks while preserving strokes & dots."""
    h, w = binary_ink.shape
    visited = np.zeros_like(binary_ink, dtype=bool)
    cleaned = binary_ink.copy()
    ys, xs = np.where(binary_ink)
    for y0, x0 in zip(ys, xs):
        if visited[y0, x0]:
            continue
        y_min, y_max = max(0, y0 - 2), min(h, y0 + 3)
        x_min, x_max = max(0, x0 - 2), min(w, x0 + 3)
        if binary_ink[y_min:y_max, x_min:x_max].sum() >= min_pixels:
            visited[y0, x0] = True
            continue
        stack = [(y0, x0)]
        comp = []
        visited[y0, x0] = True
        while stack and len(comp) < min_pixels + 2:
            cy, cx = stack.pop()
            comp.append((cy, cx))
            for ny in range(max(0, cy - 1), min(h, cy + 2)):
                for nx in range(max(0, cx - 1), min(w, cx + 2)):
                    if binary_ink[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        stack.append((ny, nx))
        if len(comp) < min_pixels and not stack:
            for cy, cx in comp:
                cleaned[cy, cx] = False
    return cleaned


def clean_and_pad(pil_img: Image.Image, pad: int = 16, thresh: int = 215) -> Image.Image:
    """Auto-trim ink bounds, whiten paper background to #FFFFFF, and add pure-white margin."""
    gray = np.array(pil_img.convert("L"), dtype=np.uint8)
    ink = remove_small_specks(gray < thresh, min_pixels=5)
    ys, xs = np.where(ink)
    if len(xs) == 0:
        return pil_img.convert("RGB")
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    sub = gray[y0:y1, x0:x1].copy()
    sub_ink = ink[y0:y1, x0:x1]
    sub_f = np.clip((sub.astype(np.float32) - 45.0) * (255.0 / (225.0 - 45.0)), 0, 255).astype(np.uint8)
    sub_f[~sub_ink & (sub > 205)] = 255
    out = np.full((sub_f.shape[0] + 2 * pad, sub_f.shape[1] + 2 * pad), 255, dtype=np.uint8)
    out[pad:pad + sub_f.shape[0], pad:pad + sub_f.shape[1]] = sub_f
    return Image.fromarray(out, mode="L").convert("RGB")


def extract_stem_figures():
    """Render 2015 & 2014 PDFs at 300 DPI and crop stem figures cleanly without `题X图` labels."""
    crops_by_year = {
        2015: (
            "849-水力学（水）2015.pdf",
            {
                "q10_orig.png": (0, (1790, 2440, 2230, 3020)),
                "q16_orig.png": (1, (510, 2340, 1320, 2930)),
                "q17_orig.png": (1, (1520, 2390, 2150, 2925)),
                "q18_orig.png": (2, (475, 1185, 1030, 1690)),
                "q19_orig.png": (2, (1270, 1070, 2040, 1705)),
            },
        ),
        2014: (
            "849-水力学（水）2014.pdf",
            {
                "q04_orig.png": (0, (840, 1505, 2220, 1815)),
                "q08_orig.png": (0, (1140, 2694, 1640, 2905)),
                "q21_orig.png": (0, (2990, 2530, 3620, 2760)),
                "q22_orig.png": (0, (3810, 2450, 4690, 2815)),
                "q23_orig.png": (1, (735, 725, 1605, 1225)),
                "q24_orig.png": (1, (1655, 825, 2465, 1245)),
                "q26_orig.png": (1, (735, 1855, 1285, 2232)),
                "q27_orig.png": (1, (1340, 1720, 2440, 2265)),
                "q28_orig.png": (1, (3255, 440, 3630, 845)),
                "q29_orig.png": (1, (3985, 405, 4615, 895)),
            },
        ),
    }

    for year, (pdf_name, fig_specs) in crops_by_year.items():
        fig_dir = PACK_ROOT / str(year) / "figures"
        fig_dir.mkdir(parents=True, exist_ok=True)
        doc = pymupdf.open(RAW_DIR / pdf_name)
        rendered_pages = {}
        for fname, (pidx, box) in fig_specs.items():
            if pidx not in rendered_pages:
                pix = doc[pidx].get_pixmap(dpi=300)
                rendered_pages[pidx] = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            cropped = clean_and_pad(rendered_pages[pidx].crop(box), pad=16)
            cropped.save(fig_dir / fname)
        doc.close()
        print(f"[{year}] Extracted {len(fig_specs)} stem figures at 300 DPI -> {fig_dir}")


# ==============================================================================
# Matplotlib Solution Figures for 2015 (dpi=220, ZERO CJK inside $...$)
# ==============================================================================

def draw_2015_q10_sol(fig_dir: Path):
    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    fig.patch.set_facecolor("white")

    # Water on left of wall x=0, surface y=2.2, bed y=-1.8
    ax.add_patch(patches.Rectangle((-2.8, -1.8), 2.8, 4.0, facecolor="#bae6fd", alpha=0.55))
    ax.plot([-2.8, 0.0], [2.2, 2.2], color="#0284c7", lw=2.0)
    ax.plot([-1.6, -1.5, -1.7, -1.6], [2.2, 2.38, 2.38, 2.2], color="#0f172a", lw=1.2)
    ax.plot([0.0, 0.0], [1.0, 2.7], color="#0f172a", lw=2.2)
    ax.plot([0.0, 0.0], [-1.8, -1.0], color="#0f172a", lw=2.2)
    ax.plot([-2.8, 1.8], [-1.8, -1.8], color="#0f172a", lw=2.2)
    for xh in np.linspace(-2.7, 1.7, 26):
        ax.plot([xh, xh - 0.12], [-1.8, -1.96], color="#64748b", lw=0.9)

    # Cylinder centered at (0, 0), radius R=1.0
    circ = patches.Circle((0, 0), 1.0, facecolor="#ffffff", edgecolor="#0f172a", lw=2.3, zorder=4)
    ax.add_patch(circ)
    ax.scatter([0], [0], color="#0f172a", s=40, zorder=6)
    ax.text(0.10, -0.06, r"$O$", fontsize=11.5, fontweight="bold", zorder=6)

    # Radial elementary pressure arrows passing through O on left semicircle
    for deg in [115, 140, 165, 195, 220, 245]:
        rad = np.radians(deg)
        x_out, y_out = 1.48 * np.cos(rad), 1.48 * np.sin(rad)
        x_in, y_in = 1.02 * np.cos(rad), 1.02 * np.sin(rad)
        ax.annotate("", xy=(x_in, y_in), xytext=(x_out, y_out),
                    arrowprops=dict(arrowstyle="->", color="#0284c7", lw=1.4), zorder=5)
        ax.plot([x_in, 0], [y_in, 0], color="#94a3b8", ls=":", lw=0.9, zorder=5)

    # Pz upward left of O (CW) and Px rightward below O (CCW)
    ax.annotate("", xy=(-0.42, 0.72), xytext=(-0.42, -0.30),
                arrowprops=dict(arrowstyle="->", color="#16a34a", lw=2.4), zorder=7)
    ax.text(-0.34, 0.56, r"$P_z$" + " (顺时针)", fontsize=9.0, ha="left", color="#15803d", fontweight="bold", zorder=7,
            bbox=dict(boxstyle="round,pad=0.14", facecolor="white", edgecolor="none", alpha=0.85))

    ax.annotate("", xy=(-0.15, -0.30), xytext=(-1.35, -0.30),
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.4), zorder=7)
    ax.text(-1.42, -0.32, r"$P_x$" + " (逆时针)", fontsize=9.5, ha="right", va="center", color="#b91c1c", fontweight="bold", zorder=7)

    # Resultant P through center O
    ax.annotate("", xy=(0.55, 0.36), xytext=(-0.82, -0.54),
                arrowprops=dict(arrowstyle="->", color="#7c3aed", lw=2.6), zorder=8)
    ax.text(1.06, 0.55, "合力 " + r"$P$" + " 过圆心 " + r"$O$" + "\n" + r"$\sum M_O = 0$",
            fontsize=9.8, color="#6d28d9", fontweight="bold", zorder=8)

    ax.text(1.55, -0.85, "各微元压力 " + r"$\mathrm{d}P$" + "\n法向均过圆心 " + r"$O$" + "\n无法持续转动！",
            fontsize=9.5, ha="center", color="#334155",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#f8fafc", edgecolor="#cbd5e1"))

    ax.set_xlim(-2.9, 2.65)
    ax.set_ylim(-2.1, 2.8)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("解图 10：半圆柱面静水压力法向均过圆心，对轴总力矩恒为零", fontsize=11, pad=6)
    plt.tight_layout()
    fig.savefig(fig_dir / "q10_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2015_q16_sol(fig_dir: Path):
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    fig.patch.set_facecolor("white")

    # Left tank (surface y=3.1) and right tank (surface y=3.7)
    ax.add_patch(patches.Rectangle((0.4, 0.4), 1.6, 2.7, facecolor="#e0f2fe", alpha=0.65))
    ax.add_patch(patches.Rectangle((5.2, 0.4), 1.6, 3.3, facecolor="#e0f2fe", alpha=0.65))
    ax.plot([0.4, 0.4, 2.0, 2.0], [3.5, 0.4, 0.4, 3.5], color="#0f172a", lw=2.0)
    ax.plot([5.2, 5.2, 6.8, 6.8], [4.0, 0.4, 0.4, 4.0], color="#0f172a", lw=2.0)
    ax.plot([0.4, 2.0], [3.1, 3.1], color="#0284c7", lw=2.0)
    ax.plot([5.2, 6.8], [3.7, 3.7], color="#0284c7", lw=2.0)
    ax.text(1.2, 1.8, r"$\gamma$", fontsize=13, ha="center", color="#0369a1", fontweight="bold")
    ax.text(6.0, 1.8, r"$\gamma$", fontsize=13, ha="center", color="#0369a1", fontweight="bold")
    ax.text(1.2, 3.28, r"液面 $z_1$", fontsize=9.8, ha="center", color="#0369a1")
    ax.text(6.0, 3.88, r"液面 $z_2$", fontsize=9.8, ha="center", color="#0369a1")

    # Upper inverted U-tube (gamma_A, diff A: left low y=2.6, right high y=3.3)
    ax.plot([2.0, 2.9, 2.9], [2.4, 2.4, 3.7], color="#0f172a", lw=2.0)
    ax.plot([4.3, 4.3, 5.2], [3.7, 2.4, 2.4], color="#0f172a", lw=2.0)
    th_top = np.linspace(0, np.pi, 60)
    ax.plot(3.6 + 0.7 * np.cos(th_top), 3.7 + 0.45 * np.sin(th_top), color="#0f172a", lw=2.0)
    ax.plot([2.85, 2.95], [2.65, 2.65], color="#ea580c", lw=3.0)
    ax.plot([4.25, 4.35], [3.35, 3.35], color="#ea580c", lw=3.0)
    ax.annotate("", xy=(3.6, 3.35), xytext=(3.6, 2.65),
                arrowprops=dict(arrowstyle="<->", color="#ea580c", lw=1.6))
    ax.plot([2.95, 4.25], [2.65, 2.65], color="#ea580c", ls="--", lw=1.1)
    ax.plot([3.45, 4.25], [3.35, 3.35], color="#ea580c", ls="--", lw=1.1)
    ax.text(3.68, 3.00, r"$A$", fontsize=11, color="#c2410c", fontweight="bold")
    ax.text(3.6, 4.32, "轻液 " + r"$\gamma_A < \gamma$", fontsize=10, ha="center", color="#c2410c", fontweight="bold")

    # Lower U-tube (gamma_B, diff B: left high y=1.45, right low y=0.85)
    ax.plot([2.0, 2.9, 2.9], [1.7, 1.7, 0.65], color="#0f172a", lw=2.0)
    ax.plot([4.3, 4.3, 5.2], [0.65, 1.7, 1.7], color="#0f172a", lw=2.0)
    th_bot = np.linspace(np.pi, 2 * np.pi, 60)
    ax.plot(3.6 + 0.7 * np.cos(th_bot), 0.65 + 0.45 * np.sin(th_bot), color="#0f172a", lw=2.0)
    ax.plot([2.85, 2.95], [1.45, 1.45], color="#15803d", lw=3.0)
    ax.plot([4.25, 4.35], [0.85, 0.85], color="#15803d", lw=3.0)
    ax.annotate("", xy=(3.6, 1.45), xytext=(3.6, 0.85),
                arrowprops=dict(arrowstyle="<->", color="#15803d", lw=1.6))
    ax.plot([2.95, 4.25], [0.85, 0.85], color="#15803d", ls="--", lw=1.1)
    ax.plot([2.95, 3.75], [1.45, 1.45], color="#15803d", ls="--", lw=1.1)
    ax.text(3.68, 1.15, r"$B$", fontsize=11, color="#15803d", fontweight="bold")
    ax.text(3.6, 0.02, "重液 " + r"$\gamma_B > \gamma$", fontsize=10, ha="center", color="#15803d", fontweight="bold")

    # Summary formula callout
    ax.text(3.6, 2.05,
            "上管：" + r"$(\gamma - \gamma_A)A = \gamma(z_2 - z_1)$" + "\n"
            "下管：" + r"$(\gamma_B - \gamma)B = \gamma(z_2 - z_1)$" + "\n"
            r"$\Rightarrow \gamma = \frac{\gamma_A A + \gamma_B B}{A + B}$",
            fontsize=9.4, ha="center", va="center", color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#fffbeb", edgecolor="#f59e0b"))

    ax.set_xlim(0.1, 7.1)
    ax.set_ylim(-0.18, 4.65)
    ax.axis("off")
    ax.set_title("解图 16：上下双 U 形差压计等压面联立消去水位差", fontsize=11, pad=6)
    plt.tight_layout()
    fig.savefig(fig_dir / "q16_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2015_q17_sol(fig_dir: Path):
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    fig.patch.set_facecolor("white")

    # Tank: x in [0, 3.2], y in [0, 3.6]; water surface y=3.0; semicircle ABC on right wall x=3.2, center O=(3.2, 1.0), R=1.0
    # Water fills tank to left of semicircle ABC
    th = np.linspace(-np.pi / 2, np.pi / 2, 120)
    xc = 3.2 - 1.0 * np.cos(th)
    yc = 1.0 + 1.0 * np.sin(th)
    water_poly = [(0.0, 0.0), (0.0, 3.0), (3.2, 3.0), (3.2, 2.0)] + list(zip(xc[::-1], yc[::-1]))
    ax.add_patch(patches.Polygon(water_poly, closed=True, facecolor="#e0f2fe", alpha=0.65))

    # Equivalent free surface at y = 2.0 (right through A!)
    ax.plot([-1.4, 4.5], [2.0, 2.0], color="#dc2626", ls="--", lw=1.8)
    ax.text(1.42, 2.15, "等压零面 (" + r"$p=0$" + ", 恰过 " + r"$A$" + " 点)", fontsize=9.5, ha="center", color="#b91c1c", fontweight="bold")

    # Tank outline & semicircle
    ax.plot([0.0, 0.0, 3.2, 3.2], [3.55, 0.0, 0.0, 0.0], color="#0f172a", lw=2.2)
    ax.plot([0.0, 3.2], [3.55, 3.55], color="#0f172a", lw=2.2)
    ax.plot([3.2, 3.2], [2.0, 3.55], color="#0f172a", lw=2.2)
    ax.plot([0.0, 3.2], [3.0, 3.0], color="#0284c7", lw=2.0)
    ax.plot(xc, yc, color="#0f172a", lw=2.8, zorder=5)

    # Piezometer on left reading h = 2.0 m
    ax.plot([-0.7, -0.7, 0.0], [2.6, 0.0, 0.0], color="#0f172a", lw=1.8)
    ax.plot([-0.52, -0.52, 0.0], [2.6, 0.16, 0.16], color="#0f172a", lw=1.8)
    ax.add_patch(patches.Rectangle((-0.68, 0.02), 0.14, 1.98, facecolor="#38bdf8", alpha=0.75))
    ax.annotate("", xy=(-0.95, 2.0), xytext=(-0.95, 0.0),
                arrowprops=dict(arrowstyle="<->", color="#0369a1", lw=1.4))
    ax.text(-1.02, 1.0, r"$h=2.0\,\mathrm{m}$", fontsize=9.8, ha="right", va="center", color="#0369a1", fontweight="bold")

    # Horizontal triangular pressure diagram on AC (p_A = 0, p_C = 2*rho*g)
    tri_poly = [(3.2, 2.0), (3.2, 0.0), (4.45, 0.0)]
    ax.add_patch(patches.Polygon(tri_poly, closed=True, facecolor="#fed7aa", edgecolor="#ea580c", lw=1.4, alpha=0.75))
    ax.annotate("", xy=(3.2, 0.67), xytext=(4.05, 0.67),
                arrowprops=dict(arrowstyle="<-", color="#ea580c", lw=2.2), zorder=6)
    ax.text(4.12, 0.67, r"$P_x = 19.60\,\mathrm{kN}$" + " (向右)", fontsize=9.5, va="center", color="#c2410c", fontweight="bold")

    # Buoyancy semicircle shading (virtual upward volume = 0.5*pi*R^2)
    semi_poly = [(3.2, 2.0)] + list(zip(xc[::-1], yc[::-1])) + [(3.2, 0.0)]
    ax.add_patch(patches.Polygon(semi_poly, closed=True, facecolor="#bbf7d0", edgecolor="#16a34a", lw=1.3, alpha=0.60, zorder=3))
    ax.annotate("", xy=(2.75, 1.68), xytext=(2.75, 0.45),
                arrowprops=dict(arrowstyle="->", color="#16a34a", lw=2.3), zorder=6)
    ax.text(1.88, 1.05, r"$P_z = 15.39\,\mathrm{kN}$" + "\n(竖直向上)", fontsize=9.5, ha="right", va="center", color="#15803d", fontweight="bold")

    # Resultant P passing through O=(3.2, 1.0) at +38.15 deg above horizontal
    ang = np.radians(38.15)
    x_pt, y_pt = 3.2 - np.cos(ang), 1.0 - np.sin(ang)
    ax.scatter([3.2, x_pt], [1.0, y_pt], color=["#0f172a", "#7c3aed"], s=36, zorder=8)
    ax.annotate("", xy=(3.2 + 0.95 * np.cos(ang), 1.0 + 0.95 * np.sin(ang)), xytext=(x_pt, y_pt),
                arrowprops=dict(arrowstyle="->", color="#7c3aed", lw=2.7), zorder=8)
    ax.text(3.85, 1.65, r"$P = 24.92\,\mathrm{kN}$" + "\n" + r"$\theta = 38.15^\circ$" + " 过圆心 " + r"$O$",
            fontsize=9.8, color="#6d28d9", fontweight="bold")

    ax.text(3.30, 2.05, r"$A$", fontsize=11, fontweight="bold")
    ax.text(2.02, 1.00, r"$B$", fontsize=11, fontweight="bold")
    ax.text(3.30, -0.10, r"$C$", fontsize=11, fontweight="bold")
    ax.text(3.26, 0.90, r"$O$", fontsize=10.5, fontweight="bold")
    ax.text(1.5, 3.25, "气体 " + r"$p_0 = -9.8\,\mathrm{kPa}$", fontsize=9.8, ha="center", color="#334155")

    ax.set_xlim(-1.55, 5.55)
    ax.set_ylim(-0.32, 3.78)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("解图 17：等效零压面与半圆柱曲面 ABC 静水总压力合成图", fontsize=11, pad=6)
    plt.tight_layout()
    fig.savefig(fig_dir / "q17_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2015_q19_sol(fig_dir: Path):
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    fig.patch.set_facecolor("white")

    th = np.radians(52.0)
    # Plate line through (0, 0) along angle th
    s_vals = np.array([-2.2, 2.4])
    xp, yp = s_vals * np.cos(th), s_vals * np.sin(th)
    ax.plot(xp, yp, color="#0f172a", lw=3.0, zorder=5)
    for si in np.linspace(-2.0, 2.2, 18):
        x0, y0 = si * np.cos(th), si * np.sin(th)
        ax.plot([x0, x0 + 0.16 * np.sin(th) - 0.10 * np.cos(th)],
                [y0, y0 - 0.16 * np.cos(th) - 0.10 * np.sin(th)], color="#64748b", lw=1.0)

    # Incoming jet
    ax.add_patch(patches.Rectangle((-3.3, -0.26), 2.35, 0.52, facecolor="#bae6fd", alpha=0.65))
    ax.plot([-3.3, -1.6], [0.26, 0.26], color="#0284c7", lw=2.0)
    ax.plot([-3.3, -1.6], [-0.26, -0.26], color="#0284c7", lw=2.0)
    ax.plot([-3.3, 1.3], [0.0, 0.0], color="#64748b", ls="--", lw=1.1)
    ax.annotate("", xy=(-1.75, 0.0), xytext=(-2.9, 0.0),
                arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2.2))
    ax.text(-2.45, 0.45, r"$Q_0, v_0$", fontsize=11, ha="center", color="#0369a1", fontweight="bold")

    # Split jets Q1 (up) and Q2 (down)
    nx, ny = -np.sin(th), np.cos(th)  # unit normal pointing from plate into water (up-left)
    ax.annotate("", xy=(1.85 * np.cos(th) + 0.35 * nx, 1.85 * np.sin(th) + 0.35 * ny),
                xytext=(0.75 * np.cos(th) + 0.35 * nx, 0.75 * np.sin(th) + 0.35 * ny),
                arrowprops=dict(arrowstyle="->", color="#16a34a", lw=2.2))
    ax.text(1.15 * np.cos(th) + 0.68 * nx, 1.15 * np.sin(th) + 0.68 * ny,
            r"$Q_1 = \frac{1}{2}Q_0(1+\cos\theta)$", fontsize=9.8, ha="right", color="#15803d", fontweight="bold")

    ax.annotate("", xy=(-1.75 * np.cos(th) + 0.26 * nx, -1.75 * np.sin(th) + 0.26 * ny),
                xytext=(-0.75 * np.cos(th) + 0.26 * nx, -0.75 * np.sin(th) + 0.26 * ny),
                arrowprops=dict(arrowstyle="->", color="#ea580c", lw=2.2))
    ax.text(-1.25 * np.cos(th) + 0.52 * nx, -1.25 * np.sin(th) + 0.52 * ny,
            r"$Q_2 = \frac{1}{2}Q_0(1-\cos\theta)$", fontsize=9.8, ha="right", color="#c2410c", fontweight="bold")

    # S and n coordinate axes
    ax.annotate("", xy=(2.55 * np.cos(th), 2.55 * np.sin(th)), xytext=(2.05 * np.cos(th), 2.05 * np.sin(th)),
                arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.8))
    ax.text(2.65 * np.cos(th), 2.65 * np.sin(th), r"$S$", fontsize=11.5, fontweight="bold")

    # Jet impact force F on plate (pointing down-right, -n direction)
    ax.annotate("", xy=(-0.95 * nx, -0.95 * ny), xytext=(0.0, 0.0),
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.8), zorder=7)
    ax.text(-1.05 * nx + 0.05, -1.05 * ny,
            "射流冲击力\n" + r"$F = \rho Q_0 v_0 \sin\theta$",
            fontsize=10.2, ha="left", va="top", color="#b91c1c", fontweight="bold")

    # Angle arc theta
    arc_t = np.linspace(0, th, 40)
    ax.plot(0.65 * np.cos(arc_t), 0.65 * np.sin(arc_t), color="#334155", lw=1.3)
    ax.text(0.78, 0.25, r"$\theta$", fontsize=11, color="#0f172a")

    ax.set_xlim(-3.45, 2.75)
    ax.set_ylim(-2.05, 2.35)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("解图 19：射流斜冲固定平板的切向分流与法向冲击力分析", fontsize=11, pad=6)
    plt.tight_layout()
    fig.savefig(fig_dir / "q19_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2015_q21_sol(fig_dir: Path):
    fig, ax = plt.subplots(figsize=(6.6, 4.8))
    fig.patch.set_facecolor("white")

    x = np.linspace(-0.5, 4.5, 240)
    y = np.linspace(-0.5, 5.8, 240)
    X, Y = np.meshgrid(x, y)
    PSI = X**2 - Y**2

    # Background streamline contours
    cs = ax.contour(X, Y, PSI, levels=[-25, -15, -9, -1, 0, 2, 6, 12], colors="#cbd5e1", linewidths=1.0)
    ax.clabel(cs, fmt=r"$\psi=%g$", fontsize=7.5, colors="#64748b")

    # Highlight psi = -3 through A(1, 2) and psi = -21 through B(2, 5)
    ax.contour(X, Y, PSI, levels=[-3], colors=["#0284c7"], linewidths=2.4)
    ax.contour(X, Y, PSI, levels=[-21], colors=["#dc2626"], linewidths=2.4)

    # Plot A(1,2), B(2,5) and connecting segment AB
    ax.plot([1, 2], [2, 5], color="#16a34a", ls="--", lw=2.2, zorder=5)
    ax.scatter([1, 2], [2, 5], color=["#0284c7", "#dc2626"], s=55, zorder=6)
    ax.text(1.12, 1.82, r"$A(1,2),\ \psi_A = -3$", fontsize=10, color="#0369a1", fontweight="bold")
    ax.text(2.12, 4.92, r"$B(2,5),\ \psi_B = -21$", fontsize=10, color="#b91c1c", fontweight="bold")
    ax.text(1.70, 3.35, "单宽流量\n" + r"$q = |\psi_B - \psi_A| = 18\,\mathrm{m^2/s}$",
            fontsize=9.6, color="#15803d", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#f0fdf4", edgecolor="#86efac"))

    ax.axhline(0, color="#334155", lw=1.0)
    ax.axvline(0, color="#334155", lw=1.0)
    ax.set_xlabel(r"$x$", fontsize=10.5)
    ax.set_ylabel(r"$y$", fontsize=10.5)
    ax.set_xlim(-0.3, 4.4)
    ax.set_ylim(-0.3, 5.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title("解图 21：等流函数双曲线簇与两点间单宽流量示意", fontsize=11, pad=6)
    plt.tight_layout()
    fig.savefig(fig_dir / "q21_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


# ==============================================================================
# Matplotlib Solution Figures for 2014 (dpi=220, ZERO CJK inside $...$)
# ==============================================================================

def draw_2014_q22_sol(fig_dir: Path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.8, 3.8))
    fig.patch.set_facecolor("white")

    for ax, deg, p_val, tag in [
        (ax1, 30, "8.50", "（a）底坡倾角 30°"),
        (ax2, 45, "6.94", "（b）底坡倾角 45°"),
    ]:
        th = np.radians(deg)
        L = 3.2
        h_perp = 1.0
        # Bed from (0, L sin th) down to (L cos th, 0)
        x0, y0 = 0.0, L * np.sin(th)
        x1, y1 = L * np.cos(th), 0.0
        nx, ny = np.sin(th), np.cos(th)  # outward normal from bed into water
        poly = [(x0, y0), (x1, y1), (x1 + h_perp * nx, y1 + h_perp * ny), (x0 + h_perp * nx, y0 + h_perp * ny)]
        ax.add_patch(patches.Polygon(poly, closed=True, facecolor="#bae6fd", alpha=0.65))
        ax.plot([x0, x1], [y0, y1], color="#0f172a", lw=2.4)
        ax.plot([x0 + h_perp * nx, x1 + h_perp * nx], [y0 + h_perp * ny, y1 + h_perp * ny], color="#0284c7", lw=2.0)
        ax.plot([x0, x1 + 0.5], [0, 0], color="#64748b", ls="--", lw=1.1)

        # Normal cross-section AC at mid-channel
        xm, ym = 0.55 * (x0 + x1), 0.55 * (y0 + y1)
        xc, yc = xm + h_perp * nx, ym + h_perp * ny
        ax.plot([xm, xc], [ym, yc], color="#dc2626", lw=2.2)
        ax.scatter([xm, xc], [ym, yc], color="#dc2626", s=30, zorder=5)
        ax.text(xm - 0.12, ym - 0.16, r"$A$", fontsize=11, color="#b91c1c", fontweight="bold")
        ax.text(xc + 0.06, yc + 0.08, r"$C\ (p_C=0)$", fontsize=9.8, color="#b91c1c", fontweight="bold")

        # Vertical drop zC - zA = h cos(theta)
        ax.plot([xm, xc], [ym, ym], color="#16a34a", ls=":", lw=1.4)
        ax.annotate("", xy=(xc, yc), xytext=(xc, ym),
                    arrowprops=dict(arrowstyle="<->", color="#16a34a", lw=1.6))
        ax.text(xc + 0.08, 0.5 * (ym + yc), r"$\Delta z = h\cos" + f"{deg}" + r"^\circ$",
                fontsize=9.5, color="#15803d", fontweight="bold")

        ax.text(0.15, 0.22, r"$p_A = \rho g h\cos" + f"{deg}" + r"^\circ \approx " + p_val + r"\,\mathrm{kPa}$",
                fontsize=9.6, color="#0f172a",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#fffbeb", edgecolor="#f59e0b"))

        ax.set_xlim(-0.2, 3.85)
        ax.set_ylim(-0.35, 3.25)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(tag, fontsize=10.8, pad=4)

    plt.tight_layout()
    fig.savefig(fig_dir / "q22_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2014_q24_sol(fig_dir: Path):
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    fig.patch.set_facecolor("white")

    # Schematic horizontal coordinate along flow path: 1(0.6) -> 2(1.4) -> 3(3.6) -> Pump(4.2) -> 4(4.8) -> 5(7.6)
    xs_pipe = [1.4, 1.4, 3.9, 4.5, 6.2, 6.2, 7.6]
    ys_pipe = [0.6, 1.8, 1.8, 1.8, 1.8, 3.3, 3.3]
    ax.plot(xs_pipe, ys_pipe, color="#0f172a", lw=4.5, alpha=0.85, zorder=4)
    ax.plot(xs_pipe, ys_pipe, color="#e0f2fe", lw=2.2, zorder=5)

    # Sump water level y=1.1 (point 1 & point 2)
    ax.add_patch(patches.Rectangle((0.2, 0.2), 1.8, 0.9, facecolor="#bae6fd", alpha=0.55))
    ax.plot([0.2, 2.0], [1.1, 1.1], color="#0284c7", lw=2.0)
    ax.plot([0.2, 7.8], [1.1, 1.1], color="#94a3b8", ls=":", lw=1.0)

    # Pump circle at (4.2, 1.8)
    ax.add_patch(patches.Circle((4.2, 1.8), 0.28, facecolor="#fef08a", edgecolor="#ca8a04", lw=2.2, zorder=6))
    ax.text(4.2, 1.8, "泵", fontsize=10.5, ha="center", va="center", fontweight="bold", color="#854d0e", zorder=7)

    # Points 1..5
    pts = [
        (0.7, 1.1, "1", (0.7, 1.24), r"$p_1=0$", (0.7, 1.48)),
        (1.4, 1.1, "2", (1.62, 1.24), r"$p_2<0$", (2.05, 0.90)),
        (3.55, 1.8, "3", (3.55, 2.02), r"$p_3<p_2<0$", (3.35, 1.35)),
        (4.85, 1.8, "4", (4.85, 2.02), r"$p_4>0$ (最大)", (5.05, 1.35)),
        (7.6, 3.3, "5", (7.80, 3.30), r"$p_5=0$", (7.6, 2.90)),
    ]
    for px, py, num, (nx_l, ny_l), lbl, (tx, ty) in pts:
        ax.scatter([px], [py], color="#dc2626", s=45, zorder=8)
        ax.text(nx_l, ny_l, num, fontsize=9.5, ha="center", va="center", fontweight="bold", color="#b91c1c", zorder=9)
        ax.text(tx, ty, lbl, fontsize=9.2, ha="center", color="#0f172a")

    # HGL (red dashed) & EGL (green solid)
    # 1(y=1.1) -> 2(HGL=0.88, EGL=1.05) -> 3(HGL=0.65, EGL=0.82) -> Pump jump -> 4(HGL=3.75, EGL=3.92) -> 5(HGL=3.30, EGL=3.47)
    ax.plot([0.7, 1.4, 3.9], [1.1, 1.04, 0.82], color="#16a34a", lw=2.1, label="总水头线 (E.G.L.)")
    ax.plot([4.5, 7.6], [3.95, 3.52], color="#16a34a", lw=2.1)
    ax.plot([3.9, 4.5], [0.82, 3.95], color="#16a34a", ls=":", lw=1.6)

    ax.plot([1.4, 3.9], [0.84, 0.62], color="#dc2626", ls="--", lw=2.1, label="测压管水头线 (H.G.L.)")
    ax.plot([4.5, 7.6], [3.75, 3.30], color="#dc2626", ls="--", lw=2.1)

    ax.annotate("", xy=(4.2, 3.90), xytext=(4.2, 0.86),
                arrowprops=dict(arrowstyle="<->", color="#7c3aed", lw=1.6))
    ax.text(4.32, 2.55, "水泵扬程\n" + r"$H_p$", fontsize=9.5, color="#6d28d9", fontweight="bold")

    ax.text(2.4, 3.85, "压强排序：" + r"$p_4 > p_1 = p_5 > p_2 > p_3$",
            fontsize=10.5, ha="center", color="#0f172a", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#f0fdf4", edgecolor="#86efac"))

    ax.legend(loc="lower right", fontsize=9.2, framealpha=0.95)
    ax.set_xlim(0.05, 8.2)
    ax.set_ylim(0.1, 4.3)
    ax.axis("off")
    ax.set_title("解图 24：抽水系统水头线分布与 1~5 点动水压强大小比较", fontsize=11, pad=6)
    plt.tight_layout()
    fig.savefig(fig_dir / "q24_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2014_q26_sol(fig_dir: Path):
    fig, ax = plt.subplots(figsize=(6.8, 4.6))
    fig.patch.set_facecolor("white")

    # Tank top at y=0, hemisphere of radius r=1.0 protruding upward into y in [0, 1.0]
    th = np.linspace(0, np.pi, 120)
    xh, yh = np.cos(th), np.sin(th)

    # Virtual pressure body between hemisphere surface and equivalent free oil surface y_eq=2.8
    y_eq = 2.65
    vpb = [(-1.0, y_eq), (1.0, y_eq)] + list(zip(xh, yh))
    ax.add_patch(patches.Polygon(vpb, closed=True, facecolor="#fef08a", edgecolor="#ca8a04", lw=1.5, alpha=0.65, zorder=2))

    # Oil inside tank y in [-1.4, 0] and inside hemisphere
    ax.add_patch(patches.Rectangle((-2.1, -1.3), 4.2, 1.3, facecolor="#ffedd5", alpha=0.65, zorder=1))
    ax.add_patch(patches.Polygon(list(zip(xh, yh)), closed=True, facecolor="#ffedd5", alpha=0.75, zorder=1))

    # Tank walls & hemisphere outline
    ax.plot([-2.1, -1.0], [0, 0], color="#0f172a", lw=2.3, zorder=4)
    ax.plot([1.0, 2.1], [0, 0], color="#0f172a", lw=2.3, zorder=4)
    ax.plot([-2.1, -2.1, 2.1, 2.1], [0, -1.3, -1.3, 0], color="#0f172a", lw=2.3, zorder=4)
    ax.plot([-1.0, 1.0], [0, 0], color="#64748b", ls="--", lw=1.3, zorder=4)
    ax.plot(xh, yh, color="#0f172a", lw=2.8, zorder=5)
    ax.scatter([0], [0], color="#0f172a", s=32, zorder=6)
    ax.text(0.06, -0.22, r"$O\ (r=0.10\,\mathrm{m})$", fontsize=9.8, ha="center", fontweight="bold")

    # Equivalent free oil surface
    ax.plot([-2.2, 2.2], [y_eq, y_eq], color="#dc2626", ls="--", lw=1.8)
    ax.text(-2.15, y_eq + 0.10, "等效自由油面 (" + r"$p=0$" + ")", fontsize=9.5, color="#b91c1c", fontweight="bold")

    # Dimension H = 3.125 m
    ax.annotate("", xy=(1.65, y_eq), xytext=(1.65, 0.0),
                arrowprops=dict(arrowstyle="<->", color="#0369a1", lw=1.6))
    ax.text(1.74, 0.5 * y_eq, r"$H = \frac{p_O}{\rho_o g}$" + "\n" + r"$= 3.125\,\mathrm{m}$",
            fontsize=9.8, va="center", color="#0369a1", fontweight="bold")

    # Upward resultant Pz
    ax.annotate("", xy=(0, 2.25), xytext=(0, 1.02),
                arrowprops=dict(arrowstyle="->", color="#16a34a", lw=2.8), zorder=7)
    ax.text(0.12, 1.65, "虚压力体向上\n" + r"$P_z = 754.0\,\mathrm{N}\ (\uparrow)$",
            fontsize=10.0, color="#15803d", fontweight="bold")

    ax.text(-1.55, -0.68, "油 " + r"$\rho_o = 800\,\mathrm{kg/m^3}$", fontsize=9.5, color="#9a3412")
    ax.text(0.0, -1.62, r"$V_z = \pi r^2 H - \frac{2}{3}\pi r^3 = 0.09608\,\mathrm{m^3}$",
            fontsize=10.0, ha="center", color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#f8fafc", edgecolor="#cbd5e1"))

    ax.set_xlim(-2.4, 2.95)
    ax.set_ylim(-1.88, 3.05)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("解图 26：容器顶部半球曲面虚压力体与铅垂向上总压力", fontsize=11, pad=6)
    plt.tight_layout()
    fig.savefig(fig_dir / "q26_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2014_q27_sol(fig_dir: Path):
    fig, ax = plt.subplots(figsize=(8.0, 4.1))
    fig.patch.set_facecolor("white")

    # Reservoir x in [0.4, 1.6], water surface y=3.0; pipe axis y=0.6 from x=1.6 to x=6.8 (midpoint x=4.2)
    ax.add_patch(patches.Rectangle((0.4, 0.1), 1.2, 2.9, facecolor="#bae6fd", alpha=0.55))
    ax.plot([0.4, 1.6], [3.0, 3.0], color="#0284c7", lw=2.0)
    ax.plot([1.6, 1.6], [3.3, 0.72], color="#0f172a", lw=2.2)
    ax.plot([1.6, 1.6], [0.48, 0.1], color="#0f172a", lw=2.2)

    # Horizontal pipe
    ax.add_patch(patches.Rectangle((1.6, 0.48), 5.2, 0.24, facecolor="#bae6fd", alpha=0.65))
    ax.plot([1.6, 6.8], [0.72, 0.72], color="#0f172a", lw=2.0)
    ax.plot([1.6, 6.8], [0.48, 0.48], color="#0f172a", lw=2.0)
    ax.plot([1.3, 7.1], [0.60, 0.60], color="#64748b", ls="-.", lw=1.0)

    # Midpoint piezometer at x=4.2, water height = 1.0 m -> y = 0.6 + 0.8 = 1.4
    ax.plot([4.12, 4.12], [0.72, 2.3], color="#0f172a", lw=1.5)
    ax.plot([4.28, 4.28], [0.72, 2.3], color="#0f172a", lw=1.5)
    ax.add_patch(patches.Rectangle((4.14, 0.72), 0.12, 0.68, facecolor="#38bdf8", alpha=0.8))
    ax.text(4.42, 1.05, r"$h_p = 1\,\mathrm{m}$", fontsize=9.6, color="#0369a1", fontweight="bold")

    # Head lines (scale: 1 m = 0.8 units above axis y=0.6; H=3 m -> y=3.0)
    # v^2/2g = 2/3 m -> 0.533 units; entrance loss 0.5 v^2/2g = 1/3 m -> 0.267 units
    # At x=1.6+ (after entrance): EGL = 3.0 - 0.267 = 2.733, HGL = 2.733 - 0.533 = 2.20
    # At x=4.2 (L/2): EGL = 2.733 - 0.80 = 1.933, HGL = 1.40 (exactly 1.0 m above axis!)
    # At x=6.8 (L): EGL = 1.933 - 0.80 = 1.133, HGL = 0.60 (exactly at axis, atmospheric exit!)
    ax.plot([1.6, 1.75, 4.2, 6.8], [3.0, 2.733, 1.933, 1.133], color="#16a34a", lw=2.2, label="总水头线 (E.G.L.)")
    ax.plot([1.75, 4.2, 6.8], [2.20, 1.40, 0.60], color="#dc2626", ls="--", lw=2.2, label="测压管水头线 (H.G.L.)")

    # Annotations
    ax.annotate("", xy=(0.95, 3.0), xytext=(0.95, 0.60),
                arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.4))
    ax.text(0.88, 1.80, r"$H=3\,\mathrm{m}$", fontsize=9.8, ha="right", color="#0f172a", fontweight="bold")

    ax.annotate("", xy=(6.95, 1.133), xytext=(6.95, 0.60),
                arrowprops=dict(arrowstyle="<->", color="#7c3aed", lw=1.5))
    ax.text(7.04, 0.86, r"$\frac{v^2}{2g}=\frac{2}{3}\,\mathrm{m}$", fontsize=9.6, color="#6d28d9", fontweight="bold")

    ax.text(5.55, 2.55,
            "后半段 " + r"$\frac{1}{2}h_f = 1\,\mathrm{m} \Rightarrow h_f = 2\,\mathrm{m}$" + "\n"
            r"$(1+\zeta_e)\frac{v^2}{2g} = 3 - 2 = 1\,\mathrm{m}$" + "\n"
            r"$v = 3.617\,\mathrm{m/s},\ Q = 0.0284\,\mathrm{m^3/s}$",
            fontsize=9.3, ha="center", color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#fffbeb", edgecolor="#f59e0b"))

    ax.legend(loc="lower left", fontsize=9.0, framealpha=0.95)
    ax.set_xlim(0.15, 8.15)
    ax.set_ylim(0.0, 3.45)
    ax.axis("off")
    ax.set_title("解图 27：中点测压管消元法求有压水平管道流量", fontsize=11, pad=6)
    plt.tight_layout()
    fig.savefig(fig_dir / "q27_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2014_q28_sol(fig_dir: Path):
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    fig.patch.set_facecolor("white")

    # 180-deg horizontal U-bend: top inlet y=+1.0, bottom outlet y=-1.0, bend radius R_mid=1.0, pipe half-width 0.25
    th = np.linspace(-np.pi / 2, np.pi / 2, 120)
    r_in, r_out = 0.75, 1.25
    x_out, y_out = r_out * np.cos(th), r_out * np.sin(th)
    x_in, y_in = r_in * np.cos(th), r_in * np.sin(th)

    bend_poly = list(zip(x_out, y_out)) + list(zip(x_in[::-1], y_in[::-1]))
    ax.add_patch(patches.Polygon(bend_poly, closed=True, facecolor="#bae6fd", alpha=0.65, zorder=2))
    ax.plot(x_out, y_out, color="#0f172a", lw=2.4, zorder=4)
    ax.plot(x_in, y_in, color="#0f172a", lw=2.4, zorder=4)
    ax.plot([0, 0], [r_in, r_out], color="#dc2626", ls="--", lw=2.0, zorder=5)
    ax.plot([0, 0], [-r_out, -r_in], color="#dc2626", ls="--", lw=2.0, zorder=5)

    # Straight pipe stubs on left
    ax.plot([-1.4, 0], [r_out, r_out], color="#64748b", lw=1.6)
    ax.plot([-1.4, 0], [r_in, r_in], color="#64748b", lw=1.6)
    ax.plot([-1.4, 0], [-r_in, -r_in], color="#64748b", lw=1.6)
    ax.plot([-1.4, 0], [-r_out, -r_out], color="#64748b", lw=1.6)

    # Section 1-1 & 2-2 forces (both push control volume RIGHT!)
    ax.annotate("", xy=(-0.05, 1.0), xytext=(-1.05, 1.0),
                arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.4), zorder=6)
    ax.text(-1.12, 1.0, r"$P_1 = pA$" + "\n" + r"$v_1 = +5.0\,\mathrm{m/s}$", fontsize=9.4, ha="right", va="center", color="#0369a1", fontweight="bold")

    ax.annotate("", xy=(-0.05, -1.0), xytext=(-1.05, -1.0),
                arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.4), zorder=6)
    ax.text(-1.12, -1.0, r"$P_2 = pA$" + "\n" + r"$v_2 = -5.0\,\mathrm{m/s}$", fontsize=9.4, ha="right", va="center", color="#0369a1", fontweight="bold")

    # Wall/bolt force on water Rx (LEFT) and water thrust on bend/bolts F (RIGHT)
    ax.annotate("", xy=(0.30, 0.0), xytext=(1.22, 0.0),
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.6), zorder=7)
    ax.text(1.36, 0.28, "弯管对水反力 " + r"$R_x$" + " (向左)\n" + "水流对弯管及螺钉拉力 " + r"$F$" + " (向右)",
            fontsize=9.5, ha="left", va="center", color="#b91c1c", fontweight="bold")
    ax.text(1.36, -0.35, r"$F = 2pA + 2\rho Q v$" + "\n" + r"$= 2513.3 + 1569.2 = 4082.5\,\mathrm{N}$",
            fontsize=9.8, ha="left", va="center", color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.32", facecolor="#fffbeb", edgecolor="#f59e0b"))

    ax.text(0.02, 1.38, "1—1", fontsize=9.5, ha="center", color="#b91c1c", fontweight="bold")
    ax.text(0.02, -1.48, "2—2", fontsize=9.5, ha="center", color="#b91c1c", fontweight="bold")

    ax.set_xlim(-2.45, 3.65)
    ax.set_ylim(-1.68, 1.65)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("解图 28：180° 水平弯管控制体水平动量方程受力图", fontsize=11, pad=6)
    plt.tight_layout()
    fig.savefig(fig_dir / "q28_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


# ==============================================================================
# Build 2015 Exam Paper (21 questions, 150 pts, 10 figures)
# ==============================================================================

def build_2015_paper() -> dict:
    questions = [
        # --- Section 1: 一、填空题（8 小题，每空格 2 分，共 40 分） ---
        {
            "id": "yzu-849-2015-01",
            "year": 2015,
            "no": 1,
            "type": "fill",
            "subType": "blank",
            "score": 8,
            "title": "牛顿内摩擦定律影响因素与温度对黏滞性的影响",
            "stem": "液体的内摩擦力与接触面积 ________ ，与流速梯度 ________ ，与正压力 ________ ，随液体温度的增加而 ________ 。",
            "note": "本小题共 4 个空，每空 2 分，共 8 分。",
            "figures": [],
            "shortAnswer": "成正比；成正比；无关；减小",
            "judgeAnswer": None,
            "answer": "成正比；成正比；无关；减小。",
            "analysis": (
                "根据牛顿内摩擦定律：\n\n"
                "$$\nT = \\tau A = \\mu A \\frac{\\mathrm{d}u}{\\mathrm{d}y}\n$$\n\n"
                "1. 内摩擦力 $T$ 与液层接触面积 $A$ **成正比**，与速度梯度 $\\frac{\\mathrm{d}u}{\\mathrm{d}y}$ **成正比**；\n\n"
                "2. 与固体库仑干摩擦不同，液体内摩擦力由分子内聚力与动量交换产生，与接触面上的正压力**无关**；\n\n"
                "3. 液体温度升高时分子间内聚力减弱，动力黏滞系数 $\\mu$ 显著减小，故液体内摩擦力随温度升高而**减小**（注意气体恰好相反）。"
            ),
            "analysisFigures": [],
            "pitfalls": "切忌将液体内摩擦规律与固体滑动摩擦混淆（固体摩擦与正压力成正比、与接触面积无关，液体恰好相反），也不要混淆温度对液体与气体黏度的相反影响。",
            "chapter": 1,
            "kps": ["牛顿内摩擦定律", "黏滞性与温度关系"],
            "method": "牛顿内摩擦定律与库仑摩擦对比法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2015-02",
            "year": 2015,
            "no": 2,
            "type": "fill",
            "subType": "mini-calc",
            "score": 8,
            "title": "一个工程大气压的四种常用压强单位换算",
            "stem": "一个工程大气压相当于 ________ $\\mathrm{N/cm^2}$， ________ $\\mathrm{mmHg}$， ________ $\\mathrm{mH_2O}$， ________ $\\mathrm{kPa}$。",
            "note": "本小题共 4 个空，每空 2 分，共 8 分。",
            "figures": [],
            "shortAnswer": "9.8（或 9.81）；735.6（或 736）；10；98（或 98.1）",
            "judgeAnswer": None,
            "answer": "$9.8\\,\\mathrm{N/cm^2}$（或 $9.81$）；$735.6\\,\\mathrm{mmHg}$（约 $736$）；$10\\,\\mathrm{mH_2O}$；$98\\,\\mathrm{kPa}$（或 $98.1$）。",
            "analysis": (
                "1 个工程大气压（$1\\,\\mathrm{at}$）定义为 $1\\,\\mathrm{kgf/cm^2}$：\n\n"
                "- 换算为 $\\mathrm{N/cm^2}$：$1\\,\\mathrm{kgf/cm^2} = 9.807\\,\\mathrm{N/cm^2} \\approx 9.8\\,\\mathrm{N/cm^2}$（常取 $9.8$ 或 $9.81$）；\n\n"
                "- 换算为 $\\mathrm{kPa}$：$9.807\\,\\mathrm{N/cm^2} = 9.807 \\times 10^4\\,\\mathrm{Pa} \\approx 98\\,\\mathrm{kPa}$（或 $98.1\\,\\mathrm{kPa}$）；\n\n"
                "- 换算为水柱高：$h_{\\mathrm{H_2O}} = \\frac{p}{\\rho g} = \\frac{9.807 \\times 10^4}{1000 \\times 9.807} = 10\\,\\mathrm{mH_2O}$；\n\n"
                "- 换算为水银柱高：$h_{\\mathrm{Hg}} = \\frac{10\\,\\mathrm{m}}{13.595} \\approx 0.7356\\,\\mathrm{m} = 735.6\\,\\mathrm{mmHg}$（工程常记作 $736\\,\\mathrm{mmHg}$）。"
            ),
            "analysisFigures": [],
            "pitfalls": "务必区分**工程大气压**（$1\\,\\mathrm{at} = 98.1\\,\\mathrm{kPa} = 10\\,\\mathrm{mH_2O} \\approx 736\\,\\mathrm{mmHg}$）与**标准物理大气压**（$1\\,\\mathrm{atm} = 101.325\\,\\mathrm{kPa} = 10.33\\,\\mathrm{mH_2O} = 760\\,\\mathrm{mmHg}$）。",
            "chapter": 2,
            "kps": ["压强单位换算", "工程大气压"],
            "method": "等压面静水压强递推法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2015-03",
            "year": 2015,
            "no": 3,
            "type": "fill",
            "subType": "blank",
            "score": 4,
            "title": "流量或管径变化对圆管雷诺数的影响",
            "stem": "两根水管，一根直径一定，流量逐渐增加，其雷诺数将 ________ ；另一根直径逐渐增大，但通过的流量恒定，雷诺数沿流程将 ________ 。",
            "note": "本小题共 2 个空，每空 2 分，共 4 分。",
            "figures": [],
            "shortAnswer": "增大；减小",
            "judgeAnswer": None,
            "answer": "增大；减小。",
            "analysis": (
                "由圆管连续性方程 $v = \\frac{4Q}{\\pi d^2}$，将流速代入圆管雷诺数定义式：\n\n"
                "$$\nRe = \\frac{vd}{\\nu} = \\frac{4Q}{\\pi \\nu d}\n$$\n\n"
                "1. 当管径 $d$ 一定时，$Re \\propto Q$，故流量逐渐增加时雷诺数将**增大**；\n\n"
                "2. 当流量 $Q$ 恒定时，$Re \\propto \\frac{1}{d}$，故管径沿流程逐渐增大时雷诺数将**减小**。"
            ),
            "analysisFigures": [],
            "pitfalls": "切勿只盯着 $Re = vd/\\nu$ 误以为管径 $d$ 增大雷诺数就增大！当流量 $Q$ 恒定时流速 $v \\propto d^{-2}$ 下降更快，综合结果是 $Re \\propto d^{-1}$ 随管径增大而减小。",
            "chapter": 4,
            "kps": ["雷诺数公式", "连续性方程"],
            "method": "水力半径与当量直径雷诺数流态判别法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2015-04",
            "year": 2015,
            "no": 4,
            "type": "fill",
            "subType": "mini-calc",
            "score": 4,
            "title": "圆管雷诺数计算与层紊流态判别",
            "stem": "水在直径为 $d = 1\\,\\mathrm{cm}$ 的圆管中流动时，流速 $v = 1\\,\\mathrm{m/s}$，运动黏滞系数 $\\nu = 0.01\\,\\mathrm{cm^2/s}$，则雷诺数 $Re$ 等于 ________ ，水流型态为 ________ 。",
            "note": "本小题共 2 个空，每空 2 分，共 4 分。",
            "figures": [],
            "shortAnswer": "10000；紊流",
            "judgeAnswer": None,
            "answer": "$10000$（或 $10^4$）；紊流。",
            "analysis": (
                "将各物理量统一换算为国际单位（或统一用厘米制）：\n\n"
                "- $d = 1\\,\\mathrm{cm} = 0.01\\,\\mathrm{m}$，$v = 1\\,\\mathrm{m/s}$，$\\nu = 0.01\\,\\mathrm{cm^2/s} = 1 \\times 10^{-6}\\,\\mathrm{m^2/s}$。\n\n"
                "代入雷诺数计算公式：\n\n"
                "$$\nRe = \\frac{vd}{\\nu} = \\frac{1 \\times 0.01}{1 \\times 10^{-6}} = 10000\n$$\n\n"
                "因 $Re = 10000 > Re_{\\mathrm{cr}} = 2300$（下临界雷诺数），故管内水流型态为**紊流**。"
            ),
            "analysisFigures": [],
            "pitfalls": "注意运动黏度单位换算：$1\\,\\mathrm{cm^2/s} = 10^{-4}\\,\\mathrm{m^2/s}$，故 $0.01\\,\\mathrm{cm^2/s} = 10^{-6}\\,\\mathrm{m^2/s}$，切勿少算两个数量级。",
            "chapter": 4,
            "kps": ["雷诺数与流态判别"],
            "method": "水力半径与当量直径雷诺数流态判别法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2015-05",
            "year": 2015,
            "no": 5,
            "type": "fill",
            "subType": "blank",
            "score": 4,
            "title": "有压管流自由出流与淹没出流测压管水头线终点位置",
            "stem": "对于有压管流自由出流，测压管水头线的终点在 ________ ；出口为淹没出流时，若下游水池中的流速水头不计，测压管水头线的终点在 ________ 。",
            "note": "本小题共 2 个空，每空 2 分，共 4 分。",
            "figures": [],
            "shortAnswer": "出口断面中心处；下游水池自由液面处",
            "judgeAnswer": None,
            "answer": "出口断面中心处；下游水池自由液面处。",
            "analysis": (
                "1. **自由出流**：管口直接排入大气，出口断面压强等于大气压（相对压强 $p = 0$），测压管水头 $z + \\frac{p}{\\rho g} = z_{\\text{口}}$，故测压管水头线的终点落在**出口断面中心处**；\n\n"
                "2. **淹没出流**：管口淹没在下游水池水面以下深 $h_s$ 处，出口断面压强等于同高度下游静水压强 $p = \\rho g h_s$，测压管水头 $z_{\\text{口}} + h_s = z_{\\text{下}}$，故测压管水头线的终点落在**下游水池自由液面处**。"
            ),
            "analysisFigures": [],
            "pitfalls": "注意区别总水头线与测压管水头线在自由出流出口处的终点：测压管水头线终止于出口断面中心，而总水头线高出出口中心一个流速水头 $\\frac{\\alpha v^2}{2g}$。",
            "chapter": 6,
            "kps": ["总水头线与测压管水头线", "简单短管出流"],
            "method": "短管出流能量方程与测压管水头线对比法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2015-06",
            "year": 2015,
            "no": 6,
            "type": "fill",
            "subType": "mini-calc",
            "score": 4,
            "title": "有压满流方形管道的湿周与水力半径",
            "stem": "方管的边长为 $a$，则管流的湿周等于 ________ ，水力半径等于 ________ 。",
            "note": "本小题共 2 个空，每空 2 分，共 4 分。",
            "figures": [],
            "shortAnswer": "4a；a/4",
            "judgeAnswer": None,
            "answer": "$4a$；$\\frac{a}{4}$。",
            "analysis": (
                "有压满流方管四条内壁均与水流接触，过水断面面积 $A = a^2$，湿周 $\\chi = 4a$，故水力半径：\n\n"
                "$$\nR = \\frac{A}{\\chi} = \\frac{a^2}{4a} = \\frac{a}{4}\n$$"
            ),
            "analysisFigures": [],
            "pitfalls": "注意题目为有压「管流」（四壁均湿润，$\\chi = 4a$），不同于明渠（顶面为自由水面不计湿周）。",
            "chapter": 4,
            "kps": ["湿周与水力半径"],
            "method": "水力半径与当量直径雷诺数流态判别法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2015-07",
            "year": 2015,
            "no": 7,
            "type": "fill",
            "subType": "blank",
            "score": 4,
            "title": "明渠均匀流水深及水力坡度与底坡的关系",
            "stem": "明渠均匀流的水深沿程 ________ ，水力坡度 $J$ ________ 明渠底坡 $i$。",
            "note": "本小题共 2 个空，每空 2 分，共 4 分。",
            "figures": [],
            "shortAnswer": "不变（保持不变）；等于",
            "judgeAnswer": None,
            "answer": "不变（保持不变）；等于。",
            "analysis": (
                "明渠恒定均匀流的典型水力特征为：过水断面形状、尺寸及正常水深 $h_0$ 沿程**保持不变**，断面平均流速沿程相等，故总水头线、水面线（测压管水头线）与渠底线三线相互平行，水力坡度 $J$、水面坡降 $J_p$ 与渠底底坡 $i$ 三者完全**相等**（$J = J_p = i$）。"
            ),
            "analysisFigures": [],
            "pitfalls": "",
            "chapter": 7,
            "kps": ["明渠均匀流特点"],
            "method": "明渠均匀流特征与形成条件判别法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2015-08",
            "year": 2015,
            "no": 8,
            "type": "fill",
            "subType": "blank",
            "score": 4,
            "title": "有涡流与无涡流的判别条件及流速势函数存在性",
            "stem": "有涡流与无涡流的判别条件是 ________ ，无涡流一定存在 ________ 。",
            "note": "本小题共 2 个空，每空 2 分，共 4 分。",
            "figures": [],
            "shortAnswer": "液体微团旋转角速度是否为零（是否有绕自身轴的旋转运动）；流速势函数",
            "judgeAnswer": None,
            "answer": "流体微团旋转角速度是否为零（$\\vec{\\omega} = \\frac{1}{2}\\nabla\\times\\vec{u}$ 是否为零，即流体微团是否绕自身轴线旋转）；流速势函数（$\\varphi$）。",
            "analysis": (
                "流体运动的旋涡特性取决于流体微团的旋转角速度矢量 $\\vec{\\omega} = \\frac{1}{2}\\nabla \\times \\vec{u}$：\n\n"
                "- 若 $\\vec{\\omega} \\neq \\vec{0}$，则微团绕自身瞬时轴线旋转，称为有涡流（有旋流）；\n\n"
                "- 若 $\\vec{\\omega} \\equiv \\vec{0}$（即 $\\omega_x = \\omega_y = \\omega_z = 0$），称为无涡流（无旋流），此时速度矢量满足全微分条件，**一定存在流速势函数 $\\varphi$**（又称有势流动）。"
            ),
            "analysisFigures": [],
            "pitfalls": "切忌把“有涡/无涡”误判为“流线是否弯曲”（自由涡流线为同心圆却属无旋流，直圆管层流流线为直线却属有旋流）。",
            "chapter": 5,
            "kps": ["无旋流判据", "流函数与势函数"],
            "method": "连续性与无旋性判据及流函数求单宽流量法",
            "difficulty": 1,
        },

        # --- Section 2: 二、简答题（7 小题，每小题 6 分，共 42 分） ---
        {
            "id": "yzu-849-2015-09",
            "year": 2015,
            "no": 9,
            "type": "short",
            "score": 6,
            "title": "实际液体黏滞性与内摩擦力产生条件的辨析",
            "stem": "“因为实际液体都存在黏滞性，所以任何情况下实际液体都存在内摩擦力”，这种说法对吗？为什么？",
            "note": "",
            "figures": [],
            "shortAnswer": "不对。实际液体虽具有黏滞性（μ≠0），但仅在液层间发生相对运动（du/dy≠0）时才表现出内摩擦力；静止或相对静止液体速度梯度为零，内摩擦力为零。",
            "judgeAnswer": None,
            "answer": "这种说法**不对**。由牛顿内摩擦定律 $\\tau = \\mu \\frac{\\mathrm{d}u}{\\mathrm{d}y}$ 可知，实际液体虽然具有固有属性黏滞性（$\\mu > 0$），但内摩擦力（切应力）的存在还必须以液层间存在**相对运动**（即速度梯度 $\\frac{\\mathrm{d}u}{\\mathrm{d}y} \\neq 0$）为前提。当实际液体处于静止状态、或作等速平动及等角速度刚体旋转等相对静止状态时，各液层间无相对滑移（$\\frac{\\mathrm{d}u}{\\mathrm{d}y} = 0$），此时黏滞性不表现出来，内摩擦力恒等于零。",
            "analysis": (
                "1. **明确判断**：题干说法**错误**。\n\n"
                "2. **定量理论依据**：根据牛顿内摩擦定律：\n\n"
                "$$\n\\tau = \\mu \\frac{\\mathrm{d}u}{\\mathrm{d}y}\n$$\n\n"
                "切应力 $\\tau$ 由液体物性参数动力黏滞系数 $\\mu$ 与运动学参数速度梯度 $\\frac{\\mathrm{d}u}{\\mathrm{d}y}$ 共同决定：\n\n"
                "- 黏滞性（$\\mu > 0$）是实际液体的**固有物理属性**，无论液体静止还是运动都始终存在；\n\n"
                "- 内摩擦力（$\\tau$）则是黏滞性在流动剪切变形中的**外在力学表现**。当液体处于绝对静止或相对静止（无相对剪切变形，$\\frac{\\mathrm{d}u}{\\mathrm{d}y} = 0$）时，尽管 $\\mu > 0$，但 $\\tau = 0$，不存在内摩擦力。"
            ),
            "analysisFigures": [],
            "pitfalls": "答题必须同时给出明确判断（“不对”）、写出牛顿内摩擦定律公式，并区分“固有属性（黏滞性）”与“力学表现（内摩擦力）”两个层次。",
            "chapter": 1,
            "kps": ["牛顿内摩擦定律", "液体黏滞性"],
            "method": "牛顿内摩擦定律与黏滞性物理本质辨析",
            "difficulty": 1,
            "rubric": [
                {"label": "明确指出该说法不对（错误）", "pts": 2},
                {"label": "结合牛顿内摩擦定律 τ = μ(du/dy) 说明黏滞性是固有属性，内摩擦力仅在存在相对运动（du/dy ≠ 0）时产生", "pts": 2},
                {"label": "指出静止或相对静止实际液体无速度梯度、故内摩擦力为零", "pts": 2},
            ],
        },
        {
            "id": "yzu-849-2015-10",
            "year": 2015,
            "no": 10,
            "type": "short",
            "score": 6,
            "title": "左半部浸水圆柱体在浮力作用下能否绕轴持续转动分析",
            "stem": "有一圆柱，其左半部在水作用下，受有浮力 $P_z$（见图示），在不考虑摩擦力的条件下，问圆柱在该浮力作用下能否绕其中心轴转动不息？",
            "note": "",
            "figures": [
                {"src": "figures/q10_orig.png", "caption": "题 10 图　左半部受水作用的圆柱体"}
            ],
            "shortAnswer": "不能转动。左半圆柱面各处静水压强均垂直指向圆心轴 O，故合力必过中心轴（Px 与 Pz 对中心轴的力矩大小相等、方向相反互相抵消），总力矩恒为零。",
            "judgeAnswer": None,
            "answer": "**不能转动**（保持静止平衡）。虽然单独看铅垂向上的浮力 $P_z$ 位于中心轴左侧、似乎产生顺时针力矩，但作用在左半圆柱曲面上的静水压力不仅有铅垂分力 $P_z$，还有水平向右的分力 $P_x$。由于静止液体压强处处垂直于作用面，左半圆柱面任一微元面积上的静水压力 $\\mathrm{d}\\vec{P}$ 均沿径向**严格通过圆柱中心轴 $O$**，对中心轴的力臂恒为零（等价地，$P_x$ 位于圆心下方产生的逆时针力矩与 $P_z$ 产生的顺时针力矩大小相等、方向相反、完全抵消），故静水总压力对中心轴的总力矩 $\\sum M_O \\equiv 0$，圆柱不可能转动（否则将违背能量守恒定律，构成第一类永动机）。",
            "analysis": (
                "1. **微元法（最本质证明）**：静止液体不能承受切应力，微元曲面上的静水压力 $\\mathrm{d}\\vec{P} = p\\,\\mathrm{d}\\vec{A}$ 方向必垂直于圆柱表面内法线，而圆弧的法线处处严格通过圆心 $O$。因此每个微元压力对中心轴 $O$ 的力矩 $\\mathrm{d}M_O = 0$，积分后总力矩恒为零：\n\n"
                "$$\n\\sum M_O = \\int \\mathrm{d}M_O = 0\n$$\n\n"
                "2. **分力力矩平衡视角**：静水总压力分解为水平分力 $P_x$（向右）与铅垂浮力 $P_z$（向上）：\n\n"
                "- 铅垂浮力 $P_z$ 作用线在中心轴 $O$ 左侧（力臂 $e_x = \\frac{4R}{3\\pi}$），对 $O$ 产生**顺时针**力矩 $M_{\\text{顺}} = P_z e_x$；\n\n"
                "- 水平总压力 $P_x$ 作用在形心（圆心高度）以下（因水深向下压强线性增大，压心在 $O$ 点下方距 $e_z$ 处），对 $O$ 产生**逆时针**力矩 $M_{\\text{逆}} = P_x e_z$；\n\n"
                "- 因为合力过圆心 $O$，必有 $P_z e_x = P_x e_z$，二者大小相等、方向相反、完全抵消，总力矩为零。\n\n"
                "3. **能量守恒佐证**：若圆柱在静水中无外界能量输入而持续转动做功，即成为违背热力学第一定律的第一类永动机，这在物理上是不可能的。"
            ),
            "analysisFigures": [
                {"src": "figures/q10_sol.png", "caption": "解图 10　圆柱面微元静水压力法向过圆心及分力力矩抵消示意"}
            ],
            "pitfalls": "切忌只盯题图标出的 $P_z$ 而忽略水平分力 $P_x$ 的反力矩！答出“各微元静水压力方向沿法线必过圆心 $O$”与“$P_x$ 和 $P_z$ 对轴力矩大小相等方向相反抵消”两条之一即可拿到满分，两条并写最稳妥。",
            "chapter": 2,
            "kps": ["平面与曲面静水总压力", "圆柱面静水压力合力过圆心"],
            "method": "等效自由液面+水平投影与铅垂压力体合成法",
            "difficulty": 2,
            "rubric": [
                {"label": "明确回答圆柱不能绕中心轴转动（保持静止）", "pts": 2},
                {"label": "指出静水压强垂直于圆柱面，微元压力及静水总压力合力均严格通过圆心轴 O，总力矩恒为零", "pts": 2},
                {"label": "说明水平分力 Px（作用于圆心下方产生逆时针力矩）与浮力 Pz（顺时针力矩）大小相等方向相反互相抵消", "pts": 2},
            ],
        },
        {
            "id": "yzu-849-2015-11",
            "year": 2015,
            "no": 11,
            "type": "short",
            "score": 6,
            "title": "变断面管道大小管径断面雷诺数比较与比值求解",
            "stem": "水流经变断面管道，已知小管径为 $d_1$，大管径为 $d_2$，$d_2 / d_1 = 2$，问哪个断面的雷诺数大，并求两断面雷诺数之比。",
            "note": "",
            "figures": [],
            "shortAnswer": "小管径断面（d1）雷诺数大；Re1 : Re2 = 2 : 1。",
            "judgeAnswer": None,
            "answer": "**小管径断面（$d_1$ 断面）的雷诺数大**，两断面雷诺数之比为 $\\frac{Re_1}{Re_2} = \\frac{d_2}{d_1} = 2$（即 $Re_1 : Re_2 = 2 : 1$）。",
            "analysis": (
                "恒定不可压缩管流满足连续性方程，两断面体积流量相等：\n\n"
                "$$\nQ = \\frac{\\pi}{4} d_1^2 v_1 = \\frac{\\pi}{4} d_2^2 v_2 \\implies \\frac{v_1}{v_2} = \\left(\\frac{d_2}{d_1}\\right)^2 = 4\n$$\n\n"
                "同一水流运动黏度 $\\nu$ 相同，分别写出两断面的雷诺数：\n\n"
                "$$\nRe_1 = \\frac{v_1 d_1}{\\nu} = \\frac{4Q}{\\pi \\nu d_1}, \\qquad Re_2 = \\frac{v_2 d_2}{\\nu} = \\frac{4Q}{\\pi \\nu d_2}\n$$\n\n"
                "两式相除得：\n\n"
                "$$\n\\frac{Re_1}{Re_2} = \\frac{v_1 d_1}{v_2 d_2} = \\frac{d_2}{d_1} = 2\n$$\n\n"
                "因此，**小管径断面 $d_1$ 的雷诺数大**，为大管径断面雷诺数的 $2$ 倍。"
            ),
            "analysisFigures": [],
            "pitfalls": "切勿把比值写成 $1:2$ 或 $4:1$；用 $Re = \\frac{4Q}{\\pi\\nu d} \\propto d^{-1}$ 可一步避免代错。",
            "chapter": 4,
            "kps": ["雷诺数公式", "连续性方程"],
            "method": "水力半径与当量直径雷诺数流态判别法",
            "difficulty": 1,
            "rubric": [
                {"label": "由连续性方程写出流量相等关系并推出流速比 v1/v2 = (d2/d1)² = 4（或 Re = 4Q/(πνd)）", "pts": 3},
                {"label": "明确指出小管径 d1 断面雷诺数大，并求得 Re1 / Re2 = 2", "pts": 3},
            ],
        },
        {
            "id": "yzu-849-2015-12",
            "year": 2015,
            "no": 12,
            "type": "short",
            "score": 6,
            "title": "无损失水平有压管流测压管水头线沿程升降及水平条件",
            "stem": "设有一水平压力管流，当不考虑水头损失影响时，其测压管水头线沿程下降、上升或水平的条件各是怎样的？",
            "note": "",
            "figures": [],
            "shortAnswer": "沿程下降：渐缩管（流速增大）；沿程上升：渐扩管（流速减小）；保持水平：等径管（流速不变）。",
            "judgeAnswer": None,
            "answer": "不计水头损失时，总水头 $H = \\left(z + \\frac{p}{\\rho g}\\right) + \\frac{\\alpha v^2}{2g} = \\text{常数}$（总水头线水平），水平管中 $z = \\text{常数}$，故测压管水头 $H_p = z + \\frac{p}{\\rho g} = H - \\frac{\\alpha v^2}{2g}$ 随流速变化：\n\n（1）**沿程下降**：管道断面沿程缩小（渐缩管），流速 $v$ 沿程增大，压能转化为动能，压强沿程减小；\n\n（2）**沿程上升**：管道断面沿程扩大（渐扩管），流速 $v$ 沿程减小，动能转化为压能，压强沿程增大；\n\n（3）**沿程水平**：管道断面不变（等径管），流速 $v$ 沿程不变，动能与压能无相互转化，压强沿程不变。",
            "analysis": (
                "对无水头损失（$h_w = 0$）的恒定水平有压管流列伯努利方程：\n\n"
                "$$\nz + \\frac{p}{\\rho g} + \\frac{\\alpha v^2}{2g} = H = \\mathrm{const}\n$$\n\n"
                "移项得测压管水头表达式：\n\n"
                "$$\nH_p = z + \\frac{p}{\\rho g} = H - \\frac{\\alpha v^2}{2g}\n$$\n\n"
                "由连续性方程 $Q = Av = \\mathrm{const}$，流速 $v$ 与过水断面面积 $A$ 成反比：\n\n"
                "1. **测压管水头线沿程下降** $\\iff \\frac{\\mathrm{d}H_p}{\\mathrm{d}s} < 0 \\iff v$ 沿程增大 $\\iff$ 断面面积 $A$ 沿程减小（**渐缩管**）；\n\n"
                "2. **测压管水头线沿程上升** $\\iff \\frac{\\mathrm{d}H_p}{\\mathrm{d}s} > 0 \\iff v$ 沿程减小 $\\iff$ 断面面积 $A$ 沿程增大（**渐扩管**）；\n\n"
                "3. **测压管水头线沿程水平** $\\iff \\frac{\\mathrm{d}H_p}{\\mathrm{d}s} = 0 \\iff v$ 沿程不变 $\\iff$ 断面面积 $A$ 沿程不变（**等径管**）。"
            ),
            "analysisFigures": [],
            "pitfalls": "注意题目明确前提是“不考虑水头损失”，所以总水头线为水平直线，等径管时测压管水头线水平（若有水头损失则等径管测压管水头线应沿程下降）。",
            "chapter": 3,
            "kps": ["恒定总流能量方程", "总水头线与测压管水头线"],
            "method": "伯努利方程动能压能转化分析法",
            "difficulty": 1,
            "rubric": [
                {"label": "写出不计水头损失的伯努利方程 Hp = H - αv²/(2g)（总水头线水平）", "pts": 2},
                {"label": "正确给出下降（渐缩/流速增大）、上升（渐扩/流速减小）、水平（等径/流速不变）三种条件及对应能量转换", "pts": 4},
            ],
        },
        {
            "id": "yzu-849-2015-13",
            "year": 2015,
            "no": 13,
            "type": "short",
            "score": 6,
            "title": "达西公式分析层流 hf∝v 与紊流粗糙区 hf∝v² 的机理差异",
            "stem": "为何层流中沿程水头损失 $h_f \\propto v$，而在紊流水力粗糙区中 $h_f \\propto v^2$？试根据达西-威斯巴赫公式分析说明理由。",
            "note": "",
            "figures": [],
            "shortAnswer": "由 hf = λ(l/d)(v²/2g)：层流中 λ = 64/Re ∝ v⁻¹，代入得 hf ∝ v；紊流粗糙区中 λ 仅取决于相对粗糙度 Δ/d 而与 Re（v）无关，故 hf ∝ v²。",
            "judgeAnswer": None,
            "answer": "根据达西—威斯巴赫公式 $h_f = \\lambda \\frac{l}{d}\\frac{v^2}{2g}$：\n\n（1）**层流区**：液流以分子黏性剪切耗能为主，圆管沿程阻力系数 $\\lambda = \\frac{64}{Re} = \\frac{64\\nu}{vd} \\propto v^{-1}$，代入达西公式得 $h_f = \\frac{32\\nu l}{gd^2}v$，故沿程水头损失与流速的一次方成正比（$h_f \\propto v$）；\n\n（2）**紊流水力粗糙区（阻力平方区）**：黏性底层极薄，壁面粗糙凸起完全暴露于紊流核心中，阻力以粗糙凸起后的绕流压差阻力为主，$\\lambda$ 仅与相对粗糙度 $\\Delta/d$ 有关而与雷诺数 $Re$（即流速 $v$）无关、保持常数，故 $h_f = \\lambda \\frac{l}{d}\\frac{v^2}{2g} \\propto v^2$。",
            "analysis": (
                "1. **写出达西—威斯巴赫沿程水头损失公式**：\n\n"
                "$$\nh_f = \\lambda \\frac{l}{d}\\frac{v^2}{2g}\n$$\n\n"
                "2. **层流区机理与推导**：层流中流体分层有序运动，无横向脉动混掺，流动阻力完全来自黏性切应力，沿程阻力系数与雷诺数成反比：\n\n"
                "$$\n\\lambda = \\frac{64}{Re} = \\frac{64\\nu}{vd}\n$$\n\n"
                "代入达西公式消去一个 $v$：\n\n"
                "$$\nh_f = \\frac{64\\nu}{vd}\\cdot\\frac{l}{d}\\cdot\\frac{v^2}{2g} = \\frac{32\\nu l}{g d^2}\\,v \\implies h_f \\propto v\n$$\n\n"
                "3. **紊流水力粗糙区机理与推导**：在紊流粗糙区，黏性底层厚度远小于壁面绝对粗糙度（$\\delta \\ll \\Delta$），粗糙凸起全部穿出黏性底层，绕流旋涡与惯性压差阻力占主导地位。此时沿程阻力系数仅取决于相对粗糙度 $\\Delta/d$（如尼古拉兹公式 $\\frac{1}{\\sqrt{\\lambda}} = 2\\lg\\frac{3.7d}{\\Delta}$），与雷诺数 $Re$ 及流速 $v$ 无关，为定常数值，因此由达西公式直接得：\n\n"
                "$$\nh_f = \\lambda\\left(\\frac{\\Delta}{d}\\right)\\frac{l}{d}\\frac{v^2}{2g} \\implies h_f \\propto v^2\n$$"
            ),
            "analysisFigures": [],
            "pitfalls": "务必既从数学上代入 $\\lambda = 64/Re$ 与 $\\lambda = f(\\Delta/d)$ 完成推导，又点明“黏性摩阻主导”与“绕流压差阻力主导”的物理机理。",
            "chapter": 4,
            "kps": ["沿程与局部损失", "达西公式", "紊流阻力分区"],
            "method": "沿程阻力系数雷诺数依赖性与达西公式辨析",
            "difficulty": 2,
            "rubric": [
                {"label": "正确写出达西—威斯巴赫公式 hf = λ(l/d)(v²/2g)", "pts": 2},
                {"label": "代入层流阻力系数 λ = 64/Re ∝ 1/v，推导并说明层流中 hf ∝ v", "pts": 2},
                {"label": "说明紊流粗糙区 λ 仅与相对粗糙度 Δ/d 有关而与 Re（v）无关，故 hf ∝ v²", "pts": 2},
            ],
        },
        {
            "id": "yzu-849-2015-14",
            "year": 2015,
            "no": 14,
            "type": "short",
            "score": 6,
            "title": "底坡不同对矩形明渠正常水深与过流流量的双向影响分析",
            "stem": "两条矩形断面棱柱体渠道，底宽、粗糙系数均相同，但底坡 $i_1 > i_2$。试分析：（1）若两渠道流量相等，其正常水深是否相等？若不等，哪条大？（2）若两条渠道正常水深相等，其流量是否相等？若不等，哪条大？",
            "note": "",
            "figures": [],
            "shortAnswer": "（1）不相等，第 2 条（缓坡）正常水深大（h02 > h01）；（2）不相等，第 1 条（陡坡）流量大（Q1 > Q2）。",
            "judgeAnswer": None,
            "answer": "由明渠均匀流曼宁公式 $Q = \\frac{1}{n} A R^{2/3} i^{1/2} = K(h_0)\\sqrt{i}$，矩形渠道流量模数 $K(h_0)$ 随水深 $h_0$ 单调递增：\n\n（1）流量相等（$Q_1 = Q_2$）时，因 $i_1 > i_2$，有 $K(h_{01}) < K(h_{02})$，故两渠道正常水深**不相等，第 2 条渠道（底坡较小者）正常水深大**（$h_{02} > h_{01}$）；\n\n（2）正常水深相等（$h_{01} = h_{02}$）时，两渠道过水面积 $A$、水力半径 $R$ 及流量模数 $K$ 完全相同，因 $i_1 > i_2$，故流量**不相等，第 1 条渠道（底坡较大者）流量大**（$Q_1 > Q_2$）。",
            "analysis": (
                "矩形断面明渠均匀流流量由谢才—曼宁公式给出：\n\n"
                "$$\nQ = A C \\sqrt{R i} = \\frac{1}{n} A R^{2/3} i^{1/2} = K(h_0)\\sqrt{i}\n$$\n\n"
                "其中 $A = b h_0$，$R = \\frac{b h_0}{b + 2h_0}$，当底宽 $b$ 与糙率 $n$ 相同时，流量模数 $K(h_0) = \\frac{1}{n} A R^{2/3}$ 是正常水深 $h_0$ 的严格单调递增函数。\n\n"
                "**（1）当 $Q_1 = Q_2$ 时**：\n\n"
                "$$\nK(h_{01})\\sqrt{i_1} = K(h_{02})\\sqrt{i_2} \\implies \\frac{K(h_{01})}{K(h_{02})} = \\sqrt{\\frac{i_2}{i_1}} < 1\n$$\n\n"
                "即 $K(h_{01}) < K(h_{02})$，由单调性知 $h_{01} < h_{02}$，故正常水深**不相等，第 2 条渠道大**。\n\n"
                "**（2）当 $h_{01} = h_{02}$ 时**：两渠道 $A_1 = A_2$、$R_1 = R_2$、$K_1 = K_2$，故：\n\n"
                "$$\n\\frac{Q_1}{Q_2} = \\sqrt{\\frac{i_1}{i_2}} > 1\n$$\n\n"
                "即 $Q_1 > Q_2$，故流量**不相等，第 1 条渠道大**。"
            ),
            "analysisFigures": [],
            "pitfalls": "物理解释直观好记：底坡越陡，重力沿程分力越大、流速越快——同流量下所需水深更浅；同水深下泄流量更大。",
            "chapter": 7,
            "kps": ["曼宁公式", "明渠均匀流特点"],
            "method": "谢才—曼宁公式明渠均匀流水力计算法",
            "difficulty": 1,
            "rubric": [
                {"label": "写出谢才—曼宁公式 Q = (1/n) A R^(2/3) i^(1/2) = K(h0)√i 并指出 K(h0) 随水深单调递增", "pts": 2},
                {"label": "第（1）问推出 K1 < K2，得出正常水深不等且第 2 条渠道大（h02 > h01）", "pts": 2},
                {"label": "第（2）问由水深同则 K 相等，得出流量不等且第 1 条渠道大（Q1 > Q2）", "pts": 2},
            ],
        },
        {
            "id": "yzu-849-2015-15",
            "year": 2015,
            "no": 15,
            "type": "short",
            "score": 6,
            "title": "瞬时流速、脉动流速、时均流速与断面平均流速的定义及相互关系",
            "stem": "瞬时流速、脉动流速、时均流速和断面平均流速的定义及其相互关系怎样？",
            "note": "",
            "figures": [],
            "shortAnswer": "u = ū + u'（瞬时点流速等于时均流速与脉动流速之和，且 ū' = 0）；v = (1/A)∬ū dA = Q/A（断面平均流速为时均点流速在过水断面上的面积平均值）。",
            "judgeAnswer": None,
            "answer": "1. **定义**：\n\n- **瞬时流速 $u$**：某一瞬时通过流场中某固定空间点的流体质点的真实点流速；\n\n- **时均流速 $\\overline{u}$**：某固定空间点在足够长统计时段 $T$ 内瞬时流速的时间平均值，即 $\\overline{u} = \\frac{1}{T}\\int_t^{t+T} u\\,\\mathrm{d}t$；\n\n- **脉动流速 $u'$**：某瞬时该点的瞬时流速与时均流速之差，即 $u' = u - \\overline{u}$，反映紊流随机脉动强度；\n\n- **断面平均流速 $v$**：假设过水断面各点流速均匀分布且总流量不变时的等效平均流速，即 $v = \\frac{Q}{A} = \\frac{1}{A}\\iint_A \\overline{u}\\,\\mathrm{d}A$。\n\n2. **相互关系**：同一点处满足 $u = \\overline{u} + u'$（且脉动流速的时间平均值为零 $\\overline{u'} = 0$）；整个过水断面上，时均点流速的面积分平均即为断面平均流速 $v = \\frac{1}{A}\\iint_A \\overline{u}\\,\\mathrm{d}A$。",
            "analysis": (
                "在紊流分析中，雷诺分解将空间固定点 $(x,y,z)$ 的瞬时点流速分解为确定性时均项与零均值随机脉动项之和：\n\n"
                "$$\nu(x,y,z,t) = \\overline{u}(x,y,z) + u'(x,y,z,t)\n$$\n\n"
                "其中时均流速与脉动流速的时间平均分别满足：\n\n"
                "$$\n\\overline{u} = \\frac{1}{T}\\int_{t_0}^{t_0+T} u\\,\\mathrm{d}t, \\qquad \\overline{u'} = \\frac{1}{T}\\int_{t_0}^{t_0+T} (u - \\overline{u})\\,\\mathrm{d}t = 0\n$$\n\n"
                "进一步在总流分析中，将过水断面 $A$ 上各点的时均流速作空间面积平均，得到一元总流所使用的断面平均流速：\n\n"
                "$$\nv = \\frac{Q}{A} = \\frac{1}{A}\\iint_A \\overline{u}\\,\\mathrm{d}A\n$$\n\n"
                "四者的层级关系为：瞬时流速 $u$ $\\xrightarrow{\\text{时间平均}}$ 时均流速 $\\overline{u}$（差值为脉动流速 $u'$）$\\xrightarrow{\\text{断面空间平均}}$ 断面平均流速 $v$。"
            ),
            "analysisFigures": [],
            "pitfalls": "注意不要把“时均流速”（针对某固定点按时间平均）与“断面平均流速”（针对整个过水断面按面积平均）混为一谈。",
            "chapter": 4,
            "kps": ["紊流时均流速与脉动流速", "断面平均流速"],
            "method": "流态微观混掺与宏观阻力多维对比法",
            "difficulty": 1,
            "rubric": [
                {"label": "准确给出瞬时流速 u、时均流速 ū、脉动流速 u' 和断面平均流速 v 四个概念的定义", "pts": 4},
                {"label": "准确写出相互关系 u = ū + u'（ū' = 0）及 v = (1/A)∬ū dA = Q/A", "pts": 2},
            ],
        },

        # --- Section 3: 三、计算题（6 小题，共 68 分） ---
        {
            "id": "yzu-849-2015-16",
            "year": 2015,
            "no": 16,
            "type": "calc",
            "score": 10,
            "title": "上下双 U 形差压计联立测定容器内液体容重",
            "stem": "盛同一种液体的两容器，用两根 U 形差压计连接。上部差压计内盛容重为 $\\gamma_A$ 的液体，液面高差为 $A$；下部差压计内盛容重为 $\\gamma_B$ 的液体，液面高差为 $B$。求容器内液体的容重 $\\gamma$（用 $\\gamma_A$、$\\gamma_B$ 及 $A$、$B$ 表示）。",
            "note": "",
            "figures": [
                {"src": "figures/q16_orig.png", "caption": "题 16 图　双 U 形差压计连接两同液容器"}
            ],
            "shortAnswer": "γ = (γA·A + γB·B) / (A + B)",
            "judgeAnswer": None,
            "answer": "$\\gamma = \\frac{\\gamma_A A + \\gamma_B B}{A + B}$",
            "analysis": (
                "设左、右两开口容器的自由液面高程分别为 $z_1$、$z_2$（由题图知 $z_2 > z_1$，两容器液面均为大气压 $p_a = 0$）。\n\n"
                "**1. 对上部倒 U 形差压计列等压面方程**\n\n"
                "由题图知上部差压计内为轻质液体（$\\gamma_A < \\gamma$），左侧交界面低于右侧交界面高差 $A$。取上部差压计较高一侧交界面（或较低一侧交界面）水平面为等压面：\n\n"
                "设左侧交界面高程为 $z_3$，右侧交界面高程为 $z_3 + A$。在两侧交界面上方连通同种均质液体 $\\gamma_A$，故右侧交界面压强与左侧交界面压强相差 $\\gamma_A A$：\n\n"
                "$$\np_{\\text{左}} = p_{\\text{右}} + \\gamma_A A\n$$\n\n"
                "又左侧连通左容器，$p_{\\text{左}} = \\gamma(z_1 - z_3)$；右侧连通右容器，$p_{\\text{右}} = \\gamma[z_2 - (z_3 + A)]$，代入上式：\n\n"
                "$$\n\\gamma(z_1 - z_3) = \\gamma(z_2 - z_3 - A) + \\gamma_A A \\implies (\\gamma - \\gamma_A)A = \\gamma(z_2 - z_1) \\tag{1}\n$$\n\n"
                "**2. 对下部正 U 形差压计列等压面方程**\n\n"
                "由题图知下部差压计内为重质液体（$\\gamma_B > \\gamma$），左侧交界面高于右侧交界面高差 $B$。设右侧交界面高程为 $z_4$，左侧交界面高程为 $z_4 + B$。取较低的右侧交界面水平面为等压面：\n\n"
                "$$\n\\gamma[z_1 - (z_4 + B)] + \\gamma_B B = \\gamma(z_2 - z_4) \\implies (\\gamma_B - \\gamma)B = \\gamma(z_2 - z_1) \\tag{2}\n$$\n\n"
                "**3. 联立（1）、（2）消去两容器水位差 $(z_2 - z_1)$**\n\n"
                "$$\n(\\gamma - \\gamma_A)A = (\\gamma_B - \\gamma)B\n$$\n\n"
                "展开移项：\n\n"
                "$$\n\\gamma(A + B) = \\gamma_A A + \\gamma_B B \\implies \\gamma = \\frac{\\gamma_A A + \\gamma_B B}{A + B}\n$$"
            ),
            "analysisFigures": [
                {"src": "figures/q16_sol.png", "caption": "解图 16　上下双 U 形差压计等压面静力平衡示意"}
            ],
            "pitfalls": "取等压面时务必保证等压面上下位于**同一连续静止均质液体**内：上部倒 U 形管需取上侧（较轻液 $\\gamma_A$）连通面，下部正 U 形管需取下侧（较重液 $\\gamma_B$）连通面。",
            "chapter": 2,
            "kps": ["多液层压差计", "静水压强基本方程"],
            "method": "等压面静水压强递推法",
            "difficulty": 2,
            "rubric": [
                {"label": "对上部倒 U 形差压计列等压面方程，推出 (γ - γA)A = γ(z2 - z1)", "pts": 4},
                {"label": "对下部正 U 形差压计列等压面方程，推出 (γB - γ)B = γ(z2 - z1)", "pts": 4},
                {"label": "联立消去未知水位差，准确解得 γ = (γA·A + γB·B)/(A + B)", "pts": 2},
            ],
        },
        {
            "id": "yzu-849-2015-17",
            "year": 2015,
            "no": 17,
            "type": "calc",
            "score": 14,
            "title": "封闭负压水箱左侧测压管液面高与内凹半圆柱曲面静水总压力计算",
            "stem": "如图所示，一个封闭水箱，液面相对压强 $p_0 = -9.8\\,\\mathrm{kPa}$，右侧面有一个 $1/2$ 圆柱曲面 $ABC$，宽 $b = 1\\,\\mathrm{m}$（垂直于纸面方向），半径 $R = 1\\,\\mathrm{m}$，$H = 3\\,\\mathrm{m}$，试求：\n\n（1）水箱左侧的测压管中水柱高度 $h$；\n\n（2）曲面 $ABC$ 所受静水总压力的大小、方向和作用点位置。",
            "note": "题干给 $p_0 = -9.8\\,\\mathrm{kPa}$ 与 $g = 9.80\\,\\mathrm{m/s^2}$ 数值精确整除，主解按 $g = 9.80\\,\\mathrm{m/s^2}$ 给出（同时附注 $g = 9.81\\,\\mathrm{m/s^2}$ 数值）。",
            "figures": [
                {"src": "figures/q17_orig.png", "caption": "题 17 图　封闭水箱与右侧半圆柱曲面 ABC"}
            ],
            "shortAnswer": "（1）h = 2.00 m；（2）P = 24.92 kN（Px = 19.60 kN 向右，Pz = 15.39 kN 向上），与水平面成 38.15° 指向右上方、作用线过圆心 O（作用点在下半圆弧 BC 上，距 A 点铅垂深度 1.62 m）。",
            "judgeAnswer": None,
            "answer": "（1）左侧测压管水柱高度 $h = 2.00\\,\\mathrm{m}$；\n\n（2）曲面 $ABC$ 所受静水总压力大小 $P = 24.92\\,\\mathrm{kN}$（若取 $g = 9.81\\,\\mathrm{m/s^2}$ 则为 $24.96\\,\\mathrm{kN}$）；方向指向**右上方**，与水平方向夹角 $\\theta = 38.15^{\\circ}$；作用线**严格通过圆心 $O$**，作用点位于下半圆弧 $BC$ 上、距顶缘 $A$ 点铅垂深度 $1.62\\,\\mathrm{m}$（距底缘 $C$ 点铅垂高度 $0.38\\,\\mathrm{m}$）处。",
            "analysis": (
                "取重力加速度 $g = 9.80\\,\\mathrm{m/s^2}$，水密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$。\n\n"
                "**（1）求左侧测压管水柱高度 $h$**\n\n"
                "由题图虚线知，$h$ 自底缘 $C$ 点水平面起算（水箱自由液面距 $C$ 点高 $H = 3\\,\\mathrm{m}$）。在 $C$ 点水平面取等压面：\n\n"
                "$$\np_0 + \\rho g H = \\rho g h \\implies h = H + \\frac{p_0}{\\rho g} = 3 + \\frac{-9.8 \\times 10^3}{1000 \\times 9.80} = 3 - 1.0 = 2.00\\,\\mathrm{m}\n$$\n\n"
                "（物理意义：气室负压使水箱内相对压强为零的**等效自由液面**恰下降 $1.0\\,\\mathrm{m}$，即刚好与半圆柱顶缘 $A$ 点齐平，故 $p_A = 0$。若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $h = 2.001\\,\\mathrm{m}$。）\n\n"
                "**（2）求半圆柱曲面 $ABC$ 所受静水总压力的大小、方向与作用点**\n\n"
                "1. **水平分力 $P_x$**：曲面 $ABC$ 的铅垂投影为宽 $b = 1\\,\\mathrm{m}$、高 $2R = 2\\,\\mathrm{m}$ 的矩形，面积 $A_x = 2Rb = 2.0\\,\\mathrm{m^2}$。因等效自由液面恰过 $A$ 点，投影形心（圆心 $O$ 高度）在等效液面下深 $h_{c} = R = 1.0\\,\\mathrm{m}$：\n\n"
                "$$\nP_x = \\rho g h_c A_x = 1000 \\times 9.80 \\times 1.0 \\times 2.0 = 19600\\,\\mathrm{N} = 19.60\\,\\mathrm{kN} \\quad (\\text{水平向右})\n$$\n\n"
                "2. **铅垂分力 $P_z$**：由题图知半圆柱 $ABC$ 向水箱内部凸入，水位于上弧 $AB$ 的上方（实压力体向下压）和下弧 $BC$ 的下方（虚压力体向上托）。由于等效自由液面过 $A$ 点：\n\n"
                "- 上弧 $AB$ 向下实压力体体积为 $V_{AB} = \\left(R^2 - \\frac{1}{4}\\pi R^2\\right)b$；\n\n"
                "- 下弧 $BC$ 向上虚压力体体积为 $V_{BC} = \\left(R^2 + \\frac{1}{4}\\pi R^2\\right)b$；\n\n"
                "上下净合成即为半圆柱排开水体的向上浮力（体积 $V_z = V_{BC} - V_{AB} = \\frac{1}{2}\\pi R^2 b$）：\n\n"
                "$$\nP_z = \\rho g \\left(\\frac{1}{2}\\pi R^2 b\\right) = 1000 \\times 9.80 \\times \\frac{\\pi \\times 1^2}{2} \\times 1 = 15393.8\\,\\mathrm{N} \\approx 15.39\\,\\mathrm{kN} \\quad (\\text{竖直向上})\n$$\n\n"
                "3. **静水总压力合力大小、方向及作用点**：\n\n"
                "$$\nP = \\sqrt{P_x^2 + P_z^2} = \\sqrt{19.60^2 + 15.394^2} = 24.92\\,\\mathrm{kN}\n$$\n\n"
                "合力与水平向右方向的夹角：\n\n"
                "$$\n\\theta = \\arctan\\left(\\frac{P_z}{P_x}\\right) = \\arctan\\left(\\frac{\\pi}{4}\\right) = 38.15^{\\circ} \\quad (\\text{指向右上方})\n$$\n\n"
                "由于圆弧曲面各微元压力法线均过圆心 $O$，故总压力作用线**必通过圆心 $O$**，并由下半圆弧 $BC$ 指向右上方穿过 $O$ 点；作用点位于下半圆弧 $BC$ 上（相对圆心在水平线下方 $38.15^{\\circ}$），距 $A$ 点的铅垂深度为 $R + R\\sin 38.15^{\\circ} = 1 + 0.618 = 1.62\\,\\mathrm{m}$（距底缘 $C$ 高 $0.38\\,\\mathrm{m}$）。\n\n"
                "（注：若全程采用 $g = 9.81\\,\\mathrm{m/s^2}$，则 $P_x = 19.64\\,\\mathrm{kN}$，$P_z = 15.41\\,\\mathrm{kN}$，$P = 24.96\\,\\mathrm{kN}$，$\\theta = 38.12^{\\circ}$。）"
            ),
            "analysisFigures": [
                {"src": "figures/q17_sol.png", "caption": "解图 17　等效零压面与半圆柱曲面 ABC 静水总压力合成图"}
            ],
            "pitfalls": "本题有两个高频失分点：① 切勿忘记静水总压力单位是 $\\mathrm{kN}$（而非压强单位 $\\mathrm{kN/m^2}$）；② 确定作用点位置时，先看清 $P_x$ 向右、$P_z$ 向上，合力过圆心 $O$ 指向右上方，故受压作用点位于**下半圆弧 $BC$**（距 $A$ 点深 $R + R\\sin\\theta = 1.62\\,\\mathrm{m}$），切勿误算成 $2R - R\\sin\\theta = 1.38\\,\\mathrm{m}$！",
            "chapter": 2,
            "kps": ["平面与曲面静水总压力", "等效自由液面", "压力体图"],
            "method": "等效自由液面+水平投影与铅垂压力体合成法",
            "difficulty": 3,
            "rubric": [
                {"label": "由等压面关系求得左侧测压管水柱高度 h = H + p0/(ρg) = 2.00 m（指出等效自由液面过 A 点）", "pts": 4},
                {"label": "求得水平分力 Px = 19.60 kN（向右）和铅垂分力 Pz = 15.39 kN（向上）", "pts": 6},
                {"label": "合成总压力 P = 24.92 kN、倾角 θ = 38.15°（右上方）并指明作用线过圆心 O 及作用点在 BC 弧上", "pts": 4},
            ],
        },
        {
            "id": "yzu-849-2015-18",
            "year": 2015,
            "no": 18,
            "type": "calc",
            "score": 10,
            "title": "利用等径管段两测压管水头差测定 90° 弯管局部水头损失系数",
            "stem": "为测定 $90^{\\circ}$ 弯管的局部水头损失系数 $\\zeta$ 值，可采用如图所示的装置。已知 $AB$ 段管长 $l$ 为 $10\\,\\mathrm{m}$，管径 $d$ 为 $50\\,\\mathrm{mm}$，该管段的沿程阻力系数 $\\lambda$ 为 $0.03$，今测得实验数据：\n\n（1）$A$、$B$ 两测压管的水头差为 $0.629\\,\\mathrm{m}$；\n\n（2）经 $2\\,\\mathrm{min}$ 流入量水箱的水量为 $0.329\\,\\mathrm{m^3}$。\n\n试求弯管的局部水头损失系数 $\\zeta$ 值。",
            "note": "",
            "figures": [
                {"src": "figures/q18_orig.png", "caption": "题 18 图　90° 弯管局部水头损失系数测定装置"}
            ],
            "shortAnswer": "ζ ≈ 0.33（g = 9.81 时 0.330；g = 9.80 时 0.323）",
            "judgeAnswer": None,
            "answer": "$\\zeta \\approx 0.33$（取 $g = 9.81\\,\\mathrm{m/s^2}$ 时精确值为 $0.330$；取 $g = 9.80\\,\\mathrm{m/s^2}$ 时为 $0.323$）。",
            "analysis": (
                "**1. 计算管内体积流量 $Q$ 与断面平均流速 $v$**\n\n"
                "量水时间 $t = 2\\,\\mathrm{min} = 120\\,\\mathrm{s}$，流量与流速分别为：\n\n"
                "$$\nQ = \\frac{V}{t} = \\frac{0.329}{120} = 2.7417 \\times 10^{-3}\\,\\mathrm{m^3/s}\n$$\n\n"
                "$$\nA = \\frac{\\pi}{4} d^2 = \\frac{\\pi}{4} \\times 0.05^2 = 1.9635 \\times 10^{-3}\\,\\mathrm{m^2}\n$$\n\n"
                "$$\nv = \\frac{Q}{A} = \\frac{2.7417 \\times 10^{-3}}{1.9635 \\times 10^{-3}} = 1.3963\\,\\mathrm{m/s}\n$$\n\n"
                "**2. 对 $A$、$B$ 两断面列恒定总流能量方程**\n\n"
                "由题图可知，断面 $A$ 与断面 $B$ 位于同一等径管道上（$d_A = d_B = 50\\,\\mathrm{mm}$），故两断面流速相等（$v_A = v_B = v$），且动能修正系数 $\\alpha_A = \\alpha_B$，能量方程中的流速水头项在等式两侧**完全抵消**：\n\n"
                "$$\n\\left(z_A + \\frac{p_A}{\\rho g}\\right) + \\frac{\\alpha v^2}{2g} = \\left(z_B + \\frac{p_B}{\\rho g}\\right) + \\frac{\\alpha v^2}{2g} + h_{wA-B}\n$$\n\n"
                "整理得 $A$、$B$ 两测压管液面高差恰好等于 $AB$ 管段总水头损失（沿程损失与 $90^{\\circ}$ 弯管局部损失之和）：\n\n"
                "$$\nh_w = \\left(z_A + \\frac{p_A}{\\rho g}\\right) - \\left(z_B + \\frac{p_B}{\\rho g}\\right) = \\left(\\lambda \\frac{l}{d} + \\zeta\\right)\\frac{v^2}{2g}\n$$\n\n"
                "**3. 代入数值反求弯管局部阻力系数 $\\zeta$**\n\n"
                "取 $g = 9.81\\,\\mathrm{m/s^2}$，流速水头 $\\frac{v^2}{2g} = \\frac{1.3963^2}{2 \\times 9.81} = 0.09937\\,\\mathrm{m}$，沿程阻力项 $\\lambda \\frac{l}{d} = 0.03 \\times \\frac{10}{0.05} = 6.00$：\n\n"
                "$$\n6.00 + \\zeta = \\frac{0.629}{0.09937} = 6.3297 \\implies \\zeta = 0.330 \\approx 0.33\n$$\n\n"
                "（若取 $g = 9.80\\,\\mathrm{m/s^2}$，则 $\\frac{v^2}{2g} = 0.09947\\,\\mathrm{m}$，$\\zeta = 0.323$。）"
            ),
            "analysisFigures": [],
            "pitfalls": "关键易错点：等径管中断面 $A$ 与断面 $B$ 的流速水头完全相等并相互消去！切勿在能量方程右侧额外多加一个 $\\frac{v^2}{2g}$ 出口流速水头（测压管 $B$ 位于阀门及出口上游的管段内部，不是自由出流断面）。",
            "chapter": 4,
            "kps": ["沿程与局部损失", "恒定总流能量方程"],
            "method": "等径参考段消去沿程损失测局部阻力系数法",
            "difficulty": 2,
            "rubric": [
                {"label": "由量水体积与时间求得流量 Q = 2.742×10⁻³ m³/s 及管内平均流速 v = 1.396 m/s", "pts": 3},
                {"label": "对等径断面 A、B 列能量方程并消去流速水头项，得 hw = (λl/d + ζ)v²/(2g)", "pts": 4},
                {"label": "准确计算 λl/d = 6.00 并反求得弯管局部阻力系数 ζ ≈ 0.33（g=9.80 时 0.323）", "pts": 3},
            ],
        },
        {
            "id": "yzu-849-2015-19",
            "year": 2015,
            "no": 19,
            "type": "calc",
            "score": 14,
            "title": "水平自由射流斜冲固定平板的分流量与法向冲击力推导",
            "stem": "水平射流从喷嘴射出，冲击着一个与之成 $\\theta$ 角的斜置固定平板，如图所示。已知射流流量为 $Q_0$，流速大小为 $v_0$，液体密度为 $\\rho$，忽略水头损失，要求确定沿 $S$ 方向的分流量 $Q_1$、$Q_2$ 及射流对平板的冲击力。",
            "note": "",
            "figures": [
                {"src": "figures/q19_orig.png", "caption": "题 19 图　水平射流斜冲固定平板"}
            ],
            "shortAnswer": "Q1 = (Q0/2)(1 + cosθ)，Q2 = (Q0/2)(1 - cosθ)；冲击力 F = ρ Q0 v0 sinθ（垂直平板指向右下方）。",
            "judgeAnswer": None,
            "answer": "沿板面向上的分流量 $Q_1 = \\frac{1}{2}Q_0(1 + \\cos\\theta)$，沿板面向下的分流量 $Q_2 = \\frac{1}{2}Q_0(1 - \\cos\\theta)$；射流对平板的冲击力大小为 $F = \\rho Q_0 v_0 \\sin\\theta$，方向垂直于平板指向右下方。",
            "analysis": (
                "**1. 由能量方程确定各出流断面流速**\n\n"
                "自由射流在大气中运动，各过水断面相对压强均为零（$p_0 = p_1 = p_2 = 0$）。忽略重力高程差及水头损失，沿流线列伯努利方程得：\n\n"
                "$$\n\\frac{v_0^2}{2g} = \\frac{v_1^2}{2g} = \\frac{v_2^2}{2g} \\implies v_1 = v_2 = v_0\n$$\n\n"
                "**2. 联立连续性方程与沿平板切向 $S$ 动量方程求分流量 $Q_1$、$Q_2$**\n\n"
                "取冲击区流体为控制体，忽略平板壁面摩擦切力（$F_S = 0$），且不计重力。沿平板向上方向（$S$ 轴正向）列恒定总流动量方程（取 $\\beta = 1$）：\n\n"
                "$$\n0 = \\rho Q_1 v_1 - \\rho Q_2 v_2 - \\rho Q_0 v_0 \\cos\\theta\n$$\n\n"
                "代入 $v_1 = v_2 = v_0$ 并约去 $\\rho v_0$：\n\n"
                "$$\nQ_1 - Q_2 = Q_0 \\cos\\theta \\tag{1}\n$$\n\n"
                "由质量守恒（连续性方程）：\n\n"
                "$$\nQ_1 + Q_2 = Q_0 \\tag{2}\n$$\n\n"
                "联立（1）、（2）式解得两股分流量：\n\n"
                "$$\nQ_1 = \\frac{1}{2}Q_0(1 + \\cos\\theta) = Q_0\\cos^2\\frac{\\theta}{2}, \\qquad Q_2 = \\frac{1}{2}Q_0(1 - \\cos\\theta) = Q_0\\sin^2\\frac{\\theta}{2}\n$$\n\n"
                "**3. 沿垂直平板法向列动量方程求射流冲击力 $F$**\n\n"
                "取垂直平板指向水体（左上方）为 $n$ 轴正向，设平板对水流的法向支反力为 $R_n$（沿 $+n$ 方向）。由于 $Q_1$、$Q_2$ 均沿板面流动，法向速度分量为零，来流 $Q_0$ 在 $n$ 轴上的投影为 $-v_0\\sin\\theta$，由 $n$ 向动量方程：\n\n"
                "$$\nR_n = \\rho(Q_1 \\cdot 0 + Q_2 \\cdot 0) - \\rho Q_0(-v_0\\sin\\theta) = \\rho Q_0 v_0 \\sin\\theta\n$$\n\n"
                "由牛顿第三定律，射流对平板的冲击力大小为：\n\n"
                "$$\nF = R_n = \\rho Q_0 v_0 \\sin\\theta\n$$\n\n"
                "方向**垂直于平板指向右下方**。"
            ),
            "analysisFigures": [
                {"src": "figures/q19_sol.png", "caption": "解图 19　射流斜冲固定平板控制体切向与法向动量分析"}
            ],
            "pitfalls": "列切向动量方程时，流向与 $+S$ 反向的分流 $Q_2$ 动量通量为负值（$-\\rho Q_2 v_2$），流出项减流入项得 $\\rho Q_1 v_0 - \\rho Q_2 v_0 - \\rho Q_0 v_0\\cos\\theta = 0$，切勿漏写负号。",
            "chapter": 3,
            "kps": ["恒定总流能量方程", "恒定总流动量方程", "射流冲击平板"],
            "method": "能量方程求流速+动量方程切法向正交分解法",
            "difficulty": 2,
            "rubric": [
                {"label": "由忽略损失与重力的能量方程说明自由射流流速不变：v1 = v2 = v0", "pts": 3},
                {"label": "沿平板切向 S 列动量方程得 Q1 - Q2 = Q0 cosθ，联立 Q1 + Q2 = Q0 解得 Q1、Q2", "pts": 6},
                {"label": "沿垂直平板法向列动量方程求得射流对平板冲击力 F = ρQ0v0 sinθ 并指明方向", "pts": 5},
            ],
        },
        {
            "id": "yzu-849-2015-20",
            "year": 2015,
            "no": 20,
            "type": "calc",
            "score": 10,
            "title": "由实测流量与水面降落反求梯形引水明渠糙率",
            "stem": "为了收集某引水渠道糙率的资料，经实测得渠中流量 $Q = 9.45\\,\\mathrm{m^3/s}$ 时，水深 $h_0 = 1.20\\,\\mathrm{m}$；在长 $l = 200\\,\\mathrm{m}$ 的渠段内，水面降落 $\\Delta z = 0.16\\,\\mathrm{m}$。渠中水流近似为恒定均匀流。渠道横断面为梯形：底宽 $b = 7.0\\,\\mathrm{m}$，边坡系数 $m = 1.5$。试确定该渠道的糙率值。",
            "note": "",
            "figures": [],
            "shortAnswer": "n ≈ 0.030（精确值 0.0302）",
            "judgeAnswer": None,
            "answer": "该渠道的糙率 $n = 0.0302 \\approx 0.030$。",
            "analysis": (
                "**1. 计算梯形过水断面水力要素**\n\n"
                "- 过水断面面积：\n\n"
                "$$\nA = (b + m h_0)h_0 = (7.0 + 1.5 \\times 1.20) \\times 1.20 = 8.80 \\times 1.20 = 10.56\\,\\mathrm{m^2}\n$$\n\n"
                "- 湿周：\n\n"
                "$$\n\\chi = b + 2h_0\\sqrt{1 + m^2} = 7.0 + 2 \\times 1.20 \\times \\sqrt{1 + 1.5^2} = 7.0 + 2.40 \\times 1.8028 = 11.327\\,\\mathrm{m}\n$$\n\n"
                "- 水力半径：\n\n"
                "$$\nR = \\frac{A}{\\chi} = \\frac{10.56}{11.327} = 0.9323\\,\\mathrm{m}\n$$\n\n"
                "**2. 计算均匀流水力坡度（等于底坡）**\n\n"
                "$$\ni = J = \\frac{\\Delta z}{l} = \\frac{0.16}{200} = 0.0008\n$$\n\n"
                "**3. 代入谢才—曼宁公式反求糙率 $n$**\n\n"
                "由 $Q = \\frac{1}{n} A R^{2/3} i^{1/2}$ 解得：\n\n"
                "$$\nn = \\frac{A R^{2/3} i^{1/2}}{Q} = \\frac{10.56 \\times 0.9323^{2/3} \\times \\sqrt{0.0008}}{9.45} = \\frac{10.56 \\times 0.9543 \\times 0.028284}{9.45} = 0.03016 \\approx 0.030\n$$"
            ),
            "analysisFigures": [],
            "pitfalls": "注意梯形边坡湿周公式是 $b + 2h_0\\sqrt{1 + m^2}$，切勿遗漏根号内的 $1$ 或漏乘系数 $2$。",
            "chapter": 7,
            "kps": ["梯形断面水力要素", "曼宁公式"],
            "method": "谢才—曼宁公式明渠均匀流反算糙率法",
            "difficulty": 1,
            "rubric": [
                {"label": "准确计算梯形过水断面面积 A = 10.56 m²、湿周 χ = 11.33 m 及水力半径 R = 0.932 m", "pts": 4},
                {"label": "由水面降落求得均匀流底坡（水力坡度）i = Δz/l = 0.0008", "pts": 2},
                {"label": "代入曼宁公式反求得糙率 n ≈ 0.030（精确值 0.0302）", "pts": 4},
            ],
        },
        {
            "id": "yzu-849-2015-21",
            "year": 2015,
            "no": 21,
            "type": "calc",
            "score": 10,
            "title": "由流函数 ψ = x² - y² 求加速度、流线方程、无旋判别及单宽流量",
            "stem": "已知某平面不可压缩流场的流函数为 $\\psi = x^2 - y^2$。试求：\n\n（1）该流场的加速度分量 $a_x$、$a_y$ 的表达式；\n\n（2）过坐标点 $A(1, 2)$ 的流线方程，并判断该流场流速势函数是否存在；\n\n（3）通过点 $A(1, 2)$ 和点 $B(2, 5)$ 两点间连线的单宽流量。",
            "note": "",
            "figures": [],
            "shortAnswer": "（1）ax = 4x，ay = 4y；（2）过 A(1,2) 流线方程 x² - y² = -3（即 y² - x² = 3），无旋故存在流速势函数；（3）q = 18 m²/s。",
            "judgeAnswer": None,
            "answer": "（1）加速度分量 $a_x = 4x$，$a_y = 4y$；\n\n（2）过点 $A(1,2)$ 的流线方程为 $x^2 - y^2 = -3$（即 $y^2 - x^2 = 3$）；该流动无旋（$\\omega_z = 0$），故**存在流速势函数**（$\\varphi = -2xy + C$，或反号定义下 $\\varphi = 2xy + C$）；\n\n（3）通过 $A(1,2)$ 与 $B(2,5)$ 两点连线的单宽流量 $q = |\\psi_B - \\psi_A| = 18\\,\\mathrm{m^2/s}$。",
            "analysis": (
                "**（1）由流函数求速度场及欧拉法加速度分量**\n\n"
                "由流函数定义（$u_x = \\frac{\\partial\\psi}{\\partial y}$，$u_y = -\\frac{\\partial\\psi}{\\partial x}$）：\n\n"
                "$$\nu_x = \\frac{\\partial(x^2 - y^2)}{\\partial y} = -2y, \\qquad u_y = -\\frac{\\partial(x^2 - y^2)}{\\partial x} = -2x\n$$\n\n"
                "该流场不含时间 $t$，为恒定流（$\\frac{\\partial u_x}{\\partial t} = \\frac{\\partial u_y}{\\partial t} = 0$），故加速度由迁移加速度给出：\n\n"
                "$$\na_x = u_x\\frac{\\partial u_x}{\\partial x} + u_y\\frac{\\partial u_x}{\\partial y} = (-2y)(0) + (-2x)(-2) = 4x\n$$\n\n"
                "$$\na_y = u_x\\frac{\\partial u_y}{\\partial x} + u_y\\frac{\\partial u_y}{\\partial y} = (-2y)(-2) + (-2x)(0) = 4y\n$$\n\n"
                "（注：即使采用反号流函数约定 $u_x = -\\frac{\\partial\\psi}{\\partial y} = 2y, u_y = \\frac{\\partial\\psi}{\\partial x} = 2x$，算得的加速度分量依然严格为 $a_x = 4x$、$a_y = 4y$。）\n\n"
                "**（2）求过点 $A(1,2)$ 的流线方程并判别流速势函数是否存在**\n\n"
                "- **流线方程**：流线即等流函数线 $\\psi(x,y) = C$。将点 $A(1,2)$ 代入 $\\psi = x^2 - y^2$ 得 $C = 1^2 - 2^2 = -3$，故过点 $A(1,2)$ 的流线方程为等轴双曲线：\n\n"
                "$$\nx^2 - y^2 = -3 \\quad (\\text{即 } y^2 - x^2 = 3)\n$$\n\n"
                "- **流速势函数存在性判别**：计算平面流动旋转角速度（或检验拉普拉斯方程 $\\nabla^2\\psi = 0$）：\n\n"
                "$$\n\\omega_z = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} - \\frac{\\partial u_x}{\\partial y}\\right) = \\frac{1}{2}\\left[(-2) - (-2)\\right] = 0\n$$\n\n"
                "（亦满足 $\\frac{\\partial^2\\psi}{\\partial x^2} + \\frac{\\partial^2\\psi}{\\partial y^2} = 2 - 2 = 0$），表明该流动为**无旋流动**，因此**存在流速势函数**（可积得 $\\varphi = -2xy + C_1$）。\n\n"
                "**（3）求通过 $A(1,2)$、$B(2,5)$ 连线的单宽流量**\n\n"
                "由流函数的物理意义，两流线间的单宽流量等于两点流函数值之差的绝对值：\n\n"
                "$$\n\\psi_A = 1^2 - 2^2 = -3, \\qquad \\psi_B = 2^2 - 5^2 = -21\n$$\n\n"
                "$$\nq = |\\psi_B - \\psi_A| = |-21 - (-3)| = 18\\,\\mathrm{m^2/s}\n$$"
            ),
            "analysisFigures": [
                {"src": "figures/q21_sol.png", "caption": "解图 21　等流函数双曲线簇与 A、B 两点间单宽流量示意"}
            ],
            "pitfalls": "两大高频笔误警示：① 计算 $a_x = u_x \\frac{\\partial u_x}{\\partial x} + u_y \\frac{\\partial u_x}{\\partial y}$ 时，因 $u_x = -2y$ 仅含 $y$，非零项是 $u_y \\frac{\\partial u_x}{\\partial y} = (-2x)(-2) = 4x$（切勿把 $a_x$ 与 $a_y$ 写反成 $4y, 4x$！）；② 已知流函数 $\\psi = x^2 - y^2$ 时，流线直接就是 $\\psi = \\mathrm{const}$，即双曲线 $x^2 - y^2 = -3$，切勿误积分成圆 $x^2 + y^2 = 5$！",
            "chapter": 5,
            "kps": ["流函数与势函数", "欧拉法加速度", "无旋流判据", "单宽流量计算"],
            "method": "流函数求流速判无旋与全微分积分求势法",
            "difficulty": 3,
            "rubric": [
                {"label": "由流函数求得速度分量 ux = -2y, uy = -2x 并正确推出加速度分量 ax = 4x, ay = 4y", "pts": 4},
                {"label": "写出过 A(1,2) 流线方程 x² - y² = -3，并检验 ωz = 0（或 ∇²ψ = 0）判定存在流速势函数", "pts": 4},
                {"label": "由流函数差值求得通过 A、B 连线的单宽流量 q = |ψB - ψA| = 18 m²/s", "pts": 2},
            ],
        },
    ]

    return {
        "year": 2015,
        "code": "849",
        "subject": "水力学（水）",
        "school": "扬州大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": True,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试（A 卷）。",
            "全卷共 21 题：一、填空题（8 题共 20 空，每空 2 分，共 40 分）；二、简答题（7×6=42 分）；三、计算题（6 题共 68 分：10+14+10+14+10+10 分）。",
            "除特别说明外，水密度取 $\\rho = 1000\\,\\mathrm{kg/m^3}$，重力加速度取 $g = 9.80\\,\\mathrm{m/s^2}$ 或 $9.81\\,\\mathrm{m/s^2}$（以题干参数整除关系协调为准，并在解析中注明差异）。",
        ],
        "sections": [
            {
                "id": "fill",
                "title": "一、填空题",
                "description": "本大题共 8 小题（20 个空格，每空格 2 分），共 40 分。",
                "range": [1, 8],
                "totalScore": 40,
            },
            {
                "id": "short",
                "title": "二、简答题",
                "description": "本大题共 7 小题，每小题 6 分，共 42 分。",
                "range": [9, 15],
                "scorePerQuestion": 6,
                "totalScore": 42,
            },
            {
                "id": "calc",
                "title": "三、计算题",
                "description": "本大题共 6 小题（10+14+10+14+10+10 分），共 68 分。",
                "range": [16, 21],
                "totalScore": 68,
            },
        ],
        "questions": questions,
    }


# ==============================================================================
# Build 2014 Exam Paper (30 questions, 150 pts, 15 figures)
# ==============================================================================

def build_2014_paper() -> dict:
    questions = [
        # --- Section 1: 一、单项选择题（10 小题，每小题 2 分，共 20 分） ---
        {
            "id": "yzu-849-2014-01",
            "year": 2014,
            "no": 1,
            "type": "single_choice",
            "score": 2,
            "title": "液体容重（重度）的基本定义",
            "stem": "单位体积液体所具有的重量称为液体的（　）",
            "options": [
                {"label": "A", "text": "重量"},
                {"label": "B", "text": "质量"},
                {"label": "C", "text": "容重"},
                {"label": "D", "text": "密度"},
            ],
            "choiceAnswer": "C",
            "note": "",
            "figures": [],
            "shortAnswer": "C",
            "judgeAnswer": None,
            "answer": "C（容重）",
            "analysis": "容重（又称重度）定义为单位体积液体所受的重力：$\\gamma = \\frac{G}{V} = \\rho g$（单位 $\\mathrm{N/m^3}$）；而单位体积液体所具有的质量称为密度 $\\rho = \\frac{m}{V}$。故选 **C**。",
            "analysisFigures": [],
            "pitfalls": "注意区分容重（单位体积重量 $\\gamma$）与密度（单位体积质量 $\\rho$）。",
            "chapter": 1,
            "kps": ["密度与容重"],
            "method": "牛顿内摩擦定律与黏滞性物理本质辨析",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2014-02",
            "year": 2014,
            "no": 2,
            "type": "single_choice",
            "score": 2,
            "title": "引起液体运动机械能损失的主要物理性质",
            "stem": "对液体运动机械能损失起主要作用的物理性质是（　）",
            "options": [
                {"label": "A", "text": "易流性"},
                {"label": "B", "text": "粘滞性"},
                {"label": "C", "text": "压缩性"},
                {"label": "D", "text": "密度与容重"},
            ],
            "choiceAnswer": "B",
            "note": "",
            "figures": [],
            "shortAnswer": "B",
            "judgeAnswer": None,
            "answer": "B（粘滞性）",
            "analysis": "实际液体流动过程中克服内摩擦力做功，以及黏性引起的边界层分离与紊动旋涡耗散，是机械能不可逆转化为热能（水头损失）的根本原因。因此起主要作用的物理性质是**粘滞性**，选 **B**。",
            "analysisFigures": [],
            "pitfalls": "",
            "chapter": 1,
            "kps": ["液体黏滞性", "水头损失机理"],
            "method": "牛顿内摩擦定律与黏滞性物理本质辨析",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2014-03",
            "year": 2014,
            "no": 3,
            "type": "single_choice",
            "score": 2,
            "title": "单位质量力的量纲辨析",
            "stem": "与单位质量力具有相同量纲的物理量是（　）",
            "options": [
                {"label": "A", "text": "速度"},
                {"label": "B", "text": "质量"},
                {"label": "C", "text": "压强"},
                {"label": "D", "text": "加速度"},
            ],
            "choiceAnswer": "D",
            "note": "",
            "figures": [],
            "shortAnswer": "D",
            "judgeAnswer": None,
            "answer": "D（加速度）",
            "analysis": "单位质量力定义为作用在单位质量液体上的质量力 $\\vec{f} = \\frac{\\vec{F}_m}{m}$，其国际单位为 $\\mathrm{N/kg} = \\mathrm{m/s^2}$，量纲为 $[\\mathrm{L\\,T^{-2}}]$，与**加速度**的量纲完全相同（如重力场中单位质量力即为重力加速度 $\\vec{g}$）。故选 **D**。",
            "analysisFigures": [],
            "pitfalls": "",
            "chapter": 2,
            "kps": ["单位质量力与量纲"],
            "method": "静水基本方程力学与能量双重阐释法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2014-04",
            "year": 2014,
            "no": 4,
            "type": "single_choice",
            "score": 2,
            "title": "双层静止液体作用在倾斜挡水平面上的静水压强分布图判别",
            "stem": "挡水平面 $AB$ 上的静水压强分布图应为（　）",
            "options": [
                {"label": "A", "text": "图 A（法向箭头、交界面连续且下层增长更陡）"},
                {"label": "B", "text": "图 B（法向箭头、交界面连续但下层增长变缓）"},
                {"label": "C", "text": "图 C（交界面处压强出现突变台阶）"},
                {"label": "D", "text": "图 D（水平箭头、未垂直于斜面 AB）"},
            ],
            "choiceAnswer": "A",
            "note": "",
            "figures": [
                {"src": "figures/q04_orig.png", "caption": "题 4 图　双层液体作用在斜平面 AB 上的静水压强分布选项"}
            ],
            "shortAnswer": "A",
            "judgeAnswer": None,
            "answer": "A",
            "analysis": (
                "由静水压强两个核心特性逐一排查：\n\n"
                "1. **方向垂直于受压面**：静水压强总是垂直指向受压斜平面 $AB$，故 **D**（水平箭头）错误；\n\n"
                "2. **分界面处压强连续**：静止流体交界面两侧压强相等（$p_1 = p_2$），不可出现台阶突变，故 **C** 错误；\n\n"
                "3. **下层液体密度更大（$\\rho_2 > \\rho_1$）**：沿斜面深度增长时，上层压强梯度为 $\\rho_1 g\\sin\\alpha$，下层压强梯度为 $\\rho_2 g\\sin\\alpha > \\rho_1 g\\sin\\alpha$，故压强分布包络线过分界面后向外折转、增长更陡，**A** 正确（**B** 向内折转反常对应 $\\rho_2 < \\rho_1$）。"
            ),
            "analysisFigures": [],
            "pitfalls": "仔细看清 A 与 B 在分界面处的折转方向：下层重液 $\\rho_2 > \\rho_1$ 使压强随深度增加得更快，包络线必须向外张开（A）。",
            "chapter": 2,
            "kps": ["静水压强特性", "双层液体静水压强分布"],
            "method": "平面静水总压力解析法与平行移轴求压心法",
            "difficulty": 2,
        },
        {
            "id": "yzu-849-2014-05",
            "year": 2014,
            "no": 5,
            "type": "single_choice",
            "score": 2,
            "title": "欧拉液体平衡微分方程的物理含义",
            "stem": "液体平衡微分方程式表明：平衡液体中，静水压强沿某一方向的变化率与该方向上（　）",
            "options": [
                {"label": "A", "text": "单位体积上的质量力相等"},
                {"label": "B", "text": "单位体积上的重力相等"},
                {"label": "C", "text": "单位体积上的惯性力相等"},
                {"label": "D", "text": "单位体积上的粘滞力相等"},
            ],
            "choiceAnswer": "A",
            "note": "",
            "figures": [],
            "shortAnswer": "A",
            "judgeAnswer": None,
            "answer": "A（单位体积上的质量力相等）",
            "analysis": (
                "欧拉液体平衡微分方程为：\n\n"
                "$$\n\\frac{\\partial p}{\\partial x} = \\rho f_x, \\qquad \\frac{\\partial p}{\\partial y} = \\rho f_y, \\qquad \\frac{\\partial p}{\\partial z} = \\rho f_z\n$$\n\n"
                "式中 $\\rho$ 为单位体积液体的质量，$f_x, f_y, f_z$ 为单位质量力分量，故右端 $\\rho f_i$ 表示该方向上**单位体积液体所受的质量力**（包括重力以及相对平衡时的惯性力）。选 **A**。"
            ),
            "analysisFigures": [],
            "pitfalls": "切勿误选 B（仅重力）：欧拉平衡微分方程适用于任意质量力场（含等加速直线运动或等角速度旋转等相对平衡情形）。",
            "chapter": 2,
            "kps": ["欧拉平衡微分方程"],
            "method": "静水基本方程力学与能量双重阐释法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2014-06",
            "year": 2014,
            "no": 6,
            "type": "single_choice",
            "score": 2,
            "title": "流线的定义辨析",
            "stem": "流线表示（　）",
            "options": [
                {"label": "A", "text": "总水头线"},
                {"label": "B", "text": "某瞬时，其上任何一点流速与该曲线相切的线"},
                {"label": "C", "text": "测压管水头线"},
                {"label": "D", "text": "水流某质点在一个时段内运动的轨迹线"},
            ],
            "choiceAnswer": "B",
            "note": "",
            "figures": [],
            "shortAnswer": "B",
            "judgeAnswer": None,
            "answer": "B（某瞬时，其上任何一点流速与该曲线相切的线）",
            "analysis": "流线是欧拉法中描述瞬时速度场方向的空间曲线：在**某一给定瞬时**，曲线上每一点的切线方向都与该点此刻的流速矢量方向重合（**B**）；选项 D 描述的是拉格朗日法中的**迹线**。故选 **B**。",
            "analysisFigures": [],
            "pitfalls": "牢记“流线看瞬时空间切线，迹线看同一质点时段轨迹”；恒定流时二者重合，非恒定流时一般不重合。",
            "chapter": 3,
            "kps": ["流线与迹线"],
            "method": "质点跟踪与流场定点观察对比法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2014-07",
            "year": 2014,
            "no": 7,
            "type": "single_choice",
            "score": 2,
            "title": "层流与紊流的划分依据",
            "stem": "将水流分为层流与紊流，依据的是（　）",
            "options": [
                {"label": "A", "text": "水流运动要素是否随时间变化"},
                {"label": "B", "text": "水流的流线是否为平行的直线"},
                {"label": "C", "text": "水流质点的运动状态"},
                {"label": "D", "text": "水流是否具有自由水面"},
            ],
            "choiceAnswer": "C",
            "note": "",
            "figures": [],
            "shortAnswer": "C",
            "judgeAnswer": None,
            "answer": "C（水流质点的运动状态）",
            "analysis": "A 是划分恒定流与非恒定流的依据；B 是划分均匀流与非均匀流的依据；D 是划分有压流与无压流（明渠流）的依据；**C（水流质点是否分层有序运动或存在随机混掺脉动）**才是划分层流与紊流的依据。故选 **C**。",
            "analysisFigures": [],
            "pitfalls": "",
            "chapter": 4,
            "kps": ["层流与紊流分类"],
            "method": "流态微观混掺与宏观阻力多维对比法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2014-08",
            "year": 2014,
            "no": 8,
            "type": "single_choice",
            "score": 2,
            "title": "恒定水位容器渐缩管出流的流动分类",
            "stem": "图示容器内水位保持不变时，沿渐缩管流动的水流为（　）",
            "options": [
                {"label": "A", "text": "恒定均匀流"},
                {"label": "B", "text": "恒定非均匀流"},
                {"label": "C", "text": "非恒定流均匀流"},
                {"label": "D", "text": "非恒定非均匀流"},
            ],
            "choiceAnswer": "B",
            "note": "",
            "figures": [
                {"src": "figures/q08_orig.png", "caption": "题 8 图　恒定水位水箱接渐缩管出流"}
            ],
            "shortAnswer": "B",
            "judgeAnswer": None,
            "answer": "B（恒定非均匀流）",
            "analysis": "容器内水位保持不变，故出流边界条件不随时间变化，管内各空间点流速、压强不随时间改变，属于**恒定流**；管道断面沿程缩小，由连续性方程知流速沿流程不断增大且流线汇聚不平行，属于**非均匀流**。综合为**恒定非均匀流**，选 **B**。",
            "analysisFigures": [],
            "pitfalls": "",
            "chapter": 3,
            "kps": ["恒定流与均匀流判别"],
            "method": "欧拉时空偏导数与流线几何特征分类法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2014-09",
            "year": 2014,
            "no": 9,
            "type": "single_choice",
            "score": 2,
            "title": "紊流水力光滑面与水力粗糙面的判别本质",
            "stem": "紊流的壁面为光滑面或粗糙面（　）",
            "options": [
                {"label": "A", "text": "取决于流速的大小"},
                {"label": "B", "text": "取决于固体边界本身是光滑的还是粗糙的"},
                {"label": "C", "text": "取决于粘性底层的厚度"},
                {"label": "D", "text": "取决于粘性底层与绝对粗糙度的相对大小"},
            ],
            "choiceAnswer": "D",
            "note": "",
            "figures": [],
            "shortAnswer": "D",
            "judgeAnswer": None,
            "answer": "D（取决于粘性底层与绝对粗糙度的相对大小）",
            "analysis": "水力光滑面与水力粗糙面是相对水力学概念，取决于黏性底层厚度 $\\delta$ 与壁面绝对粗糙高度 $\\Delta$ 的相对比值：当 $\\delta \\gg \\Delta$（粗糙凸起被黏性底层完全掩盖）为水力光滑面；当 $\\delta \\ll \\Delta$（粗糙凸起完全暴露于紊流核心）为水力粗糙面。故选 **D**。",
            "analysisFigures": [],
            "pitfalls": "",
            "chapter": 4,
            "kps": ["紊流阻力分区", "水力光滑面与粗糙面"],
            "method": "达西公式与莫迪图五区分类对比法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2014-10",
            "year": 2014,
            "no": 10,
            "type": "single_choice",
            "score": 2,
            "title": "梯形明渠底坡大小对均匀流正常水深的影响",
            "stem": "有两条梯形断面渠道 1 和 2，已知其流量、边坡系数、底宽和糙率相同，底坡 $i_1 > i_2$，则其均匀流水深 $h_{01}$ 和 $h_{02}$ 的关系为（　）",
            "options": [
                {"label": "A", "text": "$h_{01} > h_{02}$"},
                {"label": "B", "text": "$h_{01} = h_{02}$"},
                {"label": "C", "text": "$h_{01} < h_{02}$"},
                {"label": "D", "text": "$h_{01} \\le h_{02}$"},
            ],
            "choiceAnswer": "C",
            "note": "",
            "figures": [],
            "shortAnswer": "C",
            "judgeAnswer": None,
            "answer": "C（$h_{01} < h_{02}$）",
            "analysis": "由曼宁公式 $Q = K(h_0)\\sqrt{i}$，同流量下 $K(h_0) = \\frac{Q}{\\sqrt{i}}$。因 $i_1 > i_2$，得 $K(h_{01}) < K(h_{02})$；又梯形渠道流量模数 $K(h_0)$ 随水深单调递增，故必有 $h_{01} < h_{02}$。选 **C**。",
            "analysisFigures": [],
            "pitfalls": "",
            "chapter": 7,
            "kps": ["曼宁公式", "明渠均匀流"],
            "method": "谢才—曼宁公式明渠均匀流水力计算法",
            "difficulty": 1,
        },

        # --- Section 2: 二、填空题（10 小题，每空格 1 分，共 20 分） ---
        {
            "id": "yzu-849-2014-11",
            "year": 2014,
            "no": 11,
            "type": "fill",
            "subType": "blank",
            "score": 2,
            "title": "温度对水黏滞系数的影响与运动黏滞系数之量纲",
            "stem": "水的粘滞系数随温度的升高而 ________ ，运动粘滞系数的量纲是 ________ 。",
            "note": "本小题共 2 个空，每空 1 分，共 2 分。",
            "figures": [],
            "shortAnswer": "减小；L²T⁻¹",
            "judgeAnswer": None,
            "answer": "减小；$\\mathrm{L^2\\,T^{-1}}$。",
            "analysis": "水的温度升高时分子内聚力减弱，故动力与运动黏滞系数均**减小**；运动黏滞系数 $\\nu = \\mu / \\rho$，国际单位为 $\\mathrm{m^2/s}$，对应量纲为 $\\mathrm{L^2\\,T^{-1}}$。",
            "analysisFigures": [],
            "pitfalls": "注意“量纲”应写作 $\\mathrm{L^2\\,T^{-1}}$（国际单位为 $\\mathrm{m^2/s}$），不要把动力黏度与运动黏度混淆。",
            "chapter": 1,
            "kps": ["黏滞性与温度关系", "运动黏滞系数量纲"],
            "method": "牛顿内摩擦定律量纲导出法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2014-12",
            "year": 2014,
            "no": 12,
            "type": "fill",
            "subType": "blank",
            "score": 2,
            "title": "理想液体与不可压缩液体模型的基本假设",
            "stem": "在理想液体模型中，不考虑液体的 ________ 性；而在不可压缩液体模型中，则不考虑液体的 ________ 性。",
            "note": "本小题共 2 个空，每空 1 分，共 2 分。",
            "figures": [],
            "shortAnswer": "粘滞（黏滞）；压缩",
            "judgeAnswer": None,
            "answer": "粘滞（黏滞）；压缩。",
            "analysis": "理想液体是假想绝对无黏滞性（$\\mu = 0$）的液体；不可压缩液体是指密度为常数、体积不随压强变化（不考虑压缩性）的液体模型。",
            "analysisFigures": [],
            "pitfalls": "",
            "chapter": 1,
            "kps": ["理想液体假设", "不可压缩液体假设"],
            "method": "牛顿内摩擦定律与黏滞性物理本质辨析",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2014-13",
            "year": 2014,
            "no": 13,
            "type": "fill",
            "subType": "blank",
            "score": 2,
            "title": "测压管水头各项的物理名称",
            "stem": "测压管水头 $z + \\frac{p}{\\rho g}$ 中，$z$ 称为 ________ 水头，$\\frac{p}{\\rho g}$ 称为 ________ 水头。",
            "note": "本小题共 2 个空，每空 1 分，共 2 分。",
            "figures": [],
            "shortAnswer": "位置；压强",
            "judgeAnswer": None,
            "answer": "位置；压强。",
            "analysis": "在测压管水头 $H_p = z + \\frac{p}{\\rho g}$ 中，$z$ 为单位重量液体的位能即**位置水头**，$\\frac{p}{\\rho g}$ 为单位重量液体的压能即**压强水头**。",
            "analysisFigures": [],
            "pitfalls": "",
            "chapter": 2,
            "kps": ["位置水头与压强水头"],
            "method": "静水基本方程力学与能量双重阐释法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2014-14",
            "year": 2014,
            "no": 14,
            "type": "fill",
            "subType": "blank",
            "score": 2,
            "title": "水力学真空的绝对压强与相对压强判据",
            "stem": "当液体中出现水力学意义上的“真空”时，其绝对压强应小于 ________ 压强，而其 ________ 压强应为负值。",
            "note": "本小题共 2 个空，每空 1 分，共 2 分。",
            "figures": [],
            "shortAnswer": "当地大气；相对",
            "judgeAnswer": None,
            "answer": "当地大气；相对。",
            "analysis": "相对压强定义为 $p = p_{\\mathrm{abs}} - p_a$。当某点绝对压强低于**当地大气**压强（$p_{\\mathrm{abs}} < p_a$）时，其**相对**压强 $p < 0$（负压），即出现水力学意义上的真空，真空度 $p_v = p_a - p_{\\mathrm{abs}} = -p > 0$。",
            "analysisFigures": [],
            "pitfalls": "",
            "chapter": 2,
            "kps": ["绝对压强、相对压强与真空度"],
            "method": "等压面静水压强递推法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2014-15",
            "year": 2014,
            "no": 15,
            "type": "fill",
            "subType": "blank",
            "score": 2,
            "title": "总水头线降落高度与水力坡度定义",
            "stem": "两断面总水头线下降的高度就是这两个断面之间的 ________ ，该值与流动长度之比就是 ________ 。",
            "note": "本小题共 2 个空，每空 1 分，共 2 分。",
            "figures": [],
            "shortAnswer": "水头损失；水力坡度",
            "judgeAnswer": None,
            "answer": "水头损失（或总水头损失 $h_w$）；水力坡度（$J$）。",
            "analysis": "由实际液体恒定总流能量方程 $H_1 - H_2 = h_{w1-2}$，总水头线沿程降落高度即为两断面间的**水头损失**；单位流程上的水头损失 $J = \\frac{h_w}{l}$ 定义为**水力坡度**。",
            "analysisFigures": [],
            "pitfalls": "",
            "chapter": 3,
            "kps": ["总水头线与水力坡度"],
            "method": "总水头大小判别流向与恒定总流能量方程",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2014-16",
            "year": 2014,
            "no": 16,
            "type": "fill",
            "subType": "mini-calc",
            "score": 2,
            "title": "直径 D=1m 有压圆管的湿周与水力半径",
            "stem": "直径 $D = 1\\,\\mathrm{m}$ 的有压管流，其湿周为 ________ $\\mathrm{m}$，水力半径为 ________ $\\mathrm{m}$。",
            "note": "本小题共 2 个空，每空 1 分，共 2 分。",
            "figures": [],
            "shortAnswer": "π（约 3.14）；0.25",
            "judgeAnswer": None,
            "answer": "$\\pi$（约 $3.14$）；$0.25$。",
            "analysis": "满流圆管湿周 $\\chi = \\pi D = \\pi \\times 1 = \\pi \\approx 3.14\\,\\mathrm{m}$，水力半径 $R = \\frac{A}{\\chi} = \\frac{D}{4} = \\frac{1}{4} = 0.25\\,\\mathrm{m}$。",
            "analysisFigures": [],
            "pitfalls": "",
            "chapter": 4,
            "kps": ["湿周与水力半径"],
            "method": "水力半径与当量直径雷诺数流态判别法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2014-17",
            "year": 2014,
            "no": 17,
            "type": "fill",
            "subType": "blank",
            "score": 2,
            "title": "雷诺试验中层流与紊流沿程水头损失的流速幂次规律",
            "stem": "雷诺试验表明：层流时，沿程水头损失与断面平均流速的 ________ 次方成正比；而紊流时，沿程水头损失与断面平均流速的 ________ 次方成正比。",
            "note": "本小题共 2 个空，每空 1 分，共 2 分。",
            "figures": [],
            "shortAnswer": "1（一）；1.75~2",
            "judgeAnswer": None,
            "answer": "$1$（一）；$1.75\\sim 2$。",
            "analysis": "雷诺管流阻力试验表明：层流区 $h_f \\propto v^1$（一次方）；紊流区随阻力分区由光滑区（布拉休斯公式 $h_f \\propto v^{1.75}$）过渡到粗糙区（阻力平方区 $h_f \\propto v^2$），指数介于 **$1.75\\sim 2$** 之间。",
            "analysisFigures": [],
            "pitfalls": "",
            "chapter": 4,
            "kps": ["雷诺试验", "沿程阻力规律"],
            "method": "沿程阻力系数雷诺数依赖性与达西公式辨析",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2014-18",
            "year": 2014,
            "no": 18,
            "type": "fill",
            "subType": "blank",
            "score": 2,
            "title": "平面流函数与速度势函数存在的充要条件",
            "stem": "流函数的存在条件是 ________ ，速度势函数的存在条件是 ________ 。",
            "note": "本小题共 2 个空，每空 1 分，共 2 分。",
            "figures": [],
            "shortAnswer": "平面不可压缩连续流动（满足连续性方程）；无旋流动",
            "judgeAnswer": None,
            "answer": "平面不可压缩连续流动（满足连续性方程 $\\frac{\\partial u_x}{\\partial x}+\\frac{\\partial u_y}{\\partial y}=0$）；无旋流动（$\\nabla\\times\\vec{u}=0$）。",
            "analysis": "平面流函数 $\\psi$ 的全微分存在条件即不可压缩平面连续性方程 $\\frac{\\partial u_x}{\\partial x}+\\frac{\\partial u_y}{\\partial y}=0$；速度势函数 $\\varphi$ 存在的充要条件是流动无旋（旋转角速度分量为零，$\\nabla\\times\\vec{u}=0$）。",
            "analysisFigures": [],
            "pitfalls": "",
            "chapter": 5,
            "kps": ["流函数与势函数"],
            "method": "连续性与无旋性判据及流函数求单宽流量法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2014-19",
            "year": 2014,
            "no": 19,
            "type": "fill",
            "subType": "blank",
            "score": 2,
            "title": "明渠均匀流三线平行特征",
            "stem": "明渠均匀流的 ________ 线、 ________ 线和渠底底坡线彼此平行。",
            "note": "本小题共 2 个空，每空 1 分，共 2 分。",
            "figures": [],
            "shortAnswer": "总水头；水面（测压管水头）",
            "judgeAnswer": None,
            "answer": "总水头；水面（或测压管水头）。",
            "analysis": "明渠均匀流水深 $h_0$ 与断面平均流速 $v$ 沿程不变，故**总水头线**、**水面线（测压管水头线）**与渠底底坡线三线彼此平行，坡度均相等（$J = J_p = i$）。",
            "analysisFigures": [],
            "pitfalls": "",
            "chapter": 7,
            "kps": ["明渠均匀流特点"],
            "method": "明渠均匀流特征与形成条件判别法",
            "difficulty": 1,
        },
        {
            "id": "yzu-849-2014-20",
            "year": 2014,
            "no": 20,
            "type": "fill",
            "subType": "blank",
            "score": 2,
            "title": "明渠水力最优断面的等价定义",
            "stem": "水力最优断面就是当渠道底坡 $i$、糙率 $n$ 及过水断面面积 $A$ 一定时， ________ 最大或 ________ 最小的断面。",
            "note": "本小题共 2 个空，每空 1 分，共 2 分。",
            "figures": [],
            "shortAnswer": "通过的流量（过流能力）；湿周",
            "judgeAnswer": None,
            "answer": "通过的流量 $Q$（过流能力）；湿周 $\\chi$。",
            "analysis": "由曼宁公式 $Q = \\frac{1}{n} A (A/\\chi)^{2/3} i^{1/2}$，当 $i, n, A$ 一定时，湿周 $\\chi$ 越小则水力半径 $R = A/\\chi$ 越大、通过的流量 $Q$ 越大，故水力最优断面即**通过的流量最大**或**湿周最小**的断面。",
            "analysisFigures": [],
            "pitfalls": "",
            "chapter": 7,
            "kps": ["水力最佳断面"],
            "method": "固定面积最小湿周微分极值推导法",
            "difficulty": 1,
        },

        # --- Section 3: 三、简答题（5 小题，每小题 8 分，共 40 分） ---
        {
            "id": "yzu-849-2014-21",
            "year": 2014,
            "no": 21,
            "type": "short",
            "score": 8,
            "title": "等面积正方形与圆形输水管道水力半径大小比较",
            "stem": "如图所示，过水断面面积相等的正方形和圆形输水管道，哪一个水力半径大？为什么？",
            "note": "",
            "figures": [
                {"src": "figures/q21_orig.png", "caption": "题 21 图　等面积圆形与正方形输水管道断面"}
            ],
            "shortAnswer": "圆形管道水力半径大（R圆 = √A/(2√π) ≈ 0.282√A > R方 = √A/4 = 0.250√A，比值 2/√π ≈ 1.128）。",
            "judgeAnswer": None,
            "answer": "**圆形输水管道的水力半径大**。设两满流管道的过水断面面积均为 $A$，则正方形管道湿周 $\\chi_{\\text{方}} = 4\\sqrt{A}$、水力半径 $R_{\\text{方}} = \\frac{\\sqrt{A}}{4} = 0.250\\sqrt{A}$；圆形管道湿周 $\\chi_{\\text{圆}} = 2\\sqrt{\\pi A}$、水力半径 $R_{\\text{圆}} = \\frac{\\sqrt{A}}{2\\sqrt{\\pi}} \\approx 0.282\\sqrt{A}$。因 $2\\sqrt{\\pi} \\approx 3.545 < 4$，相同面积下圆形湿周更小，故 $R_{\\text{圆}} > R_{\\text{方}}$。",
            "analysis": (
                "设圆形管道直径为 $D$，正方形管道边长为 $a$，两有压满流管道的过水断面面积相等均为 $A$：\n\n"
                "1. **正方形管道**：$A = a^2 \\implies a = \\sqrt{A}$，湿周 $\\chi_{\\text{方}} = 4a = 4\\sqrt{A}$，水力半径：\n\n"
                "$$\nR_{\\text{方}} = \\frac{A}{\\chi_{\\text{方}}} = \\frac{A}{4\\sqrt{A}} = \\frac{\\sqrt{A}}{4} = 0.250\\sqrt{A}\n$$\n\n"
                "2. **圆形管道**：$A = \\frac{\\pi}{4}D^2 \\implies D = \\frac{2\\sqrt{A}}{\\sqrt{\\pi}}$，湿周 $\\chi_{\\text{圆}} = \\pi D = 2\\sqrt{\\pi A}$，水力半径：\n\n"
                "$$\nR_{\\text{圆}} = \\frac{A}{\\chi_{\\text{圆}}} = \\frac{A}{2\\sqrt{\\pi A}} = \\frac{\\sqrt{A}}{2\\sqrt{\\pi}} \\approx 0.282\\sqrt{A}\n$$\n\n"
                "3. **比较结论**：\n\n"
                "$$\n\\frac{R_{\\text{圆}}}{R_{\\text{方}}} = \\frac{4}{2\\sqrt{\\pi}} = \\frac{2}{\\sqrt{\\pi}} \\approx 1.128 > 1\n$$\n\n"
                "在等面积的所有平面封闭图形中，圆的周长（湿周）最小，边壁摩阻接触周界最短，因此**圆形输水管道的水力半径更大**。"
            ),
            "analysisFigures": [],
            "pitfalls": "推导时需将 $D$ 与 $a$ 均用共同的过水断面面积 $A$ 表示后再作比（不要直接比较 $D/4$ 与 $a/4$ 而忘记 $D \\neq a$）。",
            "chapter": 4,
            "kps": ["湿周与水力半径", "水力最佳断面"],
            "method": "水力半径与当量直径雷诺数流态判别法",
            "difficulty": 1,
            "rubric": [
                {"label": "设两断面面积均为 A，正确导出正方形湿周 χ方 = 4√A 及水力半径 R方 = √A/4", "pts": 3},
                {"label": "正确导出圆形直径 D = 2√(A/π)、湿周 χ圆 = 2√(πA) 及水力半径 R圆 = √A/(2√π)", "pts": 3},
                {"label": "比较 2√π < 4 得出圆形水力半径大的结论", "pts": 2},
            ],
        },
        {
            "id": "yzu-849-2014-22",
            "year": 2014,
            "no": 22,
            "type": "short",
            "score": 8,
            "title": "30° 与 45° 大底坡均匀流明渠渠底动水压强计算与对比",
            "stem": "有两条渠道，其底面与水平面夹角分别为 $30^{\\circ}$ 和 $45^{\\circ}$（见图中 a、b）。设两渠中的水流为均匀流，与渠底垂直方向的水深为 $1\\,\\mathrm{m}$。试说明两渠渠底的动水压强是否相等，如不相等，各为多少？",
            "note": "",
            "figures": [
                {"src": "figures/q22_orig.png", "caption": "题 22 图　底坡倾角 30° 与 45° 的均匀流陡坡明渠"}
            ],
            "shortAnswer": "不相等。p = ρgh cosθ：30° 渠底动水压强为 8.50 kPa（g=9.80 时 8.49 kPa）；45° 渠底动水压强为 6.94 kPa（g=9.80 时 6.93 kPa）。",
            "judgeAnswer": None,
            "answer": "两渠渠底的动水压强**不相等**。均匀流过水断面（垂直于渠底）上满足静水压强分布规律 $z + \\frac{p}{\\rho g} = \\text{常数}$，故渠底动水压强 $p = \\rho g h\\cos\\theta$：\n\n- （a）$\\theta = 30^{\\circ}$ 渠道：$p_a = 1000 \\times 9.81 \\times 1 \\times \\cos 30^{\\circ} = 8.50\\,\\mathrm{kPa}$（若取 $g = 9.80\\,\\mathrm{m/s^2}$ 则为 $8.49\\,\\mathrm{kPa}$）；\n\n- （b）$\\theta = 45^{\\circ}$ 渠道：$p_b = 1000 \\times 9.81 \\times 1 \\times \\cos 45^{\\circ} = 6.94\\,\\mathrm{kPa}$（若取 $g = 9.80\\,\\mathrm{m/s^2}$ 则为 $6.93\\,\\mathrm{kPa}$）。",
            "analysis": (
                "1. **均匀流过水断面动水压强规律**\n\n"
                "明渠均匀流流线为相互平行的直线，垂直于流线（即垂直于渠底）的过水断面 $AC$ 上无向心加速度，满足静水压强分布规律（各点测压管水头相等）：\n\n"
                "$$\nz_A + \\frac{p_A}{\\rho g} = z_C + \\frac{p_C}{\\rho g}\n$$\n\n"
                "2. **几何高差与压强公式**\n\n"
                "自由水面点 $C$ 相对压强 $p_C = 0$。过水断面 $AC$ 长度即垂直渠底水深 $h = 1\\,\\mathrm{m}$，渠底倾角为 $\\theta$，故 $C$ 点与渠底 $A$ 点的铅垂高程差为 $z_C - z_A = h\\cos\\theta$。代入上式得渠底相对动水压强：\n\n"
                "$$\np_A = \\rho g (z_C - z_A) = \\rho g h \\cos\\theta\n$$\n\n"
                "3. **代入数值比较（取 $g = 9.81\\,\\mathrm{m/s^2}$）**\n\n"
                "- 渠道（a）（$\\theta = 30^{\\circ}$）：\n\n"
                "$$\np_a = 1000 \\times 9.81 \\times 1 \\times \\cos 30^{\\circ} = 8495.7\\,\\mathrm{Pa} \\approx 8.50\\,\\mathrm{kPa}\n$$\n\n"
                "- 渠道（b）（$\\theta = 45^{\\circ}$）：\n\n"
                "$$\np_b = 1000 \\times 9.81 \\times 1 \\times \\cos 45^{\\circ} = 6936.7\\,\\mathrm{Pa} \\approx 6.94\\,\\mathrm{kPa}\n$$\n\n"
                "（若取 $g = 9.80\\,\\mathrm{m/s^2}$，则分别为 $8.49\\,\\mathrm{kPa}$ 与 $6.93\\,\\mathrm{kPa}$。）因此两渠底动水压强**不相等**，倾角越大的渠道渠底动水压强越小。"
            ),
            "analysisFigures": [
                {"src": "figures/q22_sol.png", "caption": "解图 22　大底坡明渠过水断面铅垂高差 Δz = h cosθ 示意图"}
            ],
            "pitfalls": "切忌直接套用缓坡近似 $p = \\rho g h$！大底坡（$30^{\\circ}, 45^{\\circ}$）时过水断面与铅垂线夹角为 $\\theta$，压强等于 $\\rho g h\\cos\\theta$（仅当底坡极缓 $\\cos\\theta \\approx 1$ 时才近似取 $\\rho g h$）。",
            "chapter": 7,
            "kps": ["均匀流过水断面静水压强分布", "大底坡明渠压强"],
            "method": "明渠均匀流特征与形成条件判别法",
            "difficulty": 2,
            "rubric": [
                {"label": "指出均匀流过水断面满足 z + p/(ρg) = const，推导出渠底动水压强公式 p = ρgh cosθ", "pts": 4},
                {"label": "准确算得 30° 渠道 pa ≈ 8.50 kPa（8.49 kPa）与 45° 渠道 pb ≈ 6.94 kPa（6.93 kPa）并指出不相等", "pts": 4},
            ],
        },
        {
            "id": "yzu-849-2014-23",
            "year": 2014,
            "no": 23,
            "type": "short",
            "score": 8,
            "title": "管道突然扩大后总水头线先陡后缓与测压管水头线升高的机理分析",
            "stem": "如图所示为一突然扩大的管道，图中绘出了总水头线和测压管水头线。试解释管径突然扩大后，为什么总水头线变成先陡后缓的曲线，测压管水头线逐渐升高？",
            "note": "",
            "figures": [
                {"src": "figures/q23_orig.png", "caption": "题 23 图　突然扩大管段的总水头线与测压管水头线"}
            ],
            "shortAnswer": "（1）扩大初期旋涡剧烈、局部损失耗能率极大故总水头线陡降，随后旋涡消散转为大管沿程损失为主且流速小故变缓；（2）流速骤减释放的动能水头大于局部水头损失，余下动能转化为压能使测压管水头线逐渐回升。",
            "judgeAnswer": None,
            "answer": "1. **总水头线先陡后缓的原因**：管径突然扩大处，主流边界层分离并在拐角周围形成剧烈的旋涡区和强烈紊动混掺，产生较大的局部水头损失 $h_j = \\frac{(v_1 - v_2)^2}{2g}$，单位流程上的机械能耗散率极大，故总水头线在扩大初期急剧陡降；随着水流向下游扩散充满全断面、旋涡逐渐减弱消散，能量耗散过渡为以大管段沿程摩阻损失为主（且大管流速 $v_2 < v_1$、水力坡度 $J_2 \\ll J_1$），故总水头线逐渐变缓。\n\n2. **测压管水头线逐渐升高的原因**：管径扩大后流速由 $v_1$ 减小到 $v_2$，动能水头显著减少 $\\Delta\\left(\\frac{\\alpha v^2}{2g}\\right) = \\frac{\\alpha(v_1^2 - v_2^2)}{2g}$。由能量方程知，减少的动能除一部分耗散为局部水头损失 $h_j$ 外，剩余部分大于零（$\\Delta H_p = \\frac{v_1^2 - v_2^2}{2g} - \\frac{(v_1 - v_2)^2}{2g} = \\frac{v_2(v_1 - v_2)}{g} > 0$）并逐步转化为压能，因此测压管水头线沿扩散段逐渐升高。",
            "analysis": (
                "1. **总水头线斜率反映单位流程的能量耗散率 $\\left|\\frac{\\mathrm{d}H}{\\mathrm{d}s}\\right|$**\n\n"
                "- **紧接突扩处（陡降段）**：水流惯性使主流来不及紧贴大管壁面而发生边界层分离，在扩大角区形成大量剧烈旋转的漩涡，主流与旋涡区之间发生剧烈剪切与动量交换，集中耗散局部水头损失 $h_j = \\frac{(v_1 - v_2)^2}{2g}$，因此总水头线下降非常陡峭；\n\n"
                "- **下游恢复段（平缓段）**：经过约 $6\\sim 8$ 倍管径的扩散长度后，主流重新充满大管、旋涡消失，仅存大管段的沿程水头损失，且因流速 $v_2$ 远小于 $v_1$、大管径 $d_2 > d_1$，沿程水力坡度 $J_2 = \\lambda_2\\frac{v_2^2}{2g d_2} \\ll J_1$，总水头线变得非常平缓。\n\n"
                "2. **测压管水头线回升的能量转换定量证明**\n\n"
                "对突扩前后渐变流断面 1、2 列能量方程（近似取 $\\alpha \\approx 1$，略去短扩散段微小沿程损失）：\n\n"
                "$$\n\\left(z_2 + \\frac{p_2}{\\rho g}\\right) - \\left(z_1 + \\frac{p_1}{\\rho g}\\right) = \\frac{v_1^2 - v_2^2}{2g} - \\frac{(v_1 - v_2)^2}{2g} = \\frac{v_2(v_1 - v_2)}{g} > 0\n$$\n\n"
                "可见流速减小所释放的动能水头大于局部水头损失，净余动能随着主流扩散逐步转化为压能（压强水头），从而使测压管水头线沿扩散段逐渐升高。"
            ),
            "analysisFigures": [],
            "pitfalls": "解释测压管水头线升高时，不能只笼统说“流速减小所以压强增大”，必须点出关键前提：**动能水头的减少量大于局部水头损失**（写上定量式 $\\frac{v_2(v_1-v_2)}{g} > 0$ 更具说服力）。",
            "chapter": 4,
            "kps": ["边界层分离", "局部水头损失", "总水头线与测压管水头线"],
            "method": "边界层分离与摩擦压差阻力对比分析",
            "difficulty": 2,
            "rubric": [
                {"label": "指出突扩处旋涡强烈、局部水头损失集中导致总水头线先陡，下游旋涡消散转为大管沿程损失为主而变缓", "pts": 4},
                {"label": "结合能量方程说明流速减小释放的动能大于局部水头损失，余下动能转化为压能使测压管水头线逐渐升高", "pts": 4},
            ],
        },
        {
            "id": "yzu-849-2014-24",
            "year": 2014,
            "no": 24,
            "type": "short",
            "score": 8,
            "title": "等径抽水系统各特征点动水压强大小排序分析",
            "stem": "有一管径不变的抽水系统，如图所示。当水泵抽水流量一定时，试比较图中 1、2、3、4、5 各点动水压强的大小。",
            "note": "",
            "figures": [
                {"src": "figures/q24_orig.png", "caption": "题 24 图　等管径水泵抽水系统特征点位置"}
            ],
            "shortAnswer": "p4 > p1 = p5 > p2 > p3（4 点在水泵压水侧出口压强最高；1、5 点均为大气压；吸水管内 2、3 点为负压，3 点水泵进口真空度最大、压强最低）。",
            "judgeAnswer": None,
            "answer": "五点动水压强由大到小排序为：**$p_4 > p_1 = p_5 > p_2 > p_3$**。\n\n其中点 4 位于水泵压水出口，承受高扬程正压最大；点 1（下水池自由液面）与点 5（大气中自由出流管口）均直接通大气，相对压强均为零；点 2、点 3 位于吸水管内为真空负压，且点 3 位置更高、沿程损失更大，故点 3 压强最低。",
            "analysis": (
                "取下水池自由水面（点 1 所在水平面）为基准面 $z_1 = z_2 = 0$，各管段管径不变故管内平均流速均为 $v$（$v_2 = v_3 = v_4 = v_5 = v$），各压强均以相对压强（表压）计：\n\n"
                "1. **点 1 与点 5**：点 1 在下水池自由液面上，点 5 在大气中自由出流管口，两点均直接与大气相通，故：\n\n"
                "$$\np_1 = p_5 = 0\n$$\n\n"
                "2. **点 2（与点 1 同高程的吸水管内）**：对断面 1—2 列能量方程（$z_1 = z_2 = 0, v_1 \\approx 0$）：\n\n"
                "$$\n0 = 0 + \\frac{p_2}{\\rho g} + \\frac{\\alpha v^2}{2g} + h_{w1-2} \\implies \\frac{p_2}{\\rho g} = -\\left(\\frac{\\alpha v^2}{2g} + h_{w1-2}\\right) < 0\n$$\n\n"
                "故 $p_2 < p_1 = 0$。\n\n"
                "3. **点 3（水泵吸水进口，高程 $z_3 > 0$）**：对断面 2—3 列能量方程（$v_2 = v_3 = v$，动能水头抵消）：\n\n"
                "$$\n\\frac{p_2}{\\rho g} = z_3 + \\frac{p_3}{\\rho g} + h_{w2-3} \\implies \\frac{p_3}{\\rho g} = \\frac{p_2}{\\rho g} - z_3 - h_{w2-3} < \\frac{p_2}{\\rho g}\n$$\n\n"
                "故 $p_3 < p_2 < 0$（点 3 处真空度最大，是水泵最易发生汽蚀的部位）。\n\n"
                "4. **点 4（水泵压水出口，高程 $z_4 = z_3 < z_5$）**：水流经水泵获得机械能扬程 $H_p$ 后由点 4 流向更高处的出口点 5。对断面 4—5 列能量方程（$v_4 = v_5 = v$，$p_5 = 0$）：\n\n"
                "$$\nz_4 + \\frac{p_4}{\\rho g} + \\frac{\\alpha v^2}{2g} = z_5 + 0 + \\frac{\\alpha v^2}{2g} + h_{w4-5} \\implies \\frac{p_4}{\\rho g} = (z_5 - z_4) + h_{w4-5} > 0\n$$\n\n"
                "故 $p_4 > 0 = p_1 = p_5$。\n\n"
                "综上，五点动水压强大小严格满足：**$p_4 > p_1 = p_5 > p_2 > p_3$**。"
            ),
            "analysisFigures": [
                {"src": "figures/q24_sol.png", "caption": "解图 24　抽水系统水头线跃升与 1~5 点动水压强比较"}
            ],
            "pitfalls": "严重避坑提醒：点 3 与点 4 之间装有**水泵**，水泵对水流输入能量使总水头与压强急剧跃升！切忌忽略水泵把点 4 错推成比点 3 更低的负压（若 $p_4 < p_3 < 0$，水流根本不可能爬升到高处出口点 5）。",
            "chapter": 6,
            "kps": ["水泵水力特征", "恒定总流能量方程", "总水头线与测压管水头线"],
            "method": "分段能量方程求流量与水泵扬程功率法",
            "difficulty": 2,
            "rubric": [
                {"label": "指出点 1（自由水面）与点 5（大气自由出流）压强均为大气压：p1 = p5 = 0", "pts": 2},
                {"label": "对吸水管 1→2→3 列能量方程，推出 p3 < p2 < 0（3 点真空最大）", "pts": 3},
                {"label": "对压水管 4→5 列能量方程，推出 p4/(ρg) = (z5 - z4) + hw4-5 > 0，得出最终排序 p4 > p1 = p5 > p2 > p3", "pts": 3},
            ],
        },
        {
            "id": "yzu-849-2014-25",
            "year": 2014,
            "no": 25,
            "type": "short",
            "score": 8,
            "title": "用伯努利能量方程解释行船向水流较急一侧河岸靠拢现象",
            "stem": "试用能量方程式分析解释现象：在河里行走的船只，总是被迫向水流较急的一侧河岸靠拢。",
            "note": "",
            "figures": [],
            "shortAnswer": "由同水平面伯努利方程 p/(ρg) + v²/(2g) = const，急流侧流速大、动水压强小，缓流侧流速小、动水压强大，两侧压差产生指向急流侧河岸的横向推力使船靠拢。",
            "judgeAnswer": None,
            "answer": "取船体吃水线附近同一水平面（$z_1 = z_2$），忽略微距横向水头损失，由伯努利能量方程 $z + \\frac{p}{\\rho g} + \\frac{v^2}{2g} = \\text{常数}$ 可知：船体靠近水流较急河岸一侧流速 $v_1$ 较大，流速水头 $\\frac{v_1^2}{2g}$ 较大，故该侧水体动水压强 $p_1$ 较小；船体另一侧水流较缓、流速 $v_2$ 较小，动水压强 $p_2$ 较大。由此在船体两侧形成净横向压强差 $\\Delta p = p_2 - p_1 \\approx \\frac{1}{2}\\rho(v_1^2 - v_2^2) > 0$，产生指向水流较急一侧河岸的横向推力，迫使船只向该侧河岸靠拢。",
            "analysis": (
                "1. **建立能量方程**：选取船体两侧同一水深处的水平流线（$z_1 = z_2$），近似按理想流体列伯努利方程：\n\n"
                "$$\nz_1 + \\frac{p_1}{\\rho g} + \\frac{v_1^2}{2g} = z_2 + \\frac{p_2}{\\rho g} + \\frac{v_2^2}{2g}\n$$\n\n"
                "2. **比较两侧动水压强**：设 1 侧为水流较急侧（流速 $v_1$），2 侧为水流较缓侧（流速 $v_2 < v_1$），由 $z_1 = z_2$ 化简得两侧压强差：\n\n"
                "$$\np_2 - p_1 = \\frac{1}{2}\\rho(v_1^2 - v_2^2) > 0 \\implies p_2 > p_1\n$$\n\n"
                "3. **受力结果**：缓流侧较高的动水压强对船舷产生指向急流侧的净横向推力，因此河中行船总是被迫向水流较急的一侧河岸靠拢（同理，两艘并行航行的船只之间因水流狭窄加速降压也会相互吸引靠拢）。"
            ),
            "analysisFigures": [],
            "pitfalls": "表述中须明确“同一水平面（$z_1 = z_2$）”，再由伯努利方程得出“流速大处压强小、流速小处压强大”的因果链条。",
            "chapter": 3,
            "kps": ["恒定总流能量方程", "流速增大降压效应"],
            "method": "伯努利方程流速增大降压效应分析法",
            "difficulty": 1,
            "rubric": [
                {"label": "写出同一水平面（z1 = z2）的伯努利能量方程 p1/(ρg) + v1²/(2g) = p2/(ρg) + v2²/(2g)", "pts": 3},
                {"label": "由 v急 > v缓 推出 p急 < p缓（两侧压差 Δp = ρ(v急² - v缓²)/2 > 0）", "pts": 3},
                {"label": "指出横向压差推力指向急流侧河岸，从而解释船只被迫靠拢的现象", "pts": 2},
            ],
        },

        # --- Section 4: 四、计算题（5 小题，共 70 分） ---
        {
            "id": "yzu-849-2014-26",
            "year": 2014,
            "no": 26,
            "type": "calc",
            "score": 15,
            "title": "复式水银—水 U 形测压计与盛油容器顶部半球曲面静水总压力计算",
            "stem": "在容器上部有一半球曲面，如图所示，试求该曲面上所受的液体总压力的大小和方向。容器中充满密度为 $800\\,\\mathrm{kg/m^3}$ 的油。",
            "note": "由题图尺寸知：半球半径 $r = 10\\,\\mathrm{cm}$，容器高 $20\\,\\mathrm{cm}$，基准面 $A\\text{—}A$ 距容器底 $5\\,\\mathrm{cm}$，两段水银柱液面差均为 $10\\,\\mathrm{cm}$。",
            "figures": [
                {"src": "figures/q26_orig.png", "caption": "题 26 图　盛油容器顶部半球曲面与复式水银—水 U 形测压计"}
            ],
            "shortAnswer": "P = Pz = 754.0 N（取 g = 9.80 m/s² 时为 753.3 N），方向竖直向上。",
            "judgeAnswer": None,
            "answer": "半球曲面所受液体总压力大小 $P = P_z = 754.0\\,\\mathrm{N}$（若取 $g = 9.80\\,\\mathrm{m/s^2}$ 则为 $753.3\\,\\mathrm{N}$），方向**竖直向上**（作用线沿竖直对称轴通过球心 $O$）。",
            "analysis": (
                "已知油密度 $\\rho_o = 800\\,\\mathrm{kg/m^3}$，水密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$，水银密度 $\\rho_m = 13600\\,\\mathrm{kg/m^3}$，半球半径 $r = 0.10\\,\\mathrm{m}$（直径 $D = 0.20\\,\\mathrm{m}$），取 $g = 9.81\\,\\mathrm{m/s^2}$。\n\n"
                "**1. 由复式 U 形测压计递推求球心 $O$ 所在水平面处的油压 $p_O$**\n\n"
                "从最右侧通大气水银自由液面（相对压强为 $0$）向左逐段递推至容器顶部球心 $O$（基准面 $A\\text{—}A$ 位于球心 $O$ 以下 $0.20 - 0.05 = 0.15\\,\\mathrm{m}$ 处，每段水银与水柱高差均为 $0.10\\,\\mathrm{m}$）：\n\n"
                "$$\np_O = \\rho_m g \\times 0.10 - \\rho g \\times 0.10 + \\rho_m g \\times 0.10 - \\rho_o g \\times (0.20 - 0.05)\n$$\n\n"
                "$$\np_O = (0.20\\rho_m - 0.10\\rho - 0.15\\rho_o)g = (0.20 \\times 13600 - 0.10 \\times 1000 - 0.15 \\times 800) \\times 9.81\n$$\n\n"
                "$$\np_O = (2720 - 100 - 120) \\times 9.81 = 2500 \\times 9.81 = 24525\\,\\mathrm{Pa} = 24.525\\,\\mathrm{kPa}\n$$\n\n"
                "折算为高出球心 $O$ 所在平面的等效自由油面高度 $H$：\n\n"
                "$$\nH = \\frac{p_O}{\\rho_o g} = \\frac{2500}{800} = 3.125\\,\\mathrm{m}\n$$\n\n"
                "**2. 求半球曲面所受总压力的大小与方向**\n\n"
                "- **水平分力**：半球曲面关于竖直中心轴对称，各方向水平静水压力两两抵消，故 $P_x = P_y = 0$；\n\n"
                "- **铅垂分力**：油位于半球曲面**下方**并向上顶托，故压力体为向上作用的**虚压力体**，其体积等于以底圆面积 $\\pi r^2$ 为底、高 $H$ 的圆柱体体积减去向上凸起的半球自身体积 $\\frac{2}{3}\\pi r^3$：\n\n"
                "$$\nV_z = \\pi r^2 H - \\frac{2}{3}\\pi r^3 = \\pi \\times 0.10^2 \\times 3.125 - \\frac{2}{3}\\pi \\times 0.10^3 = 0.098175 - 0.002094 = 0.096080\\,\\mathrm{m^3}\n$$\n\n"
                "因此，半球曲面所受液体总压力为：\n\n"
                "$$\nP = P_z = \\rho_o g V_z = 800 \\times 9.81 \\times 0.096080 = 754.04\\,\\mathrm{N} \\approx 754.0\\,\\mathrm{N}\n$$\n\n"
                "方向**竖直向上**，作用线通过球心 $O$。（若取 $g = 9.80\\,\\mathrm{m/s^2}$，则 $p_O = 24.50\\,\\mathrm{kPa}$，$P_z = 753.27\\,\\mathrm{N} \\approx 753.3\\,\\mathrm{N}$。）"
            ),
            "analysisFigures": [
                {"src": "figures/q26_sol.png", "caption": "解图 26　盛油容器顶部半球曲面等效自由油面与虚压力体"}
            ],
            "pitfalls": "两大易错点：① 虚压力体体积必须是**圆柱减半球**（$\\pi r^2 H - \\frac{2}{3}\\pi r^3$），因半球向上凸起使球面高程高于 $O$、油压略小于 $p_O$；② 计算最终乘积 $7848 \\times 0.09608$ 时仔细核对十位与百位，严防把 $754.0\\,\\mathrm{N}$（或 $753.3\\,\\mathrm{N}$）误算写错。",
            "chapter": 2,
            "kps": ["多液层压差计", "平面与曲面静水总压力", "虚压力体"],
            "method": "等效自由液面+水平投影与铅垂压力体合成法",
            "difficulty": 3,
            "rubric": [
                {"label": "由复式水银—水 U 形测压计逐段递推求得球心平面油压 pO = 2500g ≈ 24.53 kPa 及等效油面高 H = 3.125 m", "pts": 6},
                {"label": "指出轴对称得水平合力为零，正确建立向上虚压力体体积 Vz = πr²H - (2/3)πr³ = 0.09608 m³", "pts": 5},
                {"label": "准确算得总压力 P = Pz = 754.0 N（g=9.80 时 753.3 N）并指明方向竖直向上", "pts": 4},
            ],
        },
        {
            "id": "yzu-849-2014-27",
            "year": 2014,
            "no": 27,
            "type": "calc",
            "score": 15,
            "title": "未知阻力系数水平短管利用中点测压管水头求输水流量",
            "stem": "有一长度为 $L$ 的处于水平位置的有压管道，管径 $d = 0.1\\,\\mathrm{m}$，作用水头 $H = 3\\,\\mathrm{m}$，在 $L/2$ 处装一测压管，已知测压管水面高于管轴线 $1\\,\\mathrm{m}$，管道进口局部阻力系数为 $0.5$，不计行近流速，求管道中通过的流量。",
            "note": "",
            "figures": [
                {"src": "figures/q27_orig.png", "caption": "题 27 图　装设中点测压管的水平有压输水管道"}
            ],
            "shortAnswer": "Q = 0.0284 m³/s（28.4 L/s，流速 v ≈ 3.62 m/s）",
            "judgeAnswer": None,
            "answer": "管道中通过的流量 $Q = 0.0284\\,\\mathrm{m^3/s}$（即 $28.4\\,\\mathrm{L/s}$，管内平均流速 $v = 3.62\\,\\mathrm{m/s}$）。",
            "analysis": (
                "取水平管道中心轴线为基准面（$z = 0$），动能修正系数取 $\\alpha = 1$，设管道沿程阻力系数为 $\\lambda$，管内平均流速为 $v$。\n\n"
                "**1. 对上游水池液面（1—1）与管道自由出流出口（3—3）列能量方程**\n\n"
                "水池表面 $z_1 = H = 3\\,\\mathrm{m}, p_1 = 0, v_1 \\approx 0$；出口断面 $z_3 = 0, p_3 = 0, v_3 = v$：\n\n"
                "$$\nH = \\frac{v^2}{2g} + \\zeta_e\\frac{v^2}{2g} + \\lambda\\frac{L}{d}\\frac{v^2}{2g} = \\left(1 + \\zeta_e + \\lambda\\frac{L}{d}\\right)\\frac{v^2}{2g} \\tag{1}\n$$\n\n"
                "**2. 对上游水池液面（1—1）与中点 $L/2$ 断面（2—2）列能量方程**\n\n"
                "中点断面 $z_2 = 0$，测压管水头 $h_p = \\frac{p_2}{\\rho g} = 1\\,\\mathrm{m}$，流速 $v_2 = v$，前半段沿程损失恰为总沿程损失的一半：\n\n"
                "$$\nH = h_p + \\frac{v^2}{2g} + \\zeta_e\\frac{v^2}{2g} + \\frac{1}{2}\\lambda\\frac{L}{d}\\frac{v^2}{2g} = h_p + \\left(1 + \\zeta_e + \\frac{1}{2}\\lambda\\frac{L}{d}\\right)\\frac{v^2}{2g} \\tag{2}\n$$\n\n"
                "**3. 联立（1）、（2）式消去未知沿程阻力项 $\\lambda\\frac{L}{d}$**\n\n"
                "由 $2 \\times (2) - (1)$ 直接消去 $\\lambda\\frac{L}{d}$：\n\n"
                "$$\nH = 2h_p + (1 + \\zeta_e)\\frac{v^2}{2g}\n$$\n\n"
                "代入 $H = 3\\,\\mathrm{m}$、$h_p = 1\\,\\mathrm{m}$、$\\zeta_e = 0.5$：\n\n"
                "$$\n3 = 2 \\times 1 + (1 + 0.5)\\frac{v^2}{2g} \\implies 1.5\\frac{v^2}{2g} = 1 \\implies \\frac{v^2}{2g} = \\frac{2}{3}\\,\\mathrm{m}\n$$\n\n"
                "解得流速与流量（取 $g = 9.81\\,\\mathrm{m/s^2}$）：\n\n"
                "$$\nv = \\sqrt{\\frac{4}{3}g} = \\sqrt{\\frac{4 \\times 9.81}{3}} = 3.617\\,\\mathrm{m/s}\n$$\n\n"
                "$$\nQ = \\frac{\\pi}{4} d^2 v = \\frac{\\pi}{4} \\times 0.1^2 \\times 3.617 = 0.02840\\,\\mathrm{m^3/s} \\approx 0.0284\\,\\mathrm{m^3/s}\n$$\n\n"
                "（注：若取 $g = 9.80\\,\\mathrm{m/s^2}$，则 $v = 3.615\\,\\mathrm{m/s}$，$Q = 0.02839\\,\\mathrm{m^3/s}$，保留三位有效数字均为 $0.0284\\,\\mathrm{m^3/s}$。）"
            ),
            "analysisFigures": [
                {"src": "figures/q27_sol.png", "caption": "解图 27　水平短管水头线分布与中点测压管消元法"}
            ],
            "pitfalls": "亦可直接从后半段 $L/2$ 读出几何巧解：等径管后半段测压管水头由 $1\\,\\mathrm{m}$ 线性降至出口 $0\\,\\mathrm{m}$，立得半程沿程损失为 $1\\,\\mathrm{m}$、全程沿程损失 $h_f = 2\\,\\mathrm{m}$，余下 $3 - 2 = 1\\,\\mathrm{m}$ 恰等于 $(1 + \\zeta_e)\\frac{v^2}{2g} = 1.5\\frac{v^2}{2g}$！",
            "chapter": 6,
            "kps": ["简单短管自由出流", "恒定总流能量方程", "测压管水头线"],
            "method": "简单短管能量方程测流与允许真空度校核",
            "difficulty": 2,
            "rubric": [
                {"label": "对上游液面至管道出口列能量方程 H = (1 + ζe + λL/d) v²/(2g)", "pts": 5},
                {"label": "对上游液面至中点 L/2 列能量方程并消去未知沿程损失项，得 1.5 v²/(2g) = 1 m", "pts": 6},
                {"label": "求得管内流速 v = 3.62 m/s 及流量 Q = 0.0284 m³/s", "pts": 4},
            ],
        },
        {
            "id": "yzu-849-2014-28",
            "year": 2014,
            "no": 28,
            "type": "calc",
            "score": 10,
            "title": "水平 180° 等径 U 形弯管连接螺钉所受总水平拉力计算",
            "stem": "一水平放置的 $180^{\\circ}$ 弯管如图所示。已知管径 $d = 0.2\\,\\mathrm{m}$，断面 1—1 及 2—2 处管中心的相对压强 $p = 4.0 \\times 10^4\\,\\mathrm{N/m^2}$，管道通过的流量 $Q = 0.157\\,\\mathrm{m^3/s}$。试求诸螺钉上所承受的总水平力。",
            "note": "",
            "figures": [
                {"src": "figures/q28_orig.png", "caption": "题 28 图　水平 180° 弯管与连接螺钉位置"}
            ],
            "shortAnswer": "F = 4082.5 N（约 4.08 kN），螺钉承受弯管向右拉拔的总水平拉力（螺钉对弯管的约束反力水平向左）。",
            "judgeAnswer": None,
            "answer": "诸螺钉上所承受的总水平力大小为 $F = 4082.5\\,\\mathrm{N}$（约 $4.08\\,\\mathrm{kN}$）；水流对弯管的推力水平向右，故螺钉承受**水平向右拉拔的总水平拉力**（螺钉对弯管与水体施加水平向左的约束反力）。",
            "analysis": (
                "**1. 计算断面面积与平均流速**\n\n"
                "$$\nA = \\frac{\\pi}{4} d^2 = \\frac{\\pi}{4} \\times 0.2^2 = 0.031416\\,\\mathrm{m^2}\n$$\n\n"
                "$$\nv_1 = v_2 = v = \\frac{Q}{A} = \\frac{0.157}{0.031416} = 4.9975\\,\\mathrm{m/s} \\approx 5.00\\,\\mathrm{m/s}\n$$\n\n"
                "**2. 取断面 1—1 至断面 2—2 间弯管内水体为控制体列水平动量方程**\n\n"
                "取水平向右为 $x$ 轴正向（与进口流向一致），设弯管壁面（经由螺钉约束）对控制体水流的水平作用力为 $R_x$（假设方向水平向左）。注意到两断面处的静水总压力 $P_1 = pA$ 与 $P_2 = pA$ 均指向控制体内部即**均水平向右**，出口流速 $v_{2x} = -v$，进口流速 $v_{1x} = +v$，由恒定总流动量方程（取 $\\beta = 1$）：\n\n"
                "$$\nP_1 + P_2 - R_x = \\rho Q (v_{2x} - v_{1x}) = \\rho Q (-v - v) = -2\\rho Q v\n$$\n\n"
                "移项解得弯管（螺钉）对水体的约束反力：\n\n"
                "$$\nR_x = 2pA + 2\\rho Q v\n$$\n\n"
                "代入数值计算：\n\n"
                "- 静压合力项：$2pA = 2 \\times 4.0 \\times 10^4 \\times 0.031416 = 2513.27\\,\\mathrm{N}$；\n\n"
                "- 动量反转项：$2\\rho Q v = 2 \\times 1000 \\times 0.157 \\times 4.9975 = 1569.21\\,\\mathrm{N}$；\n\n"
                "$$\nR_x = 2513.27 + 1569.21 = 4082.48\\,\\mathrm{N} \\approx 4082.5\\,\\mathrm{N} \\quad (\\text{方向水平向左})\n$$\n\n"
                "由作用力与反作用力定律，水流推动弯管使诸螺钉承受的总水平拉力为 $F = 4082.5\\,\\mathrm{N}$（方向水平向右）。"
            ),
            "analysisFigures": [
                {"src": "figures/q28_sol.png", "caption": "解图 28　180° 水平弯管控制体水平动量方程受力图"}
            ],
            "pitfalls": "两大易错符号：① 出口断面 2—2 处的外部水压力 $P_2$ 垂直压向控制体内部，与 $P_1$ **同为向右**（$P_1 + P_2 = 2pA$，切勿相减！）；② 出口速度方向向左，动量变化为 $\\rho Q(-v - v) = -2\\rho Q v$，移项后与 $2pA$ 相加。",
            "chapter": 3,
            "kps": ["恒定总流动量方程", "弯管水流作用力"],
            "method": "能量方程求流量+控制体动量方程求反力",
            "difficulty": 2,
            "rubric": [
                {"label": "计算管道过水面积 A = 0.03142 m² 及平均流速 v = 5.00 m/s", "pts": 3},
                {"label": "取 1-1 至 2-2 水体为控制体，正确列出水平动量方程 2pA - Rx = -2ρQv", "pts": 4},
                {"label": "准确解得诸螺钉承受总水平力 F = 4082.5 N（约 4.08 kN）并指明方向", "pts": 3},
            ],
        },
        {
            "id": "yzu-849-2014-29",
            "year": 2014,
            "no": 29,
            "type": "calc",
            "score": 15,
            "title": "半圆底混凝土 U 形明渠均匀流过流流量计算",
            "stem": "如图所示，一半圆混凝土 U 形渠道，渠宽 $b = 1.2\\,\\mathrm{m}$，渠道底坡 $i = 1/1000$，糙率 $n = 0.017$，当渠道内均匀流水深 $h_0 = 0.8\\,\\mathrm{m}$ 时，求此渠道内通过的流量。",
            "note": "",
            "figures": [
                {"src": "figures/q29_orig.png", "caption": "题 29 图　半圆底 U 形混凝土渠道横断面"}
            ],
            "shortAnswer": "Q = 0.748 m³/s（约 0.75 m³/s）",
            "judgeAnswer": None,
            "answer": "该渠道内通过的流量 $Q = 0.748\\,\\mathrm{m^3/s}$（约 $0.75\\,\\mathrm{m^3/s}$）。",
            "analysis": (
                "**1. 计算 U 形断面几何与水力要素**\n\n"
                "由题图知，底部半圆直径等于渠宽 $b = 1.2\\,\\mathrm{m}$，故半圆半径 $r = \\frac{b}{2} = 0.6\\,\\mathrm{m}$。因均匀流水深 $h_0 = 0.8\\,\\mathrm{m} > r = 0.6\\,\\mathrm{m}$，过水断面由下部半径 $0.6\\,\\mathrm{m}$ 的半圆和上部高 $h_1 = h_0 - r = 0.8 - 0.6 = 0.2\\,\\mathrm{m}$、宽 $1.2\\,\\mathrm{m}$ 的矩形组成：\n\n"
                "- **过水断面面积 $A$**：\n\n"
                "$$\nA = \\frac{1}{2}\\pi r^2 + b h_1 = \\frac{1}{2}\\pi \\times 0.6^2 + 1.2 \\times 0.2 = 0.5655 + 0.2400 = 0.8055\\,\\mathrm{m^2}\n$$\n\n"
                "- **湿周 $\\chi$**（半圆弧长加两侧竖直侧壁湿长）：\n\n"
                "$$\n\\chi = \\pi r + 2h_1 = \\pi \\times 0.6 + 2 \\times 0.2 = 1.8850 + 0.4000 = 2.2850\\,\\mathrm{m}\n$$\n\n"
                "- **水力半径 $R$**：\n\n"
                "$$\nR = \\frac{A}{\\chi} = \\frac{0.8055}{2.2850} = 0.3525\\,\\mathrm{m}\n$$\n\n"
                "**2. 应用谢才—曼宁公式计算流量 $Q$**\n\n"
                "- 谢才系数 $C = \\frac{1}{n} R^{1/6} = \\frac{1}{0.017} \\times 0.3525^{1/6} = 58.824 \\times 0.8404 = 49.44\\,\\mathrm{m^{1/2}/s}$；\n\n"
                "- 均匀流流量：\n\n"
                "$$\nQ = \\frac{1}{n} A R^{2/3} i^{1/2} = \\frac{1}{0.017} \\times 0.8055 \\times 0.3525^{2/3} \\times \\sqrt{\\frac{1}{1000}} = 47.382 \\times 0.4991 \\times 0.03162 = 0.7477\\,\\mathrm{m^3/s} \\approx 0.748\\,\\mathrm{m^3/s}\n$$\n\n"
                "（注：若中间结果过早截断至两位小数如 $A\\approx 0.81, \\chi\\approx 2.28, R\\approx 0.36$，会算得偏大值 $0.76\\,\\mathrm{m^3/s}$；保留四位有效数字的精确解为 $0.748\\,\\mathrm{m^3/s}$。）"
            ),
            "analysisFigures": [],
            "pitfalls": "注意明渠顶部为自由水面，不计入湿周 $\\chi$；且上部矩形竖直湿壁高度是 $h_0 - r = 0.2\\,\\mathrm{m}$（切勿误代全水深 $0.8\\,\\mathrm{m}$）。",
            "chapter": 7,
            "kps": ["U形断面水力要素", "曼宁公式"],
            "method": "谢才—曼宁公式明渠均匀流水力计算法",
            "difficulty": 2,
            "rubric": [
                {"label": "正确拆分下部半圆（r = 0.6 m）与上部矩形（h1 = 0.2 m），算得面积 A = 0.8055 m²", "pts": 5},
                {"label": "正确计算湿周 χ = πr + 2h1 = 2.285 m 及水力半径 R = 0.3525 m", "pts": 5},
                {"label": "代入谢才—曼宁公式准确求得渠道均匀流流量 Q = 0.748 m³/s（约 0.75 m³/s）", "pts": 5},
            ],
        },
        {
            "id": "yzu-849-2014-30",
            "year": 2014,
            "no": 30,
            "type": "calc",
            "score": 15,
            "title": "二维流速场连续性、有旋性判别、流函数求解与两点间单宽流量计算",
            "stem": "已知平面流动的流速为 $u_x = x^2 + 2x - 4y$，$u_y = -2xy - 2y$，试求：\n\n（1）流动是否连续？\n\n（2）流动是否无旋？\n\n（3）说明是否存在流函数及流速势函数，如存在，求函数形式；\n\n（4）求点 $A(4, 3)$ 和 $B(2, 1)$ 间的单宽流量为多少？",
            "note": "",
            "figures": [],
            "shortAnswer": "（1）连续；（2）有旋（非无旋，ωz = 2 - y ≠ 0）；（3）存在流函数 ψ = x²y + 2xy - 2y² + C，不存在流速势函数；（4）q = 48 m²/s。",
            "judgeAnswer": None,
            "answer": "（1）满足不可压缩连续性方程，流动**连续**；\n\n（2）旋转角速度 $\\omega_z = 2 - y \\neq 0$，流动为**有旋流动**（非无旋）；\n\n（3）**存在流函数** $\\psi = x^2 y + 2xy - 2y^2 + C$，**不存在流速势函数**；\n\n（4）点 $A(4, 3)$ 与点 $B(2, 1)$ 间的单宽流量 $q = |\\psi_A - \\psi_B| = 48\\,\\mathrm{m^2/s}$。",
            "analysis": (
                "**（1）判别流动是否连续**\n\n"
                "检验平面不可压缩连续性微分方程：\n\n"
                "$$\n\\frac{\\partial u_x}{\\partial x} + \\frac{\\partial u_y}{\\partial y} = \\frac{\\partial(x^2 + 2x - 4y)}{\\partial x} + \\frac{\\partial(-2xy - 2y)}{\\partial y} = (2x + 2) + (-2x - 2) = 0\n$$\n\n"
                "恒满足连续性方程，故该流动**连续**。\n\n"
                "**（2）判别流动是否无旋**\n\n"
                "计算流体微团绕 $z$ 轴的旋转角速度：\n\n"
                "$$\n\\omega_z = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} - \\frac{\\partial u_x}{\\partial y}\\right) = \\frac{1}{2}\\left[(-2y) - (-4)\\right] = 2 - y \\neq 0\n$$\n\n"
                "因此该流动为**有旋流动**（非无旋流动）。\n\n"
                "**（3）判别并求解流函数与流速势函数**\n\n"
                "- 因满足平面不可压缩连续性方程，**存在流函数 $\\psi$**；因流动有旋（$\\omega_z \\neq 0$），**不存在流速势函数 $\\varphi$**。\n\n"
                "- 由流函数定义 $\\frac{\\partial\\psi}{\\partial y} = u_x = x^2 + 2x - 4y$ 对 $y$ 偏积分：\n\n"
                "$$\n\\psi(x, y) = \\int (x^2 + 2x - 4y)\\,\\mathrm{d}y + g(x) = x^2 y + 2xy - 2y^2 + g(x)\n$$\n\n"
                "对 $x$ 求偏导并与 $-u_y$ 比较：\n\n"
                "$$\n\\frac{\\partial\\psi}{\\partial x} = 2xy + 2y + g'(x) = -u_y = 2xy + 2y \\implies g'(x) = 0 \\implies g(x) = C\n$$\n\n"
                "故流函数为：\n\n"
                "$$\n\\psi(x, y) = x^2 y + 2xy - 2y^2 + C\n$$\n\n"
                "**（4）求点 $A(4, 3)$ 与点 $B(2, 1)$ 间的单宽流量**\n\n"
                "分别代入两点坐标求流函数值（常数 $C$ 相减消去）：\n\n"
                "$$\n\\psi_A = 4^2 \\times 3 + 2 \\times 4 \\times 3 - 2 \\times 3^2 + C = 48 + 24 - 18 + C = 54 + C\n$$\n\n"
                "$$\n\\psi_B = 2^2 \\times 1 + 2 \\times 2 \\times 1 - 2 \\times 1^2 + C = 4 + 4 - 2 + C = 6 + C\n$$\n\n"
                "故两点间的单宽流量为：\n\n"
                "$$\nq = |\\psi_A - \\psi_B| = |54 - 6| = 48\\,\\mathrm{m^2/s}\n$$"
            ),
            "analysisFigures": [],
            "pitfalls": "规范符号提醒：流函数符号为 $\\psi$（不是势函数 $\\varphi$），且求 $\\omega_z$ 时注意 $-u_x$ 对 $y$ 求偏导负负得正：$-2y - (-4) = 4 - 2y$。",
            "chapter": 5,
            "kps": ["平面不可压缩连续性方程", "无旋流判据", "流函数与势函数", "单宽流量计算"],
            "method": "连续性与无旋性判据及流函数求单宽流量法",
            "difficulty": 2,
            "rubric": [
                {"label": "检验 ∂ux/∂x + ∂uy/∂y = 0 成立，判定流动连续", "pts": 3},
                {"label": "求得旋转角速度 ωz = 2 - y ≠ 0，判定流动有旋", "pts": 3},
                {"label": "指出存在流函数且不存在势函数，偏积分求得 ψ = x²y + 2xy - 2y² + C", "pts": 6},
                {"label": "代入 A(4,3)、B(2,1) 算得单宽流量 q = |ψA - ψB| = 48 m²/s", "pts": 3},
            ],
        },
    ]

    return {
        "year": 2014,
        "code": "849",
        "subject": "水力学（水）",
        "school": "扬州大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": True,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试（A 卷）。",
            "全卷共 30 题：一、单项选择题（10×2=20 分）；二、填空题（10 题共 20 空，每空 1 分，共 20 分）；三、简答题（5×8=40 分）；四、计算题（5 题共 70 分：15+15+10+15+15 分）。",
            "除特别说明外，水密度取 $\\rho = 1000\\,\\mathrm{kg/m^3}$，水银密度 $\\rho_m = 13600\\,\\mathrm{kg/m^3}$，重力加速度取 $g = 9.81\\,\\mathrm{m/s^2}$（并在解析中同步附注 $g = 9.80\\,\\mathrm{m/s^2}$ 数值）。",
        ],
        "sections": [
            {
                "id": "single_choice",
                "title": "一、单项选择题",
                "description": "本大题共 10 小题，每小题 2 分，共 20 分。",
                "range": [1, 10],
                "scorePerQuestion": 2,
                "totalScore": 20,
            },
            {
                "id": "fill",
                "title": "二、填空题",
                "description": "本大题共 10 小题（20 个空格，每空格 1 分），共 20 分。",
                "range": [11, 20],
                "scorePerQuestion": 2,
                "totalScore": 20,
            },
            {
                "id": "short",
                "title": "三、简答题",
                "description": "本大题共 5 小题，每小题 8 分，共 40 分。",
                "range": [21, 25],
                "scorePerQuestion": 8,
                "totalScore": 40,
            },
            {
                "id": "calc",
                "title": "四、计算题",
                "description": "本大题共 5 小题（15+15+10+15+15 分），共 70 分。",
                "range": [26, 30],
                "totalScore": 70,
            },
        ],
        "questions": questions,
    }


def write_pack_and_web(paper: dict) -> None:
    year = int(paper["year"])
    pack_dir = PACK_ROOT / str(year)
    pack_fig_dir = pack_dir / "figures"
    pack_fig_dir.mkdir(parents=True, exist_ok=True)

    web_fig_dir = WEB_COURSE_DIR / "figures" / str(year)
    web_fig_dir.mkdir(parents=True, exist_ok=True)
    WEB_COURSE_DIR.mkdir(parents=True, exist_ok=True)

    # Sanity assertions before writing
    qs = paper["questions"]
    total_score = sum(q["score"] for q in qs)
    assert total_score == 150, f"[{year}] score sum {total_score} != 150"
    for idx, q in enumerate(qs, start=1):
        assert q["no"] == idx, f"[{year}] non-consecutive no {q['no']} != {idx}"
        assert q["id"] == f"yzu-849-{year}-{idx:02d}", f"[{year}] bad id {q['id']}"
        assert q["chapter"] in VALID_CHAPTERS, f"[{year}] invalid chapter {q['chapter']} in {q['id']}"
        if q["type"] in ("short", "calc", "proof") and q["score"] >= 5:
            assert q.get("rubric"), f"[{year}] missing rubric in {q['id']}"
            r_sum = sum(r["pts"] for r in q["rubric"])
            assert r_sum == q["score"], f"[{year}] rubric sum {r_sum} != {q['score']} in {q['id']}"

    # 1. Write standardized exam pack JSON
    pack_json_path = pack_dir / f"{year}.json"
    pack_json_path.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2. Convert every referenced figure to WebP (quality=90, method=5) and write web JSON
    web_paper = copy.deepcopy(paper)
    fig_count = 0
    for q in web_paper["questions"]:
        for key in ("figures", "analysisFigures"):
            new_list = []
            for fig in q.get(key, []):
                src_name = Path(fig["src"]).name
                src_path = pack_fig_dir / src_name
                assert src_path.exists(), f"[{year}] Missing PNG figure: {src_path}"
                webp_name = f"{Path(src_name).stem}.webp"
                dest_webp = web_fig_dir / webp_name
                img = Image.open(src_path)
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA")
                img.save(dest_webp, format="WEBP", quality=90, method=5)
                new_list.append({
                    "src": f"figures/{year}/{webp_name}",
                    "caption": fig["caption"],
                })
                fig_count += 1
            q[key] = new_list

    web_json_path = WEB_COURSE_DIR / f"{year}.json"
    web_json_path.write_text(json.dumps(web_paper, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"[{year}] Wrote {len(qs)} questions ({total_score} pts, {fig_count} figures) -> "
        f"{pack_json_path.relative_to(ROOT)} & {web_json_path.relative_to(ROOT)}"
    )


def main():
    extract_stem_figures()

    fig_dir_2015 = PACK_ROOT / "2015" / "figures"
    draw_2015_q10_sol(fig_dir_2015)
    draw_2015_q16_sol(fig_dir_2015)
    draw_2015_q17_sol(fig_dir_2015)
    draw_2015_q19_sol(fig_dir_2015)
    draw_2015_q21_sol(fig_dir_2015)
    print(f"[2015] Generated 5 matplotlib solution figures -> {fig_dir_2015}")

    fig_dir_2014 = PACK_ROOT / "2014" / "figures"
    draw_2014_q22_sol(fig_dir_2014)
    draw_2014_q24_sol(fig_dir_2014)
    draw_2014_q26_sol(fig_dir_2014)
    draw_2014_q27_sol(fig_dir_2014)
    draw_2014_q28_sol(fig_dir_2014)
    print(f"[2014] Generated 5 matplotlib solution figures -> {fig_dir_2014}")

    write_pack_and_web(build_2015_paper())
    write_pack_and_web(build_2014_paper())


if __name__ == "__main__":
    main()
