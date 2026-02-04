import React from 'react';
import { api } from '../../api';

export default function StatsHome() {
  const [rows, setRows] = React.useState<any[]>([]);
  const [err, setErr] = React.useState<string|null>(null);

  React.useEffect(() => {
    (async ()=>{
      try {
        setErr(null);
        const r = await api.statsAudit(200);
        setRows(r);
      } catch(e:any) {
        setErr(e.message || 'Failed');
      }
    })();
  }, []);

  return (
    <div>
      <div className="h1">Stats & Logs</div>
      <div className="muted">Audit logs live here. This MVP intentionally avoids storing PHI in log metadata.</div>
      <div style={{height:12}} />
      {err && <div className="card"><span className="badge attn">Error: {err}</span></div>}
      <div className="card">
        <div className="h2">Recent audit events</div>
        <div className="hr" />
        <div style={{overflowX:'auto'}}>
          <table style={{width:'100%', borderCollapse:'collapse', fontSize:13}}>
            <thead>
              <tr>
                <th style={{textAlign:'left', padding:'8px', borderBottom:'1px solid var(--border)'}}>Time</th>
                <th style={{textAlign:'left', padding:'8px', borderBottom:'1px solid var(--border)'}}>Action</th>
                <th style={{textAlign:'left', padding:'8px', borderBottom:'1px solid var(--border)'}}>Actor</th>
                <th style={{textAlign:'left', padding:'8px', borderBottom:'1px solid var(--border)'}}>Target</th>
                <th style={{textAlign:'left', padding:'8px', borderBottom:'1px solid var(--border)'}}>Company</th>
                <th style={{textAlign:'left', padding:'8px', borderBottom:'1px solid var(--border)'}}>Task</th>
                <th style={{textAlign:'left', padding:'8px', borderBottom:'1px solid var(--border)'}}>IP</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i}>
                  <td style={{padding:'8px', borderBottom:'1px solid var(--border)'}}>{r.timestamp}</td>
                  <td style={{padding:'8px', borderBottom:'1px solid var(--border)'}}><span className="badge">{r.action}</span></td>
                  <td style={{padding:'8px', borderBottom:'1px solid var(--border)'}}>{r.actor_user_id ?? '—'}</td>
                  <td style={{padding:'8px', borderBottom:'1px solid var(--border)'}}>{r.target_user_id ?? '—'}</td>
                  <td style={{padding:'8px', borderBottom:'1px solid var(--border)'}}>{r.company_id ?? '—'}</td>
                  <td style={{padding:'8px', borderBottom:'1px solid var(--border)'}}>{r.task_id ?? '—'}</td>
                  <td style={{padding:'8px', borderBottom:'1px solid var(--border)'}}>{r.ip || '—'}</td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr><td colSpan={7} style={{padding:'10px'}} className="muted">No events yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
