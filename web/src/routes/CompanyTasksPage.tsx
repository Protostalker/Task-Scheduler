import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api';
import { getPushState, enablePush, pushSupported, hasPushSubscription } from '../push';

type TaskItem = { task_code:string; title:string; category:string; task_date:string; task_time?: string | null; status:string };

function group(tasks: TaskItem[]) {
  const byDate: Record<string, Record<string, TaskItem[]>> = {};
  for (const t of tasks) {
    byDate[t.task_date] ||= {};
    byDate[t.task_date][t.category] ||= [];
    byDate[t.task_date][t.category].push(t);
  }
  return byDate;
}

export default function CompanyTasksPage() {
  const { companySlug } = useParams();
  const [tasks, setTasks] = React.useState<TaskItem[]>([]);
  const [hideCompleted, setHideCompleted] = React.useState<boolean>(true);
  const [err, setErr] = React.useState<string|null>(null);
  const [pushState, setPushState] = React.useState<'granted'|'denied'|'default'|'unsupported'>('unsupported');
  const [pushBusy, setPushBusy] = React.useState(false);
  const [pushErr, setPushErr] = React.useState<string|null>(null);
  const [pushSubscribed, setPushSubscribed] = React.useState<boolean>(false);

  React.useEffect(() => {
    (async () => {
      try {
        const st = await getPushState();
        setPushState(st);
        if (st === 'granted') {
          setPushSubscribed(await hasPushSubscription());
        } else {
          setPushSubscribed(false);
        }
      } catch {
        setPushState('unsupported');
        setPushSubscribed(false);
      }
    })();

    (async ()=>{
      if (!companySlug) return;
      try {
        setErr(null);
        const t = await api.companyTasks(companySlug);
        setTasks(t);
      } catch(e:any) {
        setErr(e.message || 'Failed to load tasks');
      }
    })();
  }, [companySlug]);

  const filteredTasks = hideCompleted ? tasks.filter(t => t.status !== "done") : tasks;
  const grouped = group(filteredTasks);
  const dates = Object.keys(grouped).sort();

  // Show if we lack permission OR we haven't subscribed this device yet.
  const showPushCard = pushState !== 'granted' || !pushSubscribed;
  const pushUnsupportedReason = !pushSupported() ? 'Push needs HTTPS (or localhost) + service worker support.' : '';

  async function onEnablePush() {
    try {
      setPushErr(null);
      setPushBusy(true);
      const ok = await enablePush();
      const st = await getPushState();
      setPushState(st);
      if (st === 'granted') setPushSubscribed(await hasPushSubscription());
      if (!ok && st === 'denied') {
        setPushErr('Notifications are blocked in the browser settings for this site.');
      }
    } catch (e:any) {
      setPushErr(e.message || 'Failed to enable notifications');
    } finally {
      setPushBusy(false);
    }
  }

  return (
    <div>
      <div className="h1">Tasks · {companySlug}</div>
      <div className="muted">Click a task to view details and mark done.</div>

      {showPushCard && (
        <div className="card" style={{marginTop:10}}>
          <div className="spread" style={{alignItems:'center'}}>
            <div>
              <div style={{fontWeight:800}}>Notifications</div>
              <div className="muted" style={{fontSize:13}}>
                Enable Chrome notifications so you get alerted when tasks are assigned to you.
                {pushState==='granted' && pushSubscribed && <div className="badge" style={{marginTop:8}}>Connected</div>}
                {pushState==='granted' && !pushSubscribed && <div className="badge attn" style={{marginTop:8}}>Permission granted, but this device isn’t subscribed yet</div>}
              </div>
              {!pushUnsupportedReason ? null : <div className="muted" style={{fontSize:13, marginTop:6}}>{pushUnsupportedReason}</div>}
              {pushState === 'denied' && <div className="badge attn" style={{marginTop:8}}>Blocked in browser settings</div>}
              {pushErr && <div className="badge attn" style={{marginTop:8}}>Error: {pushErr}</div>}
            </div>
            <div>
              <button className="btn" disabled={pushBusy || !pushSupported() || pushState==='denied'} onClick={onEnablePush}>
                {pushBusy ? 'Enabling...' : (pushState==='granted' && !pushSubscribed ? 'Enable on this device' : 'Enable notifications')}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="row" style={{marginTop:10, gap:10, alignItems:"center"}}><label style={{display:"flex", gap:8, alignItems:"center"}}><input type="checkbox" checked={hideCompleted} onChange={(e)=>setHideCompleted(e.target.checked)} /><span className="muted">Hide completed tasks</span></label></div>
      {err && <div className="card"><span className="badge attn">Error: {err}</span></div>}

      <div className="list">
        {dates.length === 0 && !err && <div className="card">No tasks found.</div>}

        {dates.map(d => (
          <div key={d} className="card">
            <div className="spread">
              <div className="h2">{d}</div>
              <span className="badge">{Object.values(grouped[d]).reduce((a,b)=>a+b.length,0)} tasks</span>
            </div>
            <div className="hr" />
            {Object.keys(grouped[d]).sort().map(cat => (
              <div key={cat} style={{marginBottom: 10}}>
                <div className="row" style={{justifyContent:'space-between'}}>
                  <div className="muted" style={{fontWeight:700}}>{cat}</div>
                  <span className="badge">{grouped[d][cat].length}</span>
                </div>
                <div style={{height:8}} />
                <div className="list">
                  {grouped[d][cat].map(t => (
                    <Link key={t.task_code} to={`/company/${companySlug}/tasks/${t.task_code}`} className="item">
                      <div className="spread">
                        <div>
                          <div style={{fontWeight:700}}>{t.title}{t.task_time ? ` · ${t.task_time}` : ""}</div>
                          <div className="muted" style={{fontSize:13}}>{t.task_code}</div>
                        </div>
                        <span className={"badge " + (t.status === 'todo' ? "attn" : "ok")}>
                          {t.status === 'todo' ? "!" : "Done"}
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
