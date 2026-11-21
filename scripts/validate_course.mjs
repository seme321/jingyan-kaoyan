#!/usr/bin/env node
/**
 * Validate one or all courses in `web/public/data/courses.json`, or standalone archival exam packs:
 * - Schema, contiguous `no`, `sections` range & score integrity, and chapter ID integrity
 * - Strict 8-type QuestionType & type-specific invariants (`judgeAnswer`, `options`/`choiceAnswer`, `rubric.label`)
 * - Score sum & rubric sum consistency
 * - Figure file existence on disk
 * - Real KaTeX compilation (`throwOnError: true`) on every math block (including rubric labels)
 * - Anti-infringement / third-party reference keyword check
 *
 * Usage:
 *   node scripts/validate_course.mjs
 *   node scripts/validate_course.mjs --course yzu-849
 *   node scripts/validate_course.mjs --course hhu-814 --pack "河海大学已整理数据/2012/2012.json"
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const DATA_ROOT = path.join(ROOT, 'web', 'public', 'data');
const katexPath = pathToFileURL(
  path.join(ROOT, 'web', 'node_modules', 'katex', 'dist', 'katex.mjs')
).href;
const { default: katex } = await import(katexPath);

const args = process.argv.slice(2);
let targetCourseId = null;
const packFiles = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--course' && i + 1 < args.length) {
    targetCourseId = args[++i];
  } else if (args[i] === '--pack') {
    while (i + 1 < args.length && !args[i + 1].startsWith('--')) {
      packFiles.push(args[++i]);
    }
  }
}

if (packFiles.length > 0 && !targetCourseId) {
  console.error('Usage error: --pack requires --course <courseId> so chapters.json can be verified.');
  process.exit(1);
}

const VALID_TYPES = new Set([
  'judge',
  'single_choice',
  'multi_choice',
  'fill',
  'term',
  'short',
  'calc',
  'proof',
]);
const BANNED_WORDS = ['视频讲解', '原视频', 'BV1', 'B 站', 'B站', '凤鸣', '阿玉', '数砖', '去水印'];

let mathChecked = 0;
let errors = 0;

function fail(msg) {
  errors++;
  console.error(`  [ERROR] ${msg}`);
}

function checkTextAndMath(label, text) {
  if (!text) return;
  for (const w of BANNED_WORDS) {
    if (text.includes(w)) {
      fail(`${label}: contains banned word "${w}"`);
    }
  }
  const regex = /\$\$([\s\S]*?)\$\$|\$([^$\n]+?)\$/g;
  let m;
  while ((m = regex.exec(text)) !== null) {
    const isDisplay = m[1] !== undefined;
    const tex = (isDisplay ? m[1] : m[2]).trim();
    mathChecked++;
    try {
      katex.renderToString(tex, { displayMode: isDisplay, throwOnError: true, strict: false });
    } catch (err) {
      fail(`${label} KaTeX error in "${tex}": ${err.message}`);
    }
  }
}

function validatePaper(paper, labelPrefix, baseDir, validChapterNums, expectedQuestionCount = null) {
  const qs = paper.questions ?? [];
  if (qs.length === 0) {
    fail(`${labelPrefix}: questions array is empty`);
    return 0;
  }
  if (expectedQuestionCount !== null && qs.length !== expectedQuestionCount) {
    fail(`${labelPrefix}: index questionCount=${expectedQuestionCount} != actual ${qs.length}`);
  }

  // Sections continuity & total score check
  const sections = paper.sections ?? [];
  if (sections.length > 0) {
    let expectedStart = 1;
    let secScoreSum = 0;
    for (const sec of sections) {
      const rng = sec.range;
      if (!Array.isArray(rng) || rng.length !== 2 || rng[0] !== expectedStart || rng[1] < rng[0]) {
        fail(
          `${labelPrefix} section "${sec.id}": invalid range ${JSON.stringify(rng)}, expected start ${expectedStart}`
        );
      } else {
        expectedStart = rng[1] + 1;
      }
      secScoreSum += Number(sec.totalScore ?? 0);
    }
    if (expectedStart - 1 !== qs.length) {
      fail(`${labelPrefix}: sections cover up to ${expectedStart - 1} != questions.length ${qs.length}`);
    }
    if (secScoreSum !== paper.totalScore) {
      fail(`${labelPrefix}: sum(sections.totalScore)=${secScoreSum} != totalScore ${paper.totalScore}`);
    }
  }

  let scoreSum = 0;
  for (let idx = 0; idx < qs.length; idx++) {
    const q = qs[idx];
    const qLabel = q.id || `${labelPrefix}-Q${idx + 1}`;
    if (q.no !== idx + 1) {
      fail(`${qLabel}: q.no=${q.no} expected ${idx + 1}`);
    }
    if (!VALID_TYPES.has(q.type)) {
      fail(`${qLabel}: invalid type "${q.type}"`);
    }
    if (typeof q.score !== 'number' || q.score <= 0) {
      fail(`${qLabel}: invalid score ${q.score}`);
    }
    scoreSum += q.score;

    if (!validChapterNums.has(q.chapter)) {
      fail(`${qLabel}: chapter ${q.chapter} does not exist in chapters.json`);
    }

    if (q.type === 'judge') {
      if (typeof q.judgeAnswer !== 'boolean') {
        fail(`${qLabel}: judge question requires boolean judgeAnswer`);
      }
    } else if (q.type === 'single_choice' || q.type === 'multi_choice') {
      if (!Array.isArray(q.options) || q.options.length < 2) {
        fail(`${qLabel}: ${q.type} requires at least 2 options`);
      }
      if (typeof q.choiceAnswer !== 'string' || !q.choiceAnswer.trim()) {
        fail(`${qLabel}: ${q.type} requires non-empty choiceAnswer`);
      }
      if (q.judgeAnswer !== null) {
        fail(`${qLabel}: ${q.type} requires judgeAnswer === null`);
      }
    } else if (q.judgeAnswer !== null) {
      fail(`${qLabel}: non-judge type "${q.type}" requires judgeAnswer === null`);
    }

    if (['short', 'calc', 'proof'].includes(q.type) && q.score >= 5) {
      if (!Array.isArray(q.rubric) || q.rubric.length === 0) {
        fail(`${qLabel}: ${q.type} question with score=${q.score} >= 5 requires non-empty rubric`);
      }
    }

    if (Array.isArray(q.rubric) && q.rubric.length > 0) {
      let rSum = 0;
      for (let rIdx = 0; rIdx < q.rubric.length; rIdx++) {
        const r = q.rubric[rIdx];
        if (typeof r.label !== 'string' || !r.label.trim()) {
          fail(`${qLabel}.rubric[${rIdx}]: missing non-empty string label`);
        } else {
          checkTextAndMath(`${qLabel}.rubric[${rIdx}]`, r.label);
        }
        rSum += Number(r.pts ?? 0);
      }
      if (rSum !== q.score) {
        fail(`${qLabel}: rubric sum ${rSum} != question score ${q.score}`);
      }
    }

    for (const fig of [...(q.figures ?? []), ...(q.analysisFigures ?? [])]) {
      const figDisk = fig.src.startsWith('data/')
        ? path.join(ROOT, 'web', 'public', fig.src)
        : path.join(baseDir, fig.src);
      if (!fs.existsSync(figDisk)) {
        fail(`${qLabel}: missing figure file ${figDisk}`);
      }
    }

    checkTextAndMath(`${qLabel}.title`, q.title);
    checkTextAndMath(`${qLabel}.stem`, q.stem);
    checkTextAndMath(`${qLabel}.note`, q.note);
    checkTextAndMath(`${qLabel}.shortAnswer`, q.shortAnswer);
    checkTextAndMath(`${qLabel}.answer`, q.answer);
    checkTextAndMath(`${qLabel}.analysis`, q.analysis);
    checkTextAndMath(`${qLabel}.pitfalls`, q.pitfalls);
    for (const opt of q.options ?? []) {
      checkTextAndMath(`${qLabel}.opt.${opt.label}`, opt.text);
    }
  }

  if (scoreSum !== paper.totalScore) {
    fail(`${labelPrefix}: question score sum ${scoreSum} != totalScore ${paper.totalScore}`);
  }
  for (const n of paper.examNotes ?? []) {
    checkTextAndMath(`${labelPrefix}.examNote`, n);
  }
  return scoreSum;
}

if (packFiles.length > 0) {
  const cDir = path.join(DATA_ROOT, targetCourseId);
  const chPath = path.join(cDir, 'chapters.json');
  if (!fs.existsSync(chPath)) {
    console.error(`Missing chapters.json for course ${targetCourseId}: ${chPath}`);
    process.exit(1);
  }
  const chJson = JSON.parse(fs.readFileSync(chPath, 'utf8'));
  const validChapterNums = new Set(chJson.chapters.map((c) => c.chapter));
  console.log(`=== Validating standalone packs for course: ${targetCourseId} ===`);
  for (const rawPack of packFiles) {
    const absPack = path.resolve(rawPack);
    if (!fs.existsSync(absPack)) {
      fail(`Missing pack file: ${absPack}`);
      continue;
    }
    const paper = JSON.parse(fs.readFileSync(absPack, 'utf8'));
    const scoreSum = validatePaper(
      paper,
      `${targetCourseId}.${paper.year ?? path.basename(absPack)}`,
      path.dirname(absPack),
      validChapterNums,
      null
    );
    console.log(
      `  [OK] ${path.basename(absPack)}: ${(paper.questions ?? []).length} questions (${scoreSum} pts) verified.`
    );
  }
  console.log(`Done! Checked ${mathChecked} KaTeX expressions. Total errors: ${errors}`);
  if (errors > 0) process.exit(1);
  process.exit(0);
}

const catalog = JSON.parse(fs.readFileSync(path.join(DATA_ROOT, 'courses.json'), 'utf8'));
const coursesToCheck = targetCourseId
  ? catalog.courses.filter((c) => c.id === targetCourseId)
  : catalog.courses;

if (coursesToCheck.length === 0) {
  console.error(`No course matched: ${targetCourseId}`);
  process.exit(1);
}

for (const course of coursesToCheck) {
  console.log(`=== Validating course: ${course.id} (${course.name}) ===`);
  const cDir = path.join(DATA_ROOT, course.id);
  const idxJson = JSON.parse(fs.readFileSync(path.join(cDir, 'index.json'), 'utf8'));
  const chJson = JSON.parse(fs.readFileSync(path.join(cDir, 'chapters.json'), 'utf8'));
  const fmJson = JSON.parse(fs.readFileSync(path.join(cDir, 'formulas.json'), 'utf8'));

  const validChapterNums = new Set(chJson.chapters.map((c) => c.chapter));

  for (const fm of fmJson.formulas) {
    if (!validChapterNums.has(fm.chapter)) {
      fail(`${course.id} formula ${fm.id}: chapter ${fm.chapter} not in chapters.json`);
    }
    mathChecked++;
    try {
      katex.renderToString(fm.latex, { displayMode: true, throwOnError: true, strict: false });
    } catch (err) {
      fail(`${course.id} formula ${fm.id} KaTeX error: ${err.message}`);
    }
    checkTextAndMath(`${course.id}.${fm.id}.variables`, fm.variables);
    checkTextAndMath(`${course.id}.${fm.id}.note`, fm.note);
  }

  for (const ym of idxJson.availableYears) {
    if (ym.status !== 'ready') continue;
    const pFile = path.join(cDir, ym.dataFile.replace(/^data\//, ''));
    if (!fs.existsSync(pFile)) {
      fail(`${course.id} ${ym.year}: missing dataFile ${pFile}`);
      continue;
    }
    const paper = JSON.parse(fs.readFileSync(pFile, 'utf8'));
    const scoreSum = validatePaper(
      paper,
      `${course.id}.${ym.year}`,
      cDir,
      validChapterNums,
      ym.questionCount
    );
    console.log(`  [OK] ${ym.year}: ${(paper.questions ?? []).length} questions (${scoreSum} pts) verified.`);
  }
}

console.log(`Done! Checked ${mathChecked} KaTeX expressions. Total errors: ${errors}`);
if (errors > 0) process.exit(1);
