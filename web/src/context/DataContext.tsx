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

export const DataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [courses, setCourses] = useState<CourseMeta[]>([FALLBACK_COURSE]);
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
        setCourses(cat.courses);
        setCourseIdState((prev) =>
          cat.courses.some((c) => c.id === prev) ? prev : cat.defaultCourseId
        );
        setCatalogLoaded(true);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : '专业课目录加载异常');
          setLoading(false);
        }
      }
    }
    loadCatalog();
    return () => {
      cancelled = true;
    };
  }, []);

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

  // 2. Load active course's data whenever courseId changes
  useEffect(() => {
    if (!catalogLoaded) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    async function loadCourseBundle() {
      try {
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

        const readyYears = idxJson.availableYears.filter((y) => y.status === 'ready');
        const loadedPapers: Record<number, ExamPaper> = {};
        await Promise.all(
          readyYears.map(async (ym) => {
            const cleanFile = ym.dataFile.replace(/^data\//, '');
            const pRes = await fetch(`${base}/${cleanFile}`);
            if (pRes.ok) {
              loadedPapers[ym.year] = (await pRes.json()) as ExamPaper;
            }
          })
        );

        if (!cancelled) {
          setYearsMeta(idxJson.availableYears);
          setChaptersPayload(chJson);
          setFormulas(fmJson.formulas ?? []);
          setPapersByYear(loadedPapers);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : '题库加载失败');
          setLoading(false);
        }
      }
    }

    loadCourseBundle();
    return () => {
      cancelled = true;
    };
  }, [catalogLoaded, courseId, currentCourse.name]);

  const resolveCourseAsset = useCallback(
    (relPath: string): string => {
      if (!relPath) return '';
      if (/^(https?:|\.\/|\/|data\/)/.test(relPath)) {
        return relPath.startsWith('data/') ? `./${relPath}` : relPath;
      }
      return `./data/${courseId}/${relPath}`;
    },
    [courseId]
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
