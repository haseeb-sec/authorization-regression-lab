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


def get_record(record_id: str, identity: str | None = None):
    headers = {}
    if identity is not None:
        headers["Authorization"] = f"Bearer {TOKENS[identity]}"

    return client.get(f"/records/{record_id}", headers=headers)


@pytest.mark.parametrize(
    ("identity", "record_id", "expected_status"),
    [
        (None, "record_a1", 401),
        ("member_a", "record_a1", 200),
        ("member_a", "record_a3", 200),
        ("member_a", "record_a2", 404),
        ("member_a", "record_b1", 404),
        ("admin_a", "record_a1", 200),
        ("admin_a", "record_a2", 200),
        ("admin_a", "record_b1", 404),
        ("admin_b", "record_b2", 200),
        ("admin_b", "record_a1", 404),
        ("member_b", "record_a1", 404),
        ("member_b", "record_b1", 200),
        ("admin_b", "record_b1", 200),
        ("member_a", "record_does_not_exist", 404),
    ],
)
def test_record_read_authorization(
    identity: str | None,
    record_id: str,
    expected_status: int,
) -> None:
    response = get_record(record_id, identity)

    assert response.status_code == expected_status


def test_invalid_bearer_token_is_rejected() -> None:
    response = client.get(
        "/records/record_a1",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )

    assert response.status_code == 401


def test_caller_supplied_identity_headers_are_not_trusted() -> None:
    response = client.get(
        "/records/record_b1",
        headers={
            "Authorization": "Bearer token-member-a",
            "X-User-Id": "admin_b",
            "X-Tenant-Id": "B",
            "X-Role": "tenant_admin",
        },
    )

    assert response.status_code == 404


def test_regression_suite_runs_in_corrected_mode() -> None:
    from app.main import AUTHZ_MODE

    assert AUTHZ_MODE == "corrected"
