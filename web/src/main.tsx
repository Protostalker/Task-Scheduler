import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './routes/App'
import { AuthProvider } from './auth'
import { ToastProvider } from './components/Toast'
import './styles.css'
import { initTheme } from './theme'
import { ensureServiceWorker } from './push';

initTheme();

// Register service worker for Web Push (requires HTTPS except localhost)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js').catch(() => {
      // Silent fail; push is optional.
    });
  });
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <App />
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
)

// V6: register service worker early
ensureServiceWorker();
