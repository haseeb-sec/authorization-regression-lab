import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

TOKENS = {
    "member_a": "token-member-a",
    "admin_a": "token-admin-a",
    "member_b": "token-member-b",
    "admin_b": "token-admin-b",
}


def get_admin_summary(identity: str | None = None):
    headers = {}
    if identity is not None:
        headers["Authorization"] = f"Bearer {TOKENS[identity]}"

    return client.get("/admin/summary", headers=headers)


@pytest.mark.parametrize(
    ("identity", "expected_status"),
    [
        (None, 401),
        ("member_a", 403),
        ("member_b", 403),
        ("admin_a", 200),
        ("admin_b", 200),
    ],
)
def test_admin_summary_requires_admin_role(
    identity: str | None,
    expected_status: int,
) -> None:
    response = get_admin_summary(identity)

    assert response.status_code == expected_status


@pytest.mark.parametrize(
    ("identity", "expected_tenant", "expected_count"),
    [
        ("admin_a", "A", 3),
        ("admin_b", "B", 2),
    ],
)
def test_admin_summary_is_scoped_to_admin_tenant(
    identity: str,
    expected_tenant: str,
    expected_count: int,
) -> None:
    response = get_admin_summary(identity)

    assert response.status_code == 200
    assert response.json() == {
        "tenant_id": expected_tenant,
        "record_count": expected_count,
    }


def test_invalid_token_cannot_access_admin_summary() -> None:
    response = client.get(
        "/admin/summary",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )

    assert response.status_code == 401


def test_member_cannot_spoof_admin_role_header() -> None:
    response = client.get(
        "/admin/summary",
        headers={
            "Authorization": "Bearer token-member-a",
            "X-Role": "tenant_admin",
            "X-Tenant-Id": "B",
        },
    )

    assert response.status_code == 403


def test_admin_summary_ignores_spoofed_tenant_header() -> None:
    response = client.get(
        "/admin/summary",
        headers={
            "Authorization": "Bearer token-admin-a",
            "X-Tenant-Id": "B",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "tenant_id": "A",
        "record_count": 3,
    }
