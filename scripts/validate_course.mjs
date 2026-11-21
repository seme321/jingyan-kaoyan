#!/usr/bin/env node
/**
 * Validate one or all courses in `web/public/data/courses.json`:
 * - Schema & chapter ID integrity
 * - Score sum & rubric sum consistency
 * - Figure file existence on disk
 * - Real KaTeX compilation (`throwOnError: true`) on every math block
 * - Anti-infringement / third-party reference keyword check
 *
 * Usage:
 *   node scripts/validate_course.mjs
 *   node scripts/validate_course.mjs --course yzu-849
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
const courseArgIdx = args.indexOf('--course');
const targetCourseId = courseArgIdx >= 0 ? args[courseArgIdx + 1] : null;

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
      // Allow formula chapter only if chapter exists
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
    const qs = paper.questions ?? [];
    if (qs.length !== ym.questionCount) {
      fail(`${course.id} ${ym.year}: index questionCount=${ym.questionCount} != actual ${qs.length}`);
    }
    const scoreSum = qs.reduce((s, q) => s + q.score, 0);
    if (scoreSum !== paper.totalScore) {
      fail(`${course.id} ${ym.year}: question score sum ${scoreSum} != totalScore ${paper.totalScore}`);
    }

    for (const n of paper.examNotes ?? []) {
      checkTextAndMath(`${course.id}.${ym.year}.examNote`, n);
    }

    for (const q of qs) {
      if (!validChapterNums.has(q.chapter)) {
        fail(`${q.id}: chapter ${q.chapter} does not exist in ${course.id}/chapters.json`);
      }
      if (q.rubric && q.rubric.length > 0) {
        const rSum = q.rubric.reduce((s, r) => s + r.pts, 0);
        if (rSum !== q.score) {
          fail(`${q.id}: rubric sum ${rSum} != question score ${q.score}`);
        }
      }
      for (const fig of [...(q.figures ?? []), ...(q.analysisFigures ?? [])]) {
        const figDisk = fig.src.startsWith('data/')
          ? path.join(ROOT, 'web', 'public', fig.src)
          : path.join(cDir, fig.src);
        if (!fs.existsSync(figDisk)) {
          fail(`${q.id}: missing figure file ${figDisk}`);
        }
      }
      checkTextAndMath(`${q.id}.title`, q.title);
      checkTextAndMath(`${q.id}.stem`, q.stem);
      checkTextAndMath(`${q.id}.note`, q.note);
      checkTextAndMath(`${q.id}.shortAnswer`, q.shortAnswer);
      checkTextAndMath(`${q.id}.answer`, q.answer);
      checkTextAndMath(`${q.id}.analysis`, q.analysis);
      checkTextAndMath(`${q.id}.pitfalls`, q.pitfalls);
      for (const opt of q.options ?? []) {
        checkTextAndMath(`${q.id}.opt.${opt.label}`, opt.text);
      }
    }
    console.log(`  [OK] ${ym.year}: ${qs.length} questions (${scoreSum} pts) verified.`);
  }
}

console.log(`Done! Checked ${mathChecked} KaTeX expressions. Total errors: ${errors}`);
if (errors > 0) process.exit(1);
