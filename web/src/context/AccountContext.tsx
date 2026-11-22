import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import type {
  AccountInboxEntry,
  AccountModalTab,
  AccountSyncStatus,
  AuthUser,
  CloudSyncConflict,
  CloudSyncMeta,
  MultiCourseStudyState,
} from '../types';
import { useStudy } from './StudyContext';
import {
  changeAccountPassword,
  claimAccountInboxReceipts,
  fetchAccountInbox,
  fetchAuthMe,
  fetchCloudStudyData,
  hasMeaningfulStudyData,
  loginAccount,
  logoutAccount,
  logoutOtherSessions,
  mergeMultiCourseState,
  pushCloudStudyData,
  registerAccount,
  updateAccountProfile,
} from '../utils/account';
import { loadPrivateInboxEntries } from '../utils/guestbook';

interface AccountContextValue {
  user: AuthUser | null;
  authLoading: boolean;
  backendOnline: boolean;
  cloudMeta: CloudSyncMeta | null;
  syncStatus: AccountSyncStatus;
  syncError: string | null;
  syncConflict: CloudSyncConflict | null;
  accountInbox: AccountInboxEntry[];
  inboxLoading: boolean;
  repliedAccountInboxCount: number;
  modalOpen: boolean;
  modalTab: AccountModalTab;
  openAccountModal: (tab?: AccountModalTab) => void;
  closeAccountModal: () => void;
  setModalTab: (tab: AccountModalTab) => void;
  login: (username: string, password: string) => Promise<{ ok: boolean; error?: string }>;
  register: (
    username: string,
    password: string,
    displayName?: string
  ) => Promise<{ ok: boolean; error?: string }>;
  logout: () => Promise<void>;
  logoutOthers: () => Promise<{ ok: boolean; revokedCount?: number; error?: string }>;
  updateProfile: (displayName: string) => Promise<{ ok: boolean; error?: string }>;
  changePassword: (
    currentPassword: string,
    newPassword: string
  ) => Promise<{ ok: boolean; error?: string }>;
  pushToCloud: (force?: boolean) => Promise<{ ok: boolean; error?: string }>;
  pullFromCloud: () => Promise<{ ok: boolean; error?: string }>;
  mergeAndSync: () => Promise<{ ok: boolean; error?: string }>;
  refreshAccountInbox: () => Promise<void>;
}

const AccountContext = createContext<AccountContextValue | null>(null);

function statesMatchCore(a: MultiCourseStudyState, b: MultiCourseStudyState): boolean {
  return (
    JSON.stringify(a.courses ?? {}) === JSON.stringify(b.courses ?? {}) &&
    JSON.stringify(a.companion ?? null) === JSON.stringify(b.companion ?? null)
  );
}

export const AccountProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { multiState, replaceMultiState } = useStudy();
  const multiRef = useRef(multiState);
  multiRef.current = multiState;

  const [user, setUser] = useState<AuthUser | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [backendOnline, setBackendOnline] = useState(true);
  const [cloudMeta, setCloudMeta] = useState<CloudSyncMeta | null>(null);
  const [syncStatus, setSyncStatus] = useState<AccountSyncStatus>('idle');
  const [syncError, setSyncError] = useState<string | null>(null);
  const [syncConflict, setSyncConflict] = useState<CloudSyncConflict | null>(null);
  const [accountInbox, setAccountInbox] = useState<AccountInboxEntry[]>([]);
  const [inboxLoading, setInboxLoading] = useState(false);

  const [modalOpen, setModalOpen] = useState(false);
  const [modalTab, setModalTab] = useState<AccountModalTab>('sync');

  const initializedSyncRef = useRef(false);
  const syncedVersionRef = useRef(0);
  const lastSyncedSnapshotRef = useRef<string | null>(null);
  const skipNextAutoSyncRef = useRef(false);
  const debounceTimerRef = useRef<number | null>(null);
  const lastFocusCheckRef = useRef(0);
  const userRef = useRef<AuthUser | null>(null);
  userRef.current = user;
  const conflictRef = useRef<CloudSyncConflict | null>(null);
  conflictRef.current = syncConflict;

  const refreshAccountInbox = useCallback(async () => {
    if (!userRef.current) {
      setAccountInbox([]);
      return;
    }
    setInboxLoading(true);
    try {
      const res = await fetchAccountInbox();
      if (res.ok) {
        setAccountInbox(res.items);
      }
    } finally {
      setInboxLoading(false);
    }
  }, []);

  const claimAndLoadInbox = useCallback(async () => {
    const localReceipts = loadPrivateInboxEntries();
    if (localReceipts.length > 0) {
      await claimAccountInboxReceipts(localReceipts);
    }
    await refreshAccountInbox();
  }, [refreshAccountInbox]);

  const reconcileOnAuth = useCallback(async () => {
    initializedSyncRef.current = false;
    setSyncStatus('syncing');
    setSyncError(null);
    const cloudRes = await fetchCloudStudyData();
    if (!cloudRes.ok) {
      setSyncStatus(cloudRes.offline ? 'offline' : 'error');
      setSyncError(cloudRes.error);
      if (cloudRes.offline) setBackendOnline(false);
      return;
    }

    const currentLocal = multiRef.current;
    const localMeaningful = hasMeaningfulStudyData(currentLocal);

    if (!cloudRes.hasData || !cloudRes.data) {
      if (localMeaningful) {
        const snapshotStr = JSON.stringify(currentLocal);
        const pushRes = await pushCloudStudyData(currentLocal, 0, true);
        if (pushRes.ok) {
          syncedVersionRef.current = pushRes.version;
          lastSyncedSnapshotRef.current = snapshotStr;
          setCloudMeta({
            version: pushRes.version,
            updatedAt: pushRes.updatedAt,
            dataSize: pushRes.dataSize,
          });
          setSyncConflict(null);
          setSyncStatus('synced');
          initializedSyncRef.current = true;
        } else {
          setSyncStatus('offline' in pushRes && pushRes.offline ? 'offline' : 'error');
          setSyncError(pushRes.error);
        }
      } else {
        syncedVersionRef.current = 0;
        lastSyncedSnapshotRef.current = JSON.stringify(currentLocal);
        setCloudMeta(null);
        setSyncConflict(null);
        setSyncStatus('synced');
        initializedSyncRef.current = true;
      }
      return;
    }

    syncedVersionRef.current = cloudRes.version;
    setCloudMeta({
      version: cloudRes.version,
      updatedAt: cloudRes.updatedAt,
      dataSize: cloudRes.dataSize,
    });

    if (!localMeaningful) {
      skipNextAutoSyncRef.current = true;
      replaceMultiState(cloudRes.data);
      lastSyncedSnapshotRef.current = JSON.stringify(cloudRes.data);
      setSyncConflict(null);
      setSyncStatus('synced');
      initializedSyncRef.current = true;
      return;
    }

    if (statesMatchCore(currentLocal, cloudRes.data)) {
      lastSyncedSnapshotRef.current = JSON.stringify(currentLocal);
      setSyncConflict(null);
      setSyncStatus('synced');
      initializedSyncRef.current = true;
      return;
    }

    setSyncConflict({
      reason: 'initial',
      cloudVersion: cloudRes.version,
      cloudUpdatedAt: cloudRes.updatedAt,
      cloudData: cloudRes.data,
    });
    setSyncStatus('conflict');
    initializedSyncRef.current = false;
  }, [replaceMultiState]);

  useEffect(() => {
    let active = true;
    const bootstrap = async () => {
      const me = await fetchAuthMe();
      if (!active) return;
      if (!me.ok) {
        if (me.offline) {
          setBackendOnline(false);
          setSyncStatus('offline');
        }
        setAuthLoading(false);
        return;
      }
      setBackendOnline(true);
      setUser(me.user);
      setCloudMeta(me.cloudMeta);
      setAuthLoading(false);
      if (me.user) {
        userRef.current = me.user;
        await Promise.all([claimAndLoadInbox(), reconcileOnAuth()]);
      }
    };
    void bootstrap();
    return () => {
      active = false;
    };
  }, [claimAndLoadInbox, reconcileOnAuth]);

  const pushToCloud = useCallback(async (force = false): Promise<{ ok: boolean; error?: string }> => {
    if (!userRef.current) {
      return { ok: false, error: '请先登录账号' };
    }
    if (debounceTimerRef.current !== null) {
      window.clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }
    setSyncStatus('syncing');
    setSyncError(null);
    const snapshotObj = multiRef.current;
    const snapshotStr = JSON.stringify(snapshotObj);
    const res = await pushCloudStudyData(snapshotObj, syncedVersionRef.current, force);
    if (res.ok) {
      syncedVersionRef.current = res.version;
      lastSyncedSnapshotRef.current = snapshotStr;
      setCloudMeta({
        version: res.version,
        updatedAt: res.updatedAt,
        dataSize: res.dataSize,
      });
      setSyncConflict(null);
      setSyncStatus('synced');
      initializedSyncRef.current = true;
      return { ok: true };
    }
    if ('conflict' in res && res.conflict) {
      syncedVersionRef.current = res.version;
      setCloudMeta((prev) => ({
        version: res.version,
        updatedAt: res.updatedAt,
        dataSize: prev?.dataSize ?? 0,
      }));
      setSyncConflict({
        reason: 'concurrent',
        cloudVersion: res.version,
        cloudUpdatedAt: res.updatedAt,
        cloudData: res.data,
      });
      setSyncStatus('conflict');
      initializedSyncRef.current = false;
      return { ok: false, error: res.error };
    }
    setSyncStatus(res.offline ? 'offline' : 'error');
    setSyncError(res.error);
    return { ok: false, error: res.error };
  }, []);

  const pullFromCloud = useCallback(async (): Promise<{ ok: boolean; error?: string }> => {
    if (!userRef.current) {
      return { ok: false, error: '请先登录账号' };
    }
    if (debounceTimerRef.current !== null) {
      window.clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }
    setSyncStatus('syncing');
    setSyncError(null);
    const res = await fetchCloudStudyData();
    if (!res.ok) {
      setSyncStatus(res.offline ? 'offline' : 'error');
      setSyncError(res.error);
      return { ok: false, error: res.error };
    }
    if (!res.hasData || !res.data) {
      setSyncStatus('synced');
      return { ok: false, error: '云端暂无已保存的数据' };
    }
    skipNextAutoSyncRef.current = true;
    replaceMultiState(res.data);
    lastSyncedSnapshotRef.current = JSON.stringify(res.data);
    syncedVersionRef.current = res.version;
    setCloudMeta({
      version: res.version,
      updatedAt: res.updatedAt,
      dataSize: res.dataSize,
    });
    setSyncConflict(null);
    setSyncStatus('synced');
    initializedSyncRef.current = true;
    return { ok: true };
  }, [replaceMultiState]);

  const mergeAndSync = useCallback(async (): Promise<{ ok: boolean; error?: string }> => {
    if (!userRef.current) {
      return { ok: false, error: '请先登录账号' };
    }
    if (debounceTimerRef.current !== null) {
      window.clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }
    setSyncStatus('syncing');
    setSyncError(null);
    const res = await fetchCloudStudyData();
    if (!res.ok) {
      setSyncStatus(res.offline ? 'offline' : 'error');
      setSyncError(res.error);
      return { ok: false, error: res.error };
    }
    const baseData = res.hasData && res.data ? res.data : conflictRef.current?.cloudData ?? null;
    const nextState = baseData ? mergeMultiCourseState(multiRef.current, baseData) : multiRef.current;
    if (baseData) {
      skipNextAutoSyncRef.current = true;
      replaceMultiState(nextState);
    }
    const baseVersion = res.hasData ? res.version : syncedVersionRef.current;
    const pushRes = await pushCloudStudyData(nextState, baseVersion, true);
    if (pushRes.ok) {
      syncedVersionRef.current = pushRes.version;
      lastSyncedSnapshotRef.current = JSON.stringify(nextState);
      setCloudMeta({
        version: pushRes.version,
        updatedAt: pushRes.updatedAt,
        dataSize: pushRes.dataSize,
      });
      setSyncConflict(null);
      setSyncStatus('synced');
      initializedSyncRef.current = true;
      return { ok: true };
    }
    setSyncStatus('offline' in pushRes && pushRes.offline ? 'offline' : 'error');
    setSyncError(pushRes.error);
    return { ok: false, error: pushRes.error };
  }, [replaceMultiState]);

  // Debounced auto-upload on local study/companion changes while logged in
  useEffect(() => {
    if (!user || syncConflict || !initializedSyncRef.current) return;
    const currentSnapshot = JSON.stringify(multiState);
    if (skipNextAutoSyncRef.current) {
      lastSyncedSnapshotRef.current = currentSnapshot;
      skipNextAutoSyncRef.current = false;
      return;
    }
    if (currentSnapshot === lastSyncedSnapshotRef.current) return;

    if (debounceTimerRef.current !== null) {
      window.clearTimeout(debounceTimerRef.current);
    }
    debounceTimerRef.current = window.setTimeout(() => {
      debounceTimerRef.current = null;
      void pushToCloud(false);
    }, 2500);

    return () => {
      if (debounceTimerRef.current !== null) {
        window.clearTimeout(debounceTimerRef.current);
        debounceTimerRef.current = null;
      }
    };
  }, [multiState, user, syncConflict, pushToCloud]);

  // Check for newer cloud versions when returning to the tab
  useEffect(() => {
    if (!user) return;
    const checkCloudUpdates = async () => {
      if (!userRef.current || conflictRef.current || !initializedSyncRef.current) return;
      if (document.visibilityState === 'hidden') return;
      const now = Date.now();
      if (now - lastFocusCheckRef.current < 30_000) return;
      lastFocusCheckRef.current = now;

      const currentSnapshot = JSON.stringify(multiRef.current);
      if (currentSnapshot !== lastSyncedSnapshotRef.current) return;

      const res = await fetchCloudStudyData();
      if (!res.ok || !res.hasData || !res.data) return;
      if (res.version > syncedVersionRef.current) {
        skipNextAutoSyncRef.current = true;
        replaceMultiState(res.data);
        lastSyncedSnapshotRef.current = JSON.stringify(res.data);
        syncedVersionRef.current = res.version;
        setCloudMeta({
          version: res.version,
          updatedAt: res.updatedAt,
          dataSize: res.dataSize,
        });
        setSyncStatus('synced');
      }
    };

    const onFocus = () => void checkCloudUpdates();
    const onVisibility = () => {
      if (document.visibilityState === 'visible') {
        void checkCloudUpdates();
      }
    };
    window.addEventListener('focus', onFocus);
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      window.removeEventListener('focus', onFocus);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [user, replaceMultiState]);

  const login = useCallback(
    async (username: string, password: string): Promise<{ ok: boolean; error?: string }> => {
      const res = await loginAccount({ username, password });
      if (!res.ok) {
        if (res.offline) setBackendOnline(false);
        return { ok: false, error: res.error };
      }
      setBackendOnline(true);
      userRef.current = res.user;
      setUser(res.user);
      setCloudMeta(res.cloudMeta);
      await Promise.all([claimAndLoadInbox(), reconcileOnAuth()]);
      return { ok: true };
    },
    [claimAndLoadInbox, reconcileOnAuth]
  );

  const register = useCallback(
    async (
      username: string,
      password: string,
      displayName?: string
    ): Promise<{ ok: boolean; error?: string }> => {
      const res = await registerAccount({ username, password, displayName });
      if (!res.ok) {
        if (res.offline) setBackendOnline(false);
        return { ok: false, error: res.error };
      }
      setBackendOnline(true);
      userRef.current = res.user;
      setUser(res.user);
      setCloudMeta(null);
      await Promise.all([claimAndLoadInbox(), reconcileOnAuth()]);
      return { ok: true };
    },
    [claimAndLoadInbox, reconcileOnAuth]
  );

  const logout = useCallback(async () => {
    if (debounceTimerRef.current !== null) {
      window.clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }
    await logoutAccount();
    userRef.current = null;
    initializedSyncRef.current = false;
    syncedVersionRef.current = 0;
    lastSyncedSnapshotRef.current = null;
    setUser(null);
    setCloudMeta(null);
    setSyncConflict(null);
    setSyncError(null);
    setSyncStatus('idle');
    setAccountInbox([]);
  }, []);

  const logoutOthers = useCallback(async (): Promise<{
    ok: boolean;
    revokedCount?: number;
    error?: string;
  }> => {
    const res = await logoutOtherSessions();
    if (!res.ok) return { ok: false, error: res.error };
    return { ok: true, revokedCount: res.revokedCount };
  }, []);

  const updateProfile = useCallback(
    async (displayName: string): Promise<{ ok: boolean; error?: string }> => {
      const res = await updateAccountProfile(displayName);
      if (!res.ok) return { ok: false, error: res.error };
      userRef.current = res.user;
      setUser(res.user);
      return { ok: true };
    },
    []
  );

  const changePassword = useCallback(
    async (
      currentPassword: string,
      newPassword: string
    ): Promise<{ ok: boolean; error?: string }> => {
      const res = await changeAccountPassword({ currentPassword, newPassword });
      if (!res.ok) return { ok: false, error: res.error };
      return { ok: true };
    },
    []
  );

  const openAccountModal = useCallback((tab: AccountModalTab = 'sync') => {
    setModalTab(tab);
    setModalOpen(true);
    if (userRef.current) {
      void refreshAccountInbox();
    }
  }, [refreshAccountInbox]);

  const closeAccountModal = useCallback(() => {
    setModalOpen(false);
  }, []);

  const repliedAccountInboxCount = useMemo(
    () => accountInbox.filter((item) => Boolean(item.adminReply)).length,
    [accountInbox]
  );

  return (
    <AccountContext.Provider
      value={{
        user,
        authLoading,
        backendOnline,
        cloudMeta,
        syncStatus,
        syncError,
        syncConflict,
        accountInbox,
        inboxLoading,
        repliedAccountInboxCount,
        modalOpen,
        modalTab,
        openAccountModal,
        closeAccountModal,
        setModalTab,
        login,
        register,
        logout,
        logoutOthers,
        updateProfile,
        changePassword,
        pushToCloud,
        pullFromCloud,
        mergeAndSync,
        refreshAccountInbox,
      }}
    >
      {children}
    </AccountContext.Provider>
  );
};

export function useAccount(): AccountContextValue {
  const ctx = useContext(AccountContext);
  if (!ctx) throw new Error('useAccount must be used inside AccountProvider');
  return ctx;
}
