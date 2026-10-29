import type {
  Profile, Job, Analysis, MatchResult, Assessment, IntelStatus, IntelBundle,
  CommitteeResult, InterviewQuestion, InterviewEvaluation, CareerRadarData, TailoredBulletResult
} from '../types';

import { demoApi } from './demo';

const RAW_BASE = (import.meta.env['VITE_API_BASE_URL'] as string | undefined) || '';
const BASE = RAW_BASE.replace(/\/$/, '');
/** True when no RADIX backend is configured: the in-browser demo engine answers instead. */
export const DEMO_MODE = !BASE;

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, init);
  } catch {
    throw new Error('Could not reach the RADIX API. Ensure the backend is running at http://localhost:8000.');
  }
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try { msg = (await res.json()).detail || msg; } catch {}
    throw new Error(msg);
  }
  return res.json();
}

const json = (method: string, body: unknown) => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});

const form = (path: string, fileOrText: File | string) => {
  const data = new FormData();
  data.append(typeof fileOrText === 'string' ? 'text' : 'file', fileOrText);
  return call<any>(path, { method: 'POST', body: data });
};

const remoteApi = {
  profiles: () => call<Profile[]>('/api/profiles'),
  assessments: () => call<Assessment[]>('/api/assessments'),
  jobs: () => call<Job[]>('/api/jobs'),
  companies: () => call<{ companies: string[]; source: string }>('/api/companies'),
  getProfile: (id: string) => call<Profile>(`/api/profile?candidate_id=${encodeURIComponent(id)}`),
  createProfile: (p: Profile) => call<Profile>('/api/profile', json('POST', p)),
  saveProfile: (p: Profile) => call<Profile>(`/api/profile?candidate_id=${encodeURIComponent(p.id)}`, json('PUT', p)),
  analyzeText: (text: string) => form('/api/jd/analyze', text) as Promise<Analysis>,
  analyzeFile: (file: File) => form('/api/jd/analyze', file) as Promise<Analysis>,
  parseText: (text: string) => form('/api/resume/parse', text),
  parseFile: (file: File) => form('/api/resume/parse', file),
  talent: (candidate_id: string, company: string) => call<any>('/api/talent-check', json('POST', { candidate_id, company })),
  match: (candidate_id: string, job_description_id: string) => call<MatchResult>('/api/skill-match', json('POST', { candidate_id, job_description_id })),
  intelStatus: () => call<IntelStatus>('/api/intelligence/status'),
  intelResearch: (company: string) => call<IntelBundle>('/api/intelligence/research', json('POST', { company })),
  intelCompany: (company: string) => call<IntelBundle>(`/api/intelligence/company/${encodeURIComponent(company)}`),
  // Differentiators: Committee Deliberation, Mock Interview, Career Radar, Resume Tailor
  committeeDeliberate: (candidate_id: string, company: string, role_title?: string, job_description?: string) =>
    call<CommitteeResult>('/api/committee/deliberate', json('POST', { candidate_id, company, role_title, job_description })),
  interviewStart: (candidate_id: string, company: string, round_name?: string) =>
    call<InterviewQuestion>('/api/interview/start', json('POST', { candidate_id, company, round_name })),
  interviewEvaluate: (candidate_id: string, company: string, round_name: string, question: string, answer: string, apply_upgrade: boolean = false) =>
    call<InterviewEvaluation>('/api/interview/evaluate', json('POST', { candidate_id, company, round_name, question, answer, apply_upgrade })),
  careerRadar: (candidate_id: string) =>
    call<CareerRadarData>(`/api/career/radar?candidate_id=${encodeURIComponent(candidate_id)}`),
  tailorBullet: (skill_name: string, target_company?: string, target_bloom?: string) =>
    call<TailoredBulletResult>('/api/resume/tailor-bullet', json('POST', { skill_name, target_company, target_bloom })),
};


export const api: typeof remoteApi = DEMO_MODE ? (demoApi as unknown as typeof remoteApi) : remoteApi;
