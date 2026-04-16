const STORAGE_KEY = "customs-brain-jobs";
const MAX_JOBS = 12;

export function getRecentJobs() {
  try {
    const payload = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(payload) ? payload : [];
  } catch {
    return [];
  }
}

export function upsertJob(job) {
  const existingJobs = getRecentJobs().filter((item) => item.job_id !== job.job_id);
  const nextJobs = [
    {
      ...job,
      last_updated_at: new Date().toISOString(),
    },
    ...existingJobs,
  ].slice(0, MAX_JOBS);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(nextJobs));
  return nextJobs;
}
