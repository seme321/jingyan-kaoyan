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
  sourcePackId?: string;
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

export type CardVariant = 'chibi' | 'medium' | 'standard';
export type CardRarity = 'R' | 'SR' | 'SSR' | 'SP';
export type StageFrameId = 'default' | 'abyssal' | 'starlight' | 'hazard';

export interface CodexSource {
  id: string;
  title: string;
  url: string;
  author: string;
  date: string;
  evidence: string;
  limits: string;
}

export interface CodexVariantAsset {
  cardId: string;
  rarity: 'R' | 'SR' | 'SSR';
  label: string;
  sheet: string;
  sprite: string;
  avatar: string;
}

export interface CodexCharacter {
  id: string;
  code: string;
  name: string;
  aliases: string[];
  subtitle: string;
  color: string;
  tags: string[];
  visual: string;
  motif: string;
  hook: string;
  communitySummary: string;
  projectRole: string;
  projectBackground: string;
  personality: string[];
  speechStyle: string;
  relationships: string;
  sources: CodexSource[];
  studyQuotes: string[];
  greetTemplate: string;
  judgeOkQuote: string;
  judgeWarnQuote: string;
  variants: Record<CardVariant, CodexVariantAsset>;
  sourcePackId?: string;
  unlockMode?: CharacterUnlockMode;
}

export interface CodexSpCard {
  id: string;
  code: string;
  name: string;
  subtitle: string;
  role: string;
  color: string;
  tags: string[];
  rarity: 'SP';
  sprite: string;
  avatar: string;
  poses?: Partial<Record<'hero' | 'study' | 'think' | 'cheer', string>>;
  bio: string;
  credit: string;
  greetTemplate: string;
  judgeOkQuote: string;
  judgeWarnQuote: string;
  studyQuotes: string[];
  sourcePackId?: string;
}

export interface CodexCatalog {
  version: number;
  updated: string;
  spCards: CodexSpCard[];
  characters: CodexCharacter[];
}

export interface DailyCompanionProgress {
  date: string;
  checkedIn: boolean;
  practicedQids: string[];
  masteredQids: string[];
  bigQuestionQids: string[];
  wrongClearedQids: string[];
  noteQids: string[];
  formulaFlippedIds: string[];
  microDropQids: string[];
  microDropEarned: number;
  bondDropQids: string[];
  bondDropEarned: number;
  mascotInteracted: boolean;
  claimedMissions: string[];
}

export interface WeeklyCompanionProgress {
  weekKey: string;
  practicedQids: string[];
  mockCount: number;
  activeDays: string[];
  claimedMissions: string[];
}

export interface CompanionState {
  version: number;
  fish: number;
  vouchers: number;
  totalPacksOpened: number;
  pityCounter: number;
  checkInStreak: number;
  lastCheckInDate: string;
  ownedCards: Record<string, number>;
  bonds: Record<string, number>;
  equippedCardId: string;
  applyGlobally: boolean;
  ownedFrames: StageFrameId[];
  equippedFrame: StageFrameId;
  daily: DailyCompanionProgress;
  weekly: WeeklyCompanionProgress;
  claimedAchievements: string[];
}

export type StudyEvent =
  | {
      type: 'attempt';
      courseId: string;
      qid: string;
      status: MasteryStatus;
      prevStatus: MasteryStatus;
      isBigQuestion: boolean;
    }
  | {
      type: 'wrong_cleared';
      courseId: string;
      qid: string;
    }
  | {
      type: 'note_saved';
      courseId: string;
      qid: string;
    }
  | {
      type: 'mock_saved';
      courseId: string;
      year: number;
    }
  | {
      type: 'question_reviewed';
      courseId: string;
      qid: string;
      isBigQuestion: boolean;
    };

export interface MultiCourseStudyState {
  courses: Record<string, CourseStudySlice>;
  settings: AppSettings;
  companion?: CompanionState;
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
export type GuestbookStatus = 'pending' | 'approved' | 'rejected';
export type GuestbookChannel = 'public' | 'inbox';
export type AdminGuestbookTab = 'pending' | 'inbox' | 'approved' | 'rejected' | 'all';

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
  status?: GuestbookStatus;
  channel?: GuestbookChannel;
  adminReply?: string;
  adminRepliedAt?: string;
  isLocal?: boolean;
  isPendingLocal?: boolean;
}

export interface AdminGuestbookEntry extends GuestbookEntry {
  status: GuestbookStatus;
  channel: GuestbookChannel;
  contact?: string;
  reviewedAt?: string;
  hasReceipt?: boolean;
  accountBound?: boolean;
}

export interface AuthUser {
  id: string;
  username: string;
  displayName: string;
  createdAt: string;
  lastLoginAt?: string;
}

export interface CloudSyncMeta {
  version: number;
  updatedAt: string;
  dataSize: number;
}

export interface CloudSyncConflict {
  reason: 'initial' | 'concurrent';
  cloudVersion: number;
  cloudUpdatedAt: string;
  cloudData: MultiCourseStudyState;
}

export type AccountSyncStatus = 'idle' | 'syncing' | 'synced' | 'conflict' | 'error' | 'offline';
export type AccountModalTab = 'sync' | 'inbox' | 'security';

export interface AccountInboxEntry {
  id: string;
  author: string;
  category: GuestbookCategory;
  courseId: string;
  content: string;
  status: GuestbookStatus;
  channel: GuestbookChannel;
  adminReply?: string;
  adminRepliedAt?: string;
  createdAt: string;
  reviewedAt?: string;
}

export interface PrivateInboxEntry {
  id: string;
  receiptToken: string;
  author: string;
  category: GuestbookCategory;
  courseId: string;
  content: string;
  createdAt: string;
  status: GuestbookStatus;
  channel: GuestbookChannel;
  adminReply?: string;
  adminRepliedAt?: string;
  reviewedAt?: string;
  removedOnServer?: boolean;
}

export interface PrivateInboxSyncItem {
  status: GuestbookStatus;
  channel: GuestbookChannel;
  adminReply?: string;
  adminRepliedAt?: string;
  reviewedAt?: string;
}

export interface AdminGuestbookCounts {
  pendingPublic: number;
  pendingInbox: number;
  approved: number;
  inboxAll: number;
  rejected: number;
}

export type WorkshopPackType = 'course' | 'exam' | 'character';
export type CharacterUnlockMode = 'direct' | 'gacha';
export type WorkshopStorageMode = 'd1' | 'url';

export interface WorkshopManifest {
  schemaVersion: 1;
  packId: string;
  type: WorkshopPackType;
  name: string;
  version: string;
  author: string;
  license: string;
  summary: string;
  description?: string;
  tags?: string[];
  cover?: string;
  targetCourseId?: string;
  unlockMode?: CharacterUnlockMode;
}

export interface WorkshopPackStats {
  paperCount?: number;
  questionCount?: number;
  figureCount?: number;
  characterCount?: number;
  spCardCount?: number;
}

export interface WorkshopCatalogItem {
  packId: string;
  type: WorkshopPackType;
  name: string;
  version: string;
  author: string;
  summary: string;
  description: string;
  license: string;
  tags: string[];
  targetCourseId: string;
  unlockMode: CharacterUnlockMode;
  storageMode: WorkshopStorageMode;
  externalUrl?: string;
  fileName: string;
  sizeBytes: number;
  sha256: string;
  coverDataUrl?: string;
  stats: WorkshopPackStats;
  downloads: number;
  featured: boolean;
  published: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface WorkshopCoursePayload {
  course?: CourseMeta;
  targetCourseId?: string;
  chapters?: ChaptersPayload;
  formulas?: FormulaItem[];
  papers: ExamPaper[];
}

export interface WorkshopCharacterPayload {
  unlockMode: CharacterUnlockMode;
  spCards: CodexSpCard[];
  characters: CodexCharacter[];
}

export interface InstalledWorkshopPack {
  packId: string;
  manifest: WorkshopManifest;
  enabled: boolean;
  source: 'workshop' | 'local';
  installedAt: string;
  sizeBytes: number;
  stats: WorkshopPackStats;
  coverRelPath?: string;
  coursePayload?: WorkshopCoursePayload;
  characterPayload?: WorkshopCharacterPayload;
}
