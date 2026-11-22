import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import type {
  ActiveMockSession,
  AppSettings,
  CompanionState,
  CourseStudySlice,
  MasteryStatus,
  MockAttempt,
  MultiCourseStudyState,
  QuestionRecord,
  StudyEvent,
} from '../types';
import { useData } from './DataContext';

const STORAGE_KEY_V2 = 'jingyan_study_multi_v2';
const LEGACY_STORAGE_KEY_V1 = 'shuizhuan_814_study_v1';

const DEFAULT_SETTINGS: AppSettings = {
  theme: 'dark',
  fontSize: 'md',
  fontFamily: 'sans',
  hideTagsBeforeAnswer: true,
  softDiagramInDark: true,
  diagramDarkMode: 'blueprint',
  animatedBg: true,
};

const EMPTY_SLICE: CourseStudySlice = {
  records: {},
  favoriteFormulas: [],
  practiceLogs: [],
  mockHistory: [],
  activeMock: null,
};

const EMPTY_RECORD: QuestionRecord = {
  status: 'unseen',
  inWrongBook: false,
  favorite: false,
  attempts: 0,
  wrongCount: 0,
  updatedAt: 0,
};

function loadInitialMultiState(): MultiCourseStudyState {
  try {
    const rawV2 = localStorage.getItem(STORAGE_KEY_V2);
    if (rawV2) {
      const parsed = JSON.parse(rawV2) as Partial<MultiCourseStudyState>;
      return {
        courses: parsed.courses ?? {},
        settings: { ...DEFAULT_SETTINGS, ...(parsed.settings ?? {}) },
        ...(parsed.companion ? { companion: parsed.companion } : {}),
      };
    }
    // Seamless migration from single-course v1 ('hhu-814')
    const rawV1 = localStorage.getItem(LEGACY_STORAGE_KEY_V1);
    if (rawV1) {
      const legacy = JSON.parse(rawV1);
      return {
        courses: {
          'hhu-814': {
            records: legacy.records ?? {},
            favoriteFormulas: legacy.favoriteFormulas ?? [],
            practiceLogs: legacy.practiceLogs ?? [],
            mockHistory: legacy.mockHistory ?? [],
            activeMock: legacy.activeMock ?? null,
          },
        },
        settings: { ...DEFAULT_SETTINGS, ...(legacy.settings ?? {}) },
      };
    }
  } catch {
    // ignore
  }
  return { courses: {}, settings: DEFAULT_SETTINGS };
}

interface ScopedStudyState extends CourseStudySlice {
  settings: AppSettings;
}

interface StudyContextValue {
  state: ScopedStudyState;
  multiState: MultiCourseStudyState;
  allCourses: Record<string, CourseStudySlice>;
  companionState: CompanionState | undefined;
  setCompanionState: (updater: (prev: CompanionState | undefined) => CompanionState) => void;
  replaceMultiState: (next: MultiCourseStudyState) => void;
  subscribeStudyEvent: (listener: (ev: StudyEvent) => void) => () => void;
  resolvedTheme: 'dark' | 'light';
  getRecord: (qid: string) => QuestionRecord;
  recordAttempt: (
    qid: string,
    status: MasteryStatus,
    extra?: { judgeChoice?: boolean | null; choice?: string; draft?: string }
  ) => void;
  toggleFavorite: (qid: string) => void;
  removeFromWrongBook: (qid: string, markMastered?: boolean) => void;
  addToWrongBook: (qid: string) => void;
  saveQuestionNote: (qid: string, note: string) => void;
  saveQuestionDraft: (qid: string, draft: string) => void;
  toggleFavoriteFormula: (fid: string) => void;
  setActiveMock: (
    session: ActiveMockSession | null | ((prev: ActiveMockSession | null) => ActiveMockSession | null)
  ) => void;
  saveMockAttempt: (attempt: MockAttempt) => void;
  trackQuestionReviewed: (qid: string) => void;
  updateSettings: (patch: Partial<AppSettings>) => void;
  exportBackupJson: () => string;
  importBackupJson: (jsonText: string) => { ok: boolean; message: string };
  resetCurrentCourseProgress: () => void;
}

const StudyContext = createContext<StudyContextValue | null>(null);

export const StudyProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { currentCourse, questionsById } = useData();
  const cid = currentCourse.id;
  const [multi, setMulti] = useState<MultiCourseStudyState>(loadInitialMultiState);
  const multiRef = useRef(multi);
  multiRef.current = multi;
  const listenersRef = useRef<Set<(ev: StudyEvent) => void>>(new Set());

  const subscribeStudyEvent = useCallback((listener: (ev: StudyEvent) => void) => {
    listenersRef.current.add(listener);
    return () => {
      listenersRef.current.delete(listener);
    };
  }, []);

  const emitStudyEvent = useCallback((ev: StudyEvent) => {
    queueMicrotask(() => {
      listenersRef.current.forEach((fn) => {
        try {
          fn(ev);
        } catch {
          // ignore subscriber errors
        }
      });
    });
  }, []);

  const setCompanionState = useCallback(
    (updater: (prev: CompanionState | undefined) => CompanionState) => {
      setMulti((prev) => ({
        ...prev,
        companion: updater(prev.companion),
      }));
    },
    []
  );

  const replaceMultiState = useCallback((next: MultiCourseStudyState) => {
    const validCompanion =
      next.companion && typeof next.companion === 'object' && !Array.isArray(next.companion);
    const normalized: MultiCourseStudyState = {
      courses: next.courses && typeof next.courses === 'object' ? next.courses : {},
      settings: { ...DEFAULT_SETTINGS, ...(next.settings ?? {}) },
      ...(validCompanion ? { companion: next.companion } : {}),
    };
    setMulti(normalized);
  }, []);

  const lastSerializedRef = useRef<string | null>(null);

  useEffect(() => {
    try {
      const serialized = JSON.stringify(multi);
      if (serialized === lastSerializedRef.current) return;
      lastSerializedRef.current = serialized;
      localStorage.setItem(STORAGE_KEY_V2, serialized);
    } catch {
      // ignore quota errors
    }
  }, [multi]);

  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key !== STORAGE_KEY_V2 || !e.newValue || e.newValue === lastSerializedRef.current) {
        return;
      }
      try {
        const parsed = JSON.parse(e.newValue) as Partial<MultiCourseStudyState>;
        if (!parsed || typeof parsed !== 'object') return;
        const validCompanion =
          parsed.companion &&
          typeof parsed.companion === 'object' &&
          !Array.isArray(parsed.companion);
        const normalized: MultiCourseStudyState = {
          courses: parsed.courses ?? {},
          settings: { ...DEFAULT_SETTINGS, ...(parsed.settings ?? {}) },
          ...(validCompanion ? { companion: parsed.companion } : {}),
        };
        lastSerializedRef.current = JSON.stringify(normalized);
        setMulti(normalized);
      } catch {
        // ignore malformed storage updates
      }
    };
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  const [resolvedTheme, setResolvedTheme] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    const root = document.documentElement;
    const { theme, fontSize, fontFamily } = multi.settings;
    const media = window.matchMedia('(prefers-color-scheme: light)');

    const applyTheme = () => {
      const nextTheme: 'dark' | 'light' =
        theme === 'system' ? (media.matches ? 'light' : 'dark') : theme;
      setResolvedTheme(nextTheme);
      root.setAttribute('data-theme', nextTheme);
      root.setAttribute('data-font-size', fontSize);
      root.setAttribute('data-font-family', fontFamily);
      const metaTheme = document.querySelector('meta[name="theme-color"]');
      if (metaTheme) {
        metaTheme.setAttribute('content', nextTheme === 'dark' ? '#0a0e14' : '#eceff3');
      }
    };

    applyTheme();
    if (theme !== 'system') return;

    media.addEventListener('change', applyTheme);
    return () => media.removeEventListener('change', applyTheme);
  }, [multi.settings]);

  const currentSlice: CourseStudySlice = useMemo(
    () => multi.courses[cid] ?? EMPTY_SLICE,
    [multi.courses, cid]
  );

  const updateSlice = useCallback(
    (updater: (prev: CourseStudySlice) => CourseStudySlice) => {
      setMulti((prev) => {
        const cur = prev.courses[cid] ?? EMPTY_SLICE;
        return {
          ...prev,
          courses: {
            ...prev.courses,
            [cid]: updater(cur),
          },
        };
      });
    },
    [cid]
  );

  const getRecord = useCallback(
    (qid: string): QuestionRecord => currentSlice.records[qid] ?? EMPTY_RECORD,
    [currentSlice.records]
  );

  const recordAttempt = useCallback(
    (
      qid: string,
      status: MasteryStatus,
      extra?: { judgeChoice?: boolean | null; choice?: string; draft?: string }
    ) => {
      const now = Date.now();
      const prevStatus: MasteryStatus =
        multiRef.current.courses[cid]?.records?.[qid]?.status ?? 'unseen';
      const q = questionsById[qid];
      const isBigQuestion = q?.type === 'calc' || q?.type === 'proof';
      updateSlice((slice) => {
        const cur = slice.records[qid] ?? { ...EMPTY_RECORD };
        const isWrongOrPartial = status === 'wrong' || status === 'partial';
        const nextRec: QuestionRecord = {
          ...cur,
          status,
          inWrongBook: status === 'mastered' ? cur.inWrongBook : isWrongOrPartial || cur.inWrongBook,
          attempts: cur.attempts + 1,
          wrongCount: cur.wrongCount + (status === 'wrong' ? 1 : 0),
          lastJudgeChoice: extra?.judgeChoice !== undefined ? extra.judgeChoice : cur.lastJudgeChoice,
          lastChoice: extra?.choice !== undefined ? extra.choice : cur.lastChoice,
          userDraft: extra?.draft !== undefined ? extra.draft : cur.userDraft,
          updatedAt: now,
        };
        const logEntry = {
          id: `${now}-${Math.random().toString(36).slice(2, 7)}`,
          qid,
          result: status,
          timestamp: now,
        };
        return {
          ...slice,
          records: { ...slice.records, [qid]: nextRec },
          practiceLogs: [logEntry, ...slice.practiceLogs].slice(0, 300),
        };
      });
      emitStudyEvent({
        type: 'attempt',
        courseId: cid,
        qid,
        status,
        prevStatus,
        isBigQuestion,
      });
    },
    [cid, emitStudyEvent, questionsById, updateSlice]
  );

  const toggleFavorite = useCallback(
    (qid: string) => {
      const now = Date.now();
      updateSlice((slice) => {
        const cur = slice.records[qid] ?? { ...EMPTY_RECORD };
        return {
          ...slice,
          records: { ...slice.records, [qid]: { ...cur, favorite: !cur.favorite, updatedAt: now } },
        };
      });
    },
    [updateSlice]
  );

  const removeFromWrongBook = useCallback(
    (qid: string, markMastered = true) => {
      const now = Date.now();
      const wasInWrongBook = Boolean(multiRef.current.courses[cid]?.records?.[qid]?.inWrongBook);
      updateSlice((slice) => {
        const cur = slice.records[qid] ?? { ...EMPTY_RECORD };
        return {
          ...slice,
          records: {
            ...slice.records,
            [qid]: {
              ...cur,
              inWrongBook: false,
              status: markMastered ? 'mastered' : cur.status,
              updatedAt: now,
            },
          },
        };
      });
      if (wasInWrongBook) {
        emitStudyEvent({ type: 'wrong_cleared', courseId: cid, qid });
      }
    },
    [cid, emitStudyEvent, updateSlice]
  );

  const addToWrongBook = useCallback(
    (qid: string) => {
      const now = Date.now();
      updateSlice((slice) => {
        const cur = slice.records[qid] ?? { ...EMPTY_RECORD };
        return {
          ...slice,
          records: {
            ...slice.records,
            [qid]: {
              ...cur,
              inWrongBook: true,
              status: cur.status === 'unseen' || cur.status === 'mastered' ? 'wrong' : cur.status,
              updatedAt: now,
            },
          },
        };
      });
    },
    [updateSlice]
  );

  const saveQuestionNote = useCallback(
    (qid: string, note: string) => {
      updateSlice((slice) => {
        const cur = slice.records[qid] ?? { ...EMPTY_RECORD };
        return {
          ...slice,
          records: { ...slice.records, [qid]: { ...cur, note, updatedAt: Date.now() } },
        };
      });
      if (note.trim().length >= 8) {
        emitStudyEvent({ type: 'note_saved', courseId: cid, qid });
      }
    },
    [cid, emitStudyEvent, updateSlice]
  );

  const saveQuestionDraft = useCallback(
    (qid: string, draft: string) => {
      updateSlice((slice) => {
        const cur = slice.records[qid] ?? { ...EMPTY_RECORD };
        return {
          ...slice,
          records: { ...slice.records, [qid]: { ...cur, userDraft: draft, updatedAt: Date.now() } },
        };
      });
    },
    [updateSlice]
  );

  const toggleFavoriteFormula = useCallback(
    (fid: string) => {
      updateSlice((slice) => {
        const exists = slice.favoriteFormulas.includes(fid);
        return {
          ...slice,
          favoriteFormulas: exists
            ? slice.favoriteFormulas.filter((x) => x !== fid)
            : [...slice.favoriteFormulas, fid],
        };
      });
    },
    [updateSlice]
  );

  const setActiveMock = useCallback(
    (
      next: ActiveMockSession | null | ((prev: ActiveMockSession | null) => ActiveMockSession | null)
    ) => {
      updateSlice((slice) => ({
        ...slice,
        activeMock: typeof next === 'function' ? next(slice.activeMock) : next,
      }));
    },
    [updateSlice]
  );

  const saveMockAttempt = useCallback(
    (attempt: MockAttempt) => {
      updateSlice((slice) => ({
        ...slice,
        activeMock: null,
        mockHistory: [attempt, ...slice.mockHistory].slice(0, 50),
      }));
      emitStudyEvent({ type: 'mock_saved', courseId: cid, year: attempt.year });
    },
    [cid, emitStudyEvent, updateSlice]
  );

  const trackQuestionReviewed = useCallback(
    (qid: string) => {
      const q = questionsById[qid];
      const isBigQuestion = q?.type === 'calc' || q?.type === 'proof';
      emitStudyEvent({
        type: 'question_reviewed',
        courseId: cid,
        qid,
        isBigQuestion,
      });
    },
    [cid, emitStudyEvent, questionsById]
  );

  const updateSettings = useCallback((patch: Partial<AppSettings>) => {
    setMulti((prev) => ({
      ...prev,
      settings: { ...prev.settings, ...patch },
    }));
  }, []);

  const exportBackupJson = useCallback(() => {
    return JSON.stringify(
      {
        app: 'jingyan-multi-v2',
        exportedAt: new Date().toISOString(),
        data: multi,
      },
      null,
      2
    );
  }, [multi]);

  const importBackupJson = useCallback((jsonText: string): { ok: boolean; message: string } => {
    try {
      const parsed = JSON.parse(jsonText);
      const payload = parsed.data ?? parsed;
      // Support both v2 multi-course backup and v1 single-course backup!
      if (payload && typeof payload.courses === 'object') {
        const hasValidCompanion =
          payload.companion &&
          typeof payload.companion === 'object' &&
          !Array.isArray(payload.companion);
        setMulti((prev) => ({
          courses: payload.courses,
          settings: { ...DEFAULT_SETTINGS, ...(payload.settings ?? {}) },
          ...(hasValidCompanion
            ? { companion: payload.companion }
            : prev.companion
              ? { companion: prev.companion }
              : {}),
        }));
        return { ok: true, message: '全部专业课板块的学习记录、笔记与养成图鉴已成功恢复！' };
      }
      if (payload && typeof payload.records === 'object') {
        setMulti((prev) => ({
          ...prev,
          courses: {
            ...prev.courses,
            [cid]: {
              records: payload.records ?? {},
              favoriteFormulas: Array.isArray(payload.favoriteFormulas) ? payload.favoriteFormulas : [],
              practiceLogs: Array.isArray(payload.practiceLogs) ? payload.practiceLogs : [],
              mockHistory: Array.isArray(payload.mockHistory) ? payload.mockHistory : [],
              activeMock: payload.activeMock ?? null,
            },
          },
          settings: { ...DEFAULT_SETTINGS, ...(payload.settings ?? prev.settings) },
        }));
        return { ok: true, message: `旧版备份已成功导入至当前板块（${currentCourse.shortLabel}）！` };
      }
      return { ok: false, message: '备份文件格式无法识别' };
    } catch {
      return { ok: false, message: 'JSON 解析失败，请检查备份文件' };
    }
  }, [cid, currentCourse.shortLabel]);

  const resetCurrentCourseProgress = useCallback(() => {
    updateSlice(() => EMPTY_SLICE);
  }, [updateSlice]);

  const scopedState = useMemo<ScopedStudyState>(
    () => ({ ...currentSlice, settings: multi.settings }),
    [currentSlice, multi.settings]
  );

  return (
    <StudyContext.Provider
      value={{
        state: scopedState,
        multiState: multi,
        allCourses: multi.courses,
        companionState: multi.companion,
        setCompanionState,
        replaceMultiState,
        subscribeStudyEvent,
        resolvedTheme,
        getRecord,
        recordAttempt,
        toggleFavorite,
        removeFromWrongBook,
        addToWrongBook,
        saveQuestionNote,
        saveQuestionDraft,
        toggleFavoriteFormula,
        setActiveMock,
        saveMockAttempt,
        trackQuestionReviewed,
        updateSettings,
        exportBackupJson,
        importBackupJson,
        resetCurrentCourseProgress,
      }}
    >
      {children}
    </StudyContext.Provider>
  );
};

export function useStudy(): StudyContextValue {
  const ctx = useContext(StudyContext);
  if (!ctx) throw new Error('useStudy must be used inside StudyProvider');
  return ctx;
}
