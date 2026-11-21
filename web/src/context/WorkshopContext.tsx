import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import type { InstalledWorkshopPack } from '../types';
import {
  deleteInstalledPack,
  listInstalledPacks,
  loadAllPackBlobs,
  saveInstalledPack,
  setInstalledPackEnabled,
} from '../utils/workshopDb';
import {
  buildInstalledPackRecord,
  parseAndValidateWorkshopZip,
} from '../utils/workshopPack';

interface WorkshopContextValue {
  ready: boolean;
  installedPacks: InstalledWorkshopPack[];
  enabledPacks: InstalledWorkshopPack[];
  installedMap: Record<string, InstalledWorkshopPack>;
  blobUrlsByPack: Record<string, Record<string, string>>;
  installPackFromBytes: (
    bytes: Uint8Array,
    source: 'workshop' | 'local'
  ) => Promise<{ ok: true; pack: InstalledWorkshopPack } | { ok: false; errors: string[] }>;
  togglePackEnabled: (packId: string, enabled?: boolean) => Promise<void>;
  uninstallPack: (packId: string) => Promise<void>;
  resolvePackBlobUrl: (packId: string, relPath: string) => string | undefined;
}

const WorkshopContext = createContext<WorkshopContextValue | null>(null);

function revokeUrlMap(map: Record<string, string> | undefined): void {
  if (!map) return;
  for (const url of Object.values(map)) {
    try {
      URL.revokeObjectURL(url);
    } catch {
      // ignore
    }
  }
}

export const WorkshopProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [ready, setReady] = useState(false);
  const [installedPacks, setInstalledPacks] = useState<InstalledWorkshopPack[]>([]);
  const [blobUrlsByPack, setBlobUrlsByPack] = useState<Record<string, Record<string, string>>>({});
  const blobUrlsRef = useRef<Record<string, Record<string, string>>>({});
  blobUrlsRef.current = blobUrlsByPack;

  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      const packs = await listInstalledPacks();
      const urlMaps: Record<string, Record<string, string>> = {};
      await Promise.all(
        packs.map(async (p) => {
          try {
            const blobs = await loadAllPackBlobs(p.packId);
            const urls: Record<string, string> = {};
            for (const [relPath, blob] of Object.entries(blobs)) {
              urls[relPath] = URL.createObjectURL(blob);
            }
            urlMaps[p.packId] = urls;
          } catch {
            urlMaps[p.packId] = {};
          }
        })
      );

      if (cancelled) {
        for (const m of Object.values(urlMaps)) revokeUrlMap(m);
        return;
      }
      setInstalledPacks(packs);
      setBlobUrlsByPack(urlMaps);
      setReady(true);
    }
    void bootstrap();

    return () => {
      cancelled = true;
      for (const m of Object.values(blobUrlsRef.current)) {
        revokeUrlMap(m);
      }
    };
  }, []);

  const installPackFromBytes = useCallback(
    async (
      bytes: Uint8Array,
      source: 'workshop' | 'local'
    ): Promise<{ ok: true; pack: InstalledWorkshopPack } | { ok: false; errors: string[] }> => {
      const parsedRes = await parseAndValidateWorkshopZip(bytes);
      if (!parsedRes.ok) {
        return parsedRes;
      }

      const { parsed } = parsedRes;
      const record = buildInstalledPackRecord(parsed, source);

      try {
        await saveInstalledPack(record, parsed.blobs);
      } catch (err) {
        return {
          ok: false,
          errors: [
            `写入本地浏览器存储失败：${err instanceof Error ? err.message : '存储空间不足'}`,
          ],
        };
      }

      const newUrls: Record<string, string> = {};
      for (const b of parsed.blobs) {
        newUrls[b.relPath] = URL.createObjectURL(b.blob);
      }

      revokeUrlMap(blobUrlsRef.current[record.packId]);
      setBlobUrlsByPack((prev) => ({
        ...prev,
        [record.packId]: newUrls,
      }));
      setInstalledPacks((prev) => {
        const filtered = prev.filter((p) => p.packId !== record.packId);
        return [record, ...filtered];
      });

      return { ok: true, pack: record };
    },
    []
  );

  const togglePackEnabled = useCallback(
    async (packId: string, nextEnabled?: boolean) => {
      const target = installedPacks.find((p) => p.packId === packId);
      if (!target) return;
      const resolvedEnabled = nextEnabled ?? !target.enabled;
      await setInstalledPackEnabled(packId, resolvedEnabled);
      setInstalledPacks((prev) =>
        prev.map((p) => (p.packId === packId ? { ...p, enabled: resolvedEnabled } : p))
      );
    },
    [installedPacks]
  );

  const uninstallPack = useCallback(async (packId: string) => {
    await deleteInstalledPack(packId);
    revokeUrlMap(blobUrlsRef.current[packId]);
    setBlobUrlsByPack((prev) => {
      const copy = { ...prev };
      delete copy[packId];
      return copy;
    });
    setInstalledPacks((prev) => prev.filter((p) => p.packId !== packId));
  }, []);

  const resolvePackBlobUrl = useCallback(
    (packId: string, relPath: string): string | undefined => {
      if (!relPath) return undefined;
      const clean = relPath.replace(/\\/g, '/').replace(/^\.\//, '').replace(/^\/+/, '');
      return blobUrlsByPack[packId]?.[clean];
    },
    [blobUrlsByPack]
  );

  const enabledPacks = useMemo(
    () => installedPacks.filter((p) => p.enabled),
    [installedPacks]
  );

  const installedMap = useMemo(() => {
    const map: Record<string, InstalledWorkshopPack> = {};
    for (const p of installedPacks) {
      map[p.packId] = p;
    }
    return map;
  }, [installedPacks]);

  const value = useMemo<WorkshopContextValue>(
    () => ({
      ready,
      installedPacks,
      enabledPacks,
      installedMap,
      blobUrlsByPack,
      installPackFromBytes,
      togglePackEnabled,
      uninstallPack,
      resolvePackBlobUrl,
    }),
    [
      ready,
      installedPacks,
      enabledPacks,
      installedMap,
      blobUrlsByPack,
      installPackFromBytes,
      togglePackEnabled,
      uninstallPack,
      resolvePackBlobUrl,
    ]
  );

  return <WorkshopContext.Provider value={value}>{children}</WorkshopContext.Provider>;
};

export function useWorkshop(): WorkshopContextValue {
  const ctx = useContext(WorkshopContext);
  if (!ctx) throw new Error('useWorkshop must be used inside WorkshopProvider');
  return ctx;
}

export function useWorkshopOptional(): WorkshopContextValue | null {
  return useContext(WorkshopContext);
}
