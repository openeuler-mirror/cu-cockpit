import Cookies from 'js-cookie';
import request from '/@/utils/request';

export const MAX_BACKUP_BYTES = 256 * 1024 * 1024;
export type BackupStatus = 'queued' | 'running' | 'succeeded' | 'failed';
export type RestoreStatus = 'awaiting_confirmation' | 'awaiting_maintenance' | 'running' | 'completed' | 'failed' | 'manual_recovery_required';

export interface BackupArchive {
  archive_id: string;
  application_version: string;
  actor: string;
  size: number;
}

export interface BackupTask {
  id: string;
  kind: 'backup' | 'restore';
  status: BackupStatus | RestoreStatus;
  phase?: string;
  error?: string;
  requires_manual_recovery?: boolean;
  safety_archive_id?: string;
  created_at: string;
  started_at?: string;
  finished_at?: string;
  archive_id?: string;
  expires_at?: string;
  confirmed_at?: string;
}

export interface BackupSchedule {
  enabled: boolean;
  time: string;
  timezone: string;
  next_run: string | null;
}

export interface BackupOverview {
  available: true;
  backups: BackupArchive[];
  tasks: BackupTask[];
  schedule: BackupSchedule;
  capabilities: { create: boolean; verify: boolean; schedule: boolean; create_reason: string | null };
}

export interface RestorePreflight {
  task_id: string;
  token: string;
  expires_at: string;
  preview: {
    members: Record<string, { size: number; sha256: string }>;
    total_size: number;
    targets: string[];
    services: string[];
    requires_maintenance: boolean;
    risks: string[];
  };
}

const base = '/system/backups';
const csrf = () => ({ 'X-CSRFToken': Cookies.get('csrftoken') || '' });

export const getBackupOverview = (): Promise<BackupOverview> => request<BackupOverview, BackupOverview>({
  url: `${base}/overview`, method: 'get', withCredentials: true,
});

export const createBackup = (): Promise<{ task: BackupTask }> => request<{ task: BackupTask }, { task: BackupTask }>({
  url: `${base}/create`, method: 'post', data: {}, withCredentials: true, headers: csrf(),
});

export const importBackup = (file: File): Promise<{ backup: BackupArchive }> => {
  const data = new FormData();
  data.append('file', file);
  return request<{ backup: BackupArchive }, { backup: BackupArchive }>({
    url: `${base}/import`, method: 'post', data, withCredentials: true,
    headers: { ...csrf(), 'Content-Type': undefined },
  });
};

export const saveBackupSchedule = (data: Pick<BackupSchedule, 'enabled' | 'time' | 'timezone'>): Promise<{ schedule: BackupSchedule }> => request<{ schedule: BackupSchedule }, { schedule: BackupSchedule }>({
  url: `${base}/schedule`, method: 'post', data, withCredentials: true, headers: csrf(),
});

export const verifyBackup = (archive_id: string): Promise<{ archive_id: string; members: string[]; total_size: number }> => request<{ archive_id: string; members: string[]; total_size: number }, { archive_id: string; members: string[]; total_size: number }>({
  url: `${base}/verify`, method: 'post', data: { archive_id }, withCredentials: true, headers: csrf(),
});

export const downloadBackup = (archive_id: string): Promise<Blob> => request<Blob, Blob>({
  url: `${base}/download/${encodeURIComponent(archive_id)}`, method: 'get',
  responseType: 'blob', withCredentials: true,
});

export const preflightRestore = (archive_id: string): Promise<RestorePreflight> => request<RestorePreflight, RestorePreflight>({
  url: `${base}/restore/preflight`, method: 'post', data: { archive_id }, withCredentials: true, headers: csrf(),
});

export const confirmRestore = (task_id: string, token: string): Promise<{ task: Pick<BackupTask, 'id' | 'status'> }> => request<{ task: Pick<BackupTask, 'id' | 'status'> }, { task: Pick<BackupTask, 'id' | 'status'> }>({
  url: `${base}/restore/confirm`, method: 'post', data: { task_id, token }, withCredentials: true, headers: csrf(),
});