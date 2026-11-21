import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Check,
  Copy,
  FileText,
  Heart,
  Info,
  Mail,
  Maximize2,
  MessageSquare,
  Scale,
  ShieldCheck,
  Sparkles,
  Users,
  X,
} from 'lucide-react';
import { BRAND } from '../brand';
import { Mascot, type MascotPose } from '../components/Mascot';
import { useData } from '../context/DataContext';
import { copyText } from '../utils/clipboard';
import { scrollToElement } from '../utils/scroll';

const FISH_POSES: Array<{ pose: MascotPose; label: string; caption: string }> = [
  { pose: 'hero', label: '欢迎', caption: '大肥鱼 · 元气迎接看板娘' },
  { pose: 'study', label: '刷题', caption: '大肥鱼 · 专注啃真题状态' },
  { pose: 'think', label: '沉思', caption: '大肥鱼 · 排查易错点提示' },
  { pose: 'cheer', label: '欢呼', caption: '大肥鱼 · 模考满分庆功姿' },
];

interface CodexZoomTarget {
  src: string;
  title: string;
  subtitle: string;
}

export const AboutPage: React.FC = () => {
  const { courses, currentCourse } = useData();
  const [searchParams] = useSearchParams();
  const [fishPose, setFishPose] = useState<MascotPose>('hero');
  const [zoomTarget, setZoomTarget] = useState<CodexZoomTarget | null>(null);
  const [copiedKey, setCopiedKey] = useState<'qq' | 'email' | null>(null);

  const courseNames = courses.map((c) => c.name).join('、') || currentCourse.name;
  const schools = Array.from(new Set(courses.map((c) => c.school))).join('、') || currentCourse.school;

  useEffect(() => {
    if (searchParams.get('section') === 'codex') {
      scrollToElement('character-codex', 76);
    }
  }, [searchParams]);

  useEffect(() => {
    if (!zoomTarget) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setZoomTarget(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [zoomTarget]);

  const handleCopy = async (key: 'qq' | 'email', text: string) => {
    const ok = await copyText(text);
    if (ok) {
      setCopiedKey(key);
      window.setTimeout(() => setCopiedKey((prev) => (prev === key ? null : prev)), 2200);
    }
  };

  const activeFishMeta = FISH_POSES.find((p) => p.pose === fishPose) ?? FISH_POSES[0];

  return (
    <div className="page-container">
      <div className="page-header-card about-hero">
        <Mascot pose="study" size={146} />
        <div>
          <div className="page-kicker">ARCHIVE // COMPLIANCE & CREDITS</div>
          <h1 className="page-title">
            <Info size={22} className="text-sky" /> 关于{BRAND.name}、鸣谢与角色图鉴
          </h1>
          <p className="page-desc">
            {BRAND.name}是一个面向考研专业课复习（现已支持 {courseNames}）的<strong>非官方、非营利</strong>个人学习工具，
            与{schools}及任何考研机构、商业刷题平台均无隶属或合作关系。
          </p>
          <div className="contact-pills-row">
            <a href={`mailto:${BRAND.contact}`} className="copy-pill">
              <Mail size={14} />
              <span>联系邮箱：{BRAND.contact}</span>
            </a>
            <button
              type="button"
              className={`copy-pill ${copiedKey === 'email' ? 'copied' : ''}`}
              onClick={() => handleCopy('email', BRAND.contact)}
            >
              {copiedKey === 'email' ? <Check size={13} /> : <Copy size={13} />}
              <span>{copiedKey === 'email' ? '已复制邮箱' : '复制邮箱'}</span>
            </button>
            <button
              type="button"
              className={`copy-pill ${copiedKey === 'qq' ? 'copied' : ''}`}
              onClick={() => handleCopy('qq', BRAND.qqGroup)}
            >
              <Users size={14} />
              <span>QQ 交流群：{BRAND.qqGroup}</span>
              {copiedKey === 'qq' ? <Check size={13} /> : <Copy size={13} />}
              <span className="copy-pill-hint">{copiedKey === 'qq' ? 'COPIED' : 'COPY'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Special Acknowledgements & Operator Dossier Character Codex */}
      <section id="character-codex" className="card-panel codex-section">
        <div className="codex-head">
          <div>
            <div className="page-kicker">OPERATOR DOSSIER // CHARACTER CODEX</div>
            <h2 className="panel-title">
              <Sparkles size={19} className="text-yellow" /> 角色图鉴与特别鸣谢
            </h2>
            <p className="codex-subtitle">
              感谢以下创作者与 AI 伙伴对本站题库整理、工程配图重绘与前端研发的支持 —— 点击立绘可放大查看高清角色形象。
            </p>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            <Link to="/companion?tab=codex" className="btn btn-tactical btn-sm">
              <Sparkles size={14} /> 进入完整 14 角色图鉴与补给站 →
            </Link>
            <Link to="/board" className="btn btn-secondary btn-sm">
              <MessageSquare size={14} /> 前往公告与留言板
            </Link>
          </div>
        </div>

        <div className="codex-grid">
          {/* Gemini Acknowledgement Dossier Card */}
          <article className="codex-card gemini-card">
            <span className="codex-dossier-wm" aria-hidden="true">GMN</span>
            <button
              type="button"
              className="codex-portrait-stage ak-brackets"
              onClick={() =>
                setZoomTarget({
                  src: './mascot/gemini.webp',
                  title: 'Gemini · AI 联合协研伙伴',
                  subtitle: '特别鸣谢 Gemini —— 助力真题精解、KaTeX 公式核验、手绘原图重置与站点共创',
                })
              }
              title="点击放大查看 Gemini 角色形象"
            >
              <img src="./mascot/gemini.webp" alt="Gemini 拟人角色形象" className="codex-portrait-img" />
              <span className="codex-zoom-chip">
                <Maximize2 size={11} /> ZOOM
              </span>
            </button>

            <div className="codex-info">
              <div className="codex-title-row">
                <span className="codex-badge gemini">PARTNER // AI 伙伴</span>
                <h3 className="codex-name">Gemini</h3>
              </div>
              <p className="codex-role">Google Gemini · 真题精解协研与站点共创角色</p>
              <div className="codex-tags">
                <span>31 套真题精解协研</span>
                <span>KaTeX 推导核验</span>
                <span>47 幅原题图清晰重置</span>
                <span>前端交互共创</span>
              </div>
              <p className="codex-bio">
                特别鸣谢 <strong>Gemini</strong> 深度参与河海大学 814 与扬州大学 849 共 31 套考研水力学真题的结构化梳理、
                公式推导与采分点校验，并协助完成了 47 幅手绘与去水印原题图的清晰重绘与本站核心学习功能的开发打磨。
              </p>
              <p className="codex-credit">
                角色形象为本站通过 AI 自行生成的非商业致谢插图（非 Google 官方吉祥物，亦不主张上游 CC
                授权）；如涉任何第三方权益争议，请联系站长于 48 小时内删除或替换。
              </p>
            </div>
          </article>

          {/* 大肥鱼 Mascot Dossier Card */}
          <article className="codex-card fish-card">
            <span className="codex-dossier-wm" aria-hidden="true">DF-01</span>
            <button
              type="button"
              className="codex-portrait-stage ak-brackets"
              onClick={() =>
                setZoomTarget({
                  src: `./mascot/${fishPose}.webp`,
                  title: `${BRAND.mascotName}（${activeFishMeta.label}姿态）`,
                  subtitle: activeFishMeta.caption,
                })
              }
              title="点击放大查看大肥鱼角色形象"
            >
              <img
                src={`./mascot/${fishPose}.webp`}
                alt={`${BRAND.mascotName}（${activeFishMeta.label}姿态）`}
                className="codex-portrait-img"
              />
              <span className="codex-zoom-chip">
                <Maximize2 size={11} /> ZOOM
              </span>
            </button>

            <div className="codex-info">
              <div className="codex-title-row">
                <span className="codex-badge fish">UNIT DF-01 // 看板娘</span>
                <h3 className="codex-name">{BRAND.mascotName}（鲸鱼娘）</h3>
              </div>
              <p className="codex-role">DeepSeek 拟人同人形象（原型「溟月」）· 全程陪读陪伴</p>
              <div className="codex-pose-tabs" role="tablist" aria-label="切换大肥鱼立绘姿态">
                {FISH_POSES.map((item) => (
                  <button
                    key={item.pose}
                    type="button"
                    role="tab"
                    aria-selected={fishPose === item.pose}
                    className={`codex-pose-btn ${fishPose === item.pose ? 'active' : ''}`}
                    onClick={() => setFishPose(item.pose)}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
              <p className="codex-bio">
                陪伴研友从首页刷题、易错点提示一路走到全真模考庆功的小鲸看板娘。刷累了记得休息喝水，错题本清零后大肥鱼会给你欢呼打气！
              </p>
              <p className="codex-credit">
                原创角色原型为「上善无形」创作的「溟月」，深蓝女仆装二创设定源自「ZipZipPipe」（公开声明见{' '}
                <a
                  href="https://t.bilibili.com/1231980045693616162"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-contact-link"
                >
                  B站动态声明
                </a>
                与{' '}
                <a
                  href="https://www.bilibili.com/video/BV1tE9XBbErS/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-contact-link"
                >
                  BV1tE9XBbErS
                </a>
                ）。本站四姿态 Q 版透明立绘系基于上述公开设定经 AI 重绘与透明抠图衍生，仅立绘衍生图片部分继续遵循{' '}
                <a
                  href="https://creativecommons.org/licenses/by-nc-sa/4.0/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-contact-link"
                >
                  CC BY-NC-SA 4.0
                </a>{' '}
                非商业相同方式共享。
              </p>
            </div>
          </article>
        </div>
      </section>

      <div className="about-grid">
        <section className="card-panel about-card">
          <h3 className="panel-title">
            <ShieldCheck size={18} className="text-emerald" /> 非官方声明
          </h3>
          <ul className="about-list">
            <li>本站不是{schools}官方网站，不代表相关高校研究生院立场，也未使用其校徽、标识等官方标志。</li>
            <li>板块名称与科目代码（当前：{currentCourse.name}）仅用于说明复习内容所对应的考试科目（指示性使用）。</li>
            <li>考试科目、参考书目、分值结构等信息以各招生院校研究生院当年发布的官方文件为准。</li>
          </ul>
        </section>

        <section className="card-panel about-card">
          <h3 className="panel-title">
            <FileText size={18} className="text-sky" /> 内容来源说明
          </h3>
          <ul className="about-list">
            <li>真题题干依据考生公开回忆整理并重新表述，可能与原卷存在出入，请以官方试卷为准。</li>
            <li>参考答案、详细解析、易错提示、步骤采分点由站长借助 Gemini 等 AI 工具生成并整理，<strong>仅供学习参考</strong>，不保证完全正确；如发现错误欢迎反馈。</li>
            <li>采分点为本站自拟的复习参考，不代表官方阅卷评分标准。</li>
            <li>章节考察规律为本站依据历年真题统计归纳，属于经验总结，非官方考纲。</li>
            <li>公式手册所列水力学公式属于公有领域的科学知识，说明文字由本站独立编写。</li>
          </ul>
        </section>

        <section className="card-panel about-card">
          <h3 className="panel-title">
            <Heart size={18} className="text-coral" /> 看板娘形象与署名
          </h3>
          <ul className="about-list">
            <li>
              本站看板娘采用中文互联网社区流行的 DeepSeek 拟人形象“鲸鱼娘 / 蓝色大肥鱼”的 Q 版二创绘示，
              <strong>非本站原创</strong>。据公开资料，上游原型「溟月」作者为「上善无形」，女仆装二创作者「ZipZipPipe」在{' '}
              <a
                href="https://t.bilibili.com/1231980045693616162"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-contact-link"
              >
                B站公开动态
              </a>
              及作品{' '}
              <a
                href="https://www.bilibili.com/video/BV1tE9XBbErS/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-contact-link"
              >
                BV1tE9XBbErS
              </a>{' '}
              中声明其二创独创部分以{' '}
              <a
                href="https://creativecommons.org/licenses/by-nc-sa/4.0/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-contact-link"
              >
                CC BY-NC-SA 4.0
              </a>{' '}
              非商业协议授权。本站对其进行了 AI 四姿态 Q 版重绘与透明抠图修改，该协议及相同方式共享（SA）条款仅适用于上述立绘衍生图片本身，不涉及本站代码与题库数据。
            </li>
            <li>
              角色图鉴中特别鸣谢角色「Gemini」为本站通过 AI 自行生成的非商业致谢插图，不主张官方关联，亦不主张上游 CC 授权。
            </li>
            <li>
              补给站角色图鉴收录的 14 位 AI 拟人角色设定图与社区资料整理自{' '}
              <a
                href="https://github.com/HABAI182/ai-girls-atlas"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-contact-link"
              >
                HABAI182 / AI Girls Atlas
              </a>{' '}
              开源资料库项目（配套离线展览企划 <strong>AI MUSE / AI_2Dgirls_Gallery</strong>）：其中社区研究说明与来源核验文字遵循{' '}
              <a
                href="https://creativecommons.org/licenses/by/4.0/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-contact-link"
              >
                CC BY 4.0
              </a>{' '}
              署名（本站补充了考研水力学陪读台词与交互展示）；42 张多视图设定板系项目维护者参考「Creeper-北极之光」提供的初始形象图经 AI 生成，本站对其进行了单视角裁切、背景透明抠图与 WebP 压缩适配，<strong>不对上述图片主张统一的 CC 或商业使用许可</strong>；同时保留「上善无形」「ZipZipPipe」「这个刀子真甜」等社区创作者的逐条来源与各自许可边界（例如鲸鱼娘女仆设定的 CC BY-NC-SA 4.0 声明仅适用于其声明范围，不扩大到其他角色）。所有形象仅限本站非商业个人考研陪伴展示，不代表对应 AI 厂商官方设定。
            </li>
            <li>如原作者或相关权利人不同意本站使用，请通过下方联系方式告知，站长将在 <strong>48 小时内</strong>核实并替换或删除。</li>
            <li>站名“{BRAND.name}”、矢量小胖鲸标志、网站代码与界面为本站独立设计开发。</li>
          </ul>
        </section>

        <section className="card-panel about-card">
          <h3 className="panel-title">
            <Scale size={18} className="text-purple" /> 开源组件与 AI 鸣谢
          </h3>
          <ul className="about-list">
            <li>特别鸣谢 Google <strong>Gemini</strong> 协助真题梳理、配图重置与页面开发。</li>
            <li>
              <a
                href="https://github.com/HABAI182/ai-girls-atlas"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-contact-link"
              >
                HABAI182 / AI Girls Atlas
              </a>
              （AI 娘形象与二创资料库：研究说明 CC BY 4.0，脚本 MIT；第三方图像沿用逐文件来源与许可边界）
            </li>
            <li>React、React Router（MIT License）</li>
            <li>KaTeX 数学公式渲染（MIT License，字体 SIL OFL 1.1）</li>
            <li>Rajdhani & JetBrains Mono 开源英数展示字体（SIL OFL 1.1）</li>
            <li>Lucide 图标（ISC License）、Vite 构建工具（MIT License）</li>
          </ul>
        </section>
      </div>

      <section className="card-panel about-card notice-card">
        <h3 className="panel-title">
          <Mail size={18} className="text-yellow" /> 联系方式、考研交流群与权利通知
        </h3>
        <p className="about-text">
          真题勘误、新科目许愿或版权/权益通知，请发送邮件至{' '}
          <a href={`mailto:${BRAND.contact}`} className="inline-contact-link">
            <strong>{BRAND.contact}</strong>
          </a>
          ；备考经验交流与研友互助欢迎加入 QQ 群 <strong>{BRAND.qqGroup}</strong>。站长收到有效权利通知后，将在 <strong>48 小时内</strong>核实并完成下架、删除或替换处理。
        </p>
        <p className="about-text muted">
          学习进度、错题、笔记与本地留言等数据只保存在你自己的浏览器本地（localStorage），本站不收集、不上传任何个人信息。
        </p>
        <div className="about-actions-row">
          <Link to="/" className="btn btn-tactical btn-sm">
            返回首页
          </Link>
          <Link to="/board" className="btn btn-secondary btn-sm">
            <MessageSquare size={14} /> 前往公告与留言板
          </Link>
          <Link to="/companion" className="btn btn-secondary btn-sm">
            <Sparkles size={14} /> 小鱼干补给站
          </Link>
        </div>
      </section>

      {zoomTarget && (
        <div className="lightbox-backdrop" onClick={() => setZoomTarget(null)}>
          <div className="lightbox-content codex-lightbox" onClick={(e) => e.stopPropagation()}>
            <div className="lightbox-toolbar">
              <span className="hud-code">CHARACTER ARCHIVE // {zoomTarget.title}</span>
              <button
                type="button"
                className="lightbox-close"
                onClick={() => setZoomTarget(null)}
                aria-label="关闭大图"
              >
                <X size={18} />
              </button>
            </div>
            <img src={zoomTarget.src} alt={zoomTarget.title} />
            <div className="lightbox-caption">
              <strong>{zoomTarget.title}</strong>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: 2 }}>
                {zoomTarget.subtitle}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
