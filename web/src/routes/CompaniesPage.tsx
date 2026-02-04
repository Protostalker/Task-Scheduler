import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, CompanyLite } from "../api";
import { useToast } from "../components/Toast";
import { pushSupported, getPushState, hasPushSubscription, enablePush } from "../push";

export default function CompaniesPage() {
  const nav = useNavigate();
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [companies, setCompanies] = useState<CompanyLite[]>([]);

  const toast = useToast();
  const [pushPerm, setPushPerm] = useState<"granted" | "denied" | "default" | "unsupported">("unsupported");
  const [pushSub, setPushSub] = useState<boolean>(false);
  const [pushBusy, setPushBusy] = useState<boolean>(false);

  async function refreshPush() {
    if (!pushSupported()) {
      setPushPerm("unsupported");
      setPushSub(false);
      return;
    }
    try {
      const perm = await getPushState();
      setPushPerm(perm);
      const sub = await hasPushSubscription();
      setPushSub(sub);
    } catch {
      // ignore
    }
  }


  useEffect(() => {
    let mounted = true;
    (async () => {
      refreshPush();
      setLoading(true);
      setErr(null);
      try {
        const cs = await api.companies();
        if (!mounted) return;
        setCompanies(cs || []);
      } catch (e: any) {
        if (!mounted) return;
        setErr(e?.message ? String(e.message) : String(e));
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>Companies</div>
          <div className="muted" style={{ marginTop: 2 }}>Pick a company to view tasks.</div>
        </div>
        <div className="row" style={{ gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
          {pushPerm !== "unsupported" && (
            <button
              className="btn"
              disabled={pushBusy || pushPerm === "denied"}
              onClick={async () => {
                setPushBusy(true);
                try {
                  if (pushPerm !== "granted" || !pushSub) {
                    const ok = await enablePush();
                    if (ok) toast.success("Notifications enabled.");
                    else toast.error("Notifications not enabled.");
                    await refreshPush();
                  } else {
                    await api.pushTest();
                    toast.success("Sent test notification.");
                  }
                } catch (e: any) {
                  toast.error(e?.message ? String(e.message) : String(e));
                } finally {
                  setPushBusy(false);
                }
              }}
              type="button"
              title={pushPerm === "denied" ? "Notifications are blocked in your browser settings" : undefined}
            >
              {pushPerm === "denied"
                ? "Notifications blocked"
                : (pushPerm !== "granted" || !pushSub)
                  ? "Click here to get notified"
                  : "Test notify"}
            </button>
          )}
          <button className="btn" onClick={() => window.location.reload()}>Refresh</button>
        </div>
      </div>

      <div style={{ height: 12 }} />

      {loading && <div className="muted">Loading...</div>}
      {!loading && err && (
        <div className="card" style={{ borderColor: "rgba(255,0,0,0.35)" }}>
          <div style={{ fontWeight: 700, marginBottom: 6 }}>Could not load companies</div>
          <div className="muted" style={{ whiteSpace: "pre-wrap" }}>{err}</div>
        </div>
      )}

      {!loading && !err && companies.length === 0 && (
        <div className="muted">No companies found.</div>
      )}

      {!loading && !err && companies.length > 0 && (
        <div className="company-list">
          {companies.map((c) => (
            <button
              key={c.slug}
              className="company-item"
              onClick={() => nav(`/company/${c.slug}`)}
              type="button"
            >
              <div className="company-item-main">
                <div className="company-item-name">{c.name}</div>
                <div className="muted" style={{ fontSize: 13 }}>{c.slug}</div>
              </div>
              <div className="company-item-right">
                {c.has_attention && (
                  <span className="pill pill-warn">
                    {typeof c.due_count === "number" ? `${c.due_count} due` : "Needs attention"}
                  </span>
                )}
                <span className="pill">Open</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
