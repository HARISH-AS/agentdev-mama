"""
Baseline tests for the seeded employee table backend.

Kept intentionally focused on the API contract (status code, shape,
count) rather than exact data values, so these keep passing even if the
Developer Agent's future patches touch EMPLOYEES data slightly, and so
they don't need updating just because of unrelated formatting changes.
"""
from app import app


def test_index_returns_200():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200


def test_get_employees_returns_200():
    client = app.test_client()
    response = client.get("/api/employees")
    assert response.status_code == 200


def test_get_employees_returns_list_of_dicts_with_expected_keys():
    client = app.test_client()
    response = client.get("/api/employees")
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 5
    expected_keys = {"id", "name", "department", "salary"}
    for employee in data:
        assert expected_keys.issubset(employee.keys())


def test_export_csv_returns_200_and_correct_content_type():
    client = app.test_client()
    response = client.get("/export")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("Content-Type", "")


def test_export_csv_contains_all_employees():
    client = app.test_client()
    response = client.get("/export")
    csv_text = response.data.decode("utf-8")
    lines = [line for line in csv_text.strip().splitlines() if line]
    # header + 5 employee rows = 6 lines
    assert len(lines) == 6
    assert "Asha Rao" in csv_text
    assert "Ethan Brooks" in csv_text