# Agent Marketplace dashboard

The frontend is a desktop-first visual dashboard for the marketplace workflow:

`buyer request → seller discovery → ANS verification → negotiation → offer comparison → selected deal`

## Run locally

Start the FastAPI backend from `../backend`, then run this app with Node.js 18+
and npm:

```powershell
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

During development, Vite proxies `/api/run` to `http://127.0.0.1:8000/run`.
Set `VITE_BACKEND_URL` before starting Vite if the backend is on another host or
port. Set `VITE_API_BASE_URL` only when a same-origin reverse proxy is already
configured for deployment.
