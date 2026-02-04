import React from 'react';
import { api } from '../../api';

export default function AdminUsers() {
  const [users, setUsers] = React.useState<any[]>([]);
  const [companies, setCompanies] = React.useState<Array<{id:number;slug:string;name:string}>>([]);
  const [editUser, setEditUser] = React.useState<any|null>(null);
  const [editSlugs, setEditSlugs] = React.useState<string[]>([]);
  const [err, setErr] = React.useState<string|null>(null);
  const [temp, setTemp] = React.useState<Record<number,string>>({});
  const [mmDraft, setMmDraft] = React.useState<Record<number,string>>({});

  const load = React.useCallback(async ()=>{
    try {
      setErr(null);
      const uu = await api.adminUsers();
      setUsers(uu);
      setMmDraft(prev => {
        const next = { ...prev };
        for (const u of uu) if (next[u.id] === undefined) next[u.id] = u.mattermost_id || "";
        return next;
      });
    }
    catch(e:any) { setErr(e.message || 'Failed'); }
  }, []);

  React.useEffect(()=>{ load(); }, [load]);

  React.useEffect(() => {
    api.adminCompanies().then(setCompanies).catch(()=>{});
  }, []);

  return (
    <div>
      <div className="h1">Users</div>
      <div className="muted">Users cannot be deleted in UI. Disable instead. Super admin is DB-only for password changes.</div>
      <div style={{height:12}} />

      {err && <div className="card"><span className="badge attn">Error: {err}</span></div>}

      <div className="list">
        {users.map(u => (
          <div key={u.id} className="card">
            <div className="spread">
              <div>
                <div className="h2">{u.display_name || u.username}</div>
                <div className="muted">{u.username} · id {u.id}</div>
              </div>
              <div className="row">
                <span className="badge">{u.role}</span>
                {u.disabled && <span className="badge attn">disabled</span>}
              </div>
            </div>

            <div className="hr" />

            <div className="row" style={{flexWrap:'wrap', gap:10, alignItems:'end'}}>
              <div className="field" style={{minWidth:260, flex:1}}
                ><label>Mattermost ID</label>
                <input value={mmDraft[u.id] ?? (u.mattermost_id || "")} onChange={e=>setMmDraft(prev=>({...prev,[u.id]: e.target.value}))} placeholder="e.g., user-id or username" />
              </div>
              <button className="btn" onClick={async ()=>{
                try {
                  await api.adminUpdateUser(u.id, { mattermost_id: mmDraft[u.id] ?? "" });
                  await load();
                  alert("Saved");
                } catch(e:any) { alert(e.message || "Failed"); }
              }}>Save Mattermost ID</button>
            </div>

            <div className="row" style={{flexWrap:'wrap'}}>
              <button className="btn" onClick={async ()=>{
                try {
                  const detail = await api.adminUserDetail(u.id);
                  setEditUser(u);
                  setEditSlugs(detail.company_slugs || []);
                } catch(e:any) { alert(e.message || 'Failed'); }
              }}>Company access</button>

              <button className="btn" onClick={async ()=>{
                try {
                  const r = await api.adminResetPassword(u.id);
                  setTemp(prev => ({...prev, [u.id]: r.temp_password}));
                } catch(e:any) { alert(e.message || 'Failed'); }
              }}>Reset password</button>

              <button className={"btn " + (u.disabled ? "" : "danger")} onClick={async ()=>{
                try {
                  await api.adminDisableUser(u.id, !u.disabled);
                  await load();
                } catch(e:any) { alert(e.message || 'Failed'); }
              }}>{u.disabled ? "Enable" : "Disable"}</button>

              <select defaultValue={u.role} onChange={async (e)=>{
                try {
                  await api.adminSetRole(u.id, e.target.value);
                  await load();
                } catch(e:any) { alert(e.message || 'Failed'); await load(); }
              }}>
                <option value="employee">employee</option>
                <option value="admin">admin</option>
                <option value="super_admin">super_admin</option>
              </select>
            </div>

            {temp[u.id] && (
              <div style={{marginTop:10}} className="badge ok">
                Temp password: <span style={{fontFamily:'monospace'}}>{temp[u.id]}</span> (forces change on next login)
              </div>
            )}
          </div>
        ))}
      </div>

      {editUser && (
        <div className="card" style={{marginTop:16}}>
          <div className="spread">
            <div>
              <div className="h2">Company access — {editUser.display_name || editUser.username}</div>
              <div className="muted">Select which companies this user can see on the employee dashboard.</div>
            </div>
            <button className="btn" onClick={()=>setEditUser(null)}>Close</button>
          </div>
          <div className="hr" />
          <div className="grid" style={{gridTemplateColumns:'repeat(auto-fit, minmax(240px, 1fr))'}}>
            {companies.map(c => {
              const checked = editSlugs.includes(c.slug);
              return (
                <label key={c.id} className="badge" style={{display:'flex', gap:10, alignItems:'center', justifyContent:'space-between'}}>
                  <span>{c.name} <span className="muted">({c.slug})</span></span>
                  <input type="checkbox" checked={checked} onChange={e=>{
                    setEditSlugs(prev => e.target.checked ? [...prev, c.slug] : prev.filter(s=>s!==c.slug));
                  }} />
                </label>
              );
            })}
          </div>
          <div style={{height:12}} />
          <div className="row">
            <button className="btn primary" onClick={async ()=>{
              try {
                await api.adminSetUserCompanies(editUser.id, editSlugs);
                setEditUser(null);
              } catch(e:any) { alert(e.message || 'Failed'); }
            }}>Save</button>
            <button className="btn" onClick={()=>{ setEditSlugs([]); }}>Clear</button>
          </div>
        </div>
      )}
    </div>
  );
}
