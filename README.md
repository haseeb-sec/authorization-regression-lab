# Authorization Regression Lab

A local-only FastAPI learning project that demonstrates how automated HTTP
regression tests can detect broken object-level and function-level
authorization in a multi-tenant API.

The lab provides two deliberately contrasting modes using the same application
and authorization test assertions:

- `corrected`: enforces the documented authorization policy.
- `vulnerable`: intentionally omits selected authorization checks to
  demonstrate the resulting failures.

**The vulnerable mode is for isolated local testing only. Never expose it
to a network or deploy it.**

## What this lab demonstrates

### BOLA — Broken Object Level Authorization

`GET /records/{record_id}` returns synthetic records.

In corrected mode:
- A member can read their own records within their tenant.
- A tenant administrator can read records within their own tenant.
- Cross-tenant and other-owner records that the caller cannot access return
  `404 Not Found`.
- Missing or invalid bearer tokens return `401 Unauthorized`.

In vulnerable mode, record-level authorization is omitted. Requests for
otherwise inaccessible existing records can return `200 OK`.

### BFLA — Broken Function Level Authorization

`GET /admin/summary` returns a synthetic record count for the authenticated
identity's tenant.

In corrected mode:
- A valid bearer token is required.
- Only a `tenant_admin` can invoke the endpoint.
- Authenticated non-admin members receive `403 Forbidden`.
- The result remains scoped to the authenticated tenant.

In vulnerable mode, the administrator-role check is omitted. Authenticated
members can invoke the endpoint, while tenant scoping remains in place.

### Caller-supplied headers

Tests attempt to override identity, role, or tenant using request headers.
The application derives these attributes from its fixed synthetic token
mapping instead of trusting those headers.

## Technology

- Python
- FastAPI
- pytest
- FastAPI `TestClient`
- Plain HTML, CSS, and JavaScript frontend served by FastAPI
- Synthetic in-memory identities and records

The lab does not use a database, production identity provider, or real
user credentials. The frontend sends requests to the API; authorization
decisions remain the backend's responsibility.

## Run locally

Activate the project's virtual environment, then install the pinned
dependencies if needed:

```bash
python -m pip install -r requirements.txt
```

Run the corrected-mode suite:

```bash
AUTHZ_MODE=corrected python -m pytest -q
```

Run the API locally for manual exploration:

```bash
AUTHZ_MODE=corrected python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The frontend is available at `http://127.0.0.1:8000/`. Interactive API
documentation is available at `http://127.0.0.1:8000/docs`.

Use the page to select a synthetic identity, request a record, or call
the administrator summary endpoint. It displays the actual HTTP status
and response body returned by the API; it does not simulate authorization.

Use only synthetic data and keep the server bound to loopback. Never run
the vulnerable mode as a network-accessible server.

## Reproduce the vulnerable behavior

Run the BOLA HTTP assertions in vulnerable mode:

```bash
AUTHZ_MODE=vulnerable python -m pytest -q \
  tests/test_record_authorization.py::test_record_read_authorization
```

Run the BFLA role-check assertions in vulnerable mode:

```bash
AUTHZ_MODE=vulnerable python -m pytest -q \
  tests/test_function_authorization.py::test_admin_summary_requires_admin_role \
  tests/test_function_authorization.py::test_member_cannot_spoof_admin_role_header
```

These commands are expected to report failures for authorization assertions
that expect corrected behavior. Those failures are evidence of the deliberately
introduced flaws, not evidence that vulnerable mode is acceptable.

The full suite includes a test that explicitly requires corrected mode, so
do not expect the entire suite to pass unchanged with `AUTHZ_MODE=vulnerable`.

## Verification evidence

Verified locally:

- Corrected mode: **31 tests passed**.
- Vulnerable BOLA assertions: **5 failed, 9 passed**; the five failures
  exposed inaccessible records returning `200` instead of `404`.
- Vulnerable BFLA role assertions: **3 failed, 3 passed**; the three failures
  exposed member requests returning `200` instead of `403`.
- BOLA guard-removal check: the cross-tenant regression test failed when the
  record authorization guard was temporarily removed; the source was restored
  and the corrected suite passed.
- BFLA guard-removal check: three role-related assertions failed when the
  administrator-role guard was temporarily disabled; the source was restored
  and the corrected suite passed.

These results are local test evidence for this implementation and its
synthetic fixtures. They are not a security certification or proof about a
deployed system.

## Limitations

This is a deliberately small learning and portfolio project, not a
production-ready authorization framework.

It does not demonstrate:

- Real authentication, credential storage, token expiry, or session security
- Database-backed access control or concurrent data changes
- Production deployment, infrastructure security, or operational monitoring
- Exhaustive authorization coverage or a formal security audit

The fixed tokens are test fixtures, not production credentials. The vulnerable
mode intentionally weakens authorization and must remain local-only.

## Scope

The current stage focuses on two API authorization failure classes:

1. BOLA: record-level ownership and tenant isolation
2. BFLA: administrator-only function access

Database integration, deployment, and additional authorization scenarios
remain out of scope for this stage. The small frontend is for local
demonstration only, not a production interface.
