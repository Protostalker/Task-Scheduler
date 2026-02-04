// Central API wrapper for the Salkhorian Design Task Scheduler web UI.
//
// IMPORTANT: Some routes call api.login(username, password) while other code calls
// api.login({username, password}). We support both.

export type Me = {
  id: number;
  username: string;
  display_name: string;
  role: string;
  must_change_password: boolean;
  disabled: boolean;
};

const API_BASE: string = (((import.meta as any).env?.VITE_API_BASE as string) || "").replace(/\/$/, "");

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    },
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || res.statusText);
  }

  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return (await res.json()) as T;
  return (await res.text()) as unknown as T;
}

// -------- Auth --------

export async function login(username: string, password: string): Promise<{ ok: boolean }>;
export async function login(payload: { username: string; password: string }): Promise<{ ok: boolean }>;
export async function login(a: any, b?: any): Promise<{ ok: boolean }> {
  const payload = typeof a === "string" ? { username: a, password: String(b ?? "") } : a;
  return req("/api/auth/login", { method: "POST", body: JSON.stringify(payload) });
}

export async function logout(): Promise<{ ok: boolean }> {
  return req("/api/auth/logout", { method: "POST" });
}

export async function me(): Promise<Me> {
  return req<Me>("/api/me");
}

export async function changePassword(newPassword: string): Promise<{ ok: boolean }> {
  return req<{ ok: boolean }>("/api/auth/change_password", {
    method: "POST",
    body: JSON.stringify({ new_password: newPassword }),
  });
}

// -------- Employee routes --------

export async function companies(): Promise<any[]> {
  return req<any[]>("/api/companies");
}

export async function pushTest(): Promise<{ ok: boolean }> {
  return req<{ ok: boolean }>("/api/push/test", { method: "POST" });
}

export async function companyTasks(companySlug: string): Promise<any[]> {
  return req<any[]>(`/api/company/${encodeURIComponent(companySlug)}/tasks`);
}

export async function taskDetail(companySlug: string, taskCode: string): Promise<any> {
  return req<any>(`/api/company/${encodeURIComponent(companySlug)}/tasks/${encodeURIComponent(taskCode)}`);
}

export async function markDone(companySlug: string, taskCode: string, done: boolean, note?: string): Promise<any> {
  return req<any>(`/api/company/${encodeURIComponent(companySlug)}/tasks/${encodeURIComponent(taskCode)}/done`, {
    method: "POST",
    body: JSON.stringify({ done, note: note || "" }),
  });
}

// -------- Stats --------

export async function statsAudit(limit: number = 200): Promise<any[]> {
  return req<any[]>(`/api/stats/audit?limit=${encodeURIComponent(String(limit))}`);
}

// -------- Admin: Companies --------

export async function adminCompanies(): Promise<any[]> {
  return req<any[]>("/api/admin/companies");
}

export async function adminCreateCompany(slug: string, name: string): Promise<any> {
  return req<any>("/api/admin/companies", {
    method: "POST",
    body: JSON.stringify({ slug, name }),
  });
}

// -------- Admin: Users --------

export async function adminUsers(): Promise<any[]> {
  return req<any[]>("/api/admin/users");
}

export async function adminUserDetail(userId: number): Promise<any> {
  return req<any>(`/api/admin/users/${userId}`);
}

export async function adminCreateUser(payload: any): Promise<any> {
  return req<any>("/api/admin/users", { method: "POST", body: JSON.stringify(payload) });
}

export async function adminResetPassword(userId: number): Promise<{ temp_password: string }> {
  return req<{ temp_password: string }>(`/api/admin/users/${userId}/reset_password`, { method: "POST" });
}

export async function adminDisableUser(userId: number, disabled: boolean): Promise<{ ok: boolean }> {
  return req<{ ok: boolean }>(`/api/admin/users/${userId}/disable`, {
    method: "POST",
    body: JSON.stringify({ disabled }),
  });
}

export async function adminUpdateUser(userId: number, payload: { display_name?: string | null; mattermost_id?: string | null }): Promise<any> {
  return req<any>(`/api/admin/users/${userId}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export async function adminSetRole(userId: number, role: string): Promise<{ ok: boolean }> {
  return req<{ ok: boolean }>(`/api/admin/users/${userId}/role`, {
    method: "POST",
    body: JSON.stringify({ role }),
  });
}

export async function adminSetUserCompanies(userId: number, company_slugs: string[]): Promise<any> {
  return req<any>(`/api/admin/users/${userId}/companies`, {
    method: "PUT",
    body: JSON.stringify({ company_slugs }),
  });
}

// -------- Admin: Tasks --------

export async function adminCreateTasksBulk(payload: any): Promise<any> {
  return req<any>("/api/admin/tasks/bulk", { method: "POST", body: JSON.stringify(payload) });
}

export async function adminListTasks(companySlug: string, includeDeleted: boolean = false): Promise<any[]> {
  const qs = new URLSearchParams({ company_slug: companySlug, include_deleted: includeDeleted ? "true" : "false" });
  return req<any[]>(`/api/admin/tasks?${qs.toString()}`);
}

export async function adminDeleteTask(taskCode: string): Promise<any> {
  return req<any>(`/api/admin/tasks/${encodeURIComponent(taskCode)}`, {
    method: "DELETE",
  });
}

export async function adminForceDoneTask(taskCode: string, done: boolean): Promise<any> {
  return req<any>(`/api/admin/tasks/${encodeURIComponent(taskCode)}/force_done`, {
    method: "POST",
    body: JSON.stringify({ done }),
  });
}

// -------- Admin: Categories (USED BY AdminCompanies) --------

export type AdminCategory = {
  id: number;
  name: string;
  sort_order: number;
  active: boolean;
};

export async function adminCategories(companySlug: string): Promise<AdminCategory[]> {
  return req<AdminCategory[]>(`/api/admin/companies/${encodeURIComponent(companySlug)}/categories`);
}

export async function adminCreateCategory(
  companySlug: string,
  payload: { name: string; sort_order?: number }
): Promise<AdminCategory> {
  return req<AdminCategory>(`/api/admin/companies/${encodeURIComponent(companySlug)}/categories`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function adminUpdateCategory(
  categoryId: number,
  payload: Partial<{ name: string; sort_order: number; active: boolean }>
): Promise<{ ok: boolean }> {
  return req<{ ok: boolean }>(`/api/admin/categories/${categoryId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

// -------- Admin: Patients (USED BY AdminCompanies) --------

export type AdminPatient = {
  id: number;
  name: string;
  phone: string;
  address: string;
  maps_url: string;
  notes: string;
  active: boolean;
};

export async function adminPatients(companySlug: string, includeInactive: boolean = false): Promise<AdminPatient[]> {
  const qs = new URLSearchParams({ include_inactive: includeInactive ? "true" : "false" });
  return req<AdminPatient[]>(`/api/admin/companies/${encodeURIComponent(companySlug)}/patients?${qs.toString()}`);
}

export async function adminCreatePatient(companySlug: string, payload: any): Promise<AdminPatient> {
  return req<AdminPatient>(`/api/admin/companies/${encodeURIComponent(companySlug)}/patients`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function adminUpdatePatient(patientId: number, payload: any): Promise<{ ok: boolean }> {
  return req<{ ok: boolean }>(`/api/admin/patients/${patientId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

// Convenience object import style: import { api } from './api'
export const api = {
  // auth
  login,
  logout,
  me,
  changePassword,

  // employee
  companies,
  myCompanies: companies,
  pushTest,
  companyTasks,
  taskDetail,
  markDone,

  // stats
  statsAudit,

  // admin: companies
  adminCompanies,
  adminCreateCompany,

  // admin: users
  adminUsers,
  adminUserDetail,
  adminCreateUser,
  adminResetPassword,
  adminDisableUser,
  adminUpdateUser,
  adminSetRole,
  adminSetUserCompanies,

  // admin: tasks
  adminCreateTasksBulk,
  adminListTasks,
  adminDeleteTask,
  adminForceDoneTask,

  // admin: categories
  adminCategories,
  adminCreateCategory,
  adminUpdateCategory,

  // admin: patients
  adminPatients,
  adminCreatePatient,
  adminUpdatePatient,
};
