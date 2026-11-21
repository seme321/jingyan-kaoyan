# -*- coding: utf-8 -*-
"""
Parse Hohai University 814 Hydraulics exam .docx files for years 2018, 2017, 2016 into:
1. Standardized exam packs: `河海大学已整理数据/{year}/{year}.json` + `figures/*.png`
2. Web-ready JSONs & WebP figures: `web/public/data/hhu-814/{year}.json` + `figures/{year}/*.webp`

Strictly self-contained: does NOT touch index.json, courses.json, sw.js, HANDOFF.md, or other years.
"""

import copy
import io
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parse_2024_2025 as base_parser

# Extend OMML symbol mappings for 2016-2018 docx files
base_parser.GREEK_AND_MATH_MAP.update({
    "κ": r"\kappa ",
    "∑": r"\sum ",
    "∈": r"\in ",
    "Φ": r"\Phi ",
    "–": "-",
    "—": r"\text{—}",
    "∫": r"\int ",
    "∞": r"\infty ",
})

ROOT = Path(__file__).resolve().parent.parent
SRC_DOCX_DIR = ROOT / "河海大学已整理真题"
STD_OUT_ROOT = ROOT / "河海大学已整理数据"
WEB_OUT_ROOT = ROOT / "web" / "public" / "data" / "hhu-814"

VALID_CHAPTERS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}


# ==============================================================================
# Curated Metadata for 2018 (Q1 - Q31)
# ==============================================================================
META_2018 = {
    1:  {"title": "牛顿内摩擦定律中切应力与速度梯度关系辨析", "chapter": 1, "kps": ["牛顿内摩擦定律"], "method": "概念偷换词辨析", "difficulty": 1},
    2:  {"title": "有压流动测压管水头线沿程升降变化规律", "chapter": 6, "kps": ["总水头线与测压管水头线", "恒定总流能量方程"], "method": "总水头线与测压管水头线判据", "difficulty": 2},
    3:  {"title": "同一明渠水流在不同紊流阻力分区间的转化", "chapter": 4, "kps": ["紊流阻力分区"], "method": "物理概念定义辨析", "difficulty": 2},
    4:  {"title": "实际液体流场中流函数与势函数存在条件辨析", "chapter": 5, "kps": ["平面不可压缩流连续性方程", "无旋流判据", "流函数与速度势函数求解"], "method": "物理概念定义辨析", "difficulty": 2},
    5:  {"title": "层流与急变流双维度流态分类兼容性判别", "chapter": 3, "kps": ["恒定流与均匀流判别", "雷诺数与流态判别"], "method": "物理概念定义辨析", "difficulty": 2},
    6:  {"title": "边壁切应力公式 τ=ρgRJ 的均匀流适用前提", "chapter": 4, "kps": ["圆管均匀流切应力分布", "沿程水头损失规律"], "method": "物理概念定义辨析", "difficulty": 2},
    7:  {"title": "剪切流中点流速大小与切应力极值位置对比", "chapter": 1, "kps": ["牛顿内摩擦定律"], "method": "概念偷换词辨析", "difficulty": 1},
    8:  {"title": "底坡变化对明渠均匀流正常水深的影响", "chapter": 7, "kps": ["明渠均匀流曼宁公式"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 1},
    9:  {"title": "负坡明渠非均匀流断面比能沿程变化规律", "chapter": 8, "kps": ["断面单位能量(比能)", "明渠渐变流基本微分方程"], "method": "比能沿程导数判别法", "difficulty": 2},
    10: {"title": "两级缓坡接平坡跌水明渠水面曲线正误判别", "chapter": 8, "kps": ["明渠水面曲线定性分析", "缓坡水面曲线(M1/M2/M3)"], "method": "渐变流微分方程符号判别", "difficulty": 3},
    11: {"title": "等面积半圆形与水力最优矩形明渠流量比计算", "chapter": 7, "kps": ["水力最佳断面", "明渠均匀流曼宁公式"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 2, "subType": "mini-calc"},
    12: {"title": "平底明渠过底坎水面跌落时的水流方向判别", "chapter": 8, "kps": ["恒定总流能量方程", "断面单位能量(比能)"], "method": "正反双向流动伯努利方程讨论法", "difficulty": 3, "subType": "blank"},
    13: {"title": "多孔自由出流 WES 实用堰设计库水位计算", "chapter": 9, "kps": ["堰流分类与基本流量公式"], "method": "堰流与闸孔出流判别及流量公式", "difficulty": 3, "subType": "mini-calc"},
    14: {"title": "底流消能消耗水流过剩动能的物理机理", "chapter": 10, "kps": ["底流消能判别", "水跃衔接形式"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "blank"},
    15: {"title": "闸基正交渗流流网单宽渗流量计算", "chapter": 11, "kps": ["平面渗流流网", "达西定律与单宽渗流量"], "method": "正交流网段数减一计数法", "difficulty": 2, "subType": "mini-calc"},
    16: {"title": "铸铁管阀门瞬时关闭直接水击波速与水击压强计算", "chapter": 6, "kps": ["有压管道水击(水锤)", "儒可夫斯基公式"], "method": "水击相长判别与儒氏公式", "difficulty": 3, "subType": "mini-calc"},
    17: {"title": "紊流串联变径长管改建前后流量比范围计算", "chapter": 6, "kps": ["长管串并联与三水池问题", "紊流阻力分区"], "method": "紊流光滑区布拉休斯幂次比例法", "difficulty": 4, "subType": "mini-calc"},
    18: {"title": "已知绝对压强与当地大气压水柱高求真空高度", "chapter": 2, "kps": ["真空高度(真空度)", "静水压强基本方程"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "mini-calc"},
    19: {"title": "双侧挡水顶铰平板闸门斜拉开启钢绳拉力计算", "chapter": 2, "kps": ["平面静水总压力"], "method": "平面总压力形心法/分块合成法", "difficulty": 3, "subType": "mini-calc"},
    20: {"title": "倾斜放置文丘里流量计过流流量计算", "chapter": 3, "kps": ["恒定总流能量方程", "总水头线与测压管水头线"], "method": "两段伯努利方程联立法", "difficulty": 2, "subType": "mini-calc"},
    21: {"title": "倒 U 形油水压差计量测沿程水头损失的放大倍数", "chapter": 2, "kps": ["静水压强基本方程", "U形水银压差计测压"], "method": "等压面静水压强递推法", "difficulty": 2, "subType": "mini-calc"},
    22: {"title": "明渠紊流弗劳德重力相似模型流量换算", "chapter": 13, "kps": ["弗劳德相似准则", "流量比尺换算"], "method": "弗劳德比尺幂次换算法", "difficulty": 1, "subType": "mini-calc"},
    23: {"title": "串联突然扩大有压短管系统输水流量计算", "chapter": 6, "kps": ["简单短管自由出流", "达西-韦斯巴赫公式"], "method": "短管自由出流流量公式判别", "difficulty": 3, "subType": "mini-calc"},
    24: {"title": "直线与抛物线层流流速分布的渠底壁面切应力之比", "chapter": 1, "kps": ["牛顿内摩擦定律"], "method": "分层液体切应力连续与速度叠加法", "difficulty": 2, "subType": "mini-calc"},
    25: {"title": "缓—陡—缓三段长直矩形明渠水跃发生渠段判别", "chapter": 8, "kps": ["明渠水面曲线定性分析", "明渠水跃与跃后水深"], "method": "渐变流微分方程符号判别", "difficulty": 3, "subType": "blank"},
    26: {
        "title": "斜面薄油膜木板加载前后匀速下滑测定动力黏度",
        "chapter": 1,
        "kps": ["牛顿内摩擦定律"],
        "method": "分层液体切应力连续与速度叠加法",
        "difficulty": 2,
        "rubric": [
            {"label": "计算木板底面积 A = 0.18 m²，写出线性流速分布下油膜黏性阻力 Fτ = μAU/δ", "pts": 5},
            {"label": "列出加载前后两次沿斜面匀速下滑平衡方程并相减消去木板自重：mg·sin30° = μA(U2 - U1)/δ", "pts": 5},
            {"label": "代入数值准确求得润滑油动力黏度 μ = 0.0545 Pa·s（单位正确）", "pts": 5},
        ],
    },
    27: {
        "title": "油水双层液体盛装水箱半圆柱曲面静水总压力计算",
        "chapter": 2,
        "kps": ["静水压强基本方程", "圆柱曲面静水总压力", "压力体图与虚压力体"],
        "method": "等效自由液面+水平投影与铅垂压力体合成法",
        "difficulty": 4,
        "rubric": [
            {"label": "求出 A、B、C 三点相对压强，按双梯形分布算得单位长度水平分力 Fx = 129.49 kN/m（向左）", "pts": 7},
            {"label": "对上弧 AB（油）与下弧 BC（水+上覆油层荷载）作压力体合成，算得铅垂分力 Fz = 55.47 kN/m（向下）", "pts": 8},
            {"label": "合成单位长度总作用力 F = 140.87 kN/m 并指明方向（指向左下方，与水平夹角 23.19°）", "pts": 5},
        ],
    },
    28: {
        "title": "水平渐缩有压管道支座所受水流水平作用力计算",
        "chapter": 3,
        "kps": ["恒定总流连续性方程", "恒定总流能量方程", "恒定总流动量方程", "弯管/底坎水流作用力"],
        "method": "能量方程求流量+控制体动量方程求反力",
        "difficulty": 3,
        "rubric": [
            {"label": "由连续性方程求得流速 v1 ≈ 1.25 m/s、v2 ≈ 5.00 m/s，列伯努利方程求得进口压强 p1 ≈ 14.65 kPa", "pts": 8},
            {"label": "取渐缩管控制体列水平动量方程 p1A1 - p2A2 - Rx' = ρQ(v2 - v1)，解得管壁反力 Rx' = 11.60 N（向左）", "pts": 8},
            {"label": "由牛顿第三定律给出支座所受水平作用力 Rx = 11.60 N，方向水平向右", "pts": 4},
        ],
    },
    29: {
        "title": "矩形平底明渠平板闸门所受水流水平作用力计算",
        "chapter": 3,
        "kps": ["恒定总流连续性方程", "恒定总流动量方程", "弯管/底坎水流作用力"],
        "method": "能量方程求流量+控制体动量方程求反力",
        "difficulty": 2,
        "rubric": [
            {"label": "由连续性方程求得闸前断面与收缩断面平均流速 v1 = 1.0 m/s、v2 = 8.0 m/s", "pts": 4},
            {"label": "计算上下游断面静水总压力 P1 = 156.96 kN、P2 = 2.45 kN 并列出水平控制体动量方程", "pts": 6},
            {"label": "解得水流对平板闸门的水平作用力 R = 98.51 kN，方向水平向右", "pts": 5},
        ],
    },
    30: {
        "title": "二维双曲拉伸流场流函数与流速势函数存在性论证及求解",
        "chapter": 5,
        "kps": ["平面不可压缩流连续性方程", "无旋流判据", "流函数与速度势函数求解"],
        "method": "不可压与无旋偏导检验+偏积分求原函数法",
        "difficulty": 2,
        "rubric": [
            {"label": "检验 ∂ux/∂x + ∂uy/∂y = 0 成立，偏积分求得流函数 ψ = 2kxy + C1", "pts": 8},
            {"label": "检验无旋条件 ωz = 0 成立，偏积分求得流速势函数 φ = k(x² - y²) + C2（或负梯度定义反号）", "pts": 7},
        ],
    },
    31: {
        "title": "计及安全超高的梯形引水明渠均匀流富余供水流量计算",
        "chapter": 7,
        "kps": ["梯形断面水力要素", "明渠均匀流曼宁公式"],
        "method": "水力要素计算+曼宁公式+水力深度Fr判据",
        "difficulty": 2,
        "rubric": [
            {"label": "扣除安全超高求得最大允许均匀流水深 h0 = 3.2 - 0.5 = 2.7 m", "pts": 4},
            {"label": "计算梯形过水断面面积 A = 102.735 m²、湿周 χ = 43.735 m 及水力半径 R = 2.349 m", "pts": 6},
            {"label": "由曼宁公式算得总过流能力 Q总 ≈ 62.00 m³/s，扣除电站引水得富余流量 Q2 = 2.00 m³/s", "pts": 5},
        ],
    },
}


# ==============================================================================
# Curated Metadata for 2017 (Q1 - Q31)
# ==============================================================================
META_2017 = {
    1:  {"title": "圆管流速分布图中微元液块表面切应力方向判别", "chapter": 1, "kps": ["牛顿内摩擦定律"], "method": "分层液体切应力连续与速度叠加法", "difficulty": 2},
    2:  {"title": "平坡接陡坡棱柱体明渠 H2—S2 水面曲线判别", "chapter": 8, "kps": ["明渠水面曲线定性分析", "临界水深与临界底坡"], "method": "渐变流微分方程符号判别", "difficulty": 2},
    3:  {"title": "非恒定流与空间渐变流概念辨析", "chapter": 3, "kps": ["恒定流与均匀流判别"], "method": "概念偷换词辨析", "difficulty": 1},
    4:  {"title": "有旋无旋流动与层流紊流流态分类辨析", "chapter": 5, "kps": ["无旋流判据", "雷诺数与流态判别"], "method": "物理概念定义辨析", "difficulty": 2},
    5:  {"title": "实用堰堰上水头增大对流量系数的影响", "chapter": 9, "kps": ["堰流分类与基本流量公式"], "method": "堰流与闸孔出流判别及流量公式", "difficulty": 2},
    6:  {"title": "渗流流网同一等势线上测压管水面高程特性", "chapter": 11, "kps": ["平面渗流流网"], "method": "物理概念定义辨析", "difficulty": 1},
    7:  {"title": "受实验室供水能力约束的溢流坝模型长度比尺校核", "chapter": 13, "kps": ["弗劳德相似准则", "流量比尺换算"], "method": "弗劳德比尺幂次换算法", "difficulty": 2},
    8:  {"title": "矩形明渠急流过底坎水面壅高判别", "chapter": 8, "kps": ["断面单位能量(比能)"], "method": "比能沿程导数判别法", "difficulty": 3},
    9:  {"title": "完全淹没平板闸门上下游水位同升时总压力压心位置判别", "chapter": 2, "kps": ["平面静水总压力"], "method": "平面总压力形心法/分块合成法", "difficulty": 3},
    10: {"title": "折线形等径有压短管总水头线、测压管水头线及负压区判别", "chapter": 6, "kps": ["总水头线与测压管水头线", "简单短管自由出流"], "method": "总水头线与测压管水头线判据", "difficulty": 3},
    11: {"title": "尼古拉兹试验双对数曲线紊流阻力分区识别", "chapter": 4, "kps": ["紊流阻力分区"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "blank"},
    12: {"title": "底流消能最佳水跃流态类型选择", "chapter": 10, "kps": ["底流消能判别", "水跃衔接形式"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "blank"},
    13: {"title": "等直径有压管道均匀流测压管水头沿程变化规律", "chapter": 4, "kps": ["总水头线与测压管水头线", "沿程水头损失规律"], "method": "总水头线与测压管水头线判据", "difficulty": 1, "subType": "blank"},
    14: {"title": "有压管壁小孔向内吸气时的相对压强符号判别", "chapter": 2, "kps": ["真空高度(真空度)", "静水压强基本方程"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "blank"},
    15: {"title": "平底等径隧洞出口闸门开启前后两点压强差变化判别", "chapter": 6, "kps": ["恒定总流能量方程", "简单短管自由出流"], "method": "两段伯努利方程联立法", "difficulty": 2, "subType": "blank"},
    16: {"title": "并联等长不同管径长管输水流量比计算", "chapter": 6, "kps": ["长管串并联与三水池问题", "达西-韦斯巴赫公式"], "method": "长管阻抗与多水池节点能量平衡", "difficulty": 2, "subType": "mini-calc"},
    17: {"title": "铅直梯形挡水平面静水总压力计算", "chapter": 2, "kps": ["平面静水总压力"], "method": "平面总压力形心法/分块合成法", "difficulty": 2, "subType": "mini-calc"},
    18: {"title": "双层不混溶静止液体测压管液面高差推算", "chapter": 2, "kps": ["静水压强基本方程"], "method": "等压面静水压强递推法", "difficulty": 2, "subType": "mini-calc"},
    19: {"title": "装设水银压差计的水平文丘里流量计流量公式推导", "chapter": 3, "kps": ["U形水银压差计测压", "恒定总流能量方程"], "method": "两段伯努利方程联立法", "difficulty": 2, "subType": "mini-calc"},
    20: {"title": "明渠糙率大小对正常水深的影响比较", "chapter": 7, "kps": ["明渠均匀流曼宁公式"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 1, "subType": "blank"},
    21: {"title": "陡坡 S2 型降水曲线断面单位能量沿程变化规律", "chapter": 8, "kps": ["断面单位能量(比能)", "明渠水面曲线定性分析"], "method": "比能沿程导数判别法", "difficulty": 2, "subType": "blank"},
    22: {"title": "并联管路各支管水力坡度是否相等判别", "chapter": 6, "kps": ["长管串并联与三水池问题"], "method": "长管阻抗与多水池节点能量平衡", "difficulty": 2, "subType": "blank"},
    23: {"title": "梯形断面棱柱体明渠均匀流流量计算", "chapter": 7, "kps": ["梯形断面水力要素", "明渠均匀流曼宁公式"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 2, "subType": "mini-calc"},
    24: {"title": "阀门突然关闭第一传播阶段水击压力波性质", "chapter": 6, "kps": ["有压管道水击(水锤)"], "method": "水击相长判别与儒氏公式", "difficulty": 1, "subType": "blank"},
    25: {"title": "挡水坝下曲边正方形渗流流网单宽渗流量计算", "chapter": 11, "kps": ["平面渗流流网", "达西定律与单宽渗流量"], "method": "正交流网段数减一计数法", "difficulty": 2, "subType": "mini-calc"},
    26: {
        "title": "平行平板甘油间隙内居中与偏置薄片匀速拖拽力计算",
        "chapter": 1,
        "kps": ["牛顿内摩擦定律"],
        "method": "分层液体切应力连续与速度叠加法",
        "difficulty": 2,
        "rubric": [
            {"label": "由牛顿内摩擦定律建立薄片双面黏性总阻力表达式 F = μAv(1/δ1 + 1/δ2)", "pts": 5},
            {"label": "代入正中间位置 δ1 = δ2 = 0.01 m 解得所需拖拽力 F1 = 124.91 N", "pts": 5},
            {"label": "代入偏置位置 δ1 = 0.0075 m、δ2 = 0.0125 m 解得所需拖拽力 F2 = 133.24 N", "pts": 5},
        ],
    },
    27: {
        "title": "隔墙下端搭接卧置圆筒双侧挡水静水总压力计算",
        "chapter": 2,
        "kps": ["圆柱曲面静水总压力", "压力体图与虚压力体"],
        "method": "等效自由液面+水平投影与铅垂压力体合成法",
        "difficulty": 4,
        "rubric": [
            {"label": "分析左右两侧有效铅垂投影高 1.7 m，算得 Px1 = 107.57 kN、Px2 = 82.55 kN 及净水平力 Px = 25.02 kN（向右）", "pts": 5},
            {"label": "求得 A 点距圆心水平偏距 xA = 0.714 m，由压力体合成求得净向上铅垂分力 Pz = 102.97 kN", "pts": 6},
            {"label": "合成静水总压力 P = 105.96 kN 并指明方向（指向右上方，与水平面夹角 76.34°）", "pts": 4},
        ],
    },
    28: {
        "title": "受最大允许真空度限制的虹吸管极限流量、最大落差与断面压强计算",
        "chapter": 6,
        "kps": ["虹吸管水力计算", "真空高度(真空度)", "恒定总流能量方程"],
        "method": "两段伯努利方程联立法",
        "difficulty": 3,
        "rubric": [
            {"label": "对水库水面 1 至最高点 3 列能量方程，由 [hv] = 7 m 求得 vmax = 2.986 m/s 及最大流量 Qmax = 0.0235 m³/s", "pts": 7},
            {"label": "对水面 1 至出口 4 列能量方程求得允许最大出水口高差 hmax = 65/11 ≈ 5.91 m", "pts": 6},
            {"label": "对水面 1 至断面 2 列能量方程求得最大流量下 2 点相对压强 p2 = -44.59 kPa（真空度 44.59 kPa）", "pts": 7},
        ],
    },
    29: {
        "title": "倾斜上行有压渐缩管段固定镇墩所受水流作用力计算",
        "chapter": 3,
        "kps": ["恒定总流连续性方程", "恒定总流能量方程", "恒定总流动量方程", "弯管/底坎水流作用力"],
        "method": "能量方程求流量+控制体动量方程求反力",
        "difficulty": 4,
        "rubric": [
            {"label": "由连续性方程得 Q = 0.0314 m³/s、v2 = 4 m/s，列能量方程求得出口压强水头 42.60 m 及端面压力 P1、P2", "pts": 7},
            {"label": "取渐缩管控制体列水平与铅垂动量方程（计入水重 G = 2 kN），求得水流对镇墩分力 Rx = 10.42 kN、Rz = 4.01 kN", "pts": 9},
            {"label": "合成镇墩所受总作用力 R = 11.16 kN 并指明方向（指向右上方，与水平方向夹角 21.07°）", "pts": 4},
        ],
    },
    30: {
        "title": "二维不可压缩势流存在性、无旋性判别及等势线与流线正交证明",
        "chapter": 5,
        "kps": ["平面不可压缩流连续性方程", "无旋流判据", "流函数与速度势函数求解"],
        "method": "不可压与无旋偏导检验+偏积分求原函数法",
        "difficulty": 2,
        "rubric": [
            {"label": "验证平面连续性方程 ∂ux/∂x + ∂uy/∂y = 0 成立，判定该不可压缩流动存在", "pts": 4},
            {"label": "计算旋转角速度 ωz = (∂uy/∂x - ∂ux/∂y)/2 = 0，判定流动为无旋流动", "pts": 4},
            {"label": "求出 φ = xy + C1 与 ψ = (y² - x²)/2 + C2，由斜率乘积为 -1 或梯度点积 ∇φ·∇ψ = 0 证明正交", "pts": 7},
        ],
    },
    31: {
        "title": "陡坡长渠接平坡明渠水跃判别及变坡断面共轭水深计算",
        "chapter": 8,
        "kps": ["临界水深与临界底坡", "明渠水面曲线定性分析", "明渠水跃与跃后水深"],
        "method": "共轭水深与尾水深对比判据",
        "difficulty": 3,
        "rubric": [
            {"label": "求得单宽流量 q = 4.0 m²/s 及临界水深 hc = 1.177 m > h0 = 0.51 m，判出上游为陡坡均匀急流", "pts": 4},
            {"label": "分析急流进入下游水平长渠段经 H3 壅水必向缓流过渡，判定渠中发生水跃", "pts": 4},
            {"label": "确定 A—A 断面跃前水深 h1 = 0.51 m、Fr1 = 3.506，由水跃方程求得跃后水深 h2 = 2.29 m", "pts": 7},
        ],
    },
}


# ==============================================================================
# Curated Metadata for 2016 (Q1 - Q31)
# ==============================================================================
META_2016 = {
    1:  {"title": "牛顿液体本构关系与宾汉流体线性关系辨析", "chapter": 1, "kps": ["牛顿内摩擦定律"], "method": "概念偷换词辨析", "difficulty": 2},
    2:  {"title": "欧拉液体平衡微分方程对理想与实际液体的适用性", "chapter": 2, "kps": ["静水压强基本方程"], "method": "物理概念定义辨析", "difficulty": 1},
    3:  {"title": "断面流速分布不均匀性与非均匀流定义辨析", "chapter": 3, "kps": ["恒定流与均匀流判别", "断面流速分布"], "method": "概念偷换词辨析", "difficulty": 1},
    4:  {"title": "圆管均匀层流最大点流速与断面平均流速比值判别", "chapter": 4, "kps": ["圆管层流哈根-泊肃叶定律", "断面流速分布"], "method": "物理概念定义辨析", "difficulty": 1},
    5:  {"title": "紊流阻力平方区沿程阻力系数与流速关系辨析", "chapter": 4, "kps": ["紊流阻力分区", "达西-韦斯巴赫公式"], "method": "概念偷换词辨析", "difficulty": 2},
    6:  {"title": "平坡明渠断面单位能量沿程单调减小特性判别", "chapter": 8, "kps": ["断面单位能量(比能)", "明渠渐变流基本微分方程"], "method": "比能沿程导数判别法", "difficulty": 2},
    7:  {"title": "并联长管各支管管壁切应力是否相等判别", "chapter": 6, "kps": ["长管串并联与三水池问题", "圆管均匀流切应力分布"], "method": "圆管切应力线性分布性质", "difficulty": 2},
    8:  {"title": "水流由陡坡进入缓坡是否必然发生水跃辨析", "chapter": 8, "kps": ["明渠水面曲线定性分析", "明渠水跃与跃后水深"], "method": "渐变流微分方程符号判别", "difficulty": 3},
    9:  {"title": "水平放置受压面静水总压力作用点与形心重合条件", "chapter": 2, "kps": ["平面静水总压力"], "method": "平面总压力形心法/分块合成法", "difficulty": 2},
    10: {"title": "实验室毕托管测定紊流时均流速原理判别", "chapter": 3, "kps": ["恒定总流能量方程"], "method": "物理概念定义辨析", "difficulty": 1},
    11: {"title": "正六边形铅直挡水平面对角分割静水总压力之比计算", "chapter": 2, "kps": ["平面静水总压力"], "method": "平面总压力形心法/分块合成法", "difficulty": 3, "subType": "mini-calc"},
    12: {"title": "密闭加压油箱底部圆锥体铅垂静水压力与平衡外力计算", "chapter": 2, "kps": ["静水压强基本方程", "压力体图与虚压力体"], "method": "等效自由液面+水平投影与铅垂压力体合成法", "difficulty": 3, "subType": "mini-calc"},
    13: {"title": "阻力平方区串联扩径长管改建前后输水流量比计算", "chapter": 6, "kps": ["长管串并联与三水池问题", "紊流阻力分区"], "method": "长管阻抗与多水池节点能量平衡", "difficulty": 3, "subType": "mini-calc"},
    14: {"title": "等面积同水力坡度圆形与方形有压管壁面切应力之比", "chapter": 4, "kps": ["圆管均匀流切应力分布"], "method": "圆管切应力线性分布性质", "difficulty": 2, "subType": "mini-calc"},
    15: {"title": "油膜窄间隙内旋转圆盘双面黏滞阻力矩积分推导", "chapter": 1, "kps": ["牛顿内摩擦定律", "环形/圆盘间隙黏性阻力矩"], "method": "分层液体切应力连续与速度叠加法", "difficulty": 3, "subType": "mini-calc"},
    16: {"title": "封闭负压水箱插入通大气玻璃管恰好充满空气的深度计算", "chapter": 2, "kps": ["静水压强基本方程", "真空高度(真空度)"], "method": "等压面静水压强递推法", "difficulty": 2, "subType": "mini-calc"},
    17: {"title": "堰流弗劳德重力相似模型原型流量换算", "chapter": 13, "kps": ["弗劳德相似准则", "流量比尺换算"], "method": "弗劳德比尺幂次换算法", "difficulty": 1, "subType": "mini-calc"},
    18: {"title": "有压管道阀门突然关闭的直接水击判别", "chapter": 6, "kps": ["有压管道水击(水锤)", "直接与间接水击判别"], "method": "水击相长判别与儒氏公式", "difficulty": 1, "subType": "mini-calc"},
    19: {"title": "三元流动速度势函数存在的充要条件", "chapter": 5, "kps": ["无旋流判据", "流函数与速度势函数求解"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "blank"},
    20: {"title": "按相对堰顶厚度判别溢流堰类型", "chapter": 9, "kps": ["堰流分类与基本流量公式"], "method": "堰流与闸孔出流判别及流量公式", "difficulty": 1, "subType": "mini-calc"},
    21: {"title": "达西渗流沿程水头损失与渗流流速的幂次关系", "chapter": 11, "kps": ["达西定律与适用范围"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "blank"},
    22: {"title": "挡水坝下曲边正方形渗流流网单宽渗流量计算", "chapter": 11, "kps": ["平面渗流流网", "达西定律与单宽渗流量"], "method": "正交流网段数减一计数法", "difficulty": 2, "subType": "mini-calc"},
    23: {"title": "底流消能水力计算的核心工程任务", "chapter": 10, "kps": ["底流消能判别", "水跃衔接形式"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "short-answer"},
    24: {"title": "由矩形明渠均匀流水面降落与流量反求渠道糙率", "chapter": 7, "kps": ["明渠均匀流曼宁公式"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 2, "subType": "mini-calc"},
    25: {"title": "同一圆管紊流光滑区与粗糙区对应过流流量大小比较", "chapter": 4, "kps": ["紊流阻力分区", "雷诺数与流态判别"], "method": "物理概念定义辨析", "difficulty": 2, "subType": "blank"},
    26: {
        "title": "窄间隙双液层内拖动隔板切应力相等与最小阻力位置求解",
        "chapter": 1,
        "kps": ["牛顿内摩擦定律", "双层液体平板剪切流"],
        "method": "分层液体切应力连续与速度叠加法",
        "difficulty": 2,
        "rubric": [
            {"label": "写出上下液层切应力 τ1 = μ1u/(h-y)、τ2 = μ2u/y，由 τ1 = τ2 解得 y = μ2h/(μ1 + μ2)", "pts": 5},
            {"label": "建立总阻力 F(y) = Au[μ1/(h-y) + μ2/y] 并求导取极值，解得最小阻力位置 y = √μ2·h/(√μ1 + √μ2)", "pts": 5},
        ],
    },
    27: {
        "title": "密闭容器底孔金属圆球静水总压力与临界浮起真空度计算",
        "chapter": 2,
        "kps": ["静水压强基本方程", "压力体图与虚压力体", "真空高度(真空度)"],
        "method": "等效自由液面+水平投影与铅垂压力体合成法",
        "difficulty": 4,
        "rubric": [
            {"label": "分析轴对称水平合力为零，建立圆孔以上内水箱向下实压力体与圆孔以下外水箱向上虚压力体关系", "pts": 6},
            {"label": "合并完整球体积 πD³/6，算得大气压下球体所受净水压力 F水 = 0.2055 N（方向竖直向上）", "pts": 6},
            {"label": "列临界浮起平衡方程 F水 + pv(πd²/4) = G，解得所需真空度 pv = 3858.4 Pa（真空高度 0.393 m）", "pts": 8},
        ],
    },
    28: {
        "title": "45° 倾斜渐变输水管结合水银压差计判别水流方向",
        "chapter": 3,
        "kps": ["恒定总流连续性方程", "恒定总流能量方程", "U形水银压差计测压"],
        "method": "两段伯努利方程联立法",
        "difficulty": 3,
        "rubric": [
            {"label": "由连续性方程求得上端细管断面平均流速 v2 = v1(d1/d2)² = 8 m/s", "pts": 5},
            {"label": "由水银压差计静力平衡关系求得两断面测压管水头差 ΔHp = (ρm/ρ - 1)hp = 2.52 m", "pts": 8},
            {"label": "计算两断面流速水头差 (v2² - v1²)/(2g) = 3.058 m 并比较总水头，判定水流由上端细管流向下端粗管", "pts": 7},
        ],
    },
    29: {
        "title": "平面不可压缩流场流函数与流速势函数存在性论证及求解",
        "chapter": 5,
        "kps": ["平面不可压缩流连续性方程", "无旋流判据", "流函数与速度势函数求解"],
        "method": "不可压与无旋偏导检验+偏积分求原函数法",
        "difficulty": 2,
        "rubric": [
            {"label": "检验连续性方程 ∂ux/∂x + ∂uy/∂y = 2y - 2y = 0 成立，偏积分求得 ψ = -3x - x³/3 + xy² + C1", "pts": 8},
            {"label": "检验无旋条件 2ωz = ∂uy/∂x - ∂ux/∂y = 2x - 2x = 0 成立，偏积分求得 φ = x²y + 3y - y³/3 + C2", "pts": 7},
        ],
    },
    30: {
        "title": "矩形棱柱形明渠底坡类型、流态及 M2 型水面曲线判别",
        "chapter": 8,
        "kps": ["临界水深与临界底坡", "弗劳德数判急缓流", "缓坡水面曲线(M1/M2/M3)"],
        "method": "渐变流微分方程符号判别",
        "difficulty": 2,
        "rubric": [
            {"label": "计算临界水深 hc = (q²/g)^(1/3) ≈ 1.00 m < h0 = 1.5 m，判定渠道底坡属于缓坡", "pts": 7},
            {"label": "比较 hc = 1.00 m < h = 1.25 m < h0 = 1.5 m（Fr = 0.715 < 1），判定该处为缓流且发生 M2 型降水曲线", "pts": 8},
        ],
    },
    31: {
        "title": "矩形河道平板闸门下水跃衔接形式判别与闸门水平作用力计算",
        "chapter": 3,
        "kps": ["恒定总流能量方程", "恒定总流动量方程", "水跃衔接形式", "矩形明渠共轭水深"],
        "method": "能量方程求流量+控制体动量方程求反力",
        "difficulty": 4,
        "rubric": [
            {"label": "求得收缩断面 vc0 = 10.0 m/s、Frc0 = 5.048 及共轭水深 h0c'' = 2.663 m > 2.5 m，判定发生远离式水跃", "pts": 8},
            {"label": "列闸前至收缩断面能量方程（计入局部损失 0.05vc0²/2g），解得闸前水深 H1 = 5.727 m 及 v1 = 0.6985 m/s", "pts": 6},
            {"label": "取单宽控制体列水平动量方程求得水流对单位宽度闸门的作用力 R = 122.88 kN/m（水平向右）", "pts": 6},
        ],
    },
}

YEAR_CONFIGS = {
    2018: {
        "meta": META_2018,
        "calc_scores": {26: 15, 27: 20, 28: 20, 29: 15, 30: 15, 31: 15},
        "calc_desc": "共 6 小题（15+20+20+15+15+15 分），共 100 分。",
        "exam_notes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "除特别说明外，统一取重力加速度 $g = 9.81\\,\\mathrm{m/s^2}$，水密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$。",
            "题型与分值：一、是非题（10×2=20 分）；二、填空题（15×2=30 分）；三、计算题（共 6 题，分别为 15、20、20、15、15、15 分，共 100 分）。",
        ],
    },
    2017: {
        "meta": META_2017,
        "calc_scores": {26: 15, 27: 15, 28: 20, 29: 20, 30: 15, 31: 15},
        "calc_desc": "共 6 小题（15+15+20+20+15+15 分），共 100 分。",
        "exam_notes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "除特别说明外，统一取重力加速度 $g = 9.81\\,\\mathrm{m/s^2}$，水密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$。",
            "题型与分值：一、是非题（10×2=20 分）；二、填空题（15×2=30 分）；三、计算题（共 6 题，分别为 15、15、20、20、15、15 分，共 100 分）。",
        ],
    },
    2016: {
        "meta": META_2016,
        "calc_scores": {26: 10, 27: 20, 28: 20, 29: 15, 30: 15, 31: 20},
        "calc_desc": "共 6 小题（10+20+20+15+15+20 分），共 100 分。",
        "exam_notes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "除特别说明外，统一取重力加速度 $g = 9.81\\,\\mathrm{m/s^2}$，水密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$。",
            "题型与分值：一、是非题（10×2=20 分）；二、填空题（15×2=30 分）；三、计算题（共 6 题，分别为 10、20、20、15、15、20 分，共 100 分）。",
        ],
    },
}


def sanitize_16_18_text(s: str) -> str:
    """Strip all third-party/video/creator/course/reference-sheet traces and fix LaTeX glitches."""
    if not s:
        return s

    # Fix OMML plain-run & KaTeX glitches first
    s = s.replace(r"\mathrm{cdots}", r"\cdots")
    s = s.replace(r"\mathrm{lg}", r"\lg ")
    s = s.replace("∞", r"\infty ")
    s = s.replace(r"^{^{\circ}}", r"^{\circ}")
    s = s.replace(r"^{\mathrm{^{\circ}}}", r"^{\circ}")
    s = re.sub(r"\^\{\s*'''\s*\}", r"^{\\prime\\prime\\prime}", s)
    s = re.sub(r"\^\{\s*''\s*\}", r"^{\\prime\\prime}", s)
    s = re.sub(r"\^\{\s*'\s*\}", r"^{\\prime}", s)

    replacements = [
        # 2018 specific sanitizations
        ("（课程讲解音频亦已确认此理）", ""),
        ("（常见随卷错误参考答案此处有误）", "（切忌误套用于非均匀流）"),
        ("（与课程另一种常见口径结论一致）", ""),
        ("（与课程视频讲解结论一致）", ""),
        ("部分随卷答案因取", "若近似取"),
        ("随卷流传参考答案在计算 $F_{z}$ 时误将上层 $AB$ 段的油也当作水，错写出", "切勿误将上层 $AB$ 段的油也当作水而错写为"),
        ("；经严密压力体分解与曲面积分双重验证，以及课程真题讲解视频明确给出 $P_{z}={\\rho}_{\\text{油}}g\\frac{\\pi R^{2}}{4}b+{\\rho}_{\\text{水}}g\\frac{\\pi R^{2}}{4}b$，严格精确解应为", "；经压力体分解与曲面积分双重验证，单位长度铅垂分力严格为 $F_{z}=({\\rho}_{\\text{油}}+{\\rho}_{\\text{水}})g\\frac{\\pi R^{2}}{4}=$"),
        ("（可对照课程讲解视频确认读数为 $0.3\\, \\mathrm{m}$）", ""),
        # Fix 2018 Q20 inverted U-tube air pocket physical explanation
        ("因压差计上部连通管内为水（水压差计直接测得两断面测压管水头差", "因倒 U 形压差计顶部充有空气（气柱重度远小于水可忽略，两支管液面气压相等，故液面高差直接等于两断面测压管水头差"),

        # 2017 specific sanitizations
        ("（经本地真题讲解视频实录核对，主讲教师最后亦明确给出“$e=e'$，作用点位置没有变化，第 9 题正确”）", ""),
        ("结合原卷图及课程真题讲解（对照经典教材流线图），图中至少存在两处明显错误：", "对照有压短管水头线绘制基本规律，图中至少存在两处明显错误："),
        ("（与课程真题讲解视频板书完全一致）", ""),
        ("；部分流传参考答案计算正值时漏写负号", "；注意相对压强须带负号"),
        ("核对本地课程真题讲解视频与教材原型题可知，本题原 PDF 扫描件重印时存在 3 处明显排版笔误：", "对照水力学经典题型与量纲关系可知，本题原扫描件存在 3 处明显印刷笔误："),

        # 2016 specific sanitizations
        ("（即按原题及视频定义 $2\\rightarrow 1$）", "（按标准断面编号即 $2\\rightarrow 1$）"),
        ("核对真题讲解视频中的原卷印刷图与本题扫描件（重绘图）存在两处图形印刷差异，以下分别说明，且两种情形均得出一致的物理流向", "原卷标准图与部分重印扫描图在断面标号及水银液面方向上存在重绘差异，以下分别核算，两种情形均得出完全一致的物理流向"),
        ("1. 按真题讲解视频（及随卷答案）原图：", "1. 按标准原卷图："),

        # Catch-all fallbacks for any remaining banned tokens
        ("真题讲解视频", "标准题解"),
        ("视频讲解", "标准解析"),
        ("原视频", "原题"),
        ("随卷参考答案", "部分旧解"),
        ("随卷答案", "部分旧解"),
        ("随卷", ""),
        ("去水印", ""),
        ("视频", ""),
    ]
    for old, new in replacements:
        s = s.replace(old, new)

    return s.strip()


def normalize_stem(year: int, qno: int, stem: str, qtype: str) -> tuple[str, str]:
    notes: list[str] = []

    if qtype == "judge":
        stem = re.sub(r"[（(]\s*[）)]\s*$", "", stem).strip()
    elif qtype in ("calc", "short", "proof"):
        stem = re.sub(r"[（(]\d+\s*分[）)]\s*$", "", stem).strip()

    # Year-specific stem normalizations & typo cleanups
    if year == 2018:
        if qno == 18:
            # Original 2018 Fill 8 printed "7m" directly instead of blank
            stem = re.sub(r"7\s*m。?$", "________。", stem)
            notes.append("原卷印刷时题干末尾已自带答案“7m”，此处恢复为填空槽供练习")
        elif qno == 23:
            # Clean duplicate '进口' after '=0.5'
            stem = stem.replace("=0.5$ 进口（", "=0.5$（")
            notes.append("原卷题干“两端”系“两段”笔误，且 L2 = 250 cm 疑似 250 m 排版笔误")
        elif qno == 31:
            notes.append("原卷“提高 h = 3.2 m”系“堤高 h = 3.2 m”印刷同音笔误")
    elif year == 2017:
        if qno == 14:
            stem = stem.replace("（填与大于、等于或小于）", "（填写大于、等于或小于）")
        elif qno == 23:
            stem = stem.replace("梯形断而", "梯形断面")
        elif qno == 25:
            # Convert inline OMML `$q=(\, ){\, \mathrm{m}}^{2}/\mathrm{s}$` to blank outside `$...$`
            stem = re.sub(
                r"\$q=\([^$]*\)[^$]*\$",
                r"$q =$ ________ $\\mathrm{m^2/s}$",
                stem,
            )
        elif qno == 28:
            notes.append("原卷附图左侧标注“2 = 2 m”系“z3 = 2 m”印刷笔误")
        elif qno == 29:
            notes.append(
                "原卷扫描件存在 3 处印刷笔误：进口压强水头应为 p1/(ρg) = 50 m，出口断面面积关系应为 A2 = A1/4，"
                "渐变段水头损失应为 hw = 2v2²/(2g)"
            )
    elif year == 2016:
        if qno == 28:
            notes.append("部分重印扫描图将断面 1—1 与 2—2 标号互换，但两种标法下物理流向均确定为由上端细管流向下端粗管")

    if qtype == "fill":
        # Normalize 3+ underscores outside math `$...$` to standard 8 underscores `________`
        parts = re.split(r"(\$[^$]+\$)", stem)
        for i in range(0, len(parts), 2):
            parts[i] = re.sub(r"_{3,}", "________", parts[i])
        stem = "".join(parts)

    return stem.strip(), "；".join(notes)


def detect_section(raw_txt: str) -> tuple[str, int] | None:
    """Detect section headers across judge / choice / fill / short / calc / proof."""
    if re.match(r"^[一二三四五六][、.．]\s*(?:是非题|判断题)", raw_txt):
        return ("judge", 0)
    if re.match(r"^[一二三四五六][、.．]\s*(?:单项选择题|单选题|选择题)", raw_txt):
        return ("single_choice", 0)
    if re.match(r"^[一二三四五六][、.．]\s*(?:多项选择题|多选题)", raw_txt):
        return ("multi_choice", 0)
    if re.match(r"^[一二三四五六][、.．]\s*填空题", raw_txt):
        return ("fill", 10)
    if re.match(r"^[一二三四五六][、.．]\s*简答题", raw_txt):
        return ("short", 25)
    if re.match(r"^[一二三四五六][、.．]\s*(?:计算题|解答题)", raw_txt):
        return ("calc", 25)
    if re.match(r"^[一二三四五六][、.．]\s*(?:证明题|推导题)", raw_txt):
        return ("proof", 25)
    return None


def parse_single_year(year: int) -> None:
    cfg = YEAR_CONFIGS[year]
    meta_map = cfg["meta"]
    calc_scores = cfg["calc_scores"]

    docx_path = SRC_DOCX_DIR / f"{year}年河海大学814《水力学》考研真题及详细解析.docx"
    std_dir = STD_OUT_ROOT / str(year)
    std_fig_dir = std_dir / "figures"
    std_fig_dir.mkdir(parents=True, exist_ok=True)

    web_fig_dir = WEB_OUT_ROOT / "figures" / str(year)
    web_fig_dir.mkdir(parents=True, exist_ok=True)
    WEB_OUT_ROOT.mkdir(parents=True, exist_ok=True)

    total_q_count = len(meta_map)
    questions: dict[int, dict] = {}
    analysis_buf: dict[int, list[str]] = {k: [] for k in range(1, total_q_count + 1)}
    pitfalls_buf: dict[int, list[str]] = {k: [] for k in range(1, total_q_count + 1)}

    with zipfile.ZipFile(docx_path) as zf:
        rels = {
            r.attrib["Id"]: r.attrib["Target"]
            for r in ET.fromstring(zf.read("word/_rels/document.xml.rels"))
        }
        body = ET.fromstring(zf.read("word/document.xml")).find("w:body", base_parser.NS)

        part1 = False
        part2 = False
        sec_type = "judge"
        sec_offset = 0
        cur_q: int | None = None

        children = list(body)
        idx = 0
        while idx < len(children):
            el = children[idx]
            ctag = el.tag.split("}")[-1]
            raw_txt = "".join(el.itertext()).strip()

            if ctag == "p" and raw_txt.startswith("第一部分："):
                part1 = True
                part2 = False
                cur_q = None
                idx += 1
                continue

            if ctag == "p" and raw_txt.startswith("第二部分："):
                part2 = True
                cur_q = None
                idx += 1
                continue

            if ctag == "p":
                sec_info = detect_section(raw_txt)
                if sec_info is not None:
                    sec_type, sec_offset = sec_info
                    cur_q = None
                    idx += 1
                    continue

            # --- Part 1: Exam Stems ---
            if part1 and not part2 and ctag == "p":
                md, imgs = base_parser.paragraph_to_markdown(el, rels)
                md = sanitize_16_18_text(md)

                m_q = re.match(r"^(\d{1,2})\.\s*(.+)$", md, flags=re.DOTALL)
                if m_q:
                    local_no = int(m_q.group(1))
                    qno = sec_offset + local_no
                    qtype = sec_type
                    raw_stem = m_q.group(2).strip()

                    if qtype in ("judge", "fill"):
                        score = 2
                    else:
                        m_sc = re.search(r"[（(](\d+)\s*分[）)]\s*$", raw_stem)
                        score = int(m_sc.group(1)) if m_sc else calc_scores[qno]

                    stem_clean, note_txt = normalize_stem(year, qno, raw_stem, qtype)
                    questions[qno] = {
                        "id": f"{year}-{qno:02d}",
                        "year": year,
                        "no": qno,
                        "type": qtype,
                        "score": score,
                        "title": meta_map[qno]["title"],
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
                    if idx + 1 < len(children):
                        nxt_txt = "".join(children[idx + 1].itertext()).strip()
                        if nxt_txt.startswith("原卷附图"):
                            idx += 1
                    for i_im, media_rel in enumerate(imgs):
                        suf = "" if i_im == 0 else f"_{i_im + 1}"
                        png_name = f"q{cur_q:02d}_orig{suf}.png"
                        webp_name = f"q{cur_q:02d}_orig{suf}.webp"
                        raw_bytes = zf.read("word/" + media_rel)
                        (std_fig_dir / png_name).write_bytes(raw_bytes)

                        im = Image.open(io.BytesIO(raw_bytes))
                        if im.mode not in ("RGB", "RGBA"):
                            im = im.convert("RGBA")
                        im.save(web_fig_dir / webp_name, format="WEBP", quality=90, method=5)

                        questions[cur_q]["figures"].append({
                            "src": f"figures/{png_name}",
                            "caption": f"题 {cur_q} 图",
                        })
                    idx += 1
                    continue

                if md and cur_q is not None and not md.startswith("原卷附图"):
                    # Multi-paragraph stem continuation (e.g. sub-questions (1), (2) with trailing score)
                    m_sc_tail = re.search(r"[（(](\d+)\s*分[）)]\s*$", md)
                    if m_sc_tail and questions[cur_q]["type"] not in ("judge", "fill"):
                        questions[cur_q]["score"] = int(m_sc_tail.group(1))
                    extra_clean, extra_note = normalize_stem(year, cur_q, md, questions[cur_q]["type"])
                    questions[cur_q]["stem"] += "\n\n" + extra_clean
                    if extra_note:
                        questions[cur_q]["note"] = (
                            questions[cur_q]["note"] + "；" + extra_note
                            if questions[cur_q]["note"]
                            else extra_note
                        )
                idx += 1
                continue

            # --- Part 2: Solutions & Detailed Analysis ---
            if part2 and ctag == "p":
                md, imgs = base_parser.paragraph_to_markdown(el, rels)
                md = sanitize_16_18_text(md)

                m_sol = re.match(r"^第\s*(\d{1,2})\s*题\s*【参考答案】\s*(.+)$", md)
                if m_sol:
                    local_no = int(m_sol.group(1))
                    cur_q = sec_offset + local_no
                    ans_txt = m_sol.group(2).strip()

                    # Clean special editorial note on 2018 Q18 answer
                    if year == 2018 and cur_q == 18:
                        ans_txt = "$7\\,\\mathrm{m}$"
                    elif year == 2018 and cur_q == 13:
                        ans_txt = "$160.15$（计入行近流速水头；若忽略行近流速水头则为 $160.29$）"

                    questions[cur_q]["answer"] = ans_txt
                    questions[cur_q]["shortAnswer"] = ans_txt
                    if questions[cur_q]["type"] == "judge":
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
                        nxt_txt = "".join(children[idx + 1].itertext()).strip()
                        if nxt_txt.startswith("解析分析附图"):
                            idx += 1
                    for i_im, media_rel in enumerate(imgs):
                        suf = "" if i_im == 0 else f"_{i_im + 1}"
                        png_name = f"q{cur_q:02d}_sol{suf}.png"
                        webp_name = f"q{cur_q:02d}_sol{suf}.webp"
                        raw_bytes = zf.read("word/" + media_rel)
                        (std_fig_dir / png_name).write_bytes(raw_bytes)

                        im = Image.open(io.BytesIO(raw_bytes))
                        if im.mode not in ("RGB", "RGBA"):
                            im = im.convert("RGBA")
                        im.save(web_fig_dir / webp_name, format="WEBP", quality=90, method=5)

                        questions[cur_q]["analysisFigures"].append({
                            "src": f"figures/{png_name}",
                            "caption": f"第 {cur_q} 题解析示意图",
                        })
                    idx += 1
                    continue

                if md.startswith("解析分析附图"):
                    idx += 1
                    continue

                if md.startswith("【详细解析】"):
                    md = md.replace("【详细解析】", "", 1).strip()

                if not md:
                    idx += 1
                    continue

                if md.startswith(("【注意纠错】", "【重要纠错】", "【勘误说明】")):
                    cleaned_pit = re.sub(r"^【[^】]+】\s*", "", md).strip()
                    pitfalls_buf[cur_q].append(cleaned_pit)
                elif md not in ("【原卷印刷勘误说明】", "【原卷图注与双重核对】"):
                    analysis_buf[cur_q].append(md)

            idx += 1

    # Add curated pitfalls for key calculation traps
    if year == 2018:
        pitfalls_buf[13].append(
            "注意区分堰顶以上总水头 $H_0$ 与静水头 $H$：由流量公式直接算出的是 $H_0 = 10.29\\,\\mathrm{m}$，"
            "若计入行近流速水头 $v_0^2/(2g) \\approx 0.14\\,\\mathrm{m}$，库水位为 $160.15\\,\\mathrm{m}$（若按大水库忽略行近流速则为 $160.29\\,\\mathrm{m}$）。"
        )
        pitfalls_buf[19].append(
            "注意钢绳在底端 $B$ 以 $45^{\\circ}$ 斜向左上拉动，对顶铰 $A$ 的垂直力臂为 $L\\cos 45^{\\circ}$（而非 $L$），"
            "且下游三角形水压力对顶铰 $A$ 的力臂为 $L - h_2/3 = 7/3\\,\\mathrm{m}$（切勿误用距底边距离 $2/3\\,\\mathrm{m}$）。"
        )
    elif year == 2017:
        pitfalls_buf[27].append(
            "右侧水体液面（$2.5\\,\\mathrm{m}$）已漫过圆筒最高点（$2.0\\,\\mathrm{m}$）直至左侧隔墙交点 $A$，故圆筒顶部左半侧高于 $A$ 点的弧段同样受右侧水体覆盖，"
            "切勿漏算隔墙左侧圆弧段由上下游水位差 $\\Delta h = 0.5\\,\\mathrm{m}$ 产生的向上净浮托力！"
        )
        pitfalls_buf[28].append(
            "第（2）问求断面 2 的相对压强时，因测压管水头低于该点位置高程，结果必为负值 $p_2 = -44.59\\,\\mathrm{kPa}$（对应真空度 $44.59\\,\\mathrm{kPa}$），切忌漏写负号。"
        )
        pitfalls_buf[29].append(
            "对倾斜管道控制体列铅垂方向动量方程时，切勿遗漏管段内水体自身重力 $G = 2\\,\\mathrm{kN}$（方向竖直向下），并注意区分镇墩对水反力与水流对镇墩作用力的正负方向。"
        )
    elif year == 2016:
        pitfalls_buf[27].append(
            "切勿将圆球所受静水合力误算为阿基米德整球浮力 $\\rho g V_{\\text{球}}$！因圆球底部封堵圆孔，上下表面分别接触不同水位的内外水体，"
            "圆孔投影面积 $\\pi d^2/4$ 上承受内外水位差 $H_1 - H_2 = 0.10\\,\\mathrm{m}$ 的向下压差项必须扣除。"
        )
        pitfalls_buf[28].append(
            "切忌仅凭测压管水头高低（或压强大小）判断有压变速管流方向！实际粘性流体总是从**总水头**高处流向总水头低处，细管断面流速高达 $8\\,\\mathrm{m/s}$，"
            "其动能水头 $v_2^2/(2g) = 3.26\\,\\mathrm{m}$ 远大于粗管，从而使细管总水头高于粗管。"
        )

    final_questions: list[dict] = []
    for qno in range(1, total_q_count + 1):
        q = questions[qno]
        q["analysis"] = "\n\n".join(analysis_buf[qno]).strip()
        q["pitfalls"] = "\n\n".join(pitfalls_buf[qno]).strip()

        meta = meta_map[qno]
        assert meta["chapter"] in VALID_CHAPTERS, f"Invalid chapter {meta['chapter']} in {year} Q{qno}"
        q["chapter"] = meta["chapter"]
        q["kps"] = meta["kps"]
        q["method"] = meta["method"]
        q["difficulty"] = meta["difficulty"]
        if "subType" in meta:
            q["subType"] = meta["subType"]
        if "rubric" in meta:
            r_sum = sum(item["pts"] for item in meta["rubric"])
            assert r_sum == q["score"], f"Rubric sum {r_sum} != score {q['score']} in {year} Q{qno}"
            q["rubric"] = meta["rubric"]
        final_questions.append(q)

    total_score = sum(q["score"] for q in final_questions)
    assert total_score == 150, f"Total score {total_score} != 150 in {year}"

    std_paper = {
        "year": year,
        "code": "814",
        "subject": "水力学",
        "school": "河海大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": False,
        "examNotes": cfg["exam_notes"],
        "sections": [
            {
                "id": "judge",
                "title": "一、是非题",
                "description": "共 10 小题，每小题 2 分，共 20 分。",
                "range": [1, 10],
                "scorePerQuestion": 2,
                "totalScore": 20,
            },
            {
                "id": "fill",
                "title": "二、填空题",
                "description": "共 15 小题，每小题 2 分，共 30 分。",
                "range": [11, 25],
                "scorePerQuestion": 2,
                "totalScore": 30,
            },
            {
                "id": "calc",
                "title": "三、计算题",
                "description": cfg["calc_desc"],
                "range": [26, total_q_count],
                "totalScore": 100,
            },
        ],
        "questions": final_questions,
    }

    # 1. Write standardized exam pack JSON
    std_json_path = std_dir / f"{year}.json"
    std_json_path.write_text(json.dumps(std_paper, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2. Build web-ready JSON with WebP figure paths `figures/<year>/<name>.webp`
    web_paper = copy.deepcopy(std_paper)
    fig_count = 0
    for q in web_paper["questions"]:
        for flist_key in ("figures", "analysisFigures"):
            new_figs = []
            for fig in q.get(flist_key, []):
                stem_name = Path(fig["src"]).stem
                new_figs.append({
                    "src": f"figures/{year}/{stem_name}.webp",
                    "caption": fig["caption"],
                })
                fig_count += 1
            q[flist_key] = new_figs

    web_json_path = WEB_OUT_ROOT / f"{year}.json"
    web_json_path.write_text(json.dumps(web_paper, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"[{year}] Wrote {len(final_questions)} questions ({total_score} pts, {fig_count} figures) -> "
        f"{std_json_path.relative_to(ROOT)} & {web_json_path.relative_to(ROOT)}"
    )


def main() -> None:
    for yr in (2018, 2017, 2016):
        parse_single_year(yr)


if __name__ == "__main__":
    main()
