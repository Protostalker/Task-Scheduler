import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api';

export default function TaskDetailPage() {
  const { companySlug, taskCode } = useParams();
  const [task, setTask] = React.useState<any|null>(null);
  const [err, setErr] = React.useState<string|null>(null);
  const [busy, setBusy] = React.useState(false);

  const load = React.useCallback(async ()=>{
    if (!companySlug || !taskCode) return;
    try {
      setErr(null);
      const t = await api.taskDetail(companySlug, taskCode);
      setTask(t);
    } catch(e:any) {
      setErr(e.message || 'Failed');
      setTask(null);
    }
  }, [companySlug, taskCode]);

  React.useEffect(() => { load(); }, [load]);

  if (err) {
    return <div className="card">
      <div className="h1">Forbidden / Not found</div>
      <div className="badge attn">{err}</div>
      <div style={{height:12}} />
      <Link className="btn" to={`/company/${companySlug}`}>Back</Link>
    </div>;
  }

  if (!task) return <div className="card">Loading...</div>;

  const done = task.status === 'done';

  return (
    <div className="card">
      <div className="spread">
        <div>
          <div className="h1">{task.title}</div>
          <div className="muted">{task.company_name} · {task.category} · {task.task_date}{task.task_time ? ` · ${task.task_time}` : ""} · {task.task_code}</div>
        </div>
        <span className={"badge " + (done ? "ok" : "attn")}>{done ? "Done" : "!"}</span>
      </div>

      <div className="hr" />

      <div className="kv">
        <div className="muted">Patient</div>
        <div>{task.patient_name || <span className="muted">—</span>}</div>

        <div className="muted">Maps link</div>
        <div>{task.maps_url ? <a className="badge" href={task.maps_url} target="_blank" rel="noreferrer">Open maps</a> : <span className="muted">—</span>}</div>

        <div className="muted">Address</div>
        <div style={{whiteSpace:'pre-wrap'}}>{task.patient_address || <span className="muted">—</span>}</div>

        <div className="muted">Phone</div>
        <div>{task.patient_phone || <span className="muted">—</span>}</div>

        <div className="muted">Bonus details</div>
        <div style={{whiteSpace:'pre-wrap'}}>{task.bonus_details || <span className="muted">—</span>}</div>
      </div>

      <div className="hr" />

      <div className="row" style={{justifyContent:'space-between'}}>
        <Link className="btn" to={`/company/${companySlug}`}>Back</Link>
        <button className={"btn " + (done ? "" : "primary")} disabled={busy} onClick={async ()=>{
          setBusy(true);
          try {
            await api.markDone(companySlug!, taskCode!, !done);
            await load();
          } catch(e:any) {
            alert(e.message || 'Failed');
          } finally { setBusy(false); }
        }}>
          {done ? "Mark not done" : "Mark done"}
        </button>
      </div>
    </div>
  );
}
