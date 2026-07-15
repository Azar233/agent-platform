def _auth_headers(client):
    client.post(
        "/api/auth/register",
        json={
            "username": "price_user",
            "email": "price_user@example.com",
            "password": "123456",
        },
    )
    login = client.post(
        "/api/auth/login",
        json={"username": "price_user", "password": "123456"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_price_category_200_can_be_created_and_updated(client):
    headers = _auth_headers(client)
    created = client.post(
        "/api/prices",
        headers=headers,
        json={
            "category_id": 200,
            "sku_name": "stationery",
            "name": "文具",
            "barcode": "6900000000200",
            "unit_price": 2.5,
            "currency": "CNY",
        },
    )
    assert created.status_code == 201

    updated = client.put(
        "/api/prices/200",
        headers=headers,
        json={
            "sku_name": "stationery-updated",
            "name": "文具（已更新）",
            "barcode": "6900000000201",
            "unit_price": 3.75,
            "currency": "CNY",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["category_id"] == 200
    assert updated.json()["name"] == "文具（已更新）"
    assert updated.json()["unit_price"] == 3.75

    fetched = client.get("/api/prices/200", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["barcode"] == "6900000000201"


def test_search_prices_by_name_and_barcode(client):
    headers = _auth_headers(client)
    # 初始化两个商品
    client.post(
        "/api/prices",
        headers=headers,
        json={
            "category_id": 198,
            "sku_name": "search_test_a",
            "name": "搜索测试商品A",
            "barcode": "6900000000198",
            "unit_price": 1.0,
            "currency": "CNY",
        },
    )
    client.post(
        "/api/prices",
        headers=headers,
        json={
            "category_id": 199,
            "sku_name": "search_test_b",
            "name": "其他商品",
            "barcode": "6900000000199",
            "unit_price": 2.0,
            "currency": "CNY",
        },
    )

    by_name = client.get("/api/prices?q=搜索测试商品A", headers=headers)
    assert by_name.status_code == 200
    assert len(by_name.json()) == 1
    assert by_name.json()[0]["category_id"] == 198

    by_barcode = client.get("/api/prices?q=6900000000199", headers=headers)
    assert by_barcode.status_code == 200
    assert len(by_barcode.json()) == 1
    assert by_barcode.json()[0]["category_id"] == 199


def test_batch_delete_prices(client):
    headers = _auth_headers(client)
    client.post(
        "/api/prices",
        headers=headers,
        json={
            "category_id": 196,
            "sku_name": "batch_a",
            "name": "批量删除A",
            "barcode": "6900000000196",
            "unit_price": 1.0,
            "currency": "CNY",
        },
    )
    client.post(
        "/api/prices",
        headers=headers,
        json={
            "category_id": 197,
            "sku_name": "batch_b",
            "name": "批量删除B",
            "barcode": "6900000000197",
            "unit_price": 2.0,
            "currency": "CNY",
        },
    )

    deleted = client.post("/api/prices/batch-delete", headers=headers, json=[196, 197])
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] == 2

    for cid in (196, 197):
        assert client.get(f"/api/prices/{cid}", headers=headers).status_code == 404
