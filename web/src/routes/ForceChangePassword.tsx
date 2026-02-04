import React from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../auth';

export default function ForceChangePassword() {
  const nav = useNavigate();
  const { me, refresh } = useAuth();
  const [pw, setPw] = React.useState('');
  const [err, setErr] = React.useState<string|null>(null);
  const [ok, setOk] = React.useState<string|null>(null);
  const [busy, setBusy] = React.useState(false);

  return (
    <div className="card">
      <div className="h1">Change password</div>
      <div className="muted">Your account requires a password change before you can continue.</div>
      <div className="hr" />
      <div className="field">
        <label>New password (min 10 chars)</label>
        <input type="password" value={pw} onChange={e=>setPw(e.target.value)} />
      </div>
      {err && <div style={{marginTop:10}} className="badge attn">Error: {err}</div>}
      {ok && <div style={{marginTop:10}} className="badge ok">{ok}</div>}
      <div style={{height:12}} />
      <button className="btn primary" disabled={busy} onClick={async ()=>{
        setErr(null); setOk(null); setBusy(true);
        try {
          await api.changePassword(pw);
          await refresh();
          setOk('Password updated.');
          nav('/');
        } catch(e:any) {
          setErr(e.message || 'Failed');
        } finally { setBusy(false); }
      }}>Save</button>
      {me?.role === 'super_admin' && (
        <div style={{marginTop:12}} className="badge attn">Super admin password changes are DB-only in this MVP.</div>
      )}
    </div>
  );
}
