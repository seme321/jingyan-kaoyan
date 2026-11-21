import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type {
  ActiveMockSession,
  AppSettings,
  CourseStudySlice,
  MasteryStatus,
  MockAttempt,
  MultiCourseStudyState,
  QuestionRecord,
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
  updateSettings: (patch: Partial<AppSettings>) => void;
  exportBackupJson: () => string;
  importBackupJson: (jsonText: string) => { ok: boolean; message: string };
  resetCurrentCourseProgress: () => void;
}

const StudyContext = createContext<StudyContextValue | null>(null);

export const StudyProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { currentCourse } = useData();
  const cid = currentCourse.id;
  const [multi, setMulti] = useState<MultiCourseStudyState>(loadInitialMultiState);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_V2, JSON.stringify(multi));
    } catch {
      // ignore quota errors
    }
  }, [multi]);

  useEffect(() => {
    const root = document.documentElement;
    const { theme, fontSize, fontFamily } = multi.settings;
    const media = window.matchMedia('(prefers-color-scheme: light)');

    const applyTheme = () => {
      const resolvedTheme: 'dark' | 'light' =
        theme === 'system' ? (media.matches ? 'light' : 'dark') : theme;
      root.setAttribute('data-theme', resolvedTheme);
      root.setAttribute('data-font-size', fontSize);
      root.setAttribute('data-font-family', fontFamily);
      const metaTheme = document.querySelector('meta[name="theme-color"]');
      if (metaTheme) {
        metaTheme.setAttribute('content', resolvedTheme === 'dark' ? '#06101f' : '#eef6ff');
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
    },
    [updateSlice]
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
    },
    [updateSlice]
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
    },
    [updateSlice]
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
    },
    [updateSlice]
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
        setMulti({
          courses: payload.courses,
          settings: { ...DEFAULT_SETTINGS, ...(payload.settings ?? {}) },
        });
        return { ok: true, message: '全部专业课板块的学习记录与笔记已成功恢复！' };
      }
      if (payload && typeof payload.records === 'object') {
        setMulti((prev) => ({
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
