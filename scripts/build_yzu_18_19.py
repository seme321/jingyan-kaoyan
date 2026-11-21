# -*- coding: utf-8 -*-
"""
Generate high-res 300 DPI cropped stem figures (q*_orig.png), clean matplotlib
solution schematics (q*_sol.png, dpi=220), standardized exam packs in
`扬州大学已整理数据/{2019,2018}/`, and web-ready JSON + WebP assets in
`web/public/data/yzu-849/` for Yangzhou University 849 Hydraulics (2019 & 2018).
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


def remove_small_specks(binary_ink: np.ndarray, min_pixels: int = 5) -> np.ndarray:
    """Remove tiny isolated 1~4 px scan dust specks while preserving all strokes & dots."""
    h, w = binary_ink.shape
    visited = np.zeros_like(binary_ink, dtype=bool)
    cleaned = binary_ink.copy()
    ys, xs = np.where(binary_ink)
    for y0, x0 in zip(ys, xs):
        if visited[y0, x0]:
            continue
        # Quick neighborhood check: if surrounded by >= min_pixels in 5x5 window, keep fast
        y_min, y_max = max(0, y0 - 2), min(h, y0 + 3)
        x_min, x_max = max(0, x0 - 2), min(w, x0 + 3)
        if binary_ink[y_min:y_max, x_min:x_max].sum() >= min_pixels:
            visited[y0, x0] = True
            continue
        # BFS for tiny connected component
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
    """Auto-trim ink bounds, clean paper background to pure white #FFFFFF, and add 16px margin."""
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
    """Render 2019 & 2018 PDFs at 300 DPI and crop stem figures without `题X图` captions."""
    crops_by_year = {
        2019: (
            "849-水力学（水）2019.pdf",
            {
                "q04_orig.png": (0, (1595, 1315, 2215, 1512)),
                "q05_orig.png": (0, (425, 1825, 998, 2415)),
                "q06_orig.png": (0, (1305, 1825, 1965, 2420)),
                "q07_orig.png": (1, (465, 435, 1020, 1015)),
                "q08_orig.png": (1, (1480, 535, 1860, 1015)),
                "q09_orig.png": (1, (285, 1735, 1345, 2125)),
                "q10_orig.png": (1, (1455, 1715, 2115, 2208)),
            },
        ),
        2018: (
            "849-水力学（水）2018.pdf",
            {
                "q02_orig.png": (0, (945, 1225, 1485, 1665)),
                "q05_orig.png": (0, (795, 2505, 1660, 2930)),
                "q06_orig.png": (1, (850, 430, 1650, 792)),
                "q07_orig.png": (1, (510, 1130, 975, 1655)),
                "q08_orig.png": (1, (1235, 1135, 2010, 1660)),
                "q09_orig.png": (1, (685, 2020, 1030, 2335)),
                "q10_orig.png": (1, (1405, 2040, 1860, 2365)),
                "q11_orig.png": (2, (895, 860, 1555, 1475)),
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
# Matplotlib Solution Figures for 2019 (dpi=220, ZERO CJK inside $...$)
# ==============================================================================

def draw_2019_q04_sol(fig_dir: Path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.4, 3.9), gridspec_kw={"width_ratios": [1.35, 1.0]})
    fig.patch.set_facecolor("white")

    # Left: compound channel partition
    pts_bed = [(-3.3, 2.2), (-2.6, 1.1), (-1.4, 1.1), (-0.8, 0.0), (0.8, 0.0),
               (1.4, 1.1), (2.6, 1.1), (3.3, 2.2)]
    xs_b, ys_b = zip(*pts_bed)
    y_ws = 1.75
    x_ws_l = -2.6 - (y_ws - 1.1) * (0.7 / 1.1)
    x_ws_r = 2.6 + (y_ws - 1.1) * (0.7 / 1.1)

    poly_water = [(x_ws_l, y_ws), (-2.6, 1.1), (-1.4, 1.1), (-0.8, 0.0),
                  (0.8, 0.0), (1.4, 1.1), (2.6, 1.1), (x_ws_r, y_ws)]
    ax1.add_patch(patches.Polygon(poly_water, closed=True, facecolor="#bae6fd", alpha=0.65))
    ax1.plot(xs_b, ys_b, color="#0f172a", lw=2.3)
    ax1.plot([x_ws_l, x_ws_r], [y_ws, y_ws], color="#0284c7", lw=2.0)

    # Vertical division lines between main channel and floodplains
    for xv in (-1.4, 1.4):
        ax1.plot([xv, xv], [1.1, y_ws], color="#dc2626", ls="--", lw=1.8)
    ax1.plot([-1.4, 1.4], [1.1, 1.1], color="#64748b", ls=":", lw=1.2)

    ax1.text(0.28, 0.56, "主槽区 " + r"$A_1$" + "\n水深大、流速快\n" + r"($n_1$ 较小)",
             ha="center", va="center", fontsize=9.0, color="#0f172a", fontweight="bold")
    ax1.text(-2.15, 1.43, "左滩地 " + r"$A_2$" + "\n浅慢", ha="center", va="center", fontsize=8.8, color="#0369a1")
    ax1.text(2.15, 1.43, "右滩地 " + r"$A_3$" + "\n浅慢", ha="center", va="center", fontsize=8.8, color="#0369a1")
    ax1.annotate("", xy=(-0.62, 1.1), xytext=(-0.62, 0.0),
                 arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.3))
    ax1.text(-0.72, 0.55, r"$h^{\prime}$", fontsize=10.5, color="#334155", va="center", ha="right")
    ax1.text(-1.4, y_ws + 0.12, "铅直分界线（不计湿周）", fontsize=8.8, ha="center", color="#dc2626")

    ax1.set_xlim(-3.55, 3.55)
    ax1.set_ylim(-0.25, 2.38)
    ax1.axis("off")
    ax1.set_title("（a）复式断面主槽与滩地分块计算示意", fontsize=10.5, pad=6)

    # Right: R(h) sudden drop when h crosses h'
    h1 = np.linspace(0.15, 1.10, 80)
    b0, m0, B_fp = 1.6, 0.55, 1.2
    A_sub = (b0 + m0 * h1) * h1
    chi_sub = b0 + 2 * h1 * np.sqrt(1 + m0**2)
    R1 = A_sub / chi_sub

    h2 = np.linspace(1.101, 2.0, 90)
    dh = h2 - 1.10
    A_main_top = b0 + 2 * m0 * 1.10
    A_sup = A_sub[-1] + (A_main_top + 2 * B_fp + m0 * dh) * dh
    chi_sup = chi_sub[-1] + 2 * B_fp + 2 * dh * np.sqrt(1 + m0**2)
    R2 = A_sup / chi_sup

    ax2.plot(R1, h1, color="#0284c7", lw=2.3)
    ax2.plot(R2, h2, color="#0284c7", lw=2.3)
    ax2.plot([R1[-1], R2[0]], [1.10, 1.101], color="#dc2626", ls="--", lw=2.0)
    ax2.axhline(1.10, color="#94a3b8", ls=":", lw=1.1)
    ax2.text(0.08, 1.17, "漫滩临界水深 " + r"$h = h^{\prime}$", fontsize=8.8, color="#334155")
    ax2.annotate("湿周突增导致\n水力半径 " + r"$R$" + " 骤降",
                 xy=((R1[-1] + R2[0]) * 0.5, 1.09), xytext=(0.43, 0.34),
                 fontsize=8.8, color="#dc2626",
                 bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#fca5a5", alpha=0.95),
                 arrowprops=dict(arrowstyle="->", color="#dc2626", lw=1.4))

    ax2.set_xlabel("整断面水力半径 " + r"$R = A/\chi$", fontsize=9.8)
    ax2.set_ylabel("水深 " + r"$h$", fontsize=9.8)
    ax2.set_xlim(0.05, 0.80)
    ax2.set_ylim(0.0, 2.15)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.set_title("（b）漫滩瞬间水力半径 " + r"$R(h)$" + " 突变曲线", fontsize=10.5, pad=6)

    plt.tight_layout()
    fig.savefig(fig_dir / "q04_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2019_q06_sol(fig_dir: Path):
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    fig.patch.set_facecolor("white")

    # Coordinate: y=0 at channel bottom, y=2 at B, y=4 at A, y=5.2 glycerin WS, y=7.0 water WS
    ax.plot([-3.4, 3.4], [0, 0], color="#0f172a", lw=2.3)
    for xh in np.linspace(-3.3, 3.2, 30):
        ax.plot([xh, xh - 0.14], [0, -0.22], color="#64748b", lw=0.9)

    # Liquids background
    ax.add_patch(patches.Rectangle((-3.2, 0.02), 3.2, 6.98, facecolor="#e0f2fe", alpha=0.50))
    ax.add_patch(patches.Rectangle((0.0, 0.02), 3.2, 5.18, facecolor="#fef3c7", alpha=0.55))
    ax.plot([-3.2, 0.0], [7.0, 7.0], color="#0284c7", lw=2.0)
    ax.plot([0.0, 3.2], [5.2, 5.2], color="#d97706", lw=2.0)

    # Wall & Gate AB (y from 2.0 to 4.0)
    ax.plot([0, 0], [0, 2.0], color="#334155", lw=2.2)
    ax.plot([0, 0], [4.0, 7.4], color="#334155", lw=2.2)
    ax.add_patch(patches.Rectangle((-0.07, 2.0), 0.14, 2.0, facecolor="#1e293b", edgecolor="#0f172a", zorder=5))
    ax.text(0.14, 4.05, r"$A$", fontsize=11, fontweight="bold", color="#0f172a")
    ax.text(0.14, 1.85, r"$B$", fontsize=11, fontweight="bold", color="#0f172a")

    # Left trapezoid: pA1=29.4, pB1=49.0 kPa (scale: 1 kPa = 0.042 unit)
    sc = 0.042
    wA1, wB1 = 29.40 * sc, 49.00 * sc
    ax.add_patch(patches.Polygon([(-wA1, 4.0), (0, 4.0), (0, 2.0), (-wB1, 2.0)],
                                 closed=True, facecolor="#bae6fd", edgecolor="#0284c7", lw=1.6, alpha=0.85, zorder=4))
    y_P1 = 4.0 - 1.0833
    ax.annotate("", xy=(-0.08, y_P1), xytext=(-wB1 - 0.35, y_P1),
                arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2.3), zorder=6)
    ax.text(-wB1 - 0.40, y_P1 + 0.15, "水侧总压力 " + r"$P_1 = 78.40\,\mathrm{kN/m}$" + "\n（距 " + r"$A$" + " 点 " + r"$1.083\,\mathrm{m}$" + "）",
            ha="right", va="center", fontsize=9.2, color="#0369a1", fontweight="bold")

    # Right trapezoid: pA2=14.86, pB2=39.64 kPa
    wA2, wB2 = 14.86 * sc, 39.64 * sc
    ax.add_patch(patches.Polygon([(0, 4.0), (wA2, 4.0), (wB2, 2.0), (0, 2.0)],
                                 closed=True, facecolor="#fde68a", edgecolor="#d97706", lw=1.6, alpha=0.85, zorder=4))
    y_P2 = 4.0 - 1.1515
    ax.annotate("", xy=(0.08, y_P2), xytext=(wB2 + 0.35, y_P2),
                arrowprops=dict(arrowstyle="->", color="#b45309", lw=2.3), zorder=6)
    ax.text(wB2 + 0.40, y_P2 - 0.18, "甘油侧压力 " + r"$P_2 = 54.50\,\mathrm{kN/m}$" + "\n（距 " + r"$A$" + " 点 " + r"$1.152\,\mathrm{m}$" + "）",
            ha="left", va="center", fontsize=9.2, color="#b45309", fontweight="bold")

    # Net resultant P = 23.90 kN/m at 0.928 m below A
    y_Pnet = 4.0 - 0.9278
    ax.annotate("", xy=(1.25, y_Pnet + 0.42), xytext=(0.08, y_Pnet + 0.42),
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.6), zorder=7)
    ax.scatter([0.0], [y_Pnet], color="#dc2626", s=38, zorder=8)
    ax.text(1.30, y_Pnet + 0.42, "合力 " + r"$P = 23.90\,\mathrm{kN/m}$" + "（向右）\n作用点距 " + r"$A$" + " 点 " + r"$0.928\,\mathrm{m}$",
            ha="left", va="center", fontsize=9.5, color="#dc2626", fontweight="bold")

    ax.text(-2.3, 6.45, "水 " + r"$\rho_1 = 1000\,\mathrm{kg/m^3}$", fontsize=9.5, color="#0369a1")
    ax.text(2.1, 4.65, "甘油 " + r"$\rho_2 = 1264\,\mathrm{kg/m^3}$", fontsize=9.5, ha="center", color="#92400e")

    ax.set_xlim(-4.7, 4.7)
    ax.set_ylim(-0.4, 7.65)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q06_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2019_q08_sol(fig_dir: Path):
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    fig.patch.set_facecolor("white")

    theta = np.linspace(-np.pi / 2, np.pi / 2, 120)
    # Outer and inner walls of contracting 180 deg U-bend
    r_mid = 1.25
    half_w = np.linspace(0.18, 0.52, 120)  # bottom (theta=-pi/2, d2) -> top (theta=+pi/2, d1)
    x_out = 1.2 + (r_mid + half_w) * np.cos(theta)
    y_out = (r_mid + half_w) * np.sin(theta)
    x_in = 1.2 + (r_mid - half_w) * np.cos(theta)
    y_in = (r_mid - half_w) * np.sin(theta)

    xs_poly = np.concatenate([[0.5], x_out[::-1], [0.5, 0.5], x_in, [0.5]])
    ys_poly = np.concatenate([[r_mid + 0.52], y_out[::-1], [-r_mid - 0.18, -r_mid + 0.18], y_in, [r_mid - 0.52]])
    ax.add_patch(patches.Polygon(list(zip(xs_poly, ys_poly)), closed=True,
                                 facecolor="#bae6fd", edgecolor="#0f172a", lw=2.0, alpha=0.75))

    # Control sections 1-1 and 2-2
    ax.plot([0.5, 0.5], [r_mid - 0.68, r_mid + 0.68], color="#dc2626", ls="--", lw=1.8)
    ax.plot([0.5, 0.5], [-r_mid - 0.36, -r_mid + 0.36], color="#dc2626", ls="--", lw=1.8)
    ax.text(0.5, r_mid + 0.78, "法兰断面 1—1", fontsize=9.5, ha="center", color="#dc2626")
    ax.text(0.5, -r_mid - 0.52, "法兰断面 2—2", fontsize=9.5, ha="center", color="#dc2626")

    # Pressure forces P1, P2 (both +x!)
    ax.annotate("", xy=(0.46, r_mid + 0.18), xytext=(-0.65, r_mid + 0.18),
                arrowprops=dict(arrowstyle="->", color="#b45309", lw=2.3))
    ax.text(-0.70, r_mid + 0.18, r"$P_1 = p_1 A_1 = 21.21\,\mathrm{kN}$", fontsize=9.5, ha="right", va="center", color="#92400e", fontweight="bold")

    ax.annotate("", xy=(0.46, -r_mid + 0.10), xytext=(-0.45, -r_mid + 0.10),
                arrowprops=dict(arrowstyle="->", color="#b45309", lw=2.0))
    ax.text(-0.50, -r_mid + 0.10, r"$P_2 = p_2 A_2 = 1.10\,\mathrm{kN}$", fontsize=9.5, ha="right", va="center", color="#92400e", fontweight="bold")

    # Velocities v1 (+x) and v2 (-x)
    ax.annotate("", xy=(1.35, r_mid - 0.12), xytext=(0.62, r_mid - 0.12),
                arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2.0))
    ax.text(1.00, r_mid - 0.32, r"$v_1 = 2\,\mathrm{m/s}$", fontsize=9.2, ha="center", color="#0369a1")

    ax.annotate("", xy=(-0.35, -r_mid - 0.12), xytext=(0.42, -r_mid - 0.12),
                arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2.0))
    ax.text(-0.42, -r_mid - 0.12, r"$v_2 = 18\,\mathrm{m/s}$", fontsize=9.2, ha="right", va="center", color="#0369a1")

    # Reaction force Rx from bolts/bend on CV (-x) & thrust on bolts (+x)
    ax.annotate("", xy=(2.05, 0.15), xytext=(3.10, 0.15),
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.6))
    ax.text(3.16, 0.15, "弯管（螺栓）对水体反力\n" + r"$R_x = 25.13\,\mathrm{kN}$" + "（向左）",
            fontsize=9.5, ha="left", va="center", color="#dc2626", fontweight="bold")

    ax.annotate("", xy=(3.45, -0.55), xytext=(2.80, -0.55),
                arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.8))
    ax.text(3.52, -0.55, r"$x$" + " 轴正方向", fontsize=9.2, va="center", color="#0f172a")

    ax.set_xlim(-2.45, 4.95)
    ax.set_ylim(-2.05, 2.25)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q08_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2019_q09_sol(fig_dir: Path):
    fig, ax = plt.subplots(figsize=(8.4, 4.3))
    fig.patch.set_facecolor("white")

    # Upstream WS y=2.0, Downstream WS y=0.6, Crest A pipe center y=3.25
    ax.plot([0.4, 2.55], [2.0, 2.0], color="#0284c7", lw=2.0)
    ax.plot([5.15, 7.6], [0.6, 0.6], color="#0284c7", lw=2.0)
    ax.add_patch(patches.Polygon([(0.4, 0.7), (2.55, 2.0), (0.4, 2.0)], closed=True, facecolor="#e0f2fe", alpha=0.55))
    ax.add_patch(patches.Polygon([(5.15, 0.6), (7.6, 0.6), (7.6, -0.2), (6.0, -0.2)], closed=True, facecolor="#e0f2fe", alpha=0.55))

    # Dam outline
    ax.plot([1.4, 3.1, 4.4, 6.2, 7.6], [0.7, 3.05, 3.05, -0.2, -0.2], color="#475569", lw=1.8)

    # Siphon pipe centerline
    sx = [2.0, 3.15, 4.35, 6.05, 6.85]
    sy = [1.45, 3.25, 3.25, 0.05, 0.05]
    ax.plot(sx, sy, color="#0f172a", lw=4.5, solid_capstyle="round")
    ax.plot(sx, sy, color="#bae6fd", lw=2.3, solid_capstyle="round")
    ax.scatter([4.35], [3.25], color="#dc2626", s=40, zorder=6)
    ax.text(4.35, 3.42, "坝顶危险断面 " + r"$A$", fontsize=9.8, ha="center", color="#dc2626", fontweight="bold")

    # Total Energy Line (E.G.L.) & Hydraulic Grade Line (H.G.L.) with exact submerged exit boundary:
    # Downstream free surface is y=0.60; velocity head gap vh=0.25.
    # H.G.L. slopes down from above to meet y=0.60 smoothly at exit x=6.85;
    # E.G.L. stays vh=0.25 above H.G.L. (0.85 just inside exit) and drops vertically by zeta_2*v^2/(2g)=0.25 to y=0.60 at exit!
    vh = 0.25
    pipe_x = [2.0, 3.15, 4.35, 6.05, 6.85]
    hgl_y = [1.55, 1.33, 1.16, 0.76, 0.60]
    egl_pipe_y = [y + vh for y in hgl_y]  # [1.80, 1.58, 1.41, 1.01, 0.85]

    egl_full_x = [1.5, 2.0] + pipe_x + [6.85]
    egl_full_y = [2.0, 2.0] + egl_pipe_y + [0.60]
    hgl_full_x = [2.0] + pipe_x
    hgl_full_y = [2.0] + hgl_y

    ax.plot(egl_full_x, egl_full_y, color="#16a34a", lw=1.9, ls="--", label="总水头线 (E.G.L.)")
    ax.plot(hgl_full_x, hgl_full_y, color="#7c3aed", lw=1.9, ls="-.", label="测压管水头线 (H.G.L.)")

    # Vacuum head arrow at A (between H.G.L. and pipe center A)
    ax.annotate("", xy=(4.35, 3.23), xytext=(4.35, hgl_y[2]),
                arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.7), zorder=6)
    ax.text(4.24, 2.25,
            "坝顶真空高度\n" + r"$h_{v,A} = h_1 + 3.06\dfrac{v^2}{2g}$",
            fontsize=9.1, ha="right", va="center", color="#dc2626", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#fca5a5", alpha=0.95), zorder=7)

    # Dimensions h1 and h2
    ax.plot([2.55, 3.15], [3.25, 3.25], color="#64748b", ls=":", lw=1.1)
    ax.annotate("", xy=(2.75, 3.25), xytext=(2.75, 2.0),
                arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.3))
    ax.text(2.65, 2.62, r"$h_1$", fontsize=10.5, ha="right", va="center")

    ax.plot([2.55, 7.25], [2.0, 2.0], color="#64748b", ls=":", lw=1.0)
    ax.annotate("", xy=(7.10, 2.0), xytext=(7.10, 0.6),
                arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.3))
    ax.text(7.20, 1.30, r"$h_2 = 4\,\mathrm{m}$", fontsize=10.0, ha="left", va="center")

    ax.legend(loc="lower left", frameon=True, fontsize=9.0)
    ax.set_xlim(0.3, 8.35)
    ax.set_ylim(-0.35, 3.78)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q09_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2019_q11_sol(fig_dir: Path):
    fig, ax = plt.subplots(figsize=(7.6, 3.6))
    fig.patch.set_facecolor("white")

    b, h, m = 10.0, 1.5, 1.5
    x_bl, x_br = -b / 2, b / 2
    x_wl, x_wr = -(b / 2 + m * h), (b / 2 + m * h)
    x_tl, x_tr = -(b / 2 + m * 2.1), (b / 2 + m * 2.1)

    ax.add_patch(patches.Polygon([(x_wl, h), (x_bl, 0), (x_br, 0), (x_wr, h)],
                                 closed=True, facecolor="#bae6fd", alpha=0.65))
    ax.plot([x_tl, x_bl, x_br, x_tr], [2.1, 0, 0, 2.1], color="#0f172a", lw=2.3)
    # Highlight wetted perimeter chi in orange
    ax.plot([x_wl, x_bl, x_br, x_wr], [h, 0, 0, h], color="#ea580c", lw=3.2, zorder=4, label="湿周 " + r"$\chi = 15.41\,\mathrm{m}$")
    ax.plot([x_wl, x_wr], [h, h], color="#0284c7", lw=2.0, zorder=4, label="水面宽 " + r"$B = 14.50\,\mathrm{m}$")

    ax.annotate("", xy=(x_br, -0.32), xytext=(x_bl, -0.32),
                arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.4))
    ax.text(0, -0.52, "底宽 " + r"$b = 10\,\mathrm{m}$", ha="center", fontsize=9.8)

    ax.annotate("", xy=(0, h), xytext=(0, 0),
                arrowprops=dict(arrowstyle="<->", color="#0369a1", lw=1.4))
    ax.text(0.22, 0.75, r"$h = 1.5\,\mathrm{m}$", va="center", fontsize=9.8, color="#0369a1", fontweight="bold")

    ax.text(-2.7, 0.78, r"$A = 18.375\,\mathrm{m^2},\; R = 1.193\,\mathrm{m}$" + "\n" + r"$v = 1.25\,\mathrm{m/s},\; n = 0.020$",
            ha="center", va="center", fontsize=9.5, color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#94a3b8", alpha=0.9))
    ax.text(x_br + 1.65, 0.52, "边坡 " + r"$1 : m = 1 : 1.5$", fontsize=9.3, color="#334155")

    ax.legend(loc="upper right", frameon=True, fontsize=9.0)
    ax.set_xlim(-8.8, 8.8)
    ax.set_ylim(-0.8, 2.35)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q11_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


# ==============================================================================
# Matplotlib Solution Figures for 2018 (dpi=220, ZERO CJK inside $...$)
# ==============================================================================

def draw_2018_q03_sol(fig_dir: Path):
    fig, ax = plt.subplots(figsize=(6.8, 4.1))
    fig.patch.set_facecolor("white")

    y = np.linspace(0.2, 3.2, 160)
    # Two thin paper sheets curving inward toward the center jet
    x_left = -0.85 + 0.36 * np.sin(np.pi * (y - 0.2) / 3.0)
    x_right = 0.85 - 0.36 * np.sin(np.pi * (y - 0.2) / 3.0)

    ax.fill_betweenx(y, x_left, x_right, color="#e0f2fe", alpha=0.65)
    ax.plot(x_left, y, color="#0f172a", lw=2.6, label="薄纸片")
    ax.plot(x_right, y, color="#0f172a", lw=2.6)

    # Center fast airflow streamlines
    for x_off in (-0.24, 0.0, 0.24):
        xs_s = x_off * (1.0 - 0.32 * np.sin(np.pi * (y - 0.2) / 3.0))
        ax.plot(xs_s, y, color="#0284c7", lw=1.4, ls="--")
    ax.annotate("", xy=(0.0, 0.35), xytext=(0.0, 3.45),
                arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.4))
    ax.text(0.0, 3.58, "吹入高速气流（" + r"$v_1$" + " 大）", ha="center", fontsize=10.0, color="#0369a1", fontweight="bold")

    ax.text(0.0, 1.72, "内侧高速低压区\n" + r"$v_1 > 0 \Rightarrow p_1 < p_a$",
            ha="center", va="center", fontsize=9.3, color="#0369a1",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#38bdf8", alpha=0.92))

    # Outer atmospheric pressure pushing inward
    for yp in (1.15, 2.25):
        xl = -0.85 + 0.36 * np.sin(np.pi * (yp - 0.2) / 3.0)
        xr = 0.85 - 0.36 * np.sin(np.pi * (yp - 0.2) / 3.0)
        ax.annotate("", xy=(xl - 0.03, yp), xytext=(-1.75, yp),
                    arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.2))
        ax.annotate("", xy=(xr + 0.03, yp), xytext=(1.75, yp),
                    arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.2))

    ax.text(-1.82, 1.70, "外侧静止大气\n" + r"$v_2 \approx 0,\; p_2 = p_a$" + "\n压差推纸向内靠拢",
            ha="right", va="center", fontsize=9.3, color="#b91c1c", fontweight="bold")
    ax.text(1.82, 1.70, "外侧静止大气\n" + r"$v_2 \approx 0,\; p_2 = p_a$" + "\n" + r"$\Delta p = p_a - p_1 > 0$",
            ha="left", va="center", fontsize=9.3, color="#b91c1c", fontweight="bold")

    ax.set_xlim(-3.25, 3.25)
    ax.set_ylim(-0.05, 3.92)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q03_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2018_q08_sol(fig_dir: Path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 4.3), gridspec_kw={"width_ratios": [1.35, 1.0]})
    fig.patch.set_facecolor("white")

    # Left: Real pressure body above upper submerged cone (D0=0.75 m, hc=0.9 m, H=3.0 m)
    ax1.plot([-1.4, -1.4, -0.375], [3.35, 0.0, 0.0], color="#0f172a", lw=2.1)
    ax1.plot([0.375, 1.4, 1.4], [0.0, 0.0, 3.35], color="#0f172a", lw=2.1)
    ax1.add_patch(patches.Rectangle((-1.38, 0.02), 2.76, 2.98, facecolor="#e0f2fe", alpha=0.45))
    ax1.plot([-1.4, 1.4], [3.0, 3.0], color="#0284c7", lw=2.0)

    # Shaded real pressure body Vz: cylinder [-0.375, 0.375] x [0, 3.0] minus upper cone
    pb_pts = [(-0.375, 0.0), (-0.375, 3.0), (0.375, 3.0), (0.375, 0.0), (0.0, 0.9)]
    ax1.add_patch(patches.Polygon(pb_pts, closed=True, facecolor="#fde68a", edgecolor="#d97706",
                                  hatch="///", lw=1.5, alpha=0.80, zorder=4))

    # Full cone (base d=1.5 -> [-0.75, 0.75] at y=-0.9, apex at y=+0.9)
    cone_pts = [(-0.75, -0.9), (0.75, -0.9), (0.0, 0.9)]
    ax1.add_patch(patches.Polygon(cone_pts, closed=True, facecolor="#cbd5e1", edgecolor="#0f172a", lw=2.0, zorder=5))
    ax1.plot([-0.375, 0.375], [0.0, 0.0], color="#dc2626", ls="--", lw=1.8, zorder=6)
    ax1.annotate("底孔接触圆\n" + r"$D_0 = 0.75\,\mathrm{m}$",
                 xy=(0.34, 0.02), xytext=(0.56, 0.62),
                 fontsize=8.8, ha="left", va="center", color="#dc2626", fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#fca5a5", alpha=0.95),
                 arrowprops=dict(arrowstyle="->", color="#dc2626", lw=1.3), zorder=7)
    ax1.text(0.0, 2.05, "实压力体 " + r"$V_z$" + "\n" + r"$= V_{\mathrm{cyl}} - V_{\mathrm{cone}}$",
             ha="center", va="center", fontsize=9.3, color="#92400e", fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.2", facecolor="#fffbeb", edgecolor="#f59e0b", alpha=0.92), zorder=7)

    ax1.plot([-1.75, -1.42], [3.0, 3.0], color="#64748b", ls=":", lw=1.0)
    ax1.plot([-1.75, -1.42], [0.0, 0.0], color="#64748b", ls=":", lw=1.0)
    ax1.annotate("", xy=(-1.62, 3.0), xytext=(-1.62, 0.0),
                 arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.3))
    ax1.text(-1.70, 1.5, r"$H = 3.00\,\mathrm{m}$", ha="right", va="center", fontsize=9.5, fontweight="bold")

    ax1.set_xlim(-2.65, 1.85)
    ax1.set_ylim(-1.15, 3.55)
    ax1.axis("off")
    ax1.set_title("（a）圆底孔上方锥面实压力体分解", fontsize=10.5, pad=6)

    # Right: Vertical FBD of cone at critical opening (N_seat = 0)
    cone_fbd = [(-0.65, -0.7), (0.65, -0.7), (0.0, 0.85)]
    ax2.add_patch(patches.Polygon(cone_fbd, closed=True, facecolor="#e2e8f0", edgecolor="#0f172a", lw=2.0))

    # Upward wire tension T = W = 12000 N
    ax2.annotate("", xy=(0.0, 2.15), xytext=(0.0, 0.88),
                 arrowprops=dict(arrowstyle="->", color="#16a34a", lw=2.6))
    ax2.text(0.08, 1.75, "钢丝向上拉力\n" + r"$T = W = 12000\,\mathrm{N}$",
             fontsize=9.5, color="#15803d", fontweight="bold", va="center")

    # Downward hydrostatic force Fz = 11690 N
    ax2.annotate("", xy=(-0.22, -1.55), xytext=(-0.22, -0.15),
                 arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.6))
    ax2.text(-0.30, -1.25, "向下静水总压力\n" + r"$F_z = 11690\,\mathrm{N}$",
             fontsize=9.3, ha="right", va="center", color="#b91c1c", fontweight="bold")

    # Downward self-weight G = 310 N
    ax2.annotate("", xy=(0.25, -1.35), xytext=(0.25, -0.25),
                 arrowprops=dict(arrowstyle="->", color="#ea580c", lw=2.2))
    ax2.text(0.33, -1.05, "自重 " + r"$G = 310\,\mathrm{N}$",
             fontsize=9.3, ha="left", va="center", color="#c2410c", fontweight="bold")

    ax2.text(0.0, -1.95, "临界开启平衡：" + r"$F_z + G = W$", ha="center", fontsize=9.8, color="#0f172a", fontweight="bold")
    ax2.set_xlim(-1.55, 1.55)
    ax2.set_ylim(-2.2, 2.35)
    ax2.axis("off")
    ax2.set_title("（b）锥形阀临界开启竖向受力图", fontsize=10.5, pad=6)

    plt.tight_layout()
    fig.savefig(fig_dir / "q08_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2018_q09_sol(fig_dir: Path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.0, 3.9), gridspec_kw={"width_ratios": [1.15, 1.0]})
    fig.patch.set_facecolor("white")

    # Left: Tank and 3 trajectories (h/H = 0.2, 0.5, 0.8)
    ax1.add_patch(patches.Rectangle((-0.45, 0.0), 0.45, 1.0, facecolor="#bae6fd", alpha=0.65))
    ax1.plot([-0.45, -0.45, 0.0, 0.0], [1.12, 0.0, 0.0, 1.12], color="#0f172a", lw=2.1)
    ax1.plot([-0.45, 0.0], [1.0, 1.0], color="#0284c7", lw=2.0)
    ax1.plot([-0.5, 1.22], [0.0, 0.0], color="#334155", lw=1.8)

    for ratio, col, ls, lbl in [
        (0.2, "#0284c7", "--", r"$h = 0.2H \Rightarrow x = 0.8H$"),
        (0.5, "#dc2626", "-", r"$h = 0.5H \Rightarrow x_{\max} = H$"),
        (0.8, "#16a34a", "-.", r"$h = 0.8H \Rightarrow x = 0.8H$"),
    ]:
        xmax = 2.0 * np.sqrt(ratio * (1.0 - ratio))
        xs = np.linspace(0, xmax, 100)
        ys = ratio - (xs**2) / (4.0 * (1.0 - ratio))
        ax1.plot(xs, ys, color=col, ls=ls, lw=2.1, label=lbl)
        ax1.scatter([0.0], [ratio], color=col, s=22, zorder=5)

    ax1.annotate("", xy=(1.0, -0.10), xytext=(0.0, -0.10),
                 arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.5))
    ax1.text(0.5, -0.22, r"$x_{\max} = H$", ha="center", fontsize=9.8, color="#dc2626", fontweight="bold")
    ax1.legend(loc="upper right", frameon=True, fontsize=8.5)
    ax1.set_xlim(-0.55, 1.30)
    ax1.set_ylim(-0.30, 1.22)
    ax1.axis("off")
    ax1.set_title("（a）不同孔口高度平抛射流轨迹对比", fontsize=10.5, pad=6)

    # Right: Dimensionless curve x/H = 2*sqrt((h/H)*(1 - h/H))
    eta = np.linspace(0.0, 1.0, 200)
    xi = 2.0 * np.sqrt(eta * (1.0 - eta))
    ax2.plot(xi, eta, color="#0284c7", lw=2.3)
    ax2.scatter([1.0], [0.5], color="#dc2626", s=42, zorder=5)
    ax2.plot([0, 1.0], [0.5, 0.5], color="#dc2626", ls="--", lw=1.3)
    ax2.plot([1.0, 1.0], [0, 0.5], color="#dc2626", ls="--", lw=1.3)
    ax2.text(0.58, 0.55, "极值点：" + r"$h = \dfrac{H}{2},\; x_{\max} = H$", fontsize=9.2, color="#dc2626", fontweight="bold")

    ax2.set_xlabel("无量纲水平射程 " + r"$x / H$", fontsize=9.8)
    ax2.set_ylabel("无量纲孔口高度 " + r"$h / H$", fontsize=9.8)
    ax2.set_xlim(0.0, 1.18)
    ax2.set_ylim(0.0, 1.08)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.set_title("（b）无量纲射程曲线 " + r"$x/H = 2\sqrt{(h/H)(1-h/H)}$", fontsize=10.2, pad=6)

    plt.tight_layout()
    fig.savefig(fig_dir / "q09_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2018_q10_sol(fig_dir: Path):
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    fig.patch.set_facecolor("white")

    # Platform scale base
    ax.add_patch(patches.Rectangle((1.35, 0.55), 3.30, 0.30, facecolor="#cbd5e1", edgecolor="#0f172a", lw=1.8))
    ax.plot([0.9, 5.1], [0.35, 0.35], color="#0f172a", lw=2.2)

    # Tank + water
    ax.add_patch(patches.Rectangle((1.15, 0.88), 3.70, 1.85, facecolor="#bae6fd", alpha=0.65))
    ax.plot([1.15, 1.15, 4.85, 4.85], [3.15, 0.88, 0.88, 3.15], color="#0f172a", lw=2.2)
    ax.plot([1.15, 4.85], [2.73, 2.73], color="#0284c7", lw=2.0)

    # Left horizontal outlet
    ax.add_patch(patches.Rectangle((0.45, 1.25), 0.72, 0.22, facecolor="#bae6fd", edgecolor="none"))
    ax.plot([0.45, 1.15], [1.47, 1.47], color="#0f172a", lw=1.8)
    ax.plot([0.45, 1.15], [1.25, 1.25], color="#0f172a", lw=1.8)
    ax.annotate("", xy=(-0.15, 1.36), xytext=(0.65, 1.36),
                arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.1))
    ax.text(0.25, 1.66, "水平出流 " + r"$v_{2z} = 0$", ha="center", fontsize=9.2, color="#0369a1")

    # Top vertical inlet jet
    ax.annotate("", xy=(3.0, 2.76), xytext=(3.0, 3.75),
                arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.6))
    ax.text(3.15, 3.48, "铅直入射 " + r"$v_1 = 30.56\,\mathrm{m/s}$" + "\n（" + r"$v_{1z} = -v_1$" + "，动量冲击 " + r"$\rho Q v_1 = 1829.8\,\mathrm{N}$" + "）",
            fontsize=9.2, va="center", color="#0369a1", fontweight="bold")

    # Control volume dashed box around whole (tank + water)
    cv_box = patches.Rectangle((0.92, 0.82), 4.12, 2.42, fill=False, edgecolor="#dc2626", ls="--", lw=1.7)
    ax.add_patch(cv_box)
    ax.text(5.12, 2.95, "整体控制体\n（水箱 + 箱内水）", fontsize=9.2, color="#dc2626", va="top")

    # Gravity & scale support reaction N
    ax.annotate("", xy=(2.35, 1.18), xytext=(2.35, 2.18),
                arrowprops=dict(arrowstyle="->", color="#ea580c", lw=2.3))
    ax.text(2.26, 1.78, "总重 " + r"$G_{\mathrm{tank}} + G_{\mathrm{water}}$" + "\n" + r"$= 10.76\,\mathrm{kN}$",
            ha="right", va="center", fontsize=9.0, color="#c2410c", fontweight="bold")

    ax.annotate("", xy=(2.92, 1.58), xytext=(2.92, 0.42),
                arrowprops=dict(arrowstyle="->", color="#16a34a", lw=2.7))
    ax.text(3.04, 1.22, "磅秤支反力 " + r"$N = 12.59\,\mathrm{kN}$" + "\n（等效质量 " + r"$1284.7\,\mathrm{kg}$" + "）",
            ha="left", va="center", fontsize=9.1, color="#15803d", fontweight="bold")

    ax.set_xlim(-0.45, 6.75)
    ax.set_ylim(0.15, 3.98)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q10_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2018_q12_sol(fig_dir: Path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.0, 3.8), gridspec_kw={"width_ratios": [1.0, 1.5]})
    fig.patch.set_facecolor("white")

    # Left: Rectangular aqueduct cross-section (b=1.5 m, h0=2.56 m)
    b, h0 = 1.5, 2.56
    ax1.add_patch(patches.Rectangle((-b / 2, 0), b, h0, facecolor="#bae6fd", alpha=0.7))
    ax1.plot([-b / 2, -b / 2, b / 2, b / 2], [3.05, 0, 0, 3.05], color="#0f172a", lw=2.5)
    ax1.plot([-b / 2, b / 2], [h0, h0], color="#0284c7", lw=2.0)

    ax1.annotate("", xy=(b / 2, -0.25), xytext=(-b / 2, -0.25),
                 arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.4))
    ax1.text(0, -0.48, r"$b = 1.5\,\mathrm{m}$", ha="center", fontsize=9.8)

    ax1.annotate("", xy=(b / 2 + 0.28, h0), xytext=(b / 2 + 0.28, 0),
                 arrowprops=dict(arrowstyle="<->", color="#0369a1", lw=1.4))
    ax1.text(b / 2 + 0.36, h0 / 2, r"$h_0 = 2.56\,\mathrm{m}$", va="center", fontsize=9.6, color="#0369a1", fontweight="bold")
    ax1.text(0, 1.28, r"$A = 3.84\,\mathrm{m^2}$" + "\n" + r"$\chi = 6.62\,\mathrm{m}$" + "\n" + r"$R = 0.580\,\mathrm{m}$",
             ha="center", va="center", fontsize=9.2, color="#0f172a")

    ax1.set_xlim(-1.45, 2.25)
    ax1.set_ylim(-0.7, 3.35)
    ax1.axis("off")
    ax1.set_title("（a）矩形渡槽横断面要素", fontsize=10.5, pad=6)

    # Right: Longitudinal profile (Z1=52.06 m -> Z2=51.707 m over L=116.5 m)
    x = np.array([0.5, 5.5])
    yb = np.array([1.65, 0.85])
    yw = yb + 1.35
    ye = yw + 0.42

    ax2.fill_between(x, yb, yw, color="#bae6fd", alpha=0.65)
    ax2.plot(x, yb, color="#0f172a", lw=2.4, label="槽底线（底坡 " + r"$i = 0.00303$" + "）")
    ax2.plot(x, yw, color="#0284c7", lw=2.0, label="均匀流水面线（" + r"$J_p = i$" + "）")
    ax2.plot(x, ye, color="#dc2626", ls="--", lw=1.8, label="总水头线（" + r"$J = i$" + "）")
    ax2.plot([0.3, 5.8], [0.25, 0.25], color="#64748b", ls=":", lw=1.2)

    ax2.scatter([0.5, 5.5], [1.65, 0.85], color="#0f172a", s=32, zorder=5)
    ax2.text(0.5, 1.50, "进口槽底\n" + r"$Z_1 = 52.06\,\mathrm{m}$", ha="center", va="top", fontsize=9.2, fontweight="bold")
    ax2.text(5.5, 0.70, "出口槽底\n" + r"$Z_2 = 51.71\,\mathrm{m}$", ha="center", va="top", fontsize=9.2, color="#dc2626", fontweight="bold")

    ax2.annotate("", xy=(5.5, 1.65), xytext=(5.5, 0.85),
                 arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.5))
    ax2.plot([0.5, 5.65], [1.65, 1.65], color="#94a3b8", ls="--", lw=1.0)
    ax2.text(5.65, 1.25, r"$\Delta Z = iL = 0.353\,\mathrm{m}$", va="center", fontsize=9.2, color="#dc2626")

    ax2.annotate("", xy=(5.5, 0.08), xytext=(0.5, 0.08),
                 arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.3))
    ax2.text(3.0, -0.14, "渡槽总长 " + r"$L = 116.5\,\mathrm{m}$", ha="center", fontsize=9.5)

    ax2.legend(loc="upper right", frameon=True, fontsize=8.6)
    ax2.set_xlim(-0.15, 7.35)
    ax2.set_ylim(-0.35, 3.85)
    ax2.axis("off")
    ax2.set_title("（b）均匀流三线平行纵剖面高程关系", fontsize=10.5, pad=6)

    plt.tight_layout()
    fig.savefig(fig_dir / "q12_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


# ==============================================================================
# Build Standardized JSON Dictionaries for 2019 & 2018
# ==============================================================================

def build_2019_paper() -> dict:
    return {
        "year": 2019,
        "code": "849",
        "subject": "水力学（水）",
        "school": "扬州大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": True,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试（A 卷）。",
            "全卷共 12 道大题：第 1～4 题为基本概念与机理简答题（4×8=32 分），第 5～12 题为综合计算与公式推导题（共 118 分）。",
            "除题干另有给定外，常温清水密度取 $\\rho = 1000\\,\\mathrm{kg/m^3}$，重力加速度取 $g = 9.80\\,\\mathrm{m/s^2}$（解析同步列出 $g = 9.81\\,\\mathrm{m/s^2}$ 对照结果）。"
        ],
        "sections": [
            {
                "id": "short",
                "title": "一、机理分析与简答题",
                "description": "第 1～4 题，每题 8 分，共 32 分。",
                "range": [1, 4],
                "scorePerQuestion": 8,
                "totalScore": 32
            },
            {
                "id": "calc",
                "title": "二、计算与推导题",
                "description": "第 5～12 题（12+20+15+12+20+15+12+12 分），共 118 分。",
                "range": [5, 12],
                "totalScore": 118
            }
        ],
        "questions": [
            {
                "id": "yzu-849-2019-01",
                "year": 2019,
                "no": 1,
                "type": "short",
                "score": 8,
                "title": "静止液体与运动液体黏滞性固有属性辨析",
                "stem": "有人说“静止液体没有粘滞性，运动液体才有粘滞性”，这种说法对吗？为什么？",
                "note": "",
                "figures": [],
                "shortAnswer": "不对。黏滞性是液体本身的固有物理属性（取决于液体种类与温度），静止液体同样具有黏滞性；只是静止液体内部质点无相对运动（du/dy=0），黏滞性所引起的内摩擦力（切应力 τ=0）未表现出来而已。",
                "judgeAnswer": None,
                "answer": "**这种说法不对（错误）。**\n\n**原因**：\n1. **黏滞性是液体的固有物性**：黏滞性源于液体分子间的内聚力以及分子热运动引起的动量交换，其强弱由动力黏度 $\\mu$（或运动黏度 $\\nu$）度量，仅取决于液体的种类和温度（以及极高压强），与液体处于静止还是运动状态无关，因此静止液体同样具有黏滞性。\n2. **黏滞性的外在力学表现需要相对运动**：根据牛顿内摩擦定律 $\\tau = \\mu \\frac{\\mathrm{d}u}{\\mathrm{d}y}$，静止液体内部各层质点之间没有相对运动，速度梯度 $\\frac{\\mathrm{d}u}{\\mathrm{d}y} = 0$，虽然 $\\mu \\neq 0$，但黏滞切应力 $\\tau = 0$（即黏滞力未显现出来）；只有当液体发生相对运动（$\\frac{\\mathrm{d}u}{\\mathrm{d}y} \\neq 0$）时，黏滞性才以抵抗相对变形的内摩擦力形式表现出来。不能将“内摩擦力为零”误认为“没有黏滞性”。",
                "analysis": "本题核心在于严格区分**物性参数（黏滞性 $\\mu$）**与**力学响应（黏性切应力 $\\tau$）**两个概念：\n\n$$\n\\tau = \\mu \\frac{\\mathrm{d}u}{\\mathrm{d}y}\n$$\n\n- **动力黏度 $\\mu$**：表征液体抵抗剪切变形能力的固有物理属性（犹如固体质量表征惯性一样，物体静止时惯性依然存在）。例如 $20^{\\circ}\\mathrm{C}$ 的静止水其动力黏度恒为 $\\mu \\approx 1.005 \\times 10^{-3}\\,\\mathrm{Pa\\cdot s} > 0$，绝非理想无黏流体。\n- **切应力 $\\tau$**：黏滞性在流层存在法向速度梯度 $\\frac{\\mathrm{d}u}{\\mathrm{d}y} \\neq 0$ 时产生的宏观内摩擦力。静止或作刚体平动的液体因 $\\frac{\\mathrm{d}u}{\\mathrm{d}y} = 0$ 而使 $\\tau = 0$，这属于黏滞力“隐而不发”，而非液体失去了黏滞性。",
                "analysisFigures": [],
                "pitfalls": "切忌把“黏滞性（物性 $\\mu$）”与“黏滞力 / 切应力（$\\tau$）”混为一谈！正确表述应当是：“静止液体具有黏滞性（$\\mu \\neq 0$），但不显现黏滞切应力（$\\tau = 0$）”。",
                "chapter": 1,
                "kps": ["液体黏滞性", "牛顿内摩擦定律"],
                "method": "牛顿内摩擦定律与黏滞性物理本质辨析",
                "difficulty": 1,
                "rubric": [
                    {"label": "明确判断该说法错误，指出黏滞性是液体固有的物理属性（仅与种类、温度有关，静止液体同样具有黏滞性）", "pts": 4},
                    {"label": "结合牛顿内摩擦定律 τ = μ(du/dy) 阐明静止液体因无相对运动（du/dy=0）故不产生切应力，而非没有黏滞性", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2019-02",
                "year": 2019,
                "no": 2,
                "type": "short",
                "score": 8,
                "title": "一元流、二元流与三元流的空间自变量分类及工程实例",
                "stem": "液体流动可分为一元流、二元流、三元流，即一维流动、二维流动、三维流动，试说明这些流动有何不同，并列举相应的实例。",
                "note": "",
                "figures": [],
                "shortAnswer": "按流场运动要素（流速、压强等）所依赖的空间坐标自变量个数划分：一元流仅与 1 个空间坐标有关（如总流断面平均法分析的有压管流、棱柱体明渠渐变流）；二元流与 2 个空间坐标有关（如宽浅矩形明渠剖面流、平行平板间层流、长溢流坝面水流）；三元流与 3 个空间坐标均有关（如天然弯曲河道水流、水轮机流道水流、桥墩三维绕流）。",
                "judgeAnswer": None,
                "answer": "三者的本质区别在于**描述流场运动要素（流速、压强等）所需的独立空间坐标（空间自变量）个数不同**（与时间自变量 $t$ 无关）：\n\n1. **一元流（一维流动）**：运动要素仅随 **1 个**空间坐标（通常为流线弧长坐标 $s$）变化，即 $u = u(s, t)$。\n   - **实例**：微小流束流动；工程水力学中引入“断面平均流速”简化后的有压圆管总流、顺直棱柱形明渠均匀流或渐变流。\n2. **二元流（二维流动 / 平面流动）**：运动要素随 **2 个**相互正交的空间坐标变化（而在第三个方向上无变化且无速度分量），即 $\\vec{u} = \\vec{u}(x, y, t)$，各平行平面上的流线形状完全相同。\n   - **实例**：两无限宽平行平板间的层流、顺直长溢流坝（实用堰）中段剖面泄流、极宽矩形明渠中的水流、长圆柱体横截面绕流。\n3. **三元流（三维流动 / 空间流动）**：运动要素随 **3 个**空间坐标 $(x, y, z)$ 均发生变化，即 $\\vec{u} = \\vec{u}(x, y, z, t)$。\n   - **实例**：天然蜿蜒弯曲河道（含横向环流）的水流、圆球或桥墩局部绕流、水泵叶轮与水轮机蜗壳内的空间流动、断面沿程急剧收缩或扩大的非对称流道水流。",
                "analysis": "**1. 流动维数的数学判据**\n\n在欧拉法中，一般非恒定流的速度场记为 $\\vec{u} = \\vec{u}(x, y, z, t)$。流动是“几元流（几维流）”，**只看空间自变量 $(x, y, z)$ 的个数，不计入时间变量 $t$**（例如非恒定一维水击波 $v = v(s, t)$ 仍属一元非恒定流）。\n\n**2. 需要注意的经典概念辨析**\n\n- 若以真实微观流场严格考察，圆管层流的速度分布 $u(r) = u_{\\max}(1 - r^2/r_0^2)$ 在柱坐标系下仅依赖于径向坐标 $r$（轴对称流），而在直角坐标系 $(x,y)$ 下与两个坐标有关；但在工程水力学总流分析法中，用断面平均流速 $v(s)$ 代替断面上点流速后，有压管流和明渠总流均按**一元总流**处理。\n- 列举二元流实例时，关键特征是“沿宽度方向无限宽或边壁影响可忽略，各纵剖面流况完全一致”，如长直宽浅明渠剖面流或顺直溢流坝单宽剖面流。",
                "analysisFigures": [],
                "pitfalls": "1. 切忌误把时间 $t$ 当作一个维度（误认为非恒定流比恒定流多一维）！几维流动完全取决于选择合适坐标系后运动要素所依赖的**空间坐标自变量个数**。\n2. 勿将“速度分量的个数”与“空间自变量的个数”简单等同，判别标准应以运动要素所含空间自变量个数为准。",
                "chapter": 3,
                "kps": ["一元二元三元流动分类", "欧拉法运动要素描述"],
                "method": "运动要素空间坐标维数分类法",
                "difficulty": 1,
                "rubric": [
                    {"label": "准确阐明一元流、二元流、三元流按运动要素所含空间坐标自变量个数（1、2、3 个）区分的定义", "pts": 5},
                    {"label": "分别给出物理合理的工程流动实例（各 1 例以上）", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2019-03",
                "year": 2019,
                "no": 3,
                "type": "short",
                "score": 8,
                "title": "影响水头损失的主要因素及沿程与局部水头损失产生机理辨析",
                "stem": "影响水头损失大小的主要因素有哪些？水头损失分为沿程水头损失和局部水头损失，这两种水头损失的产生机理是否相同？为什么？",
                "note": "",
                "figures": [],
                "shortAnswer": "主要因素：（1）内因——液体的黏滞性与惯性（物性 μ、ρ）；（2）外因——固体边界几何条件（管长直径、壁面粗糙度、局部断面形状突变）与液流运动状态（流速大小、层流或紊流流态，综合体现为雷诺数 Re）。产生机理本质相同（均源于液体黏滞性在相对运动质点间产生内摩擦切应力做功转化为热能），仅诱发相对运动的外部边界条件不同。",
                "judgeAnswer": None,
                "answer": "**（1）影响水头损失大小的主要因素**：\n① **流体的物理性质（内因）**：主要是液体的**黏滞性**（动力黏度 $\\mu$）与密度 $\\rho$（惯性）；\n② **固体边界条件（外因）**：包括流道沿程几何尺寸（长度 $l$、水力半径 $R$ 或管径 $d$）、固体壁面的绝对粗糙度 $\\Delta$（或相对粗糙度 $\\Delta/d$），以及局部管件/边界的形状、曲率与过水断面急剧变化情况；\n③ **液流运动状态**：断面平均流速 $v$ 的大小及水流流态（层流或紊流脉动混掺强度，无量纲综合体现为雷诺数 $Re = \\frac{vd}{\\nu}$）。\n\n**（2）两种水头损失的产生机理本质相同**：\n- **相同原因（内因一致）**：无论是沿程水头损失还是局部水头损失，其根本物理内因都是**液体具有黏滞性**，且液流内部各流层或质点之间存在相对运动（速度梯度），黏性切应力做功将水流的机械能不可逆地耗散转化为热能（理想无黏液体中两种损失均为零）。\n- **表现差异（外因不同）**：将水头损失划分为两类，只是促成质点剧烈相对运动的外因不同——**沿程水头损失**是在边壁顺直均匀流段内，由固壁摩阻维持的法向速度梯度及紊流横向脉动混掺引起的沿程持续摩擦耗能；**局部水头损失**则是由局部边界急剧转折、扩大或收缩引发流线弯曲、边界层分离及旋涡区剧烈碰撞掺混，最终仍通过旋涡微团间的**黏性剪切摩擦**将机械能转化为热能。",
                "analysis": "结合达西公式 $h_f = \\lambda\\left(Re, \\frac{\\Delta}{d}\\right)\\frac{l}{d}\\frac{v^2}{2g}$ 与局部损失公式 $h_j = \\zeta\\frac{v^2}{2g}$ 可系统梳理影响水头损失的三要素：\n\n1. **内因**：黏滞性 $\\mu$ 是产生切应力的物理前提；\n2. **边界外因**：相对粗糙度 $\\frac{\\Delta}{d}$ 主导沿程阻力，几何局部突变程度主导局部阻力系数 $\\zeta$；\n3. **流动参数**：流速水头 $\\frac{v^2}{2g}$ 与反映惯性力/黏性力之比的雷诺数 $Re$。\n\n在能量转化链条上：\n- **沿程水头损失**：主流机械能 $\\xrightarrow{\\text{壁面剪切 + 紊流脉动}}$ 黏性摩擦耗散为热能；\n- **局部水头损失**：主流机械能 $\\xrightarrow{\\text{边界突变分离}}$ 旋涡动能 $\\xrightarrow{\\text{旋涡破碎与质点相对剪切}}$ **黏性摩擦耗散为热能**。\n\n可见，局部旋涡只是能量传递的中间载体，最终将机械能不可逆耗散掉的物理机制依然是液体的黏滞内摩擦，因此两者的产生机理在物理本质上是完全相同的。",
                "analysisFigures": [],
                "pitfalls": "切勿因为局部水头损失伴随“碰撞与旋涡”就误判两者产生机理不同！旋涡本身仍是流体机械能（涡动能），若没有液体黏滞性产生的微团剪切摩擦，涡动能无法耗散为内能。故“外因（边界诱因）不同，内因与耗能本质（黏滞切应力做功）相同”是最严密的满分表述。",
                "chapter": 4,
                "kps": ["水头损失影响因素", "沿程与局部损失", "黏性耗散机理"],
                "method": "水头损失影响因素与黏性耗散机理分析",
                "difficulty": 2,
                "rubric": [
                    {"label": "完整答出影响水头损失的主要因素（液体黏滞性物性、边界几何尺寸与粗糙度、流速与流态 Re）", "pts": 4},
                    {"label": "明确回答产生机理本质相同，并阐明两者均因黏滞性与质点相对运动产生切应力耗能，仅外部边界诱因不同", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2019-04",
                "year": 2019,
                "no": 4,
                "type": "short",
                "score": 8,
                "title": "复式断面明渠均匀流水力计算方法及水力半径骤减机理分析",
                "stem": "在明渠均匀流的水力计算中，如图所示复式断面明渠能否直接采用单式断面明渠的方法来进行计算？为什么？",
                "note": "",
                "figures": [
                    {"src": "figures/q04_orig.png", "caption": "题 4 图　复式断面明渠横断面示意图"}
                ],
                "shortAnswer": "不能。因为水深刚漫过滩地（h 略大于 h'）时，过水断面面积增加很小而湿周 χ 突然剧增，导致按整断面算出的水力半径 R=A/χ 骤减，使曼宁公式算得的流量随水深增大反而反常减小，且主槽与滩地水深、糙率及流速差异悬殊，故必须分块（主槽与滩地）分别计算流量再求和。",
                "judgeAnswer": None,
                "answer": "**不能直接采用单式断面明渠的整断面法进行计算**（应从滩地边坡脚作铅直分界线，将断面划分为主槽与左、右滩地若干子断面，分别用均匀流公式计算流量后再相加）。\n\n**原因**：\n1. **漫滩初期水力半径 $R$ 骤减导致“水深增大、计算流量反而减小”的反常悖论**：当水深由主槽满槽水深 $h \\le h^{\\prime}$ 刚漫上两侧宽阔滩地（$h$ 略大于 $h^{\\prime}$）时，滩地水层极薄，过水断面面积 $A$ 增加很少，但固体接触湿周 $\\chi$ 却突然增加了两侧很长的滩地底宽，导致整断面水力半径 $R = \\frac{A}{\\chi}$ 发生剧烈突降（见解图 4）。若直接套用单式断面公式 $Q = \\frac{1}{n} A R^{2/3} i^{1/2}$，在 $h > h^{\\prime}$ 的一定水深范围内会出现“水深越深、计算流量反而越小”的荒谬结果，严重违背物理实际。\n2. **主槽与滩地水力条件差异悬殊**：主槽水深大、表面较平整（糙率 $n$ 小）、流速远大于滩地；滩地水浅且常有植被（糙率 $n$ 大）、流速很慢，全断面流速分布极不均匀，也不满足单式断面单一糙率与整体平均流速水力半径的假定。",
                "analysis": "以曼宁公式考察复式断面的输水能力（水力半径突变规律见解图 4）：\n\n$$\nQ = K\\sqrt{i} = \\frac{1}{n} A R^{2/3} i^{1/2} = \\frac{1}{n} \\frac{A^{5/3}}{\\chi^{2/3}} i^{1/2}\n$$\n\n**1. 为什么单式整断面算法会失效？**\n\n设主槽满槽水深为 $h^{\\prime}$，对应面积 $A_0$、湿周 $\\chi_0$，两侧水平滩地总宽度为 $B_{\\text{滩}}$。当水位刚刚漫过滩唇达到 $h = h^{\\prime} + \\Delta h$（$\\Delta h \\to 0^+$）时：\n- 过水断面面积近似不变：$A(h^{\\prime}+\\Delta h) \\approx A_0$；\n- 湿周却发生阶跃突增：$\\chi(h^{\\prime}+\\Delta h) \\approx \\chi_0 + B_{\\text{滩}} \\gg \\chi_0$；\n- 因而水力半径 $R = A/\\chi$ 瞬间大幅跌落，使整断面流量模数 $K = \\frac{1}{n} A R^{2/3}$ 显著小于满槽未漫滩时的 $K_0$，造成计算出的水位—流量关系曲线 $Q(h)$ 在 $h = h^{\\prime}$ 处发生折返失真。\n\n**2. 正确的工程处理方法（主滩分块合成法）**\n\n自左、右滩唇向水面作铅直假想分界线，将复式断面分割为主槽（$A_1, n_1, R_1$）和左、右滩地（$A_2, n_2, R_2$ 及 $A_3, n_3, R_3$）独立子区（假想水体铅直分界面不计入各自湿周），按同一底坡 $i$ 分块计算后叠加：\n\n$$\nQ = \\sum_{k=1}^{3} Q_k = \\left( \\frac{1}{n_1} A_1 R_1^{2/3} + \\frac{1}{n_2} A_2 R_2^{2/3} + \\frac{1}{n_3} A_3 R_3^{2/3} \\right) i^{1/2}\n$$",
                "analysisFigures": [
                    {"src": "figures/q04_sol.png", "caption": "解图 4　复式断面主槽—滩地分块划分与漫滩水力半径突变曲线"}
                ],
                "pitfalls": "答题时切勿只泛泛说“断面形状复杂”，必须点出最核心的定量机理解释：**当水深刚超过 $h^{\\prime}$ 漫上滩地时，面积 $A$ 微增而湿周 $\\chi$ 突增，导致水力半径 $R = A/\\chi$ 骤减，直接按单式断面计算会出现流量随水深增大反而减小的失真现象**！",
                "chapter": 7,
                "kps": ["复式断面明渠水力计算", "水力半径与湿周", "曼宁公式"],
                "method": "复式断面主滩分块与水力半径突变分析",
                "difficulty": 2,
                "rubric": [
                    {"label": "明确回答不能直接采用单式断面明渠方法计算", "pts": 2},
                    {"label": "阐明漫滩初期（h 略大于 h'）面积增加有限而湿周突增导致水力半径 R 骤减、计算流量反常减小的核心原因", "pts": 3},
                    {"label": "补充主槽与滩地水深、糙率、流速差异大，并指明应划铅直分界线分块计算流量再求和", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2019-05",
                "year": 2019,
                "no": 5,
                "type": "calc",
                "score": 12,
                "title": "密闭容器受压浸没圆柱体竖向静力平衡与测压管水柱高度计算",
                "stem": "如图所示，有一直径 $d = 12\\,\\mathrm{cm}$ 的圆柱体，其质量 $m = 5\\,\\mathrm{kg}$，在力 $F = 100\\,\\mathrm{N}$ 的作用下，当淹没深度 $h = 0.5\\,\\mathrm{m}$ 时，处于静止状态，求测压管中水柱的高度 $H$。",
                "note": "",
                "figures": [
                    {"src": "figures/q05_orig.png", "caption": "题 5 图　密闭顶盖容器内浸没圆柱体与测压管"}
                ],
                "shortAnswer": "H = 0.844 m（84.4 cm；若取 g = 9.81 m/s² 则 H = 0.843 m）",
                "judgeAnswer": None,
                "answer": "测压管中水柱的高度 $H \\approx 0.844\\,\\mathrm{m}$（或 $84.4\\,\\mathrm{cm}$；若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $H \\approx 0.843\\,\\mathrm{m}$）。",
                "analysis": "**1. 分析圆柱体底面动水/静水压强与顶盖内表面压强关系**\n\n设容器水平密闭顶盖下表面（与液体接触面，即淹没深度起算面）处的相对压强为 $p_0$。左侧敞口测压管液面通大气，故测压管中高出顶盖下表面的水柱高度 $H$ 满足：\n\n$$\np_0 = \\rho g H\n$$\n\n圆柱体直径 $d = 0.12\\,\\mathrm{m}$，横截面积为：\n\n$$\nA = \\frac{\\pi}{4} d^2 = \\frac{\\pi}{4} \\times 0.12^2 = 0.0036\\pi \\approx 0.011310\\,\\mathrm{m^2}\n$$\n\n圆柱体下端平底面位于淹没深度 $h = 0.5\\,\\mathrm{m}$ 处，该水平面上的相对静水压强为：\n\n$$\np_{\\text{底}} = p_0 + \\rho g h = \\rho g (H + h)\n$$\n\n**2. 列圆柱体竖向静力平衡方程求解 $H$**\n\n以圆柱体为隔离体：上端暴露于大气（相对压强为 $0$），受向下的外推力 $F = 100\\,\\mathrm{N}$ 与自身重力 $W = mg$；侧面静水压力水平对称自相平衡；下底面受水体向上的静水总压力 $P_{\\text{底}} = p_{\\text{底}} A$。由竖向力平衡 $\\sum F_z = 0$ 得：\n\n$$\nF + m g = \\rho g (H + h) A\n$$\n\n整理得测压管水柱高度表达式：\n\n$$\nH = \\frac{F + m g}{\\rho g A} - h = \\frac{F}{\\rho g A} + \\frac{m}{\\rho A} - h\n$$\n\n代入已知数值（取 $\\rho = 1000\\,\\mathrm{kg/m^3}$，$g = 9.80\\,\\mathrm{m/s^2}$）：\n\n$$\nH = \\frac{100 + 5 \\times 9.80}{1000 \\times 9.80 \\times 0.0113097} - 0.5 = \\frac{149.00}{110.835} - 0.5 = 1.3443 - 0.5 = 0.8443\\,\\mathrm{m} \\approx 0.844\\,\\mathrm{m}\n$$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $F + mg = 149.05\\,\\mathrm{N}$，$p_0 \\approx 8273.9\\,\\mathrm{Pa}$，$H = \\frac{149.05}{1000 \\times 9.81 \\times 0.0113097} - 0.5 = 0.8434\\,\\mathrm{m} \\approx 0.843\\,\\mathrm{m}$。）",
                "analysisFigures": [],
                "pitfalls": "切忌直接套用敞口自由液面阿基米德浮力公式 $\\rho g h A$ 而漏掉容器密闭顶盖处的附加相对压强 $p_0 = \\rho g H$！圆柱体上端穿出密闭盖板通大气（表压为 $0$），故底面向上总推力为 $(p_0 + \\rho g h)A$，并非仅有 $\\rho g h A$。",
                "chapter": 2,
                "kps": ["静水压强基本方程", "测压管水头", "隔离体静力平衡"],
                "method": "隔离体竖向力平衡与静水压强递推法",
                "difficulty": 2,
                "rubric": [
                    {"label": "建立容器顶盖内表面相对压强 p0 = ρgH 及圆柱下底面压强 p底 = p0 + ρgh 的关系", "pts": 4},
                    {"label": "计算圆柱底面积 A = πd²/4 ≈ 0.01131 m² 并正确列出圆柱竖向平衡方程 F + mg = (p0 + ρgh)A", "pts": 5},
                    {"label": "代入数据准确解出测压管水柱高度 H ≈ 0.844 m（或 0.843 m）", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2019-06",
                "year": 2019,
                "no": 6,
                "type": "calc",
                "score": 20,
                "title": "分隔水与甘油的矩形平板闸门单宽静水总压力及作用点计算",
                "stem": "如图所示的矩形闸门 $AB$ 将水（$\\rho_1 = 1000\\,\\mathrm{kg/m^3}$）和甘油（$\\rho_2 = 1264\\,\\mathrm{kg/m^3}$）分隔，试求作用在单位宽度闸门上的总压力及作用点。",
                "note": "",
                "figures": [
                    {"src": "figures/q06_orig.png", "caption": "题 6 图　水与甘油双侧受压铅直矩形闸门 AB"}
                ],
                "shortAnswer": "单宽净总压力 P = 23.90 kN/m（若取 g=9.81 m/s² 则为 23.92 kN/m），方向水平向右（由水侧指向甘油侧）；作用点位于 A 点以下 0.928 m 处（即距门底 B 点 1.072 m 处）。",
                "judgeAnswer": None,
                "answer": "作用在单位宽度闸门 $AB$ 上的净静水总压力大小为 **$23.90\\,\\mathrm{kN/m}$**（若取 $g = 9.81\\,\\mathrm{m/s^2}$ 则为 **$23.92\\,\\mathrm{kN/m}$**），方向**水平向右**（由水侧指向甘油侧）；总压力的作用点位于门顶 **$A$ 点正下方 $0.928\\,\\mathrm{m}$** 处（或距门底 $B$ 点 $1.072\\,\\mathrm{m}$ 处）。",
                "analysis": "取闸门宽度 $b = 1.0\\,\\mathrm{m}$，由题 6 图几何标注可知铅直矩形闸门 $AB$ 高度 $L = 2.0\\,\\mathrm{m}$，受压面积 $A = b L = 2.0\\,\\mathrm{m^2}$，绕水平形心轴惯性矩为：\n\n$$\nI_C = \\frac{b L^3}{12} = \\frac{1.0 \\times 2.0^3}{12} = \\frac{2}{3}\\,\\mathrm{m^4}\n$$\n\n**1. 计算左侧水对单位宽度闸门的水平总压力 $P_1$ 及其作用点**\n\n- 门顶 $A$ 在左侧水面下的深度 $h_{A1} = 1.8 + 1.2 = 3.0\\,\\mathrm{m}$，门底 $B$ 深度 $h_{B1} = 3.0 + 2.0 = 5.0\\,\\mathrm{m}$，闸门形心淹没水深 $h_{C1} = 4.0\\,\\mathrm{m}$。\n- 左侧水总压力大小（方向水平向右，取 $g = 9.80\\,\\mathrm{m/s^2}$）：\n\n$$\nP_1 = \\rho_1 g h_{C1} A = 1000 \\times 9.80 \\times 4.0 \\times 2.0 = 78400\\,\\mathrm{N} = 78.40\\,\\mathrm{kN}\n$$\n\n- $P_1$ 的压心在水面下的深度 $h_{D1}$ 及距 $A$ 点的距离 $y_{D1}$：\n\n$$\nh_{D1} = h_{C1} + \\frac{I_C}{h_{C1} A} = 4.0 + \\frac{2/3}{4.0 \\times 2.0} = 4.0 + \\frac{1}{12} \\approx 4.0833\\,\\mathrm{m}\n$$\n\n$$\ny_{D1} = h_{D1} - h_{A1} = 4.0833 - 3.0 = \\frac{13}{12}\\,\\mathrm{m} \\approx 1.0833\\,\\mathrm{m}\n$$\n\n**2. 计算右侧甘油对单位宽度闸门的水平总压力 $P_2$ 及其作用点**\n\n- 门顶 $A$ 在右侧甘油液面下的深度 $h_{A2} = 1.2\\,\\mathrm{m}$，门底 $B$ 深度 $h_{B2} = 1.2 + 2.0 = 3.2\\,\\mathrm{m}$，闸门形心在甘油面下的深度 $h_{C2} = 2.2\\,\\mathrm{m}$。\n- 右侧甘油总压力大小（方向水平向左）：\n\n$$\nP_2 = \\rho_2 g h_{C2} A = 1264 \\times 9.80 \\times 2.2 \\times 2.0 = 54503.68\\,\\mathrm{N} \\approx 54.504\\,\\mathrm{kN}\n$$\n\n- $P_2$ 的压心在甘油液面下的深度 $h_{D2}$ 及距 $A$ 点的距离 $y_{D2}$：\n\n$$\nh_{D2} = h_{C2} + \\frac{I_C}{h_{C2} A} = 2.2 + \\frac{2/3}{2.2 \\times 2.0} = 2.2 + \\frac{5}{33} \\approx 2.3515\\,\\mathrm{m}\n$$\n\n$$\ny_{D2} = h_{D2} - h_{A2} = 2.3515 - 1.2 = \\frac{38}{33}\\,\\mathrm{m} \\approx 1.1515\\,\\mathrm{m}\n$$\n\n**3. 合成单宽净总压力 $P$ 并由合力矩定理求总作用点（见解图 6）**\n\n因 $P_1 > P_2$，单位宽度闸门所受净总压力方向**水平向右**，大小为：\n\n$$\nP = P_1 - P_2 = 78.400 - 54.504 = 23.896\\,\\mathrm{kN} \\approx 23.90\\,\\mathrm{kN}\n$$\n\n设合力 $P$ 作用点位于 $A$ 点下方 $y_D$ 处，对门顶 $A$ 点列合力矩平衡方程 $P \\cdot y_D = P_1 y_{D1} - P_2 y_{D2}$（注：由于分子分母同含因子 $g$，作用点位置 $y_D$ 与重力加速度 $g$ 的取值完全无关）：\n\n$$\ny_D = \\frac{P_1 y_{D1} - P_2 y_{D2}}{P_1 - P_2} = \\frac{78.400 \\times 1.08333 - 54.5037 \\times 1.15152}{23.8963} = \\frac{84.9333 - 62.7618}{23.8963} = \\frac{22.1715}{23.8963} \\approx 0.9278\\,\\mathrm{m} \\approx 0.928\\,\\mathrm{m}\n$$\n\n即总压力作用点位于 **$A$ 点下方 $0.928\\,\\mathrm{m}$** 处（距门底 $B$ 点 $2.0 - 0.928 = 1.072\\,\\mathrm{m}$，高于闸门几何中心 $1.0\\,\\mathrm{m}$ 处——这是因为右侧甘油密度更大，使净压强差 $\\Delta p(y)$ 随深度增加反而减小，故上大下小的净压强梯形压心上移至形心上方！）。\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $P_1 = 78.48\\,\\mathrm{kN}$，$P_2 = 54.56\\,\\mathrm{kN}$，净总压力 $P = 23.92\\,\\mathrm{kN}$，作用点距 $A$ 点仍为 $0.928\\,\\mathrm{m}$。）",
                "analysisFigures": [
                    {"src": "figures/q06_sol.png", "caption": "解图 6　矩形闸门 AB 双侧梯形静水压强分布与合力作用点分析"}
                ],
                "pitfalls": "1. 两侧液体密度不同（$\\rho_1 < \\rho_2$），严禁误认为净压强沿水深不变！左侧水深每增 $1\\,\\mathrm{m}$ 增压 $9.80\\,\\mathrm{kPa}$，右侧甘油每增 $1\\,\\mathrm{m}$ 增压 $12.39\\,\\mathrm{kPa}$，故净压强上大下小（$\\Delta p_A = 14.54\\,\\mathrm{kPa} > \\Delta p_B = 9.36\\,\\mathrm{kPa}$），总作用点位于闸门中点偏上（距 $A$ 点 $0.928\\,\\mathrm{m} < 1.0\\,\\mathrm{m}$），这一物理校验可瞬间检验力矩正负号是否写错！\n2. 底部标注的 $2\\,\\mathrm{m}$ 是门底 $B$ 到渠底的高度，不属于闸门 $AB$ 的受压高度，切勿将闸门高误取为 $4\\,\\mathrm{m}$。",
                "chapter": 2,
                "kps": ["平面静水总压力", "压心与合力矩定理", "双侧液体受压闸门"],
                "method": "双侧平面静水总压力合成与力矩平衡法",
                "difficulty": 3,
                "rubric": [
                    {"label": "求出左侧水对单宽闸门的总压力 P1 = 78.40 kN（或 78.48 kN）及其距 A 点位置 yD1 = 1.083 m", "pts": 6},
                    {"label": "求出右侧甘油对单宽闸门的总压力 P2 = 54.50 kN（或 54.56 kN）及其距 A 点位置 yD2 = 1.152 m", "pts": 6},
                    {"label": "合成求得净总压力大小 P = P1 - P2 = 23.90 kN/m（或 23.92 kN/m）并指明方向水平向右", "pts": 4},
                    {"label": "对 A 点（或 B 点）应用合力矩定理求得总作用点位于 A 点下方 0.928 m（距 B 点 1.072 m）", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2019-07",
                "year": 2019,
                "no": 7,
                "type": "calc",
                "score": 15,
                "title": "带收缩喷嘴有压管路流量及各高程特征点动水相对压强计算",
                "stem": "如图所示的管路流动系统中，管径 $d = 150\\,\\mathrm{mm}$，出口喷嘴直径 $d_1 = 50\\,\\mathrm{mm}$。求 $A$、$B$、$C$、$D$ 各点的相对压强和通过管道的流量，不计水头损失。",
                "note": "",
                "figures": [
                    {"src": "figures/q07_orig.png", "caption": "题 7 图　高低起伏有压管路与末端收缩喷嘴出流系统"}
                ],
                "shortAnswer": "流量 Q = 0.0174 m³/s（17.39 L/s）；各点相对压强：pA = 68.12 kPa，pB = -0.484 kPa（-484 Pa），pC = -20.08 kPa，pD = 38.72 kPa（若取 g=9.81 m/s² 则分别为 68.19、-0.484、-20.10、38.76 kPa）。",
                "judgeAnswer": None,
                "answer": "- 通过管道的流量：$Q = 0.0174\\,\\mathrm{m^3/s}$（即 $17.39\\,\\mathrm{L/s}$）；\n- 各点相对压强（取 $g = 9.80\\,\\mathrm{m/s^2}$）：\n  - $p_A = 68.12\\,\\mathrm{kPa}$（若取 $g = 9.81\\,\\mathrm{m/s^2}$ 则为 $68.19\\,\\mathrm{kPa}$）；\n  - $p_B = -0.484\\,\\mathrm{kPa} = -484\\,\\mathrm{Pa}$；\n  - $p_C = -20.08\\,\\mathrm{kPa}$（若取 $g = 9.81\\,\\mathrm{m/s^2}$ 则为 $-20.10\\,\\mathrm{kPa}$）；\n  - $p_D = 38.72\\,\\mathrm{kPa}$（若取 $g = 9.81\\,\\mathrm{m/s^2}$ 则为 $38.76\\,\\mathrm{kPa}$）。",
                "analysis": "**1. 列水箱液面至喷嘴出口伯努利方程求喷嘴流速 $v_1$ 与流量 $Q$**\n\n以出口喷嘴（及 $D$ 点所在水平管段）中心线为基准面（$z_D = z_{\\text{出}} = 0$），则水箱自由液面 $0\\text{—}0$ 高程 $z_0 = 4.0\\,\\mathrm{m}$（$B$ 点高程 $z_B = 4.0\\,\\mathrm{m}$，$C$ 点高程 $z_C = 4.0 + 2.0 = 6.0\\,\\mathrm{m}$，$A$ 点高程 $z_A = -3.0\\,\\mathrm{m}$）。\n\n不计水头损失（$h_w = 0$，取动能修正系数 $\\alpha = 1.0$），对上游大水箱自由液面 $0\\text{—}0$（$p_0 = 0$，$v_0 \\approx 0$）与喷嘴出口大气射流断面 $1\\text{—}1$（$z_1 = 0$，$p_1 = 0$）列理想液体伯努利方程：\n\n$$\nz_0 + 0 + 0 = 0 + 0 + \\frac{v_1^2}{2g} \\implies \\frac{v_1^2}{2g} = 4.0\\,\\mathrm{m}\n$$\n\n解得喷嘴出口流速与管道体积流量（取 $g = 9.80\\,\\mathrm{m/s^2}$）：\n\n$$\nv_1 = \\sqrt{2 g \\times 4.0} = \\sqrt{2 \\times 9.80 \\times 4.0} = \\sqrt{78.40} \\approx 8.8544\\,\\mathrm{m/s}\n$$\n\n$$\nQ = \\frac{\\pi}{4} d_1^2 v_1 = \\frac{\\pi}{4} \\times 0.05^2 \\times 8.8544 \\approx 0.017386\\,\\mathrm{m^3/s} \\approx 0.0174\\,\\mathrm{m^3/s} = 17.39\\,\\mathrm{L/s}\n$$\n\n**2. 求内径 $d = 150\\,\\mathrm{mm}$ 主管道内的流速水头与 $A$、$B$、$C$、$D$ 各点相对压强**\n\n$A$、$B$、$C$、$D$ 四点均位于直径 $d = 150\\,\\mathrm{mm}$ 的主管道内。由连续性方程 $v d^2 = v_1 d_1^2$ 得主管平均流速及主管流速水头：\n\n$$\nv = v_1 \\left(\\frac{d_1}{d}\\right)^2 = \\frac{v_1}{9} \\approx 0.9838\\,\\mathrm{m/s}, \\qquad \\frac{v^2}{2g} = \\frac{1}{81}\\frac{v_1^2}{2g} = \\frac{4.0}{81}\\,\\mathrm{m} \\approx 0.04938\\,\\mathrm{m}\n$$\n\n对应的主管动压头为 $\\frac{1}{2}\\rho v^2 = \\rho g \\frac{v^2}{2g} = 1000 \\times 9.80 \\times \\frac{4}{81} \\approx 483.95\\,\\mathrm{Pa} \\approx 0.484\\,\\mathrm{kPa}$。\n\n对水箱液面 $0\\text{—}0$ 与主管内任一点 $i \\in \\{A, B, C, D\\}$ 列伯努利方程：\n\n$$\nz_0 = z_i + \\frac{p_i}{\\rho g} + \\frac{v^2}{2g} \\implies p_i = \\rho g \\left(z_0 - z_i - \\frac{v^2}{2g}\\right)\n$$\n\n逐点代入相对液面淹没高差 $(z_0 - z_i)$ 计算（取 $\\rho = 1000\\,\\mathrm{kg/m^3}$，$g = 9.80\\,\\mathrm{m/s^2}$）：\n1. **$A$ 点**（位于液面下 $z_0 - z_A = 4 + 3 = 7.0\\,\\mathrm{m}$）：\n   $$\n   p_A = 9800 \\times \\left(7.0 - \\frac{4}{81}\\right) = 68600 - 483.95 = 68116\\,\\mathrm{Pa} \\approx 68.12\\,\\mathrm{kPa}\n   $$\n2. **$B$ 点**（与液面同高程，$z_0 - z_B = 0$）：\n   $$\n   p_B = 9800 \\times \\left(0 - \\frac{4}{81}\\right) = -483.95\\,\\mathrm{Pa} \\approx -0.484\\,\\mathrm{kPa}\n   $$\n3. **$C$ 点**（高出液面 $2.0\\,\\mathrm{m}$，$z_0 - z_C = -2.0\\,\\mathrm{m}$）：\n   $$\n   p_C = 9800 \\times \\left(-2.0 - \\frac{4}{81}\\right) = -19600 - 483.95 = -20084\\,\\mathrm{Pa} \\approx -20.08\\,\\mathrm{kPa}\n   $$\n4. **$D$ 点**（位于液面下 $z_0 - z_D = 4.0\\,\\mathrm{m}$ 的喷嘴前主管内）：\n   $$\n   p_D = 9800 \\times \\left(4.0 - \\frac{4}{81}\\right) = 39200 - 483.95 = 38716\\,\\mathrm{Pa} \\approx 38.72\\,\\mathrm{kPa}\n   $$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $Q = 0.0174\\,\\mathrm{m^3/s}$，$p_A = 68.19\\,\\mathrm{kPa}$，$p_B = -0.484\\,\\mathrm{kPa}$，$p_C = -20.10\\,\\mathrm{kPa}$，$p_D = 38.76\\,\\mathrm{kPa}$；若因 $\\frac{v^2}{2g} \\approx 0.049\\,\\mathrm{m}$ 较小而忽略主管流速水头作工程近似，则四点压强分别近似为 $68.60$、$0$、$-19.60$、$39.20\\,\\mathrm{kPa}$，但严格伯努利方程必须扣除主管动压 $\\frac{1}{2}\\rho v^2 \\approx 0.484\\,\\mathrm{kPa}$！）",
                "analysisFigures": [],
                "pitfalls": "本题头号陷阱是把流动管道误当作静止连通器来算各点压强（误写出 $p_B = 0$、$p_D = 4\\rho g$）！喷嘴正在向外射流，直径 $150\\,\\mathrm{mm}$ 的管道内有流速 $v = v_1/9 \\approx 0.984\\,\\mathrm{m/s}$，因此与液面同高的 $B$ 点相对压强并非为零，而是存在微弱负压 $p_B = -\\frac{1}{2}\\rho v^2 \\approx -484\\,\\mathrm{Pa}$；同样 $D$ 点位于喷嘴收缩前的主管内（尚未收缩到大气射流），故 $p_D = \\rho g(4 - v^2/2g) \\approx 38.72\\,\\mathrm{kPa} > 0$！",
                "chapter": 3,
                "kps": ["伯努利方程测流", "恒定总流连续性方程", "管内动水压强与负压"],
                "method": "伯努利方程求喷嘴流量与逐点动水压强法",
                "difficulty": 3,
                "rubric": [
                    {"label": "对水箱液面与喷嘴出口列伯努利方程求出喷嘴流速 v1 ≈ 8.85 m/s 及流量 Q ≈ 0.0174 m³/s", "pts": 5},
                    {"label": "由连续性方程求出 d=150 mm 主管流速 v = v1/9 ≈ 0.984 m/s 及流速水头 v²/(2g) ≈ 0.0494 m", "pts": 2},
                    {"label": "应用伯努利方程准确算出 A、B、C、D 四点的相对压强（每点 2 分）", "pts": 8}
                ]
            },
            {
                "id": "yzu-849-2019-08",
                "year": 2019,
                "no": 8,
                "type": "calc",
                "score": 12,
                "title": "水平收缩 180° 弯管连接螺栓所受总拉力计算",
                "stem": "如图所示，水流稳定地通过一收缩弯管，已知 $p_1 = 300\\,\\mathrm{kPa}$，$d_1 = 300\\,\\mathrm{mm}$，$v_1 = 2\\,\\mathrm{m/s}$，$d_2 = 100\\,\\mathrm{mm}$，试求螺栓所承受的力。管轴线均位于同一水平面内，不计水头损失。",
                "note": "",
                "figures": [
                    {"src": "figures/q08_orig.png", "caption": "题 8 图　水平面内 180° 收缩弯管及法兰连接螺栓"}
                ],
                "shortAnswer": "25.13 kN（8000π N；若 π 取 3.14 则为 25.12 kN），水流推弯管向右，故两组法兰螺栓承受的总水平拉力为 25.13 kN（螺栓受拉，对弯管施以水平向左的约束拉力）。",
                "judgeAnswer": None,
                "answer": "水流对收缩弯管的水平推力（即断面 ①、② 连接螺栓共同承受的总水平拉力）大小为 **$25.13\\,\\mathrm{kN}$**（精确值 $8000\\pi\\,\\mathrm{N}$；若 $\\pi$ 取 $3.14$ 则为 $25.12\\,\\mathrm{kN}$），螺栓承受水平轴向拉力（弯管对螺栓的推力方向水平向右，螺栓对弯管的约束力方向水平向左）。",
                "analysis": "**1. 由连续性方程与伯努利方程求断面 ② 的流速 $v_2$ 和相对压强 $p_2$**\n\n进口断面 ① 直径 $d_1 = 0.30\\,\\mathrm{m}$，出口法兰断面 ② 直径 $d_2 = 0.10\\,\\mathrm{m}$，过水断面面积与流量分别为：\n\n$$\nA_1 = \\frac{\\pi}{4}d_1^2 = 0.0225\\pi \\approx 0.070686\\,\\mathrm{m^2}, \\qquad A_2 = \\frac{\\pi}{4}d_2^2 = 0.0025\\pi \\approx 0.007854\\,\\mathrm{m^2}\n$$\n\n$$\nQ = A_1 v_1 = 0.0225\\pi \\times 2 = 0.045\\pi \\approx 0.14137\\,\\mathrm{m^3/s}\n$$\n\n$$\nv_2 = \\frac{Q}{A_2} = v_1 \\left(\\frac{d_1}{d_2}\\right)^2 = 2 \\times \\left(\\frac{300}{100}\\right)^2 = 18\\,\\mathrm{m/s}\n$$\n\n因弯管位于同一水平面内（$z_1 = z_2$）且不计水头损失（$h_w = 0$，取 $\\alpha_1 = \\alpha_2 = 1.0$，$\\rho = 1000\\,\\mathrm{kg/m^3}$），对 ①、② 两断面列伯努利方程：\n\n$$\np_1 + \\frac{1}{2}\\rho v_1^2 = p_2 + \\frac{1}{2}\\rho v_2^2\n$$\n\n$$\np_2 = p_1 - \\frac{1}{2}\\rho \\left(v_2^2 - v_1^2\\right) = 300 \\times 10^3 - \\frac{1}{2} \\times 1000 \\times (18^2 - 2^2) = 300 \\times 10^3 - 160 \\times 10^3 = 140 \\times 10^3\\,\\mathrm{Pa} = 140\\,\\mathrm{kPa}\n$$\n\n**2. 取弯管内水体为控制体列水平动量方程求螺栓受力（见解图 8）**\n\n选取法兰断面 ① 与断面 ② 之间的弯管水体为控制体，取水平向右为 $x$ 轴正方向（即进口流速 $\\vec{v}_1$ 方向）：\n- 断面 ①、② 上的动水总压力均指向控制体内部，即**方向均水平向右（$+x$ 向）**：\n\n$$\nP_1 = p_1 A_1 = 300\\times 10^3 \\times 0.0225\\pi = 6750\\pi \\approx 21205.75\\,\\mathrm{N} \\approx 21.21\\,\\mathrm{kN}\n$$\n\n$$\nP_2 = p_2 A_2 = 140\\times 10^3 \\times 0.0025\\pi = 350\\pi \\approx 1099.56\\,\\mathrm{N} \\approx 1.10\\,\\mathrm{kN}\n$$\n\n- 进口流速投影 $v_{1x} = +v_1 = +2\\,\\mathrm{m/s}$，经 $180^{\\circ}$ 回转后出口流速水平向左，投影 $v_{2x} = -v_2 = -18\\,\\mathrm{m/s}$。\n- 设弯管内壁（经由法兰连接螺栓传递）对水体的水平反作用力为 $R_x$（假设方向水平向左，即 $-x$ 向），取动量修正系数 $\\beta_1 = \\beta_2 = 1.0$，列 $x$ 向动量方程：\n\n$$\nP_1 + P_2 - R_x = \\rho Q (v_{2x} - v_{1x}) = \\rho Q (-v_2 - v_1)\n$$\n\n解得：\n\n$$\nR_x = P_1 + P_2 + \\rho Q (v_1 + v_2) = 6750\\pi + 350\\pi + 1000 \\times 0.045\\pi \\times (2 + 18)\n$$\n\n$$\nR_x = (6750 + 350 + 900)\\pi = 8000\\pi\\,\\mathrm{N} \\approx 25132.74\\,\\mathrm{N} \\approx 25.13\\,\\mathrm{kN}\n$$\n\n（在 $y$ 方向上，进出流均无 $y$ 向速度分量且断面正交于 $x$ 轴，故 $R_y = 0$。）\n\n由牛顿第三定律，水流对弯管产生**水平向右、大小为 $25.13\\,\\mathrm{kN}$** 的总推力；忽略弯管自重摩擦支撑时，断面 ① 和 ② 处的法兰连接螺栓共同承受大小为 **$25.13\\,\\mathrm{kN}$** 的水平拉力（螺栓对弯管施以水平向左的约束拉力 $25.13\\,\\mathrm{kN}$）。",
                "analysisFigures": [
                    {"src": "figures/q08_sol.png", "caption": "解图 8　水平 180° 收缩弯管控制体水平受力与动量通量图"}
                ],
                "pitfalls": "1. 断面 ② 带有连接法兰与下游直管相连，并非直接通大气自由出流，故 $p_2 \\neq 0$，必须先由伯努利方程算出 $p_2 = 140\\,\\mathrm{kPa}$！\n2. $180^{\\circ}$ 弯管有两处极易出错的符号：一是断面 ② 外侧水体对控制体的压力 $P_2$ 指向控制体内部，故**向右为 $+P_2$**（与 $P_1$ 同向叠加）；二是出口流速向左，$v_{2x} = -18\\,\\mathrm{m/s}$，故动量变化项为 $\\rho Q(-v_2 - v_1)$，移项后变为 $+\\rho Q(v_1 + v_2)$，切勿写成 $v_2 - v_1$！",
                "chapter": 3,
                "kps": ["闸门与弯管动水总压力", "恒定总流动量方程", "实际液体恒定总流能量方程"],
                "method": "能量方程求压强+控制体动量方程求反力",
                "difficulty": 3,
                "rubric": [
                    {"label": "由连续性方程与伯努利方程求出出口流速 v2 = 18 m/s 及断面 ② 相对压强 p2 = 140 kPa", "pts": 4},
                    {"label": "正确计算两断面压力 P1 ≈ 21.21 kN、P2 ≈ 1.10 kN（均向右）及流量 Q ≈ 0.1414 m³/s", "pts": 4},
                    {"label": "列出 180° 弯管 x 向动量方程 P1 + P2 - Rx = ρQ(-v2 - v1)，解得螺栓承受总拉力 25.13 kN", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2019-09",
                "year": 2019,
                "no": 9,
                "type": "calc",
                "score": 20,
                "title": "跨坝虹吸管输水流量与坝顶最大允许吸水高度计算",
                "stem": "如图所示虹吸管总长 $l = 21\\,\\mathrm{m}$，坝顶 $A$ 点前管长 $\\Delta l = 8\\,\\mathrm{m}$，管内径 $d = 0.25\\,\\mathrm{m}$，坝顶管道中心与上游水面的高度差 $h_1 = 3.5\\,\\mathrm{m}$，二水面落差 $h_2 = 4\\,\\mathrm{m}$。设沿程阻力系数 $\\lambda = 0.03$。虹吸管进口局部阻力系数 $\\zeta_1 = 0.8$，出口局部阻力系数 $\\zeta_2 = 1$，三个 $45^{\\circ}$ 折管的局部阻力系数均为 $0.3$，试求虹吸管的吸水流量 $Q$。若当地大气压强 $p_a = 10^5\\,\\mathrm{Pa}$，水温 $t = 20^{\\circ}\\mathrm{C}$，所对应的水的密度 $\\rho = 998\\,\\mathrm{kg/m^3}$，最大允许真空压强 $p_v = 2.42 \\times 10^3\\,\\mathrm{Pa}$，试求最大吸水高度。",
                "note": "注：题干中 $t = 20^{\\circ}\\mathrm{C}$ 下给定的 $p_v = 2.42 \\times 10^3\\,\\mathrm{Pa}$ 物理实质为该水温下水的饱和蒸汽压（汽化绝对压强），故管顶允许最大真空压强为 $p_{v,\\max} = p_a - p_v$。",
                "figures": [
                    {"src": "figures/q09_orig.png", "caption": "题 9 图　跨坝虹吸管布置与上下游水位关系图"}
                ],
                "shortAnswer": "虹吸管吸水流量 Q = 0.190 m³/s；最大吸水高度 h1,max = 7.63 m（若取 g = 9.81 m/s² 则为 7.62 m）。",
                "judgeAnswer": None,
                "answer": "（1）虹吸管的吸水流量 $Q \\approx 0.190\\,\\mathrm{m^3/s}$；\n\n（2）在维持该输水流量不变的条件下，虹吸管的最大允许吸水高度 $h_{1,\\max} \\approx 7.63\\,\\mathrm{m}$（若取 $g = 9.81\\,\\mathrm{m/s^2}$ 则为 $7.62\\,\\mathrm{m}$）。",
                "analysis": "**1. 求虹吸管的吸水流量 $Q$**\n\n以下游水池自由液面 $2\\text{—}2$ 为基准面，对上游渠道自由液面 $1\\text{—}1$（$z_1 = h_2 = 4\\,\\mathrm{m}$，$p_1 = 0$，$v_0 \\approx 0$）与下游水池自由液面 $2\\text{—}2$（$z_2 = 0$，$p_2 = 0$，$v_{\\text{池}} \\approx 0$）列恒定总流能量方程（注意虹吸管淹没出流的出口局部阻力系数 $\\zeta_2 = 1.0$ 已包含出口断面流速水头耗散）：\n\n$$\nh_2 = \\left(\\lambda \\frac{l}{d} + \\zeta_1 + 3\\zeta_{\\text{折}} + \\zeta_2\\right)\\frac{v^2}{2g}\n$$\n\n计算全管系统总阻力系数：\n\n$$\n\\Sigma K = 0.03 \\times \\frac{21}{0.25} + 0.8 + 3 \\times 0.3 + 1.0 = 2.52 + 0.8 + 0.9 + 1.0 = 5.22\n$$\n\n由此求得管内流速水头、平均流速与流量（取 $g = 9.80\\,\\mathrm{m/s^2}$）：\n\n$$\n\\frac{v^2}{2g} = \\frac{h_2}{5.22} = \\frac{4.0}{5.22} \\approx 0.76628\\,\\mathrm{m}\n$$\n\n$$\nv = \\sqrt{2 g \\times 0.76628} = \\sqrt{2 \\times 9.80 \\times 0.76628} \\approx 3.8755\\,\\mathrm{m/s}\n$$\n\n$$\nQ = \\frac{\\pi}{4} d^2 v = \\frac{\\pi}{4} \\times 0.25^2 \\times 3.8755 = 0.049087 \\times 3.8755 \\approx 0.1902\\,\\mathrm{m^3/s} \\approx 0.190\\,\\mathrm{m^3/s}\n$$\n\n（校核设计工况：$h_1 = 3.5\\,\\mathrm{m}$ 时坝顶真空水头仅约 $3.5 + 2.345 = 5.845\\,\\mathrm{m}$，未发生汽化断流，流量有效。）\n\n**2. 求坝顶不发生汽化时的最大允许吸水高度 $h_{1,\\max}$（见解图 9）**\n\n- **物理参数辨析**：$t = 20^{\\circ}\\mathrm{C}$ 时水的汽化压强（绝对压强）为 $p_v = 2.42 \\times 10^3\\,\\mathrm{Pa}$，当地大气压 $p_a = 10^5\\,\\mathrm{Pa}$，对应水密度 $\\rho = 998\\,\\mathrm{kg/m^3}$，因此虹吸管最高点断面 $A$ 不发生空化汽化的最大允许真空高度为：\n\n$$\nh_{v,\\max} = \\frac{p_a - p_v}{\\rho g} = \\frac{10^5 - 2.42 \\times 10^3}{998 \\times 9.80} = \\frac{97580}{9780.4} \\approx 9.9771\\,\\mathrm{m}\n$$\n\n- **确定 $A$ 点前局部阻力个数**：观察题 9 图，虹吸管共有三处 $45^{\\circ}$ 折管（左坡顶进入水平坝顶 1 个、坝顶 $A$ 点转入右斜坡 1 个、右坡脚转水平出口 1 个），在坝顶 $A$ 点断面之前（管长 $\\Delta l = 8\\,\\mathrm{m}$）包含 **1 个进口（$\\zeta_1 = 0.8$）和 1 个 $45^{\\circ}$ 折管（$\\zeta_{\\text{折}} = 0.3$）**。\n- 以模块上游水面为基准面，对上游水面 $1\\text{—}1$ 与坝顶 $A$ 点前断面列能量方程（取 $\\alpha_A = 1.0$）：\n\n$$\n0 = h_{1,\\max} - h_{v,\\max} + \\frac{v^2}{2g} + \\left(\\lambda \\frac{\\Delta l}{d} + \\zeta_1 + \\zeta_{\\text{折}}\\right)\\frac{v^2}{2g}\n$$\n\n其中 $A$ 点速度水头与前段水头损失之和为：\n\n$$\n\\left(1 + \\lambda \\frac{\\Delta l}{d} + \\zeta_1 + \\zeta_{\\text{折}}\\right)\\frac{v^2}{2g} = \\left(1 + 0.03 \\times \\frac{8}{0.25} + 0.8 + 0.3\\right) \\times \\frac{4.0}{5.22} = 3.06 \\times 0.76628 \\approx 2.3448\\,\\mathrm{m}\n$$\n\n解得最大允许吸水高度：\n\n$$\nh_{1,\\max} = h_{v,\\max} - 2.3448 = 9.9771 - 2.3448 = 7.6323\\,\\mathrm{m} \\approx 7.63\\,\\mathrm{m}\n$$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $Q = 0.1903\\,\\mathrm{m^3/s}$，$h_{v,\\max} = 9.9669\\,\\mathrm{m}$，$h_{1,\\max} = 7.6221\\,\\mathrm{m} \\approx 7.62\\,\\mathrm{m}$；若将 $A$ 点处的第 2 个 $45^{\\circ}$ 折管也计入 $A$ 点断面之前，则再多扣 $0.3 \\times 0.7663 = 0.23\\,\\mathrm{m}$，得 $h_{1,\\max} \\approx 7.40\\,\\mathrm{m}$。）",
                "analysisFigures": [
                    {"src": "figures/q09_sol.png", "caption": "解图 9　跨坝虹吸管总水头线、测压管水头线与坝顶 A 点真空高度关系"}
                ],
                "pitfalls": "1. 淹没出流列上下游两水池水面能量方程时，既然已计入出口局部损失系数 $\\zeta_2 = 1.0$，等式右边就**不能**再重复加上管道出口动能 $\\frac{v^2}{2g}$（否则会把出口水头损失算成两遍）！而列上游水面到管内 $A$ 断面的能量方程时，$A$ 断面还在管内流动，**必须**保留 $A$ 断面的动能水头 $\\frac{v^2}{2g}$！\n2. 认清 $20^{\\circ}\\mathrm{C}$ 时 $2.42 \\times 10^3\\,\\mathrm{Pa}$ 是水的饱和汽化**绝对**压强，对应的允许真空压强应为 $p_a - p_v = 97.58\\,\\mathrm{kPa}$（约 $9.98\\,\\mathrm{m}$ 水柱）。",
                "chapter": 6,
                "kps": ["虹吸管水力计算", "简单短管流量计算", "最大允许吸水高度与空化"],
                "method": "简单短管能量方程测流与允许真空度校核",
                "difficulty": 4,
                "rubric": [
                    {"label": "列出上下游水面恒定总流能量方程，准确计入沿程损失与进口、3个折管、淹没出口局部损失（ΣK = 5.22）", "pts": 5},
                    {"label": "求出管内流速 v ≈ 3.88 m/s 及虹吸管吸水流量 Q ≈ 0.190 m³/s", "pts": 5},
                    {"label": "由大气压 pa 与汽化压强 pv 求得最大允许真空水头 hv,max = (pa - pv)/(ρg) ≈ 9.98 m", "pts": 5},
                    {"label": "列上游水面至坝顶 A 断面能量方程，扣除流速水头与前段损失（2.345 m）解得 h1,max ≈ 7.63 m", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2019-10",
                "year": 2019,
                "no": 10,
                "type": "proof",
                "score": 15,
                "title": "文丘里流量计理论流量与实际流量计算公式推导",
                "stem": "如图所示为文丘里流量计，已知被测管道直径为 $d_1$，喉管管径为 $d_2$，两测压管液面高度差为 $h$。试运用能量方程推导水管中流量的理论公式，并据此写出实际流量的计算公式。",
                "note": "",
                "figures": [
                    {"src": "figures/q10_orig.png", "caption": "题 10 图　水平文丘里流量计结构与测压管水头差"}
                ],
                "shortAnswer": "理论流量 Q理 = (π d1² d2² / [4√(d1⁴ - d2⁴)]) √(2gh)；实际流量 Q = μ Q理 = μ (π d1² d2² / [4√(d1⁴ - d2⁴)]) √(2gh)（μ 为文丘里流量计流量系数）。",
                "judgeAnswer": None,
                "answer": "**（1）水管中流量的理论公式**：\n\n$$\nQ_{\\text{理}} = \\frac{\\pi d_2^2}{4\\sqrt{1 - \\left(\\dfrac{d_2}{d_1}\\right)^4}}\\sqrt{2gh} = \\frac{\\pi d_1^2 d_2^2}{4\\sqrt{d_1^4 - d_2^4}}\\sqrt{2gh}\n$$\n\n**（2）实际流量的计算公式**（引入流量修正系数 $\\mu$，一般 $\\mu = 0.95 \\sim 0.98$）：\n\n$$\nQ = \\mu Q_{\\text{理}} = \\mu \\frac{\\pi d_1^2 d_2^2}{4\\sqrt{d_1^4 - d_2^4}}\\sqrt{2gh}\n$$",
                "analysis": "**1. 列喉管前管道断面 $1\\text{—}1$ 与喉管断面 $2\\text{—}2$ 的理想液体能量方程**\n\n推导理论流量时，假定流体为理想不可压缩液体（忽略 $1\\text{—}1$ 至 $2\\text{—}2$ 极短收缩段的水头损失 $h_{w1\\text{-}2} = 0$），并取动能修正系数 $\\alpha_1 = \\alpha_2 = 1.0$。对渐变流断面 $1\\text{—}1$ 与喉管断面 $2\\text{—}2$ 列伯努利方程：\n\n$$\nz_1 + \\frac{p_1}{\\rho g} + \\frac{v_1^2}{2g} = z_2 + \\frac{p_2}{\\rho g} + \\frac{v_2^2}{2g}\n$$\n\n由静水力学测压管水头的几何意义，两根开口测压管的液面高程分别为 $H_{p1} = z_1 + \\frac{p_1}{\\rho g}$ 和 $H_{p2} = z_2 + \\frac{p_2}{\\rho g}$（如图中以水平管轴为基准面时，$z_1 = z_2 = 0$，$h_1 = \\frac{p_1}{\\rho g}$，$h_2 = \\frac{p_2}{\\rho g}$），故两测压管液面高度差为：\n\n$$\nh = \\left(z_1 + \\frac{p_1}{\\rho g}\\right) - \\left(z_2 + \\frac{p_2}{\\rho g}\\right) = \\frac{v_2^2 - v_1^2}{2g}\n$$\n\n（注：此关系表明即使文丘里管倾斜或铅直安装，测压管液面差 $h$ 依然严格等于 $\\frac{v_2^2 - v_1^2}{2g}$！）\n\n**2. 联立连续性方程消元推导理论流量 $Q_{\\text{理}}$**\n\n两圆管过水断面面积分别为 $A_1 = \\frac{\\pi}{4}d_1^2$、$A_2 = \\frac{\\pi}{4}d_2^2$。由不可压缩恒定总流连续性方程：\n\n$$\nQ_{\\text{理}} = A_1 v_1 = A_2 v_2 \\implies v_1 = \\frac{A_2}{A_1} v_2 = \\left(\\frac{d_2}{d_1}\\right)^2 v_2\n$$\n\n代入水头差关系式：\n\n$$\nh = \\frac{v_2^2}{2g}\\left[1 - \\left(\\frac{d_2}{d_1}\\right)^4\\right] \\implies v_2 = \\frac{\\sqrt{2gh}}{\\sqrt{1 - \\left(\\dfrac{d_2}{d_1}\\right)^4}} = \\frac{d_1^2}{\\sqrt{d_1^4 - d_2^4}}\\sqrt{2gh}\n$$\n\n故水管中的**理论体积流量公式**为：\n\n$$\nQ_{\\text{理}} = A_2 v_2 = \\frac{\\pi d_2^2}{4\\sqrt{1 - \\left(\\dfrac{d_2}{d_1}\\right)^4}}\\sqrt{2gh} = \\frac{\\pi d_1^2 d_2^2}{4\\sqrt{d_1^4 - d_2^4}}\\sqrt{2gh}\n$$\n\n**3. 修正黏性水头损失与流速不均写出实际流量公式**\n\n实际黏性水流通过收缩段时存在微小的水头损失 $h_{w1\\text{-}2} > 0$，且断面动能修正系数 $\\alpha \\neq 1.0$，使得相同压差读数 $h$ 下的实际流量略小于理论流量。工程上引入无量纲**流量系数 $\\mu$**（$0 < \\mu < 1$，文丘里流量计通常由实验率定为 $\\mu = 0.95 \\sim 0.98$）加以综合修正，得到**实际流量计算公式**：\n\n$$\nQ = \\mu Q_{\\text{理}} = \\mu \\frac{\\pi d_1^2 d_2^2}{4\\sqrt{d_1^4 - d_2^4}}\\sqrt{2gh}\n$$\n\n若令文丘里常数 $K_V = \\mu \\frac{\\pi d_1^2 d_2^2}{4\\sqrt{d_1^4 - d_2^4}}\\sqrt{2g}$，则对于给定流量计几何尺寸，可简写为实用测流式 $Q = K_V \\sqrt{h}$。",
                "analysisFigures": [],
                "pitfalls": "1. 由面积比 $\\frac{A_2}{A_1} = \\left(\\frac{d_2}{d_1}\\right)^2$ 代入平方差 $v_2^2 - v_1^2$ 时，直径比变成**四次方** $\\left(\\frac{d_2}{d_1}\\right)^4$（即根号下为 $d_1^4 - d_2^4$），切勿漏平方写成 $d_1^2 - d_2^2$！\n2. 题目明确要求“推导理论公式，并据此写出实际流量计算公式”两问，切勿遗漏乘以流量系数 $\\mu$（$\\mu < 1$）的实际流量公式及对 $\\mu$ 物理含义的说明。",
                "chapter": 3,
                "kps": ["文丘里流量计", "伯努利方程测流", "恒定总流连续性方程"],
                "method": "能量方程与连续性方程联立测流推导法",
                "difficulty": 2,
                "rubric": [
                    {"label": "对 1—1、2—2 两断面列理想液体伯努利方程，结合测压管几何关系得出 h = (v2² - v1²)/(2g)", "pts": 5},
                    {"label": "联立连续性方程 A1·v1 = A2·v2 消元解出喉管流速并推得理论流量公式 Q理", "pts": 6},
                    {"label": "考虑实际流体水头损失与流速分布不均影响，引入流量系数 μ（0 < μ < 1）写出实际流量公式 Q = μ·Q理", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2019-11",
                "year": 2019,
                "no": 11,
                "type": "calc",
                "score": 12,
                "title": "梯形断面明渠均匀流断面平均流速与糙率计算",
                "stem": "一梯形渠道，按均匀流设计。已知 $Q$ 为 $23\\,\\mathrm{m^3/s}$，$h$ 为 $1.5\\,\\mathrm{m}$，$b$ 为 $10\\,\\mathrm{m}$，$m$ 为 $1.5$ 及 $i$ 为 $0.0005$，求 $n$ 和 $v$。",
                "note": "",
                "figures": [],
                "shortAnswer": "断面平均流速 v = 1.25 m/s；渠道粗糙系数（糙率）n = 0.020（精确值 0.0201）。",
                "judgeAnswer": None,
                "answer": "渠道断面平均流速 $v \\approx 1.25\\,\\mathrm{m/s}$（$1.252\\,\\mathrm{m/s}$），粗糙系数（曼宁糙率）$n \\approx 0.020$（$0.0201$）。",
                "analysis": "**1. 计算梯形过水断面几何与水力要素（见解图 11）**\n\n已知梯形渠道底宽 $b = 10\\,\\mathrm{m}$，均匀流水深 $h = 1.5\\,\\mathrm{m}$，边坡系数 $m = 1.5$：\n- 过水断面面积 $A$：\n\n$$\nA = (b + m h) h = (10 + 1.5 \\times 1.5) \\times 1.5 = 12.25 \\times 1.5 = 18.375\\,\\mathrm{m^2}\n$$\n\n- 湿周 $\\chi$：\n\n$$\n\\chi = b + 2 h \\sqrt{1 + m^2} = 10 + 2 \\times 1.5 \\times \\sqrt{1 + 1.5^2} = 10 + 3\\sqrt{3.25} \\approx 10 + 5.4083 = 15.4083\\,\\mathrm{m}\n$$\n\n- 水力半径 $R$：\n\n$$\nR = \\frac{A}{\\chi} = \\frac{18.375}{15.4083} \\approx 1.1925\\,\\mathrm{m}\n$$\n\n**2. 求断面平均流速 $v$**\n\n由连续性方程 $Q = A v$ 得：\n\n$$\nv = \\frac{Q}{A} = \\frac{23}{18.375} \\approx 1.2517\\,\\mathrm{m/s} \\approx 1.25\\,\\mathrm{m/s}\n$$\n\n**3. 由谢才—曼宁公式反求渠道糙率 $n$**\n\n明渠均匀流时总水头坡度等于渠底坡度 $J = i = 0.0005$。应用谢才—曼宁公式：\n\n$$\nv = C\\sqrt{R i} = \\frac{1}{n} R^{2/3} i^{1/2}\n$$\n\n解得糙率 $n$：\n\n$$\nn = \\frac{R^{2/3} i^{1/2}}{v} = \\frac{1.1925^{2/3} \\times \\sqrt{0.0005}}{1.2517} = \\frac{1.12451 \\times 0.0223607}{1.25170} \\approx 0.02009 \\approx 0.020\n$$",
                "analysisFigures": [
                    {"src": "figures/q11_sol.png", "caption": "解图 11　梯形断面明渠均匀流水力要素示意图"}
                ],
                "pitfalls": "1. 计算梯形渠道湿周 $\\chi = b + 2h\\sqrt{1 + m^2}$ 时，只计渠底与两侧斜坡的接触长度，切勿误将自由水面宽度 $B = b + 2mh = 14.5\\,\\mathrm{m}$ 加进湿周！\n2. 曼宁公式中水力半径指数是 $R^{2/3}$（或 $C = \\frac{1}{n}R^{1/6}$ 再乘 $\\sqrt{R}$ 合成 $R^{2/3}$），切勿在代 $v = \\frac{1}{n}R^{2/3}i^{1/2}$ 时把指数误写为 $1/6$ 或 $1/2$。",
                "chapter": 7,
                "kps": ["梯形断面水力要素", "曼宁公式", "明渠均匀流计算"],
                "method": "谢才—曼宁公式明渠均匀流水力计算法",
                "difficulty": 2,
                "rubric": [
                    {"label": "正确算出梯形过水断面面积 A = 18.375 m²、湿周 χ ≈ 15.41 m 及水力半径 R ≈ 1.193 m", "pts": 4},
                    {"label": "由连续性方程求出断面平均流速 v = Q/A ≈ 1.25 m/s", "pts": 4},
                    {"label": "应用明渠均匀流曼宁公式 v = (1/n)R^(2/3)i^(1/2) 解得糙率 n ≈ 0.020", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2019-12",
                "year": 2019,
                "no": 12,
                "type": "calc",
                "score": 12,
                "title": "由平面流函数判别有势流动并积分求解速度势函数",
                "stem": "已知平面流动的流函数为 $\\psi = 3xy + 2x$，判断是否有势函数存在，若有，求势函数。",
                "note": "",
                "figures": [],
                "shortAnswer": "因 ∇²ψ = 0（旋转角速度 ωz = 0），流动为无旋流，存在速度势函数；φ(x, y) = (3/2)x² - (3/2)y² - 2y + C（C 为任意常数）。",
                "judgeAnswer": None,
                "answer": "该平面流动为无旋流动（$\\omega_z = 0$），**存在势函数**；对应的速度势函数为：\n\n$$\n\\varphi(x, y) = \\frac{3}{2}x^2 - \\frac{3}{2}y^2 - 2y + C \\quad (C\\text{ 为任意常数})\n$$",
                "analysis": "**1. 由流函数计算流速分量**\n\n采用标准水力学符号约定，平面不可压缩流动的流速分量 $(u_x, u_y)$ 与流函数 $\\psi(x, y)$ 的关系为：\n\n$$\nu_x = \\frac{\\partial \\psi}{\\partial y} = \\frac{\\partial (3xy + 2x)}{\\partial y} = 3x\n$$\n\n$$\nu_y = -\\frac{\\partial \\psi}{\\partial x} = -\\frac{\\partial (3xy + 2x)}{\\partial x} = -3y - 2\n$$\n\n**2. 检验无旋条件判断势函数是否存在**\n\n存在速度势函数 $\\varphi(x, y)$ 的充要条件是流场为**无旋流动**，即绕 $z$ 轴的旋转角速度 $\\omega_z = 0$（等价于流函数满足拉普拉斯方程 $\\nabla^2 \\psi = 0$）：\n\n$$\n\\omega_z = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} - \\frac{\\partial u_x}{\\partial y}\\right) = \\frac{1}{2}\\left[\\frac{\\partial (-3y - 2)}{\\partial x} - \\frac{\\partial (3x)}{\\partial y}\\right] = \\frac{1}{2}(0 - 0) = 0\n$$\n\n故该流动为无旋（有势）流动，**速度势函数 $\\varphi(x, y)$ 必然存在**。\n\n**3. 利用柯西—黎曼关系（或全微分线积分）求势函数 $\\varphi(x, y)$**\n\n由速度势定义 $\\frac{\\partial \\varphi}{\\partial x} = u_x = 3x$，$\\frac{\\partial \\varphi}{\\partial y} = u_y = -3y - 2$，写出 $\\varphi$ 的全微分：\n\n$$\n\\mathrm{d}\\varphi = u_x\\,\\mathrm{d}x + u_y\\,\\mathrm{d}y = 3x\\,\\mathrm{d}x - (3y + 2)\\,\\mathrm{d}y\n$$\n\n由于被积表达式中 $x$ 与 $y$ 已完全分离，直接积分得：\n\n$$\n\\varphi(x, y) = \\int 3x\\,\\mathrm{d}x - \\int (3y + 2)\\,\\mathrm{d}y = \\frac{3}{2}x^2 - \\frac{3}{2}y^2 - 2y + C\n$$\n\n其中 $C$ 为任意积分常数。（校核：$\\frac{\\partial \\varphi}{\\partial x} = 3x = u_x$，$\\frac{\\partial \\varphi}{\\partial y} = -3y - 2 = u_y$，且 $\\nabla^2 \\varphi = 3 - 3 = 0$，完全正确。注：若个别教材采用反号约定 $u_x = -\\frac{\\partial \\psi}{\\partial y},\\; u_y = \\frac{\\partial \\psi}{\\partial x}$，则势函数整体反号为 $\\varphi = -\\frac{3}{2}x^2 + \\frac{3}{2}y^2 + 2y + C$。）",
                "analysisFigures": [],
                "pitfalls": "1. 作答第一步务必明确写出自己采用的流函数定义式 $u_x = \\frac{\\partial \\psi}{\\partial y},\\; u_y = -\\frac{\\partial \\psi}{\\partial x}$，注意 $u_y$ 前的**负号**千万不能漏掉！\n2. 不定积分求势函数时切勿漏写任意常数 $+C$；若用偏导分步积分法（先对 $x$ 积分加待定函数 $f(y)$，再对 $y$ 求导比对），也可避免交叉项重复积分错误。",
                "chapter": 5,
                "kps": ["流函数与势函数", "无旋流判别条件", "柯西-黎曼条件"],
                "method": "流函数求流速判无旋与全微分积分求势法",
                "difficulty": 2,
                "rubric": [
                    {"label": "由流函数定义正确求出流速分量 ux = ∂ψ/∂y = 3x，uy = -∂ψ/∂x = -3y - 2", "pts": 4},
                    {"label": "计算旋转角速度 ωz = (∂uy/∂x - ∂ux/∂y)/2 = 0（或 ∇²ψ = 0），明确判定存在势函数", "pts": 4},
                    {"label": "对 dφ = ux·dx + uy·dy 积分求得势函数 φ = (3/2)x² - (3/2)y² - 2y + C", "pts": 4}
                ]
            }
        ]
    }


def build_2018_paper() -> dict:
    return {
        "year": 2018,
        "code": "849",
        "subject": "水力学（水）",
        "school": "扬州大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": True,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试（B 卷）。",
            "全卷共 13 道大题：第 1～5 题为概念辨析与机理分析简答题（5×10=50 分），第 6～13 题为综合计算与公式推导题（共 100 分）。",
            "除题干明确给定温度密度外，常温清水密度取 $\\rho = 1000\\,\\mathrm{kg/m^3}$，重力加速度取 $g = 9.80\\,\\mathrm{m/s^2}$（解析同步附 $g = 9.81\\,\\mathrm{m/s^2}$ 对照结果）。"
        ],
        "sections": [
            {
                "id": "short",
                "title": "一、机理分析与简答题",
                "description": "第 1～5 题，每题 10 分，共 50 分。",
                "range": [1, 5],
                "scorePerQuestion": 10,
                "totalScore": 50
            },
            {
                "id": "calc",
                "title": "二、计算与推导题",
                "description": "第 6～13 题（10+10+15+10+15+15+15+10 分），共 100 分。",
                "range": [6, 13],
                "totalScore": 100
            }
        ],
        "questions": [
            {
                "id": "yzu-849-2018-01",
                "year": 2018,
                "no": 1,
                "type": "short",
                "score": 10,
                "title": "从测压管水头角度阐述静水压强与动水压强的本质区别",
                "stem": "从测压管水头的角度，阐述静水压强与动水压强的不同之处。",
                "note": "",
                "figures": [],
                "shortAnswer": "静止均质连通液体中流速为零、无水头损失，测压管水头 z + p/(ρg) 等于总水头且在全流场处处为同一常数；运动液体中存在流速水头与水头损失，测压管水头等于总水头减去流速水头，随空间位置不同而变化（渐变流同一过水断面上为常数但沿程可升可降可不变，急变流同一断面上亦不相等）。",
                "judgeAnswer": None,
                "answer": "设单位重量液体的位置水头为 $z$、压强水头为 $\\frac{p}{\\rho g}$，两者之和 $H_p = z + \\frac{p}{\\rho g}$ 即为**测压管水头**。从测压管水头角度看，静水压强与动水压强的核心不同之处在于：\n\n1. **在静止液体（静水压强）中**：\n   - 流体无宏观运动，流速水头 $\\frac{u^2}{2g} = 0$，水头损失 $h_w = 0$，因此**测压管水头直接等于总水头**（$H_p = H$）；\n   - 在重力场同一种连续、均质静止液体内部，**空间各点的测压管水头处处相等（恒为同一常数）**：\n     $$\n     z + \\frac{p}{\\rho g} = C\n     $$\n     即静水压强大小仅取决于该点距自由液面的淹没深度，各点插入测压管后液面严格齐平于同一水平面。\n2. **在运动液体（动水压强）中**：\n   - 流体具有动能且伴随黏性摩擦耗能，由实际液体伯努利方程 $z + \\frac{p}{\\rho g} + \\frac{u^2}{2g} = H_0 - h_w$ 可知，**测压管水头等于当地总水头减去流速水头**：\n     $$\n     z + \\frac{p}{\\rho g} = H - \\frac{u^2}{2g} \\neq \\text{全局常数}\n     $$\n   - **沿流向变化多样性**：由于总水头 $H$ 沿程单调减小，但流速水头 $\\frac{u^2}{2g}$ 随过水断面收缩或扩大可增可减，故动水中的测压管水头线沿程**可以下降、可以水平不变、甚至可以在断面扩散减速段沿程上升**！\n   - **同一过水断面上的差异**：仅在流线近乎平行直线的**渐变流断面**上，动水测压管水头才在同一断面内保持常数（$z + \\frac{p}{\\rho g} = C_{\\text{断面}}$）；而在流线急剧弯曲的**急变流断面**上，受离心惯性力影响，同一过水断面不同点处的测压管水头也不相等（凹岸高、凸岸低）。",
                "analysis": "对比静水力学基本方程与恒定流元流伯努利方程，可将两者在测压管水头 $H_p = z + \\frac{p}{\\rho g}$ 维度下的区别归纳为三层：\n\n| 对比维度 | 静水压强（静止均质连通液体） | 动水压强（运动液体） |\n| :--- | :--- | :--- |\n| 与总水头关系 | $H_p = H$（无流速水头） | $H_p = H - \\dfrac{u^2}{2g} < H$ |\n| 沿流线 / 不同位置 | 全域恒定 $H_p = \\text{const}$（测压管水头线为水平直线） | 随流速变化与沿程摩阻而变，测压管水头线**可升、可降、可平** |\n| 同一过水断面内 | 任意方向恒有 $z + \\dfrac{p}{\\rho g} = \\text{const}$ | **渐变流**断面内为常数；**急变流**断面内因离心力 $z + \\dfrac{p}{\\rho g} \\neq \\text{const}$ |\n\n此外，动水压强因高速流动使 $\\frac{u^2}{2g}$ 大幅增大时，即使该点位置低于自由液面，测压管水头仍可能低于该点位置高程 $z$，从而产生静水中同位置绝不会出现的**动水负压（真空）现象**（如文丘里喉管、收缩断面等）。",
                "analysisFigures": [],
                "pitfalls": "切忌误答“动水压强的测压管水头沿程一定减小”！沿程必然单调减小的是**总水头线**；而测压管水头 $z + \\frac{p}{\\rho g}$ 在渐变扩散管段因部分动能转化为压能（$\\frac{v_1^2 - v_2^2}{2g} > h_w$），完全可以沿程升高！另外别漏掉急变流与渐变流在同一过水断面上测压管水头是否相等的区别。",
                "chapter": 3,
                "kps": ["测压管水头", "静水压强与动水压强对比", "渐变流与急变流性质"],
                "method": "测压管水头空间分布与能量转换对比法",
                "difficulty": 2,
                "rubric": [
                    {"label": "指出静水中不存在流速水头与水头损失，测压管水头 z+p/(ρg) 等于总水头且在连通静止液体内处处相等", "pts": 4},
                    {"label": "阐明动水中测压管水头等于总水头减流速水头，沿程可升可降可不变，且急变流同一断面上亦不相等", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2018-02",
                "year": 2018,
                "no": 2,
                "type": "short",
                "score": 10,
                "title": "恒水头水箱不同深度向上出流管出口流速与射流高度论证",
                "stem": "从水箱中分别引出三根直径相等的管子，其出口方向均向上，如图所示。当各管末端阀门单独开启，水流自各管出口向上射出时，试论证：\n\n（1）各管出口流速是否相等；\n\n（2）各管出口射流所到达的高度是否相等（不计水头损失）。",
                "note": "",
                "figures": [
                    {"src": "figures/q02_orig.png", "caption": "题 2 图　溢流恒水头水箱引出三根不同深度的向上出流管"}
                ],
                "shortAnswer": "（1）不相等，因 vi = √(2ghi) 且 h1 < h2 < h3，故 v1 < v2 < v3；（2）射流最高点所到达的高程（高度）相等，均恰好到达水箱溢流自由液面所在水平面（各射流相对自身管口上升的高度分别为 h1、h2、h3）。",
                "judgeAnswer": None,
                "answer": "**（1）各管出口流速不相等**（且满足 $v_1 < v_2 < v_3$）。\n- **论证**：水箱设有溢流口保持自由液面高程 $z_0$ 恒定。不计水头损失（$h_w = 0$，取 $\\alpha = 1.0$），当第 $i$ 根管（$i = 1, 2, 3$）阀门单独开启时，以第 $i$ 管出口断面为基准面，对水箱自由液面 $0\\text{—}0$（$z = h_i$，$p_0 = 0$，$v_0 \\approx 0$）与管出口断面 $i\\text{—}i$（$z = 0$，$p_i = 0$）列理想液体伯努利方程：\n  $$\n  h_i + 0 + 0 = 0 + 0 + \\frac{v_i^2}{2g} \\implies v_i = \\sqrt{2 g h_i}\n  $$\n  由图知三管出口在水面下的淹没深度满足 $h_1 < h_2 < h_3$，故 $v_1 < v_2 < v_3$，三管出口流速互不相等。\n\n**（2）各管出口射流所到达的最高点高度（高程）相等**（均与水箱自由液面齐平）。\n- **论证**：不计流动水头损失与空气阻力，选任一统一水平基准面（设水箱液面高程为 $z_0$，则第 $i$ 管出口高程为 $z_i = z_0 - h_i$）。对管出口断面 $i\\text{—}i$ 与铅直向上射流的最高点断面 $i^{\\prime}\\text{—}i^{\\prime}$（高程 $z_i^{\\prime}$，大气压 $p_i^{\\prime} = 0$，最高点竖向速度 $v_i^{\\prime} = 0$）列伯努利方程：\n  $$\n  z_i + 0 + \\frac{v_i^2}{2g} = z_i^{\\prime} + 0 + 0\n  $$\n  将 $\\frac{v_i^2}{2g} = h_i$ 代入得：射流相对自身管口向上喷起的高度为 $\\Delta z_i = z_i^{\\prime} - z_i = h_i$，而射流最高点到达的绝对高程为：\n  $$\n  z_i^{\\prime} = z_i + h_i = (z_0 - h_i) + h_i = z_0 \\quad (i = 1, 2, 3)\n  $$\n  即三股射流最高点均恰好到达水箱溢流自由液面所在水平面，所到达的高度完全相等。",
                "analysis": "本题从能量守恒角度直观诠释了理想流体伯努利方程的几何意义：\n\n1. **势能向动能转化（管内出流段）**：水箱自由液面处的总水头恒为 $H_0 = z_0$。第 $i$ 根管口比液面低 $h_i$，位置水头减少了 $h_i$、压强水头在出口处降为零，不计损失时减少的势能全部转化为出口动能水头 $\\frac{v_i^2}{2g} = h_i$。管口越深，$h_i$ 越大，出口射流速度 $v_i = \\sqrt{2gh_i}$ 越大。\n2. **动能重新转化为位置势能（自由射流上升段）**：射流离开管口铅直上抛至顶点时速度归零，动能水头 $\\frac{v_i^2}{2g} = h_i$ 重新全部转化为位置高度增量 $\\Delta z_i = h_i$，总机械能守恒使最高点严格回到初始总水头线高度 $z_0$。",
                "analysisFigures": [],
                "pitfalls": "第（2）问表述时务必严谨区分“相对各管出口上升的射流高度 $\\Delta z_i = h_i$（三者不等）”与“射流顶点到达的标高 / 高度 $z_i^{\\prime} = z_0$（三者相等，均与水箱水面齐平）”，把两层关系都写出来绝不失分！",
                "chapter": 3,
                "kps": ["实际液体恒定总流能量方程", "孔口与管嘴出流", "总水头守恒"],
                "method": "理想流体伯努利方程水头转换论证法",
                "difficulty": 2,
                "rubric": [
                    {"label": "列水箱液面至各管出口伯努利方程推出 vi = √(2ghi)，由 h1 < h2 < h3 证得出口流速不相等", "pts": 5},
                    {"label": "列管口至射流最高点能量方程推出上升高度 Δzi = hi，证得三股射流最高点均到达水箱液面同一高度", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2018-03",
                "year": 2018,
                "no": 3,
                "type": "short",
                "score": 10,
                "title": "应用能量方程解释向两张平行薄纸间吹气彼此靠拢现象",
                "stem": "试用能量方程式解释现象：向两张靠得很近的薄纸吹气，两张纸不是彼此分开，而是彼此靠拢。",
                "note": "",
                "figures": [],
                "shortAnswer": "吹气时两纸内侧空气流速 v1 大，外侧空气近乎静止（v2 ≈ 0、压强为大气压 pa）；由同高程伯努利方程 p1/(ρg) + v1²/(2g) = p2/(ρg) + v2²/(2g) 知流速大处压强小（p1 < pa），纸片外侧大气压大于内侧气压，产生向内的净压力差使两纸彼此靠拢。",
                "judgeAnswer": None,
                "answer": "**解释如下**（流场与压强关系见解图 3）：\n\n1. **建立内外侧气流能量关系**：在忽略空气压缩性与局部高度差（取同一水平高度 $z_1 = z_2$）及能量损失的近似下，沿流线由上游静止大气环境（压强 $p_a$，流速 $\\approx 0$）至两张薄纸之间的夹缝内侧（断面 $1$，流速 $v_1$，绝对压强 $p_1$）及薄纸外侧环境（点 $2$，空气基本静止 $v_2 \\approx 0$，绝对压强 $p_2 = p_a$）应用伯努利能量方程：\n   $$\n   z_1 + \\frac{p_1}{\\rho_{\\text{气}} g} + \\frac{v_1^2}{2g} = z_2 + \\frac{p_2}{\\rho_{\\text{气}} g} + \\frac{v_2^2}{2g}\n   $$\n2. **推导内外侧压强差**：因 $z_1 = z_2$，化简得：\n   $$\n   p_1 + \\frac{1}{2}\\rho_{\\text{气}} v_1^2 = p_2 + \\frac{1}{2}\\rho_{\\text{气}} v_2^2\n   $$\n   向两张靠得很近的薄纸中间吹气时，纸间通道狭窄，内侧空气流速 $v_1$ 很大，而两纸外侧的空气几乎处于静止状态（$v_2 \\approx 0$，$p_2 = p_a$）。因 $v_1 > v_2$，必有：\n   $$\n   p_1 = p_a - \\frac{1}{2}\\rho_{\\text{气}} v_1^2 < p_a = p_2\n   $$\n3. **受力结论**：每张薄纸外侧承受较大的大气压强 $p_a$，内侧承受较小的动压强 $p_1$，内外两侧形成指向夹缝中心的净压强差 $\\Delta p = p_2 - p_1 \\approx \\frac{1}{2}\\rho_{\\text{气}} v_1^2 > 0$，将两张薄纸向中间推压而彼此靠拢（且越靠拢缝隙越窄、流速越快、负压吸力越强）。",
                "analysis": "**深入物理补充（伯努利效应与流线弯曲适用性）**\n\n- 严格从流体力学角度看，吹入的高速射流对周围静止空气产生卷吸（夹带）作用，周围远场大气压为 $p_a$（流速为 $0$）的空气向低压射流区汇入；同时当两张薄纸微微向内弯曲形成先收缩后扩散的流道时（见解图 3），夹缝喉部过流面积最小、流速 $v_1$ 最大，沿同一流束由进口（接近大气压）至喉部应用伯努利方程，喉部静压显著低于外侧静止大气压 $p_a$。\n- 这一“流速大处静压强小，流速小处静压强大”的规律即著名的**伯努利效应**，在航海中“两船近距离同向并行易发生吸拢相撞”以及文丘里射流抽吸器中具有完全相同的力学本质。",
                "analysisFigures": [
                    {"src": "figures/q03_sol.png", "caption": "解图 3　向两张平行薄纸中间吹气时的内外侧流速与压强差示意图"}
                ],
                "pitfalls": "题目明确要求“试用能量方程式解释现象”，答题时**必须写出完整的伯努利能量方程表达式** $z_1 + \\frac{p_1}{\\rho g} + \\frac{v_1^2}{2g} = z_2 + \\frac{p_2}{\\rho g} + \\frac{v_2^2}{2g}$，并明确指出 $z_1 = z_2$、$v_1 > v_2 \\Rightarrow p_1 < p_2$，切勿只写定性文字而不列方程！",
                "chapter": 3,
                "kps": ["实际液体恒定总流能量方程", "伯努利流速压强转换效应"],
                "method": "伯努利方程流速增大降压效应分析法",
                "difficulty": 1,
                "rubric": [
                    {"label": "正确写出等高处伯努利能量方程 z1 + p1/(ρg) + v1²/(2g) = z2 + p2/(ρg) + v2²/(2g)", "pts": 3},
                    {"label": "对比纸片内侧吹气流速大（v1 > v2 ≈ 0）推出内侧气压小于外侧大气压（p1 < p2 = pa）", "pts": 4},
                    {"label": "指明外侧大气压大于内侧气压产生向内的净压力差，使两张薄纸彼此靠拢", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2018-04",
                "year": 2018,
                "no": 4,
                "type": "short",
                "score": 10,
                "title": "圆管层流与紊流粗糙区沿程水头损失流速指数关系及达西公式统一性辨析",
                "stem": "为什么说在圆管层流中的沿程水头损失与流速的一次方成正比？又为什么在紊流粗糙区中的沿程水头损失与流速的二次方成正比？而两种流型下都能应用达西公式 $h_f = \\lambda \\frac{l}{d}\\frac{v^2}{2g}$ 计算沿程水头损失，它们是否矛盾？为什么？",
                "note": "",
                "figures": [],
                "shortAnswer": "（1）圆管层流中 λ = 64/Re = 64ν/(vd) 与 v 成反比，代入达西公式消去一个 v 得 hf = 32νlv/(gd²) ∝ v¹；（2）紊流粗糙区黏性底层被粗糙突起完全刺穿，阻力由突起脱流旋涡惯性主导，λ = f(Δ/d) 与 Re（即 v）无关为常数，故 hf ∝ v²；（3）不矛盾，因为达西公式中的沿程阻力系数 λ 并非定常数，而是随流态变化的无量纲函数 λ = f(Re, Δ/d)，通过 λ 对 v 的不同依赖关系将各流区统一在同一形式下。",
                "judgeAnswer": None,
                "answer": "**（1）为什么圆管层流中 $h_f \\propto v^1$？**\n- 圆管层流中流体分层平行滑动、无横向脉动混掺，阻力纯由分子黏滞切应力 $\\tau = \\mu \\frac{\\mathrm{d}u}{\\mathrm{d}y}$ 引起（哈根—泊肃叶定律）。此时沿程阻力系数仅与雷诺数成反比：\n  $$\n  \\lambda = \\frac{64}{Re} = \\frac{64 \\nu}{v d}\n  $$\n  将其代入达西公式得：\n  $$\n  h_f = \\frac{64 \\nu}{v d} \\cdot \\frac{l}{d} \\frac{v^2}{2g} = \\frac{32 \\nu l}{g d^2} v \\propto v^1\n  $$\n  故层流沿程水头损失与断面平均流速的一次方成正比。\n\n**（2）为什么紊流粗糙区（阻力平方区）中 $h_f \\propto v^2$？**\n- 在高雷诺数的紊流粗糙区（尼古拉兹曲线水平直线区），近壁层流黏性底层极薄（$\\delta_l \\ll \\Delta$），管壁粗糙凸起完全暴露在高速紊流核心中，水流绕过粗糙颗粒不断发生边界层分离与旋涡脱落，阻力几乎完全由正比于 $\\rho v^2$ 的形状压差惯性阻力主导。此时 $\\lambda = f\\left(\\frac{\\Delta}{d}\\right)$ **仅取决于相对粗糙度而与雷诺数 $Re$（即流速 $v$）无关**，对给定管道 $\\lambda$ 为常数，故由 $h_f = \\lambda \\frac{l}{d}\\frac{v^2}{2g}$ 知 $h_f \\propto v^2$。\n\n**（3）两者都能应用达西公式计算并不矛盾！**\n- **原因**：达西—韦斯巴赫公式 $h_f = \\lambda \\frac{l}{d}\\frac{v^2}{2g}$ 是由量纲分析与流体力学基本平衡关系导出的普适水头损失结构式，公式中的**沿程阻力系数 $\\lambda$ 并不是一个固定常数**，而是雷诺数与相对粗糙度的无量纲函数 $\\lambda = \\lambda\\left(Re, \\frac{\\Delta}{d}\\right)$：\n  - 当层流时，$\\lambda = 64/Re \\propto v^{-1}$，与后项 $v^2$ 相乘正好还原出 $h_f \\propto v^1$；\n  - 当紊流光滑区时，$\\lambda = 0.3164 Re^{-0.25} \\propto v^{-0.25}$，相乘得 $h_f \\propto v^{1.75}$；\n  - 当紊流粗糙区时，$\\lambda = \\text{const} \\propto v^0$，相乘得 $h_f \\propto v^2$。\n  正是由于 $\\lambda$ 随流型改变其对 $v$ 的函数依赖关系，才使达西公式在所有流区均精确成立，毫无矛盾。",
                "analysis": "可结合尼古拉兹（Nikuradse）实验与通用幂指数形式 $h_f \\propto v^m$ 深化理解：\n\n$$\n\\lambda \\propto Re^{m - 2} \\propto v^{m - 2} \\implies h_f = \\lambda \\frac{l}{d}\\frac{v^2}{2g} \\propto v^{m - 2} \\cdot v^2 = v^m\n$$\n\n- **层流区（$Re \\le 2000$）**：$m = 1 \\iff \\lambda = 64/Re \\propto v^{-1}$（耗能由黏性剪切应力主导，与管壁粗糙度 $\\Delta/d$ 无关）；\n- **紊流过渡区（含水力光滑区 $m = 1.75$）**：$1.75 \\le m < 2$，$\\lambda = \\lambda(Re, \\Delta/d)$；\n- **紊流粗糙区 / 阻力平方区**：$m = 2 \\iff \\lambda = \\frac{1}{\\left(2\\lg\\frac{3.7d}{\\Delta}\\right)^2}$ 为与 $v$ 无关的常数（耗能由粗糙元尾迹涡惯性力主导，与黏度 $\\nu$ 无关）。\n\n因此，不能孤立地只看达西公式显式写出的 $v^2$ 因子，必须把隐含在 $\\lambda(Re)$ 中的流速幂次合并考察。",
                "analysisFigures": [],
                "pitfalls": "最常见的失分点是只背诵了数学代换 $\\lambda = 64/Re$，却漏答第（2）问的物理原因（黏性底层变薄使壁面粗糙突起完全暴露于紊流中、压差惯性阻力主导导致 $\\lambda$ 仅与 $\\Delta/d$ 有关而与 $Re$ 无关），以及第（3）问未点明“$\\lambda$ 不是常数而是 $\\lambda(Re, \\Delta/d)$ 函数”。",
                "chapter": 4,
                "kps": ["圆管层流哈根-泊肃叶公式", "尼古拉兹实验与阻力分区", "达西-韦斯巴赫公式"],
                "method": "沿程阻力系数雷诺数依赖性与达西公式辨析",
                "difficulty": 2,
                "rubric": [
                    {"label": "由圆管层流 λ = 64/Re = 64ν/(vd) 代入达西公式推得 hf = 32νlv/(gd²)，阐明与 v 一次方成正比", "pts": 3},
                    {"label": "阐明紊流粗糙区粗糙元刺穿黏性底层、λ = f(Δ/d) 与 Re 无关为常数，故 hf 与 v 二次方成正比", "pts": 3},
                    {"label": "明确回答不矛盾，指出达西公式中 λ = λ(Re, Δ/d) 是随流态变化的非常数函数，统一了不同流区的流速幂次", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2018-05",
                "year": 2018,
                "no": 5,
                "type": "short",
                "score": 10,
                "title": "不同高程同尺寸坝身淹没泄水管泄流量相等的机理分析",
                "stem": "图示 $A$，$B$，$C$ 为三条高程不同的坝身泄水管，其管径 $d$，长度 $l$，沿程阻力系数 $\\lambda$ 均相同，试问它们的泄流量是否相同？为什么？",
                "note": "",
                "figures": [
                    {"src": "figures/q05_orig.png", "caption": "题 5 图　上下游水位差为 z 的三条不同高程坝身淹没泄水管"}
                ],
                "shortAnswer": "相同（QA = QB = QC）。因为三条泄水管出口均淹没在下游水面以下，属于简单短管淹没出流，推动水流的净作用水头均等于上下游水库自由液面高差 z（与管道安装高程无关），且三管的 d、l、λ、ζ进、ζ出 均完全相同，故流速与流量相等。",
                "judgeAnswer": None,
                "answer": "**三条泄水管 $A$、$B$、$C$ 的泄流量完全相同**（$Q_A = Q_B = Q_C$）。\n\n**原因**：\n1. 由题 5 图可知，三条水平泄水管的进口与出口**全部淹没在上下游自由水面以下**，均属于**短管淹没出流**。\n2. 以下游渠道自由液面 $2\\text{—}2$ 为基准面（$z_2 = 0$，$p_2 = 0$，大水体行近流速 $v_2 \\approx 0$），对上游水库自由液面 $1\\text{—}1$（$z_1 = z$，$p_1 = 0$，$v_1 \\approx 0$）列实际液体恒定总流能量方程（对 $A$、$B$、$C$ 任一管均适用）：\n   $$\n   z + 0 + 0 = 0 + 0 + 0 + h_{w1\\text{-}2} = \\left(\\lambda \\frac{l}{d} + \\zeta_{\\text{进}} + \\zeta_{\\text{出}}\\right)\\frac{v^2}{2g}\n   $$\n   其中直角进口局部阻力系数 $\\zeta_{\\text{进}} = 0.5$，淹没突然扩大出口局部阻力系数 $\\zeta_{\\text{出}} = 1.0$。\n3. 由此解得管内平均流速与泄流量公式：\n   $$\n   v = \\frac{\\sqrt{2gz}}{\\sqrt{\\lambda \\dfrac{l}{d} + \\zeta_{\\text{进}} + \\zeta_{\\text{出}}}}, \\qquad Q = \\frac{\\pi}{4}d^2 v\n   $$\n   上式表明，淹没出流的有效作用水头恒等于**上下游自由液面落差 $z$**，与泄水管在下游水面下的淹没深度（高程）无关（位置越低的管道虽然进口静水压强大，但出口承受的下游背压也同步等量增大，两端测压管水头差恒为 $z$）。因三管的 $z$、$d$、$l$、$\\lambda$ 及进、出口局部阻力系数完全相同，故 $v_A = v_B = v_C$，泄流量 $Q_A = Q_B = Q_C$。",
                "analysis": "也可从单根管道首末断面的压差直观验证为何管轴高程自动抵消：设某泄水管中心线在下游水面下的深度为 $h_s$，则其在前池水面下的深度为 $z + h_s$。管进口前静水测压管水头为 $(z + h_s) - h_s = z$，管出口外静水测压管水头为 $h_s - h_s = 0$，推动管内水体克服阻力的总测压管水头差恒为 $\\Delta H_p = z - 0 = z$，与淹没深度 $h_s$ 彻底无关。\n\n**对比拓展**：若下游无水（或下游水位低于管道出口），使三管变为**自由出流**，则各管作用水头变为上游水面至各自管口中心的高差 $H_A < H_B < H_C$，此时才会出现 $Q_A < Q_B < Q_C$！本题题图清晰画出了下游水面淹没全部三根管道，故必为淹没出流且流量相等。",
                "analysisFigures": [],
                "pitfalls": "切忌凭直觉看到 $C$ 管埋得最深、进口水压最大就误判 $Q_C > Q_B > Q_A$！这是把“自由出流”与“淹没出流”混淆了：淹没出流时 $C$ 管进口水压虽大，但其出口淹没更深、下游水体顶托背压也同样增大，净作用水头只取决于上下游水面高差 $z$！",
                "chapter": 6,
                "kps": ["简单短管淹没出流", "实际液体恒定总流能量方程"],
                "method": "淹没短管出流上下游水位差能量分析法",
                "difficulty": 2,
                "rubric": [
                    {"label": "明确判断 A、B、C 三条泄水管的泄流量相同", "pts": 2},
                    {"label": "列上下游自由液面能量方程 z = (λl/d + ζ进 + ζ出)v²/(2g)，证明淹没出流有效作用水头均为水面差 z（与管道高程无关）", "pts": 5},
                    {"label": "结合三管 d、l、λ、ζ 均相等得出管内流速 v 与流量 Q = (πd²/4)v 完全相等", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2018-06",
                "year": 2018,
                "no": 6,
                "type": "calc",
                "score": 10,
                "title": "活塞油缸环状窄缝剪切流润滑油运动黏度计算",
                "stem": "一活塞油缸如图所示。已知油缸内径 $D = 14\\,\\mathrm{cm}$，活塞直径 $d = 13.4\\,\\mathrm{cm}$，活塞长度 $s = 16\\,\\mathrm{cm}$，当拉动活塞的力 $F = 7.5\\,\\mathrm{N}$ 时，活塞的移动速度 $u = 0.5\\,\\mathrm{m/s}$，若油缸内润滑油的密度为 $860\\,\\mathrm{kg/m^3}$，试求润滑油的运动粘度系数 $\\nu$ 的大小。",
                "note": "",
                "figures": [
                    {"src": "figures/q06_orig.png", "caption": "题 6 图　活塞在盛满润滑油的油缸内匀速拉动示意图"}
                ],
                "shortAnswer": "ν = 7.77 × 10⁻⁴ m²/s（动力黏度 μ ≈ 0.668 Pa·s）",
                "judgeAnswer": None,
                "answer": "润滑油的运动黏度系数 $\\nu \\approx 7.77 \\times 10^{-4}\\,\\mathrm{m^2/s}$（即 $7.77\\,\\mathrm{cm^2/s}$）。",
                "analysis": "**1. 计算油缸与活塞之间的环状单边油膜厚度 $\\delta$ 及剪切接触面积 $A$**\n\n活塞与油缸同轴布置，油缸内径 $D = 0.14\\,\\mathrm{m}$，活塞直径 $d = 0.134\\,\\mathrm{m}$，单侧环状油膜间隙厚度为：\n\n$$\n\\delta = \\frac{D - d}{2} = \\frac{0.14 - 0.134}{2} = 0.003\\,\\mathrm{m} = 3\\,\\mathrm{mm}\n$$\n\n因 $\\delta \\ll d$，可将环状薄油膜展开视为平行平板间线性库埃特剪切流，活塞外圆柱面受剪切面积为：\n\n$$\nA = \\pi d s = \\pi \\times 0.134 \\times 0.16 = 0.02144\\pi \\approx 0.067356\\,\\mathrm{m^2}\n$$\n\n**2. 应用牛顿内摩擦定律求动力黏度 $\\mu$ 与运动黏度 $\\nu$**\n\n活塞以速度 $u = 0.5\\,\\mathrm{m/s}$ 匀速移动，油缸壁静止，薄油膜内法向速度梯度近似为线性常量 $\\frac{\\mathrm{d}u}{\\mathrm{d}y} \\approx \\frac{u}{\\delta}$。由牛顿内摩擦定律：\n\n$$\nF = \\tau A = \\mu \\frac{u}{\\delta} A\n$$\n\n解得润滑油动力黏度 $\\mu$：\n\n$$\n\\mu = \\frac{F \\delta}{A u} = \\frac{7.5 \\times 0.003}{0.067356 \\times 0.5} = \\frac{0.0225}{0.033678} \\approx 0.6681\\,\\mathrm{Pa\\cdot s}\n$$\n\n已知润滑油密度 $\\rho = 860\\,\\mathrm{kg/m^3}$，故运动黏度系数 $\\nu$ 为：\n\n$$\n\\nu = \\frac{\\mu}{\\rho} = \\frac{0.66809}{860} \\approx 7.7685 \\times 10^{-4}\\,\\mathrm{m^2/s} \\approx 7.77 \\times 10^{-4}\\,\\mathrm{m^2/s}\n$$\n\n（注：若中间步骤将 $A$ 保留两位有效数字取 $0.067\\,\\mathrm{m^2}$、$\\mu \\approx 0.67\\,\\mathrm{Pa\\cdot s}$，则算得 $\\nu \\approx 7.79 \\times 10^{-4}\\,\\mathrm{m^2/s}$。）",
                "analysisFigures": [],
                "pitfalls": "1. 头号易错点：单边油膜厚度是 $\\delta = \\frac{D - d}{2} = 3\\,\\mathrm{mm}$，**千万不可漏除以 $2$** 误算成 $D - d = 6\\,\\mathrm{mm}$！\n2. 题目最终求的是**运动黏度 $\\nu = \\mu / \\rho$**（单位 $\\mathrm{m^2/s}$），算出动力黏度 $\\mu = 0.668\\,\\mathrm{Pa\\cdot s}$ 后切勿忘记再除以油的密度 $\\rho = 860\\,\\mathrm{kg/m^3}$！",
                "chapter": 1,
                "kps": ["牛顿内摩擦定律", "动力黏度与运动黏度", "环状薄油膜剪切流"],
                "method": "环状薄油膜牛顿内摩擦定律黏度反演法",
                "difficulty": 2,
                "rubric": [
                    {"label": "正确算出单边环状油膜厚度 δ = (D - d)/2 = 0.003 m 及活塞侧面积 A = πds ≈ 0.0674 m²", "pts": 3},
                    {"label": "应用牛顿内摩擦定律 F = μ(u/δ)A 解出动力黏度 μ ≈ 0.668 Pa·s", "pts": 4},
                    {"label": "由 ν = μ/ρ 除以润滑油密度 860 kg/m³ 求得运动黏度 ν ≈ 7.77 × 10⁻⁴ m²/s", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2018-07",
                "year": 2018,
                "no": 7,
                "type": "calc",
                "score": 10,
                "title": "活塞自重加压油缸与 U 形水银测压计液面高差计算",
                "stem": "如图测量装置，活塞直径 $d = 35\\,\\mathrm{mm}$，油的相对密度 $S_{\\text{油}} = 0.92$，水银的相对密度 $S_{\\text{水银}} = 13.60$，活塞与缸壁无泄漏和摩擦。当活塞重为 $15\\,\\mathrm{N}$ 时，$h = 700\\,\\mathrm{mm}$，试计算 U 形管测压计的液面高度 $\\Delta h$ 值。",
                "note": "",
                "figures": [
                    {"src": "figures/q07_orig.png", "caption": "题 7 图　活塞加压油容器连接 U 形水银测压计"}
                ],
                "shortAnswer": "Δh = 0.164 m（16.4 cm 或 164 mm）",
                "judgeAnswer": None,
                "answer": "U 形管测压计的水银液面高度差 $\\Delta h \\approx 0.164\\,\\mathrm{m}$（即 $16.4\\,\\mathrm{cm}$ 或 $164\\,\\mathrm{mm}$）。",
                "analysis": "**1. 求活塞底面传递给油液顶面的相对压强 $p_{\\text{活}}$**\n\n活塞直径 $d = 0.035\\,\\mathrm{m}$，其有效受压横截面积及自重 $G = 15\\,\\mathrm{N}$ 产生的相对压强为：\n\n$$\nA = \\frac{\\pi}{4} d^2 = \\frac{\\pi}{4} \\times 0.035^2 \\approx 9.6211 \\times 10^{-4}\\,\\mathrm{m^2}\n$$\n\n$$\np_{\\text{活}} = \\frac{G}{A} = \\frac{15}{9.6211 \\times 10^{-4}} \\approx 15590.7\\,\\mathrm{Pa} \\approx 15.59\\,\\mathrm{kPa}\n$$\n\n**2. 选取等压面 $1\\text{—}1$ 列静水压强平衡方程求 $\\Delta h$**\n\n如题 7 图所示，过 U 形管左支油—水银分界面作水平面 $1\\text{—}1$。下方水银连续、均质且静止，故 $1\\text{—}1$ 为等压面。U 形管右支顶端通大气（相对压强为 $0$），左支自活塞下表面至 $1\\text{—}1$ 等压面的油柱高度为 $h = 0.70\\,\\mathrm{m}$，设常温清水密度 $\\rho_{\\text{水}} = 1000\\,\\mathrm{kg/m^3}$，则 $\\rho_{\\text{油}} = S_{\\text{油}} \\rho_{\\text{水}} = 920\\,\\mathrm{kg/m^3}$，$\\rho_{\\text{水银}} = S_{\\text{水银}} \\rho_{\\text{水}} = 13600\\,\\mathrm{kg/m^3}$。列等压面相对压强平衡方程：\n\n$$\np_{\\text{活}} + \\rho_{\\text{油}} g h = \\rho_{\\text{水银}} g \\Delta h\n$$\n\n两边同除以 $\\rho_{\\text{水}} g$（取 $g = 9.80\\,\\mathrm{m/s^2}$）：\n\n$$\n\\Delta h = \\frac{\\dfrac{p_{\\text{活}}}{\\rho_{\\text{水}} g} + S_{\\text{油}} h}{S_{\\text{水银}}} = \\frac{\\dfrac{15590.7}{1000 \\times 9.80} + 0.92 \\times 0.70}{13.60} = \\frac{1.5909 + 0.6440}{13.60} = \\frac{2.2349}{13.60} \\approx 0.1643\\,\\mathrm{m} = 164.3\\,\\mathrm{mm}\n$$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，算得 $\\Delta h = \\frac{1.5893 + 0.6440}{13.60} \\approx 0.1642\\,\\mathrm{m} = 164.2\\,\\mathrm{mm}$，三位有效数字均为 $0.164\\,\\mathrm{m}$。）",
                "analysisFigures": [],
                "pitfalls": "1. 注意单位换算：$d = 35\\,\\mathrm{mm} = 0.035\\,\\mathrm{m}$、$h = 700\\,\\mathrm{mm} = 0.70\\,\\mathrm{m}$，切勿漏换算毫米直接代入国际单位公式；\n2. 活塞上表面与油缸下侧大气压 $p_a$ 相互抵消，采用相对压强（表压）列式最为简洁，右支开口端表压直接取 $0$ 即可。",
                "chapter": 2,
                "kps": ["多液层压差计", "等压面性质", "静水压强基本方程"],
                "method": "等压面静水压强递推法",
                "difficulty": 2,
                "rubric": [
                    {"label": "计算活塞横截面积 A = πd²/4 及活塞底面附加相对压强 p活 = G/A ≈ 15.59 kPa", "pts": 3},
                    {"label": "以 1—1 断面为等压面正确列出静水压强平衡方程 p活 + ρ油gh = ρ水银gΔh", "pts": 4},
                    {"label": "代入相对密度与高度解得 U 形管液面高度差 Δh ≈ 0.164 m（16.4 cm）", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2018-08",
                "year": 2018,
                "no": 8,
                "type": "calc",
                "score": 15,
                "title": "水箱圆底孔配重滑轮锥形自动控制阀开启临界水深计算",
                "stem": "水箱圆形底孔采用锥形自动控制阀，锥形阀以钢丝悬吊于滑轮上，钢丝的另一端系有重量 $W$ 为 $12000\\,\\mathrm{N}$ 的金属块，锥阀自重为 $310\\,\\mathrm{N}$，当不计滑轮摩擦时，问箱中水深 $H$ 为多大时锥形阀即可自动开启？",
                "note": "",
                "figures": [
                    {"src": "figures/q08_orig.png", "caption": "题 8 图　水箱圆底孔锥形自动控制阀与配重滑轮系统"}
                ],
                "shortAnswer": "H = 3.00 m（当水深 H ≥ 3.00 m 时锥形阀自动向下脱座开启）",
                "judgeAnswer": None,
                "answer": "当箱中水深达到 $H = 3.00\\,\\mathrm{m}$ 时，锥形阀即可自动开启。",
                "analysis": "**1. 分析锥形阀几何尺寸与开启运动机理（见解图 8）**\n\n由题 8 图尺寸可知：圆锥体总高 $h_{\\text{总}} = 1.8\\,\\mathrm{m}$，底面直径 $d = 1.5\\,\\mathrm{m}$，圆锥底面至水箱底孔下缘接触圆的铅垂距离为 $0.9\\,\\mathrm{m}$。因此伸入底孔接触圆上方水体中的小圆锥高度为：\n\n$$\nh_c = 1.8 - 0.9 = 0.9\\,\\mathrm{m}\n$$\n\n由相似三角形比例关系，水箱圆形底孔接触圆的直径 $D_0$ 为：\n\n$$\nD_0 = d \\cdot \\frac{h_c}{h_{\\text{总}}} = 1.5 \\times \\frac{0.9}{1.8} = 0.75\\,\\mathrm{m}\n$$\n\n**开启机理**：水深较浅时，右侧配重块 $W = 12000\\,\\mathrm{N}$ 通过定滑轮钢丝向上拉紧锥阀，使圆锥侧面从下方紧贴底孔圆周密封闭水；随着水深 $H$ 增大，水体对孔内上半部分锥面产生**竖直向下**的静水总压力 $F_z$，当向下的 $F_z$ 与向下的锥阀自重 $G = 310\\,\\mathrm{N}$ 之和达到向上的钢丝拉力 $T = W$ 时，底孔阀座接触支持力降为零，锥阀向下脱开阀座而自动开启泄水！\n\n**2. 计算上半锥面所受竖直向下的静水总压力 $F_z$（压力体法）**\n\n在未开启前，底孔接触圆（直径 $D_0 = 0.75\\,\\mathrm{m}$）外侧及下半截锥体全部暴露于大气中（相对压强为 $0$），仅有接触圆以内的上半圆锥侧表面承受箱内静水压力。假设开启时水深 $H > h_c = 0.9\\,\\mathrm{m}$（锥顶完全淹没），则该圆锥曲面与自由水面所围成的铅垂**实压力体**体积 $V_z$ 等于底径为 $D_0$、高为 $H$ 的圆柱体积减去上半圆锥体积：\n\n$$\nA_0 = \\frac{\\pi}{4} D_0^2 = \\frac{\\pi}{4} \\times 0.75^2 = 0.140625\\pi \\approx 0.441786\\,\\mathrm{m^2}\n$$\n\n$$\nV_{\\text{锥}} = \\frac{1}{3} A_0 h_c = \\frac{1}{3} \\times 0.441786 \\times 0.9 \\approx 0.132536\\,\\mathrm{m^3}\n$$\n\n$$\nV_z = V_{\\text{柱}} - V_{\\text{锥}} = A_0 H - V_{\\text{锥}} = 0.441786 H - 0.132536 = 0.441786 (H - 0.30)\n$$\n\n因为水体位于受压锥面正上方，为**实压力体**，故静水总压力方向**竖直向下**，大小为 $F_z = \\rho g V_z$。\n\n**3. 列临界开启竖向力平衡方程求水深 $H$**\n\n临界开启瞬间阀座法向反力 $N = 0$，对锥形阀列竖向力平衡方程 $\\sum F_z = 0$：\n\n$$\nF_z + G = W \\implies \\rho g V_z = W - G = 12000 - 310 = 11690\\,\\mathrm{N}\n$$\n\n代入 $\\rho = 1000\\,\\mathrm{kg/m^3}$，$g = 9.80\\,\\mathrm{m/s^2}$：\n\n$$\nV_z = \\frac{11690}{1000 \\times 9.80} \\approx 1.19286\\,\\mathrm{m^3}\n$$\n\n$$\nH = 0.30 + \\frac{V_z}{A_0} = 0.30 + \\frac{1.19286}{0.441786} = 0.30 + 2.7001 = 3.0001\\,\\mathrm{m} \\approx 3.00\\,\\mathrm{m}\n$$\n\n（校核：$H = 3.00\\,\\mathrm{m} > h_c = 0.9\\,\\mathrm{m}$，锥顶完全淹没假定成立！若取 $g = 9.81\\,\\mathrm{m/s^2}$，算得 $H = 0.30 + \\frac{11690}{9810 \\times 0.441786} = 2.997\\,\\mathrm{m} \\approx 3.00\\,\\mathrm{m}$，完全一致。）",
                "analysisFigures": [
                    {"src": "figures/q08_sol.png", "caption": "解图 8　锥形自动控制阀实压力体分解与临界开启竖向受力平衡图"}
                ],
                "pitfalls": "1. **受力方向千万看清题图结构**：圆锥底大顶小，下半截（$d = 1.5\\,\\mathrm{m}$）挂在底孔（$D_0 = 0.75\\,\\mathrm{m}$）下方大气中，配重块拉着钢丝**向上**顶紧阀座闭水，而箱内水压 $F_z$ 与锥体自重 $G$ 均**竖直向下**推开锥阀！因此临界平衡式是 $F_z + G = W$（即 $F_z = 12000 - 310 = 11690\\,\\mathrm{N}$），切勿把自重 $G$ 的方向写反，更不可把下半截暴露在空气中的圆台算进受压面！\n2. 压力体底圆直径必须取底孔接触圆直径 $D_0 = 0.75\\,\\mathrm{m}$，而非锥底直径 $d = 1.5\\,\\mathrm{m}$。",
                "chapter": 2,
                "kps": ["曲面静水总压力", "压力体计算", "自动控制阀静力平衡"],
                "method": "曲面实压力体与配重静力平衡临界开启法",
                "difficulty": 3,
                "rubric": [
                    {"label": "由相似几何关系求出底孔接触圆直径 D0 = 0.75 m 及孔内上半圆锥高 hc = 0.9 m", "pts": 4},
                    {"label": "应用压力体法写出孔内锥面实压力体体积 Vz = (πD0²/4)H - (1/3)(πD0²/4)hc（方向竖直向下）", "pts": 6},
                    {"label": "正确列出临界开启平衡方程 ρgVz + G = W（Fz = 11690 N），解得临界水深 H = 3.00 m", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2018-09",
                "year": 2018,
                "no": 9,
                "type": "proof",
                "score": 10,
                "title": "容器侧壁小孔自由平抛射流水平射程公式推导与最大射程条件求解",
                "stem": "一个很大的容器，侧壁有一小孔，其中心到容器底部的距离为 $h$，如图所示。忽略流动能量损失。试推导自由喷射流在水平方向所喷射的距离 $x$ 与 $H$ 和 $h$ 的函数关系；在 $H$ 一定的条件下，$h$ 为何值时，$x$ 最大。",
                "note": "",
                "figures": [
                    {"src": "figures/q09_orig.png", "caption": "题 9 图　大容器侧壁薄壁小孔自由平抛射流"}
                ],
                "shortAnswer": "函数关系：x = 2√[h(H - h)]（0 < h < H）；当 h = H/2 时水平射程 x 最大，最大射程 xmax = H。",
                "judgeAnswer": None,
                "answer": "（1）自由喷射流水平射程 $x$ 与 $H$、$h$ 的函数关系为：\n\n$$\nx = 2\\sqrt{h(H - h)} \\qquad (0 < h < H)\n$$\n\n（2）在总水深 $H$ 一定的条件下，当小孔高度 **$h = \\frac{H}{2}$**（位于总水深一半处）时水平射程 $x$ 最大，且最大水平射程为 $x_{\\max} = H$。",
                "analysis": "**1. 由伯努利方程（托里拆利公式）求小孔水平射流初速度 $v$**\n\n以容器底部水平面为基准面（$z = 0$）。容器很大，自由液面行近流速 $v_0 \\approx 0$；忽略流动能量损失（$h_w = 0$，收缩断面速度系数 $\\varphi = 1.0$）。对自由液面 $1\\text{—}1$（$z_1 = H$，$p_1 = 0$）与小孔出口大气射流断面 $2\\text{—}2$（$z_2 = h$，$p_2 = 0$）列理想液体伯努利方程：\n\n$$\nH + 0 + 0 = h + 0 + \\frac{v^2}{2g} \\implies v = \\sqrt{2g(H - h)}\n$$\n\n**2. 结合质点平抛运动方程推导水平射程 $x(H, h)$**\n\n水流自小孔水平射出后在重力作用下作自由平抛运动（不计空气阻力），从高度 $h$ 下落至容器底面（竖直位移为 $h$）所需时间 $t$ 满足：\n\n$$\nh = \\frac{1}{2} g t^2 \\implies t = \\sqrt{\\frac{2h}{g}}\n$$\n\n故射流落地点的水平喷射距离 $x$ 为：\n\n$$\nx = v t = \\sqrt{2g(H - h)} \\cdot \\sqrt{\\frac{2h}{g}} = 2\\sqrt{h(H - h)} = 2\\sqrt{Hh - h^2}\n$$\n\n**3. 求 $H$ 一定时使 $x$ 取极大值的孔口高度 $h$（见解图 9）**\n\n对 $x(h) = 2\\sqrt{Hh - h^2}$（$0 < h < H$）关于 $h$ 求导并令导数为零：\n\n$$\n\\frac{\\mathrm{d}x}{\\mathrm{d}h} = \\frac{H - 2h}{\\sqrt{Hh - h^2}} = 0 \\implies h = \\frac{H}{2}\n$$\n\n当 $0 < h < \\frac{H}{2}$ 时 $\\frac{\\mathrm{d}x}{\\mathrm{d}h} > 0$（单调递增），当 $\\frac{H}{2} < h < H$ 时 $\\frac{\\mathrm{d}x}{\\mathrm{d}h} < 0$（单调递减）（或由均值不等式 $h(H - h) \\le \\left[\\frac{h + (H - h)}{2}\\right]^2 = \\frac{H^2}{4}$，当且仅当 $h = H - h$ 即 $h = \\frac{H}{2}$ 时取等号）。\n\n因此，当 **$h = \\frac{H}{2}$** 时水平射程 $x$ 达到最大值，且最大水平射程为 $x_{\\max} = 2\\sqrt{\\frac{H}{2}\\cdot\\frac{H}{2}} = H$。",
                "analysisFigures": [
                    {"src": "figures/q09_sol.png", "caption": "解图 9　侧壁小孔不同高度平抛射流轨迹对比与无量纲极值曲线"}
                ],
                "pitfalls": "注意分辨小孔中心距底面的高度 $h$ 与小孔在水面下的淹没作用水头 $(H - h)$：孔口出流初速度由淹没深度决定 $v = \\sqrt{2g(H - h)}$（而非 $\\sqrt{2gh}$），下落时间由距底高度决定 $t = \\sqrt{2h/g}$，切勿将两者的物理角色颠倒（虽然乘积对称，但中间推导公式若写反会扣步骤分）！",
                "chapter": 9,
                "kps": ["薄壁孔口自由出流", "实际液体恒定总流能量方程", "平抛射流极值分析"],
                "method": "孔口出流托里拆利公式与平抛运动极值法",
                "difficulty": 2,
                "rubric": [
                    {"label": "列容器液面与小孔出口伯努利方程求得水平出流速度 v = √[2g(H - h)]", "pts": 3},
                    {"label": "联立自由落体时间 t = √(2h/g) 推导出水平射程函数关系 x = 2√[h(H - h)]", "pts": 4},
                    {"label": "通过求导 dx/dh = 0 或均值不等式证得当 h = H/2 时 x 最大（且 xmax = H）", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2018-10",
                "year": 2018,
                "no": 10,
                "type": "calc",
                "score": 15,
                "title": "顶部铅直进水侧壁水平出流水箱的磅秤读数动量方程计算",
                "stem": "质量为 $100\\,\\mathrm{kg}$ 的空水箱，放在磅秤上，如图所示。水箱中存有 $20^{\\circ}\\mathrm{C}$ 的水（密度为 $998\\,\\mathrm{kg/m^3}$），体积为 $1\\,\\mathrm{m^3}$。进水和出水管管径均为 $d_1 = d_2 = 50\\,\\mathrm{mm}$，它们的流量均为 $0.06\\,\\mathrm{m^3/s}$，试问磅秤上的读数为多少？",
                "note": "",
                "figures": [
                    {"src": "figures/q10_orig.png", "caption": "题 10 图　顶部铅直进水、侧壁水平出流的磅秤测力水箱"}
                ],
                "shortAnswer": "磅秤上的力读数为 12590.2 N（12.59 kN，对应质量读数 1284.7 kg；若取 g = 9.81 m/s² 则为 12601.2 N ≈ 12.60 kN，对应质量读数 1284.5 kg）。",
                "judgeAnswer": None,
                "answer": "磅秤上的竖向压力读数为 **$12590.2\\,\\mathrm{N}$（即 $12.59\\,\\mathrm{kN}$）**，若折算为质量刻度读数则为 **$1284.7\\,\\mathrm{kg}$**（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，力读数为 **$12601.2\\,\\mathrm{N} \\approx 12.60\\,\\mathrm{kN}$**，对应质量读数 **$1284.5\\,\\mathrm{kg}$**）。",
                "analysis": "**1. 判断流态恒定性并计算进、出水断面流速**\n\n已知进水流量与出水流量相等：$Q_1 = Q_2 = Q = 0.06\\,\\mathrm{m^3/s}$，故水箱内贮水体积恒保持 $V = 1\\,\\mathrm{m^3}$ 不变，系统处于**恒定流动**状态。进、出水圆管内径均为 $d_1 = d_2 = 0.05\\,\\mathrm{m}$，断面面积及平均流速为：\n\n$$\nA_1 = A_2 = \\frac{\\pi}{4} d_1^2 = \\frac{\\pi}{4} \\times 0.05^2 \\approx 1.9635 \\times 10^{-3}\\,\\mathrm{m^2}\n$$\n\n$$\nv_1 = v_2 = \\frac{Q}{A_1} = \\frac{0.06}{1.9635 \\times 10^{-3}} \\approx 30.5577\\,\\mathrm{m/s}\n$$\n\n**2. 选取“水箱壳体 + 箱内水体”整体控制体列竖向动量方程（见解图 10）**\n\n沿顶部进水射流进入液面处截取水平控制面 $1\\text{—}1$，沿左侧出水管出口处截取铅直控制面 $2\\text{—}2$，以**水箱壳体与箱内 $1\\,\\mathrm{m^3}$ 水体整体**为控制体（水箱与磅秤不接触上方悬空进水管），取竖直向上为 $z$ 轴正方向：\n- **作用在整体控制体上的竖向外力**：\n  - 磅秤台面对水箱底部的向上支反力 $N$；\n  - 空水箱自重（向下）：$G_{\\text{箱}} = m_{\\text{箱}} g = 100 g$；\n  - 箱内存水自重（向下）：$G_{\\text{水}} = \\rho V g = 998 \\times 1 \\times g = 998 g$；\n  - 进、出口均为大气自由射流，相对压强 $p_1 = p_2 = 0$。\n- **进、出控制面的竖向速度投影**：\n  - 进口 $1\\text{—}1$：水流铅直向下射入，$v_{1z} = -v_1 = -30.5577\\,\\mathrm{m/s}$；\n  - 出口 $2\\text{—}2$：水流沿水平方向射出，竖向分速为零，$v_{2z} = 0$（说明水平出流仅对水箱产生向右的水平反推力，由台面静摩擦力平衡，不影响竖向磅秤读数）。\n\n取动量修正系数 $\\beta_1 = \\beta_2 = 1.0$，列 $z$ 向恒定总流动量方程：\n\n$$\nN - G_{\\text{箱}} - G_{\\text{水}} = \\rho Q (v_{2z} - v_{1z}) = \\rho Q \\left[0 - (-v_1)\\right] = \\rho Q v_1\n$$\n\n其中顶部铅直水射流冲击产生的动反力增量为（注意水密度采用题给 $20^{\\circ}\\mathrm{C}$ 值 $\\rho = 998\\,\\mathrm{kg/m^3}$）：\n\n$$\nF_{\\text{动}} = \\rho Q v_1 = 998 \\times 0.06 \\times 30.5577 \\approx 1829.80\\,\\mathrm{N}\n$$\n\n**3. 计算磅秤读数**\n\n取 $g = 9.80\\,\\mathrm{m/s^2}$ 时，水箱与存水总重为：\n\n$$\nG_{\\text{箱}} + G_{\\text{水}} = (100 + 998) \\times 9.80 = 1098 \\times 9.80 = 10760.40\\,\\mathrm{N}\n$$\n\n故磅秤受到的总竖向压力（即磅秤力读数）为：\n\n$$\nN = G_{\\text{箱}} + G_{\\text{水}} + \\rho Q v_1 = 10760.40 + 1829.80 = 12590.20\\,\\mathrm{N} \\approx 12.59\\,\\mathrm{kN}\n$$\n\n若磅秤表盘以质量（$\\mathrm{kg}$）刻度显示，则等效质量读数为：\n\n$$\nM_{\\text{读}} = \\frac{N}{g} = 1098 + \\frac{1829.80}{9.80} = 1098 + 186.71 = 1284.71\\,\\mathrm{kg} \\approx 1284.7\\,\\mathrm{kg}\n$$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $G_{\\text{箱}} + G_{\\text{水}} = 10771.38\\,\\mathrm{N}$，$N = 12601.18\\,\\mathrm{N} \\approx 12.60\\,\\mathrm{kN}$，对应质量刻度 $M_{\\text{读}} = 1284.52\\,\\mathrm{kg}$。）",
                "analysisFigures": [
                    {"src": "figures/q10_sol.png", "caption": "解图 10　水箱与箱内水体整体控制体竖向受力与动量通量图"}
                ],
                "pitfalls": "1. **严防把箱内水重 $G_{\\text{水}}$ 重复加两次的经典大坑**！若先单独取水体为控制体算出箱底对水体的支持力 $F = G_{\\text{水}} + \\rho Q v_1$，则 $F$ 中**已经包含了水重 $G_{\\text{水}}$**，此时磅秤总读数只等于 $F + G_{\\text{箱}}$，绝不能再写成 $F + G_{\\text{箱}} + G_{\\text{水}}$！直接取“水箱 + 水体”整体控制体列式 $N = G_{\\text{箱}} + G_{\\text{水}} + \\rho Q v_1$ 最清晰安全，绝不会重算。\n2. 题干专门给出了 $20^{\\circ}\\mathrm{C}$ 水密度 $\\rho = 998\\,\\mathrm{kg/m^3}$，计算 $G_{\\text{水}}$ 与动量项 $\\rho Q v_1$ 时应统一使用 $998\\,\\mathrm{kg/m^3}$。",
                "chapter": 3,
                "kps": ["恒定总流动量方程", "射流冲击力", "控制体选取技巧"],
                "method": "整体控制体竖向动量方程求支反力法",
                "difficulty": 3,
                "rubric": [
                    {"label": "由连续性方程求出进、出水断面流速 v1 = v2 = 4Q/(πd1²) ≈ 30.56 m/s", "pts": 4},
                    {"label": "选取恰当控制体列出竖向动量方程，准确给出铅直射流冲击力 ρQv1 ≈ 1829.8 N 且水平出流竖向动量为零", "pts": 6},
                    {"label": "计入空水箱重与 1 m³ 水重（不重复计入水重），求得磅秤读数 12.59 kN（或 12.60 kN / 1284.7 kg）", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2018-11",
                "year": 2018,
                "no": 11,
                "type": "calc",
                "score": 15,
                "title": "封闭受压容器铅直变径管淹没出流流量与管内特征点压强计算",
                "stem": "如图所示，水由封闭容器 $A$ 沿垂直变直径管道流入下面的水池，容器内 $p_0 = 20\\,\\mathrm{kPa}$ 且液面保持不变，若 $d_1 = 50\\,\\mathrm{mm}$，$d_2 = 100\\,\\mathrm{mm}$，容器内液面与水池液面的高差 $H = 1.0\\,\\mathrm{m}$，只计局部水头损失，试求：\n\n（1）管道通过的流量 $Q$；\n\n（2）距水池液面 $h = 0.5\\,\\mathrm{m}$ 处的管道内 $B$ 点的压强 $p_B$。\n\n（注：突然扩大局部阻力系数 $\\zeta = \\left(1 - \\frac{A_1}{A_2}\\right)^2$，突然缩小局部阻力系数 $\\zeta = 0.5\\left(1 - \\frac{A_2}{A_1}\\right)$，$A_1$ 为突变前的过水断面面积，$A_2$ 为突变后的过水断面面积，局部阻力系数均对应较小管道流速水头）",
                "note": "",
                "figures": [
                    {"src": "figures/q11_orig.png", "caption": "题 11 图　封闭受压容器铅直变径管淹没出流系统"}
                ],
                "shortAnswer": "（1）流量 Q = 9.71 × 10⁻³ m³/s（9.71 L/s）；（2）B 点相对压强 pB = 11.15 kPa（1.115 × 10⁴ Pa）。",
                "judgeAnswer": None,
                "answer": "（1）管道通过的流量 $Q \\approx 9.71 \\times 10^{-3}\\,\\mathrm{m^3/s}$（即 $9.71\\,\\mathrm{L/s}$）；\n\n（2）管道内 $B$ 点的相对压强 $p_B \\approx 11.15\\,\\mathrm{kPa}$（即 $1.115 \\times 10^4\\,\\mathrm{Pa}$）。",
                "analysis": "**（1）求全系统局部水头损失与管道流量 $Q$**\n\n小管直径 $d_1 = 0.05\\,\\mathrm{m}$，大管直径 $d_2 = 0.10\\,\\mathrm{m}$，小管与大管过水断面面积之比为：\n\n$$\n\\frac{A_{d1}}{A_{d2}} = \\left(\\frac{d_1}{d_2}\\right)^2 = \\left(\\frac{50}{100}\\right)^2 = 0.25\n$$\n\n按题干注释公式，水流自上而下依次经过 **4 处截面突变**，各局部阻力系数均对应较小管道（内径 $d_1$，流速 $v_1$）的流速水头 $\\frac{v_1^2}{2g}$：\n1. **容器 $A$ 进入上段小管 $d_1$（进口突然缩小，$\\frac{A_{\\text{后}}}{A_{\\text{前}}} \\to 0$）**：$\\zeta_{\\text{进}} = 0.5(1 - 0) = 0.5000$；\n2. **上段小管 $d_1$ 突然扩大至中段大管 $d_2$**：$\\zeta_{\\text{扩}} = \\left(1 - \\frac{A_{d1}}{A_{d2}}\\right)^2 = (1 - 0.25)^2 = 0.5625$；\n3. **中段大管 $d_2$ 突然缩小至下段小管 $d_1$**：$\\zeta_{\\text{缩}} = 0.5\\left(1 - \\frac{A_{d1}}{A_{d2}}\\right) = 0.5 \\times (1 - 0.25) = 0.3750$；\n4. **下段小管 $d_1$ 淹没流入水池（出口突然扩大，$\\frac{A_{\\text{前}}}{A_{\\text{后}}} \\to 0$）**：$\\zeta_{\\text{出}} = (1 - 0)^2 = 1.0000$。\n\n全管总局部水头损失为：\n\n$$\nh_{w,\\text{总}} = \\left(\\zeta_{\\text{进}} + \\zeta_{\\text{扩}} + \\zeta_{\\text{缩}} + \\zeta_{\\text{出}}\\right)\\frac{v_1^2}{2g} = (0.5 + 0.5625 + 0.375 + 1.0)\\frac{v_1^2}{2g} = 2.4375\\,\\frac{v_1^2}{2g}\n$$\n\n以下方水池自由液面 $3\\text{—}3$ 为基准面（$z_3 = 0$，$p_3 = 0$，$v_3 \\approx 0$），对封闭容器 $A$ 液面 $0\\text{—}0$（$z_0 = H = 1.0\\,\\mathrm{m}$，$p_0 = 20\\,\\mathrm{kPa}$，$v_0 \\approx 0$）与水池液面 $3\\text{—}3$ 列恒定总流能量方程（取 $\\rho = 1000\\,\\mathrm{kg/m^3}$，$g = 9.80\\,\\mathrm{m/s^2}$）：\n\n$$\nH + \\frac{p_0}{\\rho g} = 2.4375\\,\\frac{v_1^2}{2g}\n$$\n\n其中总作用水头 $H + \\frac{p_0}{\\rho g} = 1.0 + \\frac{20000}{9800} = 3.04082\\,\\mathrm{m}$，解得小管流速水头、流速与流量：\n\n$$\n\\frac{v_1^2}{2g} = \\frac{3.04082}{2.4375} \\approx 1.24751\\,\\mathrm{m}, \\qquad v_1 = \\sqrt{2 \\times 9.80 \\times 1.24751} \\approx 4.9448\\,\\mathrm{m/s}\n$$\n\n$$\nQ = \\frac{\\pi}{4} d_1^2 v_1 = \\frac{\\pi}{4} \\times 0.05^2 \\times 4.9448 \\approx 9.7091 \\times 10^{-3}\\,\\mathrm{m^3/s} \\approx 9.71 \\times 10^{-3}\\,\\mathrm{m^3/s}\n$$\n\n**（2）求粗管内 $B$ 点的相对压强 $p_B$**\n\n$B$ 点位于内径 $d_2 = 0.10\\,\\mathrm{m}$ 的中段粗管内，由连续性方程得 $B$ 断面平均流速及流速水头：\n\n$$\nv_2 = v_1 \\left(\\frac{d_1}{d_2}\\right)^2 = 0.25 v_1 \\approx 1.2362\\,\\mathrm{m/s}, \\qquad \\frac{v_2^2}{2g} = \\frac{1}{16}\\frac{v_1^2}{2g} \\approx 0.07797\\,\\mathrm{m}\n$$\n\n仍以水池液面 $3\\text{—}3$ 为基准面，对 $B\\text{—}B$ 断面（$z_B = h = 0.5\\,\\mathrm{m}$）与水池液面 $3\\text{—}3$ 列能量方程（$B$ 点至水池之间包含**突然缩小 $\\zeta_{\\text{缩}}$** 和**淹没出口 $\\zeta_{\\text{出}}$** 两项局部损失，且均乘以小管流速水头 $\\frac{v_1^2}{2g}$）：\n\n$$\nh + \\frac{p_B}{\\rho g} + \\frac{v_2^2}{2g} = 0 + (\\zeta_{\\text{缩}} + \\zeta_{\\text{出}})\\frac{v_1^2}{2g}\n$$\n\n代入数值解得 $B$ 点压强水头与相对压强：\n\n$$\n\\frac{p_B}{\\rho g} = (0.375 + 1.0) \\times 1.24751 - 0.5 - 0.07797 = 1.71533 - 0.57797 = 1.13736\\,\\mathrm{m}\n$$\n\n$$\np_B = \\rho g \\times 1.13736 = 9800 \\times 1.13736 \\approx 11146\\,\\mathrm{Pa} \\approx 11.15\\,\\mathrm{kPa}\n$$\n\n（注：若由容器液面 $0\\text{—}0$ 至 $B\\text{—}B$ 列式：$1.0 + \\frac{20000}{9800} = 0.5 + \\frac{p_B}{\\rho g} + \\frac{v_2^2}{2g} + (0.5 + 0.5625)\\frac{v_1^2}{2g}$，算得 $p_B = 11146\\,\\mathrm{Pa}$ 完全吻合！若取 $g = 9.81\\,\\mathrm{m/s^2}$，算得 $Q = 9.711 \\times 10^{-3}\\,\\mathrm{m^3/s}$，$p_B = 11147\\,\\mathrm{Pa} \\approx 11.15\\,\\mathrm{kPa}$。）",
                "analysisFigures": [],
                "pitfalls": "1. **不要漏掉进口 $\\zeta_{\\text{进}} = 0.5$ 和淹没出口 $\\zeta_{\\text{出}} = 1.0$**！题干注释给出突然缩小与突然扩大通式，容器进管与管入水池恰好分别是 $A_{\\text{容器}} \\to \\infty$ 与 $A_{\\text{池}} \\to \\infty$ 的特例，全管共有 4 处局部损失（总系数 $2.4375$），而非只有中间 2 处！\n2. 题干明确规定“局部阻力系数均对应较小管道流速水头”，故第（2）问列 $B\\text{—}B$ 到水池的能量方程时，$B$ 断面的自身动能水头用粗管流速 $\\frac{v_2^2}{2g}$，而右侧局部损失项 $(\\zeta_{\\text{缩}} + \\zeta_{\\text{出}})$ 必须乘以细管流速水头 $\\frac{v_1^2}{2g}$，切勿混用！",
                "chapter": 6,
                "kps": ["局部水头损失计算", "串联变径短管", "实际液体恒定总流能量方程"],
                "method": "局部阻力折算系数法与分段伯努利方程",
                "difficulty": 3,
                "rubric": [
                    {"label": "完整算准进口 0.5、突扩 0.5625、突缩 0.375、淹没出口 1.0 四项局部阻力系数（Σζ = 2.4375）", "pts": 4},
                    {"label": "列容器液面至水池液面能量方程求出细管流速 v1 ≈ 4.94 m/s 及流量 Q ≈ 9.71 × 10⁻³ m³/s", "pts": 5},
                    {"label": "求出粗管流速 v2 = 0.25v1 ≈ 1.24 m/s 并列 B 断面能量方程准确解出 pB ≈ 11.15 kPa", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2018-12",
                "year": 2018,
                "no": 12,
                "type": "calc",
                "score": 15,
                "title": "矩形断面混凝土引水渡槽均匀流底坡与出口槽底高程计算",
                "stem": "有一矩形断面引水渡槽，底宽 $b = 1.5\\,\\mathrm{m}$，槽长 $L = 116.5\\,\\mathrm{m}$，进口处槽底高程 $Z_1 = 52.06\\,\\mathrm{m}$，槽身为普通混凝土，糙率 $n = 0.014$。当通过设计流量 $Q = 10.5\\,\\mathrm{m^3/s}$ 时，槽中均匀流水深 $h_0 = 2.56\\,\\mathrm{m}$。求渡槽出口处底部高程 $Z_2$。",
                "note": "",
                "figures": [],
                "shortAnswer": "底坡 i = 0.00303（3.03 × 10⁻³），出口处槽底高程 Z2 = 51.71 m（精确值 51.707 m）。",
                "judgeAnswer": None,
                "answer": "渡槽出口处底部高程 $Z_2 \\approx 51.71\\,\\mathrm{m}$（保留三位小数为 $51.707\\,\\mathrm{m}$）。",
                "analysis": "**1. 计算矩形渡槽过水断面几何与水力要素（见解图 12）**\n\n已知矩形渡槽底宽 $b = 1.5\\,\\mathrm{m}$，均匀流正常水深 $h_0 = 2.56\\,\\mathrm{m}$：\n- 过水断面面积 $A$：\n\n$$\nA = b h_0 = 1.5 \\times 2.56 = 3.84\\,\\mathrm{m^2}\n$$\n\n- 湿周 $\\chi$（不含顶部自由水面宽度）：\n\n$$\n\\chi = b + 2 h_0 = 1.5 + 2 \\times 2.56 = 6.62\\,\\mathrm{m}\n$$\n\n- 水力半径 $R$：\n\n$$\nR = \\frac{A}{\\chi} = \\frac{3.84}{6.62} \\approx 0.58006\\,\\mathrm{m}\n$$\n\n**2. 应用谢才—曼宁公式求渡槽底坡 $i$**\n\n混凝土槽身糙率 $n = 0.014$，谢才系数 $C$ 与流量模数 $K$ 为：\n\n$$\nC = \\frac{1}{n} R^{1/6} = \\frac{1}{0.014} \\times 0.58006^{1/6} \\approx 65.2305\\,\\mathrm{m^{1/2}/s}\n$$\n\n$$\nK = A C \\sqrt{R} = \\frac{1}{n} A R^{2/3} = 3.84 \\times 65.2305 \\times \\sqrt{0.58006} \\approx 190.774\\,\\mathrm{m^3/s}\n$$\n\n由明渠均匀流基本公式 $Q = K\\sqrt{i}$，反解出渡槽底坡 $i$：\n\n$$\ni = \\left(\\frac{Q}{K}\\right)^2 = \\left(\\frac{10.5}{190.774}\\right)^2 \\approx 3.0293 \\times 10^{-3} \\approx 0.00303\n$$\n\n**3. 计算渡槽出口处底部高程 $Z_2$**\n\n明渠均匀流只能在正坡（顺坡 $i > 0$）渠道中形成，沿水流方向槽底高程降低。已知槽长 $L = 116.5\\,\\mathrm{m}$，进口槽底高程 $Z_1 = 52.06\\,\\mathrm{m}$，由底坡定义 $i = \\frac{Z_1 - Z_2}{L}$ 得：\n\n$$\n\\Delta Z = i L = 3.0293 \\times 10^{-3} \\times 116.5 \\approx 0.3529\\,\\mathrm{m}\n$$\n\n$$\nZ_2 = Z_1 - i L = 52.06 - 0.3529 = 51.7071\\,\\mathrm{m} \\approx 51.71\\,\\mathrm{m}\n$$",
                "analysisFigures": [
                    {"src": "figures/q12_sol.png", "caption": "解图 12　矩形混凝土引水渡槽断面尺寸与均匀流纵剖面高程示意图"}
                ],
                "pitfalls": "1. 明渠均匀流必定是顺坡流动（$Z_2 < Z_1$），故出口槽底高程是**进口高程减去高差** $Z_2 = Z_1 - i L$，切勿加反成 $Z_1 + i L$！\n2. 矩形敞口渡槽湿周为 $\\chi = b + 2h_0 = 6.62\\,\\mathrm{m}$，切勿按有压满管误算成 $2(b + h_0)$。",
                "chapter": 7,
                "kps": ["矩形明渠水力要素", "曼宁公式", "明渠均匀流底坡与高程"],
                "method": "谢才—曼宁公式明渠均匀流水力计算法",
                "difficulty": 2,
                "rubric": [
                    {"label": "计算矩形渡槽过水面积 A = 3.84 m²、湿周 χ = 6.62 m 及水力半径 R ≈ 0.580 m", "pts": 5},
                    {"label": "由谢才—曼宁公式求出谢才系数 C ≈ 65.23（或流量模数 K ≈ 190.77）及底坡 i ≈ 0.00303", "pts": 5},
                    {"label": "由顺坡关系 Z2 = Z1 - iL 准确算出出口底部高程 Z2 ≈ 51.71 m（51.707 m）", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2018-13",
                "year": 2018,
                "no": 13,
                "type": "calc",
                "score": 10,
                "title": "由不可压缩平面流函数验证无旋条件并求解速度势函数",
                "stem": "已知不可压缩流体平面流动的流函数为 $\\psi = xy + 2x - 3y + 10$，求速度势 $\\varphi$。",
                "note": "",
                "figures": [],
                "shortAnswer": "φ(x, y) = (1/2)x² - 3x - (1/2)y² - 2y + C（C 为任意常数）。",
                "judgeAnswer": None,
                "answer": "该平面流动的速度势函数为：\n\n$$\n\\varphi(x, y) = \\frac{1}{2}x^2 - 3x - \\frac{1}{2}y^2 - 2y + C \\quad (C\\text{ 为任意常数})\n$$",
                "analysis": "**1. 由流函数求平面流速分量 $(u_x, u_y)$**\n\n根据平面不可压缩流动流函数与流速分量的标准关系：\n\n$$\nu_x = \\frac{\\partial \\psi}{\\partial y} = \\frac{\\partial (xy + 2x - 3y + 10)}{\\partial y} = x - 3\n$$\n\n$$\nu_y = -\\frac{\\partial \\psi}{\\partial x} = -\\frac{\\partial (xy + 2x - 3y + 10)}{\\partial x} = -y - 2\n$$\n\n**2. 验证无旋（有势）流动条件**\n\n计算流体微团绕 $z$ 轴的旋转角速度 $\\omega_z$：\n\n$$\n\\omega_z = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} - \\frac{\\partial u_x}{\\partial y}\\right) = \\frac{1}{2}(0 - 0) = 0\n$$\n\n满足无旋条件（$\\nabla^2 \\psi = 0$），故速度势函数 $\\varphi(x, y)$ 确实存在。\n\n**3. 积分求解速度势函数 $\\varphi(x, y)$**\n\n由速度势定义 $\\frac{\\partial \\varphi}{\\partial x} = u_x = x - 3$，$\\frac{\\partial \\varphi}{\\partial y} = u_y = -(y + 2)$，写出全微分：\n\n$$\n\\mathrm{d}\\varphi = u_x\\,\\mathrm{d}x + u_y\\,\\mathrm{d}y = (x - 3)\\,\\mathrm{d}x - (y + 2)\\,\\mathrm{d}y\n$$\n\n两边不定积分得：\n\n$$\n\\varphi(x, y) = \\int (x - 3)\\,\\mathrm{d}x - \\int (y + 2)\\,\\mathrm{d}y = \\frac{1}{2}x^2 - 3x - \\frac{1}{2}y^2 - 2y + C\n$$\n\n其中 $C$ 为任意积分常数（流函数中的常数项 $10$ 求偏导后消去，对流速场及势函数无影响）。\n\n（注：若个别教材采用反号流函数定义 $u_x = -\\frac{\\partial \\psi}{\\partial y},\\; u_y = \\frac{\\partial \\psi}{\\partial x}$，则算得 $\\varphi = -\\frac{1}{2}x^2 + 3x + \\frac{1}{2}y^2 + 2y + C$。）",
                "analysisFigures": [],
                "pitfalls": "1. 流函数表达式中的常数项 $+10$ 对 $x$、$y$ 求偏导后均为 $0$，切勿误把 $10x$ 或 $10y$ 带入势函数；最后积分结果必须补上任意常数 $+C$！\n2. 即使题干未显式要求“先判断是否存在速度势”，标准解题步骤中也应先写一步 $\\omega_z = 0$ 验证有势条件成立，保证逻辑严密无懈可击。",
                "chapter": 5,
                "kps": ["流函数与势函数", "无旋流判别条件", "柯西-黎曼条件"],
                "method": "流函数求流速判无旋与全微分积分求势法",
                "difficulty": 2,
                "rubric": [
                    {"label": "由流函数定义正确求出流速分量 ux = ∂ψ/∂y = x - 3，uy = -∂ψ/∂x = -y - 2", "pts": 3},
                    {"label": "验证旋转角速度 ωz = (∂uy/∂x - ∂ux/∂y)/2 = 0，确认满足无旋有势条件", "pts": 3},
                    {"label": "由全微分 dφ = ux·dx + uy·dy 积分求得速度势 φ = (1/2)x² - 3x - (1/2)y² - 2y + C", "pts": 4}
                ]
            }
        ]
    }


def export_pack_and_web(paper: dict):
    """Write standardized pack (`扬州大学已整理数据/<year>/`) AND web JSON + WebP (`web/public/data/yzu-849/`)."""
    year = int(paper["year"])
    pack_dir = PACK_ROOT / str(year)
    pack_fig_dir = pack_dir / "figures"
    pack_dir.mkdir(parents=True, exist_ok=True)
    pack_fig_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save standardized JSON in `扬州大学已整理数据/<year>/<year>.json`
    pack_json_path = pack_dir / f"{year}.json"
    pack_json_path.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2. Convert figures to WebP (`quality=90, method=5`) and rewrite `src` for web JSON
    web_fig_dir = WEB_COURSE_DIR / "figures" / str(year)
    web_fig_dir.mkdir(parents=True, exist_ok=True)
    web_paper = copy.deepcopy(paper)

    fig_count = 0
    for q in web_paper["questions"]:
        for key in ("figures", "analysisFigures"):
            new_list = []
            for fig in q.get(key) or []:
                raw_name = Path(fig["src"]).name
                src_png = pack_fig_dir / raw_name
                if not src_png.exists():
                    raise FileNotFoundError(f"Missing source figure: {src_png}")
                webp_name = f"{src_png.stem}.webp"
                dest_webp = web_fig_dir / webp_name
                img = Image.open(src_png)
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
    print(f"[{year}] Wrote pack JSON ({pack_json_path}) & web JSON ({web_json_path}) with {fig_count} WebP figures.")


def main():
    extract_stem_figures()

    fig_2019 = PACK_ROOT / "2019" / "figures"
    draw_2019_q04_sol(fig_2019)
    draw_2019_q06_sol(fig_2019)
    draw_2019_q08_sol(fig_2019)
    draw_2019_q09_sol(fig_2019)
    draw_2019_q11_sol(fig_2019)
    print("[2019] Drew 5 matplotlib solution figures.")

    fig_2018 = PACK_ROOT / "2018" / "figures"
    draw_2018_q03_sol(fig_2018)
    draw_2018_q08_sol(fig_2018)
    draw_2018_q09_sol(fig_2018)
    draw_2018_q10_sol(fig_2018)
    draw_2018_q12_sol(fig_2018)
    print("[2018] Drew 5 matplotlib solution figures.")

    export_pack_and_web(build_2019_paper())
    export_pack_and_web(build_2018_paper())


if __name__ == "__main__":
    main()
