export async function ensureServiceWorker(){
  if (!('serviceWorker' in navigator)) return;
  try {
    await navigator.serviceWorker.register('/public/service-worker.js', { scope: '/' });
    console.log('[sw] registered');
  } catch (e) {
    console.error('[sw] register failed', e);
  }
}

const API_BASE: string = (((import.meta as any).env?.VITE_API_BASE as string) || '').replace(/\/$/, '');

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...(opts.headers || {}),
    },
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || res.statusText);
  }

  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return (await res.json()) as T;
  return (await res.text()) as unknown as T;
}

function urlBase64ToUint8Array(base64String: string) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
  return outputArray;
}

export function pushSupported(): boolean {
  return !!(window.isSecureContext && 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window);
}

export async function getPushState(): Promise<'granted' | 'denied' | 'default' | 'unsupported'> {
  if (!('Notification' in window)) return 'unsupported';
  if (!pushSupported()) return 'unsupported';
  return Notification.permission;
}

export async function hasPushSubscription(): Promise<boolean> {
  if (!pushSupported()) return false;
  try {
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.getSubscription();
    return !!sub;
  } catch {
    return false;
  }
}

export async function enablePush(): Promise<boolean> {
  if (!pushSupported()) throw new Error('Push not supported (needs HTTPS + service worker)');

  // If permission is already granted, Chrome will return 'granted' immediately (no prompt).
  const perm = await Notification.requestPermission();
  if (perm !== 'granted') return false;

  const reg = await navigator.serviceWorker.ready;

  // Fetch VAPID public key from API at runtime (so we don't need build-time envs)
  const keyResp = await req<{ public_key: string }>('/api/push/public_key');
  const publicKey = (keyResp.public_key || '').trim();
  if (!publicKey) throw new Error('Push public key not configured on server');

  // IMPORTANT: subscribe() throws if a subscription already exists. Reuse if present.
  let sub = await reg.pushManager.getSubscription();
  if (!sub) {
    sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicKey),
    });
  }

  // Upsert subscription server-side (safe to call repeatedly).
  await req('/api/push/subscribe', {
    method: 'POST',
    body: JSON.stringify(sub),
  });

  return true;
}
