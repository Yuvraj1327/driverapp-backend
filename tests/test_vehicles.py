"""
Tests for vehicle CRUD endpoints.
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_create_and_get_vehicle(client: AsyncClient, admin_token: str):
    payload = {
        "registration_number": "DXB-T-11111",
        "make": "Toyota",
        "model": "Hilux",
        "year": 2023,
        "current_odometer": 0,
    }
    create_response = await client.post(
        "/api/v1/vehicles/", json=payload, headers=auth_headers(admin_token)
    )
    assert create_response.status_code == 201
    vehicle = create_response.json()
    assert vehicle["registration_number"] == "DXB-T-11111"

    get_response = await client.get(
        f"/api/v1/vehicles/{vehicle['id']}", headers=auth_headers(admin_token)
    )
    assert get_response.status_code == 200
    assert get_response.json()["make"] == "Toyota"


async def test_duplicate_registration_conflict(client: AsyncClient, admin_token: str):
    payload = {
        "registration_number": "DXB-T-22222",
        "make": "Ford",
        "model": "Transit",
        "year": 2022,
    }
    first = await client.post("/api/v1/vehicles/", json=payload, headers=auth_headers(admin_token))
    assert first.status_code == 201

    second = await client.post("/api/v1/vehicles/", json=payload, headers=auth_headers(admin_token))
    assert second.status_code == 409


async def test_list_vehicles_paginated(client: AsyncClient, admin_token: str):
    for i in range(3):
        await client.post(
            "/api/v1/vehicles/",
            json={
                "registration_number": f"DXB-P-{i}",
                "make": "Nissan",
                "model": "Urvan",
                "year": 2021,
            },
            headers=auth_headers(admin_token),
        )
    response = await client.get(
        "/api/v1/vehicles/?page=1&page_size=2", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert len(body["items"]) == 2
    assert body["total"] >= 3


async def test_update_and_delete_vehicle(client: AsyncClient, admin_token: str):
    create_response = await client.post(
        "/api/v1/vehicles/",
        json={"registration_number": "DXB-U-999", "make": "Kia", "model": "Bongo", "year": 2020},
        headers=auth_headers(admin_token),
    )
    vehicle_id = create_response.json()["id"]

    update_response = await client.put(
        f"/api/v1/vehicles/{vehicle_id}", json={"color": "Red"}, headers=auth_headers(admin_token)
    )
    assert update_response.status_code == 200
    assert update_response.json()["color"] == "Red"

    delete_response = await client.delete(
        f"/api/v1/vehicles/{vehicle_id}", headers=auth_headers(admin_token)
    )
    assert delete_response.status_code == 200

    get_response = await client.get(
        f"/api/v1/vehicles/{vehicle_id}", headers=auth_headers(admin_token)
    )
    assert get_response.status_code == 404


async def test_vehicles_require_auth(client: AsyncClient):
    response = await client.get("/api/v1/vehicles/")
    assert response.status_code == 401
