import React from 'react';
import { api } from '../../api';

export default function AdminSignUp() {
  const [username, setUsername] = React.useState('');
  const [display, setDisplay] = React.useState('');
  const [mattermostId, setMattermostId] = React.useState('');
  const [role, setRole] = React.useState('employee');
  const [password, setPassword] = React.useState('');
  const [companySlugs, setCompanySlugs] = React.useState<string[]>([]);
  const [companies, setCompanies] = React.useState<Array<{id:number;slug:string;name:string}>>([]);
  const [msg, setMsg] = React.useState<string|null>(null);
  const [err, setErr] = React.useState<string|null>(null);

  React.useEffect(() => {
    api.adminCompanies().then(setCompanies).catch(()=>{});
  }, []);

  return (
    <div className="card">
      <div className="h1">Create user</div>
      <div className="muted">Internal signup only (admin-created). No public account creation.</div>
      <div className="hr" />
      <div className="grid">
        <div className="field">
          <label>Username</label>
          <input value={username} onChange={e=>setUsername(e.target.value)} placeholder="email or username" />
        </div>
        <div className="field">
          <label>Display name</label>
          <input value={display} onChange={e=>setDisplay(e.target.value)} placeholder="e.g., Nurse Jane" />
        </div>
        <div className="field">
          <label>Mattermost ID (optional)</label>
          <input value={mattermostId} onChange={e=>setMattermostId(e.target.value)} placeholder="e.g., jane.doe" />
        </div>
        <div className="field">
          <label>Role</label>
          <select value={role} onChange={e=>setRole(e.target.value)}>
            <option value="employee">employee</option>
            <option value="admin">admin</option>
            <option value="super_admin">super_admin</option>
          </select>
        </div>
        <div className="field">
          <label>Initial password</label>
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="min 10 chars" />
        </div>
      </div>

      <div style={{height:10}} />
      <div className="field">
        <label>Company access</label>
        <div className="grid" style={{gridTemplateColumns:'repeat(auto-fit, minmax(220px, 1fr))'}}>
          {companies.map(c => {
            const checked = companySlugs.includes(c.slug);
            return (
              <label key={c.id} className="badge" style={{display:'flex', gap:10, alignItems:'center', justifyContent:'space-between'}}>
                <span>{c.name} <span className="muted">({c.slug})</span></span>
                <input type="checkbox" checked={checked} onChange={e=>{
                  setCompanySlugs(prev => e.target.checked ? [...prev, c.slug] : prev.filter(s=>s!==c.slug));
                }} />
              </label>
            );
          })}
          {companies.length === 0 && <div className="muted">No companies yet. Create companies first.</div>}
        </div>
      </div>

      {err && <div style={{marginTop:10}} className="badge attn">Error: {err}</div>}
      {msg && <div style={{marginTop:10}} className="badge ok">{msg}</div>}

      <div style={{height:12}} />
      <button className="btn primary" onClick={async ()=>{
        setErr(null); setMsg(null);
        try {
          const u = await api.adminCreateUser({ username: username.trim(), display_name: display.trim(), mattermost_id: mattermostId.trim(), role, password, company_slugs: companySlugs });
          setMsg(`Created user id ${u.id} (${u.username})`);
          setUsername(''); setDisplay(''); setMattermostId(''); setPassword('');
        } catch(e:any) {
          setErr(e.message || 'Failed');
        }
      }}>Create</button>
    </div>
  );
}
