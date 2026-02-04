import Redis from 'ioredis';
import webpush from 'web-push';

const redisUrl = process.env.REDIS_URL || 'redis://redis:6379/0';
const queueKey = process.env.PUSH_QUEUE_KEY || 'taskflow:push:queue';

const vapidPublic = process.env.VAPID_PUBLIC_KEY || '';
const vapidPrivate = process.env.VAPID_PRIVATE_KEY || '';
const vapidSubject = process.env.VAPID_SUBJECT || 'mailto:admin@example.com';

const redis = new Redis(redisUrl);

console.log(`[push-worker] starting; redis=${redisUrl} queue=${queueKey}`);

if (!vapidPublic || !vapidPrivate) {
  console.warn('[push-worker] WARNING: VAPID keys are missing. Worker will consume jobs but cannot send notifications.');
} else {
  webpush.setVapidDetails(vapidSubject, vapidPublic, vapidPrivate);
}

async function loop() {
  while (true) {
    try {
      const res = await redis.blpop(queueKey, 0);
      if (!res) continue;
      const [_key, payload] = res;
      let job;
      try {
        job = JSON.parse(payload);
      } catch {
        console.error('[push-worker] bad job (not JSON):', payload);
        continue;
      }

      const subscription = job.subscription;
      const data = job.payload || {};

      if (!vapidPublic || !vapidPrivate) {
        console.log('[push-worker] (dry-run) would send:', JSON.stringify(data));
        continue;
      }

      try {
        await webpush.sendNotification(subscription, JSON.stringify(data), {
          TTL: 60 * 30,
        });
        console.log('[push-worker] sent');
      } catch (err) {
        const statusCode = err?.statusCode || err?.status || null;
        console.error('[push-worker] send error:', statusCode, err?.message || err);
      }
    } catch (err) {
      console.error('[push-worker] error:', err);
      await new Promise(r => setTimeout(r, 2000));
    }
  }
}

loop();
