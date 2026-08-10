"""
Tests covering driver creation and KM log distance auto-calculation.
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_create_driver_provisions_user(client: AsyncClient, admin_token: str):
    payload = {
        "full_name": "New Driver",
        "email": "newdriver@test.com",
        "phone": "+971500000099",
        "password": "Driver@123",
        "license_number": "LIC-999888",
    }
    response = await client.post("/api/v1/drivers/", json=payload, headers=auth_headers(admin_token))
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "newdriver@test.com"
    assert body["license_number"] == "LIC-999888"
    assert body["is_available"] is True


async def test_km_log_distance_auto_calculated(client: AsyncClient, admin_token: str):
    vehicle_resp = await client.post(
        "/api/v1/vehicles/",
        json={
            "registration_number": "DXB-K-100",
            "make": "Toyota",
            "model": "Hiace",
            "year": 2022,
            "current_odometer": 1000,
        },
        headers=auth_headers(admin_token),
    )
    vehicle_id = vehicle_resp.json()["id"]

    driver_resp = await client.post(
        "/api/v1/drivers/",
        json={
            "full_name": "KM Driver",
            "email": "kmdriver@test.com",
            "password": "Driver@123",
            "license_number": "LIC-777",
        },
        headers=auth_headers(admin_token),
    )
    driver_id = driver_resp.json()["id"]

    log_resp = await client.post(
        "/api/v1/km-logs/",
        json={
            "vehicle_id": vehicle_id,
            "driver_id": driver_id,
            "start_odometer": 1000,
            "end_odometer": 1120.5,
            "trip_purpose": "Delivery run",
        },
        headers=auth_headers(admin_token),
    )
    assert log_resp.status_code == 201
    body = log_resp.json()
    assert body["distance_covered"] == 120.5

    vehicle_after = await client.get(
        f"/api/v1/vehicles/{vehicle_id}", headers=auth_headers(admin_token)
    )
    assert vehicle_after.json()["current_odometer"] == 1120.5


async def test_km_log_rejects_start_below_vehicle_odometer(client: AsyncClient, admin_token: str):
    vehicle_resp = await client.post(
        "/api/v1/vehicles/",
        json={
            "registration_number": "DXB-K-200",
            "make": "Ford",
            "model": "Transit",
            "year": 2023,
            "current_odometer": 5000,
        },
        headers=auth_headers(admin_token),
    )
    vehicle_id = vehicle_resp.json()["id"]

    driver_resp = await client.post(
        "/api/v1/drivers/",
        json={
            "full_name": "Edge Driver",
            "email": "edgedriver@test.com",
            "password": "Driver@123",
            "license_number": "LIC-555",
        },
        headers=auth_headers(admin_token),
    )
    driver_id = driver_resp.json()["id"]

    log_resp = await client.post(
        "/api/v1/km-logs/",
        json={
            "vehicle_id": vehicle_id,
            "driver_id": driver_id,
            "start_odometer": 4000,
            "end_odometer": 4100,
        },
        headers=auth_headers(admin_token),
    )
    assert log_resp.status_code == 422


async def test_km_stats_endpoints(client: AsyncClient, admin_token: str):
    vehicle_resp = await client.post(
        "/api/v1/vehicles/",
        json={
            "registration_number": "DXB-K-300",
            "make": "Toyota",
            "model": "Hiace",
            "year": 2022,
            "current_odometer": 2000,
        },
        headers=auth_headers(admin_token),
    )
    vehicle_id = vehicle_resp.json()["id"]

    driver_resp = await client.post(
        "/api/v1/drivers/",
        json={
            "full_name": "Stats Driver",
            "email": "statsdriver@test.com",
            "password": "Driver@123",
            "license_number": "LIC-STATS-1",
        },
        headers=auth_headers(admin_token),
    )
    driver_id = driver_resp.json()["id"]

    await client.post(
        "/api/v1/km-logs/",
        json={
            "vehicle_id": vehicle_id,
            "driver_id": driver_id,
            "start_odometer": 2000,
            "end_odometer": 2150,
        },
        headers=auth_headers(admin_token),
    )

    vehicle_stats = await client.get(
        f"/api/v1/km-logs/vehicle/{vehicle_id}/stats", headers=auth_headers(admin_token)
    )
    assert vehicle_stats.status_code == 200
    stats_body = vehicle_stats.json()
    assert stats_body["today_km"] == 150.0
    assert stats_body["total_km"] == 150.0
    assert stats_body["current_month_km"] == 150.0

    driver_stats = await client.get(
        f"/api/v1/km-logs/driver/{driver_id}/stats", headers=auth_headers(admin_token)
    )
    assert driver_stats.status_code == 200
    assert driver_stats.json()["total_km"] == 150.0
