import React from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../auth';

export default function LoginPage() {
  const nav = useNavigate();
  const { refresh } = useAuth();
  const [username, setUsername] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [err, setErr] = React.useState<string|null>(null);
  const [busy, setBusy] = React.useState(false);

  async function doLogin() {
    setErr(null); setBusy(true);
    try {
      await api.login(username.trim(), password);
      await refresh();
      nav('/');
    } catch(e:any) {
      setErr(e.message || 'Login failed');
    } finally { setBusy(false); }
  }

  return (
    <form className="card" onSubmit={(e)=>{e.preventDefault(); if(!busy) doLogin();}}>
      <div className="h1">Login</div>
      <div className="muted">Use your internal username (e.g. email) and password.</div>
      <div className="hr" />
      <div className="grid">
        <div className="field">
          <label>Username</label>
          <input value={username} onChange={e=>setUsername(e.target.value)} placeholder="username" />
        </div>
        <div className="field">
          <label>Password</label>
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="password" />
        </div>
      </div>
      {err && <div style={{marginTop:10}} className="badge attn">Error: {err}</div>}
      <div style={{height:12}} />
      <button className="btn primary" type="submit" disabled={busy}>Sign in</button>
    </form>
  );
}
