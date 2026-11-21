# -*- coding: utf-8 -*-
"""
Build Codex image assets (sheets, transparent front-view sprites, closeup avatars)
and structured codex.json from AI_2Dgirls_Gallery-main, plus QA contact sheets.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.ndimage import binary_dilation, label

ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = Path(r"c:\Users\6\Desktop\AI_2Dgirls_Gallery-main")
GALLERY_JSON = SRC_ROOT / "data" / "gallery-data.json"

OUT_CODEX = ROOT / "web" / "public" / "codex"
OUT_SHEETS = OUT_CODEX / "sheets"
OUT_SPRITES = OUT_CODEX / "sprites"
OUT_AVATARS = OUT_CODEX / "avatars"
OUT_JSON = ROOT / "web" / "public" / "data" / "codex.json"

QA_DIR = Path(
    r"C:\Users\6\.gemini\antigravity\brain\41e1a533-63f2-4ecb-9a5f-7e2268a97ee3\scratch"
)

VARIANTS: List[Tuple[str, str, str, str, str]] = [
    ("chibi", "03_Q版", "Q版", "R", "Q版"),
    ("medium", "02_中间体型版", "中间体型版", "SR", "中间体型版"),
    ("standard", "01_标准版", "标准版", "SSR", "标准版"),
]

# Character-specific kaoyan & hydraulics study quotes (6 each) + judge/greet lines
STUDY_DIALOGUES: Dict[str, dict] = {
    "chatgpt": {
        "greetTemplate": "所有真题草稿都已归档就位！先把今天最想攻克的章节告诉我吧。",
        "judgeOkQuote": "思路很稳！把这道题的推导步骤顺手记下来，就是考场上的模板。",
        "judgeWarnQuote": "别急，错题也是草稿本里最宝贵的线索，展开精解看看卡在哪一步。",
        "studyQuotes": [
            "伯努利方程列式三步走：定基准面、选过水断面、补齐沿程与局部水头损失。",
            "复习别只看结论，把每道大题的第一步受力图画出来，答案就成功一半。",
            "遇到不会的综合题先拆成静力学、动力学、明渠流三个小模块，逐段击破。",
            "错题本不是失败清单，是帮你在考前把失分点提前收编进掌控区的档案。",
            "模考结束后记得复盘时间分配，小题尽量控制在 25 分钟内稳稳拿下。",
            "草稿纸分栏编号写清楚，考场上复查验算时能帮你省下十分钟！",
        ],
    },
    "claude": {
        "greetTemplate": "书房的热茶刚沏好，今天也按自己的节奏把每道题吃透吧。",
        "judgeOkQuote": "非常扎实！边界条件和符号正负都没有遗漏，继续保持这份细心。",
        "judgeWarnQuote": "没关系，我们慢下来再读一遍题干条件——是不是忽略了某个隐含假设？",
        "studyQuotes": [
            "读题时先圈出『均匀流 / 非均匀流』『恒定 / 非恒定』『粗糙区 / 过渡区』，别直接代公式。",
            "写推导与证明题时，每引用一条假设（如不可压缩、理想流体）都顺手写明，采分点稳稳拿满。",
            "静水总压力算铅垂分力时，先明确压力体是实还是虚、向上还是向下，再落笔积分。",
            "遇到复杂管道串并联问题，先列清节点连续方程，再对每个环路列出能量平衡。",
            "公式背诵不用贪多，每天用 3D 闪卡过五组，把物理量纲和适用雷诺数一起记住。",
            "做完一整套真题后留十分钟总结错因，比多刷十道同类题更有效。",
        ],
    },
    "deepseek": {
        "greetTemplate": "咕噜……今天也要潜入深蓝题海捞上岸吗？先喝口水再开刷！",
        "judgeOkQuote": "漂亮！一发命中核心考点，大肥鱼给你鼓鼓掌～",
        "judgeWarnQuote": "咦，这题藏了个小暗礁！先别划走，看看解析是怎么绕过去的。",
        "studyQuotes": [
            "明渠非均匀流 12 条水面线口诀：先判底坡（缓/陡/临），再看水深落在 1/2/3 哪一区！",
            "算水跃共轭水深之前，先算一下临界水深 hk，千万别把急流和缓流搞反啦。",
            "动量方程求水流对弯管的作用力，别漏掉上下游断面的静水压强合力！",
            "雷诺实验记住临界雷诺数 Re_c ≈ 2000（圆管），层流沿程损失系数 λ = 64/Re 必考！",
            "错题本里积攒的题都是考前最能提分的宝藏，今天也顺手清掉两道吧～",
            "刷题累了就伸个懒腰，把『半会』的题再手算一遍，考场绝不手生。",
        ],
    },
    "gemini": {
        "greetTemplate": "观测站星光就位！让我们把分散的考点和公式连成一张清晰星图吧～",
        "judgeOkQuote": "闪耀命中！思路像流线一样丝滑，直接进入下一题！",
        "judgeWarnQuote": "发现一处能量跃变陷阱！展开下方解析图，换个视角重新梳理一下吧。",
        "studyQuotes": [
            "把历年真题按『章节 × 方法』双轴对照，你会发现高频大题其实就那几套模型。",
            "画水面曲线定性草图时，先用虚线标出 N-N（正常水深线）与 C-C（临界水深线）。",
            "渗流问题牢记达西定律适用层流，浸润线计算和井流公式要分清承压与无压！",
            "量纲分析 π 定理选基本量时，记得挑几何、运动、动力各一个且互不相关的物理量。",
            "遇到不会做的原题别空着，对照采分点拆出已知条件与控制方程，照样拿步骤分。",
            "3D 公式闪卡翻面抽背的时候，试着在脑海里还原方程每一项的几何意义！",
        ],
    },
    "glm": {
        "greetTemplate": "待办清单和真题档案都已整理成三步流程，按顺序推进吧。",
        "judgeOkQuote": "严谨无误，已归入『已掌握』台账。继续保持这份秩序感。",
        "judgeWarnQuote": "发现一处疏漏，我已经记进错题手册了。先把这一题订正完再休息吧。",
        "studyQuotes": [
            "复习效率来自秩序：先清前一天错题，再刷今日新卷，最后背十分钟公式闪卡。",
            "平面静水总压力记住两件事：大小看形心压强乘面积，作用点永远在形心下方。",
            "孔口与管嘴出流别混用系数：圆柱形外管嘴流量系数 μ ≈ 0.82，真空度有上限！",
            "算管网阻力时注意区分『短管』（计局部+流速水头）和『长管』（可略去局部和流速水头）。",
            "每天做题不用追求爆刷一百道，把每道大题的单位换算和有效数字核对准才关键。",
            "这一页任务完成之后，记得给自己留一点点心和休息时间，张弛有度才能走远。",
        ],
    },
    "grok": {
        "greetTemplate": "天台电台上线！别光顾着刷简单题，敢不敢来啃一道压轴计算？",
        "judgeOkQuote": "干脆利落！这种陷阱题都没能骗到你，有点东西啊。",
        "judgeWarnQuote": "哈哈，正中出题人下怀吧？快来看看解析拆穿这个套路！",
        "studyQuotes": [
            "出题人最爱在单位上挖坑：看到 kPa、cm、L/s 先统一换算成国际单位制再动笔！",
            "明渠水力最优断面不是背公式，是记住矩形 b=2h、梯形水力半径 R=h/2 的核心特征。",
            "水击计算先判断直接水击还是间接水击：比较阀门关闭时间 Ts 与相长 2L/c 的大小！",
            "别被复杂的组合曲面吓到，拆成水平投影矩形和铅垂压力体，几何面积都会算。",
            "全真模考别跳步骤，180 分钟逼着自己完整手写一遍，才能暴露真正的卡壳点。",
            "错题越早暴露越赚，现在踩过的坑，考场上就不会再踩第二遍！",
        ],
    },
    "hunyuan": {
        "greetTemplate": "展厅晨光正好，真题预算与时间余量都给你留足了，从容开练吧。",
        "judgeOkQuote": "算盘一响，分毫不差！这题的分值稳稳收入囊中。",
        "judgeWarnQuote": "账面稍微对不上号哦，核对一下正负号和断面编号再试一次。",
        "studyQuotes": [
            "算静水压强分布图和压力体体积时，就像对账一样，方向一正一负抵消得清清楚楚。",
            "有压管道串并联记住两句话：串联流量相等损失相加，并联水头损失相等流量相加。",
            "计算题尽量把中间结果保留三位有效数字，防止连环代入把最终误差放大。",
            "水泵扬程计算别忘了把吸水管和压水管的全部沿程、局部水头损失都加进需求里。",
            "把历年真题各章分值热力图看一遍，优先重兵投入年均 30 分以上的核心大章。",
            "考前最后阶段稳住基本盘，基础判断与简答分拿稳，大题写出控制方程就不慌。",
        ],
    },
    "kimi": {
        "greetTemplate": "月台图书室很安静，你上次停下的那页错题，我替你夹好书签了。",
        "judgeOkQuote": "嗯，这一步的上下文衔接得很好。记在日志里了，继续吧。",
        "judgeWarnQuote": "没关系，先停一拍。把题目条件从头到尾重新读一遍，答案就在字里行间。",
        "studyQuotes": [
            "长计算题最怕读漏后面补充的已知条件，动笔前花十秒把所有条件列成小清单。",
            "流线与迹线区别：恒定流时二者重合；非恒定流时一般不重合，概念题常考。",
            "连续性方程、能量方程、动量方程被称为水力学三大基石，90% 的大题都在联立它们。",
            "推导题记不住全篇没关系，记住微元控制体的受力平衡或质量守恒出发点就能现场推出。",
            "深夜刷题效率下降时，换成翻看公式手册或复盘白天记录的私人笔记会更轻松。",
            "长夜足够把一整门专业课梳理通透，一步一步来，每一页都会算数。",
        ],
    },
    "llama": {
        "greetTemplate": "工作台多留了把椅子给你！这一题我们一步一步拆解，好吗？",
        "judgeOkQuote": "太棒啦！这一步你独立解出来了，我们接着拼下一块！",
        "judgeWarnQuote": "别灰心，做实验也是调一处再试一次。看看解析里是怎么迈出第一步的吧。",
        "studyQuotes": [
            "复习水力学就像拼布，把静力学、流态判别、管流和明渠一点点拼成完整知识网。",
            "遇到陌生的综合实验或量纲分析题，先用 Buckingham π 定理把已知量纲全部写出指数矩阵。",
            "尼古拉兹实验曲线的五个区一定要画在脑子里：层流区、过渡区、光滑区、粗糙过渡、阻力平方区。",
            "模型试验中重力主导（明渠、堰流）用弗劳德准则 Fr，粘性力主导（有压满管）用雷诺准则 Re。",
            "把做错的题目写上自己的『一句话避坑笔记』，过一周再看真的超管用！",
            "每天坚持完成一个小目标，累积起来就是上岸那天最踏实的底气。",
        ],
    },
    "minimax": {
        "greetTemplate": "场记板准备就绪！Action——把今天的真题演练拍成高分大戏吧！",
        "judgeOkQuote": "Cut！一条过！这题节奏和答案都漂亮极了！",
        "judgeWarnQuote": "NG 啦！没关系，查看解析调整一下机位，下一条一定稳过！",
        "studyQuotes": [
            "解题就像拍镜头，先给整个流动系统来个『全景』（控制体），再切『特写』（计算断面）。",
            "堰流计算区分薄壁堰、实用堰和宽顶堰，侧收缩和淹没修正系数看清题干给不给。",
            "有压管恒定流总水头线永远沿程下降，而测压管水头线在管径扩张处可能上升！",
            "明渠水跃发生条件是从急流（Fr > 1）向缓流（Fr < 1）跃迁，伴随大量水头损失。",
            "全真模考计时器一开就像正式开机，前五分钟先通览全卷分值排好做题顺序。",
            "每解决一道拦路虎错题，就等于多剪完一场漂亮镜头，成就感满满！",
        ],
    },
    "mistral": {
        "greetTemplate": "暖风和真题地图都带好啦！今天打算先突破哪一座考点高地？",
        "judgeOkQuote": "漂亮收工！干净利落，简直像阵风一样穿过这道题！",
        "judgeWarnQuote": "哎呀，路标看岔了？展开解析重新校准航向，咱们立刻再出发！",
        "studyQuotes": [
            "自由射流与管嘴出流问题，直接找大气压面作为能量方程断面，计算瞬间清爽一半。",
            "欧拉平衡微分方程和静止流体等压面性质：重力场中等压面必是水平面且互相平行。",
            "流网绘制与判读牢记正交性：流线与等势线处处垂直，网格长宽比保持一致。",
            "算流速分布时记住：层流圆管呈抛物线分布（动能修正系数 α=2），紊流较均匀（α≈1）。",
            "刷真题不要只顾着往前冲，偶尔回头把本周错题速通一遍能提速不少！",
            "保持轻快的好奇心去理解物理图景，公式其实都只是自然规律的速记符号。",
        ],
    },
    "qwen": {
        "greetTemplate": "书房小灯已点亮，带着今天的疑问坐下吧，我们一条一条理清楚。",
        "judgeOkQuote": "嗯，步骤清晰、结论准确！记得去领今天的小鱼干奖励哦。",
        "judgeWarnQuote": "这里稍微拐了个弯，对照下方分步精解，把漏掉的那一环补上吧。",
        "studyQuotes": [
            "先定题型，再选控制方程：静水找平衡，恒定找能量，求力找动量，变断面盯连续。",
            "判断管流处于紊流哪个区：先算层流底层厚度 δ 与绝对粗糙度 Δ 的比值（或雷诺数界限）。",
            "明渠均匀流谢才公式 C = R^(1/6) / n（曼宁公式），记住糙率 n 越大、过流能力越小。",
            "边界层分离的必要条件是逆压梯度（dp/dx > 0）加上流体粘性的滞止作用，简答题高频！",
            "考纲重点章节按 20%、30% 分配时间，用命题结构大盘一眼看清各章历史出题规律。",
            "再小的一个概念疑惑，只要今天弄懂了，考场上就不会变成丢分项。",
        ],
    },
    "seed": {
        "greetTemplate": "今天的复习灵感正在发芽！先从一道拿手小题热热身怎么样？",
        "judgeOkQuote": "太好啦！又有一道题开出满分小花，继续种下更多进度吧！",
        "judgeWarnQuote": "这颗小种子暂时卡在土里了，打开解析给它浇点水，马上就能搞懂～",
        "studyQuotes": [
            "每多掌握一道真题，知识花园里就多点亮一盏绿灯，看着进度条涨起来超治愈！",
            "势流叠加原理和流函数、势函数关系（柯西-黎曼条件）是很多院校的选择简答爱考题。",
            "卡门涡街频率与斯托罗哈数 St 有关，遇到绕流阻力题记清楚压差阻力与摩擦阻力区别。",
            "如果今天状态一般，就先去『公式手册』用 3D 闪卡翻十张，保持手感不掉线。",
            "把错题本里的题目逐个标记成『已掌握』，看着待攻克数清零超级解压！",
            "别担心起步晚，把每个当下的五道题踏踏实实弄懂，结局一定会越来越亮堂。",
        ],
    },
    "wenxin": {
        "greetTemplate": "窗边书桌已经摆好，把今天遇到的关键方程和疑难点认真写下来吧。",
        "judgeOkQuote": "笔落精准，论证严谨。这份扎实会陪你一直走到考场交卷那一刻。",
        "judgeWarnQuote": "这里还需要多推敲一句。细读下方精解的易错提示，把细节补充完整吧。",
        "studyQuotes": [
            "名词解释与简答题最重逻辑关键词：比如『水力半径 R = A/χ』『佛汝德数 Fr 的物理意义』。",
            "压强三种表示法（绝对压强、相对压强、真空度）互换时，务必锚定当地大气压基准。",
            "推导沿程水头损失达西公式时，记住切应力分布从管轴线性增大到管壁的物理图像。",
            "做笔记不需要长篇大论，写一句『为什么当时我算错了』，就能救回考场上同样的失误。",
            "连续学习一段时间记得远眺放松肩颈，健康和好心态同样是考研战斗力的一部分。",
            "每一段仔细推演过的公式，都会在你下笔的时候变成最稳的回声。",
        ],
    },
}

SP_CARDS = [
    {
        "id": "sp:dafeyu",
        "code": "DF-01",
        "name": "大肥鱼（经典四姿态）",
        "subtitle": "鲸研首发看板娘 · 海洋系护航",
        "role": "鲸研首发看板娘 · 全姿态动态响应",
        "color": "#22c7f2",
        "tags": ["初始看板娘", "四姿态切换", "蓝白女仆", "鲸尾"],
        "rarity": "SP",
        "sprite": "./mascot/hero.webp",
        "avatar": "./mascot/hero.webp",
        "bio": "鲸研专业课最初的陪伴伙伴「大肥鱼」，内置欢迎 / 刷题 / 沉思 / 欢呼四种独立立绘姿态，随答题对错与掌握度自动切换神态。",
        "credit": "原型「溟月」出自「上善无形」，女仆装二创设定源自「ZipZipPipe」（CC BY-NC-SA 4.0 非商业共享）；本站四姿态 Q 版立绘经 AI 重绘与透明抠图制作。",
        "greetTemplate": "你好呀，我是大肥鱼！今天也一起把考研真题一点点啃下来吧～",
        "judgeOkQuote": "判断正确！本题已归档为已掌握，继续保持节奏～",
        "judgeWarnQuote": "判断失误！已自动同步至错题本，展开下方精解核查陷阱吧。",
        "studyQuotes": [
            "伯努利方程先定基准面、再找渐变流断面，水头损失一项都别漏！",
            "静水总压力曲面算水平与铅垂分力，压力体虚实一定先画箭头判断方向～",
            "明渠非均匀流 12 条水面线：先判坡度（缓/陡），再看水深落在 1/2/3 哪一区！",
            "刷错的题会自动同步进错题本，考前清零错题本就能稳稳上岸！",
            "完成每日任务可以攒小鱼干，去补给站开卡包解锁更多性格各异的陪读搭档哦～",
        ],
    },
    {
        "id": "sp:gemini",
        "code": "GMN-SP",
        "name": "Gemini（协研纪念版）",
        "subtitle": "AI 联合协研与真题精解纪念卡",
        "role": "特邀协研角色 · 站点共创纪念",
        "color": "#a78bfa",
        "tags": ["协研纪念", "猫耳", "异色瞳", "初始赠卡"],
        "rarity": "SP",
        "sprite": "./mascot/gemini.webp",
        "avatar": "./mascot/gemini.webp",
        "bio": "特别鸣谢 Google Gemini 深度参与河海 814 与扬大 849 共 31 套考研水力学真题精解梳理、16000+ 处 KaTeX 核验与 47 幅原题图清晰重绘。",
        "credit": "角色形象为本站通过 AI 自行生成的非商业致谢插图（非 Google 官方吉祥物，亦不主张上游 CC 授权）。",
        "greetTemplate": "协研频道在线！31 套真题精解与高清重绘配图已就位，随时可以开刷。",
        "judgeOkQuote": "推导验证通过！逻辑链与公式边界都十分严密。",
        "judgeWarnQuote": "检测到概念误差，建议对照下方精解与重绘示意图核对关键步骤。",
        "studyQuotes": [
            "16485 处 KaTeX 公式已全部通过静态校验，安心刷题与背诵公式吧！",
            "遇到模糊手绘原题的年份，我们已重绘为高清蓝图矢量风格，暗黑模式也能护眼阅读。",
            "采分点自评模式下，试着按照步骤拆分写清控制方程，锻炼考场规范拿分。",
            "在错题笔记写下自己的思考，复盘效率会翻倍提升。",
            "祝你专业课一战成硕，顺利上岸目标院校！",
        ],
    },
]


def is_cool_slate_border(rgb: np.ndarray) -> np.ndarray:
    """Detect cool blue-gray / neutral-gray rounded panel border lines."""
    r = rgb[:, :, 0].astype(np.int16)
    g = rgb[:, :, 1].astype(np.int16)
    b = rgb[:, :, 2].astype(np.int16)
    mn = np.minimum(np.minimum(r, g), b)
    mx = np.maximum(np.maximum(r, g), b)
    # Cool gray / light slate line: bright-ish neutral or slightly cool blue
    return (mn >= 95) & (mn <= 238) & ((mx - mn) <= 92) & (b >= r - 12)


def strip_outer_box_border(sub: np.ndarray, margin: int = 26) -> np.ndarray:
    """
    Erase straight thin frame border lines near the outer edges of a panel
    without harming character art that crosses into the border area.
    """
    out = sub.copy()
    h, w, _ = out.shape
    border_px = is_cool_slate_border(out)
    light_px = out.min(axis=2) >= 185

    # Horizontal borders in top margin & bottom margin
    mid_x0 = min(w // 4, 40)
    mid_x1 = max(w - mid_x0, w - 40)
    span_w = max(1, mid_x1 - mid_x0)

    def erase_h_bands(y_range: range):
        detected = []
        for y in y_range:
            if y < 0 or y >= h:
                continue
            cov = border_px[y, mid_x0:mid_x1].mean()
            if cov >= 0.55:
                detected.append(y)
        for y in detected:
            for dy in (-1, 0, 1):
                yy = y + dy
                if 0 <= yy < h:
                    mask = border_px[yy] | (light_px[yy] & (abs(dy) == 1))
                    out[yy, mask] = 255

    def erase_v_bands(x_range: range):
        mid_y0 = min(h // 4, 40)
        mid_y1 = max(h - mid_y0, h - 40)
        detected = []
        for x in x_range:
            if x < 0 or x >= w:
                continue
            cov = border_px[mid_y0:mid_y1, x].mean()
            if cov >= 0.55:
                detected.append(x)
        for x in detected:
            for dx in (-1, 0, 1):
                xx = x + dx
                if 0 <= xx < w:
                    mask = border_px[:, xx] | (light_px[:, xx] & (abs(dx) == 1))
                    out[mask, xx] = 255

    erase_h_bands(range(0, min(margin, h)))
    erase_h_bands(range(max(0, h - margin), h))
    erase_v_bands(range(0, min(margin, w)))
    erase_v_bands(range(max(0, w - margin), w))

    # Also clean rounded corner arcs (18x18 at the 4 corners) where cool-gray border exists
    c = min(22, h // 6, w // 6)
    corner_mask = np.zeros((h, w), dtype=bool)
    corner_mask[:c, :c] = True
    corner_mask[:c, w - c :] = True
    corner_mask[h - c :, :c] = True
    corner_mask[h - c :, w - c :] = True
    out[corner_mask & border_px] = 255

    # Clean tiny 1-2px border fragments along the outermost 3px rim
    rim_mask = np.zeros((h, w), dtype=bool)
    rim_mask[:4, :] = True
    rim_mask[h - 4 :, :] = True
    rim_mask[:, :4] = True
    rim_mask[:, w - 4 :] = True
    out[rim_mask & border_px] = 255
    return out


def dp_vertical_seam_cut(fg: np.ndarray, x_min: int, x_max: int) -> np.ndarray:
    """
    Find a minimum-cost seam from top to bottom inside [x_min, x_max]
    separating the front-view figure (left) from the side-view figure (right).
    Returns a boolean mask keeping pixels left of the seam.
    """
    h, w = fg.shape
    x0 = max(0, x_min)
    x1 = min(w - 1, x_max)
    sub_fg = fg[:, x0 : x1 + 1].astype(np.float32)
    sw = sub_fg.shape[1]

    # Prefer the lowest-foreground column on average as gentle center bias
    col_means = sub_fg.mean(axis=0)
    center_bias = 0.002 * col_means

    cost = np.zeros((h, sw), dtype=np.float32)
    back = np.zeros((h, sw), dtype=np.int16)
    cost[0] = sub_fg[0] * 100.0 + center_bias

    # Step penalty for lateral moves (-1, 0, +1)
    for y in range(1, h):
        prev = cost[y - 1]
        best_c = prev.copy()
        best_k = np.arange(sw, dtype=np.int16)

        # From left (x-1 -> x)
        c_left = np.empty(sw, dtype=np.float32)
        c_left[0] = 1e9
        c_left[1:] = prev[:-1] + 0.08
        mask_l = c_left < best_c
        best_c[mask_l] = c_left[mask_l]
        best_k[mask_l] = np.arange(sw, dtype=np.int16)[mask_l] - 1

        # From right (x+1 -> x)
        c_right = np.empty(sw, dtype=np.float32)
        c_right[-1] = 1e9
        c_right[:-1] = prev[1:] + 0.08
        mask_r = c_right < best_c
        best_c[mask_r] = c_right[mask_r]
        best_k[mask_r] = np.arange(sw, dtype=np.int16)[mask_r] + 1

        cost[y] = best_c + sub_fg[y] * 100.0 + center_bias
        back[y] = best_k

    seam = np.zeros(h, dtype=np.int32)
    cur = int(np.argmin(cost[h - 1]))
    for y in range(h - 1, -1, -1):
        seam[y] = x0 + cur
        cur = int(back[y, cur])

    xs = np.arange(w)[None, :]
    return xs <= seam[:, None]


def cutout_front_sprite(arr: np.ndarray, variant: str) -> Image.Image:
    """Isolate the front-view full-body character and remove white background cleanly."""
    h, w, _ = arr.shape

    if variant == "standard":
        col_cov = (arr.min(axis=2) < 245).mean(axis=0)
        vx = 980 + int(np.argmin(col_cov[980:1080]))
        sub = arr[:, :vx].copy()
        seam_range = (340, 470)
        max_valid_right = 530
    elif variant == "medium":
        row_cov = (arr.min(axis=2) < 245).mean(axis=1)
        hy = 600 + int(np.argmin(row_cov[600:675]))
        top_band = arr[: hy - 4, :]
        col_t = (top_band.min(axis=2) < 245).mean(axis=0)
        lx = 460 + int(np.argmin(col_t[460:560]))
        sub = strip_outer_box_border(arr[:hy, :lx], margin=24)
        seam_range = None
        max_valid_right = lx
    else:  # chibi
        row_cov = (arr.min(axis=2) < 245).mean(axis=1)
        hy = 600 + int(np.argmin(row_cov[600:675]))
        sub = strip_outer_box_border(arr[:hy, :], margin=24)
        seam_range = (440, 560)
        max_valid_right = 590

    sh, sw, _ = sub.shape
    yy = np.arange(sh)[:, None]
    mn = sub.min(axis=2)
    mx = sub.max(axis=2)
    diff = mx.astype(np.int16) - mn.astype(np.int16)

    # Strict foreground mask for component isolation (ignores soft gray floor shadows)
    floor_shadow = (yy > int(sh * 0.91)) & (mn > 182) & (diff < 32)
    fg = ((mn < 232) | (diff > 18)) & (~floor_shadow)

    lbl, n_comp = label(fg)
    counts = np.bincount(lbl.ravel())

    # Pick main leftmost component (front character)
    best_id = 0
    best_area = 0
    for i in range(1, n_comp + 1):
        if counts[i] < 6000:
            continue
        ys_i, xs_i = np.where(lbl == i)
        if xs_i.mean() < sw * 0.42 and counts[i] > best_area:
            best_area = int(counts[i])
            best_id = i

    if best_id == 0 and n_comp > 0:
        best_id = int(np.argmax(counts[1:]) + 1)

    ys_m, xs_m = np.where(lbl == best_id)
    if len(xs_m) > 0 and xs_m.max() > max_valid_right and seam_range is not None:
        # Front figure touched side figure — cut via DP minimum-cost vertical seam
        keep_left = dp_vertical_seam_cut(fg, seam_range[0], seam_range[1])
        fg = fg & keep_left
        lbl, n_comp = label(fg)
        counts = np.bincount(lbl.ravel())
        best_id = 0
        best_area = 0
        for i in range(1, n_comp + 1):
            if counts[i] < 4000:
                continue
            _, xs_i = np.where(lbl == i)
            if xs_i.mean() < sw * 0.55 and counts[i] > best_area:
                best_area = int(counts[i])
                best_id = i
        if best_id == 0 and n_comp > 0:
            best_id = int(np.argmax(counts[1:]) + 1)
        ys_m, xs_m = np.where(lbl == best_id)

    # Keep main front figure + small detached accessories (floating ahoge/stars/sparkles)
    keep_fg = lbl == best_id
    if len(xs_m) > 0:
        fx0, fx1 = int(xs_m.min()), int(xs_m.max())
        fy0, fy1 = int(ys_m.min()), int(ys_m.max())
        for i in range(1, n_comp + 1):
            if i == best_id or counts[i] < 12 or counts[i] > 4500:
                continue
            ys_i, xs_i = np.where(lbl == i)
            cx_i = float(xs_i.mean())
            cy_i = float(ys_i.mean())
            # Must sit comfortably inside/near front figure span (and left of side figure)
            if (fx0 - 30) <= cx_i <= (fx1 + 12) and (fy0 - 40) <= cy_i <= (fy1 + 20):
                # Ensure it's not closer to side figure on the right
                if variant == "medium" or cx_i <= min(fx1 + 10, max_valid_right - 15):
                    keep_fg |= lbl == i

    # Zero out non-front foreground regions (side/back views) to pure white
    keep_region = binary_dilation(keep_fg, iterations=8)
    cleaned = sub.copy()
    cleaned[~keep_region] = 255

    # Exterior background flood from image border (preserves interior white dress/socks!)
    c_mn = cleaned.min(axis=2)
    c_mx = cleaned.max(axis=2)
    c_diff = c_mx.astype(np.int16) - c_mn.astype(np.int16)
    bg_cand = (
        ((c_mn >= 236) & (c_diff <= 20))
        | ((yy > int(sh * 0.90)) & (c_mn >= 205) & (c_diff <= 28))
    )
    bg_lbl, _ = label(bg_cand)
    border_labels = set(np.unique(bg_lbl[0, :]).tolist())
    border_labels.update(np.unique(bg_lbl[sh - 1, :]).tolist())
    border_labels.update(np.unique(bg_lbl[:, 0]).tolist())
    border_labels.update(np.unique(bg_lbl[:, sw - 1]).tolist())
    border_labels.discard(0)

    ext_bg = np.isin(bg_lbl, list(border_labels))

    # Build smooth alpha & defringe 1px bright neutral boundary halo
    alpha = np.where(ext_bg, 0.0, 255.0)
    sil_edge = (~ext_bg) & binary_dilation(ext_bg, iterations=1)
    bright_neutral = (c_mn >= 210) & (c_diff <= 24)
    # Soften bright near-white fringe pixels on outer silhouette
    fringe = sil_edge & bright_neutral
    alpha[fringe] = np.clip((242.0 - c_mn[fringe]) * 4.5, 0.0, 175.0)

    alpha_img = Image.fromarray(alpha.astype(np.uint8), mode="L").filter(
        ImageFilter.GaussianBlur(0.5)
    )
    rgba = Image.fromarray(cleaned, mode="RGB").convert("RGBA")
    rgba.putalpha(alpha_img)

    # Crop tight around non-transparent pixels with padding, bottom-aligned in 512x512
    a_arr = np.array(alpha_img)
    bbox = Image.fromarray((a_arr > 12).astype(np.uint8) * 255).getbbox()
    if bbox:
        pad = 12
        x0, y0, x1, y1 = bbox
        rgba = rgba.crop(
            (max(0, x0 - pad), max(0, y0 - pad), min(sw, x1 + pad), min(sh, y1 + pad))
        )

    side = max(rgba.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(rgba, ((side - rgba.width) // 2, side - rgba.height), rgba)
    return canvas.resize((512, 512), Image.LANCZOS)


def find_inner_box(panel: np.ndarray) -> Tuple[int, int, int, int]:
    """Find inner rectangle strictly inside a panel's cool-gray border lines."""
    ph, pw, _ = panel.shape
    bp = is_cool_slate_border(panel)
    # Row coverage in horizontal middle 60%
    rx0, rx1 = int(pw * 0.2), int(pw * 0.8)
    rcov = bp[:, rx0:rx1].mean(axis=1)
    # Col coverage in vertical middle 60%
    cy0, cy1 = int(ph * 0.2), int(ph * 0.8)
    ccov = bp[cy0:cy1, :].mean(axis=0)

    # True panel borders sit within 28px of the panel slice boundary and span >= 65%
    top_rows = [y for y in range(0, min(28, ph // 5)) if rcov[y] > 0.65]
    bot_rows = [y for y in range(max(0, ph - 28), ph) if rcov[y] > 0.65]
    left_cols = [x for x in range(0, min(28, pw // 5)) if ccov[x] > 0.65]
    right_cols = [x for x in range(max(0, pw - 28), pw) if ccov[x] > 0.65]

    y0 = (max(top_rows) + 6) if top_rows else 12
    y1 = (min(bot_rows) - 6) if bot_rows else (ph - 12)
    x0 = (max(left_cols) + 6) if left_cols else 12
    x1 = (min(right_cols) - 6) if right_cols else (pw - 12)
    return x0, y0, max(x0 + 64, x1), max(y0 + 64, y1)


def crop_closeup_avatar(arr: np.ndarray, variant: str, char_id: str = "") -> Image.Image:
    """Crop the high-res face closeup panel into a clean 320x320 square avatar."""
    h, w, _ = arr.shape
    if variant == "standard":
        col_cov = (arr.min(axis=2) < 245).mean(axis=0)
        vx = 980 + int(np.argmin(col_cov[980:1080]))
        right_slice = arr[:, vx + 4 :]
        row_r = (right_slice.min(axis=2) < 245).mean(axis=1)
        closeup_bot = 460 + int(np.argmin(row_r[460:760]))
        panel = arr[:closeup_bot, vx + 4 :]
    else:
        row_cov = (arr.min(axis=2) < 245).mean(axis=1)
        hy = 600 + int(np.argmin(row_cov[600:675]))
        bot_slice = arr[hy + 4 :, :]
        col_b = (bot_slice.min(axis=2) < 245).mean(axis=0)
        bx = 540 + int(np.argmin(col_b[540:760]))
        panel = arr[hy + 4 :, :bx]

    ix0, iy0, ix1, iy1 = find_inner_box(panel)
    inner = panel[iy0:iy1, ix0:ix1]
    ih, iw, _ = inner.shape

    side = min(iw, ih)
    if iw >= ih:
        # Center on upper-middle face region (avoids wide props/headdresses on edges)
        if char_id == "qwen" and variant == "chibi":
            cx = int(iw * 0.56)
        else:
            cx = iw // 2
        sx0 = max(0, min(iw - side, cx - side // 2))
        sy0 = 0
    else:
        # Tall closeup box (standard): keep top portion (face + hair/ears)
        sx0 = (iw - side) // 2
        sy0 = min(ih - side, max(0, int((ih - side) * 0.14)))

    crop = Image.fromarray(inner[sy0 : sy0 + side, sx0 : sx0 + side], mode="RGB")
    return crop.resize((320, 320), Image.LANCZOS)


def make_contact_sheet(
    items: List[Tuple[str, Image.Image]], out_path: Path, bg_rgb: Tuple[int, int, int]
) -> None:
    cols = 7
    rows = (len(items) + cols - 1) // cols
    cell_w, cell_h = 200, 224
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), bg_rgb)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for idx, (label_text, im) in enumerate(items):
        r, c = divmod(idx, cols)
        x = c * cell_w
        y = r * cell_h
        thumb = im.copy()
        thumb.thumbnail((cell_w - 16, cell_h - 32), Image.LANCZOS)
        ox = x + (cell_w - thumb.width) // 2
        oy = y + (cell_h - 24 - thumb.height) // 2
        if thumb.mode == "RGBA":
            sheet.paste(thumb, (ox, oy), thumb)
        else:
            sheet.paste(thumb, (ox, oy))
        draw.rectangle([x, y, x + cell_w - 1, y + cell_h - 1], outline=(40, 56, 78))
        draw.text((x + 8, y + cell_h - 18), label_text, fill=(215, 228, 244), font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, "PNG")


def main() -> int:
    if not GALLERY_JSON.exists():
        raise FileNotFoundError(f"Missing reference data: {GALLERY_JSON}")

    raw_data = json.loads(GALLERY_JSON.read_text(encoding="utf-8"))
    characters_raw = raw_data["characters"]

    # Clean output folders so reruns don't leave stale files
    for d in (OUT_SHEETS, OUT_SPRITES, OUT_AVATARS):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    qa_sprites: List[Tuple[str, Image.Image]] = []
    qa_avatars: List[Tuple[str, Image.Image]] = []
    codex_chars: List[dict] = []

    for idx, c in enumerate(characters_raw, start=1):
        cid = c["id"]
        dialogue = STUDY_DIALOGUES[cid]
        variants_meta = {}

        for variant_key, src_folder, src_suffix, rarity, label_zh in VARIANTS:
            # Resolve original file from gallery-data.json relative path
            orig_rel = c["images"][variant_key]["original"]
            orig_path = SRC_ROOT / orig_rel
            if not orig_path.exists():
                raise FileNotFoundError(f"Missing original image: {orig_path}")

            with Image.open(orig_path) as im:
                rgb_im = im.convert("RGB")
                arr = np.array(rgb_im)

                # 1. Full reference sheet (900x675)
                sheet_im = rgb_im.copy()
                sheet_im.thumbnail((900, 675), Image.LANCZOS)
                sheet_file = f"{cid}-{variant_key}.webp"
                sheet_im.save(OUT_SHEETS / sheet_file, "WEBP", quality=84, method=6)

                # 2. Transparent front-view sprite (512x512 RGBA)
                sprite_im = cutout_front_sprite(arr, variant_key)
                sprite_file = f"{cid}-{variant_key}.webp"
                sprite_im.save(OUT_SPRITES / sprite_file, "WEBP", quality=88, method=6)
                qa_sprites.append((f"{cid}-{variant_key} [{rarity}]", sprite_im))

                # 3. Closeup avatar (320x320 RGB)
                avatar_im = crop_closeup_avatar(arr, variant_key, cid)
                avatar_file = f"{cid}-{variant_key}.webp"
                avatar_im.save(OUT_AVATARS / avatar_file, "WEBP", quality=88, method=6)
                qa_avatars.append((f"{cid}-{variant_key}", avatar_im))

            variants_meta[variant_key] = {
                "cardId": f"{cid}:{variant_key}",
                "rarity": rarity,
                "label": label_zh,
                "sheet": f"./codex/sheets/{sheet_file}",
                "sprite": f"./codex/sprites/{sprite_file}",
                "avatar": f"./codex/avatars/{avatar_file}",
            }

        sources_clean = [
            {
                "id": s["id"],
                "title": s["title"],
                "url": s["url"],
                "author": s["author"],
                "date": s["date"],
                "evidence": s["evidence"],
                "limits": s["limits"],
            }
            for s in c.get("sources", [])
        ]

        ps = c["projectSetting"]
        vis = c["visual"]
        codex_chars.append(
            {
                "id": cid,
                "code": f"AI-{idx:02d}",
                "name": c["name"],
                "aliases": c.get("aliases", []),
                "subtitle": vis["subtitle"],
                "color": vis["color"],
                "tags": vis["tags"],
                "visual": vis["visual"],
                "motif": vis["motif"],
                "hook": vis["hook"],
                "communitySummary": c.get("communitySummary", ""),
                "projectRole": ps["role"],
                "projectBackground": ps["background"],
                "personality": ps.get("personality", []),
                "speechStyle": ps["speechStyle"],
                "relationships": ps["relationships"],
                "sources": sources_clean,
                "studyQuotes": dialogue["studyQuotes"],
                "greetTemplate": dialogue["greetTemplate"],
                "judgeOkQuote": dialogue["judgeOkQuote"],
                "judgeWarnQuote": dialogue["judgeWarnQuote"],
                "variants": variants_meta,
            }
        )

    catalog = {
        "version": 1,
        "updated": raw_data.get("updated", "2026-11-21"),
        "spCards": SP_CARDS,
        "characters": codex_chars,
    }
    OUT_JSON.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    make_contact_sheet(qa_sprites, QA_DIR / "qa_sprites_dark.png", (11, 17, 27))
    make_contact_sheet(qa_avatars, QA_DIR / "qa_avatars.png", (17, 23, 34))

    total_bytes = sum(
        p.stat().st_size for p in OUT_CODEX.rglob("*.webp") if p.is_file()
    )
    print(
        f"Generated {len(codex_chars)} characters x 3 variants = {len(qa_sprites)} cards; "
        f"total webp size = {total_bytes / 1024 / 1024:.2f} MB"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
