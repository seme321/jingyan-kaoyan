# -*- coding: utf-8 -*-
"""
Parse Hohai University 814 Hydraulics exam .docx files for years 2015, 2014, 2013:
  - `河海大学已整理真题/2015年河海大学814《水力学》考研真题及详细解析.docx`
  - `河海大学已整理真题/2014年河海大学814《水力学》考研真题及详细解析.docx`
  - `河海大学已整理真题/2013年河海大学814《水力学》考研真题及详细解析.docx`

Outputs:
  1. Standardized exam packs:
     `河海大学已整理数据/{2015,2014,2013}/{year}.json` + `figures/*.png`
  2. Web-ready JSONs & WebP figures (PIL quality=90, method=5):
     `web/public/data/hhu-814/{2015,2014,2013}.json`
     `web/public/data/hhu-814/figures/{2015,2014,2013}/*.webp`

Key physics & diagram verifications/corrections included:
  - 2015 Q04 (Judge #4): Accurate sudden-expansion & submerged-exit HGL/EGL analysis + redrawn sol diagram.
  - 2015 Q09 (Judge #9): Fixed answer from True (√) to False (×) — in a wide-shallow rectangular channel,
    hc ~ q^(2/3) grows faster than h0 ~ q^(3/5) (ic = g*n^2/hc^(1/3) decreases with Q), so supercritical
    uniform flow (h0 < hc, i > ic) remains supercritical when Q increases and cannot turn subcritical.
  - 2015 Q27 (Calc #2): Redrawn clean pressure-body decomposition diagram showing overhang virtual region.
  - 2015 Q29 (Calc #4): Unified control-volume reaction sign convention (Rx leftward, Ry downward -> F = 3.569 kN).
  - 2015 Q30 (Calc #5): Fixed intermediate coefficient rounding (1.1312 * b^(8/3) = 5 -> b = 1.746 m, h0 = 1.512 m).
  - 2014 Q27 (Calc #2): Fixed vertical pressure body & resultant direction in both (a) and (b) — fluid is INSIDE
    the tank beneath convex quarter-circle plate AB, so Pz is a virtual pressure body acting UPWARD (not downward!)
    and resultant P points UPWARD-RIGHT (41.5° in (a), 41.0° in (b)), passing through center O; redrawn sol diagram.
  - 2014 Q29 (Calc #4): Redrawn control-volume diagram fixing erroneous velocity labels (v1=1.031 m/s, v2=2.320 m/s).
  - 2014 Q31 (Calc #6): Redrawn three-slope water surface profile fixing h02''=0.945 m and smooth S1 curve.
  - 2013 Q32 (Calc #2): Fixed moment direction labels about bottom hinge O and redrawn diagram with G at true L/2.
  - 2013 Q33 (Calc #3): Cropped out third-party video note at bottom of q33_orig.png and redrawn clean q33_sol.png.
  - 2013 Q34 (Calc #4): Redrawn three-slope water surface profile with physically smooth S1 backwater curve.
"""

import copy
import io
import json
import math
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, FancyArrowPatch, Polygon, Rectangle, Circle
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parse_2024_2025 as base_parser

base_parser.GREEK_AND_MATH_MAP.update({
    "κ": r"\kappa ",
    "∑": r"\sum ",
    "∈": r"\in ",
    "Φ": r"\Phi ",
    "Ω": r"\Omega ",
    "∞": r"\infty ",
    "–": "-",
    "∫": r"\int ",
})

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "河海大学已整理真题"
STD_ROOT = ROOT / "河海大学已整理数据"
WEB_COURSE_DIR = ROOT / "web" / "public" / "data" / "hhu-814"


# ==============================================================================
# Curated Metadata: 2015 (Q1 - Q31)
# ==============================================================================
META_2015 = {
    1:  {"title": "达西公式圆管形式对明渠水流的适用性辨析", "chapter": 4, "kps": ["达西-韦斯巴赫公式", "沿程水头损失规律"], "method": "概念偷换词辨析", "difficulty": 1},
    2:  {"title": "流体黏性与层流紊流流态划分的前提条件", "chapter": 4, "kps": ["雷诺数与流态判别", "理想液体假设"], "method": "物理概念定义辨析", "difficulty": 1},
    3:  {"title": "虹吸管最高点动水压强与大气压大小比较", "chapter": 6, "kps": ["虹吸管水力计算", "真空高度(真空度)"], "method": "两段伯努利方程联立法", "difficulty": 1},
    4:  {"title": "变径短管总水头线与测压管水头线定性判别", "chapter": 6, "kps": ["总水头线与测压管水头线", "恒定总流能量方程"], "method": "总水头线与测压管水头线判据", "difficulty": 2},
    5:  {"title": "有压管道直接水击的阀门关闭时间判据", "chapter": 6, "kps": ["有压管道水击(水锤)", "直接与间接水击判别"], "method": "水击相长判别与儒氏公式", "difficulty": 1},
    6:  {"title": "紊流光滑区沿程阻力系数随雷诺数变化规律", "chapter": 4, "kps": ["紊流阻力分区", "达西-韦斯巴赫公式"], "method": "紊流光滑区布拉休斯幂次比例法", "difficulty": 1},
    7:  {"title": "圆管抛物线流速分布对应的流态判别", "chapter": 4, "kps": ["圆管层流哈根-泊肃叶定律", "断面流速分布"], "method": "物理概念定义辨析", "difficulty": 1},
    8:  {"title": "明渠壅水曲线水深增大与水面高程变化辨析", "chapter": 8, "kps": ["明渠水面曲线定性分析", "明渠渐变流基本微分方程"], "method": "渐变流微分方程符号判别", "difficulty": 3},
    9:  {"title": "宽浅矩形渠道均匀急流随流量增大的流态演变判别", "chapter": 8, "kps": ["临界水深与临界底坡", "明渠均匀流曼宁公式", "弗劳德数判急缓流"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 3},
    10: {"title": "矩形明渠缓流越过渠底障碍物的水面变化规律", "chapter": 8, "kps": ["断面单位能量(比能)", "弗劳德数判急缓流"], "method": "比能沿程导数判别法", "difficulty": 2},
    11: {"title": "平衡液体等压面与质量力的正交性质", "chapter": 2, "kps": ["静水压强基本方程"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "blank"},
    12: {"title": "水泵吸水管真空水柱高换算绝对压强", "chapter": 2, "kps": ["真空高度(真空度)", "静水压强基本方程"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "mini-calc"},
    13: {"title": "有压管道突然缩小处测压管水头线沿程变化", "chapter": 6, "kps": ["总水头线与测压管水头线", "恒定总流能量方程"], "method": "总水头线与测压管水头线判据", "difficulty": 1, "subType": "blank"},
    14: {"title": "压力表指针摆动反映的紊流脉动性特征", "chapter": 4, "kps": ["雷诺数与流态判别"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "blank"},
    15: {"title": "文丘里流量计流量公式的理论推导依据", "chapter": 3, "kps": ["恒定总流连续性方程", "恒定总流能量方程"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "blank"},
    16: {"title": "渠道断面设计糙率取值偏小引起的输水后果", "chapter": 7, "kps": ["明渠均匀流曼宁公式"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 2, "subType": "short-answer"},
    17: {"title": "重力相似准则水力模型流速比尺换算", "chapter": 13, "kps": ["弗劳德相似准则"], "method": "弗劳德比尺幂次换算法", "difficulty": 1, "subType": "mini-calc"},
    18: {"title": "铅直正方形平面由压心偏心距反算顶边淹深", "chapter": 2, "kps": ["平面静水总压力"], "method": "平面总压力形心法/分块合成法", "difficulty": 2, "subType": "mini-calc"},
    19: {"title": "铅直矩形挡水板斜分梯形与三角形静水总压力之比", "chapter": 2, "kps": ["平面静水总压力"], "method": "平面总压力形心法/分块合成法", "difficulty": 2, "subType": "mini-calc"},
    20: {"title": "阻力平方区串联长管水头增大后的流量换算", "chapter": 6, "kps": ["长管串并联与三水池问题", "紊流阻力分区"], "method": "长管阻抗与多水池节点能量平衡", "difficulty": 1, "subType": "mini-calc"},
    21: {"title": "建筑物地基正交渗流流网对称点渗流压强计算", "chapter": 11, "kps": ["平面渗流流网"], "method": "正交流网段数减一计数法", "difficulty": 2, "subType": "mini-calc"},
    22: {"title": "多孔溢流坝闸门开启流态判别与过流流量计算", "chapter": 9, "kps": ["平板闸孔出流判别", "堰流分类与基本流量公式"], "method": "堰流与闸孔出流判别及流量公式", "difficulty": 2, "subType": "mini-calc"},
    23: {"title": "矩形明渠M2降水曲线判别与断面比能沿程变化", "chapter": 8, "kps": ["临界水深与临界底坡", "缓坡水面曲线(M1/M2/M3)", "断面单位能量(比能)"], "method": "比能沿程导数判别法", "difficulty": 2, "subType": "mini-calc"},
    24: {"title": "同面积同坡降矩形明渠与正方形满管流量之比", "chapter": 7, "kps": ["达西-韦斯巴赫公式", "梯形断面水力要素"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 2, "subType": "mini-calc"},
    25: {"title": "平底矩形明渠跃后共轭水深计算与水跃移动方向", "chapter": 10, "kps": ["矩形明渠共轭水深", "水跃衔接形式"], "method": "核心基本概念记忆", "difficulty": 2, "subType": "mini-calc"},
    26: {
        "title": "铅直圆管内圆柱体等速下滑测定油液动力黏度",
        "chapter": 1,
        "kps": ["牛顿内摩擦定律", "环形/圆盘间隙黏性阻力矩"],
        "method": "分层液体切应力连续与速度叠加法",
        "difficulty": 2,
        "rubric": [
            {"label": "计算环形油膜厚度 δ = (D - d)/2 = 0.3 mm 及圆柱接触侧面积 A = πdh ≈ 7.04×10⁻³ m²", "pts": 3},
            {"label": "列出圆柱体匀速下滑竖直向力平衡方程 G = μA(u/δ)", "pts": 4},
            {"label": "统一国际单位制代入数值解得油液动力黏度 μ ≈ 6.95 Pa·s", "pts": 3},
        ],
    },
    27: {
        "title": "带U形水银压差计密闭水箱斜置半圆柱面静水总压力计算",
        "chapter": 2,
        "kps": ["U形水银压差计测压", "圆柱曲面静水总压力", "压力体图与虚压力体"],
        "method": "等效自由液面+水平投影与铅垂压力体合成法",
        "difficulty": 4,
        "rubric": [
            {"label": "由水银压差计求得 B 点等效淹深 hB ≈ 2.00 m 及 A 点等效淹深 hA = 1.50 m", "pts": 5},
            {"label": "计算半圆柱面铅垂投影面积与水平分力 Px ≈ 8.584 kN（方向水平向左）", "pts": 5},
            {"label": "由斜弦梯形扣除半圆体积求得净实压力体 Vz ≈ 1.123 m³ 及铅垂分力 Pz ≈ 11.015 kN（竖直向下）", "pts": 6},
            {"label": "合成静水总压力 P ≈ 13.965 kN 并指明方向（过圆心指向左下方，与水平面夹角 52.1°）", "pts": 4},
        ],
    },
    28: {
        "title": "含倒U型油水压差计等径弯管系统两水池水位差计算",
        "chapter": 6,
        "kps": ["简单短管自由出流", "恒定总流能量方程", "U形水银压差计测压"],
        "method": "两段伯努利方程联立法",
        "difficulty": 3,
        "rubric": [
            {"label": "由流量求得管内流速 v ≈ 1.019 m/s、流速水头 v²/(2g) ≈ 0.0529 m 及除弯管外其余水头损失 0.5288 m", "pts": 7},
            {"label": "由倒 U 型油水压差计等压面关系求得 90° 弯管局部水头损失 hj = (1 - ρ油/ρ)Δh = 0.0201 m", "pts": 8},
            {"label": "列上下游水池水面总流能量方程求得水位高差 H ≈ 0.549 m", "pts": 5},
        ],
    },
    29: {
        "title": "水平面内 60° 渐缩弯管水流作用力计算",
        "chapter": 3,
        "kps": ["恒定总流连续性方程", "恒定总流能量方程", "恒定总流动量方程", "弯管/底坎水流作用力"],
        "method": "能量方程求流量+控制体动量方程求反力",
        "difficulty": 3,
        "rubric": [
            {"label": "求得进出口流速 vA = 3.183 m/s、vB = 5.659 m/s，列水平能量方程求得 pB ≈ 109.06 kPa", "pts": 7},
            {"label": "取控制体列水平面 x、y 向动量方程求得水流对弯管分力 Fx ≈ 2.842 kN、Fy ≈ 2.159 kN", "pts": 9},
            {"label": "合成水流对弯管总作用力 F ≈ 3.569 kN 并指明方向（指向弯管外侧右上方，偏角 37.23°）", "pts": 4},
        ],
    },
    30: {
        "title": "半正六边形断面明渠均匀流底宽与正常水深设计",
        "chapter": 7,
        "kps": ["梯形断面水力要素", "明渠均匀流曼宁公式", "水力最佳断面"],
        "method": "水力要素计算+曼宁公式+水力深度Fr判据",
        "difficulty": 3,
        "rubric": [
            {"label": "导出半正六边形过水面积 A = (3√3/4)b²、湿周 χ = 3b 及水力半径 R = (√3/4)b", "pts": 5},
            {"label": "代入明渠均匀流曼宁公式解得渠道底宽 b ≈ 1.746 m", "pts": 6},
            {"label": "由正六边形几何关系求得正常水深 h0 = b·sin60° ≈ 1.512 m", "pts": 4},
        ],
    },
    31: {
        "title": "二维不可压缩流场存在性判别、流函数与势函数求解",
        "chapter": 5,
        "kps": ["平面不可压缩流连续性方程", "无旋流判据", "流函数与速度势函数求解"],
        "method": "不可压与无旋偏导检验+偏积分求原函数法",
        "difficulty": 2,
        "rubric": [
            {"label": "检验不可压缩连续性方程 ∂ux/∂x + ∂uy/∂y + ∂uz/∂z = 2y - 2y + 0 = 0 成立，判定流动存在", "pts": 5},
            {"label": "偏积分求得平面流函数 ψ = xy² - x³/3 + C", "pts": 5},
            {"label": "检验旋转角速度 ωz = 0 判定为无旋流动，积分求得流速势函数 φ = x²y - y³/3 + C（或负梯度反号）", "pts": 5},
        ],
    },
}


# ==============================================================================
# Curated Metadata: 2014 (Q1 - Q31)
# ==============================================================================
META_2014 = {
    1:  {"title": "均匀流流场压强分布与静水压强分布规律辨析", "chapter": 3, "kps": ["恒定流与均匀流判别", "静水压强基本方程"], "method": "概念偷换词辨析", "difficulty": 2},
    2:  {"title": "重力与其他质量力共同作用下的等压面形状判别", "chapter": 2, "kps": ["静水压强基本方程"], "method": "物理概念定义辨析", "difficulty": 2},
    3:  {"title": "明渠S1型壅水曲线断面单位能量沿程变化判别", "chapter": 8, "kps": ["明渠水面曲线定性分析", "断面单位能量(比能)"], "method": "比能沿程导数判别法", "difficulty": 2},
    4:  {"title": "静止盛水容器侧壁两点间U形水银压差计读数判别", "chapter": 2, "kps": ["静水压强基本方程", "U形水银压差计测压"], "method": "等压面静水压强递推法", "difficulty": 2},
    5:  {"title": "均质土基闸下有压渗流流网几何形状的影响因素", "chapter": 11, "kps": ["平面渗流流网"], "method": "物理概念定义辨析", "difficulty": 2},
    6:  {"title": "非恒定流与渐变流时空分类概念辨析", "chapter": 3, "kps": ["恒定流与均匀流判别"], "method": "概念偷换词辨析", "difficulty": 1},
    7:  {"title": "水平渐扩管道管轴动水压强沿程变化规律辨析", "chapter": 6, "kps": ["有压渐扩管压强变化", "恒定总流能量方程"], "method": "伯努利方程多因素反例法", "difficulty": 2},
    8:  {"title": "有压管道均匀流水力坡度与管轴线几何坡度辨析", "chapter": 6, "kps": ["总水头线与测压管水头线", "沿程水头损失规律"], "method": "概念偷换词辨析", "difficulty": 2},
    9:  {"title": "无旋流同一流线上流速势函数沿流向变化规律", "chapter": 5, "kps": ["流函数与速度势函数求解"], "method": "物理概念定义辨析", "difficulty": 2},
    10: {"title": "紊流相对粗糙度对沿程水头损失系数的影响判别", "chapter": 4, "kps": ["紊流阻力分区", "达西-韦斯巴赫公式"], "method": "物理概念定义辨析", "difficulty": 2},
    11: {"title": "牛顿内摩擦定律的流体与流态适用条件", "chapter": 1, "kps": ["牛顿内摩擦定律"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "blank"},
    12: {"title": "矩形断面明渠临界水深计算", "chapter": 8, "kps": ["临界水深与临界底坡"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 1, "subType": "mini-calc"},
    13: {"title": "定流量定水温输水圆管雷诺数随管径变化趋势", "chapter": 4, "kps": ["雷诺数与流态判别", "恒定总流连续性方程"], "method": "物理概念定义辨析", "difficulty": 1, "subType": "blank"},
    14: {"title": "冷热水同流量紊流光滑区水力坡度大小比较", "chapter": 4, "kps": ["紊流阻力分区", "雷诺数与流态判别"], "method": "紊流光滑区布拉休斯幂次比例法", "difficulty": 2, "subType": "blank"},
    15: {"title": "由平面无旋流流速势函数求两流线间单宽流量", "chapter": 5, "kps": ["流函数与速度势函数求解"], "method": "不可压与无旋偏导检验+偏积分求原函数法", "difficulty": 2, "subType": "mini-calc"},
    16: {"title": "溢流坝重力相似模型实测流速换算原型流速", "chapter": 13, "kps": ["弗劳德相似准则"], "method": "弗劳德比尺幂次换算法", "difficulty": 1, "subType": "mini-calc"},
    17: {"title": "抽水机吸水管动水压强随安装高度的变化趋势", "chapter": 6, "kps": ["虹吸管水力计算", "真空高度(真空度)"], "method": "两段伯努利方程联立法", "difficulty": 1, "subType": "blank"},
    18: {"title": "60°斜坡上静止圆筒所受静水总压力大小计算", "chapter": 2, "kps": ["圆柱曲面静水总压力", "压力体图与虚压力体"], "method": "等效自由液面+水平投影与铅垂压力体合成法", "difficulty": 3, "subType": "mini-calc"},
    19: {"title": "管道末端直接水击由压强水头反求原流速", "chapter": 6, "kps": ["有压管道水击(水锤)", "儒可夫斯基公式"], "method": "水击相长判别与儒氏公式", "difficulty": 1, "subType": "mini-calc"},
    20: {"title": "平底矩形明渠平板闸下水跃衔接形式判别", "chapter": 10, "kps": ["平板闸孔出流判别", "水跃衔接形式", "矩形明渠共轭水深"], "method": "堰流与闸孔出流判别及流量公式", "difficulty": 3, "subType": "mini-calc"},
    21: {"title": "无侧收缩矩形薄壁堰消除水舌下局部真空的工程措施", "chapter": 9, "kps": ["堰流分类与基本流量公式"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "short-answer"},
    22: {"title": "正反双U形压差计联立测定两容器内液体密度", "chapter": 2, "kps": ["静水压强基本方程", "U形水银压差计测压"], "method": "等压面静水压强递推法", "difficulty": 3, "subType": "mini-calc"},
    23: {"title": "阻力平方区长管半程并联等径支管前后流量比", "chapter": 6, "kps": ["长管串并联与三水池问题"], "method": "长管阻抗与多水池节点能量平衡", "difficulty": 3, "subType": "mini-calc"},
    24: {"title": "水闸底板有压渗流正交流网单宽渗流量计算", "chapter": 11, "kps": ["平面渗流流网", "达西定律与单宽渗流量"], "method": "正交流网段数减一计数法", "difficulty": 2, "subType": "mini-calc"},
    25: {"title": "同一管道紊流光滑区与粗糙区过流流量大小比较", "chapter": 4, "kps": ["紊流阻力分区", "雷诺数与流态判别"], "method": "物理概念定义辨析", "difficulty": 1, "subType": "blank"},
    26: {
        "title": "双层不同黏度油膜中极薄平板匀速运动动力黏度计算",
        "chapter": 1,
        "kps": ["牛顿内摩擦定律", "双层液体平板剪切流"],
        "method": "分层液体切应力连续与速度叠加法",
        "difficulty": 2,
        "rubric": [
            {"label": "写出上下两油层线性速度梯度切应力表达式 τ1 = μ1(u/δ)、τ2 = μ2(u/δ)", "pts": 4},
            {"label": "列出平板双面总切应力平衡方程 τ = (μ1 + μ2)(u/δ) = 25 N/m²", "pts": 3},
            {"label": "结合 μ1 = 2μ2 解得 μ1 ≈ 0.833 Pa·s、μ2 ≈ 0.417 Pa·s", "pts": 3},
        ],
    },
    27: {
        "title": "单层与双层静止液体容器中1/4圆弧钢板静水总压力计算",
        "chapter": 2,
        "kps": ["静水压强基本方程", "圆柱曲面静水总压力", "压力体图与虚压力体"],
        "method": "等效自由液面+水平投影与铅垂压力体合成法",
        "difficulty": 3,
        "rubric": [
            {"label": "容器 (a)：求得水平分力 Px = 24.53 kN（向右）与虚压力体铅垂分力 Pz = 21.73 kN（向上）", "pts": 5},
            {"label": "容器 (a)：合成总压力 P = 32.76 kN 并指明方向（过圆心指向右上方，仰角 41.5°）", "pts": 5},
            {"label": "容器 (b)：计入双层液体压强递推求得 Px = 25.51 kN（向右）与向上铅垂分力 Pz = 22.15 kN", "pts": 5},
            {"label": "容器 (b)：合成总压力 P = 33.78 kN 并指明方向（过圆心指向右上方，仰角 41.0°）", "pts": 5},
        ],
    },
    28: {
        "title": "带喉部负压吸水玻璃管水平收缩短管作用水头计算",
        "chapter": 6,
        "kps": ["简单短管自由出流", "真空高度(真空度)", "恒定总流能量方程"],
        "method": "两段伯努利方程联立法",
        "difficulty": 3,
        "rubric": [
            {"label": "对水箱液面至管出口列总流能量方程得 H = 5v²/(2g)", "pts": 6},
            {"label": "由连续性方程得收缩段流速 v2 = (16/9)v，并判出喉部真空压强水头 p2/(ρg) = -0.35 m", "pts": 4},
            {"label": "对水箱液面至喉部断面列能量方程得 H = -0.35 + (499/81)v²/(2g)", "pts": 6},
            {"label": "联立两能量方程解得 v²/(2g) ≈ 0.3016 m 及水箱水头 H ≈ 1.51 m", "pts": 4},
        ],
    },
    29: {
        "title": "带U形水银压差计水平渐缩输油管段流体作用力计算",
        "chapter": 3,
        "kps": ["U形水银压差计测压", "恒定总流能量方程", "恒定总流动量方程", "弯管/底坎水流作用力"],
        "method": "能量方程求流量+控制体动量方程求反力",
        "difficulty": 3,
        "rubric": [
            {"label": "由水银压差计求得压强差 p1 - p2 = (ρm - ρ)gΔh ≈ 1873.6 Pa 及进口压强 p1 ≈ 26.37 kPa", "pts": 5},
            {"label": "联立连续性方程与能量方程解得流速 v1 ≈ 1.031 m/s、v2 ≈ 2.320 m/s 及流量 Q ≈ 0.01822 m³/s", "pts": 6},
            {"label": "取渐变段控制体列水平动量方程解得油流对管段作用力 F ≈ 253.3 N（方向水平向右）", "pts": 9},
        ],
    },
    30: {
        "title": "三维非恒定流场不可压缩性判别与流速势函数求解",
        "chapter": 5,
        "kps": ["平面不可压缩流连续性方程", "无旋流判据", "流函数与速度势函数求解"],
        "method": "不可压与无旋偏导检验+偏积分求原函数法",
        "difficulty": 2,
        "rubric": [
            {"label": "计算 ∂ux/∂x + ∂uy/∂y + ∂uz/∂z = 0 + 0 + 0 = 0，判定满足不可压缩液体连续性方程", "pts": 6},
            {"label": "计算三个旋转角速度分量 ωx = ωy = ωz = 0，判定为无旋运动", "pts": 5},
            {"label": "由全微分 dφ = t·d(xyz) 积分求得速度势函数 φ = xyzt + C（或按负梯度约定 φ = -xyzt + C）", "pts": 4},
        ],
    },
    31: {
        "title": "缓—陡—缓三坡段宽浅矩形明渠特征水深与水面曲线分析",
        "chapter": 8,
        "kps": ["临界水深与临界底坡", "明渠均匀流曼宁公式", "明渠水面曲线定性分析", "明渠水跃与跃后水深"],
        "method": "渐变流微分方程符号判别",
        "difficulty": 4,
        "rubric": [
            {"label": "求得各渠段正常水深 h01 ≈ 1.036 m、h02 ≈ 0.570 m、h03 ≈ 0.975 m", "pts": 5},
            {"label": "判出缓坡接陡坡变坡点为控制断面，求得第一、二渠段交接处临界水深 hc ≈ 0.742 m", "pts": 4},
            {"label": "算得跃后共轭水深 h02'' ≈ 0.945 m < h03（陡坡末端淹没水跃），准确绘出 M2→S2→水跃→S1→h03 水面线", "pts": 6},
        ],
    },
}


# ==============================================================================
# Curated Metadata: 2013 (Q1 - Q36)
# ==============================================================================
META_2013 = {
    1:  {"title": "牛顿液体切应力与剪切变形速度的线性本构关系", "chapter": 1, "kps": ["牛顿内摩擦定律"], "method": "物理概念定义辨析", "difficulty": 1},
    2:  {"title": "明渠水流流动方向的总水头判据辨析", "chapter": 8, "kps": ["恒定总流能量方程", "明渠水面曲线定性分析"], "method": "伯努利方程多因素反例法", "difficulty": 2},
    3:  {"title": "恒定总流能量方程计算动水压强与基准面选取无关性", "chapter": 3, "kps": ["恒定总流能量方程"], "method": "物理概念定义辨析", "difficulty": 1},
    4:  {"title": "二元流与非均匀流分类维度辨析", "chapter": 3, "kps": ["恒定流与均匀流判别", "断面流速分布"], "method": "概念偷换词辨析", "difficulty": 2},
    5:  {"title": "紊流各阻力区沿程水头损失与流速幂次关系辨析", "chapter": 4, "kps": ["紊流阻力分区", "达西-韦斯巴赫公式"], "method": "紊流光滑区布拉休斯幂次比例法", "difficulty": 2},
    6:  {"title": "水流固体边界附近流速大小与边壁切应力关系辨析", "chapter": 4, "kps": ["牛顿内摩擦定律", "圆管均匀流切应力分布"], "method": "圆管切应力线性分布性质", "difficulty": 2},
    7:  {"title": "有压管流与明渠水流急缓流分类适用范围辨析", "chapter": 8, "kps": ["弗劳德数判急缓流"], "method": "概念偷换词辨析", "difficulty": 1},
    8:  {"title": "达西线性渗流定律对层流与紊流渗流的适用范围", "chapter": 11, "kps": ["达西定律与适用范围"], "method": "物理概念定义辨析", "difficulty": 2},
    9:  {"title": "雷诺实验与尼古拉兹实验研究目的辨析", "chapter": 4, "kps": ["雷诺数与流态判别", "紊流阻力分区"], "method": "概念偷换词辨析", "difficulty": 1},
    10: {"title": "并联管道各支管单位重量总机械能损失相等规律", "chapter": 6, "kps": ["长管串并联与三水池问题", "恒定总流能量方程"], "method": "长管阻抗与多水池节点能量平衡", "difficulty": 2},
    11: {"title": "绝对静止与相对平衡液体等压面形状辨析", "chapter": 2, "kps": ["静水压强基本方程"], "method": "物理概念定义辨析", "difficulty": 2},
    12: {"title": "平坡棱柱形明渠断面单位能量沿程单调减小规律", "chapter": 8, "kps": ["断面单位能量(比能)", "明渠渐变流基本微分方程"], "method": "比能沿程导数判别法", "difficulty": 2},
    13: {"title": "实用堰超设计水头运行时流量系数变化规律", "chapter": 9, "kps": ["堰流分类与基本流量公式"], "method": "堰流与闸孔出流判别及流量公式", "difficulty": 2},
    14: {"title": "底流消能工程设计采用略微淹没水跃的原则", "chapter": 10, "kps": ["底流消能判别", "水跃衔接形式"], "method": "物理概念定义辨析", "difficulty": 1},
    15: {"title": "按堰顶相对厚度判别实用堰与宽顶堰", "chapter": 9, "kps": ["堰流分类与基本流量公式"], "method": "堰流与闸孔出流判别及流量公式", "difficulty": 1},
    16: {"title": "由真空高度计算水流相对压强", "chapter": 2, "kps": ["真空高度(真空度)", "静水压强基本方程"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "mini-calc"},
    17: {"title": "由实测二维流速时间序列计算瞬时紊动附加切应力", "chapter": 4, "kps": ["断面流速分布"], "method": "核心基本概念记忆", "difficulty": 3, "subType": "mini-calc"},
    18: {"title": "圆管恒定均匀流管壁切应力计算", "chapter": 4, "kps": ["圆管均匀流切应力分布"], "method": "圆管切应力线性分布性质", "difficulty": 1, "subType": "mini-calc"},
    19: {"title": "毕托管测量点流速的驻点能量转换原理", "chapter": 3, "kps": ["恒定总流能量方程"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "short-answer"},
    20: {"title": "缓坡M1型壅水曲线弗劳德数沿程变化规律", "chapter": 8, "kps": ["缓坡水面曲线(M1/M2/M3)", "弗劳德数判急缓流"], "method": "渐变流微分方程符号判别", "difficulty": 1, "subType": "blank"},
    21: {"title": "溢流坝重力相似模型收缩断面原型平均流速换算", "chapter": 13, "kps": ["弗劳德相似准则"], "method": "弗劳德比尺幂次换算法", "difficulty": 1, "subType": "mini-calc"},
    22: {"title": "文丘里管流量系数小于1的物理原因", "chapter": 3, "kps": ["恒定总流能量方程"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "short-answer"},
    23: {"title": "水电比拟正交流网指定等势线点渗流压强计算", "chapter": 11, "kps": ["平面渗流流网"], "method": "正交流网段数减一计数法", "difficulty": 2, "subType": "mini-calc"},
    24: {"title": "不同下游堰高自由出流实用堰收缩断面水深大小比较", "chapter": 9, "kps": ["堰流分类与基本流量公式", "断面单位能量(比能)"], "method": "比能沿程导数判别法", "difficulty": 3, "subType": "blank"},
    25: {"title": "局部水头损失系数的水力试验确定方法", "chapter": 4, "kps": ["沿程水头损失规律"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "blank"},
    26: {"title": "按黏滞底层与粗糙高度相对值划分紊流三类壁面", "chapter": 4, "kps": ["紊流阻力分区"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "blank"},
    27: {"title": "窄间隙双层黏性液膜中运动平板最小内摩擦力位置求解", "chapter": 1, "kps": ["牛顿内摩擦定律", "双层液体平板剪切流"], "method": "分层液体切应力连续与速度叠加法", "difficulty": 3, "subType": "mini-calc"},
    28: {"title": "液体有旋运动的旋转角速度判据与轨迹无关性", "chapter": 5, "kps": ["无旋流判据"], "method": "核心基本概念记忆", "difficulty": 2, "subType": "short-answer"},
    29: {"title": "输油圆管雷诺数流态判别与层流沿程水头损失计算", "chapter": 4, "kps": ["雷诺数与流态判别", "圆管层流哈根-泊肃叶定律"], "method": "圆管切应力线性分布性质", "difficulty": 2, "subType": "mini-calc"},
    30: {"title": "输水长管直接水击判别与最大水击压强增量计算", "chapter": 6, "kps": ["有压管道水击(水锤)", "直接与间接水击判别", "儒可夫斯基公式"], "method": "水击相长判别与儒氏公式", "difficulty": 2, "subType": "mini-calc"},
    31: {
        "title": "圆柱管嘴水平射流冲击力与密闭水箱静水压力平衡计算",
        "chapter": 3,
        "kps": ["孔口与管嘴出流", "恒定总流动量方程", "U形水银压差计测压", "平面静水总压力"],
        "method": "能量方程求流量+控制体动量方程求反力",
        "difficulty": 3,
        "qtype_override": "calc",
        "rubric": [
            {"label": "对甲水箱管嘴列能量方程与射流动量方程求得右侧冲击推力 F = (4/3)ρgh1A", "pts": 7},
            {"label": "对乙水箱水银压差计列等压面方程求得液面相对压强 p0 及封堵管嘴形心水头 pc/(ρg) = 2.31 m", "pts": 8},
            {"label": "由挡板两侧水平作用力平衡 F = P = pcA 解得 h1 ≈ 1.73 m（精确值 1.7325 m）", "pts": 5},
        ],
    },
    32: {
        "title": "绕底端无摩擦铰链转动倾斜平面闸门力矩平衡求门长",
        "chapter": 2,
        "kps": ["平面静水总压力"],
        "method": "平面总压力形心法/分块合成法",
        "difficulty": 3,
        "qtype_override": "calc",
        "rubric": [
            {"label": "计算浸水斜长 lw = 2.0 m、静水总压力 P = 78.48 kN 及对底铰 O 的力臂 e = 2/3 m（顺时针力矩）", "pts": 6},
            {"label": "写出闸门自重 G = Mg = 19.62 kN 对底铰 O 的逆时针力矩 G·(L/2)cos30°", "pts": 4},
            {"label": "列绕底铰 O 的力矩平衡方程 ∑MO = 0 解得闸门长度 L ≈ 6.16 m", "pts": 5},
        ],
    },
    33: {
        "title": "双层静止液体隔板圆孔处无重圆球压力体平衡关系推导",
        "chapter": 2,
        "kps": ["圆柱曲面静水总压力", "压力体图与虚压力体"],
        "method": "等效自由液面+水平投影与铅垂压力体合成法",
        "difficulty": 4,
        "qtype_override": "calc",
        "rubric": [
            {"label": "求得上半球所受密度 ρ2 液体向下实压力体体积 V下 = πD²h2/4 - πD³/12 及铅垂压力 P下", "pts": 5},
            {"label": "求得下半球所受密度 ρ1 液体向上虚压力体体积 V上 = πD²h1/4 + πD³/12 及铅垂压力 P上", "pts": 5},
            {"label": "由铅垂方向静力平衡 P上 = P下 化简导出 D = 3(ρ2h2 - ρ1h1) / (ρ1 + ρ2)", "pts": 5},
        ],
    },
    34: {
        "title": "缓—陡—缓三段宽浅矩形明渠单宽流量、比能变化与水跃位置分析",
        "chapter": 8,
        "kps": ["临界水深与临界底坡", "断面单位能量(比能)", "明渠水面曲线定性分析", "明渠水跃与跃后水深"],
        "method": "渐变流微分方程符号判别",
        "difficulty": 4,
        "qtype_override": "calc",
        "rubric": [
            {"label": "判定第一、二段交接处（缓坡转陡坡）为临界水深 hc = 4 m，求得单宽流量 q ≈ 25.06 m²/s", "pts": 5},
            {"label": "求得三段正常水深并判出比能变化：第一段 M2 沿程减小，第二段 S2 与 S1 沿程增大，第三段均匀流不变", "pts": 5},
            {"label": "算得第二段跃后共轭水深 h02'' ≈ 4.84 m < h03 = 5.59 m，判定发生淹没水跃且位于第二渠段末端", "pts": 5},
        ],
    },
    35: {
        "title": "流函数与势函数表示同一平面不可压无旋流场的恒等证明",
        "chapter": 5,
        "kps": ["平面不可压缩流连续性方程", "无旋流判据", "流函数与速度势函数求解"],
        "method": "不可压与无旋偏导检验+偏积分求原函数法",
        "difficulty": 2,
        "qtype_override": "proof",
        "rubric": [
            {"label": "由流函数 ψ1 求偏导得出流速分量 ux1 = ∂ψ1/∂y = x + 2、uy1 = -∂ψ1/∂x = -y - 3", "pts": 6},
            {"label": "由势函数 φ2 求偏导得出流速分量 ux2 = ∂φ2/∂x = x + 2、uy2 = ∂φ2/∂y = -y - 3", "pts": 6},
            {"label": "对比任意点 (x, y) 处速度矢量恒等 ux1 = ux2、uy1 = uy2，证得两流场完全相同", "pts": 3},
        ],
    },
    36: {
        "title": "宽浅矩形河道均匀流谢才公式估算水库蓄水引起的水位降幅",
        "chapter": 7,
        "kps": ["梯形断面水力要素", "明渠均匀流曼宁公式"],
        "method": "水力要素计算+曼宁公式+水力深度Fr判据",
        "difficulty": 2,
        "qtype_override": "calc",
        "rubric": [
            {"label": "按宽浅矩形河道 R ≈ h 写出谢才公式水深显式解 h = [Q / (CB√i)]^(2/3)", "pts": 4},
            {"label": "分别求得天然流量下水深 h1 ≈ 9.56 m 与拦蓄后流量 12000 m³/s 下水深 h2 ≈ 7.58 m", "pts": 4},
            {"label": "算得蓄水所致水位降幅 Δh ≈ 1.98 m ≈ 2 m < 4～5 m，说明下游枯水不全由三峡蓄水引起", "pts": 2},
        ],
    },
}


# ==============================================================================
# Matplotlib High-Resolution Clean Engineering Diagrams (Zero Chinese in $...$)
# ==============================================================================
def draw_2015_q04_sol(dest_path: Path):
    """Draw accurate EGL/HGL diagram for 2015 Judge Q4 (narrow ascending -> sudden expansion -> submerged exit)."""
    fig, ax = plt.subplots(figsize=(8.6, 4.0))
    fig.patch.set_facecolor("white")

    # Upstream & downstream tanks
    ax.plot([0.2, 0.2, 1.8], [3.5, 0.4, 0.4], color="#0f172a", lw=2.0)
    ax.plot([1.8, 1.8], [0.4, 0.85], color="#0f172a", lw=2.0)
    ax.plot([1.8, 1.8], [1.10, 3.5], color="#0f172a", lw=2.0)

    # Pipe 1 (narrow ascending: x=1.8..4.5)
    ax.plot([1.8, 4.5], [1.10, 1.40], color="#0f172a", lw=1.8)
    ax.plot([1.8, 4.5], [0.85, 1.15], color="#0f172a", lw=1.8)
    # Sudden expansion at x=4.5 into Pipe 2 (wider descending: x=4.5..7.2)
    ax.plot([4.5, 4.5], [1.40, 1.56], color="#0f172a", lw=1.8)
    ax.plot([4.5, 4.5], [1.15, 0.99], color="#0f172a", lw=1.8)
    ax.plot([4.5, 7.2], [1.56, 1.16], color="#0f172a", lw=1.8)
    ax.plot([4.5, 7.2], [0.99, 0.59], color="#0f172a", lw=1.8)

    # Downstream tank wall at x=7.2
    ax.plot([7.2, 7.2], [1.16, 2.5], color="#0f172a", lw=2.0)
    ax.plot([7.2, 7.2, 9.0], [0.59, 0.2, 0.2], color="#0f172a", lw=2.0)

    # Water surfaces
    z_up, z_dn = 3.10, 1.75
    ax.plot([0.25, 1.8], [z_up, z_up], color="#0284c7", lw=2.0)
    ax.plot([7.2, 8.95], [z_dn, z_dn], color="#0284c7", lw=2.0)
    ax.text(0.55, z_up - 0.22, "上游水面", fontsize=9.2, color="#0369a1")
    ax.text(7.90, z_dn - 0.22, "下游水面", fontsize=9.2, color="#0369a1")

    # Correct EGL (green solid) & Correct HGL (red dashed)
    egl_up = z_up + 0.16
    ax.plot([0.3, 1.8], [egl_up, egl_up], color="#15803d", lw=2.2)
    egl_x = [1.8, 1.8, 4.5, 4.5, 7.2, 7.2, 8.9]
    egl_y = [egl_up, 2.98, 2.50, 2.34, 2.12, z_dn + 0.12, z_dn + 0.12]
    ax.plot(egl_x, egl_y, color="#15803d", lw=2.4, label="正确总水头线 EGL（全程单调下降）")

    # HGL: drops by hv1=0.66 below EGL in narrow pipe, RISES at sudden expansion (gap narrows to hv2=0.30!), meets downstream HGL at z_dn!
    hgl_x = [1.8, 4.5, 4.5, 7.2]
    hgl_y = [2.98 - 0.66, 2.50 - 0.66, 2.34 - 0.30, z_dn]
    ax.plot([1.8, 1.8], [z_up, 2.98 - 0.66], color="#dc2626", lw=1.6, ls=":")
    ax.plot(hgl_x, hgl_y, color="#dc2626", lw=2.3, ls="--", label="正确测压管水头线 HGL（突扩后间距收窄，末端接下游水面）")

    # Double arrows showing velocity head narrowing
    ax.annotate("", xy=(2.95, 2.775), xytext=(2.95, 2.775 - 0.66),
                arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.4))
    ax.text(3.04, 2.40, r"$\frac{\alpha_1 v_1^2}{2g}$（细管大）", fontsize=9.0, color="#1e293b")

    ax.annotate("", xy=(5.75, 2.238), xytext=(5.75, 2.238 - 0.30),
                arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.4))
    ax.text(5.84, 2.02, r"$\frac{\alpha_2 v_2^2}{2g}$（粗管小）", fontsize=9.0, color="#1e293b")

    ax.scatter([7.2], [z_dn], color="#dc2626", s=36, zorder=6)
    ax.text(7.28, z_dn - 0.50, "淹没出口 HGL 必接下游水面", fontsize=8.8, color="#b91c1c")

    ax.set_title("2015 年是非第 4 题：变径短管正确的总水头线与测压管水头线关系", fontsize=11, pad=6)
    ax.legend(loc="lower left", fontsize=8.6, framealpha=0.92)
    ax.set_xlim(0.0, 9.2)
    ax.set_ylim(0.05, 3.65)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(dest_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2015_q27_sol(dest_path: Path):
    """Draw clean pressure-body & resultant vector diagram for 2015 Calc Q2."""
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    fig.patch.set_facecolor("white")

    R = 0.5
    thA, thB = np.radians(150.0), np.radians(-30.0)
    xA, zA = R * np.cos(thA), R * np.sin(thA)   # (-0.433, +0.25)
    xB, zB = R * np.cos(thB), R * np.sin(thB)   # (+0.433, -0.25)
    Z0 = zB + 2.00                              # +1.75 m

    # Equivalent free surface
    ax.plot([-1.05, 1.05], [Z0, Z0], color="#0284c7", lw=2.0, ls="-.")
    ax.text(-1.02, Z0 + 0.06, r"等效自由液面（$p=0$，高于箱顶 $0.50\,\mathrm{m}$）", fontsize=9.5, color="#0369a1")

    # Shade real downward pressure body between xA and x=R (upper arc from 150 deg to 0 deg)
    ths_top = np.linspace(np.radians(150.0), 0.0, 120)
    poly_down = [(xA, Z0), (R, Z0)] + [(R * np.cos(t), R * np.sin(t)) for t in ths_top[::-1]]
    ax.add_patch(Polygon(poly_down, closed=True, facecolor="#dbeafe", edgecolor="#2563eb", lw=1.2, alpha=0.82,
                         label="上弧段向下实压力体"))

    # Shade small overhang virtual upward region between xB and x=R (lower arc from 0 deg to -30 deg)
    ths_over = np.linspace(0.0, np.radians(-30.0), 50)
    poly_up = [(xB, Z0), (R, Z0)] + [(R * np.cos(t), R * np.sin(t)) for t in ths_over] + [(xB, zB)]
    # Actually the upward virtual body on the lower overhang (0 to -30 deg) is from that arc up to Z0!
    poly_virt = [(R, Z0), (xB, Z0)] + [(R * np.cos(t), R * np.sin(t)) for t in ths_over[::-1]]
    ax.add_patch(Polygon(poly_virt, closed=True, facecolor="#fee2e2", edgecolor="#dc2626", lw=1.1, hatch="//", alpha=0.65,
                         label="右下悬挑段向上虚压力体（相减抵消）"))

    # Semicircle arc AB & dashed chord AB
    ths_all = np.linspace(thB, thA, 160)
    ax.plot(R * np.cos(ths_all), R * np.sin(ths_all), color="#0f172a", lw=3.6, zorder=5)
    ax.plot([xA, xB], [zA, zB], color="#475569", lw=1.5, ls="--", zorder=4)
    ax.scatter([0.0], [0.0], color="#0f172a", s=28, zorder=6)
    ax.text(-0.08, -0.02, "$O$", fontsize=10, fontweight="bold")
    ax.text(xA - 0.13, zA - 0.04, "$A$", fontsize=10.5, fontweight="bold")
    ax.text(xB + 0.05, zB - 0.08, "$B$", fontsize=10.5, fontweight="bold")

    # Dimension arrows for hA = 1.50 m and hB = 2.00 m
    ax.annotate("", xy=(-0.72, zA), xytext=(-0.72, Z0), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.4))
    ax.plot([-0.76, xA], [zA, zA], color="#94a3b8", lw=0.9, ls=":")
    ax.text(-0.76, 0.5 * (zA + Z0) - 0.12, r"$h_A = 1.50\,\mathrm{m}$", fontsize=9.5, ha="right", va="center")

    ax.annotate("", xy=(0.74, zB), xytext=(0.74, Z0), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.4))
    ax.plot([xB, 0.78], [zB, zB], color="#94a3b8", lw=0.9, ls=":")
    ax.text(0.78, 0.5 * (zB + Z0) - 0.12, r"$h_B = 2.00\,\mathrm{m}$", fontsize=9.5, ha="left", va="center")

    # Resultant force vector through O pointing down-left at 52.1 deg
    ang = np.radians(52.07)
    Lvec = 0.66
    ax.annotate("", xy=(-Lvec * np.cos(ang), -Lvec * np.sin(ang)), xytext=(0.0, 0.0),
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.8), zorder=7)
    ax.text(-Lvec * np.cos(ang) - 0.06, -Lvec * np.sin(ang) - 0.08,
            r"$P = 13.965\,\mathrm{kN}$" + "\n" + r"（过圆心 $O$，左下方 $52.1^{\circ}$）",
            fontsize=9.4, ha="right", va="top", color="#b91c1c", fontweight="bold")

    ax.text(0.0, 1.30, r"净压力体 $V_z = \frac{h_A+h_B}{2}(2R\cos 30^{\circ})L - \frac{1}{2}\pi R^2 L = 1.123\,\mathrm{m^3}$",
            fontsize=8.6, ha="center", color="#1e3a8a",
            bbox=dict(boxstyle="round,pad=0.24", facecolor="white", edgecolor="#93c5fd", alpha=0.94))

    ax.set_title("2015 年计算第 2 题：等效自由液面、压力体合成与静水总压力方向图", fontsize=11, pad=6)
    ax.legend(loc="lower right", fontsize=8.4, framealpha=0.94)
    ax.set_xlim(-1.55, 1.55)
    ax.set_ylim(-0.96, 2.02)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(dest_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2014_q27_sol(dest_path: Path):
    """Draw physically corrected pressure-body & UPWARD-RIGHT force diagram for 2014 Calc Q2."""
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.4))
    fig.patch.set_facecolor("white")

    configs = [
        ("(a) 单一液体 " + r"$\rho_1 = 1000\,\mathrm{kg/m^3}$", False, 24.53, 21.73, 32.76, 41.5),
        ("(b) 双层液体 " + r"$\rho_1 = 1000,\ \rho_2 = 1200\,\mathrm{kg/m^3}$", True, 25.51, 22.15, 33.78, 41.0),
    ]

    for ax, (sub_title, is_two_layer, px, pz, ptot, deg) in zip(axes, configs):
        # Tank geometry: left wall x=-1.1, top wall x=0 from y=1..3.3, quarter-circle AB centered at O=(0,0) from A=(0,1) to B=(1,0)
        ths = np.linspace(0, np.pi / 2, 120)
        arc_x, arc_y = np.cos(ths), np.sin(ths)

        # Fill interior liquid
        if not is_two_layer:
            poly_liq = [(-1.1, 3.0), (0.0, 3.0), (0.0, 1.0)] + list(zip(arc_x[::-1], arc_y[::-1])) + [(-1.1, 0.0)]
            ax.add_patch(Polygon(poly_liq, closed=True, facecolor="#e0f2fe", edgecolor="none", alpha=0.85))
            ax.text(-0.55, 1.75, r"$\rho_1$", fontsize=11, ha="center", color="#0369a1")
        else:
            ax.add_patch(Rectangle((-1.1, 1.0), 1.1, 2.0, facecolor="#e0f2fe", edgecolor="none", alpha=0.85))
            poly_bot = [(-1.1, 1.0), (0.0, 1.0)] + list(zip(arc_x[::-1], arc_y[::-1])) + [(-1.1, 0.0)]
            ax.add_patch(Polygon(poly_bot, closed=True, facecolor="#fef3c7", edgecolor="none", alpha=0.9))
            ax.plot([-1.1, 0.0], [1.0, 1.0], color="#64748b", lw=1.2, ls="--")
            ax.text(-0.55, 2.0, r"$\rho_1$", fontsize=11, ha="center", color="#0369a1")
            ax.text(-0.55, 0.45, r"$\rho_2$", fontsize=11, ha="center", color="#b45309")

        # Virtual pressure body ABOVE convex arc AB (x=0..1, from arc up to y=3.0)
        if not is_two_layer:
            poly_vp = [(0.0, 3.0), (1.0, 3.0)] + list(zip(arc_x, arc_y))
            ax.add_patch(Polygon(poly_vp, closed=True, facecolor="#fee2e2", edgecolor="#dc2626",
                                 lw=1.2, ls="--", hatch="//", alpha=0.55))
        else:
            ax.add_patch(Rectangle((0.0, 1.0), 1.0, 2.0, facecolor="#fee2e2", edgecolor="#dc2626",
                                   lw=1.1, ls="--", hatch="//", alpha=0.48))
            poly_vp2 = [(0.0, 1.0), (1.0, 1.0)] + list(zip(arc_x, arc_y))
            ax.add_patch(Polygon(poly_vp2, closed=True, facecolor="#ffedd5", edgecolor="#ea580c",
                                 lw=1.1, ls="--", hatch="\\\\", alpha=0.65))

        ax.text(0.50, 2.15, "虚压力体\n" + r"（$P_z$ 铅垂向上）", fontsize=8.8, ha="center", color="#991b1b")

        # Free surface & tank walls
        ax.plot([-1.1, 0.0], [3.0, 3.0], color="#0284c7", lw=2.0)
        ax.plot([-1.1, -1.1, 1.0], [3.35, 0.0, 0.0], color="#0f172a", lw=2.3)
        ax.plot([0.0, 0.0], [1.0, 3.35], color="#0f172a", lw=2.3)
        ax.plot(arc_x, arc_y, color="#0f172a", lw=3.4, zorder=5)

        # Center O, A, B
        ax.scatter([0.0], [0.0], color="#0f172a", s=26, zorder=6)
        ax.text(-0.16, -0.18, "$O$", fontsize=10, fontweight="bold")
        ax.text(-0.19, 1.03, "$A$", fontsize=10, fontweight="bold")
        ax.text(1.04, -0.06, "$B$", fontsize=10, fontweight="bold")

        # Resultant vector P from O pointing UPWARD-RIGHT through arc AB!
        rad = np.radians(deg)
        Larrow = 1.48
        ax.annotate("", xy=(Larrow * np.cos(rad), Larrow * np.sin(rad)), xytext=(0.0, 0.0),
                    arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.6), zorder=7)
        ax.text(Larrow * np.cos(rad) + 0.04, Larrow * np.sin(rad) + 0.04,
                rf"$P = {ptot:.2f}\,\mathrm{{kN}}$" + "\n" + rf"（右上方 ${deg:.1f}^{{\circ}}$）",
                fontsize=9.2, color="#b91c1c", fontweight="bold", ha="left", va="bottom")

        # Component summary at bottom
        ax.text(0.05, -0.45,
                rf"$P_x = {px:.2f}\,\mathrm{{kN}}\ (\rightarrow),\quad P_z = {pz:.2f}\,\mathrm{{kN}}\ (\uparrow)$",
                fontsize=8.8, ha="center", color="#1e293b")

        ax.set_title(sub_title, fontsize=10.5, pad=6)
        ax.set_xlim(-1.35, 2.15)
        ax.set_ylim(-0.62, 3.50)
        ax.set_aspect("equal")
        ax.axis("off")

    plt.tight_layout()
    fig.savefig(dest_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2014_q29_sol(dest_path: Path):
    """Draw control-volume diagram for 2014 Calc Q4 with exact oil velocities v1=1.031 m/s, v2=2.320 m/s."""
    fig, ax = plt.subplots(figsize=(8.8, 3.5))
    fig.patch.set_facecolor("white")

    x_top = [-0.4, 2.2, 4.8, 7.6]
    y_top = [0.75, 0.75, 0.50, 0.50]
    y_bot = [-0.75, -0.75, -0.50, -0.50]

    poly_cv = [(1.1, 0.75), (2.2, 0.75), (4.8, 0.50), (5.9, 0.50),
               (5.9, -0.50), (4.8, -0.50), (2.2, -0.75), (1.1, -0.75)]
    ax.add_patch(Polygon(poly_cv, closed=True, facecolor="#e0f2fe", edgecolor="none", alpha=0.82))

    ax.plot(x_top, y_top, color="#0f172a", lw=2.8)
    ax.plot(x_top, y_bot, color="#0f172a", lw=2.8)
    ax.plot([1.1, 1.1], [-0.75, 0.75], color="#1d4ed8", lw=1.8, ls="--")
    ax.plot([5.9, 5.9], [-0.50, 0.50], color="#1d4ed8", lw=1.8, ls="--")
    ax.text(1.1, 0.84, "1-1 断面", fontsize=9.2, ha="center", color="#1e40af")
    ax.text(5.9, 0.60, "2-2 断面", fontsize=9.2, ha="center", color="#1e40af")

    # Left pressure & velocity
    ax.annotate("", xy=(1.04, -0.05), xytext=(-0.25, -0.05),
                arrowprops=dict(arrowstyle="->", color="#1d4ed8", lw=2.5))
    ax.text(0.18, 0.14,
            r"$P_1 = p_1 A_1 = 466.06\,\mathrm{N}$" + "\n" + r"$v_1 = 1.031\,\mathrm{m/s}$",
            fontsize=8.9, ha="center", color="#1e3a8a")

    # Right pressure opposing CV
    ax.annotate("", xy=(5.96, -0.05), xytext=(7.25, -0.05),
                arrowprops=dict(arrowstyle="->", color="#1d4ed8", lw=2.5))
    ax.text(6.85, 0.12,
            r"$P_2 = p_2 A_2 = 192.42\,\mathrm{N}$" + "\n" + r"$v_2 = 2.320\,\mathrm{m/s}$",
            fontsize=8.9, ha="center", color="#1e3a8a")

    # Wall reaction Rx on oil (leftward) & oil force F on reducer (rightward)
    ax.annotate("", xy=(2.55, -0.15), xytext=(4.35, -0.15),
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.5))
    ax.text(3.45, 0.05,
            r"管壁对油流反力 $R_x = 253.3\,\mathrm{N}\ (\leftarrow)$" + "\n"
            + r"油流对渐缩段作用力 $F = 253.3\,\mathrm{N}\ (\rightarrow)$",
            fontsize=9.4, ha="center", color="#b91c1c", fontweight="bold")

    ax.set_title("2014 年计算第 4 题：水平渐缩输油管段控制体动量平衡受力图", fontsize=11, pad=6)
    ax.set_xlim(-0.85, 8.05)
    ax.set_ylim(-1.05, 1.12)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(dest_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_three_slope_profile(dest_path: Path, title_txt: str, i_vals: tuple, h0_vals: tuple, hc: float, h02_conj: float, show_es_labels: bool = False):
    """Draw smooth M2 -> S2 -> submerged hydraulic jump -> S1 -> uniform h03 profile."""
    fig, ax = plt.subplots(figsize=(9.2, 4.1))
    fig.patch.set_facecolor("white")

    # Schematic x spans: seg 1 [0, 3.2], seg 2 [3.2, 6.4], seg 3 [6.4, 9.6]
    x0, x1, x2, x3 = 0.0, 3.2, 6.4, 9.6
    zb0 = 2.50
    zb1 = zb0 - 0.30
    zb2 = zb1 - 1.15
    zb3 = zb2 - 0.25

    def zb_seg(x_arr, xa, xb, za, zb):
        return za + (zb - za) * (x_arr - xa) / (xb - xa)

    # Channel bed + hatch ticks
    ax.plot([x0, x1, x2, x3], [zb0, zb1, zb2, zb3], color="#0f172a", lw=2.8, zorder=4)
    for xs, xe, zs, ze, n_tk in [(x0, x1, zb0, zb1, 9), (x1, x2, zb1, zb2, 9), (x2, x3, zb2, zb3, 9)]:
        for xt in np.linspace(xs + 0.2, xe - 0.2, n_tk):
            zt = zs + (ze - zs) * (xt - xs) / (xe - xs)
            ax.plot([xt, xt - 0.12], [zt, zt - 0.16], color="#475569", lw=1.0)

    # Break verticals
    ax.axvline(x1, ymin=0.06, ymax=0.92, color="#94a3b8", lw=1.2, ls=":")
    ax.axvline(x2, ymin=0.06, ymax=0.92, color="#94a3b8", lw=1.2, ls=":")

    # Normalized depth visual scaling so relative ordering h01 > hc > h02, h03 > h02'' > hc > h02 is crystal clear
    d_hc = 1.00
    d01 = 1.28
    d02 = 0.62
    d03 = 1.32
    d_conj = 1.17

    # Critical depth line C-C (dash-dot gray)
    for xa, xb, za, zb in [(x0, x1, zb0, zb1), (x1, x2, zb1, zb2), (x2, x3, zb2, zb3)]:
        ax.plot([xa, xb], [za + d_hc, zb + d_hc], color="#64748b", lw=1.3, ls="-.",
                label=rf"临界水深线 $C$（$h_c = {hc:.3g}\,\mathrm{{m}}$）" if xa == x0 else None)

    # Normal depth lines N-N (dashed green)
    ax.plot([x0, x1], [zb0 + d01, zb1 + d01], color="#15803d", lw=1.3, ls="--",
            label=rf"正常水深线 $N$（$h_{{01}}, h_{{02}}, h_{{03}}$）")
    ax.plot([x1, x2], [zb1 + d02, zb2 + d02], color="#15803d", lw=1.3, ls="--")
    ax.plot([x2, x3], [zb2 + d03, zb3 + d03], color="#15803d", lw=1.3, ls="--")

    # Segment 1: M2 curve (asymptotic to d01 upstream, dropping steeply to d_hc at x1)
    s1 = np.linspace(x0, x1, 100)
    u1 = (s1 - x0) / (x1 - x0)
    d1 = d01 - (d01 - d_hc) * (u1 ** 2.6)
    ax.plot(s1, zb_seg(s1, x0, x1, zb0, zb1) + d1, color="#1d4ed8", lw=2.8, zorder=6, label="实际水面曲线")

    # Segment 2a: S2 curve from x1 (d_hc) to jump toe x_j = 5.05 (approaching d02)
    xj1, xj2 = 5.00, 5.42
    s2a = np.linspace(x1, xj1, 80)
    u2a = (s2a - x1) / (xj1 - x1)
    d2a = d02 + (d_hc - d02) * np.exp(-3.4 * u2a)
    ax.plot(s2a, zb_seg(s2a, x1, x2, zb1, zb2) + d2a, color="#1d4ed8", lw=2.8, zorder=6)

    # Submerged hydraulic jump roller from xj1 (depth d2a[-1] ~ d02) to xj2 (depth d_conj)
    sj = np.linspace(xj1, xj2, 30)
    uj = (sj - xj1) / (xj2 - xj1)
    dj = d2a[-1] + (d_conj - d2a[-1]) * uj + 0.04 * np.sin(4 * np.pi * uj)
    ax.plot(sj, zb_seg(sj, x1, x2, zb1, zb2) + dj, color="#dc2626", lw=2.8, zorder=7)

    # Segment 2b: S1 backwater curve from xj2 (depth d_conj) to x2 (depth d03) — depth increases smoothly while water surface approaches horizontal!
    s2b = np.linspace(xj2, x2, 50)
    u2b = (s2b - xj2) / (x2 - xj2)
    # Linear/convex depth growth from d_conj to d03 so Z(x) = zb(x) + d(x) gently slopes down or stays nearly horizontal (NEVER a sharp peak!)
    d2b = d_conj + (d03 - d_conj) * (u2b ** 1.15)
    ax.plot(s2b, zb_seg(s2b, x1, x2, zb1, zb2) + d2b, color="#1d4ed8", lw=2.8, zorder=6)

    # Segment 3: Uniform flow at h03
    s3 = np.linspace(x2, x3, 40)
    ax.plot(s3, zb_seg(s3, x2, x3, zb2, zb3) + d03, color="#1d4ed8", lw=2.8, zorder=6)

    # Annotations
    e1 = "（$E_s$ 沿程减小）" if show_es_labels else rf"（$h_{{01}} = {h0_vals[0]:.3g}\,\mathrm{{m}}$）"
    e2 = "（$E_s$ 沿程增大）" if show_es_labels else rf"（$h_{{02}} = {h0_vals[1]:.3g}\,\mathrm{{m}}$）"
    e3 = "（$E_s$ 沿程不变）" if show_es_labels else ""

    ax.text(1.45, zb0 + d01 + 0.22, f"第 1 段缓坡 $i_1={i_vals[0]}$\n$M_2$ 降水曲线{e1}", fontsize=8.8, ha="center", color="#1e40af")
    ax.text(x1 + 0.06, zb1 + d_hc + 0.28, rf"$h_c = {hc:.3g}\,\mathrm{{m}}$", fontsize=8.8, color="#0f172a", fontweight="bold")
    ax.text(4.22, zb1 + d_hc - 0.08, f"$S_2$ 曲线{e2}", fontsize=8.5, ha="center", color="#1e40af")
    ax.text(5.72, zb_seg(5.72, x1, x2, zb1, zb2) + d_conj + 0.34,
            f"淹没水跃 + $S_1$ 曲线\n" + rf"（$h_{{02}}'' = {h02_conj:.3g}\,\mathrm{{m}} < h_{{03}}$）",
            fontsize=8.5, ha="center", color="#b91c1c")
    ax.text(8.05, zb2 + d03 + 0.18, f"第 3 段缓坡 $i_3={i_vals[2]}$\n均匀流 $h_{{03}} = {h0_vals[2]:.3g}\\,\\mathrm{{m}}${e3}",
            fontsize=8.8, ha="center", color="#1e40af")

    ax.set_title(title_txt, fontsize=11, pad=6)
    ax.legend(loc="lower left", fontsize=8.5, framealpha=0.93)
    ax.set_xlim(-0.15, 9.75)
    ax.set_ylim(0.55, 4.45)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(dest_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2013_q32_sol(dest_path: Path):
    """Draw accurate moment-equilibrium diagram for 2013 Calc Q2 with G at true midpoint L/2 = 3.08 m."""
    fig, ax = plt.subplots(figsize=(8.0, 4.3))
    fig.patch.set_facecolor("white")

    L = 6.16
    lw = 2.0
    th = np.radians(30.0)
    # Hinge O at (0, 0); gate extends up-left to (-L cos30, +L sin30)
    xT, yT = -L * np.cos(th), L * np.sin(th)
    xW, yW = -lw * np.cos(th), lw * np.sin(th)  # (-1.732, 1.0)
    xG, yG = 0.5 * xT, 0.5 * yT                 # true midpoint (-2.667, 1.54)

    # Channel bottom, vertical abutment under O, horizontal bank right of O, water surface
    ax.plot([-6.0, 0.0, 0.0, 2.2], [-1.1, -1.1, 0.0, 0.0], color="#0f172a", lw=2.2)
    ax.plot([-5.8, xW], [1.0, 1.0], color="#0284c7", lw=2.0)
    ax.text(-4.9, 1.08, r"水面（$H = 1.0\,\mathrm{m}$）", fontsize=9.2, color="#0369a1")

    # Triangular pressure prism on submerged lower part OW (normal down-left (-sin30, -cos30))
    nx, ny = np.sin(th), np.cos(th)
    pO = (-0.85 * nx, -0.85 * ny)
    ax.add_patch(Polygon([(0.0, 0.0), (xW, yW), pO], closed=True,
                         facecolor="#dbeafe", edgecolor="#2563eb", lw=1.3, alpha=0.82))

    # Gate bar OT & hinge O
    ax.plot([0.0, xT], [0.0, yT], color="#0f172a", lw=5.0, zorder=5)
    ax.scatter([0.0], [0.0], s=90, facecolor="white", edgecolor="#0f172a", lw=2.2, zorder=6)
    ax.text(0.14, -0.16, "$O$", fontsize=11, fontweight="bold")
    ax.plot([-1.4, 0.0], [0.0, 0.0], color="#64748b", lw=1.1, ls=":")
    ax.text(-1.15, 0.10, r"$30^{\circ}$", fontsize=9.2, color="#334155")

    # Hydrostatic resultant P at e = lw/3 from O, pointing UP-RIGHT (clockwise moment about O!)
    e = lw / 3.0
    xP, yP = -e * np.cos(th), e * np.sin(th)
    ax.annotate("", xy=(xP + 1.15 * nx, yP + 1.15 * ny), xytext=(xP, yP),
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.5), zorder=7)
    ax.text(xP + 1.18 * nx + 0.06, yP + 1.18 * ny,
            r"$P = 78.48\,\mathrm{kN}$（顺时针顶门力矩）" + "\n" + r"力臂 $e = \frac{1}{3}l_w = \frac{2}{3}\,\mathrm{m}$",
            fontsize=9.2, color="#b91c1c", ha="left", va="center")

    # Self-weight G at TRUE midpoint (L/2 = 3.08 m > lw = 2.0 m!), pointing straight down (counterclockwise about O!)
    ax.scatter([xG], [yG], color="#15803d", s=34, zorder=7)
    ax.annotate("", xy=(xG, -0.45), xytext=(xG, yG),
                arrowprops=dict(arrowstyle="->", color="#15803d", lw=2.5), zorder=7)
    ax.plot([xG, 0.0], [-0.45, -0.45], color="#15803d", lw=1.2, ls=":")
    ax.text(xG + 0.12, yG + 0.14,
            r"$G = Mg = 19.62\,\mathrm{kN}$" + "\n" + "（门板中点，逆时针压门力矩）",
            fontsize=9.1, color="#166534", ha="left", va="bottom")
    ax.text(0.5 * xG - 0.25, -0.72, r"水平力臂 $\frac{L}{2}\cos 30^{\circ}$", fontsize=9.0, color="#166534", ha="center")

    ax.set_title("2013 年计算第 2 题：斜置平面闸门静水总压力与自重绕底铰 $O$ 的力矩平衡图", fontsize=11, pad=6)
    ax.set_xlim(-6.1, 2.55)
    ax.set_ylim(-1.35, 3.45)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(dest_path, dpi=220, facecolor="white")
    plt.close(fig)


def clean_crop_2013_q33_orig(raw_bytes: bytes, dest_path: Path):
    """Crop out bottom third-party note from 2013/image4.png onto pure white RGB canvas."""
    im = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bg.paste(im, mask=im.split()[3])
    # Tank bottom border sits at y ~ 670 in 1488x768; bottom note starts below y ~ 705
    cropped = bg.crop((80, 65, 1410, 688))
    padded = Image.new("RGB", (cropped.width + 32, cropped.height + 32), (255, 255, 255))
    padded.paste(cropped, (16, 16))
    padded.save(dest_path, format="PNG")


def draw_2013_q33_sol(dest_path: Path):
    """Draw clean pressure-body diagram for 2013 Calc Q3 with proper subscripts (no raw underscores)."""
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.0))
    fig.patch.set_facecolor("white")

    R = 0.75
    ths_up = np.linspace(0, np.pi, 120)
    ths_dn = np.linspace(np.pi, 2 * np.pi, 120)

    # Left subplot: Upper hemisphere downward real pressure body (density rho2, height h2)
    ax = axes[0]
    h2 = 1.65
    poly_real = [(-R, h2), (R, h2)] + [(R * np.cos(t), R * np.sin(t)) for t in ths_up]
    ax.add_patch(Polygon(poly_real, closed=True, facecolor="#dbeafe", edgecolor="#2563eb", lw=1.3, alpha=0.82))
    ax.plot([-1.5, 1.5], [h2, h2], color="#0284c7", lw=2.0)
    ax.plot([-1.5, -R], [0.0, 0.0], color="#0f172a", lw=2.2)
    ax.plot([R, 1.5], [0.0, 0.0], color="#0f172a", lw=2.2)
    ax.plot(R * np.cos(ths_up), R * np.sin(ths_up), color="#0f172a", lw=2.6)
    ax.plot(R * np.cos(ths_dn), R * np.sin(ths_dn), color="#94a3b8", lw=1.4, ls="--")
    ax.annotate("", xy=(-1.15, 0.0), xytext=(-1.15, h2), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.4))
    ax.text(-1.22, 0.5 * h2, r"$h_2$", fontsize=10.5, ha="right", va="center")
    ax.annotate("", xy=(0.0, 0.68), xytext=(0.0, 1.38), arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.5))
    ax.text(0.0, 1.43, r"实压力体（$P_{\mathrm{down}}$ 向下）", fontsize=9.5, ha="center", color="#b91c1c", fontweight="bold")
    ax.set_title("上半球（液体密度 " + r"$\rho_2$" + "）：圆柱减半球", fontsize=10.2, pad=6)
    ax.set_xlim(-1.7, 1.7)
    ax.set_ylim(-0.95, 2.05)
    ax.set_aspect("equal")
    ax.axis("off")

    # Right subplot: Lower hemisphere upward virtual pressure body (density rho1, height h1)
    ax = axes[1]
    h1 = 1.85
    poly_virt = [(-R, h1), (R, h1)] + [(R * np.cos(t), R * np.sin(t)) for t in ths_dn[::-1]]
    ax.add_patch(Polygon(poly_virt, closed=True, facecolor="#ffedd5", edgecolor="#ea580c", lw=1.3, hatch="//", alpha=0.72))
    ax.plot([-1.5, 1.5], [h1, h1], color="#c2410c", lw=2.0, ls="-.")
    ax.plot([-1.5, -R], [0.0, 0.0], color="#0f172a", lw=2.2)
    ax.plot([R, 1.5], [0.0, 0.0], color="#0f172a", lw=2.2)
    ax.plot(R * np.cos(ths_up), R * np.sin(ths_up), color="#94a3b8", lw=1.4, ls="--")
    ax.plot(R * np.cos(ths_dn), R * np.sin(ths_dn), color="#0f172a", lw=2.6)
    ax.annotate("", xy=(-1.15, 0.0), xytext=(-1.15, h1), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.4))
    ax.text(-1.22, 0.5 * h1, r"$h_1$", fontsize=10.5, ha="right", va="center")
    ax.annotate("", xy=(0.0, 1.05), xytext=(0.0, 0.25), arrowprops=dict(arrowstyle="->", color="#15803d", lw=2.5))
    ax.text(0.0, 1.13, r"虚压力体（$P_{\mathrm{up}}$ 向上）", fontsize=9.5, ha="center", color="#166534", fontweight="bold")
    ax.set_title("下半球（液体密度 " + r"$\rho_1$" + "）：圆柱加半球", fontsize=10.2, pad=6)
    ax.set_xlim(-1.7, 1.7)
    ax.set_ylim(-0.95, 2.05)
    ax.set_aspect("equal")
    ax.axis("off")

    plt.tight_layout()
    fig.savefig(dest_path, dpi=220, facecolor="white")
    plt.close(fig)


# ==============================================================================
# Text Sanitization & Normalization Helpers
# ==============================================================================
BANNED_SUBSTRINGS = [
    "视频讲解", "原视频", "BV1", "B 站", "B站", "凤鸣", "阿玉", "数砖", "去水印", "视频", "真题讲解视频", "随卷参考答案"
]


def sanitize_hhu_text(s: str) -> str:
    if not s:
        return s
    s = s.replace("真题讲解视频", "参考资料")
    s = s.replace("真题视频", "参考资料")
    s = s.replace("讲解视频", "参考资料")
    s = s.replace("原视频", "常见参考资料")
    s = s.replace("视频", "参考资料")
    s = s.replace("随卷参考答案", "常见参考解答")
    # Fix KaTeX edge cases:
    # 1. Replace raw ∞ or Ω inside math if any slipped through
    s = s.replace("∞", r"\infty ")
    s = s.replace(r"\vec{Ω}", r"\vec{\Omega}")
    # 2. Fix `\tau {'}_{5}` -> `\tau'_{5}` so prime attaches cleanly
    s = s.replace(r"\tau {'}_{5}", r"\tau'_{5}")
    return s.strip()


def normalize_stem_and_note(stem: str, qtype: str) -> tuple[str, str]:
    notes = []

    def repl_note(m: re.Match) -> str:
        notes.append(m.group(1).strip())
        return ""

    stem = re.sub(r"（((?:原回忆件|原卷误印|注：原卷误印|注：疑原回忆|注：图中标注)[^）]+)）", repl_note, stem)
    if qtype == "judge":
        stem = re.sub(r"[（(]\s*[）)]\s*$", "", stem).strip()
    elif qtype in ("calc", "proof"):
        stem = re.sub(r"[（(]\d+\s*分[）)]\s*$", "", stem).strip()
    elif qtype == "fill":
        parts = re.split(r"(\$[^$]+\$)", stem)
        for i in range(0, len(parts), 2):
            parts[i] = re.sub(r"_{3,}", "________", parts[i])
        stem = "".join(parts)

    return stem.strip(), "；".join(notes)


# ==============================================================================
# Generic DOCX Year Parser + Year-Specific Overrides
# ==============================================================================
def parse_year_docx(
    year: int,
    meta_map: dict,
    judge_count: int,
    fill_count: int,
    calc_count: int,
    calc_scores: list[int],
) -> dict:
    docx_path = SRC_DIR / f"{year}年河海大学814《水力学》考研真题及详细解析.docx"
    out_dir = STD_ROOT / str(year)
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    total_q = judge_count + fill_count + calc_count
    sec_offsets = {
        "judge": 0,
        "fill": judge_count,
        "calc": judge_count + fill_count,
    }

    questions = {}
    analysis_buf = {k: [] for k in range(1, total_q + 1)}
    pitfalls_buf = {k: [] for k in range(1, total_q + 1)}

    with zipfile.ZipFile(docx_path) as zf:
        rels = {r.attrib["Id"]: r.attrib["Target"] for r in ET.fromstring(zf.read("word/_rels/document.xml.rels"))}
        body = ET.fromstring(zf.read("word/document.xml")).find("w:body", base_parser.NS)

        part1 = False
        part2 = False
        cur_sec = "judge"
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
                cur_sec = "judge"
                cur_q = None
                idx += 1
                continue
            if ctag == "p" and raw_txt.startswith("二、填空题"):
                cur_sec = "fill"
                cur_q = None
                idx += 1
                continue
            if ctag == "p" and raw_txt.startswith("三、计算题"):
                cur_sec = "calc"
                cur_q = None
                idx += 1
                continue

            # --- Part 1: Exam Stems & Figures ---
            if part1 and not part2:
                if ctag == "tbl" and cur_q is not None:
                    tmd = sanitize_hhu_text(base_parser.table_to_markdown(el, rels))
                    if tmd:
                        questions[cur_q]["stem"] += "\n\n" + tmd
                    idx += 1
                    continue

                if ctag == "p":
                    md, imgs = base_parser.paragraph_to_markdown(el, rels)
                    md = sanitize_hhu_text(md)

                    m_q = re.match(r"^(\d{1,2})\.\s*(.+)$", md, flags=re.DOTALL)
                    if m_q:
                        local_no = int(m_q.group(1))
                        qno = sec_offsets[cur_sec] + local_no
                        qmeta = meta_map[qno]
                        if cur_sec == "judge":
                            qtype = "judge"
                            score = 2
                        elif cur_sec == "fill":
                            qtype = "fill"
                            score = 2
                        else:
                            qtype = qmeta.get("qtype_override", "calc")
                            score = calc_scores[local_no - 1]

                        stem_clean, note_txt = normalize_stem_and_note(m_q.group(2).strip(), qtype)
                        questions[qno] = {
                            "id": f"{year}-{qno:02d}",
                            "year": year,
                            "no": qno,
                            "type": qtype,
                            "score": score,
                            "title": qmeta["title"],
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
                            raw_img = zf.read("word/" + media_rel)
                            if year == 2013 and cur_q == 33:
                                clean_crop_2013_q33_orig(raw_img, fig_dir / fname)
                            else:
                                (fig_dir / fname).write_bytes(raw_img)
                            questions[cur_q]["figures"].append({"src": f"figures/{fname}", "caption": f"题 {cur_q} 图"})
                        idx += 1
                        continue

                    if md and cur_q is not None and not md.startswith("原卷附图"):
                        extra_clean, extra_note = normalize_stem_and_note(md, questions[cur_q]["type"])
                        questions[cur_q]["stem"] += "\n\n" + extra_clean
                        if extra_note:
                            questions[cur_q]["note"] = (
                                questions[cur_q]["note"] + "；" + extra_note if questions[cur_q]["note"] else extra_note
                            )
                idx += 1
                continue

            # --- Part 2: Solutions & Solution Figures ---
            if part2 and ctag == "p":
                md, imgs = base_parser.paragraph_to_markdown(el, rels)
                md = sanitize_hhu_text(md)

                m_sol = re.match(r"^第\s*(\d{1,2})\s*题\s*【参考答案】\s*(.+)$", md)
                if m_sol:
                    local_no = int(m_sol.group(1))
                    cur_q = sec_offsets[cur_sec] + local_no
                    ans_txt = m_sol.group(2).strip()
                    questions[cur_q]["answer"] = ans_txt
                    questions[cur_q]["shortAnswer"] = ans_txt
                    if cur_sec == "judge":
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
                        (fig_dir / fname).write_bytes(zf.read("word/" + media_rel))
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
                if md.startswith("【解题思路】"):
                    md = md.replace("【解题思路】", "解题思路：", 1).strip()

                if md.startswith("【注意纠错】"):
                    pitfalls_buf[cur_q].append(md.replace("【注意纠错】", "", 1).strip())
                elif md:
                    analysis_buf[cur_q].append(md)

            idx += 1

    final_questions = []
    for qno in range(1, total_q + 1):
        q = questions[qno]
        q["analysis"] = "\n\n".join(analysis_buf[qno]).strip()
        q["pitfalls"] = "\n\n".join(pitfalls_buf[qno]).strip()
        meta = meta_map[qno]
        q["chapter"] = meta["chapter"]
        q["kps"] = meta["kps"]
        q["method"] = meta["method"]
        q["difficulty"] = meta["difficulty"]
        if "subType" in meta:
            q["subType"] = meta["subType"]
        if "rubric" in meta:
            q["rubric"] = meta["rubric"]
        final_questions.append(q)

    # Apply rigorous physics & diagram overrides per year
    apply_year_overrides(year, final_questions, fig_dir)

    judge_total = judge_count * 2
    fill_total = fill_count * 2
    calc_total = sum(calc_scores)
    calc_desc_scores = "+".join(str(s) for s in calc_scores)

    sec_calc_title = "三、计算与证明题" if year == 2013 else "三、计算题"
    paper = {
        "year": year,
        "code": "814",
        "subject": "水力学",
        "school": "河海大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": False,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "除特别说明外，统一取重力加速度 g = 9.81 m/s²，水密度 ρ = 1000 kg/m³。",
            f"题型与分值：一、是非题（{judge_count}×2={judge_total} 分）；二、填空题（{fill_count}×2={fill_total} 分）；{sec_calc_title}（共 {calc_count} 题，分别为 {'、'.join(str(s) for s in calc_scores)} 分，共 {calc_total} 分）。",
        ],
        "sections": [
            {
                "id": "judge",
                "title": "一、是非题",
                "description": f"共 {judge_count} 小题，每小题 2 分，共 {judge_total} 分。",
                "range": [1, judge_count],
                "scorePerQuestion": 2,
                "totalScore": judge_total,
            },
            {
                "id": "fill",
                "title": "二、填空题",
                "description": f"共 {fill_count} 小题，每小题 2 分，共 {fill_total} 分。",
                "range": [judge_count + 1, judge_count + fill_count],
                "scorePerQuestion": 2,
                "totalScore": fill_total,
            },
            {
                "id": "calc",
                "title": sec_calc_title,
                "description": f"共 {calc_count} 小题（{calc_desc_scores} 分），共 {calc_total} 分。",
                "range": [judge_count + fill_count + 1, total_q],
                "totalScore": calc_total,
            },
        ],
        "questions": final_questions,
    }

    # 1. Write standardized JSON
    std_json_path = out_dir / f"{year}.json"
    std_json_path.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2. Write web-ready JSON + WebP figures (PIL quality=90, method=5)
    web_paper = copy.deepcopy(paper)
    web_fig_dir = WEB_COURSE_DIR / "figures" / str(year)
    web_fig_dir.mkdir(parents=True, exist_ok=True)
    web_fig_count = 0

    for q in web_paper["questions"]:
        for flist_key in ("figures", "analysisFigures"):
            new_list = []
            for fig in q.get(flist_key, []):
                src_png = out_dir / fig["src"]
                stem_name = src_png.stem
                webp_name = f"{stem_name}.webp"
                dest_webp = web_fig_dir / webp_name
                with Image.open(src_png) as im:
                    if im.mode not in ("RGB", "RGBA"):
                        im = im.convert("RGBA")
                    im.save(dest_webp, format="WEBP", quality=90, method=5)
                new_list.append({
                    "src": f"figures/{year}/{webp_name}",
                    "caption": fig["caption"],
                })
                web_fig_count += 1
            q[flist_key] = new_list

    web_json_path = WEB_COURSE_DIR / f"{year}.json"
    web_json_path.write_text(json.dumps(web_paper, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {year}: {len(final_questions)} questions ({sum(q['score'] for q in final_questions)} pts), {web_fig_count} figures -> {std_json_path.name} & web/{year}.json")
    return web_paper


def apply_year_overrides(year: int, qs: list[dict], fig_dir: Path):
    by_no = {q["no"]: q for q in qs}

    if year == 2015:
        # Q04: Accurate analysis matching image2.png (narrow pipe -> sudden expansion -> submerged reservoir) + clean diagram
        q04 = by_no[4]
        draw_2015_q04_sol(fig_dir / "q04_sol.png")
        q04["analysis"] = (
            "对照原卷题图逐项校核总水头线与测压管水头线的三处明显错误：\n\n"
            "1. 管径突然扩大处流速水头关系画反：前段细管过水断面小、平均流速大，后段粗管断面扩大、平均流速 $v_{1}$ 减小，故总水头线与测压管水头线之间的竖直间距（即流速水头 $\\frac{\\alpha v^{2}}{2g}$）在突扩后必须收窄（测压管水头线应局部回升靠近总水头线），而题图在转折扩大处将测压管水头线画成同步下跌、间距未收窄；\n\n"
            "2. 下游淹没出流边界条件错误：管道淹没接入下游水池时，出口断面的测压管水头必须等于下游水池自由水面高程（测压管水头线末端应恰好落在下游水面上），而题图中测压管水头线末端悬空高于下游水面；\n\n"
            "3. 上下游水池流速水头标注矛盾：图中标注 $v_{0}\\neq 0$、$v_{3}\\neq 0$，此时水池内总水头线应位于自由水面上方 $\\frac{\\alpha v_{0}^{2}}{2g}$（及 $\\frac{\\alpha v_{3}^{2}}{2g}$）处。\n\n"
            "因此题图定性绘制错误。"
        )

        # Q09: CRITICAL FIX — True -> False!
        q09 = by_no[9]
        q09["judgeAnswer"] = False
        q09["shortAnswer"] = "×"
        q09["answer"] = "×（错误）"
        q09["analysis"] = (
            "对宽浅棱柱形矩形渠道，水力半径 $R\\approx h$。设单宽流量为 $q=Q/b$：\n\n"
            "1. 若按曼宁公式 $C=\\frac{1}{n}h^{1/6}$ 计算，均匀流正常水深满足 $q=\\frac{1}{n}h_{0}^{5/3}i^{1/2}$，即：\n\n"
            "$$\nh_{0}=\\left(\\frac{nq}{\\sqrt{i}}\\right)^{3/5}\\propto q^{3/5}=q^{0.60}\n$$\n\n"
            "而矩形断面临界水深为：\n\n"
            "$$\nh_{c}=\\sqrt[3]{\\frac{\\alpha q^{2}}{g}}\\propto q^{2/3}\\approx q^{0.667}\n$$\n\n"
            "可见比值 $\\frac{h_{0}}{h_{c}}\\propto q^{3/5-2/3}=q^{-1/15}$（或均匀流弗劳德数 $Fr_{0}=\\frac{q}{\\sqrt{g}h_{0}^{3/2}}\\propto q^{1/10}$）。已知流量为 $Q$ 时水流为急流，即初始已有 $h_{0} < h_{c}$（$Fr_{0} > 1$，或底坡 $i > i_{c1}$）；当流量 $Q$（即 $q$）增大时，$h_{c}$ 增长得比 $h_{0}$ 更快（临界底坡 $i_{c}=\\frac{gn^{2}}{h_{c}^{1/3}}$ 随 $Q$ 增大而进一步减小，故仍有 $i > i_{c1} > i_{c2}$），因此 $\\frac{h_{0}}{h_{c}}$ 进一步减小、$Fr_{0}$ 进一步增大，水流必定维持急流，绝不可能变为缓流！\n\n"
            "2. 若按谢才系数 $C$ 为常数简化，则 $h_{0}=\\left(\\frac{q}{C\\sqrt{i}}\\right)^{2/3}\\propto q^{2/3}$，比值 $\\frac{h_{0}}{h_{c}}$ 与流量无关，同样保持急流不变。\n\n"
            "故题干表述错误。"
        )
        q09["pitfalls"] = (
            "极易因不等式方向推反而误判为 √！记住宽浅矩形明渠临界底坡 $i_{c}=\\frac{gn^{2}}{h_{c}^{1/3}}$ 随流量 $Q$ 增大而减小："
            "只有初始为缓流（$i < i_{c}$）时增大流量才可能使 $i_{c}$ 降到 $i$ 以下而转为急流；初始已是急流（$i > i_{c}$）时，流量增大只会使急流程度更强，唯有减小流量才可能转为缓流。"
        )

        # Q11: Clean minor typo "等压面于" -> "等压面与"
        by_no[11]["stem"] = by_no[11]["stem"].replace("等压面于", "等压面与")

        # Q27: Redraw clean pressure-body diagram
        draw_2015_q27_sol(fig_dir / "q27_sol.png")

        # Q29: Clean consistent sign convention for Rx, Ry
        q29 = by_no[29]
        q29["analysis"] = (
            "1. 求 A、B 两断面平均流速与 B 断面压强\n\n"
            "$$\nA_{A}=\\frac{\\pi}{4}\\times 0.20^{2}=0.031416\\,\\mathrm{m^{2}},\\quad A_{B}=\\frac{\\pi}{4}\\times 0.15^{2}=0.017671\\,\\mathrm{m^{2}}\n$$\n\n"
            "$$\nv_{A}=\\frac{Q}{A_{A}}=\\frac{0.1}{0.031416}=3.183\\,\\mathrm{m/s},\\quad v_{B}=\\frac{Q}{A_{B}}=\\frac{0.1}{0.017671}=5.659\\,\\mathrm{m/s}\n$$\n\n"
            "管轴位于同一水平面（$z_{A}=z_{B}$）且不计水头损失（$h_{w}=0$），取 $\\alpha =1$ 列能量方程：\n\n"
            "$$\n\\frac{p_{A}}{\\rho g}+\\frac{v_{A}^{2}}{2g}=\\frac{p_{B}}{\\rho g}+\\frac{v_{B}^{2}}{2g}\\Rightarrow p_{B}=p_{A}+\\frac{1}{2}\\rho (v_{A}^{2}-v_{B}^{2})\n$$\n\n"
            "$$\np_{B}=120000+500\\times (3.183^{2}-5.659^{2})=120000-10945=109055\\,\\mathrm{Pa}\\approx 109.06\\,\\mathrm{kPa}\n$$\n\n"
            "2. 取渐缩弯管控制体列水平面 $x$、$y$ 方向动量方程\n\n"
            "建立平面直角坐标系：取 $x$ 轴沿 A 管来流方向向右为正，$y$ 轴在水平面内垂直 A 管向上为正。两端面总压力为：\n\n"
            "$$\nP_{A}=p_{A}A_{A}=120000\\times 0.031416=3769.9\\,\\mathrm{N},\\quad P_{B}=p_{B}A_{B}=109055\\times 0.017671=1927.2\\,\\mathrm{N}\n$$\n\n"
            "设弯管壁对控制体水体的反力分量为 $R_{x}$（向左，即 $-x$ 向）和 $R_{y}$（向下，即 $-y$ 向），出口流速偏角 $\\theta =60^{\\circ}$（$v_{Bx}=v_{B}\\cos 60^{\\circ}$，$v_{By}=-v_{B}\\sin 60^{\\circ}$）：\n\n"
            "- $x$ 方向动量方程：$P_{A}-P_{B}\\cos 60^{\\circ}-R_{x}=\\rho Q(v_{B}\\cos 60^{\\circ}-v_{A})$\n\n"
            "$$\nR_{x}=3769.9-1927.2\\times 0.5-1000\\times 0.1\\times (5.659\\times 0.5-3.183)=2841.7\\,\\mathrm{N}\\,(\\text{向左})\n$$\n\n"
            "- $y$ 方向动量方程：$P_{B}\\sin 60^{\\circ}-R_{y}=\\rho Q(-v_{B}\\sin 60^{\\circ}-0)$\n\n"
            "$$\nR_{y}=(P_{B}+\\rho Qv_{B})\\sin 60^{\\circ}=(1927.2+1000\\times 0.1\\times 5.659)\\times 0.86603=2159.0\\,\\mathrm{N}\\,(\\text{向下})\n$$\n\n"
            "3. 求水流对弯管的总作用力 $F$\n\n"
            "由牛顿第三定律，水流对弯管的作用力分量分别为 $F_{x}=2841.7\\,\\mathrm{N}$（向右）、$F_{y}=2159.0\\,\\mathrm{N}$（向上），合力大小为：\n\n"
            "$$\nF=\\sqrt{F_{x}^{2}+F_{y}^{2}}=\\sqrt{2841.7^{2}+2159.0^{2}}=3568.9\\,\\mathrm{N}\\approx 3.569\\,\\mathrm{kN}\n$$\n\n"
            "方向在水平面内指向弯管外侧（右上方），与 A 管来流方向夹角 $\\varphi =\\arctan\\frac{2159.0}{2841.7}=37.23^{\\circ}$。"
        )

        # Q30: Fix intermediate rounding typo 1.12904 -> 1.1312, 4.4285 -> 4.4200
        q30 = by_no[30]
        q30["analysis"] = (
            "半正六边形过水断面可分割为三个边长均为 $b$ 的等边三角形（边坡内角 $120^{\\circ}$，斜壁倾角 $60^{\\circ}$）：\n\n"
            "- 过水断面面积：$A=3\\times \\frac{\\sqrt{3}}{4}b^{2}=\\frac{3\\sqrt{3}}{4}b^{2}\\approx 1.29904\\,b^{2}$\n\n"
            "- 湿周：$\\chi =b+b+b=3b$\n\n"
            "- 水力半径：$R=\\frac{A}{\\chi}=\\frac{\\sqrt{3}}{4}b\\approx 0.43301\\,b$\n\n"
            "代入明渠均匀流曼宁公式 $Q=\\frac{1}{n}AR^{2/3}i^{1/2}$：\n\n"
            "$$\n5=\\frac{1}{0.012}\\cdot \\left(\\frac{3\\sqrt{3}}{4}b^{2}\\right)\\cdot \\left(\\frac{\\sqrt{3}}{4}b\\right)^{2/3}\\cdot \\sqrt{\\frac{1}{3000}}\n$$\n\n"
            "计算常数项系数：\n\n"
            "$$\n\\frac{1}{0.012}\\times 1.29904\\times (0.43301)^{2/3}\\times 0.0182574=1.13122\n$$\n\n"
            "故 $1.13122\\,b^{8/3}=5\\Rightarrow b^{8/3}=4.4200\\Rightarrow b=4.4200^{3/8}\\approx 1.746\\,\\mathrm{m}$。\n\n"
            "渠道正常水深即半正六边形高度：\n\n"
            "$$\nh_{0}=b\\sin 60^{\\circ}=1.746\\times \\frac{\\sqrt{3}}{2}\\approx 1.512\\,\\mathrm{m}\n$$"
        )

    elif year == 2014:
        # Q20: Accept both 远驱式 and 远离式
        by_no[20]["shortAnswer"] = "远离式（远驱式）"
        by_no[20]["answer"] = "远离式（或远驱式）"

        # Q27: CRITICAL FIX — fluid is INSIDE the tank beneath convex arc AB -> virtual pressure body UPWARD, resultant UPWARD-RIGHT!
        q27 = by_no[27]
        draw_2014_q27_sol(fig_dir / "q27_sol.png")
        q27["shortAnswer"] = "(a) P = 32.76 kN（右上方 41.5°）；(b) P = 33.78 kN（右上方 41.0°）"
        q27["answer"] = "（a）$P=32.76\\,\\mathrm{kN}$（过圆心指向右上方，与水平面夹角 $\\theta =41.5^{\\circ}$）；（b）$P=33.78\\,\\mathrm{kN}$（过圆心指向右上方，与水平面夹角 $\\theta =41.0^{\\circ}$）"
        q27["analysis"] = (
            "由原卷题图可知，两个容器内的液体均位于 $1/4$ 圆弧钢板 $AB$ 的左下方（容器内部），圆弧外部为大气。因此液体对圆弧钢板 $AB$ 的水平静水压力 $P_{x}$ 指向右方，铅垂静水压力 $P_{z}$ 对应圆弧上方的虚压力体、方向铅垂向上！\n\n"
            "（a）单一液体 $\\rho_{1}=1000\\,\\mathrm{kg/m^{3}}$\n\n"
            "$A$ 点淹深 $h_{A}=H-R=3-1=2\\,\\mathrm{m}$，$B$ 点淹深 $h_{B}=H=3\\,\\mathrm{m}$。\n\n"
            "- 水平分力 $P_{x}$（水平向右）：\n\n"
            "$$\nP_{x}=\\rho_{1}gh_{c}A_{x}=1000\\times 9.81\\times \\frac{2+3}{2}\\times (1\\times 1)=24525\\,\\mathrm{N}\\approx 24.53\\,\\mathrm{kN}\n$$\n\n"
            "- 铅垂分力 $P_{z}$（铅垂向上，圆弧 $AB$ 至自由液面围成的虚压力体体积为宽 $R$、高 $H$ 的矩形柱扣除半径 $R$ 的 $1/4$ 圆柱）：\n\n"
            "$$\nP_{z}=\\rho_{1}g\\left(HR-\\frac{1}{4}\\pi R^{2}\\right)b=1000\\times 9.81\\times \\left(3\\times 1-\\frac{\\pi}{4}\\right)\\times 1=21725.2\\,\\mathrm{N}\\approx 21.73\\,\\mathrm{kN}\n$$\n\n"
            "- 静水总压力大小及方向：\n\n"
            "$$\nP=\\sqrt{P_{x}^{2}+P_{z}^{2}}=\\sqrt{24.525^{2}+21.725^{2}}\\approx 32.76\\,\\mathrm{kN}\n$$\n\n"
            "$$\n\\theta =\\arctan\\frac{P_{z}}{P_{x}}=\\arctan\\frac{21.725}{24.525}=41.54^{\\circ}\\approx 41.5^{\\circ}\\,(\\text{作用线过圆心 }O\\text{，指向右上方})\n$$\n\n"
            "（b）双层液体 $\\rho_{1}=1000\\,\\mathrm{kg/m^{3}}$（上层厚 $2\\,\\mathrm{m}$）、$\\rho_{2}=1200\\,\\mathrm{kg/m^{3}}$（下层厚 $1\\,\\mathrm{m}$）\n\n"
            "两液体交界面恰位于 $A$ 点所在水平面（深 $h_{A}=2\\,\\mathrm{m}$），圆弧 $AB$ 完全与下层液体 $\\rho_{2}$ 接触。\n\n"
            "- 水平分力 $P_{x}$（水平向右）：\n\n"
            "$$\np_{A}=\\rho_{1}g(H-R)=1000\\times 9.81\\times 2=19620\\,\\mathrm{Pa}\n$$\n\n"
            "$$\np_{B}=p_{A}+\\rho_{2}gR=19620+1200\\times 9.81\\times 1=31392\\,\\mathrm{Pa}\n$$\n\n"
            "$$\nP_{x}=\\frac{p_{A}+p_{B}}{2}Rb=\\frac{19620+31392}{2}\\times 1\\times 1=25506\\,\\mathrm{N}\\approx 25.51\\,\\mathrm{kN}\n$$\n\n"
            "- 铅垂分力 $P_{z}$（铅垂向上，在距离右壁 $x\\in[0,R]$ 处圆弧高 $y=\\sqrt{R^{2}-x^{2}}$，压强 $p(x)=\\rho_{1}g(H-R)+\\rho_{2}g(R-y)$，沿水平投影积分得）：\n\n"
            "$$\nP_{z}=\\left[\\rho_{1}g(H-R)R+\\rho_{2}g\\left(R^{2}-\\frac{1}{4}\\pi R^{2}\\right)\\right]b=9.81\\times \\left[1000\\times 2+1200\\times \\left(1-\\frac{\\pi}{4}\\right)\\right]\\times 1=22146.3\\,\\mathrm{N}\\approx 22.15\\,\\mathrm{kN}\n$$\n\n"
            "- 静水总压力大小及方向（即使流体分层，圆弧面上各微元静水压力仍处处沿法线通过圆心 $O$，故合力作用线依然严格过圆心 $O$）：\n\n"
            "$$\nP=\\sqrt{25.506^{2}+22.146^{2}}\\approx 33.78\\,\\mathrm{kN},\\quad \\theta =\\arctan\\frac{22.146}{25.506}=40.97^{\\circ}\\approx 41.0^{\\circ}\\,(\\text{过圆心 }O\\text{，指向右上方})\n$$"
        )
        q27["pitfalls"] = (
            "审图头号陷阱：切忌受思维定势影响误把圆弧外侧空白区当作盛水区而写成“实压力体向下、合力向右下”！"
            "原卷图中液体装在容器内部（圆弧钢板 $AB$ 左下方），液体向上顶托凸圆弧顶盖，因此铅垂分力 $P_{z}$ 必定铅垂向上（虚压力体），总压力指向右上方。"
        )

        # Q29: Redraw control-volume diagram with exact oil velocities
        draw_2014_q29_sol(fig_dir / "q29_sol.png")

        # Q31: Redraw smooth three-slope profile fixing h02'' = 0.945 m and smooth S1 curve
        draw_three_slope_profile(
            fig_dir / "q31_sol.png",
            title_txt="2014 年计算第 6 题：缓—陡—缓三坡段明渠水面曲线与淹没水跃定性绘制图",
            i_vals=(0.001, 0.006, 0.0012),
            h0_vals=(1.036, 0.570, 0.975),
            hc=0.742,
            h02_conj=0.945,
            show_es_labels=False,
        )

    elif year == 2013:
        # Q04: Add clear prismatic channel example u(y,z) so 2D uniform flow is airtight under all textbook conventions
        q04 = by_no[4]
        q04["analysis"] = (
            "二元流（二维流）是指运动要素仅取决于两个空间坐标的流动，而均匀流是指流线为平行直线、运动要素沿流线方向不随流程改变的流动，两者划分依据完全独立。"
            "例如长直棱柱形矩形明渠或非圆截面管道中的恒定均匀流，流线均为平行于渠轴线 $x$ 的直线（$\\frac{\\partial u}{\\partial x}=0$，属于均匀流），但断面上流速 $u(y,z)$ 同时随横向 $y$ 与垂向 $z$ 两个坐标变化（属于二元流）；平面平行平板间的恒定层流在平面坐标系下亦常作二元均匀流处理。故二元流可以是均匀流，题干错误。"
        )

        # Q17: Place the 10-second velocity table before the fill-in-the-blank prompt for natural reading order
        q17 = by_no[17]
        q17["stem"] = (
            "下表为某次试验中所测得的水流中某点的流速：\n\n"
            "时间（s）：1 ｜ 2 ｜ 3 ｜ 4 ｜ 5 ｜ 6 ｜ 7 ｜ 8 ｜ 9 ｜ 10\n\n"
            "$X$ 方向流速（m/s）：1.04 ｜ 1.04 ｜ 1.05 ｜ 1.00 ｜ 1.05 ｜ 1.00 ｜ 0.97 ｜ 0.96 ｜ 1.05 ｜ 1.00\n\n"
            "$Y$ 方向流速（m/s）：0.09 ｜ 0.09 ｜ 0.09 ｜ 0.10 ｜ 0.09 ｜ 0.10 ｜ 0.11 ｜ 0.11 ｜ 0.09 ｜ 0.10\n\n"
            "则在 $5\\,\\mathrm{s}$ 时，该点紊动附加切应力为________ $\\mathrm{N/m^{2}}$。"
        )

        # Q32: Fix moment sense labels (P clockwise, G counterclockwise about bottom-right hinge O) + redraw accurate G position
        q32 = by_no[32]
        draw_2013_q32_sol(fig_dir / "q32_sol.png")
        q32["analysis"] = (
            "解题思路：闸门绕底端无摩擦铰链 $O$ 处于静力平衡，对底铰 $O$ 列力矩平衡方程即可求得闸门总长 $L$。\n\n"
            "1. 计算斜置闸门所受静水总压力 $P$ 及其对底铰 $O$ 的力臂\n\n"
            "闸门浸水挡水部分的斜长 $l_{w}=\\frac{H}{\\sin\\theta}=\\frac{1.0}{\\sin 30^{\\circ}}=2.0\\,\\mathrm{m}$，受压面积 $A=b\\cdot l_{w}=8\\times 2.0=16.0\\,\\mathrm{m^{2}}$。\n\n"
            "受压面形心淹深 $h_{c}=\\frac{H}{2}=0.5\\,\\mathrm{m}$，静水总压力大小为：\n\n"
            "$$\nP=\\rho gh_{c}A=1000\\times 9.81\\times 0.5\\times 16.0=78480\\,\\mathrm{N}=78.48\\,\\mathrm{kN}\n$$\n\n"
            "因受压面顶边与自由水面齐平，压强分布呈三角形，压心距底端铰链 $O$ 的斜距为：\n\n"
            "$$\ne=\\frac{1}{3}l_{w}=\\frac{2.0}{3}\\,\\mathrm{m}\n$$\n\n"
            "静水总压力 $P$ 垂直于闸门指向右上方，绕底铰 $O$ 产生顺时针顶门力矩（力臂为 $e$）。\n\n"
            "2. 计算闸门自重 $G$ 对底铰 $O$ 的力矩\n\n"
            "匀质闸门总长为 $L$，自重 $G=Mg=2000\\times 9.81=19620\\,\\mathrm{N}$ 作用于门板几何中点（距底铰 $O$ 斜距为 $\\frac{L}{2}$），方向竖直向下，绕底铰 $O$ 产生逆时针压门力矩，水平力臂为 $\\frac{L}{2}\\cos 30^{\\circ}$。\n\n"
            "3. 对底铰 $O$ 列力矩平衡方程 $\\sum M_{O}=0$\n\n"
            "$$\nG\\cdot \\frac{L}{2}\\cos 30^{\\circ}=P\\cdot e\n$$\n\n"
            "代入数值：\n\n"
            "$$\n19620\\times \\frac{L}{2}\\times \\frac{\\sqrt{3}}{2}=78480\\times \\frac{2.0}{3}\n$$\n\n"
            "解得：\n\n"
            "$$\nL=\\frac{2\\times 78480\\times \\frac{2}{3}}{19620\\times \\frac{\\sqrt{3}}{2}}=\\frac{32}{3\\sqrt{3}}\\approx 6.158\\,\\mathrm{m}\\approx 6.16\\,\\mathrm{m}\n$$"
        )
        q32["pitfalls"] = (
            "易错点提醒：① 浸水斜长 $l_{w}=\\frac{H}{\\sin 30^{\\circ}}=2.0\\,\\mathrm{m}$ 仅占闸门下部一段，水压力压心距底铰 $O$ 为 $\\frac{1}{3}l_{w}$ 而非 $\\frac{1}{3}L$；"
            "② 闸门自重 $G$ 作用在全门长中点 $\\frac{L}{2}$ 处，水平力臂为 $\\frac{L}{2}\\cos 30^{\\circ}$，切勿与浸水长度混淆。"
        )

        # Q33: Redraw clean pressure-body solution figure without raw underscore text
        draw_2013_q33_sol(fig_dir / "q33_sol.png")

        # Q34: Redraw smooth three-slope profile without upward V-kink on S1
        draw_three_slope_profile(
            fig_dir / "q34_sol.png",
            title_txt="2013 年计算第 4 题：三坡段宽浅明渠水面线、比能变化与淹没水跃位置图",
            i_vals=(0.002, 0.005, 0.001),
            h0_vals=(4.43, 3.27, 5.59),
            hc=4.00,
            h02_conj=4.84,
            show_es_labels=True,
        )


def self_verify_papers(papers: list[dict]):
    valid_chapters = {c["chapter"] for c in json.loads((WEB_COURSE_DIR / "chapters.json").read_text(encoding="utf-8"))["chapters"]}
    assert valid_chapters == {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}, f"Unexpected chapters: {valid_chapters}"

    for p in papers:
        yr = p["year"]
        qs = p["questions"]
        nos = [q["no"] for q in qs]
        assert nos == list(range(1, len(qs) + 1)), f"{yr}: non-consecutive nos {nos}"
        assert sum(q["score"] for q in qs) == p["totalScore"] == 150, f"{yr}: score sum != 150"
        assert p["sections"][0]["range"][0] == 1 and p["sections"][-1]["range"][1] == len(qs), f"{yr}: section range mismatch"

        for q in qs:
            assert q["id"] == f"{yr}-{q['no']:02d}", f"Bad id {q['id']}"
            assert q["chapter"] in valid_chapters, f"{q['id']}: invalid chapter {q['chapter']}"
            if q["type"] in ("short", "calc", "proof") and q["score"] >= 5:
                assert q.get("rubric") and sum(r["pts"] for r in q["rubric"]) == q["score"], f"{q['id']}: rubric sum mismatch"
            if q["type"] == "judge":
                assert isinstance(q["judgeAnswer"], bool), f"{q['id']}: missing boolean judgeAnswer"
            if q["type"] == "fill":
                assert "________" in q["stem"], f"{q['id']}: fill stem missing 8 underscores"

            for field in ("title", "stem", "note", "shortAnswer", "answer", "analysis", "pitfalls"):
                val = q.get(field, "") or ""
                for bw in BANNED_SUBSTRINGS:
                    assert bw not in val, f"{q['id']}.{field} contains banned word: {bw}"

            for fig in q.get("figures", []) + q.get("analysisFigures", []):
                wpath = WEB_COURSE_DIR / fig["src"]
                assert wpath.exists() and wpath.stat().st_size > 200, f"{q['id']}: missing/empty webp {wpath}"

    print("[SELF-VERIFY] Python schema, chapters, scores, rubrics, underscores, WebP files & banned-word checks: 100% PASSED!")


def main():
    p2015 = parse_year_docx(2015, META_2015, judge_count=10, fill_count=15, calc_count=6, calc_scores=[10, 20, 20, 20, 15, 15])
    p2014 = parse_year_docx(2014, META_2014, judge_count=10, fill_count=15, calc_count=6, calc_scores=[10, 20, 20, 20, 15, 15])
    p2013 = parse_year_docx(2013, META_2013, judge_count=15, fill_count=15, calc_count=6, calc_scores=[20, 15, 15, 15, 15, 10])
    self_verify_papers([p2015, p2014, p2013])


if __name__ == "__main__":
    main()
