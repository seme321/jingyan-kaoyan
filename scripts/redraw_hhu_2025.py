# -*- coding: utf-8 -*-
"""
Batch redraw all 12 HHU 814 (2025) original exam figures (formerly sourced from
a watermark-removed .docx) into crisp, faithful white-background schematics.

Usage:
  python scripts/redraw_hhu_2025.py --workers 4 --qa-dir "<scratch>/qa_hhu_2025"
  python scripts/redraw_hhu_2025.py --only 2025:8,2025:27
"""

from __future__ import annotations

import argparse
import concurrent.futures
import math
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.patches as patches
import numpy as np

from fig_kit import (
    AUX,
    CONCRETE,
    INK,
    MERCURY,
    OIL,
    WATER,
    angle_arc,
    backup_and_save,
    build_qa_sheets,
    concrete_block,
    dim_arrow,
    flow_arrow,
    ground_hatch,
    new_canvas,
    water_surface,
)

REGISTRY: dict[tuple[int, int], Callable[[], object]] = {}


def reg(year: int, no: int):
    def deco(fn: Callable[[], object]):
        REGISTRY[(year, no)] = fn
        return fn
    return deco


def _u_tube_arc(cx: float, cy: float, r: float, n: int = 60) -> tuple[np.ndarray, np.ndarray]:
    ang = np.linspace(math.pi, 2.0 * math.pi, n)
    return cx + r * np.cos(ang), cy + r * np.sin(ang)


@reg(2025, 2)
def draw_2025_02():
    fig, ax = new_canvas(5.4, 4.2, (0.4, 7.8), (0.2, 5.6))
    cx, cy = 3.7, 1.85
    ri, ro = 0.72, 1.32
    x_l_out, x_l_in = cx - ro, cx - ri
    x_r_in, x_r_out = cx + ri, cx + ro
    y_top = 5.15
    y_00 = 2.45
    y_l = 3.45
    y_r = 4.45

    # Bottom U-bend coordinates
    xo, yo = _u_tube_arc(cx, cy, ro)
    xi, yi = _u_tube_arc(cx, cy, ri)

    # Liquid rho_1 fill (left column + U-bend + right column up to 0-0)
    poly_1_x = np.concatenate([[x_l_out, x_l_out], xo, [x_r_out, x_r_out, x_r_in, x_r_in], xi[::-1], [x_l_in, x_l_in]])
    poly_1_y = np.concatenate([[y_l, cy], yo, [cy, y_00, y_00, cy], yi[::-1], [cy, y_l]])
    ax.fill(poly_1_x, poly_1_y, facecolor=WATER, edgecolor="none", zorder=1)

    # Liquid rho_2 fill in right column (0-0 to y_r)
    ax.add_patch(
        patches.Rectangle((x_r_in, y_00), x_r_out - x_r_in, y_r - y_00, facecolor="#cbd5e1", edgecolor="none", zorder=1.5)
    )

    # Tube walls
    outer_x = np.concatenate([[x_l_out, x_l_out], xo, [x_r_out, x_r_out]])
    outer_y = np.concatenate([[y_top, cy], yo, [cy, y_top]])
    inner_x = np.concatenate([[x_l_in, x_l_in], xi, [x_r_in, x_r_in]])
    inner_y = np.concatenate([[y_top, cy], yi, [cy, y_top]])
    ax.plot(outer_x, outer_y, color=INK, lw=1.9, zorder=4)
    ax.plot(inner_x, inner_y, color=INK, lw=1.9, zorder=4)

    # Liquid surfaces & 0-0 isobaric datum
    water_surface(ax, x_l_out, x_l_in, y_l, mark_x=0.5 * (x_l_out + x_l_in), size=0.21)
    water_surface(ax, x_r_in, x_r_out, y_r, mark_x=0.5 * (x_r_in + x_r_out), size=0.21)
    ax.plot([1.45, 5.95], [y_00, y_00], ls="--", color=INK, lw=1.2, zorder=4)
    ax.text(1.3, y_00, "0", ha="right", va="center", fontsize=11.5, color=INK)
    ax.text(6.1, y_00, "0", ha="left", va="center", fontsize=11.5, color=INK)

    # Density labels
    ax.text(0.5 * (x_l_out + x_l_in), 1.9, r"$\rho_1$", ha="center", va="center", fontsize=12, color=INK, zorder=5)
    ax.text(
        0.5 * (x_r_in + x_r_out),
        3.45,
        r"$\rho_2$",
        ha="center",
        va="center",
        fontsize=12,
        color=INK,
        bbox=dict(facecolor="#cbd5e1", edgecolor="none", pad=1.2),
        zorder=5,
    )

    # Delta h between the two surfaces
    ax.plot([x_l_in, 3.92], [y_l, y_l], ls="--", color=AUX, lw=0.95, zorder=3)
    ax.plot([3.48, x_r_in], [y_r, y_r], ls="--", color=AUX, lw=0.95, zorder=3)
    dim_arrow(ax, (3.7, y_l), (3.7, y_r), r"$\Delta h$", bbox_white=True, fontsize=11.5)

    # Height h on the right
    ax.plot([x_r_out, 5.9], [y_r, y_r], ls="--", color=AUX, lw=0.95, zorder=3)
    dim_arrow(ax, (5.7, y_00), (5.7, y_r), r"$h$", text_offset=(0.24, 0.0), fontsize=12)
    return fig


@reg(2025, 3)
def draw_2025_03():
    fig, ax = new_canvas(6.8, 4.2, (0.0, 9.6), (0.2, 5.7))
    y_bot = 0.72
    y_top_tank = 5.05
    y_pipe_b = y_bot  # single continuous flat bottom line!
    y_pipe_t = 1.28
    y_pipe_c = 0.5 * (y_pipe_b + y_pipe_t)
    y_surf = 4.18

    # Tank & pipe on clean white background (open left side, single flat floor line)
    ax.plot([0.35, 8.50], [y_bot, y_bot], color=INK, lw=1.7, zorder=4)
    ax.plot([2.25, 2.25], [y_pipe_t, y_top_tank], color=INK, lw=1.7, zorder=4)

    # Piezometers (generous bore between k1 and k2)
    x_p1, x_p2, pw = 4.65, 6.25, 0.42
    hw = 0.5 * pw
    ax.plot([2.25, x_p1 - hw], [y_pipe_t, y_pipe_t], color=INK, lw=1.7, zorder=4)
    ax.plot([x_p1 + hw, x_p2 - hw], [y_pipe_t, y_pipe_t], color=INK, lw=1.7, zorder=4)
    ax.plot([x_p2 + hw, 8.50], [y_pipe_t, y_pipe_t], color=INK, lw=1.7, zorder=4)

    # Piezometer tubes + full-width inverted triangles inside tubes + vertical h1/h2 labels
    y_p_top = 5.15
    y_h1, y_h2 = 3.92, 3.05  # strictly H > h1 > h2
    for xp, yh, lbl in ((x_p1, y_h1, r"$h_1$"), (x_p2, y_h2, r"$h_2$")):
        ax.plot([xp - hw, xp - hw], [y_pipe_t, y_p_top], color=INK, lw=1.5, zorder=4)
        ax.plot([xp + hw, xp + hw], [y_pipe_t, y_p_top], color=INK, lw=1.5, zorder=4)
        # Water level line & full-width inverted triangle mark matching original
        ax.plot([xp - hw, xp + hw], [yh, yh], color=INK, lw=1.3, zorder=5)
        th = 0.34
        ax.plot([xp, xp - hw, xp + hw, xp], [yh, yh + th, yh + th, yh], color=INK, lw=1.2, zorder=5)
        ax.text(xp - hw - 0.16, 0.5 * (y_pipe_t + yh), lbl, ha="right", va="center", rotation=90, fontsize=11.5, color=INK)

    # Pipe centerline + outflow Q
    ax.plot([2.25, 8.50], [y_pipe_c, y_pipe_c], ls="--", color=AUX, lw=1.2, zorder=3)
    flow_arrow(ax, (8.50, y_pipe_c), (9.15, y_pipe_c), r"$Q$", text_offset=(0.50, 0.0), fontsize=12, lw=1.5)

    # Tank water surface + vertical H label
    water_surface(ax, 0.35, 2.25, y_surf, mark_x=0.88, size=0.22, lw=1.5)
    dim_arrow(ax, (1.50, y_pipe_c), (1.50, y_surf), "", fontsize=12)
    ax.text(1.22, 0.5 * (y_pipe_c + y_surf), r"$H$", ha="center", va="center", rotation=90, fontsize=12, color=INK)

    # Valves k1 and k2: stem passes down through pipe top wall into centerline + top cross-bar
    for xv, klbl in ((3.45, r"$k_1$"), (7.45, r"$k_2$")):
        ax.plot([xv, xv], [y_pipe_c, y_pipe_t + 0.32], color=INK, lw=1.6, zorder=5)
        ax.plot([xv - 0.22, xv + 0.22], [y_pipe_t + 0.32, y_pipe_t + 0.32], color=INK, lw=1.6, zorder=5)
        ax.text(xv, y_pipe_t + 0.44, klbl, ha="center", va="bottom", fontsize=12, color=INK)

    return fig


@reg(2025, 8)
def draw_2025_08():
    fig, ax = new_canvas(7.2, 4.0, (0.0, 10.0), (0.15, 5.75))

    # Left high reservoir (open on left) & right low reservoir (open on right)
    y_l_surf, y_l_bot = 4.22, 1.50
    y_r_surf, y_r_bot = 1.68, 0.45
    x_lw, x_rw = 2.00, 8.20

    # Siphon geometry flush with partition walls x_lw and x_rw
    x_t1, y_t1 = 4.05, 4.68
    x_t2, y_t2 = 6.00, 4.68
    y_in_c, y_out_c = 2.92, 1.12
    hp = 0.22  # generous pipe half-width

    # Left & right slant slopes and vertical wall intersection half-spans
    m1 = (y_t1 - y_in_c) / (x_t1 - x_lw)
    m2 = (y_out_c - y_t2) / (x_rw - x_t2)
    dy_l = hp * math.hypot(1.0, m1)
    dy_r = hp * math.hypot(1.0, m2)

    # Left tank walls (open left, stepped partition at x_lw broken across pipe opening)
    ax.plot([0.35, x_lw], [y_l_bot, y_l_bot], color=INK, lw=1.7, zorder=4)
    ax.plot([x_lw, x_lw], [y_l_bot, y_in_c - dy_l], color=INK, lw=1.7, zorder=4)
    ax.plot([x_lw, x_lw], [y_in_c + dy_l, 4.65], color=INK, lw=1.7, zorder=4)
    water_surface(ax, 0.35, x_lw, y_l_surf, mark_x=1.22, size=0.20, lw=1.5)
    flow_arrow(ax, (0.55, 2.55), (1.60, 2.55), r"$v_0 = 0$", text_offset=(0.0, -0.34), fontsize=10.5, lw=1.2)

    # Right tank walls (open right, stepped partition at x_rw broken across pipe opening)
    ax.plot([x_rw, 9.65], [y_r_bot, y_r_bot], color=INK, lw=1.7, zorder=4)
    ax.plot([x_rw, x_rw], [y_r_bot, y_out_c - dy_r], color=INK, lw=1.7, zorder=4)
    ax.plot([x_rw, x_rw], [y_out_c + dy_r, 2.45], color=INK, lw=1.7, zorder=4)
    water_surface(ax, x_rw, 9.65, y_r_surf, mark_x=8.95, size=0.20, lw=1.5)
    flow_arrow(ax, (8.45, 1.12), (9.48, 1.12), r"$v_1 = 0$", text_offset=(0.0, -0.32), fontsize=10.5, lw=1.2)

    # Trapezoidal siphon outer/inner walls flush with x_lw and x_rw
    ang1 = math.atan(m1)
    ang2 = math.atan(abs(m2))
    dx_b1 = hp * math.tan(0.5 * ang1)
    dx_b2 = hp * math.tan(0.5 * ang2)

    up_x = [x_lw, x_t1 - dx_b1, x_t2 + dx_b2, x_rw]
    up_y = [y_in_c + dy_l, y_t1 + hp, y_t2 + hp, y_out_c + dy_r]
    dn_x = [x_lw, x_t1 + dx_b1, x_t2 - dx_b2, x_rw]
    dn_y = [y_in_c - dy_l, y_t1 - hp, y_t2 - hp, y_out_c - dy_r]

    ax.plot(up_x, up_y, color=INK, lw=1.6, zorder=6)
    ax.plot(dn_x, dn_y, color=INK, lw=1.6, zorder=6)

    # Velocity arrow + v centered inside horizontal top section
    flow_arrow(ax, (4.52, y_t1), (5.16, y_t1), r"$v$", text_offset=(0.56, 0.0), fontsize=11.5, lw=1.3)

    # Hanging inverted-U tube from bottom wall of horizontal segment
    xm = 4.78
    hu = 0.085  # half-width of U-tube bore
    y_dn_top = y_t1 - hp
    y_ub = 2.15
    rc_u = 0.25
    x_r_leg = xm + 2.0 * rc_u
    y_u_open = 2.98

    # Break bottom pipe wall at left U-tube attachment
    ax.add_patch(patches.Rectangle((xm - hu + 0.01, y_dn_top - 0.04), 2 * hu - 0.02, 0.08, facecolor="white", edgecolor="none", zorder=6.2))
    ax.plot([xm - hu, xm - hu], [y_dn_top, y_ub], color=INK, lw=1.3, zorder=6.5)
    ax.plot([xm + hu, xm + hu], [y_dn_top, y_ub], color=INK, lw=1.3, zorder=6.5)

    uo_x, uo_y = _u_tube_arc(xm + rc_u, y_ub, rc_u + hu, n=40)
    ui_x, ui_y = _u_tube_arc(xm + rc_u, y_ub, rc_u - hu, n=40)
    ax.plot(uo_x, uo_y, color=INK, lw=1.3, zorder=6.5)
    ax.plot(ui_x, ui_y, color=INK, lw=1.3, zorder=6.5)
    ax.plot([x_r_leg - hu, x_r_leg - hu], [y_ub, y_u_open], color=INK, lw=1.3, zorder=6.5)
    ax.plot([x_r_leg + hu, x_r_leg + hu], [y_ub, y_u_open], color=INK, lw=1.3, zorder=6.5)
    # Small horizontal liquid meniscus line near top of right open U-tube arm
    ax.plot([x_r_leg - hu, x_r_leg + hu], [y_u_open - 0.24, y_u_open - 0.24], color=INK, lw=1.2, zorder=6.5)

    # INTENTIONALLY ERRONEOUS HEAD LINES (faithful to original exam figure!)
    # Solid Total Head Line: starts below left water surface, steps slightly down at U-tube,
    # and terminates ABOVE right water surface at x_rw (y_r_surf + 0.28).
    y_sol_l0, y_sol_l1 = 3.92, 3.22
    y_sol_r0, y_sol_r1 = 2.96, y_r_surf + 0.28
    ax.plot([x_lw, xm - hu], [y_sol_l0, y_sol_l1], color=INK, lw=1.35, zorder=7.5)
    ax.plot([xm + hu, x_rw], [y_sol_r0, y_sol_r1], color=INK, lw=1.35, zorder=7.5)

    # Dashed Piezometric Head Line: continuous parallel below total head line,
    # terminating BELOW right water surface at x_rw (y_r_surf - 0.22).
    y_piezo_l = 3.50
    y_piezo_r = y_r_surf - 0.22
    ax.plot([x_lw, x_rw], [y_piezo_l, y_piezo_r], ls="--", color=INK, lw=1.25, zorder=7.5)

    # Clean leader annotations
    ax.annotate(
        "总水头线",
        xy=(2.75, 3.73),
        xytext=(2.60, 4.92),
        ha="center",
        va="bottom",
        fontsize=10.5,
        color=INK,
        arrowprops=dict(arrowstyle="-", color=AUX, lw=0.95),
        zorder=8,
    )
    ax.annotate(
        "测压管水头线",
        xy=(3.55, 3.04),
        xytext=(3.55, 1.88),
        ha="center",
        va="top",
        fontsize=10.5,
        color=INK,
        arrowprops=dict(arrowstyle="-", color=AUX, lw=0.95),
        zorder=8,
    )
    for txt in ax.texts:
        txt.set_zorder(8)
    return fig


@reg(2025, 12)
def draw_2025_12():
    fig, ax = new_canvas(5.8, 3.8, (0.4, 8.2), (0.1, 5.4))
    ox, oy = 4.2, 0.85
    # Parabolic curve y - oy = a * (x - ox)^2 from (4.2, 0.85) to (6.2, 4.15)
    h_dam = 3.3
    x_top_l = 6.2
    a = h_dam / ((x_top_l - ox) ** 2)
    xs_curve = np.linspace(ox, x_top_l, 80)
    ys_curve = oy + a * ((xs_curve - ox) ** 2)

    # Shaded dam body
    dam_x = np.concatenate([xs_curve, [6.75, 7.35, ox]])
    dam_y = np.concatenate([ys_curve, [oy + h_dam, oy, oy]])
    ax.fill(dam_x, dam_y, facecolor="#e2e8f0", edgecolor="none", zorder=2)
    ax.plot(xs_curve, ys_curve, color=INK, lw=2.0, zorder=4)
    ax.plot([x_top_l, 6.75, 7.35], [oy + h_dam, oy + h_dam, oy], color=INK, lw=1.7, zorder=4)

    # Coordinate axes x, y, O
    flow_arrow(ax, (1.0, oy), (7.85, oy), r"$x$", text_offset=(3.55, 0.0), fontsize=12, lw=1.4)
    flow_arrow(ax, (ox, oy), (ox, 5.05), r"$y$", text_offset=(-0.26, 2.02), fontsize=12, lw=1.4)
    ax.text(ox, oy - 0.16, r"$O$", ha="center", va="top", fontsize=12, color=INK)

    # Upstream water surface at y = oy + h_dam
    y_w = oy + h_dam
    water_surface(ax, 1.35, x_top_l, y_w, mark_x=3.15, size=0.22)
    dim_arrow(ax, (2.15, oy), (2.15, y_w), "24 m", bbox_white=True, fontsize=11)
    return fig


@reg(2025, 13)
def draw_2025_13():
    fig, ax = new_canvas(7.4, 4.0, (0.0, 10.6), (0.2, 5.8))

    # --- Left View: Profile ---
    y_bed = 0.85
    ground_hatch(ax, 0.25, y_bed, 5.25, y_bed, side="below", step=0.28, depth=0.2)

    # Upper concrete headwall (rounded bottom touching top-left of gate, open top with break zigzag)
    hw_l, hw_r = 2.68, 3.30
    hw_bot, hw_top = 2.98, 5.18
    t_b = np.linspace(math.pi, 2.0 * math.pi, 24)
    xb_arc = 0.5 * (hw_l + hw_r) + 0.5 * (hw_r - hw_l) * np.cos(t_b)
    yb_arc = hw_bot + 0.14 * np.sin(t_b)  # gentle downward convex rounded base

    wall_poly_x = np.concatenate([[hw_l], xb_arc, [hw_r, hw_r, hw_l]])
    wall_poly_y = np.concatenate([[hw_top], yb_arc, [hw_bot, hw_top, hw_top]])
    ax.fill(wall_poly_x, wall_poly_y, facecolor=CONCRETE, edgecolor="none", zorder=3)
    ax.plot(np.concatenate([[hw_l], xb_arc, [hw_r]]), np.concatenate([[hw_top], yb_arc, [hw_top]]), color=INK, lw=1.6, zorder=4)

    # Zigzag break line at top of concrete wall
    ax.plot([hw_l - 0.25, hw_l + 0.24, hw_l + 0.30, hw_l + 0.38, hw_l + 0.44, hw_r + 0.25],
            [hw_top, hw_top, hw_top + 0.16, hw_top - 0.14, hw_top, hw_top], color=INK, lw=1.3, zorder=5)

    # Deterministic concrete gravel stipple inside headwall
    rng = np.random.default_rng(202513)
    for idx in range(18):
        cx = hw_l + 0.08 + rng.random() * (hw_r - hw_l - 0.16)
        cy = hw_bot + 0.08 + rng.random() * (hw_top - hw_bot - 0.22)
        if idx % 4 == 0:
            s = 0.055
            ang = rng.random() * 6.28
            tri = np.array([
                [cx + s * math.cos(ang), cy + s * math.sin(ang)],
                [cx + s * math.cos(ang + 2.1), cy + s * math.sin(ang + 2.1)],
                [cx + s * math.cos(ang + 4.2), cy + s * math.sin(ang + 4.2)],
            ])
            ax.add_patch(patches.Polygon(tri, closed=True, facecolor="none", edgecolor=AUX, lw=0.75, zorder=4))
        else:
            ax.plot(cx, cy, marker="o", markersize=1.4, color=AUX, zorder=4)

    # Closed vertical gate with rounded top, diagonal hatch, and protruding semicircular hinge lug
    gx0, gx1 = 3.30, 3.48
    gy_bot, gy_top = y_bed, 2.95
    r_cap = 0.5 * (gx1 - gx0)
    xc_g = 0.5 * (gx0 + gx1)
    yc_cap = gy_top - r_cap
    t_cap = np.linspace(math.pi, 0.0, 20)
    x_cap = xc_g + r_cap * np.cos(t_cap)
    y_cap = yc_cap + r_cap * np.sin(t_cap)

    px, py = 3.54, 1.62  # hinge pin center
    t_lug = np.linspace(0.5 * math.pi, -0.5 * math.pi, 24)
    x_lug = gx1 + 0.16 * np.cos(t_lug)
    y_lug = py + 0.16 * np.sin(t_lug)

    gate_x = np.concatenate([[gx0, gx0], x_cap, [gx1, gx1], x_lug, [gx1, gx1]])
    gate_y = np.concatenate([[gy_bot, yc_cap], y_cap, [yc_cap, py + 0.16], y_lug, [py - 0.16, gy_bot]])
    ax.add_patch(patches.Polygon(np.column_stack([gate_x, gate_y]), closed=True, facecolor="#f1f5f9", edgecolor=INK, lw=1.5, hatch="////", zorder=4.5))
    ax.add_patch(patches.Circle((px, py), 0.065, facecolor="white", edgecolor=INK, lw=1.3, zorder=6))

    # Dashed opened gate rotated ~55 deg clockwise around hinge pin (px, py)
    ang = math.radians(-56.0)
    ca, sa = math.cos(ang), math.sin(ang)
    # Use simplified rounded-end strip slightly shortened at bottom so it clears the bed cleanly
    strip_pts = np.column_stack([
        np.concatenate([[gx0], x_cap, [gx1, gx1], x_cap[::-1]]),
        np.concatenate([[1.02], y_cap, [yc_cap, 1.02], 1.02 - 0.07 * np.sin(t_cap)]),
    ])
    rot_pts = np.array([
        [px + (vx - px) * ca - (vy - py) * sa, py + (vx - px) * sa + (vy - py) * ca]
        for vx, vy in strip_pts
    ])
    ax.add_patch(patches.Polygon(rot_pts, closed=True, facecolor="none", edgecolor=AUX, ls="--", lw=1.25, zorder=3.5))

    # Upstream water surface + H (against left face of concrete headwall)
    y_w = 4.08
    water_surface(ax, 0.35, hw_l, y_w, mark_x=1.05, size=0.21)
    ax.plot([1.85, hw_l], [hw_bot - 0.12, hw_bot - 0.12], color=AUX, lw=0.95, zorder=3)
    dim_arrow(ax, (2.15, hw_bot - 0.12), (2.15, y_w), r"$H$", text_offset=(-0.26, 0.0), fontsize=11.5)

    # --- Right View: Gate Cross-Section ---
    rx0, rx1 = 6.65, 8.30
    ry0, ry1 = 1.45, 3.65  # 1.65 x 2.20 = exact 1.5 : 2.0 aspect ratio
    xc = 0.5 * (rx0 + rx1)
    yc = 0.5 * (ry0 + ry1)
    y00 = 2.08  # hinge axis clearly below centroid c

    ax.add_patch(patches.Rectangle((rx0, ry0), rx1 - rx0, ry1 - ry0, facecolor="white", edgecolor=INK, lw=1.6, zorder=4))

    # Top width 1.5 m
    dim_arrow(ax, (rx0, 4.22), (rx1, 4.22), "1.5 m", ext_len=0.45, ext_dir=(0, -1), fontsize=10.5, text_offset=(0, 0.24))

    # Right height 2.0 m (rotated vertically outside extension lines)
    ax.plot([rx1 + 0.15, 9.25], [ry0, ry0], color=AUX, lw=0.85, zorder=4)
    ax.plot([rx1 + 0.15, 9.25], [ry1, ry1], color=AUX, lw=0.85, zorder=4)
    dim_arrow(ax, (9.02, ry0), (9.02, ry1), "", fontsize=10.5)
    ax.text(9.35, 0.5 * (ry0 + ry1), "2.0 m", ha="center", va="center", rotation=90, fontsize=10.5, color=INK)

    # Centroid dot & label c on LEFT of dot
    ax.plot(xc, yc, marker="o", markersize=4.5, color=INK, zorder=6)
    ax.text(xc - 0.14, yc, r"$c$", ha="right", va="center", fontsize=11.5, color=INK, zorder=6)

    # Hinge axis 0- (dash-dot across gate, '0' ONLY on left side!)
    ax.plot([5.98, 8.75], [y00, y00], ls="-.", color=INK, lw=1.2, zorder=5)
    ax.text(5.86, y00, "0", ha="right", va="center", fontsize=11, color=INK)

    # Opposing U-bracket hinge bearings above/below axis on left & right of gate
    for bx, sgn in ((rx0 - 0.12, -1), (rx1 + 0.12, 1)):
        for dy_b in (0.07, -0.07):
            h_b = 0.11 if dy_b > 0 else -0.11
            ax.plot([bx, bx, bx + sgn * 0.22, bx + sgn * 0.22], [y00 + dy_b, y00 + dy_b + h_b, y00 + dy_b + h_b, y00 + dy_b], color=INK, lw=1.15, zorder=5)

    # Inward vertical arrows on centerline for 0.15 m + rotated '0.15 m' label placed cleanly ABOVE hinge line
    ax.annotate("", xy=(xc, yc + 0.04), xytext=(xc, yc + 0.54), arrowprops=dict(arrowstyle="->", color=INK, lw=1.0), zorder=6)
    ax.annotate("", xy=(xc, y00 - 0.02), xytext=(xc, y00 - 0.48), arrowprops=dict(arrowstyle="->", color=INK, lw=1.0), zorder=6)
    ax.text(xc + 0.26, yc + 0.16, "0.15 m", ha="center", va="center", rotation=90, fontsize=9.8, color=INK, bbox=dict(facecolor="white", edgecolor="none", pad=0.8), zorder=6)

    ax.text(xc, 0.92, "闸门断面", ha="center", va="center", fontsize=11, color=INK)
    return fig


@reg(2025, 15)
def draw_2025_15():
    fig, ax = new_canvas(5.8, 4.0, (0.3, 8.4), (0.2, 5.4))

    # Tank A
    tx0, tx1, ty0, ty1 = 0.75, 4.15, 0.65, 3.05
    y_surf = 2.25
    ax.add_patch(patches.Rectangle((tx0, ty0), tx1 - tx0, y_surf - ty0, facecolor=WATER, edgecolor="none", zorder=1))
    ax.plot([tx0, tx0, tx1, tx1], [ty1, ty0, ty0, ty1], color=INK, lw=2.0, zorder=4)
    water_surface(ax, tx0, tx1, y_surf, mark_x=1.65, size=0.22)
    ax.text(tx0 + 0.42, ty0 + 0.38, r"$A$", ha="center", va="center", fontsize=13, color=INK, zorder=5)

    # Inverted U siphon pipe (white mask + double walls)
    pw = 0.36
    hp = 0.5 * pw
    x_l, x_r = 3.2, 6.75
    y_in = 1.45
    y_top = 3.95
    y_out = 0.55

    # Mask water lines behind left pipe leg
    ax.add_patch(patches.Rectangle((x_l - hp, y_in), pw, y_top - hp - y_in, facecolor="white", edgecolor="none", zorder=3))
    ax.add_patch(patches.Rectangle((x_l - hp, y_top - hp), (x_r - x_l) + pw, pw, facecolor="white", edgecolor="none", zorder=3))
    ax.add_patch(patches.Rectangle((x_r - hp, y_out), pw, y_top - hp - y_out, facecolor="white", edgecolor="none", zorder=3))

    # Outer & inner walls
    ax.plot([x_l - hp, x_l - hp, x_r + hp, x_r + hp], [y_in, y_top + hp, y_top + hp, y_out], color=INK, lw=1.7, zorder=5)
    ax.plot([x_l + hp, x_l + hp, x_r - hp, x_r - hp], [y_in, y_top - hp, y_top - hp, y_out], color=INK, lw=1.7, zorder=5)
    ax.text(0.5 * (x_l + x_r), y_top + hp + 0.18, r"$B$", ha="center", va="bottom", fontsize=12.5, color=INK)

    # Dashed reference lines (water surface, top pipe axis, outlet)
    ax.plot([x_l + hp, x_r - hp], [y_surf, y_surf], ls="--", color=AUX, lw=1.0, zorder=4)
    ax.plot([4.5, x_r - hp], [y_top, y_top], ls="--", color=AUX, lw=0.9, zorder=4)
    ax.plot([4.5, x_r - hp], [y_out, y_out], ls="--", color=AUX, lw=0.9, zorder=4)

    # Two 1 m dimensions
    dim_arrow(ax, (5.1, y_surf), (5.1, y_top), "1 m", bbox_white=True, fontsize=11)
    dim_arrow(ax, (5.1, y_out), (5.1, y_surf), "1 m", bbox_white=True, fontsize=11)
    return fig


@reg(2025, 16)
def draw_2025_16():
    fig, ax = new_canvas(6.8, 4.2, (0.0, 10.0), (0.2, 6.0))

    # Bottom datum line
    y0 = 0.55
    ax.plot([0.85, 9.6], [y0, y0], color=INK, lw=1.3, zorder=3)

    # Reservoir B (left, open on left side as in original)
    bx0, bx1, by0, by1 = 1.45, 3.05, 2.55, 5.45
    yb_s = 5.05
    ax.plot([bx0, bx1, bx1], [by0, by0, by1], color=INK, lw=1.6, zorder=4)
    water_surface(ax, bx0, bx1, yb_s, mark_x=0.5 * (bx0 + bx1), size=0.20, lw=1.4)
    ax.text(0.5 * (bx0 + bx1), 3.65, r"$B$", ha="center", va="center", fontsize=13, color=INK)
    ax.plot([0.85, bx0], [yb_s, yb_s], color=AUX, lw=0.95, zorder=3)
    dim_arrow(ax, (1.10, y0), (1.10, yb_s), "", fontsize=10.5)
    ax.text(0.76, 0.5 * (y0 + yb_s), "120 m", ha="center", va="center", rotation=90, fontsize=11, color=INK)

    # Reservoir A (upper right, with water surface line extending rightward)
    ax0, ax1, ay0, ay1 = 7.05, 8.05, 3.05, 4.25
    ya_s = 3.88
    ax.plot([ax0, ax0, ax1, ax1], [ay1, ay0, ay0, ay1], color=INK, lw=1.6, zorder=4)
    water_surface(ax, ax0, ax1, ya_s, mark_x=0.5 * (ax0 + ax1), size=0.18, lw=1.4)
    ax.plot([ax1, 9.55], [ya_s, ya_s], color=INK, lw=1.1, zorder=3)
    ax.text(0.5 * (ax0 + ax1), 3.40, r"$A$", ha="center", va="center", fontsize=12, color=INK)

    # Reservoir C (lower right)
    cx0, cx1, cy0, cy1 = 7.55, 8.85, 0.55, 2.45
    yc_s = 2.02
    ax.plot([cx0, cx0, cx1, cx1], [cy1, cy0, cy0, cy1], color=INK, lw=1.6, zorder=4)
    water_surface(ax, cx0, cx1, yc_s, mark_x=0.5 * (cx0 + cx1), size=0.19, lw=1.4)
    ax.text(0.5 * (cx0 + cx1), 1.15, r"$C$", ha="center", va="center", fontsize=13, color=INK)
    ax.plot([cx1, 9.55], [yc_s, yc_s], color=AUX, lw=0.95, zorder=3)
    dim_arrow(ax, (9.35, y0), (9.35, yc_s), "", fontsize=10.5)
    ax.text(9.05, 0.5 * (y0 + yc_s), "105 m", ha="center", va="center", rotation=90, fontsize=10.5, color=INK)

    # Y-junction pipes (CRITICAL: preserve original schematic arrow directions:
    # Q2: B -> J; Q1: J -> A (pointing RIGHT-UP toward A!); Q3: J -> C)
    jx, jy = 4.75, 2.85
    pipes = [
        ((bx1, 3.35), (jx, jy), (0.32, 0.68), r"$Q_2$", (0.0, 0.36), +1),   # B -> J
        ((jx, jy), (ax0, 3.55), (0.32, 0.68), r"$Q_1$", (0.12, -0.34), -1), # J -> A (FIXED!)
        ((jx, jy), (cx0, 1.25), (0.32, 0.68), r"$Q_3$", (-0.28, -0.28), -1),# J -> C
    ]
    for p0, p1, (t0, t1), lbl, loff, side_sgn in pipes:
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L * 0.08, dx / L * 0.08
        poly = np.array([
            [p0[0] + nx, p0[1] + ny],
            [p1[0] + nx, p1[1] + ny],
            [p1[0] - nx, p1[1] - ny],
            [p0[0] - nx, p0[1] - ny],
        ])
        ax.add_patch(patches.Polygon(poly, closed=True, facecolor="white", edgecolor="none", zorder=4.5))
        ax.plot([p0[0] + nx, p1[0] + nx], [p0[1] + ny, p1[1] + ny], color=INK, lw=1.4, zorder=5)
        ax.plot([p0[0] - nx, p1[0] - nx], [p0[1] - ny, p1[1] - ny], color=INK, lw=1.4, zorder=5)

        ap0 = (p0[0] + t0 * dx + side_sgn * nx * 3.2, p0[1] + t0 * dy + side_sgn * ny * 3.2)
        ap1 = (p0[0] + t1 * dx + side_sgn * nx * 3.2, p0[1] + t1 * dy + side_sgn * ny * 3.2)
        flow_arrow(ax, ap0, ap1, lbl, text_offset=loff, fontsize=11.5, lw=1.3)

    # Clean Y-junction mask (seamless three-way merge without an extra circle)
    ax.add_patch(patches.Circle((jx, jy), 0.075, facecolor="white", edgecolor="none", zorder=5.2))
    return fig


@reg(2025, 18)
def draw_2025_18():
    fig, ax = new_canvas(6.4, 4.0, (0.3, 9.5), (0.3, 5.4))

    # Horizontal converging pipe (NO flow direction arrow!)
    y_c = 4.35
    r1, r2 = 0.56, 0.28
    x0, x1, x2, x3 = 0.8, 4.3, 5.3, 9.0
    # Pipe outline
    ax.plot([x0, x1, x2, x3], [y_c + r1, y_c + r1, y_c + r2, y_c + r2], color=INK, lw=1.8, zorder=5)

    # Bottom wall broken for manometer taps
    xt1, xt2, tw = 2.0, 7.6, 0.22
    htw = 0.5 * tw
    ax.plot([x0, xt1 - htw], [y_c - r1, y_c - r1], color=INK, lw=1.8, zorder=5)
    ax.plot([xt1 + htw, x1, x2, xt2 - htw], [y_c - r1, y_c - r1, y_c - r2, y_c - r2], color=INK, lw=1.8, zorder=5)
    ax.plot([xt2 + htw, x3], [y_c - r2, y_c - r2], color=INK, lw=1.8, zorder=5)

    # Pipe diameters d1, d2
    dim_arrow(ax, (1.35, y_c - r1), (1.35, y_c + r1), r"$d_1$", text_offset=(-0.25, 0.0), fontsize=11.5)
    # External opposing arrows for d2
    ax.annotate("", xy=(6.45, y_c + r2), xytext=(6.45, y_c + r2 + 0.48), arrowprops=dict(arrowstyle="->", color=INK, lw=1.1))
    ax.annotate("", xy=(6.45, y_c - r2), xytext=(6.45, y_c - r2 - 0.48), arrowprops=dict(arrowstyle="->", color=INK, lw=1.1))
    ax.text(6.65, y_c + r2 + 0.28, r"$d_2$", ha="left", va="center", fontsize=11.5, color=INK)

    # U-tube mercury differential manometer (right meniscus HIGHER than left!)
    y_bot = 0.85
    ym1, ym2 = 1.65, 2.55
    # Mercury fills
    ax.add_patch(patches.Rectangle((xt1 - htw, y_bot - htw), (xt2 - xt1) + tw, tw, facecolor="#94a3b8", edgecolor="none", zorder=2))
    ax.add_patch(patches.Rectangle((xt1 - htw, y_bot - htw), tw, ym1 - (y_bot - htw), facecolor="#94a3b8", edgecolor="none", zorder=2))
    ax.add_patch(patches.Rectangle((xt2 - htw, y_bot - htw), tw, ym2 - (y_bot - htw), facecolor="#94a3b8", edgecolor="none", zorder=2))
    # Tube walls
    ax.plot([xt1 - htw, xt1 - htw, xt2 + htw, xt2 + htw], [y_c - r1, y_bot - htw, y_bot - htw, y_c - r2], color=INK, lw=1.6, zorder=5)
    ax.plot([xt1 + htw, xt1 + htw, xt2 - htw, xt2 - htw], [y_c - r1, y_bot + htw, y_bot + htw, y_c - r2], color=INK, lw=1.6, zorder=5)
    ax.plot([xt1 - htw, xt1 + htw], [ym1, ym1], color=INK, lw=1.3, zorder=5)
    ax.plot([xt2 - htw, xt2 + htw], [ym2, ym2], color=INK, lw=1.3, zorder=5)

    # Delta h between ym1 and ym2
    ax.plot([xt1 + htw, 5.2], [ym1, ym1], ls="--", color=AUX, lw=0.95, zorder=3)
    ax.plot([4.6, xt2 - htw], [ym2, ym2], ls="--", color=AUX, lw=0.95, zorder=3)
    dim_arrow(ax, (4.9, ym1), (4.9, ym2), r"$\Delta h$", bbox_white=True, fontsize=11.5)

    # rho_m leader
    ax.annotate(
        r"$\rho_m$",
        xy=(xt2 + htw, 1.95),
        xytext=(8.45, 2.25),
        ha="left",
        va="center",
        fontsize=12,
        color=INK,
        arrowprops=dict(arrowstyle="-", color=AUX, lw=0.95),
    )
    return fig


@reg(2025, 21)
def draw_2025_21():
    fig, ax = new_canvas(5.4, 4.2, (0.4, 7.6), (0.2, 5.5))
    xc = 4.0
    rp = 0.72
    y_bot, y_neck = 0.55, 2.32
    # Flared nozzle outer walls at +-35 deg from vertical, leaving generous annular channel around +-30 deg cone
    flare_h = 2.25
    dx_f = flare_h * math.tan(math.radians(35.0))
    ax.plot([xc - rp, xc - rp, xc - rp - dx_f], [y_bot, y_neck, y_neck + flare_h], color=INK, lw=1.8, zorder=4)
    ax.plot([xc + rp, xc + rp, xc + rp + dx_f], [y_bot, y_neck, y_neck + flare_h], color=INK, lw=1.8, zorder=4)

    # Inverted cone centered on axis (apex angle 60 deg)
    y_apex = 2.25
    cone_h = 2.18
    half_base = cone_h * math.tan(math.radians(30.0))
    cone = np.array([[xc, y_apex], [xc - half_base, y_apex + cone_h], [xc + half_base, y_apex + cone_h]])
    ax.add_patch(patches.Polygon(cone, closed=True, facecolor="white", edgecolor=INK, lw=1.7, zorder=5))

    # Vertical dash-dot centerline
    ax.plot([xc, xc], [0.35, 5.1], ls="-.", color=AUX, lw=1.1, zorder=6)

    # Cone apex angle theta (placed slightly right of centerline inside angle arc, clear of dashed axis)
    angle_arc(ax, (xc, y_apex), 60.0, 120.0, radius=0.92, label="", fontsize=11.5)
    ax.text(xc + 0.22, y_apex + 1.24, r"$\theta$", ha="center", va="center", fontsize=12, color=INK, zorder=8)

    # Pipe diameter d leader
    ax.plot([xc + 0.16, xc + 1.18], [1.45, 1.92], color=AUX, lw=1.0, zorder=5)
    ax.text(xc + 1.26, 1.95, r"$d$", ha="left", va="center", fontsize=12, color=INK)

    # Pipe flow arrow Q (Q placed to the right of upward arrow)
    flow_arrow(ax, (xc, 0.72), (xc, 1.62), r"$Q$", text_offset=(0.24, -0.18), fontsize=12, lw=1.6)

    # Outflow arrows strictly INSIDE the center of the left & right annular channels!
    # At y=3.05..4.15: channel center lies halfway between cone flank (at 30 deg) and outer flared wall (at 35 deg)
    for sgn in (-1.0, 1.0):
        y_a0, y_a1 = 3.00, 4.15
        x_c0 = (y_a0 - y_apex) * math.tan(math.radians(30.0))
        x_w0 = rp + (y_a0 - y_neck) * math.tan(math.radians(35.0))
        x_c1 = (y_a1 - y_apex) * math.tan(math.radians(30.0))
        x_w1 = rp + (y_a1 - y_neck) * math.tan(math.radians(35.0))
        ax.annotate(
            "",
            xy=(xc + sgn * 0.5 * (x_c1 + x_w1), y_a1),
            xytext=(xc + sgn * 0.5 * (x_c0 + x_w0), y_a0),
            arrowprops=dict(arrowstyle="->", color=INK, lw=1.5),
            zorder=6,
        )
    for txt in ax.texts:
        txt.set_zorder(8)
    return fig


@reg(2025, 27)
def draw_2025_27():
    fig, ax = new_canvas(6.4, 4.4, (0.3, 9.5), (-0.05, 6.1))
    # Tank interior: right=7.15, top=4.95, bot=2.35, center of arc O-B at (3.70, 3.65), R=1.30
    x_c, y_c = 3.70, 3.65
    R = 1.30
    x_B, y_B = x_c - R, y_c        # (2.40, 3.65)
    x_O, y_O = x_c, y_c + R        # (3.70, 4.95)
    x_R, y_bot = 7.15, 2.35
    wt = 0.28  # wall thickness

    # Compact U-tube tap near right end of tank bottom; right leg sits just outside right outer wall
    xt = 6.72
    htw = 0.14
    x_m2 = 7.78
    y_mb = 0.42
    y_mid = 0.85  # horizontal boundary inside U-tube separating lower gray layer & upper black layer!
    y_m1 = 1.25   # top of black layer in left leg (aligned with bottom of left 'h' and bottom of right 'Delta h')
    y_m2 = 2.18   # top of black layer in right leg (aligned with top of right 'Delta h')
    y_m_top = 3.65

    # 1) Tank upper & lower liquid fills + U-tube two-layer fills:
    #    - Oil (light yellow OIL) in upper chamber bounded by 90-deg arc OB and y = y_B
    ang = np.linspace(0.5 * math.pi, math.pi, 60)
    arc_x = x_c + R * np.cos(ang)
    arc_y = y_c + R * np.sin(ang)
    oil_poly = np.column_stack([
        np.concatenate([arc_x, [x_B, x_R, x_R, x_O]]),
        np.concatenate([arc_y, [y_B, y_B, y_O, y_O]]),
    ])
    ax.add_patch(patches.Polygon(oil_poly, closed=True, facecolor=OIL, edgecolor="none", zorder=1.2))

    #    - Water (light blue WATER) in lower chamber AND extending down left manometer leg to y_m1
    ax.add_patch(patches.Rectangle((x_B, y_bot), x_R - x_B, y_B - y_bot, facecolor=WATER, edgecolor="none", zorder=1.2))
    ax.add_patch(patches.Rectangle((xt - htw, y_m1), 2 * htw, y_bot - y_m1, facecolor=WATER, edgecolor="none", zorder=1.2))

    #    - U-tube LOWER liquid layer (medium-dark gray #6b7280): bottom U-bend + both legs up to y_mid
    u_gray = "#6b7280"
    u_black = "#0f172a"
    ax.add_patch(patches.Rectangle((xt - htw, y_mb - htw), (x_m2 - xt) + 2 * htw, 2 * htw, facecolor=u_gray, edgecolor="none", zorder=1.8))
    ax.add_patch(patches.Rectangle((xt - htw, y_mb - htw), 2 * htw, y_mid - (y_mb - htw), facecolor=u_gray, edgecolor="none", zorder=1.8))
    ax.add_patch(patches.Rectangle((x_m2 - htw, y_mb - htw), 2 * htw, y_mid - (y_mb - htw), facecolor=u_gray, edgecolor="none", zorder=1.8))

    #    - U-tube UPPER liquid layer (solid dark black #0f172a): left leg y_mid..y_m1, right leg y_mid..y_m2
    ax.add_patch(patches.Rectangle((xt - htw, y_mid), 2 * htw, y_m1 - y_mid, facecolor=u_black, edgecolor="none", zorder=1.9))
    ax.add_patch(patches.Rectangle((x_m2 - htw, y_mid), 2 * htw, y_m2 - y_mid, facecolor=u_black, edgecolor="none", zorder=1.9))

    # 2) Outer hatched concrete tank walls
    wall_polys = [
        np.array([
            [x_O, y_O], [x_R, y_O], [x_R, y_bot], [xt + htw, y_bot],
            [xt + htw, y_bot - wt], [x_R + wt, y_bot - wt], [x_R + wt, y_O + wt], [x_O, y_O + wt],
        ]),
        np.array([
            [x_B, y_B], [x_B - wt, y_B], [x_B - wt, y_bot - wt], [xt - htw, y_bot - wt],
            [xt - htw, y_bot], [x_B, y_bot],
        ]),
    ]
    for wp in wall_polys:
        ax.add_patch(patches.Polygon(wp, closed=True, facecolor=CONCRETE, edgecolor=INK, lw=1.4, hatch="////", zorder=3))

    # 3) 90-deg circular arc gate OB, hinge O, point B, force F
    ax.plot(arc_x, arc_y, color=INK, lw=2.0, zorder=5)
    ax.add_patch(patches.Circle((x_O, y_O), 0.07, facecolor="white", edgecolor=INK, lw=1.4, zorder=6))
    ax.text(x_O - 0.04, y_O + 0.34, r"$O$", ha="center", va="bottom", fontsize=12, color=INK)
    ax.text(x_B + 0.14, y_B + 0.14, r"$B$", ha="left", va="bottom", fontsize=12, color=INK)
    flow_arrow(ax, (1.20, y_B), (x_B - 0.04, y_B), r"$F$", text_offset=(-0.72, 0.0), fontsize=12, lw=1.7)

    # 4) Oil-Water interface, medium labels, top liquid level symbol, and water thickness h
    ax.plot([x_B, x_R], [y_B, y_B], color=INK, lw=1.4, zorder=4)
    ax.text(4.95, 4.25, "油", ha="center", va="center", fontsize=13, color=INK, zorder=5)
    ax.text(4.95, 2.98, "水", ha="center", va="center", fontsize=13, color=INK, zorder=5)
    water_surface(ax, 5.45, 5.95, y_O - 0.22, mark_x=5.7, size=0.18, lw=0.0)
    dim_arrow(ax, (6.05, y_bot), (6.05, y_B), r"$h$", text_offset=(-0.22, 0.0), fontsize=11.5)

    # 5) U-tube walls, clear interface lines, and dimensions h (below tank bottom) & Delta h
    ax.plot([xt - htw, xt - htw, x_m2 + htw, x_m2 + htw], [y_bot - wt, y_mb - htw, y_mb - htw, y_m_top], color=INK, lw=1.5, zorder=5)
    ax.plot([xt + htw, xt + htw, x_m2 - htw, x_m2 - htw], [y_bot - wt, y_mb + htw, y_mb + htw, y_m_top], color=INK, lw=1.5, zorder=5)
    ax.plot([xt - htw, xt + htw], [y_mid, y_mid], color="white", lw=0.8, zorder=5)
    ax.plot([x_m2 - htw, x_m2 + htw], [y_mid, y_mid], color="white", lw=0.8, zorder=5)
    ax.plot([xt - htw, xt + htw], [y_m1, y_m1], color=INK, lw=1.3, zorder=5)
    ax.plot([x_m2 - htw, x_m2 + htw], [y_m2, y_m2], color=INK, lw=1.3, zorder=5)

    y_tank_outer_bot = y_bot - wt
    ax.plot([5.82, xt - htw], [y_tank_outer_bot, y_tank_outer_bot], ls="--", color=AUX, lw=0.9, zorder=3)
    ax.plot([5.82, xt - htw], [y_m1, y_m1], ls="--", color=AUX, lw=0.9, zorder=3)
    dim_arrow(ax, (6.05, y_m1), (6.05, y_tank_outer_bot), r"$h$", text_offset=(-0.24, 0.0), fontsize=11.5)

    ax.plot([x_m2 + htw, 8.75], [y_m1, y_m1], ls="--", color=AUX, lw=0.9, zorder=3)
    ax.plot([x_m2 + htw, 8.75], [y_m2, y_m2], ls="--", color=AUX, lw=0.9, zorder=3)
    dim_arrow(ax, (8.45, y_m1), (8.45, y_m2), r"$\Delta h$", text_offset=(0.36, 0.0), fontsize=11.5)
    return fig


@reg(2025, 28)
def draw_2025_28():
    fig, ax = new_canvas(6.4, 3.8, (0.2, 9.6), (0.2, 5.4))
    y_bed = 1.05
    ground_hatch(ax, 0.4, y_bed, 9.2, y_bed, side="below", step=0.30, depth=0.22)

    # Practical weir profile: vertical front at x=2.6, rounded crest (2.6..3.2), smooth S-ogee down to (7.3, y_bed)
    t_arc = np.linspace(math.pi, 0.5 * math.pi, 24)
    x_crest = 2.95 + 0.35 * np.cos(t_arc)
    y_crest = 3.25 + 0.35 * np.sin(t_arc)  # crest peak at y=3.60

    s = np.linspace(0.0, 1.0, 70)
    # Smooth cubic-like S-curve from (2.95, 3.60) to (7.3, y_bed) with zero slope at both ends
    x_ogee = 2.95 + (7.3 - 2.95) * s
    y_ogee = 3.60 - (3.60 - y_bed) * (3 * s**2 - 2 * s**3)

    weir_x = np.concatenate([[2.6, 2.6], x_crest, x_ogee[1:]])
    weir_y = np.concatenate([[y_bed, 3.25], y_crest, y_ogee[1:]])
    ax.plot(weir_x, weir_y, color=INK, lw=2.0, zorder=5)

    # Interior boundary hatch ticks along weir inside edge (matching original textbook look)
    for idx in range(1, len(weir_x) - 1, 4):
        dx = weir_x[idx + 1] - weir_x[idx - 1]
        dy = weir_y[idx + 1] - weir_y[idx - 1]
        L = max(1e-6, math.hypot(dx, dy))
        tx, ty = dx / L, dy / L
        # Inward normal (pointing right/down into weir body)
        nx, ny = ty, -tx
        ax.plot(
            [weir_x[idx], weir_x[idx] + 0.14 * nx - 0.08 * tx],
            [weir_y[idx], weir_y[idx] + 0.14 * ny - 0.08 * ty],
            color=AUX,
            lw=0.85,
            zorder=4,
        )

    # Upstream water surface + nappe flowing smoothly over weir to contracted section c-c
    y_w_up = 4.4
    xs_nappe = np.linspace(1.2, 8.7, 120)
    ys_nappe = np.where(
        xs_nappe <= 2.95,
        y_w_up - 0.12 * np.exp((xs_nappe - 2.95) * 1.4),
        np.where(
            xs_nappe <= 7.3,
            3.60 - (3.60 - y_bed) * (3 * ((xs_nappe - 2.95) / (7.3 - 2.95)) ** 2 - 2 * ((xs_nappe - 2.95) / (7.3 - 2.95)) ** 3)
            + 0.68 * (1.0 - 0.45 * ((xs_nappe - 2.95) / (7.3 - 2.95))),
            y_bed + 0.37,
        ),
    )
    ax.plot(xs_nappe, ys_nappe, color=INK, lw=1.7, zorder=5)
    water_surface(ax, 0.7, 1.5, y_w_up, mark_x=0.95, size=0.22, lw=0.0)
    ax.plot([0.7, 1.3], [y_w_up, y_w_up], color=INK, lw=1.7, zorder=5)

    # Dimensions P and H on left
    ax.plot([1.6, 2.95], [3.60, 3.60], ls="--", color=AUX, lw=0.9, zorder=3)
    dim_arrow(ax, (1.85, y_bed), (1.85, 3.60), r"$P$", text_offset=(-0.24, 0.0), fontsize=12)
    dim_arrow(ax, (1.85, 3.60), (1.85, y_w_up), r"$H$", text_offset=(-0.24, 0.0), fontsize=12)

    # Contracted section c - c arrows
    xc_sec = 7.95
    yc_top = y_bed + 0.37
    ax.annotate("", xy=(xc_sec, yc_top + 0.02), xytext=(xc_sec, yc_top + 0.55), arrowprops=dict(arrowstyle="->", color=INK, lw=1.3))
    ax.text(xc_sec, yc_top + 0.60, r"$c$", ha="center", va="bottom", fontsize=11.5, color=INK)
    ax.annotate("", xy=(xc_sec, y_bed - 0.02), xytext=(xc_sec, y_bed - 0.55), arrowprops=dict(arrowstyle="->", color=INK, lw=1.3))
    ax.text(xc_sec, y_bed - 0.58, r"$c$", ha="center", va="top", fontsize=11.5, color=INK)
    return fig


@reg(2025, 30)
def draw_2025_30():
    # Strictly NO water surface curve H2/S2 or hk/h02 spoiler!
    fig, ax = new_canvas(6.8, 3.4, (0.2, 9.8), (0.3, 4.8))

    # Left rounded reservoir inlet wall + horizontal bed i1 + sloped bed i2
    x_in, x_brk, x_end = 2.2, 5.4, 9.4
    y1 = 2.65
    y2_end = 2.05

    # Curved intake wall on left (smooth quarter-ellipse down-left)
    t = np.linspace(0.5 * math.pi, math.pi, 40)
    x_curve = x_in + 1.45 * np.cos(t)
    y_curve = (y1 - 1.35) + 1.35 * np.sin(t)
    ax.plot(x_curve, y_curve, color=INK, lw=1.7, zorder=4)

    ground_hatch(ax, x_in, y1, x_brk, y1, side="below", step=0.48, depth=0.22)
    ground_hatch(ax, x_brk, y1, x_end, y2_end, side="below", step=0.48, depth=0.22)

    # Upstream reservoir free water surface
    water_surface(ax, 0.55, 2.25, 3.85, mark_x=1.45, size=0.22)

    # Vertical dashed line at break-in-slope
    ax.plot([x_brk, x_brk], [y1, 4.35], ls="--", color=INK, lw=1.1, zorder=4)

    # Parallel dash-dot reference line above bed (no text label, faithful to original)
    dy_ref = 0.58
    ax.plot([1.85, x_brk, x_end], [y1 + dy_ref, y1 + dy_ref, y2_end + dy_ref], ls="-.", color=INK, lw=1.2, zorder=4)

    # Slope labels i1, i2
    ax.text(3.8, y1 - 0.45, r"$i_1$", ha="center", va="top", fontsize=12, color=INK)
    ax.text(7.4, 0.5 * (y1 + y2_end) - 0.45, r"$i_2$", ha="center", va="top", fontsize=12, color=INK)
    return fig


# ==============================================================================
# Runner + CLI + Parallel Execution + Before/After QA Builder
# ==============================================================================


def _render_one(task: tuple[int, int]) -> tuple[int, int, str, str]:
    year, no = task
    stem = f"q{no:02d}_orig"
    fig = REGISTRY[(year, no)]()
    png_p, webp_p = backup_and_save(fig, "hhu-814", year, stem, ROOT)
    return year, no, str(png_p), str(webp_p)


def main() -> int:
    ap = argparse.ArgumentParser(description="Batch redraw all 12 HHU 814 (2025) original exam figures.")
    ap.add_argument("--only", default="", help="Comma-separated year:no pairs, e.g. 2025:8,2025:27")
    ap.add_argument("--workers", type=int, default=4, help="Parallel worker processes (default 4)")
    ap.add_argument("--qa-dir", default="", help="Optional directory to output Before/After QA sheets")
    args = ap.parse_args()

    if args.only:
        tasks = []
        for tok in args.only.split(","):
            tok = tok.strip()
            if not tok:
                continue
            y_s, n_s = tok.split(":")
            key = (int(y_s), int(n_s))
            if key not in REGISTRY:
                raise SystemExit(f"Unknown figure key: {key}")
            tasks.append(key)
    else:
        tasks = sorted(REGISTRY.keys())

    print(f"Rendering {len(tasks)} figures with workers={args.workers} ...")
    if args.workers > 1 and len(tasks) > 1:
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
            for yr, no, _png_s, webp_s in pool.map(_render_one, tasks):
                print(f"  [OK] {yr} Q{no:02d} -> {Path(webp_s).name}")
    else:
        for t in tasks:
            yr, no, _png_s, webp_s = _render_one(t)
            print(f"  [OK] {yr} Q{no:02d} -> {Path(webp_s).name}")

    if args.qa_dir:
        qa_dir = Path(args.qa_dir)
        pairs = []
        for yr, no in tasks:
            stem = f"q{no:02d}_orig"
            bak_p = ROOT / "assets_src" / "handdrawn_backup" / "hhu-814" / str(yr) / f"{stem}.webp"
            new_p = ROOT / "web" / "public" / "data" / "hhu-814" / "figures" / str(yr) / f"{stem}.webp"
            pairs.append((f"{yr} Q{no:02d} ({stem})", bak_p, new_p))
        sheets = build_qa_sheets(pairs, qa_dir, prefix="qa", pairs_per_sheet=4)
        print(f"Generated {len(sheets)} QA sheets:")
        for sp in sheets:
            print(f"  {sp}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
