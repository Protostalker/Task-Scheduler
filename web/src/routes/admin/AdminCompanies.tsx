import React from 'react';
import { api } from '../../api';

export default function AdminCompanies() {
  const [slug, setSlug] = React.useState('');
  const [name, setName] = React.useState('');
  const [msg, setMsg] = React.useState<string|null>(null);
  const [err, setErr] = React.useState<string|null>(null);
  const [companies, setCompanies] = React.useState<any[]>([]);
  const [selected, setSelected] = React.useState<string>('');
  const [cats, setCats] = React.useState<any[]>([]);
  const [newCat, setNewCat] = React.useState('');
  const [patients, setPatients] = React.useState<any[]>([]);
  const [newPatient, setNewPatient] = React.useState<{name:string;phone:string;address:string;maps_url:string;notes:string}>({name:'',phone:'',address:'',maps_url:'',notes:''});

  const refreshCompanies = React.useCallback(async()=>{
    try {
      const cs = await api.adminCompanies();
      setCompanies(cs);
      if (!selected && cs.length) setSelected(cs[0].slug);
    } catch {}
  }, [selected]);

  React.useEffect(() => { refreshCompanies(); }, [refreshCompanies]);

  React.useEffect(() => {
    if (!selected) return;
    api.adminCategories(selected).then(setCats).catch(()=>setCats([]));
    api.adminPatients(selected, true).then(setPatients).catch(()=>setPatients([]));
  }, [selected]);

  return (
    <div className="card">
      <div className="h1">Companies</div>
      <div className="muted">Create or update companies by slug. Slug is used in URLs.</div>
      <div className="hr" />
      <div className="grid">
        <div className="field">
          <label>Slug</label>
          <input value={slug} onChange={e=>setSlug(e.target.value)} placeholder="fastcare" />
        </div>
        <div className="field">
          <label>Name</label>
          <input value={name} onChange={e=>setName(e.target.value)} placeholder="FastCare" />
        </div>
      </div>

      {err && <div style={{marginTop:10}} className="badge attn">Error: {err}</div>}
      {msg && <div style={{marginTop:10}} className="badge ok">{msg}</div>}
      <div style={{height:12}} />
      <button className="btn primary" onClick={async ()=>{
        setErr(null); setMsg(null);
        try {
          const r = await api.adminCreateCompany(slug.trim(), name.trim());
          setMsg(`Saved company ${r.company.slug} (${r.company.name})`);
          setSlug(''); setName('');
          await refreshCompanies();
        } catch(e:any) { setErr(e.message || 'Failed'); }
      }}>Save</button>

      <div className="hr" />
      <div className="h2">Manage existing companies</div>
      <div className="muted">Categories and Patients are per-company.</div>

      <div style={{height:8}} />
      <div className="field">
        <label>Select company</label>
        <select value={selected} onChange={e=>setSelected(e.target.value)}>
          {companies.map(c => (
            <option key={c.id} value={c.slug}>{c.name} ({c.slug})</option>
          ))}
        </select>
      </div>

      <div style={{height:12}} />
      <div className="grid">
        <div className="card">
          <div className="h2">Categories</div>
          <div className="muted">Used for task grouping on employee view.</div>
          <div className="hr" />
          <div className="row" style={{flexWrap:'wrap'}}>
            <input value={newCat} onChange={e=>setNewCat(e.target.value)} placeholder="e.g., idt" />
            <button className="btn primary" onClick={async ()=>{
              if (!newCat.trim()) return;
              try {
                await api.adminCreateCategory(selected, { name: newCat.trim() });
                setNewCat('');
                setCats(await api.adminCategories(selected));
              } catch(e:any) { alert(e.message || 'Failed'); }
            }}>Add</button>
          </div>
          <div style={{height:10}} />
          <div className="list">
            {cats.map(c => (
              <div key={c.id} className="row" style={{justifyContent:'space-between'}}>
                <div>
                  <span className="badge">{c.name}</span>
                  {!c.active && <span className="badge attn" style={{marginLeft:8}}>inactive</span>}
                </div>
                <div className="row">
                  <button className="btn" onClick={async ()=>{
                    await api.adminUpdateCategory(c.id, { active: !c.active });
                    setCats(await api.adminCategories(selected));
                  }}>{c.active ? 'Disable' : 'Enable'}</button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="h2">Patients</div>
          <div className="muted">Select a patient during task creation to auto-fill address/phone/maps.</div>
          <div className="hr" />
          <div className="grid">
            <div className="field">
              <label>Name</label>
              <input value={newPatient.name} onChange={e=>setNewPatient({...newPatient, name:e.target.value})} />
            </div>
            <div className="field">
              <label>Phone</label>
              <input value={newPatient.phone} onChange={e=>setNewPatient({...newPatient, phone:e.target.value})} />
            </div>
          </div>
          <div style={{height:8}} />
          <div className="field">
            <label>Address</label>
            <input value={newPatient.address} onChange={e=>setNewPatient({...newPatient, address:e.target.value})} onBlur={()=>{
              if (!newPatient.maps_url && newPatient.address.trim()) {
                const q = encodeURIComponent(newPatient.address.trim());
                setNewPatient({...newPatient, maps_url:`https://www.google.com/maps/search/?api=1&query=${q}`});
              }
            }} />
          </div>
          <div style={{height:8}} />
          <div className="field">
            <label>Maps URL (auto-generated if empty)</label>
            <input value={newPatient.maps_url} onChange={e=>setNewPatient({...newPatient, maps_url:e.target.value})} />
          </div>
          <div style={{height:8}} />
          <div className="field">
            <label>Notes</label>
            <textarea value={newPatient.notes} onChange={e=>setNewPatient({...newPatient, notes:e.target.value})} />
          </div>
          <button className="btn primary" onClick={async ()=>{
            try {
              if (!newPatient.name.trim()) throw new Error('Name required');
              await api.adminCreatePatient(selected, newPatient);
              setNewPatient({name:'',phone:'',address:'',maps_url:'',notes:''});
              setPatients(await api.adminPatients(selected, true));
            } catch(e:any) { alert(e.message || 'Failed'); }
          }}>Add patient</button>

          <div style={{height:10}} />
          <div className="list">
            {patients.map(p => (
              <div key={p.id} className="row" style={{justifyContent:'space-between'}}>
                <div>
                  <div className="h2" style={{fontSize:16}}>{p.name}</div>
                  <div className="muted">{p.phone} · {p.address}</div>
                  {!p.active && <div className="badge attn" style={{display:'inline-block', marginTop:6}}>inactive</div>}
                </div>
                <div className="row">
                  <button className="btn" onClick={async ()=>{
                    await api.adminUpdatePatient(p.id, { active: !p.active });
                    setPatients(await api.adminPatients(selected, true));
                  }}>{p.active ? 'Disable' : 'Enable'}</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{marginTop:12}} className="muted">Tip: assign employees to companies from the Users page.</div>
    </div>
  );
}
