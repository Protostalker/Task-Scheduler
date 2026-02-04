import { useEffect, useMemo, useState } from "react";
import { api } from "../../api";
import { useToast } from "../../components/Toast";
import { formatISODate } from "../../utils/date";

type Company = { id: number; slug: string; name: string };
type User = { id: number; username: string; display_name: string; role: string; disabled: boolean };

type Category = { id: number; name: string; sort_order: number; active: boolean };
type Patient = { id: number; name: string; address: string; phone: string; maps_url: string; active: boolean };

type AdminTaskRow = {
  task_code: string;
  task_num: number;
  company_slug: string;
  assigned_user_id: number;
  assigned_username: string;
  task_date: string;
  task_time?: string | null;
  status: string;
  category: string;
  title: string;
  deleted_at?: string | null;
  forced_done_at?: string | null;
};

function Badge({ text }: { text: string }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        border: "1px solid rgba(255,255,255,0.18)",
        borderRadius: 999,
        fontSize: 12,
        opacity: 0.95,
      }}
    >
      {text}
    </span>
  );
}

export default function AdminTasks() {
  const toast = useToast();

  const [companies, setCompanies] = useState<Company[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [companySlug, setCompanySlug] = useState<string>("");
  const [includeDeleted, setIncludeDeleted] = useState<boolean>(false);

  const [taskList, setTaskList] = useState<AdminTaskRow[]>([]);
  const [loadingTasks, setLoadingTasks] = useState(false);

  const [categories, setCategories] = useState<Category[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);

  // create form
  const [assignees, setAssignees] = useState<number[]>([]);
  const [taskDate, setTaskDate] = useState<string>(formatISODate(new Date()));
  const [taskTime, setTaskTime] = useState<string>("");
  const [category, setCategory] = useState<string>("visits");
  const [title, setTitle] = useState<string>("Patient routine visit");
  const [mapsUrl, setMapsUrl] = useState<string>("");
  const [patientId, setPatientId] = useState<number | "">("");
  const [patientName, setPatientName] = useState<string>("");
  const [patientAddress, setPatientAddress] = useState<string>("");
  const [patientPhone, setPatientPhone] = useState<string>("");
  const [bonusDetails, setBonusDetails] = useState<string>("");

  const activeUsers = useMemo(() => users.filter((u) => !u.disabled), [users]);

  async function refreshTasks(slug?: string) {
    const s = slug ?? companySlug;
    if (!s) return;
    setLoadingTasks(true);
    try {
      const rows = await api.adminListTasks(s, includeDeleted);
      setTaskList(rows as any);
    } catch (e: any) {
      toast.error(String(e?.message ?? e));
    } finally {
      setLoadingTasks(false);
    }
  }

  useEffect(() => {
    (async () => {
      const cs = await api.adminCompanies();
      const us = await api.adminUsers();
      setCompanies(cs as any);
      setUsers(us as any);
      if (cs?.length) setCompanySlug((cs as any)[0].slug);
    })().catch((e) => toast.error(String(e?.message ?? e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    refreshTasks();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companySlug, includeDeleted]);

  useEffect(() => {
    refreshCompanyMeta();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companySlug]);

  async function refreshCompanyMeta() {
    if (!companySlug) return;
    try {
      const cs = await api.adminCategories(companySlug);
      setCategories((cs as any) || []);
      const ps = await api.adminPatients(companySlug);
      setPatients(((ps as any) || []).filter((p:any)=>p.active!==false));
    } catch (e: any) {
      console.error(e);
      // show a toast once; don't spam
      try { toast.error("Failed to load categories/patients for this company"); } catch {}
    }
  }

  // Re-fetch categories/patients when the tab regains focus so newly-added categories
  // show up without having to change the company dropdown.
  useEffect(() => {
    function onFocus() {
      refreshCompanyMeta();
    }
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companySlug]);

  async function createTasks() {
    if (!companySlug) return toast.error("Pick a company");
    if (!assignees.length) return toast.error("Pick at least one assignee");

    try {
      await api.adminCreateTasksBulk({
        company_slug: companySlug,
        assignee_user_ids: assignees,
        task_date: taskDate,
        task_time: taskTime || null,
        category,
        title,
        maps_url: mapsUrl,
        patient_id: patientId === "" ? null : patientId,
        patient_name: patientName,
        patient_address: patientAddress,
        patient_phone: patientPhone,
        bonus_details: bonusDetails,
      });
      toast.success("Created task(s)");
      await refreshTasks(companySlug);
    } catch (e: any) {
      toast.error(String(e?.message ?? e));
    }
  }

  async function doForceDone(taskCode: string, done: boolean) {
    try {
      await api.adminForceDoneTask(taskCode, done);
      toast.success(done ? "Forced done" : "Reopened");
      await refreshTasks(companySlug);
    } catch (e: any) {
      toast.error(String(e?.message ?? e));
    }
  }

  async function doDelete(taskCode: string) {
    if (!confirm(`Delete ${taskCode}?`)) return;
    try {
      await api.adminDeleteTask(taskCode);
      toast.success("Deleted");
      await refreshTasks(companySlug);
    } catch (e: any) {
      toast.error(String(e?.message ?? e));
    }
  }

  return (
    <div className="container">
      <h1>Admin Tasks</h1>
      <p style={{ opacity: 0.85, marginTop: -8 }}>
        View, create, delete, and force-complete tasks for any company.
      </p>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div className="row" style={{ gap: 12 }}>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span style={{ opacity: 0.85 }}>Company</span>
              <select value={companySlug} onChange={(e) => setCompanySlug(e.target.value)}>
                {companies.map((c) => (
                  <option key={c.id} value={c.slug}>
                    {c.name} ({c.slug})
                  </option>
                ))}
              </select>
            </label>

            <label style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 22 }}>
              <input
                type="checkbox"
                checked={includeDeleted}
                onChange={(e) => setIncludeDeleted(e.target.checked)}
              />
              <span style={{ opacity: 0.85 }}>Show deleted</span>
            </label>
          </div>

          <button className="btn" onClick={() => refreshTasks(companySlug)} disabled={loadingTasks}>
            {loadingTasks ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      <div className="grid2" style={{ marginTop: 16 }}>
        <div className="card">
          <h2>Create tasks</h2>

          <div className="row" style={{ gap: 10, flexWrap: "wrap" }}>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span style={{ opacity: 0.85 }}>Task date</span>
              <input type="date" value={taskDate} onChange={(e) => setTaskDate(e.target.value)} />
            </label>

            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span style={{ opacity: 0.85 }}>Task time</span>
              <input type="time" value={taskTime} onChange={(e) => setTaskTime(e.target.value)} />
            </label>

            <label style={{ display: "flex", flexDirection: "column", gap: 6, minWidth: 240 }}>
              <span style={{ opacity: 0.85 }}>Assignees</span>
              <select
                multiple
                value={assignees.map(String)}
                onChange={(e) => {
                  const vals = Array.from(e.target.selectedOptions).map((o) => Number(o.value));
                  setAssignees(vals);
                }}
                style={{ height: 120 }}
              >
                {activeUsers.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.display_name || u.username} (#{u.id})
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="row" style={{ gap: 10, flexWrap: "wrap", marginTop: 10 }}>
            <label style={{ display: "flex", flexDirection: "column", gap: 6, minWidth: 240 }}>
              <span style={{ opacity: 0.85 }}>Category</span>
              <select
                value={category}
                onMouseDown={refreshCompanyMeta}
                onFocus={refreshCompanyMeta}
                onChange={(e) => setCategory(e.target.value)}
              >
                {/* If category is set to something not in the list (legacy/custom), keep it visible */}
                {category && !categories.some((c) => c.name === category) ? (
                  <option value={category}>{category}</option>
                ) : null}
                {categories
                  .slice()
                  .sort((a, b) => a.sort_order - b.sort_order || a.name.localeCompare(b.name))
                  .map((c) => (
                    <option key={c.id} value={c.name}>
                      {c.name}{c.active === false ? " (inactive)" : ""}
                    </option>
                  ))}
              </select>
            </label>

            <label style={{ display: "flex", flexDirection: "column", gap: 6, flex: 1, minWidth: 260 }}>
              <span style={{ opacity: 0.85 }}>Title</span>
              <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Patient routine visit" />
            </label>
          </div>

          <div className="row" style={{ gap: 10, flexWrap: "wrap", marginTop: 10 }}>
            <label style={{ display: "flex", flexDirection: "column", gap: 6, flex: 1, minWidth: 300 }}>
              <span style={{ opacity: 0.85 }}>Maps URL (optional)</span>
              <input value={mapsUrl} onChange={(e) => setMapsUrl(e.target.value)} placeholder="https://maps.google.com/..." />
            </label>
          </div>

          <div className="row" style={{ gap: 10, flexWrap: "wrap", marginTop: 10 }}>
            <label style={{ display: "flex", flexDirection: "column", gap: 6, minWidth: 260 }}>
              <span style={{ opacity: 0.85 }}>Patient (saved)</span>
              <select value={patientId === "" ? "" : String(patientId)} onFocus={refreshCompanyMeta} onChange={(e) => {
                const v = e.target.value;
                if (!v) { setPatientId(""); return; }
                const pid = Number(v);
                setPatientId(pid);
                const p = patients.find((x) => x.id === pid);
                if (p) {
                  setPatientName(p.name || "");
                  setPatientAddress(p.address || "");
                  setPatientPhone(p.phone || "");
                  setMapsUrl(p.maps_url || "");
                }
              }}>
                <option value="">(custom / ad-hoc)</option>
                {patients.map((p) => (<option key={p.id} value={p.id}>{p.name}</option>))}
              </select>
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 6, flex: 1, minWidth: 200 }}>
              <span style={{ opacity: 0.85 }}>Patient name</span>
              <input value={patientName} onChange={(e) => setPatientName(e.target.value)} />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 6, flex: 1, minWidth: 240 }}>
              <span style={{ opacity: 0.85 }}>Address</span>
              <input value={patientAddress} onChange={(e) => setPatientAddress(e.target.value)} />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 6, minWidth: 160 }}>
              <span style={{ opacity: 0.85 }}>Phone</span>
              <input value={patientPhone} onChange={(e) => setPatientPhone(e.target.value)} />
            </label>
          </div>

          <label style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 10 }}>
            <span style={{ opacity: 0.85 }}>Bonus details</span>
            <textarea value={bonusDetails} onChange={(e) => setBonusDetails(e.target.value)} rows={3} />
          </label>

          <div style={{ marginTop: 12 }}>
            <button className="btn primary" onClick={createTasks}>
              Create task(s)
            </button>
          </div>
        </div>

        <div className="card">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h2 style={{ marginBottom: 0 }}>Current tasks</h2>
            <span style={{ opacity: 0.8 }}>{taskList.length} shown</span>
          </div>

          <div style={{ marginTop: 10, overflow: "auto", maxHeight: 520 }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={{ textAlign: "left", padding: "6px 4px", opacity: 0.85 }}>Task</th>
                  <th style={{ textAlign: "left", padding: "6px 4px", opacity: 0.85 }}>Title</th>
                  <th style={{ textAlign: "left", padding: "6px 4px", opacity: 0.85 }}>Assignee</th>
                  <th style={{ textAlign: "left", padding: "6px 4px", opacity: 0.85 }}>Date</th>
                  <th style={{ textAlign: "left", padding: "6px 4px", opacity: 0.85 }}>Status</th>
                  <th style={{ textAlign: "right", padding: "6px 4px", opacity: 0.85 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {taskList.map((t) => {
                  const isDeleted = !!t.deleted_at;
                  const isForced = !!t.forced_done_at;
                  return (
                    <tr key={t.task_code} style={{ borderTop: "1px solid rgba(255,255,255,0.12)", opacity: isDeleted ? 0.55 : 1 }}>
                      <td style={{ padding: "8px 4px", whiteSpace: "nowrap" }}>
                        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                          <strong>{t.task_code}</strong>
                          {isDeleted ? <Badge text="deleted" /> : null}
                          {isForced ? <Badge text="forced" /> : null}
                        </div>
                      </td>
                      <td style={{ padding: "8px 4px" }}>
                        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                          <span>{t.title}</span>
                          <span style={{ opacity: 0.75, fontSize: 12 }}>{t.category}</span>
                        </div>
                      </td>
                      <td style={{ padding: "8px 4px" }}>{t.assigned_username}</td>
                      <td style={{ padding: "8px 4px", whiteSpace: "nowrap" }}>{t.task_date}{t.task_time ? ` ${t.task_time}` : ""}</td>
                      <td style={{ padding: "8px 4px", whiteSpace: "nowrap" }}>{t.status}</td>
                      <td style={{ padding: "8px 4px", textAlign: "right", whiteSpace: "nowrap" }}>
                        <div className="row" style={{ justifyContent: "flex-end", gap: 8 }}>
                          <button
                            className="btn"
                            onClick={() => doForceDone(t.task_code, t.status !== "done")}
                            disabled={isDeleted}
                            title={t.status === "done" ? "Reopen" : "Force done"}
                          >
                            {t.status === "done" ? "Reopen" : "Force done"}
                          </button>
                          <button className="btn" onClick={() => doDelete(t.task_code)} disabled={isDeleted}>
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}

                {!taskList.length && !loadingTasks ? (
                  <tr>
                    <td colSpan={6} style={{ padding: "12px 4px", opacity: 0.8 }}>
                      No tasks found.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
