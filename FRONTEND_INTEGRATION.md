# Frontend Integration Guide — CLICK IX

Companion to `API_CONTRACT_final.md`. Tells your Python team **exactly** what the React app expects, and tells the frontend dev how everything wires together.

---

## 1. Network topology

```
[Browser]  →  https://app.clickix.local        ← React static bundle (nginx)
           →  https://app.clickix.local/api/v1 ← nginx reverse-proxy
                                                  → 127.0.0.1:8000  FastAPI (systemd: clickix-api.service)
                                                                       └─→ MariaDB :3306 (local socket)
                                                                       └─→ /var/www/app/uploads/
```

- Frontend and API **same origin** (`app.clickix.local`) → no CORS in production.
- For local dev (`http://localhost:5173` → `http://192.168.100.200:8000`) you MUST enable CORS on FastAPI:

```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://app.clickix.local"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

## 2. Environment variables (frontend)

`.env.local`
```
VITE_API_BASE_URL=http://192.168.100.200:8000/api/v1
```
Production build: `VITE_API_BASE_URL=/api/v1` (same origin).

All client env vars **must** start with `VITE_` — anything else is undefined in the browser bundle.

---

## 3. Auth flow (JWT + refresh)

```
POST /auth/login   → { access_token, refresh_token, expires_in: 1800, user }
   ↓ store both tokens in zustand (persisted to localStorage)
[every API call] Authorization: Bearer <access_token>
   ↓ on 401:
POST /auth/refresh { refresh_token } → new access_token
   ↓ retry original request once
   ↓ if refresh also 401 → logout, redirect /login
POST /auth/logout  → revoke refresh, clear local state
```

The included `src/lib/api.ts` axios client implements this transparently.

### Recommended token lifetimes
- `access_token`: 30 min (JWT HS256 signed with `JWT_SECRET`)
- `refresh_token`: 14 days, stored in `refresh_tokens` DB table (so revoke works)

### Password hashing
Use `argon2id` (or `bcrypt` cost ≥ 12). **Never** plain SHA-256.

---

## 4. Data the frontend needs the DB to expose

Beyond §12 of the contract, the frontend will query these **read-mostly** endpoints heavily — make sure they're indexed:

| Endpoint | Hot filters | Index hint |
|---|---|---|
| `GET /sales/quotations` | `status`, `customer_id`, `from`, `to`, `q` (matches `quotation_no` or customer name) | `(status, created_at DESC)`, `(customer_id, created_at DESC)`, FULLTEXT on `quotation_no` + `project_ref` |
| `GET /operations/delivery-orders` | `status`, `assignee`, date range | `(status, created_at DESC)`, `(assigned_to, status)` |
| `GET /tickets` | `status`, `sla_breach`, `assignee` | `(status, sla_due_at)`, computed column `sla_breached BOOL` |
| `GET /hardware/outlet-context` | `outlet_id` | unique on `outlets.id`; cached at app layer |
| `GET /catalog/items` | `type`, `q` | `(type, active)`, FULLTEXT on `item_code` + `description` |

For every list endpoint, the response **must** include `total` so the table can show pagination correctly.

---

## 5. Error contract the frontend relies on

Every non-2xx returns:
```json
{ "error": { "code": "VALIDATION_FAILED", "message": "qty must be > 0", "field": "items[2].qty" } }
```

The axios interceptor surfaces `error.code` to the UI (toast + inline field error via `field`). **Do not** return raw FastAPI `{ "detail": [...] }` — wrap pydantic errors into this shape:

```python
@app.exception_handler(RequestValidationError)
async def validation_handler(req, exc):
    first = exc.errors()[0]
    return JSONResponse(status_code=422, content={"error": {
        "code": "VALIDATION_FAILED",
        "message": first["msg"],
        "field": ".".join(str(p) for p in first["loc"][1:]),
        "details": exc.errors(),
    }})
```

---

## 6. File uploads

Frontend `<input type="file">` → `POST /uploads` (multipart) → server returns `{ upload_id }`. That id is then attached to the parent resource (e.g. `acknowledgement.signature_png_upload_id`). **Never** base64-embed binaries in JSON.

Compress PDFs server-side before persisting:
```bash
gs -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook -o out.pdf in.pdf
```

---

## 7. Money & tax — round once, on the server

- All amounts wire as **strings** (`"3991.00"`) to avoid JS float drift.
- Frontend uses `parseFloat` only for display; arithmetic happens server-side.
- SST 8% computed **per line** then summed; `tax_base = Σ line_total where tax_code ∉ {Z,EX}`; `tax_amount = round(tax_base * 0.08, 2)`. Server rejects client-submitted totals — recomputes and validates.

---

## 8. Date/time

- All timestamps ISO-8601 with timezone: `2026-05-17T14:22:00+08:00`.
- Server stores UTC; converts to `Asia/Kuala_Lumpur` on render.
- Frontend uses `date-fns` + `formatInTimeZone` for display.

---

## 9. Where each frontend page hits the API

| Page | Endpoints used |
|---|---|
| `/login` | `POST /auth/login` |
| `/` (dashboard) | `GET /tickets?status=open`, `GET /operations/delivery-orders?status=in_progress`, `GET /sales/quotations?status=sent` |
| `/quotations` | `GET /sales/quotations` |
| `/quotations/$id` | `GET /sales/quotations/{no}`, `POST .../send`, `POST .../accept`, `GET .../pdf` |
| `/quotations/new` | `GET /catalog/items?type=…`, `POST /sales/quotations` |
| `/delivery-orders` | `GET /operations/delivery-orders` |
| `/delivery-orders/$id` | `GET /operations/delivery-orders/{no}`, `POST .../sign-off`, `POST .../split`, `GET .../pdf` |
| `/service-reports/new?do=…` | `POST /uploads` (signature + photos), `POST /operations/service-reports` |
| `/tickets` | `GET /tickets`, `POST /tickets/{no}/escalate` |
| `/finance/autocount` | `POST /finance/autocount/import` (multipart CSV), `GET …/export` |
| `/hr/leave` | `GET/POST /hr/leave`, approve/reject |
| `/hardware?outlet=…` | `GET /hardware/outlet-context` |

---

## 10. Local dev checklist

1. `bun install`
2. Create `.env.local` with `VITE_API_BASE_URL`
3. `bun run dev` → http://localhost:5173
4. FastAPI: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
5. MariaDB: load schema from `API_CONTRACT_final.md` §12
6. Seed an admin user, log in, verify token refresh by waiting 30 min (or shorten `expires_in` temporarily).

---

## 11. Deployment checklist (192.168.100.200)

- **nginx** serves `dist/` + proxies `/api/v1` to `127.0.0.1:8000`
- **systemd unit** `/etc/systemd/system/clickix-api.service` runs FastAPI under `gunicorn -k uvicorn.workers.UvicornWorker -w 4`
- **MariaDB** local, `bind-address=127.0.0.1`, daily mysqldump cron to `/var/backups/`
- **/var/www/app/uploads/** owned by `www-data:www-data`, mode 750
- **TLS** via self-signed or internal CA on nginx; HSTS once stable
- **Backups**: nightly `mysqldump` + `tar` of `/var/www/app/uploads/` → NAS
