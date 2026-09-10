import axios from 'axios';
import { Client, Project, FileRecord, AuditResult } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- Clients API ---
export async function getClients(): Promise<Client[]> {
  const res = await api.get<Client[]>('/clients/');
  return res.data;
}

export async function createClient(data: { name: string; industry?: string; fiscal_year_end?: string; contact_email?: string }): Promise<Client> {
  const res = await api.post<Client>('/clients/', data);
  return res.data;
}

// --- Projects API ---
export async function getProjects(): Promise<Project[]> {
  const res = await api.get<Project[]>('/projects/');
  return res.data;
}

export async function getProjectById(id: string): Promise<Project> {
  const res = await api.get<Project>(`/projects/${id}`);
  return res.data;
}

export async function createProject(data: { title: string; audit_year: number; client_id: string; description?: string }): Promise<Project> {
  const res = await api.post<Project>('/projects/', data);
  return res.data;
}

export async function updateProject(id: string, data: { title?: string; audit_year?: number; description?: string; status?: string }): Promise<Project> {
  const res = await api.patch<Project>(`/projects/${id}`, data);
  return res.data;
}

export async function deleteProject(id: string): Promise<void> {
  await api.delete(`/projects/${id}`);
}

// --- Files API ---
export async function getFilesForProject(projectId: string): Promise<FileRecord[]> {
  const res = await api.get<FileRecord[]>(`/files/?project_id=${projectId}`);
  return res.data;
}

export async function uploadFile(projectId: string, file: File): Promise<FileRecord> {
  const formData = new FormData();
  formData.append('project_id', projectId);
  formData.append('file', file);

  const res = await api.post<FileRecord>('/files/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data;
}

export async function deleteFile(fileId: string): Promise<void> {
  await api.delete(`/files/${fileId}`);
}

// --- Pipeline & Audit Results API ---
export async function runAuditPipeline(projectId: string): Promise<{ status: string; project_id: string; message: string }> {
  const res = await api.post<{ status: string; project_id: string; message: string }>(`/AuditService/run/${projectId}`);
  return res.data;
}

export async function getAuditResults(projectId: string): Promise<AuditResult> {
  const res = await api.get<AuditResult>(`/AuditService/results/${projectId}`);
  return res.data;
}
