import React from "react";

type ToastItem = { id: number; kind: "success" | "error"; msg: string };

type ToastApi = {
  success: (msg: string) => void;
  error: (msg: string) => void;
};

const ToastCtx = React.createContext<ToastApi | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = React.useState<ToastItem[]>([]);

  function push(kind: ToastItem["kind"], msg: string) {
    const id = Date.now() + Math.floor(Math.random() * 1000);
    setItems((prev) => [...prev, { id, kind, msg }].slice(-3));
    window.setTimeout(() => {
      setItems((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }

  const api: ToastApi = React.useMemo(
    () => ({
      success: (msg) => push("success", msg),
      error: (msg) => push("error", msg),
    }),
    []
  );

  return (
    <ToastCtx.Provider value={api}>
      {children}
      <div style={{ position: "fixed", right: 16, bottom: 16, display: "flex", flexDirection: "column", gap: 8, zIndex: 9999 }}>
        {items.map((t) => (
          <div
            key={t.id}
            style={{
              padding: "10px 12px",
              borderRadius: 10,
              border: "1px solid rgba(255,255,255,0.18)",
              background: "rgba(20,20,20,0.85)",
              color: "white",
              minWidth: 240,
              boxShadow: "0 8px 24px rgba(0,0,0,0.25)",
              fontSize: 14,
            }}
          >
            <b style={{ display: "block", marginBottom: 4 }}>{t.kind === "success" ? "OK" : "Error"}</b>
            <span>{t.msg}</span>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

export function useToast(): ToastApi {
  const ctx = React.useContext(ToastCtx);
  if (!ctx) {
    // fallback that won't crash
    return {
      success: (msg: string) => console.log("toast success:", msg),
      error: (msg: string) => console.error("toast error:", msg),
    };
  }
  return ctx;
}
