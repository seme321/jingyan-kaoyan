import type { InstalledWorkshopPack } from '../types';

const DB_NAME = 'jingyan_workshop_v1';
const DB_VERSION = 1;
const STORE_PACKS = 'packs';
const STORE_BLOBS = 'blobs';

interface WorkshopBlobRecord {
  key: string;
  packId: string;
  relPath: string;
  mimeType: string;
  blob: Blob;
}

function openWorkshopDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') {
      reject(new Error('当前浏览器不支持 IndexedDB 本地资源库'));
      return;
    }
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE_PACKS)) {
        db.createObjectStore(STORE_PACKS, { keyPath: 'packId' });
      }
      if (!db.objectStoreNames.contains(STORE_BLOBS)) {
        const blobStore = db.createObjectStore(STORE_BLOBS, { keyPath: 'key' });
        blobStore.createIndex('by_pack', 'packId', { unique: false });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error ?? new Error('打开 IndexedDB 失败'));
  });
}

function deletePackBlobsInTx(blobStore: IDBObjectStore, packId: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const idx = blobStore.index('by_pack');
    const cursorReq = idx.openCursor(IDBKeyRange.only(packId));
    cursorReq.onsuccess = () => {
      const cursor = cursorReq.result;
      if (!cursor) {
        resolve();
        return;
      }
      cursor.delete();
      cursor.continue();
    };
    cursorReq.onerror = () => reject(cursorReq.error ?? new Error('清理旧资源文件失败'));
  });
}

export async function listInstalledPacks(): Promise<InstalledWorkshopPack[]> {
  try {
    const db = await openWorkshopDb();
    return await new Promise<InstalledWorkshopPack[]>((resolve, reject) => {
      const tx = db.transaction(STORE_PACKS, 'readonly');
      const req = tx.objectStore(STORE_PACKS).getAll();
      req.onsuccess = () => {
        const rows = Array.isArray(req.result) ? (req.result as InstalledWorkshopPack[]) : [];
        rows.sort((a, b) => b.installedAt.localeCompare(a.installedAt));
        resolve(rows);
      };
      req.onerror = () => reject(req.error ?? new Error('读取已安装包列表失败'));
    });
  } catch {
    return [];
  }
}

export async function saveInstalledPack(
  pack: InstalledWorkshopPack,
  blobs: Array<{ relPath: string; mimeType: string; blob: Blob }>
): Promise<void> {
  const db = await openWorkshopDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction([STORE_PACKS, STORE_BLOBS], 'readwrite');
    const packStore = tx.objectStore(STORE_PACKS);
    const blobStore = tx.objectStore(STORE_BLOBS);

    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error('保存资源包到 IndexedDB 失败'));
    tx.onabort = () => reject(tx.error ?? new Error('保存资源包事务被中止'));

    deletePackBlobsInTx(blobStore, pack.packId)
      .then(() => {
        packStore.put(pack);
        for (const b of blobs) {
          const rec: WorkshopBlobRecord = {
            key: `${pack.packId}:${b.relPath}`,
            packId: pack.packId,
            relPath: b.relPath,
            mimeType: b.mimeType,
            blob: b.blob,
          };
          blobStore.put(rec);
        }
      })
      .catch((err) => {
        try {
          tx.abort();
        } catch {
          // ignore
        }
        reject(err);
      });
  });
}

export async function setInstalledPackEnabled(packId: string, enabled: boolean): Promise<void> {
  const db = await openWorkshopDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE_PACKS, 'readwrite');
    const store = tx.objectStore(STORE_PACKS);
    const req = store.get(packId);
    req.onsuccess = () => {
      const existing = req.result as InstalledWorkshopPack | undefined;
      if (existing) {
        store.put({ ...existing, enabled });
      }
    };
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error('更新启用状态失败'));
  });
}

export async function deleteInstalledPack(packId: string): Promise<void> {
  const db = await openWorkshopDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction([STORE_PACKS, STORE_BLOBS], 'readwrite');
    const packStore = tx.objectStore(STORE_PACKS);
    const blobStore = tx.objectStore(STORE_BLOBS);

    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error('卸载资源包失败'));

    packStore.delete(packId);
    deletePackBlobsInTx(blobStore, packId).catch((err) => {
      try {
        tx.abort();
      } catch {
        // ignore
      }
      reject(err);
    });
  });
}

export async function loadAllPackBlobs(packId: string): Promise<Record<string, Blob>> {
  const db = await openWorkshopDb();
  return await new Promise<Record<string, Blob>>((resolve, reject) => {
    const tx = db.transaction(STORE_BLOBS, 'readonly');
    const idx = tx.objectStore(STORE_BLOBS).index('by_pack');
    const req = idx.getAll(IDBKeyRange.only(packId));
    req.onsuccess = () => {
      const result: Record<string, Blob> = {};
      const rows = Array.isArray(req.result) ? (req.result as WorkshopBlobRecord[]) : [];
      for (const r of rows) {
        if (r && r.relPath && r.blob) {
          result[r.relPath] = r.blob;
        }
      }
      resolve(result);
    };
    req.onerror = () => reject(req.error ?? new Error('加载资源包媒体文件失败'));
  });
}
