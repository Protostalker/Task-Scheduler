import React from 'react';
import { Link } from 'react-router-dom';

export default function AdminHome() {
  return (
    <div className="card">
      <div className="h1">Administrator</div>
      <div className="muted">Create users, companies, and tasks. Copy task links into Mattermost as needed.</div>
      <div className="hr" />
      <div className="row" style={{flexWrap:'wrap'}}>
        <Link className="btn" to="/administrator/users">Users</Link>
        <Link className="btn" to="/administrator/sign_up">Sign up</Link>
        <Link className="btn" to="/administrator/companies">Companies</Link>
        <Link className="btn primary" to="/administrator/tasks">Create tasks</Link>
        <Link className="btn" to="/stats">Stats</Link>
      </div>
    </div>
  );
}
