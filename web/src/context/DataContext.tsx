import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import type {
  AnnouncementItem,
  ChapterInfo,
  ChaptersPayload,
  CourseMeta,
  CoursesCatalog,
  ExamPaper,
  ExamYearMeta,
  FormulaItem,
  Question,
} from '../types';
import { BRAND } from '../brand';
import { useWorkshopOptional } from './WorkshopContext';

const ACTIVE_COURSE_STORAGE_KEY = 'jingyan_active_course_v1';
const LAST_READ_ANN_KEY = 'jingyan_last_read_ann_v1';

const FALLBACK_COURSE: CourseMeta = {
  id: 'hhu-814',
  name: '河海大学 · 814 水力学',
  shortLabel: '河海 814',
  school: '河海大学',
  code: '814',
  subject: '水力学',
  category: '水利 / 土木考研专业课',
  examMetaBadge: '科目代码 814 · 闭卷 · 禁用计算器',
  status: 'ready',
  description: '',
};

interface DataContextValue {
  loading: boolean;
  error: string | null;
  courses: CourseMeta[];
  currentCourse: CourseMeta;
  setCourseId: (courseId: string) => void;
  resolveCourseAsset: (relPath: string) => string;
  yearsMeta: ExamYearMeta[];
  papersByYear: Record<number, ExamPaper>;
  allQuestions: Question[];
  questionsById: Record<string, Question>;
  chaptersPayload: ChaptersPayload | null;
  chapters: ChapterInfo[];
  chapterMap: Record<number, ChapterInfo>;
  formulas: FormulaItem[];
  announcements: AnnouncementItem[];
  latestAnnouncement: AnnouncementItem | null;
  hasUnreadAnnouncement: boolean;
  markAnnouncementsRead: () => void;
}

const DataContext = createContext<DataContextValue | null>(null);

function readInitialCourseId(): string {
  try {
    const hashParams = new URLSearchParams(window.location.hash.split('?')[1] ?? '');
    const fromUrl = hashParams.get('course');
    if (fromUrl) return fromUrl;
    return localStorage.getItem(ACTIVE_COURSE_STORAGE_KEY) || 'hhu-814';
  } catch {
    return 'hhu-814';
  }
}

function countPaperFigures(paper: ExamPaper): number {
  let count = 0;
  for (const q of paper.questions ?? []) {
    count += (q.figures?.length ?? 0) + (q.analysisFigures?.length ?? 0);
  }
  return count;
}

function normalizeAssetKey(relPath: string): string {
  return relPath.replace(/\\/g, '/').replace(/^\.\//, '').replace(/^\/+/, '');
}

export const DataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const workshop = useWorkshopOptional();
  const workshopReady = workshop ? workshop.ready : true;
  const enabledPacks = useMemo(() => workshop?.enabledPacks ?? [], [workshop?.enabledPacks]);

  const [baseCourses, setBaseCourses] = useState<CourseMeta[]>([FALLBACK_COURSE]);
  const [defaultCourseId, setDefaultCourseId] = useState<string>('hhu-814');
  const [courseId, setCourseIdState] = useState<string>(readInitialCourseId);
  const courseIdRef = useRef(courseId);
  courseIdRef.current = courseId;
  const [catalogLoaded, setCatalogLoaded] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [yearsMeta, setYearsMeta] = useState<ExamYearMeta[]>([]);
  const [papersByYear, setPapersByYear] = useState<Record<number, ExamPaper>>({});
  const [chaptersPayload, setChaptersPayload] = useState<ChaptersPayload | null>(null);
  const [formulas, setFormulas] = useState<FormulaItem[]>([]);
  const [assetOwnerMap, setAssetOwnerMap] = useState<Record<string, string>>({});
  const [announcements, setAnnouncements] = useState<AnnouncementItem[]>([]);
  const [lastReadAnnId, setLastReadAnnId] = useState<string>(() => {
    try {
      return localStorage.getItem(LAST_READ_ANN_KEY) || '';
    } catch {
      return '';
    }
  });

  // 0. Non-blocking load of announcements.json
  useEffect(() => {
    let cancelled = false;
    fetch('./data/announcements.json')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (cancelled || !data || !Array.isArray(data.announcements)) return;
        const sorted = [...(data.announcements as AnnouncementItem[])].sort((a, b) => {
          if (Boolean(a.pinned) !== Boolean(b.pinned)) return a.pinned ? -1 : 1;
          return b.date.localeCompare(a.date);
        });
        setAnnouncements(sorted);
      })
      .catch(() => {
        // non-blocking; leave empty on error
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const latestAnnouncement = announcements[0] ?? null;
  const hasUnreadAnnouncement = Boolean(latestAnnouncement && latestAnnouncement.id !== lastReadAnnId);

  const markAnnouncementsRead = useCallback(() => {
    if (!latestAnnouncement) return;
    setLastReadAnnId(latestAnnouncement.id);
    try {
      localStorage.setItem(LAST_READ_ANN_KEY, latestAnnouncement.id);
    } catch {
      // ignore
    }
  }, [latestAnnouncement]);

  // 1. Load master courses.json once
  useEffect(() => {
    let cancelled = false;
    async function loadCatalog() {
      try {
        const res = await fetch('./data/courses.json');
        if (!res.ok) throw new Error('专业课目录加载失败');
        const cat = (await res.json()) as CoursesCatalog;
        if (cancelled) return;
        setBaseCourses(cat.courses);
        setDefaultCourseId(cat.defaultCourseId || cat.courses[0]?.id || 'hhu-814');
        setCatalogLoaded(true);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : '专业课目录加载异常');
          setLoading(false);
        }
      }
    }
    void loadCatalog();
    return () => {
      cancelled = true;
    };
  }, []);

  const courses = useMemo(() => {
    const merged: CourseMeta[] = [...baseCourses];
    const seenIds = new Set(merged.map((c) => c.id));
    for (const pack of enabledPacks) {
      if (pack.manifest.type !== 'course') continue;
      const wc = pack.coursePayload?.course;
      if (!wc || seenIds.has(wc.id)) continue;
      seenIds.add(wc.id);
      merged.push({ ...wc, status: 'ready', sourcePackId: pack.packId });
    }
    return merged;
  }, [baseCourses, enabledPacks]);

  // Keep courseId valid when catalog & workshop ready state change
  useEffect(() => {
    if (!catalogLoaded || !workshopReady) return;
    if (!courses.some((c) => c.id === courseId)) {
      const fallback = courses.some((c) => c.id === defaultCourseId)
        ? defaultCourseId
        : courses[0]?.id || 'hhu-814';
      setCourseIdState(fallback);
      try {
        localStorage.setItem(ACTIVE_COURSE_STORAGE_KEY, fallback);
      } catch {
        // ignore
      }
    }
  }, [catalogLoaded, workshopReady, courses, courseId, defaultCourseId]);

  const setCourseId = useCallback((nextId: string) => {
    if (nextId === courseIdRef.current) return;
    courseIdRef.current = nextId;
    setLoading(true);
    setError(null);
    setCourseIdState(nextId);
    try {
      localStorage.setItem(ACTIVE_COURSE_STORAGE_KEY, nextId);
    } catch {
      // ignore
    }
  }, []);

  const currentCourse = useMemo(
    () => courses.find((c) => c.id === courseId) ?? courses[0] ?? FALLBACK_COURSE,
    [courses, courseId]
  );

  // Update browser tab title dynamically when course changes
  useEffect(() => {
    document.title = `${BRAND.name} · ${currentCourse.name}`;
  }, [currentCourse]);

  // 2. Load active course's data (built-in + workshop course/exam overlays)
  useEffect(() => {
    if (!catalogLoaded || !workshopReady) return;
    if (!courses.some((c) => c.id === courseId)) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    const activeWorkshopCoursePack = enabledPacks.find(
      (p) => p.manifest.type === 'course' && p.coursePayload?.course?.id === courseId
    );
    const matchingExamPacks = enabledPacks
      .filter((p) => p.manifest.type === 'exam' && p.coursePayload?.targetCourseId === courseId)
      .sort((a, b) => a.installedAt.localeCompare(b.installedAt));

    async function loadCourseBundle() {
      try {
        let nextYearsMeta: ExamYearMeta[] = [];
        let nextChapters: ChaptersPayload | null = null;
        let nextFormulas: FormulaItem[] = [];
        const loadedPapers: Record<number, ExamPaper> = {};
        const nextAssetOwners: Record<string, string> = {};

        const recordPaperAssets = (paper: ExamPaper, ownerPackId: string) => {
          for (const q of paper.questions ?? []) {
            for (const f of [...(q.figures ?? []), ...(q.analysisFigures ?? [])]) {
              nextAssetOwners[normalizeAssetKey(f.src)] = ownerPackId;
            }
          }
        };

        if (activeWorkshopCoursePack?.coursePayload) {
          const cp = activeWorkshopCoursePack.coursePayload;
          nextChapters = cp.chapters ?? null;
          nextFormulas = [...(cp.formulas ?? [])];
          for (const paper of cp.papers ?? []) {
            loadedPapers[paper.year] = paper;
            recordPaperAssets(paper, activeWorkshopCoursePack.packId);
            nextYearsMeta.push({
              year: paper.year,
              title: `${paper.year}年 ${paper.subject || currentCourse.subject} 真题`,
              questionCount: paper.questions.length,
              totalScore: paper.totalScore,
              figureCount: countPaperFigures(paper),
              status: 'ready',
              dataFile: `papers/${paper.year}.json`,
            });
          }
        } else {
          const base = `./data/${courseId}`;
          const [idxRes, chRes, fmRes] = await Promise.all([
            fetch(`${base}/index.json`),
            fetch(`${base}/chapters.json`),
            fetch(`${base}/formulas.json`),
          ]);
          if (!idxRes.ok || !chRes.ok || !fmRes.ok) {
            throw new Error(`板块「${currentCourse.name}」数据加载失败`);
          }
          const idxJson = (await idxRes.json()) as { availableYears: ExamYearMeta[] };
          const chJson = (await chRes.json()) as ChaptersPayload;
          const fmJson = (await fmRes.json()) as { formulas: FormulaItem[] };

          nextYearsMeta = [...(idxJson.availableYears ?? [])];
          nextChapters = chJson;
          nextFormulas = [...(fmJson.formulas ?? [])];

          const readyYears = nextYearsMeta.filter((y) => y.status === 'ready');
          await Promise.all(
            readyYears.map(async (ym) => {
              const cleanFile = ym.dataFile.replace(/^data\//, '');
              const pRes = await fetch(`${base}/${cleanFile}`);
              if (pRes.ok) {
                loadedPapers[ym.year] = (await pRes.json()) as ExamPaper;
              }
            })
          );
        }

        // Overlay any enabled incremental exam packs targeting this course
        for (const examPack of matchingExamPacks) {
          const ep = examPack.coursePayload;
          if (!ep) continue;
          if (!nextChapters && ep.chapters) {
            nextChapters = ep.chapters;
          }
          if (ep.formulas && ep.formulas.length > 0) {
            const seenFormulaIds = new Set(nextFormulas.map((f) => f.id));
            for (const fm of ep.formulas) {
              if (!seenFormulaIds.has(fm.id)) {
                seenFormulaIds.add(fm.id);
                nextFormulas.push(fm);
              }
            }
          }
          for (const paper of ep.papers ?? []) {
            loadedPapers[paper.year] = paper;
            recordPaperAssets(paper, examPack.packId);
            const metaEntry: ExamYearMeta = {
              year: paper.year,
              title: `${paper.year}年 ${paper.subject || currentCourse.subject} 真题（工坊扩展）`,
              questionCount: paper.questions.length,
              totalScore: paper.totalScore,
              figureCount: countPaperFigures(paper),
              status: 'ready',
              dataFile: `papers/${paper.year}.json`,
            };
            const existingIdx = nextYearsMeta.findIndex((y) => y.year === paper.year);
            if (existingIdx >= 0) {
              nextYearsMeta[existingIdx] = metaEntry;
            } else {
              nextYearsMeta.push(metaEntry);
            }
          }
        }

        nextYearsMeta.sort((a, b) => b.year - a.year);

        if (!cancelled) {
          setYearsMeta(nextYearsMeta);
          setChaptersPayload(nextChapters);
          setFormulas(nextFormulas);
          setPapersByYear(loadedPapers);
          setAssetOwnerMap(nextAssetOwners);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : '题库加载失败');
          setLoading(false);
        }
      }
    }

    void loadCourseBundle();
    return () => {
      cancelled = true;
    };
  }, [catalogLoaded, workshopReady, courses, courseId, currentCourse.name, currentCourse.subject, enabledPacks]);

  const resolveCourseAsset = useCallback(
    (relPath: string): string => {
      if (!relPath) return '';
      if (/^(blob:|data:image\/|https?:|\/)/.test(relPath)) {
        return relPath;
      }
      const clean = normalizeAssetKey(relPath);
      const ownerPackId = assetOwnerMap[clean];
      if (ownerPackId && workshop) {
        const blobUrl = workshop.resolvePackBlobUrl(ownerPackId, clean);
        if (blobUrl) return blobUrl;
      }
      if (workshop) {
        for (const pack of enabledPacks) {
          if (
            (pack.manifest.type === 'course' && pack.coursePayload?.course?.id === courseId) ||
            (pack.manifest.type === 'exam' && pack.coursePayload?.targetCourseId === courseId)
          ) {
            const blobUrl = workshop.resolvePackBlobUrl(pack.packId, clean);
            if (blobUrl) return blobUrl;
          }
        }
      }
      if (relPath.startsWith('./')) return relPath;
      return clean.startsWith('data/') ? `./${clean}` : `./data/${courseId}/${clean}`;
    },
    [assetOwnerMap, courseId, enabledPacks, workshop]
  );

  const value = useMemo<DataContextValue>(() => {
    const chapters = chaptersPayload?.chapters ?? [];
    const chapterMap: Record<number, ChapterInfo> = {};
    for (const c of chapters) {
      chapterMap[c.chapter] = c;
    }
    const allQuestions: Question[] = Object.values(papersByYear)
      .sort((a, b) => b.year - a.year)
      .flatMap((p) => p.questions);
    const questionsById: Record<string, Question> = {};
    for (const q of allQuestions) {
      questionsById[q.id] = q;
    }
    return {
      loading,
      error,
      courses,
      currentCourse,
      setCourseId,
      resolveCourseAsset,
      yearsMeta,
      papersByYear,
      allQuestions,
      questionsById,
      chaptersPayload,
      chapters,
      chapterMap,
      formulas,
      announcements,
      latestAnnouncement,
      hasUnreadAnnouncement,
      markAnnouncementsRead,
    };
  }, [
    loading,
    error,
    courses,
    currentCourse,
    setCourseId,
    resolveCourseAsset,
    yearsMeta,
    papersByYear,
    chaptersPayload,
    formulas,
    announcements,
    latestAnnouncement,
    hasUnreadAnnouncement,
    markAnnouncementsRead,
  ]);

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
};

export function useData(): DataContextValue {
  const ctx = useContext(DataContext);
  if (!ctx) throw new Error('useData must be used inside DataProvider');
  return ctx;
}
