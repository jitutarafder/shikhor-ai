import {
  AdminMetrics,
  AdminUser,
  AuditLogItem,
  KnowledgeArticleCreateInput,
  ModerationReportDetail,
} from './types';

export async function getAdminMetricsApi(token: string): Promise<AdminMetrics> {
  const res = await fetch('/api/v1/admin/metrics', {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'সিস্টেম মেট্রিক্স লোড করা যায়নি।');
  }
  return data;
}

export async function getAdminReportsApi(
  token: string,
  statusFilter?: string
): Promise<ModerationReportDetail[]> {
  const url = statusFilter
    ? `/api/v1/admin/reports?status=${statusFilter}`
    : '/api/v1/admin/reports';
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'অভিযোগ তালিকা লোড করা যায়নি।');
  }
  return data;
}

export async function resolveAdminReportApi(
  token: string,
  reportId: string,
  action: 'dismiss' | 'warn' | 'hide_content' | 'suspend_user',
  resolutionNotes: string
): Promise<ModerationReportDetail> {
  const res = await fetch(`/api/v1/admin/reports/${reportId}/resolve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ action, resolutionNotes }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'অভিযোগ নিষ্পত্তি করা সম্ভব হয়নি।');
  }
  return data;
}

export async function getAdminUsersApi(
  token: string,
  roleFilter?: string
): Promise<AdminUser[]> {
  const url = roleFilter ? `/api/v1/admin/users?role=${roleFilter}` : '/api/v1/admin/users';
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'ব্যবহারকারী তালিকা লোড করা যায়নি।');
  }
  return data;
}

export async function toggleUserStatusApi(
  token: string,
  userId: string,
  isActive: boolean,
  reason: string
): Promise<AdminUser> {
  const res = await fetch(`/api/v1/admin/users/${userId}/status`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ isActive, reason }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'ব্যবহারকারীর অবস্থা পরিবর্তন করা যায়নি।');
  }
  return data;
}

export async function toggleUserVerificationApi(
  token: string,
  userId: string,
  isVerified: boolean,
  notes?: string
): Promise<AdminUser> {
  const res = await fetch(`/api/v1/admin/users/${userId}/verify`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ isVerified, notes }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'ব্যবহারকারীর ভেরিফিকেশন পরিবর্তন করা যায়নি।');
  }
  return data;
}

export async function getNidVerificationsApi(
  token: string,
  statusFilter?: string
): Promise<AdminUser[]> {
  const url = statusFilter && statusFilter !== 'all'
    ? `/api/v1/admin/nid-verifications?status=${statusFilter}`
    : '/api/v1/admin/nid-verifications';
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'এনআইডি যাচাই তালিকা লোড করা যায়নি।');
  }
  return data;
}

export async function reviewNidVerificationApi(
  token: string,
  userId: string,
  action: 'approve' | 'reject',
  reason?: string
): Promise<AdminUser> {
  const res = await fetch(`/api/v1/admin/nid-verifications/${userId}/review`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ action, reason }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'এনআইডি যাচাই সিদ্ধান্ত সম্পন্ন করা যায়নি।');
  }
  return data;
}

export async function getAuditLogsApi(token: string): Promise<AuditLogItem[]> {
  const res = await fetch('/api/v1/admin/audit-logs', {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'অডিট লগ লোড করা যায়নি।');
  }
  return data;
}

export async function publishKnowledgeArticleApi(
  token: string,
  input: KnowledgeArticleCreateInput
): Promise<any> {
  const res = await fetch('/api/v1/admin/knowledge', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(input),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'নতুন জ্ঞান প্রকাশ করা সম্ভব হয়নি।');
  }
  return data;
}

export async function getJobStatsApi(token: string) {
  const res = await fetch('/api/v1/jobs/stats', {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'জব কিউ পরিসংখ্যান লোড করা যায়নি।');
  }
  return data;
}

export async function getJobsListApi(token: string, status?: string) {
  const url = status ? `/api/v1/jobs?status=${status}` : '/api/v1/jobs';
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'জব তালিকা লোড করা যায়নি।');
  }
  return data;
}

export async function enqueueJobApi(
  token: string,
  jobType: string,
  payload: Record<string, unknown> = {},
  priority: number = 1
) {
  const res = await fetch('/api/v1/jobs/enqueue', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ job_type: jobType, payload, priority }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'জব যুক্ত করা সম্ভব হয়নি।');
  }
  return data;
}

export async function retryJobApi(token: string, jobId: string) {
  const res = await fetch(`/api/v1/jobs/${jobId}/retry`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'জব পুনরায় চালানো সম্ভব হয়নি।');
  }
  return data;
}

export async function cancelJobApi(token: string, jobId: string) {
  const res = await fetch(`/api/v1/jobs/${jobId}/cancel`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'জব বাতিল করা সম্ভব হয়নি।');
  }
  return data;
}

export async function triggerWorkerTickApi(token: string) {
  const res = await fetch('/api/v1/jobs/run-tick', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'ওয়ার্কার এক্সিকিউট করা সম্ভব হয়নি।');
  }
  return data;
}
