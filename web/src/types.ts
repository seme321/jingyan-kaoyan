export type QuestionType =
  | 'judge'
  | 'single_choice'
  | 'multi_choice'
  | 'fill'
  | 'term'
  | 'short'
  | 'calc'
  | 'proof';

export const QUESTION_TYPE_LABELS: Record<QuestionType, string> = {
  judge: '判断题',
  single_choice: '单选题',
  multi_choice: '多选题',
  fill: '填空与简答题',
  term: '名词解释',
  short: '简答与分析题',
  calc: '计算题',
  proof: '推导与证明题',
};

export interface ChoiceOption {
  label: string; // 'A' | 'B' | 'C' | 'D'
  text: string;
}

export interface QuestionFigure {
  src: string;
  caption: string;
}

export interface RubricItem {
  label: string;
  pts: number;
}

export interface Question {
  id: string;
  year: number;
  no: number;
  type: QuestionType;
  subType?: 'blank' | 'mini-calc' | 'short-answer';
  score: number;
  title: string;
  stem: string;
  options?: ChoiceOption[];
  choiceAnswer?: string; // e.g. 'B' or 'ACD'
  note: string;
  figures: QuestionFigure[];
  shortAnswer: string;
  judgeAnswer: boolean | null;
  answer: string;
  analysis: string;
  analysisFigures: QuestionFigure[];
  pitfalls: string;
  chapter: number;
  kps: string[];
  method: string;
  difficulty: number;
  rubric?: RubricItem[];
}

export interface ExamSection {
  id: string;
  title: string;
  description: string;
  range: [number, number];
  scorePerQuestion?: number;
  totalScore: number;
}

export interface ExamPaper {
  year: number;
  code: string;
  subject: string;
  school: string;
  totalScore: number;
  durationMinutes: number;
  calculatorAllowed: boolean;
  examNotes: string[];
  sections: ExamSection[];
  questions: Question[];
}

export interface CourseMeta {
  id: string;
  name: string;
  shortLabel: string;
  school: string;
  code: string;
  subject: string;
  category: string;
  examMetaBadge: string;
  status: 'ready' | 'preparing';
  description: string;
}

export interface CoursesCatalog {
  defaultCourseId: string;
  courses: CourseMeta[];
}

export interface ExamYearMeta {
  year: number;
  title: string;
  questionCount: number;
  totalScore: number;
  figureCount: number;
  status: 'ready' | 'planned';
  dataFile: string;
}

export interface ChapterInfo {
  chapter: number;
  name: string;
  fullTitle: string;
  questionTypes: string;
  scoreRange?: [number, number];
  scoreLabel: string;
  stars: number;
  hasBigQuestion: boolean;
  summary: string;
  coreKps: string[];
}

export interface ChaptersPayload {
  syllabusTitle: string;
  textbook: string;
  highlights: string[];
  omittedChapterNote?: string;
  chapters: ChapterInfo[];
}

export interface FormulaItem {
  id: string;
  chapter: number;
  name: string;
  latex: string;
  variables: string;
  note: string;
}

export type MasteryStatus = 'unseen' | 'mastered' | 'partial' | 'wrong';

export interface QuestionRecord {
  status: MasteryStatus;
  inWrongBook: boolean;
  favorite: boolean;
  attempts: number;
  wrongCount: number;
  lastJudgeChoice?: boolean | null;
  lastChoice?: string;
  userDraft?: string;
  note?: string;
  updatedAt: number;
}

export interface PracticeLogItem {
  id: string;
  qid: string;
  result: MasteryStatus;
  timestamp: number;
}

export interface SectionScoreSummary {
  id: string;
  title: string;
  earned: number;
  max: number;
}

export interface MockAttempt {
  id: string;
  year: number;
  startedAt: number;
  submittedAt: number;
  elapsedSeconds: number;
  totalScore: number;
  maxScore: number;
  sectionScores?: SectionScoreSummary[];
  judgeScore?: number;
  fillScore?: number;
  calcScore?: number;
  scoresByQid: Record<string, number>;
  answersByQid: Record<string, string>;
}

export interface ActiveMockSession {
  year: number;
  startedAt: number;
  elapsedSeconds: number;
  phase: 'answering' | 'grading';
  judgeChoices: Record<string, boolean | null>;
  choiceAnswers?: Record<string, string>;
  textAnswers: Record<string, string>;
  flagged: Record<string, boolean>;
  selfScores: Record<string, number>;
  rubricChecks: Record<string, boolean[]>;
}

export type DiagramDarkMode = 'blueprint' | 'soft' | 'original';

export interface AppSettings {
  theme: 'dark' | 'light' | 'system';
  fontSize: 'md' | 'lg' | 'xl' | '2xl';
  fontFamily: 'sans' | 'serif';
  hideTagsBeforeAnswer: boolean;
  softDiagramInDark: boolean;
  diagramDarkMode?: DiagramDarkMode;
  animatedBg?: boolean;
}

export interface CourseStudySlice {
  records: Record<string, QuestionRecord>;
  favoriteFormulas: string[];
  practiceLogs: PracticeLogItem[];
  mockHistory: MockAttempt[];
  activeMock: ActiveMockSession | null;
}

export interface MultiCourseStudyState {
  courses: Record<string, CourseStudySlice>;
  settings: AppSettings;
}

export interface AnnouncementItem {
  id: string;
  date: string;
  tag: string;
  pinned?: boolean;
  title: string;
  summary: string;
  highlights: string[];
  relatedCourses?: string[];
}

export type GuestbookCategory = 'checkin' | 'errata' | 'wish' | 'chat';

export interface GuestbookEntry {
  id: string;
  author: string;
  role?: 'admin' | 'assistant' | 'user';
  category: GuestbookCategory;
  courseId: string;
  content: string;
  createdAt: string;
  likes: number;
  pinned?: boolean;
  isLocal?: boolean;
}
