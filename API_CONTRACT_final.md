# CLICK IX — API Contract (Final, Consolidated)

**Supersedes:** `API_CONTRACT_v1.md`, `API_CONTRACT_v2.md`, `API_CONTRACT_v3.md`
**Base URL:** `http://192.168.100.200:8000/api/v1` (intranet) → reverse-proxy `https://app.clickix.local/api/v1`
**Auth:** `Authorization: Bearer <JWT>` on every call except `/auth/login` and `/auth/refresh`
**Content-Type:** `application/json` unless noted (`multipart/form-data` for uploads, `text/csv` for AutoCount)
**Errors:** uniform envelope `{ "error": { "code": "...", "message": "...", "field": "...", "details": {...} } }`
**IDs:** every entity has integer PK `id` + business code (`quotation_no`, `do_no`, etc.) — clients show the code, joins use the PK.

---

## 0. Numbering Schemes (authoritative)

| Entity | Format | Example | Notes |
|---|---|---|---|
| Quotation | `QT-NNNNNN` (plain sequential, global) | `QT-000964` | When escalated: display `QT-000964/148662`; stored as `quotation_no` + `remedy_id` |
| Sales Order | `SO-NNNNNN` | `SO-001204` | |
| Delivery Order | `DO/YY/NNNN` (slashed, per-year) | `DO/26/0179` | URL-encode `%2F` |
| Service Report | `SR/YY/NNNN` | `SR/26/0188` | Always bound to a DO |
| Goods Received Note | `GRN/YY/NNNN` | `GRN/26/0044` | |
| Supplier PO | `PO/YY/NNNN` | `PO/26/0091` | |
| Goods Return (to supplier) | `GR/YY/NNNN` | `GR/26/0017` | |
| Ticket (CS) | `TKT-NNNNNN` | `TKT-004412` | |
| Leave request | `LV-YYMM-NNNN` | `LV-2605-0033` | |
| Trip claim | `TRP-YYMM-NNNN` | `TRP-2605-0117` | |
| Asset SKU – Media Player | `MP-YYMM-NNNN` | `MP-2605-0001` | physical unit serial |
| Asset SKU – TV | `TV-YYMM-NNNN` | `TV-2605-0044` | |
| Asset SKU – Spare RAM/SSD | `RM-…`, `SSD-…` | `RM-2605-0012` | |
| Catalog Item – Hardware | `MHD-NNN` | `MHD-085` | priced SKU on QT/DO |
| Catalog Item – Service | `MSV-NNN` | `MSV-020` | install/diag/travel |
| Project reference | `[SalesInitials][YY]-[ClientCode][NNN]` | `LG26-MAX103` | header on QT |
| Dealer acceptance | `dealer-MMYY-NNNN` | `dealer-0526-0329` | post-acceptance stamp |

**Allocation rule:** every numbered insert uses `SELECT next_seq FROM number_counters WHERE scope = ? FOR UPDATE` inside the same transaction; gaps are forbidden.

---

## 1. Auth

### POST /auth/login
```json
// req
{ "username": "lexus.gan", "password": "..." }
// 200
{ "access_token": "...", "refresh_token": "...", "expires_in": 1800,
  "user": { "id": 7, "username": "lexus.gan", "display_name": "Lexus Gan",
            "initials": "LG", "roles": ["sales", "ops_viewer"] } }
```
### POST /auth/refresh — `{ "refresh_token": "..." }` → same shape as login
### GET /auth/me → current user
### POST /auth/logout → revoke refresh

**Roles:** `admin`, `sales`, `ops`, `ops_viewer`, `finance`, `procurement`, `hr`, `cs`, `tech` (field engineer). RBAC enforced server-side per endpoint.

---

## 2. Catalog (priced SKUs on QT/DO)

### GET /catalog/items?type=hardware|service&q=&page=&page_size=
```json
{ "items": [
    { "id": 85, "item_code": "MHD-085", "type": "hardware",
      "description": "Media Player – Standard",
      "default_uom": "UNIT", "default_unit_price": "1450.00",
      "default_tax_code": "S", "active": true } ],
  "page": 1, "page_size": 50, "total": 312 }
```
### POST /catalog/items  *(admin)* — auto-allocates next `MHD-NNN` / `MSV-NNN`
### PATCH /catalog/items/{id} — partial update

---

## 3. Sales

### GET /sales/quotations?status=&customer_id=&q=&from=&to=&page=
```json
{ "items": [ {
  "id": 964, "quotation_no": "QT-000964", "remedy_id": "148662",
  "display_no": "QT-000964/148662",
  "job_type": "Escalated Issue",
  "customer": { "id": 12, "name": "Maxis Berhad", "code": "MAX" },
  "project_ref": "LG26-MAX103",
  "salesperson": "Lexus Gan",
  "subtotal": "3945.00", "tax_base": "575.00", "tax_amount": "46.00", "total": "3991.00",
  "currency": "MYR", "status": "accepted",
  "wo_number": "WO-77231", "remedy_number": "REM-148662",
  "dealer_code": "dealer-0526-0329",
  "validity_days": 14, "payment_term_days": 90,
  "created_at": "2026-05-12T09:14:00+08:00" } ],
  "page": 1, "total": 287 }
```
### GET /sales/quotations/{quotation_no}
Full payload adds `items[]`, `affected_screen`, `audit[]`, `attachments[]`.
```json
"items": [ {
  "line_no": 1, "item_code": "MHD-085", "description": "Media Player – Standard\nAffected Screen: Counter-1",
  "uom": "UNIT", "qty": 1, "unit_price": "1450.00", "tax_code": "S", "line_total": "1450.00" } ]
```
### POST /sales/quotations
```json
{ "customer_id": 12, "job_type": "Escalated Issue",
  "project_ref": "LG26-MAX103", "salesperson": "Lexus Gan",
  "wo_number": "WO-77231", "remedy_number": "REM-148662",
  "affected_screen": "Counter-1",
  "validity_days": 14, "payment_term_days": 90,
  "items": [ { "item_code": "MHD-085", "qty": 1, "unit_price": "1450.00", "tax_code": "S" } ] }
```
Server allocates `quotation_no`, computes subtotal / tax_base / tax_amount (SST 8% on lines where `tax_code ∉ {Z,EX}`), returns full record.

### PATCH /sales/quotations/{quotation_no}  — only `status ∈ {draft, sent}`
### POST /sales/quotations/{quotation_no}/send → status `sent`
### POST /sales/quotations/{quotation_no}/accept — `{ "dealer_code": "dealer-0526-0329", "signature_upload_id": 991 }` → status `accepted`, locks
### GET  /sales/quotations/{quotation_no}/pdf — `application/pdf`, exact CLICK IX layout

### Sales Orders — same shape under `/sales/orders` (`so_no`), generated from accepted QT.

---

## 4. Procurement

- `GET/POST /procurement/supplier-pos` — `po_no = PO/YY/NNNN`
- `GET/POST /procurement/grn` — `grn_no`, links `po_no`, on receive transitions SKU state `inbound → unassign`
- `GET/POST /procurement/returns` — `gr_no`, SKU state → `returned_supplier`

---

## 5. Operations

### Delivery Orders
**Header fields:** `do_no`, `salesperson` (the "Your P/O No." column on the printed DO — it's the CLICK IX salesperson, **not** a customer PO), `bill_to`, `ship_to`, `affected_screen` (sub-line under first hardware item), `assigned_pc_skus[]`, `status`.

**DO has NO price columns** — items are `{ line_no, item_code, description, uom, qty }` only. Footer `Total` is a quantity count.

- `GET /operations/delivery-orders?status=&assignee=&from=&to=`
- `GET /operations/delivery-orders/{do_no}`  (path-encode the slashes: `DO%2F26%2F0179`)
- `POST /operations/delivery-orders` — `assigned_pc_skus` MUST all be in state `unassign`; server transitions them to `assigned`
- `POST /operations/delivery-orders/{do_no}/split` — body `{ "skus": [...] }` strict subset of original `assigned_pc_skus`; creates child DO
- `POST /operations/delivery-orders/{do_no}/sign-off` — `{ "signature_upload_id": 8821, "signed_by": "PIC name" }`; precondition: a Service Report exists for this DO and all hardware lines are fulfilled
- `GET  /operations/delivery-orders/{do_no}/pdf`

### Service Reports
**Mirrors the official `Template_-_Service_Report.docx`.**
```json
{ "sr_no": "SR/26/0188", "do_no": "DO/26/0179",
  "client": { "company": "Maxis Berhad",
              "company_address": ["Level 18, Menara Maxis", "KLCC, 50088 KL"],
              "store_type": "Flagship", "store_name": "KLCC Centre Court",
              "pic_name": "Aiman Rashid", "pic_tel": "+60123456789" },
  "wo_number": "WO-77231", "remedy_number": "REM-148662",
  "diagnostic": "HDMI handshake failure on display 2.",
  "action_taken": "Swapped MP, reseated HDMI, verified playback.",
  "hardware_removed":  [ { "sku": "MP-2504-0033", "item_code": "MHD-085", "reason": "faulty HDMI" } ],
  "hardware_installed":[ { "sku": "MP-2605-0001", "item_code": "MHD-085" } ],
  "acknowledgement": { "signed_by": "Aiman Rashid",
                       "signature_png_upload_id": 8821,
                       "signed_at": "2026-05-17T14:22:00+08:00" },
  "photos": [ { "upload_id": 8822 }, { "upload_id": 8823 } ] }
```
- `GET /operations/service-reports/{sr_no}`
- `POST /operations/service-reports` — submit. Side-effects: removed SKUs → `returned_faulty`, installed SKUs → `deployed`, DO lines → `fulfilled`, SLA clock stops. `photos` min 1, max 12.

---

## 6. Tickets (CS / SLA)

- `POST /tickets` — open ticket from customer call/email. Auto `tkt_no`.
- `GET  /tickets?status=&assignee=&sla_breach=`
- `POST /tickets/{tkt_no}/escalate` — `{ "wo_number": "...", "remedy_number": "..." }` → locks ticket; subsequent QT for this ticket inherits these numbers and `job_type = "Escalated Issue"`.

---

## 7. Finance — AutoCount Handshake

- `POST /finance/autocount/import` — `multipart/form-data` file=`autocount.csv`. Server parses, matches by `QT-NNNNNN` / `SO-NNNNNN` / `DO/YY/NNNN`, updates payment / invoice status on the matched records. Returns `{ "matched": 142, "unmatched": [...], "errors": [...] }`.
- `GET  /finance/autocount/export?kind=claims|payroll|billing&from=&to=` — returns `text/csv` formatted for AutoCount re-import.

---

## 8. HR / Ops admin

- `POST /hr/leave` `{ "type": "annual|medical|unpaid", "from": "YYYY-MM-DD", "to": "YYYY-MM-DD", "reason": "..." }` → `lv_no`
- `GET  /hr/leave?user_id=&status=`
- `POST /hr/leave/{lv_no}/approve|reject`
- `POST /ops/trips` → `trp_no`, mileage claim
- `GET  /ops/trips?user_id=&status=`

---

## 9. Hardware lookup (auto-context on search)

### GET /hardware/outlet-context?outlet_id=  *or* `?pc_sku=`  *or* `?tv_sku=`
Server executes `Outlet ⨝ PC ⨝ TV` and returns:
```json
{ "outlet": { "id": 12, "name": "KLCC Centre Court", "address": "...", "anydesk_id": "987 654 321" },
  "pcs": [ { "sku": "MP-2504-0033", "item_code": "MHD-085", "anydesk_id": "111 222 333",
             "cpu": "i5-10500", "ram_gb": 16, "ssd_gb": 512, "installed_at": "2025-04-10" } ],
  "tvs":[ { "sku": "TV-2503-0021", "model": "LG 55UR640", "panel_hours": 8932 } ] }
```

---

## 10. Uploads

- `POST /uploads` — `multipart/form-data` file=… → `{ "upload_id": 8821, "url": "/uploads/2026/05/8821.pdf", "mime": "application/pdf", "size": 184221 }`
  PDFs are compressed (ghostscript `/ebook`) and written to `/var/www/app/uploads/YYYY/MM/`.
- `GET /uploads/{upload_id}` → file stream (auth required).

---

## 11. Validation Rules (enforced at gateway)

| Code | Condition |
|---|---|
| `VALIDATION_FAILED` | Generic Zod/pydantic failure |
| `UNAUTHENTICATED` | Missing / expired JWT |
| `FORBIDDEN_ROLE` | Role lacks endpoint permission |
| `NOT_FOUND` | Entity by code/id not present |
| `SKU_STATE_INVALID` | DO insert when SKU not `unassign`; sign-off when not `assigned`/`deployed` |
| `ESCALATION_FIELDS_REQUIRED` | `job_type=="Escalated Issue"` and (`wo_number` empty or `remedy_number` empty) |
| `ESCALATION_LOCKED` | Mutation attempted on a ticket after `/escalate` |
| `PARTIAL_SPLIT_INVALID` | Split SKUs not a strict subset of parent DO |
| `TAX_BASE_MISMATCH` | `tax_base != Σ(line_total where tax_code ∉ {Z,EX})` |
| `PROJECT_REF_INVALID` | `!~ /^[A-Z]{2,3}\d{2}-[A-Z]{3,4}\d{3}$/` |
| `DEALER_CODE_INVALID` | `!~ /^dealer-\d{4}-\d{4}$/` |
| `SR_SIGNATURE_REQUIRED` | SR submit without `acknowledgement.signature_png_upload_id` |
| `SR_PHOTOS_REQUIRED` | SR submit with `photos.length < 1` |
| `SR_WO_REMEDY_REQUIRED` | SR for an Escalated DO missing WO/Remedy |
| `SR_DO_MISMATCH` | SR `do_no` doesn't match parent DO |
| `SR_SKU_STATE_INVALID` | Installed SKU not in `unassign`; removed SKU not currently `deployed` at this outlet |
| `AUTOCOUNT_PARSE_ERROR` | CSV header mismatch / row decode fail |
| `INTERNAL_ERROR` | 500 fallback |

---

## 12. MariaDB Schema (essentials)

```sql
-- Core
users(id, username UNIQUE, password_hash, display_name, initials, active, created_at)
roles(id, code UNIQUE)               -- 'admin','sales','ops',...
user_roles(user_id, role_id, PRIMARY KEY(user_id,role_id))

customers(id, code UNIQUE, name, billing_address, shipping_address, ...)
outlets(id, customer_id FK, name, address, anydesk_id, ...)

-- Atomic numbering
number_counters(scope VARCHAR(32) PK, next_seq BIGINT, year SMALLINT, month TINYINT)

-- Catalog
catalog_items(id, item_code UNIQUE, type ENUM('hardware','service'),
              description, default_uom, default_unit_price DECIMAL(12,2),
              default_tax_code, active)

-- Asset SKUs (physical units)
asset_skus(id, sku UNIQUE, item_code FK, type ENUM('MP','TV','RM','SSD'),
           state ENUM('inbound','unassign','assigned','deployed','returned_faulty','returned_supplier','retired'),
           outlet_id NULL FK, anydesk_id, cpu, ram_gb, ssd_gb, panel_hours, ...)

-- Sales
quotations(id, quotation_no UNIQUE, remedy_id NULL, customer_id FK, job_type,
           project_ref, salesperson, wo_number, remedy_number, dealer_code,
           subtotal, tax_base, tax_amount, total, currency, status,
           validity_days, payment_term_days, accepted_signature_upload_id,
           created_by FK, created_at, accepted_at)
quotation_items(id, quotation_id FK, line_no, item_code, description,
                uom, qty DECIMAL(12,3), unit_price DECIMAL(12,2),
                tax_code, line_total DECIMAL(12,2))

sales_orders(id, so_no UNIQUE, quotation_id FK, ...)

-- Operations
delivery_orders(id, do_no UNIQUE, so_id FK NULL, customer_id FK, outlet_id FK,
                salesperson, bill_to, ship_to, affected_screen, status,
                parent_do_id NULL, signed_by, signature_upload_id, signed_at)
do_items(id, do_id FK, line_no, item_code, description, uom, qty, fulfilled BOOL)
do_assigned_skus(do_id FK, sku_id FK, PRIMARY KEY(do_id,sku_id))

service_reports(id, sr_no UNIQUE, do_id FK, wo_number, remedy_number,
                client_company, client_addr_json, store_type, store_name,
                pic_name, pic_tel, diagnostic, action_taken,
                ack_signed_by, ack_signature_upload_id, ack_signed_at,
                created_by FK, created_at)
sr_hardware(id, sr_id FK, direction ENUM('removed','installed'),
            sku_id FK, item_code, reason)
sr_photos(id, sr_id FK, upload_id FK)

-- Procurement
supplier_pos(id, po_no UNIQUE, supplier_id FK, status, ...)
grns(id, grn_no UNIQUE, po_id FK, received_at, received_by FK)
grn_items(grn_id FK, sku_id FK, qty)
goods_returns(id, gr_no UNIQUE, po_id FK, reason, ...)

-- Tickets / SLA
tickets(id, tkt_no UNIQUE, customer_id FK, outlet_id FK, opened_by FK,
        status, severity, sla_due_at, escalated_at,
        escalation_wo, escalation_remedy)

-- Finance handshake
autocount_imports(id, filename, imported_at, imported_by FK, matched, unmatched_json)
autocount_exports(id, kind, from_date, to_date, generated_at, generated_by FK)

-- HR / trips
leave_requests(id, lv_no UNIQUE, user_id FK, type, from_date, to_date, reason, status, decided_by FK)
trips(id, trp_no UNIQUE, user_id FK, date, km, purpose, claim_amount, status)

-- Uploads
uploads(id, path, mime, size, sha256, uploaded_by FK, uploaded_at)

-- Audit
audit_log(id, entity, entity_id, action, actor_id FK, before_json, after_json, at)
```

All `DECIMAL(12,2)` for money, `DECIMAL(12,3)` for quantities. UTF-8 (`utf8mb4`), InnoDB, FK CASCADE on child rows.

---

## 13. Standard Response Envelopes

**List:** `{ "items": [...], "page": 1, "page_size": 50, "total": 287 }`
**Single:** the resource directly.
**Mutation:** the resource after mutation, plus `{ "audit_id": 12345 }` if applicable.
**Error:** `{ "error": { "code": "...", "message": "...", "field": "items[2].qty", "details": {...} } }` with appropriate HTTP status (400/401/403/404/409/422/500).

— END —
