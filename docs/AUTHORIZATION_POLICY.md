# Authorization Regression Lab: Authorization Policy

## Scope

This document defines the initial record-read authorization contract.
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

## Policy

- Requests without a valid Bearer token receive HTTP 401.
- A member may read records they own within their tenant.
- A tenant administrator may read records within their assigned tenant.
- No identity may read a record belonging to another tenant.
- An inaccessible or nonexistent record returns HTTP 404.
- Authorization is enforced by the API, not by the frontend or caller-supplied headers.

## Required HTTP test matrix

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

## Vulnerability demonstration requirements

The same black-box HTTP tests must later run in two local modes:

- `corrected`: enforces the policy above.
- `vulnerable`: intentionally omits the record authorization check.

The vulnerable mode must remain local-only and must never be publicly exposed.

Evidence required:
1. Cross-tenant access is rejected with HTTP 404 in corrected mode.
2. The same cross-tenant request succeeds in vulnerable mode, demonstrating the flaw.
3. The regression test fails when the authorization check is temporarily removed.
4. The authorization check is restored and the corrected suite passes again.

## Out of scope for this stage

- Database and migrations
- Real passwords, login, JWT, or OAuth
- Frontend
- BFLA and other resource types
- Deployment or public hosting
