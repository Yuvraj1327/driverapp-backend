"""
End-to-end tests for the expense approval workflow and reporting/export endpoints.
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _setup_vehicle_driver_category(client: AsyncClient, token: str):
    vehicle = (
        await client.post(
            "/api/v1/vehicles/",
            json={"registration_number": "DXB-E-1", "make": "Toyota", "model": "Hiace", "year": 2022},
            headers=auth_headers(token),
        )
    ).json()
    driver = (
        await client.post(
            "/api/v1/drivers/",
            json={
                "full_name": "Expense Driver",
                "email": "expensedriver@test.com",
                "password": "Driver@123",
                "license_number": "LIC-EXP-1",
            },
            headers=auth_headers(token),
        )
    ).json()
    category = (
        await client.post(
            "/api/v1/expense-categories/",
            json={"name": "Fuel", "description": "Fuel costs"},
            headers=auth_headers(token),
        )
    ).json()
    return vehicle, driver, category


async def test_expense_lifecycle_and_approval(client: AsyncClient, admin_token: str):
    vehicle, driver, category = await _setup_vehicle_driver_category(client, admin_token)

    create_resp = await client.post(
        "/api/v1/expenses/",
        json={
            "vehicle_id": vehicle["id"],
            "driver_id": driver["id"],
            "category_id": category["id"],
            "amount": 150.5,
            "description": "Fuel refill",
        },
        headers=auth_headers(admin_token),
    )
    assert create_resp.status_code == 201
    expense = create_resp.json()
    assert expense["status"] == "pending"

    review_resp = await client.post(
        f"/api/v1/expenses/{expense['id']}/review",
        json={"decision": "approved", "remarks": "Looks good"},
        headers=auth_headers(admin_token),
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["status"] == "approved"

    second_review = await client.post(
        f"/api/v1/expenses/{expense['id']}/review",
        json={"decision": "rejected"},
        headers=auth_headers(admin_token),
    )
    assert second_review.status_code == 409


async def test_dashboard_summary(client: AsyncClient, admin_token: str):
    response = await client.get("/api/v1/reports/dashboard", headers=auth_headers(admin_token))
    assert response.status_code == 200
    body = response.json()
    assert "total_vehicles" in body
    assert "pending_expense_approvals" in body


async def test_report_export_pdf_and_excel(client: AsyncClient, admin_token: str):
    vehicle, driver, category = await _setup_vehicle_driver_category(client, admin_token)
    await client.post(
        "/api/v1/expenses/",
        json={
            "vehicle_id": vehicle["id"],
            "driver_id": driver["id"],
            "category_id": category["id"],
            "amount": 75.0,
            "description": "Toll",
        },
        headers=auth_headers(admin_token),
    )

    pdf_resp = await client.post(
        "/api/v1/reports/export",
        json={"report_type": "monthly", "export_format": "pdf"},
        headers=auth_headers(admin_token),
    )
    assert pdf_resp.status_code == 200
    assert pdf_resp.json()["file_path"].endswith(".pdf")

    excel_resp = await client.post(
        "/api/v1/reports/export",
        json={"report_type": "expense_wise", "export_format": "excel"},
        headers=auth_headers(admin_token),
    )
    assert excel_resp.status_code == 200
    assert excel_resp.json()["file_path"].endswith(".xlsx")
