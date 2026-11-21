import { strFromU8, unzipSync } from 'fflate';
import katex from 'katex';
import { BRAND } from '../brand';
import type {
  ChaptersPayload,
  CharacterUnlockMode,
  CodexCharacter,
  CodexSpCard,
  CourseMeta,
  ExamPaper,
  FormulaItem,
  InstalledWorkshopPack,
  WorkshopCatalogItem,
  WorkshopCharacterPayload,
  WorkshopCoursePayload,
  WorkshopManifest,
  WorkshopPackStats,
  WorkshopPackType,
} from '../types';

const SAFE_PACK_ID_RE = /^[a-z0-9][a-z0-9_-]{2,47}$/;
const SAFE_COURSE_ID_RE = /^[a-z0-9][a-z0-9_-]{1,31}$/;
const VALID_PACK_TYPES = new Set<WorkshopPackType>(['course', 'exam', 'character']);
const MAX_ZIP_BYTES = 60 * 1024 * 1024;
const MAX_UNZIPPED_BYTES = 60 * 1024 * 1024;
const MAX_FILES = 600;
const D1_CHUNK_SIZE = 512 * 1024;
export const MAX_D1_PACK_BYTES = 15 * 1024 * 1024;

const MIME_MAP: Record<string, string> = {
  png: 'image/png',
  jpg: 'image/jpeg',
  jpeg: 'image/jpeg',
  webp: 'image/webp',
  gif: 'image/gif',
  svg: 'image/svg+xml',
};

export interface ParsedWorkshopZip {
  manifest: WorkshopManifest;
  stats: WorkshopPackStats;
  targetCourseId: string;
  unlockMode: CharacterUnlockMode;
  coverRelPath?: string;
  coverDataUrl?: string;
  coursePayload?: WorkshopCoursePayload;
  characterPayload?: WorkshopCharacterPayload;
  blobs: Array<{ relPath: string; mimeType: string; blob: Blob }>;
  sha256: string;
  sizeBytes: number;
}

function normalizeRelPath(raw: string): string {
  return raw
    .replace(/\\/g, '/')
    .replace(/^\.\//, '')
    .replace(/^\/+/, '');
}

function getMimeType(relPath: string): string | null {
  const ext = relPath.split('.').pop()?.toLowerCase() ?? '';
  return MIME_MAP[ext] ?? null;
}

function checkTextAndMath(label: string, text: string | undefined, errors: string[]): void {
  if (!text || errors.length >= 25) return;
  const regex = /\$\$([\s\S]*?)\$\$|\$([^$\n]+?)\$/g;
  let m: RegExpExecArray | null;
  while ((m = regex.exec(text)) !== null) {
    const isDisplay = m[1] !== undefined;
    const tex = (isDisplay ? m[1] : m[2]).trim();
    try {
      katex.renderToString(tex, { displayMode: isDisplay, throwOnError: true, strict: false });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      errors.push(`${label} KaTeX 语法错误 ("${tex.slice(0, 48)}"): ${msg}`);
      if (errors.length >= 25) return;
    }
  }
}

export async function sha256Hex(bytes: Uint8Array): Promise<string> {
  const copy = new Uint8Array(bytes.byteLength);
  copy.set(bytes);
  const digest = await crypto.subtle.digest('SHA-256', copy.buffer);
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, '0')).join('');
}

async function buildCoverDataUrl(blob: Blob): Promise<string | undefined> {
  if (typeof document === 'undefined' || typeof createImageBitmap !== 'function') {
    return undefined;
  }
  try {
    const bitmap = await createImageBitmap(blob);
    const maxDim = 420;
    const scale = Math.min(1, maxDim / Math.max(bitmap.width, bitmap.height));
    const w = Math.max(1, Math.round(bitmap.width * scale));
    const h = Math.max(1, Math.round(bitmap.height * scale));
    const canvas = document.createElement('canvas');
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      bitmap.close();
      return undefined;
    }
    ctx.drawImage(bitmap, 0, 0, w, h);
    bitmap.close();
    const webp = canvas.toDataURL('image/webp', 0.82);
    if (webp.startsWith('data:image/') && webp.length <= 160_000) {
      return webp;
    }
    const jpeg = canvas.toDataURL('image/jpeg', 0.78);
    if (jpeg.startsWith('data:image/') && jpeg.length <= 160_000) {
      return jpeg;
    }
  } catch {
    // ignore thumbnail generation failures
  }
  return undefined;
}

export async function parseAndValidateWorkshopZip(
  rawBytes: Uint8Array
): Promise<{ ok: true; parsed: ParsedWorkshopZip } | { ok: false; errors: string[] }> {
  if (rawBytes.byteLength === 0) {
    return { ok: false, errors: ['文件为空'] };
  }
  if (rawBytes.byteLength > MAX_ZIP_BYTES) {
    return { ok: false, errors: ['资源包体积超过 60MB 上限'] };
  }

  let unzipped: Record<string, Uint8Array>;
  try {
    unzipped = unzipSync(rawBytes);
  } catch (err) {
    return {
      ok: false,
      errors: [`无法解压 ZIP 文件：${err instanceof Error ? err.message : '格式损坏'}`],
    };
  }

  const rawEntries: Array<[string, Uint8Array]> = [];
  let totalUnzipped = 0;
  for (const [entryPath, data] of Object.entries(unzipped)) {
    const clean = entryPath.replace(/\\/g, '/').replace(/^\/+/, '');
    if (
      !clean ||
      clean.endsWith('/') ||
      clean.startsWith('__MACOSX/') ||
      clean.endsWith('/.DS_Store') ||
      clean === '.DS_Store'
    ) {
      continue;
    }
    rawEntries.push([clean, data]);
    totalUnzipped += data.byteLength;
    if (rawEntries.length > MAX_FILES) {
      return { ok: false, errors: [`压缩包内文件数量超过 ${MAX_FILES} 个上限`] };
    }
    if (totalUnzipped > MAX_UNZIPPED_BYTES) {
      return { ok: false, errors: ['解压后总体积超过 60MB 上限'] };
    }
  }

  if (rawEntries.length === 0) {
    return { ok: false, errors: ['压缩包内没有任何文件'] };
  }

  // Auto-strip a single common wrapper directory when manifest.json is nested 1 level deep
  const hasRootManifest = rawEntries.some(([p]) => p === 'manifest.json');
  let wrapperPrefix = '';
  if (!hasRootManifest) {
    const firstSegs = new Set(rawEntries.map(([p]) => p.split('/')[0]));
    if (firstSegs.size === 1) {
      const candidate = `${[...firstSegs][0]}/`;
      if (rawEntries.some(([p]) => p === `${candidate}manifest.json`)) {
        wrapperPrefix = candidate;
      }
    }
  }

  const fileMap = new Map<string, Uint8Array>();
  for (const [origPath, data] of rawEntries) {
    const rel = normalizeRelPath(wrapperPrefix ? origPath.slice(wrapperPrefix.length) : origPath);
    if (!rel || rel.split('/').includes('..')) {
      return { ok: false, errors: [`检测到非法路径：${origPath}`] };
    }
    fileMap.set(rel, data);
  }

  const manifestBytes = fileMap.get('manifest.json');
  if (!manifestBytes) {
    return { ok: false, errors: ['缺少根目录 manifest.json 文件'] };
  }

  let manifestRaw: Record<string, unknown>;
  try {
    manifestRaw = JSON.parse(strFromU8(manifestBytes)) as Record<string, unknown>;
  } catch (err) {
    return {
      ok: false,
      errors: [`manifest.json 解析失败：${err instanceof Error ? err.message : 'JSON 无效'}`],
    };
  }

  const errors: string[] = [];
  if (manifestRaw.schemaVersion !== 1) {
    errors.push('manifest.schemaVersion 必须为 1');
  }
  const packId = typeof manifestRaw.packId === 'string' ? manifestRaw.packId.trim().toLowerCase() : '';
  if (!SAFE_PACK_ID_RE.test(packId)) {
    errors.push('manifest.packId 必须为 3~48 位小写字母、数字、连字符或下划线');
  }
  const packType =
    typeof manifestRaw.type === 'string' ? (manifestRaw.type.trim() as WorkshopPackType) : null;
  if (!packType || !VALID_PACK_TYPES.has(packType)) {
    errors.push('manifest.type 必须为 course、exam 或 character');
  }
  const name = typeof manifestRaw.name === 'string' ? manifestRaw.name.trim() : '';
  const version = typeof manifestRaw.version === 'string' ? manifestRaw.version.trim() : '';
  const author = typeof manifestRaw.author === 'string' ? manifestRaw.author.trim() : '';
  const summary = typeof manifestRaw.summary === 'string' ? manifestRaw.summary.trim() : '';
  const license = typeof manifestRaw.license === 'string' ? manifestRaw.license.trim() : '';

  if (!name) errors.push('manifest.name 不能为空');
  if (!version) errors.push('manifest.version 不能为空');
  if (!author) errors.push('manifest.author 不能为空');
  if (!summary) errors.push('manifest.summary 不能为空');
  if (!license) errors.push('manifest.license（许可与署名说明）不能为空');

  const unlockMode: CharacterUnlockMode =
    manifestRaw.unlockMode === 'gacha' ? 'gacha' : 'direct';

  const manifest: WorkshopManifest = {
    schemaVersion: 1,
    packId,
    type: packType ?? 'course',
    name,
    version,
    author,
    license,
    summary,
    description: typeof manifestRaw.description === 'string' ? manifestRaw.description.trim() : '',
    tags: Array.isArray(manifestRaw.tags)
      ? manifestRaw.tags.filter((t): t is string => typeof t === 'string' && t.trim().length > 0)
      : [],
    cover: typeof manifestRaw.cover === 'string' ? normalizeRelPath(manifestRaw.cover) : undefined,
    targetCourseId:
      typeof manifestRaw.targetCourseId === 'string'
        ? manifestRaw.targetCourseId.trim()
        : undefined,
    unlockMode,
  };

  if (errors.length > 0) {
    return { ok: false, errors };
  }

  // Collect image blobs
  const blobs: Array<{ relPath: string; mimeType: string; blob: Blob }> = [];
  const imageBlobMap = new Map<string, Blob>();
  for (const [relPath, bytes] of fileMap.entries()) {
    const mime = getMimeType(relPath);
    if (!mime) continue;
    const copy = new Uint8Array(bytes.byteLength);
    copy.set(bytes);
    const blob = new Blob([copy.buffer], { type: mime });
    blobs.push({ relPath, mimeType: mime, blob });
    imageBlobMap.set(relPath, blob);
  }

  const coverCandidate =
    manifest.cover ||
    ['cover.webp', 'cover.png', 'cover.jpg', 'assets/cover.webp', 'assets/cover.png'].find((p) =>
      imageBlobMap.has(p)
    );
  let coverDataUrl: string | undefined;
  if (coverCandidate) {
    const coverBlob = imageBlobMap.get(coverCandidate);
    if (coverBlob) {
      coverDataUrl = await buildCoverDataUrl(coverBlob);
    } else if (manifest.cover) {
      errors.push(`manifest.cover 指向的文件不存在：${manifest.cover}`);
    }
  }

  const readJsonFile = <T>(relPath: string, required: boolean): T | undefined => {
    const b = fileMap.get(relPath);
    if (!b) {
      if (required) errors.push(`缺少必要文件：${relPath}`);
      return undefined;
    }
    try {
      return JSON.parse(strFromU8(b)) as T;
    } catch (err) {
      errors.push(`${relPath} JSON 解析失败：${err instanceof Error ? err.message : '格式错误'}`);
      return undefined;
    }
  };

  let targetCourseId = manifest.targetCourseId || '';
  const stats: WorkshopPackStats = {};
  let coursePayload: WorkshopCoursePayload | undefined;
  let characterPayload: WorkshopCharacterPayload | undefined;

  if (manifest.type === 'course' || manifest.type === 'exam') {
    let courseMeta: CourseMeta | undefined;
    if (manifest.type === 'course') {
      const cRaw = readJsonFile<CourseMeta>('course.json', true);
      if (cRaw) {
        const cid = typeof cRaw.id === 'string' ? cRaw.id.trim() : '';
        if (!SAFE_COURSE_ID_RE.test(cid)) {
          errors.push('course.json 中的 id 必须为 2~32 位小写字母、数字或连字符');
        }
        if (!cRaw.name || !cRaw.shortLabel || !cRaw.school || !cRaw.code || !cRaw.subject) {
          errors.push('course.json 缺少 name / shortLabel / school / code / subject 必填字段');
        }
        courseMeta = {
          ...cRaw,
          id: cid,
          status: 'ready',
          sourcePackId: manifest.packId,
        };
        targetCourseId = cid;
      }
    } else {
      if (!targetCourseId || !SAFE_COURSE_ID_RE.test(targetCourseId)) {
        errors.push('单年试卷包（type=exam）必须在 manifest.json 中填写合法的 targetCourseId');
      }
    }

    const chaptersPayload = readJsonFile<ChaptersPayload>(
      'chapters.json',
      manifest.type === 'course'
    );
    const validChapterNums = new Set<number>();
    if (chaptersPayload) {
      if (!Array.isArray(chaptersPayload.chapters) || chaptersPayload.chapters.length === 0) {
        errors.push('chapters.json 中的 chapters 数组不能为空');
      } else {
        for (const ch of chaptersPayload.chapters) {
          if (typeof ch.chapter === 'number') {
            validChapterNums.add(ch.chapter);
          }
        }
      }
    }

    const formulasRaw = readJsonFile<{ formulas?: FormulaItem[] } | FormulaItem[]>(
      'formulas.json',
      false
    );
    const formulas: FormulaItem[] = Array.isArray(formulasRaw)
      ? formulasRaw
      : Array.isArray(formulasRaw?.formulas)
        ? formulasRaw.formulas
        : [];
    for (const fm of formulas) {
      if (validChapterNums.size > 0 && !validChapterNums.has(fm.chapter)) {
        errors.push(`公式 ${fm.id || fm.name} 的 chapter=${fm.chapter} 不在 chapters.json 中`);
      }
      if (fm.latex) {
        try {
          katex.renderToString(fm.latex, { displayMode: true, throwOnError: true, strict: false });
        } catch (err) {
          errors.push(
            `公式 ${fm.id || fm.name} KaTeX 报错：${err instanceof Error ? err.message : String(err)}`
          );
        }
      }
      checkTextAndMath(`公式 ${fm.id}.variables`, fm.variables, errors);
      checkTextAndMath(`公式 ${fm.id}.note`, fm.note, errors);
    }

    const paperPaths = [...fileMap.keys()]
      .filter((p) => /^papers\/[^/]+\.json$/i.test(p))
      .sort();
    if (paperPaths.length === 0) {
      errors.push('papers/ 目录下至少需要包含 1 份试卷 JSON（例如 papers/2024.json）');
    }

    const papers: ExamPaper[] = [];
    let totalQuestions = 0;
    const referencedFigures = new Set<string>();

    for (const pPath of paperPaths) {
      const paper = readJsonFile<ExamPaper>(pPath, true);
      if (!paper) continue;
      if (typeof paper.year !== 'number' || paper.year < 1990 || paper.year > 2100) {
        errors.push(`${pPath}: year 字段无效`);
      }
      if (!Array.isArray(paper.questions) || paper.questions.length === 0) {
        errors.push(`${pPath}: questions 数组不能为空`);
        continue;
      }

      let scoreSum = 0;
      const normalizedQuestions = paper.questions.map((q, idx) => {
        const expectedNo = idx + 1;
        if (q.no !== expectedNo) {
          errors.push(`${pPath}: 第 ${idx + 1} 题的 no 应为 ${expectedNo}（实际为 ${q.no}）`);
        }
        scoreSum += Number(q.score ?? 0);
        if (validChapterNums.size > 0 && !validChapterNums.has(q.chapter)) {
          errors.push(`${pPath} Q${q.no}: chapter=${q.chapter} 不在 chapters.json 定义中`);
        }
        if (Array.isArray(q.rubric) && q.rubric.length > 0) {
          const rSum = q.rubric.reduce((s, r) => s + Number(r.pts ?? 0), 0);
          if (rSum !== q.score) {
            errors.push(`${pPath} Q${q.no}: rubric 采分点总和 ${rSum} != 题分 ${q.score}`);
          }
        }

        const normFigures = (q.figures ?? []).map((f) => {
          const cleanSrc = normalizeRelPath(f.src);
          if (!fileMap.has(cleanSrc)) {
            errors.push(`${pPath} Q${q.no}: 找不到配图 ${cleanSrc}`);
          } else {
            referencedFigures.add(cleanSrc);
          }
          return { ...f, src: cleanSrc };
        });

        const normAnalysisFigures = (q.analysisFigures ?? []).map((f) => {
          const cleanSrc = normalizeRelPath(f.src);
          if (!fileMap.has(cleanSrc)) {
            errors.push(`${pPath} Q${q.no}: 找不到解析配图 ${cleanSrc}`);
          } else {
            referencedFigures.add(cleanSrc);
          }
          return { ...f, src: cleanSrc };
        });

        const qLabel = `${paper.year} Q${q.no}`;
        checkTextAndMath(`${qLabel}.title`, q.title, errors);
        checkTextAndMath(`${qLabel}.stem`, q.stem, errors);
        checkTextAndMath(`${qLabel}.note`, q.note, errors);
        checkTextAndMath(`${qLabel}.shortAnswer`, q.shortAnswer, errors);
        checkTextAndMath(`${qLabel}.answer`, q.answer, errors);
        checkTextAndMath(`${qLabel}.analysis`, q.analysis, errors);
        checkTextAndMath(`${qLabel}.pitfalls`, q.pitfalls, errors);
        for (const opt of q.options ?? []) {
          checkTextAndMath(`${qLabel}.选项${opt.label}`, opt.text, errors);
        }

        const safeCourse = targetCourseId || manifest.packId;
        return {
          ...q,
          id: `${safeCourse}-${paper.year}-${String(q.no).padStart(2, '0')}`,
          figures: normFigures,
          analysisFigures: normAnalysisFigures,
        };
      });

      if (scoreSum !== paper.totalScore) {
        errors.push(`${pPath}: 各题分值总和 ${scoreSum} != totalScore ${paper.totalScore}`);
      }
      for (const note of paper.examNotes ?? []) {
        checkTextAndMath(`${pPath}.examNotes`, note, errors);
      }

      totalQuestions += normalizedQuestions.length;
      papers.push({
        ...paper,
        questions: normalizedQuestions,
      });
    }

    stats.paperCount = papers.length;
    stats.questionCount = totalQuestions;
    stats.figureCount = referencedFigures.size;

    coursePayload = {
      course: courseMeta,
      targetCourseId: targetCourseId || undefined,
      chapters: chaptersPayload,
      formulas: formulas.length > 0 ? formulas : undefined,
      papers,
    };
  } else if (manifest.type === 'character') {
    const chJson = readJsonFile<{
      spCards?: CodexSpCard[];
      characters?: CodexCharacter[];
    }>('characters.json', true);

    if (chJson) {
      const rawSp = Array.isArray(chJson.spCards) ? chJson.spCards : [];
      const rawChars = Array.isArray(chJson.characters) ? chJson.characters : [];
      if (rawSp.length === 0 && rawChars.length === 0) {
        errors.push('characters.json 中 spCards 与 characters 不能同时为空');
      }

      const spCards: CodexSpCard[] = rawSp.map((sp, idx) => {
        const sid = typeof sp.id === 'string' ? sp.id.trim() : '';
        if (!sid || sid === 'sp:dafeyu' || sid === 'sp:gemini') {
          errors.push(`characters.json spCards[${idx}] 的 id 非法或与内置看板娘冲突：${sid}`);
        }
        const sprite = normalizeRelPath(sp.sprite ?? '');
        const avatar = normalizeRelPath(sp.avatar ?? sprite);
        if (!sprite || !imageBlobMap.has(sprite)) {
          errors.push(`SP 角色 ${sp.name || sid} 缺少立绘文件：${sprite}`);
        }
        if (!avatar || !imageBlobMap.has(avatar)) {
          errors.push(`SP 角色 ${sp.name || sid} 缺少头像文件：${avatar}`);
        }
        let poses: CodexSpCard['poses'];
        if (sp.poses && typeof sp.poses === 'object') {
          poses = {};
          for (const poseKey of ['hero', 'study', 'think', 'cheer'] as const) {
            const pVal = sp.poses[poseKey];
            if (pVal) {
              const norm = normalizeRelPath(pVal);
              if (!imageBlobMap.has(norm)) {
                errors.push(`SP 角色 ${sp.name || sid} 缺少姿态图 (${poseKey}): ${norm}`);
              } else {
                poses[poseKey] = norm;
              }
            }
          }
        }
        return {
          ...sp,
          id: sid.startsWith('sp:') ? sid : `sp:${manifest.packId}-${sid}`,
          rarity: 'SP',
          sprite,
          avatar,
          poses,
          sourcePackId: manifest.packId,
        };
      });

      const characters: CodexCharacter[] = rawChars.map((ch, idx) => {
        const cid = typeof ch.id === 'string' ? ch.id.trim() : '';
        if (!cid) {
          errors.push(`characters.json characters[${idx}] 缺少 id`);
        }
        const normVariants = { ...ch.variants };
        for (const variantKey of ['chibi', 'medium', 'standard'] as const) {
          const v = ch.variants?.[variantKey];
          if (!v) {
            errors.push(`角色 ${ch.name || cid} 缺少 ${variantKey} 形态配置`);
            continue;
          }
          const sprite = normalizeRelPath(v.sprite ?? '');
          const avatar = normalizeRelPath(v.avatar ?? sprite);
          const sheet = normalizeRelPath(v.sheet ?? sprite);
          if (!sprite || !imageBlobMap.has(sprite)) {
            errors.push(`角色 ${ch.name || cid} (${variantKey}) 缺少立绘：${sprite}`);
          }
          if (!avatar || !imageBlobMap.has(avatar)) {
            errors.push(`角色 ${ch.name || cid} (${variantKey}) 缺少头像：${avatar}`);
          }
          if (v.sheet && !imageBlobMap.has(sheet)) {
            errors.push(`角色 ${ch.name || cid} (${variantKey}) 缺少设定图：${sheet}`);
          }
          normVariants[variantKey] = {
            ...v,
            cardId: v.cardId || `${cid}:${variantKey}`,
            sprite,
            avatar,
            sheet,
          };
        }

        return {
          ...ch,
          id: cid,
          variants: normVariants,
          sourcePackId: manifest.packId,
          unlockMode,
        };
      });

      stats.spCardCount = spCards.length;
      stats.characterCount = characters.length;

      characterPayload = {
        unlockMode,
        spCards,
        characters,
      };
    }
  }

  if (errors.length > 0) {
    return { ok: false, errors };
  }

  const sha256 = await sha256Hex(rawBytes);

  return {
    ok: true,
    parsed: {
      manifest,
      stats,
      targetCourseId,
      unlockMode,
      coverRelPath: coverCandidate,
      coverDataUrl,
      coursePayload,
      characterPayload,
      blobs,
      sha256,
      sizeBytes: rawBytes.byteLength,
    },
  };
}

export function buildInstalledPackRecord(
  parsed: ParsedWorkshopZip,
  source: 'workshop' | 'local'
): InstalledWorkshopPack {
  return {
    packId: parsed.manifest.packId,
    manifest: parsed.manifest,
    enabled: true,
    source,
    installedAt: new Date().toISOString(),
    sizeBytes: parsed.sizeBytes,
    stats: parsed.stats,
    coverRelPath: parsed.coverRelPath,
    coursePayload: parsed.coursePayload,
    characterPayload: parsed.characterPayload,
  };
}

export function formatPackSize(bytes: number): string {
  if (!bytes || bytes <= 0) return '未知大小';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

// ============================================================================
// Workshop Catalog & Admin API Client
// ============================================================================

export async function fetchWorkshopCatalog(
  type?: WorkshopPackType
): Promise<{ packs: WorkshopCatalogItem[]; online: boolean }> {
  const apiBase = BRAND.workshopApiUrl;
  if (apiBase) {
    try {
      const url = type ? `${apiBase}/packs?type=${encodeURIComponent(type)}` : `${apiBase}/packs`;
      const res = await fetch(url, { cache: 'no-store' });
      const contentType = res.headers.get('content-type') ?? '';
      if (res.ok && contentType.includes('application/json')) {
        const data = await res.json();
        if (Array.isArray(data?.packs)) {
          return { packs: data.packs as WorkshopCatalogItem[], online: true };
        }
      }
    } catch {
      // fall back to static json
    }
  }

  try {
    const res = await fetch('./data/workshop.json');
    if (res.ok) {
      const data = await res.json();
      const all = Array.isArray(data?.packs) ? (data.packs as WorkshopCatalogItem[]) : [];
      const filtered = type ? all.filter((p) => p.type === type) : all;
      return { packs: filtered, online: false };
    }
  } catch {
    // ignore
  }
  return { packs: [], online: false };
}

export async function downloadWorkshopPackBytes(
  pack: WorkshopCatalogItem,
  onProgress?: (received: number, total: number) => void
): Promise<{ ok: true; bytes: Uint8Array } | { ok: false; error: string }> {
  const downloadUrl = `${BRAND.workshopApiUrl}/packs/${encodeURIComponent(pack.packId)}/download`;
  try {
    const res = await fetch(downloadUrl);
    if (!res.ok) {
      const errJson = await res.json().catch(() => null);
      return {
        ok: false,
        error: errJson?.error || `下载失败（HTTP ${res.status}）`,
      };
    }

    const headerTotal = Number(res.headers.get('Content-Length') ?? pack.sizeBytes ?? 0);
    if (!res.body) {
      const buf = new Uint8Array(await res.arrayBuffer());
      onProgress?.(buf.byteLength, buf.byteLength);
      return { ok: true, bytes: buf };
    }

    const reader = res.body.getReader();
    const chunks: Uint8Array[] = [];
    let received = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (!value) continue;
      chunks.push(value);
      received += value.byteLength;
      onProgress?.(received, headerTotal);
    }

    const merged = new Uint8Array(received);
    let offset = 0;
    for (const chunk of chunks) {
      merged.set(chunk, offset);
      offset += chunk.byteLength;
    }
    return { ok: true, bytes: merged };
  } catch {
    if (pack.storageMode === 'url' && pack.externalUrl) {
      return {
        ok: false,
        error: '外部链接受跨域（CORS）限制无法直接由浏览器拉取，请点击「下载 .zip」后使用「从本地导入」。',
      };
    }
    return { ok: false, error: '下载资源包时网络中断，请稍后重试。' };
  }
}

function getWorkshopAdminBase(): string {
  return BRAND.workshopApiUrl.replace(/\/workshop\/?$/, '/admin/workshop/packs');
}

async function workshopAdminJson<T>(
  path: string,
  token: string,
  init: RequestInit = {}
): Promise<({ ok: true } & T) | { ok: false; status: number; error: string }> {
  try {
    const headers = new Headers(init.headers);
    headers.set('Authorization', `Bearer ${token}`);
    if (init.body && typeof init.body === 'string' && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }
    const res = await fetch(path, { ...init, headers, cache: 'no-store' });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      return {
        ok: false,
        status: res.status,
        error: data?.error || `请求失败（HTTP ${res.status}）`,
      };
    }
    return { ok: true, ...(data as T) };
  } catch {
    return { ok: false, status: 0, error: '无法连接工坊管理接口，请检查网络。' };
  }
}

export async function fetchAdminWorkshopPacks(
  token: string
): Promise<
  { ok: true; packs: WorkshopCatalogItem[] } | { ok: false; status: number; error: string }
> {
  return workshopAdminJson<{ packs: WorkshopCatalogItem[] }>(getWorkshopAdminBase(), token, {
    method: 'GET',
  });
}

export async function uploadAdminWorkshopPack(
  token: string,
  fileBytes: Uint8Array,
  fileName: string,
  parsed: ParsedWorkshopZip,
  options: {
    featured: boolean;
    unlockMode: CharacterUnlockMode;
    description?: string;
  },
  onProgress?: (percent: number, label: string) => void
): Promise<{ ok: true; pack: WorkshopCatalogItem } | { ok: false; status: number; error: string }> {
  if (fileBytes.byteLength > MAX_D1_PACK_BYTES) {
    return {
      ok: false,
      status: 400,
      error: '资源包超过 15MB D1 直传上限，请改用「外链 URL 登记」。',
    };
  }

  const totalChunks = Math.ceil(fileBytes.byteLength / D1_CHUNK_SIZE);
  const base = getWorkshopAdminBase();
  onProgress?.(5, '正在注册资源包元信息…');

  const initRes = await workshopAdminJson<{ pack: WorkshopCatalogItem }>(base, token, {
    method: 'POST',
    body: JSON.stringify({
      packId: parsed.manifest.packId,
      type: parsed.manifest.type,
      name: parsed.manifest.name,
      version: parsed.manifest.version,
      author: parsed.manifest.author,
      summary: parsed.manifest.summary,
      description: options.description ?? parsed.manifest.description ?? '',
      license: parsed.manifest.license,
      tags: parsed.manifest.tags ?? [],
      targetCourseId: parsed.targetCourseId,
      unlockMode: options.unlockMode,
      storageMode: 'd1',
      fileName,
      sizeBytes: fileBytes.byteLength,
      chunkCount: totalChunks,
      sha256: parsed.sha256,
      coverDataUrl: parsed.coverDataUrl ?? '',
      stats: parsed.stats,
      featured: options.featured,
    }),
  });
  if (!initRes.ok) return initRes;

  for (let i = 0; i < totalChunks; i++) {
    const start = i * D1_CHUNK_SIZE;
    const end = Math.min(fileBytes.byteLength, start + D1_CHUNK_SIZE);
    const slice = fileBytes.slice(start, end);
    const pct = 10 + Math.round(((i + 1) / totalChunks) * 80);
    onProgress?.(pct, `正在上传分片 ${i + 1} / ${totalChunks}…`);

    const chunkRes = await workshopAdminJson<{ ok: boolean }>(
      `${base}/${encodeURIComponent(parsed.manifest.packId)}/chunks/${i}`,
      token,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/octet-stream' },
        body: slice,
      }
    );
    if (!chunkRes.ok) return chunkRes;
  }

  onProgress?.(95, '正在校验分片完整性并上线…');
  const finRes = await workshopAdminJson<{ pack: WorkshopCatalogItem }>(
    `${base}/${encodeURIComponent(parsed.manifest.packId)}/finalize`,
    token,
    { method: 'POST' }
  );
  if (!finRes.ok) return finRes;

  onProgress?.(100, '上传完成并已发布到创意工坊！');
  return { ok: true, pack: finRes.pack };
}

export async function registerExternalWorkshopPack(
  token: string,
  payload: {
    packId: string;
    type: WorkshopPackType;
    name: string;
    version: string;
    author: string;
    summary: string;
    description?: string;
    license: string;
    tags?: string[];
    targetCourseId?: string;
    unlockMode: CharacterUnlockMode;
    externalUrl: string;
    sizeBytes?: number;
    featured: boolean;
  }
): Promise<{ ok: true; pack: WorkshopCatalogItem } | { ok: false; status: number; error: string }> {
  return workshopAdminJson<{ pack: WorkshopCatalogItem }>(getWorkshopAdminBase(), token, {
    method: 'POST',
    body: JSON.stringify({
      ...payload,
      storageMode: 'url',
      fileName: `${payload.packId}.jypack.zip`,
      published: true,
    }),
  });
}

export async function patchAdminWorkshopPack(
  token: string,
  packId: string,
  patch: {
    name?: string;
    summary?: string;
    description?: string;
    license?: string;
    tags?: string[];
    externalUrl?: string;
    featured?: boolean;
    published?: boolean;
    unlockMode?: CharacterUnlockMode;
  }
): Promise<{ ok: true; pack: WorkshopCatalogItem } | { ok: false; status: number; error: string }> {
  return workshopAdminJson<{ pack: WorkshopCatalogItem }>(
    `${getWorkshopAdminBase()}/${encodeURIComponent(packId)}`,
    token,
    {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }
  );
}

export async function deleteAdminWorkshopPack(
  token: string,
  packId: string
): Promise<{ ok: true; deletedId: string } | { ok: false; status: number; error: string }> {
  return workshopAdminJson<{ deletedId: string }>(
    `${getWorkshopAdminBase()}/${encodeURIComponent(packId)}`,
    token,
    { method: 'DELETE' }
  );
}
