# Authorization Regression Lab: Authorization Policy

## Scope

This document defines the authorization contract for two API operations:

- `GET /records/{record_id}` — record-level authorization (BOLA).
- `GET /admin/summary` — function-level authorization (BFLA).

The API uses static in-memory fixtures and synthetic Bearer tokens.
These fixtures are for local testing only, not production authentication.

## Identities

| Identity | Tenant | Role |
|---|---|---|
| member_a | A | member |
| admin_a | A | tenant_admin |
| member_b | B | member |
| admin_b | B | tenant_admin |

The server maps fixed synthetic Bearer tokens to identities.
Authorization must not trust caller-provided identity, tenant, or role headers.

## Records

| Record ID | Tenant | Owner |
|---|---|---|
| record_a1 | A | member_a |
| record_a2 | A | member_a2 |
| record_a3 | A | member_a |
| record_b1 | B | member_b |
| record_b2 | B | member_b |

`member_a2` is a synthetic owner with no login token in the initial fixture set.

## Record-level authorization: BOLA

For `GET /records/{record_id}`:

- Requests without a valid Bearer token receive HTTP 401.
- A member may read records they own within their tenant.
- A tenant administrator may read records within their assigned tenant.
- No identity may read a record belonging to another tenant.
- An inaccessible or nonexistent record returns HTTP 404.
- Authorization is enforced by the API, not by the frontend or caller-supplied headers.

### Required record-read HTTP test matrix

| Identity | Record | Expected status | Reason |
|---|---|---:|---|
| No token | record_a1 | 401 | Authentication required |
| Invalid token | record_a1 | 401 | Invalid bearer token |
| member_a | record_a1 | 200 | Own record |
| member_a | record_a3 | 200 | Own record |
| member_a | record_a2 | 404 | Different owner |
| member_a | record_b1 | 404 | Different tenant |
| admin_a | record_a1 | 200 | Same tenant |
| admin_a | record_a2 | 200 | Same tenant |
| admin_a | record_b1 | 404 | Different tenant |
| member_b | record_a1 | 404 | Different tenant |
| member_b | record_b1 | 200 | Own record |
| admin_b | record_a1 | 404 | Different tenant |
| admin_b | record_b1 | 200 | Same tenant |
| admin_b | record_b2 | 200 | Same tenant |
| Any valid identity | nonexistent ID | 404 | Record does not exist |
| member_a with spoofed identity/tenant/role headers | record_b1 | 404 | Headers are not trusted |

## Function-level authorization: BFLA

For `GET /admin/summary`:

- A valid Bearer token is required in both modes.
- Only a `tenant_admin` may invoke the function in corrected mode.
- A member receives HTTP 403 in corrected mode.
- A tenant administrator receives HTTP 200 and a summary for their own tenant.
- The summary contains `tenant_id` and `record_count`.
- Tenant A's summary reports three records; Tenant B's summary reports two.
- The summary is always scoped to the authenticated identity's tenant, including in vulnerable mode.
- Caller-supplied role or tenant headers must not grant administrator permissions or change the summary's tenant.
- A missing or invalid token receives HTTP 401.

### Required admin-summary HTTP test matrix

| Identity | Corrected status | Vulnerable status | Reason |
|---|---:|---:|---|
| No token | 401 | 401 | Authentication required |
| Invalid token | 401 | 401 | Invalid Bearer token |
| member_a | 403 | 200 | Member must not invoke admin function |
| member_b | 403 | 200 | Member must not invoke admin function |
| admin_a | 200 | 200 | Authorized for Tenant A |
| admin_b | 200 | 200 | Authorized for Tenant B |
| member_a with spoofed admin role and tenant headers | 403 | 200 | Headers cannot grant permissions |

The vulnerable-mode results above are intentional demonstrations of the missing role check, not acceptable authorization behavior.

## Demonstration frontend

A small plain HTML, CSS, and JavaScript frontend is served by FastAPI
for local demonstration.

- It lets users select one of the fixed synthetic identities, request a
  record, and request the administrator summary.
- It sends actual HTTP requests using the corresponding synthetic Bearer
  token and displays the returned status and response body.
- It is a demonstration and observability layer, not a security boundary.
  All authorization decisions must remain enforced by the backend.
- The frontend and API must be used with synthetic data on loopback only.
  The deliberately vulnerable mode must never be exposed to a network.

The frontend does not implement real authentication and does not replace
the black-box HTTP regression tests.

## Corrected and vulnerable modes

The same black-box HTTP test suite must support two local modes, selected through `AUTHZ_MODE`:

- `corrected`: enforces the approved authorization policies.
- `vulnerable`: intentionally omits the relevant authorization check to demonstrate the corresponding flaw.

For BOLA, vulnerable mode omits record-level authorization.
For BFLA, vulnerable mode omits the administrator-role check on `/admin/summary` but retains authentication and tenant scoping.

The vulnerable mode must remain local-only and must never be publicly exposed.

## Required regression evidence

### BOLA

1. Cross-tenant record access returns HTTP 404 in corrected mode.
2. The same cross-tenant request succeeds in vulnerable mode.
3. A test fails when the record authorization check is temporarily removed.
4. The original check is restored and the corrected suite passes.

### BFLA

1. Members receive HTTP 403 for `/admin/summary` in corrected mode.
2. The same member requests receive HTTP 200 in vulnerable mode, exposing the missing function-level check.
3. Valid tenant administrators receive HTTP 200 in both modes.
4. The summary remains scoped to the authenticated tenant in both modes.
5. A test fails when the role check is temporarily removed, and the corrected suite passes after the check is restored.

## Out of scope for this stage

- Database and migrations
- Real passwords, login, JWT, or OAuth
- Additional resource types or authorization scenarios beyond the current BOLA and BFLA slices
- Deployment or public hosting
