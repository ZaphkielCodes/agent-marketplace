# AI Agent Marketplace Sandbox Backend

This FastAPI service demonstrates a deterministic marketplace workflow:

1. Discover seller agents for a requested capability.
2. Verify each seller with the sandbox ANS layer or GoDaddy ANS.
3. Negotiate only with verified sellers.
4. Keep only offers at or below the buyer's budget.
5. Select the lowest verified, affordable offer.

Seller discovery and negotiation remain deterministic sandbox components. ANS
verification defaults to sandbox mode, with an opt-in live GoDaddy ANS lookup.

## ANS configuration

Sandbox mode is the default and preserves the demo's simulated seller trust
state:

```text
ANS_MODE=sandbox
```

To verify sellers against GoDaddy ANS, configure the environment before starting
the service:

```text
ANS_MODE=live
GODADDY_KEY=<your-key>
GODADDY_SECRET=<your-secret>
GODADDY_ANS_BASE_URL=https://api.godaddy.com
```

Live mode calls `GET https://api.godaddy.com/v1/agents/{agentId}` with the
`Authorization: sso-key {GODADDY_KEY}:{GODADDY_SECRET}` header. A seller is
verified only when the response's `agentId` exactly matches the seller's
`ans_id` and `agentStatus` is `ACTIVE`. Missing credentials, invalid responses,
authentication failures, and network failures return an unverified result; live
mode never falls back to simulated trust.

`GameHubBot` is the registered live ANS seller. The other demo seller IDs may
remain sandbox/demo identities.

The included root `.env.example` lists the variable names only. Do not commit a
real credential or a populated `.env` file.

## Run locally

Use Python 3.10 or later.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

The API documentation is then available at `http://127.0.0.1:8000/docs`.

## Example request

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/run `
  -ContentType 'application/json' `
  -Body '{"item":"PS5","max_price":490}'
```

`GameHubBot` is selected at `$465.00`. If the buyer submits a `$400.00`
budget, neither verified PS5 seller is affordable and no deal is selected. An
unverified seller is never considered, even when it advertises a lower price.

## Run tests

```powershell
python -m unittest -v
```

The tests cover budget enforcement, firm pricing, trust filtering, selection,
request validation, and mocked sandbox/live ANS verification behavior.
