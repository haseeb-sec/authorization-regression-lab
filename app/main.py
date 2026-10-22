import os
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

app = FastAPI(
    title="Authorization Regression Lab",
    description="A local learning lab for testing API authorization.",
    version="0.1.0",
)

bearer_scheme = HTTPBearer(auto_error=False)

AUTHZ_MODE = os.getenv("AUTHZ_MODE", "corrected").strip().lower()

if AUTHZ_MODE not in {"vulnerable", "corrected"}:
    raise RuntimeError(
        "AUTHZ_MODE must be either 'vulnerable' or 'corrected'"
    )

# Synthetic tokens for local testing only. These are not production credentials.
IDENTITIES = {
    "token-member-a": {
        "user_id": "member_a",
        "tenant_id": "A",
        "role": "member",
    },
    "token-admin-a": {
        "user_id": "admin_a",
        "tenant_id": "A",
        "role": "tenant_admin",
    },
    "token-member-b": {
        "user_id": "member_b",
        "tenant_id": "B",
        "role": "member",
    },
    "token-admin-b": {
        "user_id": "admin_b",
        "tenant_id": "B",
        "role": "tenant_admin",
    },
}

RECORDS = {
    "record_a1": {
        "record_id": "record_a1",
        "tenant_id": "A",
        "owner_id": "member_a",
        "description": "Synthetic Tenant A record 1",
    },
    "record_a2": {
        "record_id": "record_a2",
        "tenant_id": "A",
        "owner_id": "member_a2",
        "description": "Synthetic Tenant A record 2",
    },
    "record_a3": {
        "record_id": "record_a3",
        "tenant_id": "A",
        "owner_id": "member_a",
        "description": "Synthetic Tenant A record 3",
    },
    "record_b1": {
        "record_id": "record_b1",
        "tenant_id": "B",
        "owner_id": "member_b",
        "description": "Synthetic Tenant B record 1",
    },
    "record_b2": {
        "record_id": "record_b2",
        "tenant_id": "B",
        "owner_id": "member_b",
        "description": "Synthetic Tenant B record 2",
    },
}


def get_current_identity(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> dict[str, str]:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    identity = IDENTITIES.get(credentials.credentials)
    if identity is None:
        raise HTTPException(status_code=401, detail="Invalid bearer token")

    return identity


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/records/{record_id}")
def get_record(
    record_id: str,
    identity: Annotated[dict[str, str], Depends(get_current_identity)],
) -> dict[str, str]:
    record = RECORDS.get(record_id)

    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")

    if AUTHZ_MODE == "corrected":
        same_tenant = record["tenant_id"] == identity["tenant_id"]
        is_tenant_admin = identity["role"] == "tenant_admin"
        is_owner = record["owner_id"] == identity["user_id"]

        if not same_tenant or not (is_tenant_admin or is_owner):
            raise HTTPException(status_code=404, detail="Record not found")

    return record


@app.get("/admin/summary")
def get_admin_summary(
    identity: Annotated[dict[str, str], Depends(get_current_identity)],
) -> dict[str, str | int]:
    if AUTHZ_MODE == "corrected" and identity["role"] != "tenant_admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator role required",
        )

    tenant_records = [
        record
        for record in RECORDS.values()
        if record["tenant_id"] == identity["tenant_id"]
    ]

    return {
        "tenant_id": identity["tenant_id"],
        "record_count": len(tenant_records),
    }
