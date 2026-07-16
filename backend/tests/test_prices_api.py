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


def _seed_dataset(client, db_session):
    from app.entity.db_models import (
        DatasetClassMapping,
        DatasetVersion,
        DetectionScene,
        Product,
        ProductPrice,
        User,
    )

    headers = _auth_headers(client)
    user = db_session.query(User).filter_by(username="price_user").one()
    scene = DetectionScene(
        name="price_scene",
        display_name="价目表测试场景",
        category="retail",
        class_names=["cola", "chips"],
        created_by=user.id,
    )
    cola = Product(
        product_key="prod:price-cola",
        name="可乐",
        sku_name="cola",
        barcode="6900000000101",
    )
    chips = Product(
        product_key="prod:price-chips",
        name="薯片",
        sku_name="chips",
        barcode="6900000000102",
    )
    unrelated = Product(
        product_key="prod:unrelated",
        name="其他数据集商品",
        sku_name="unrelated",
        barcode="6900000000199",
    )
    db_session.add_all([scene, cola, chips, unrelated])
    db_session.flush()
    dataset = DatasetVersion(
        scene_id=scene.id,
        version="price-v1",
        name="价目表版本",
        status="pending_train",
        storage_path="dataset_versions/price-v1",
        data_yaml_path="data.yaml",
        class_count=2,
        created_by=user.id,
    )
    db_session.add(dataset)
    db_session.flush()
    db_session.add_all(
        [
            DatasetClassMapping(
                dataset_version_id=dataset.id,
                class_index=0,
                product_id=cola.id,
                product_key=cola.product_key,
                category_id=101,
                class_name="cola",
                display_name="可乐",
            ),
            DatasetClassMapping(
                dataset_version_id=dataset.id,
                class_index=1,
                product_id=chips.id,
                product_key=chips.product_key,
                category_id=102,
                class_name="chips",
                display_name="薯片",
            ),
            ProductPrice(
                product_id=cola.id,
                category_id=101,
                sku_name="cola",
                name="可乐",
                barcode=cola.barcode,
                unit_price=3.5,
                currency="CNY",
            ),
            ProductPrice(
                product_id=unrelated.id,
                category_id=199,
                sku_name="unrelated",
                name="其他数据集商品",
                barcode=unrelated.barcode,
                unit_price=99,
                currency="CNY",
            ),
        ]
    )
    db_session.commit()
    return headers, dataset, cola, chips, unrelated


def test_prices_require_dataset_version_and_only_list_mapped_products(client, db_session):
    headers, dataset, cola, chips, unrelated = _seed_dataset(client, db_session)

    assert client.get("/api/prices", headers=headers).status_code == 422
    response = client.get(
        "/api/prices",
        headers=headers,
        params={"dataset_version_id": dataset.id},
    )
    assert response.status_code == 200, response.text
    rows = response.json()
    assert [row["product_id"] for row in rows] == [cola.id, chips.id]
    assert unrelated.id not in {row["product_id"] for row in rows}
    assert rows[0]["has_price"] is True
    assert rows[0]["unit_price"] == 3.5
    assert rows[1]["has_price"] is False
    assert rows[1]["unit_price"] is None

    searched = client.get(
        "/api/prices",
        headers=headers,
        params={"dataset_version_id": dataset.id, "q": "price-chips"},
    )
    assert searched.status_code == 200
    assert [row["product_id"] for row in searched.json()] == [chips.id]

    outside = client.get(
        f"/api/prices/{unrelated.id}",
        headers=headers,
        params={"dataset_version_id": dataset.id},
    )
    assert outside.status_code == 404
    assert "不属于所选数据集版本" in outside.json()["message"]


def test_update_only_existing_dataset_products_and_fill_missing_price(client, db_session):
    from app.entity.db_models import ProductPrice

    headers, dataset, cola, chips, unrelated = _seed_dataset(client, db_session)
    updated = client.put(
        f"/api/prices/{cola.id}",
        headers=headers,
        params={"dataset_version_id": dataset.id},
        json={"name": "冰镇可乐", "unit_price": 4.25, "currency": "CNY"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "冰镇可乐"
    assert updated.json()["unit_price"] == 4.25

    configured = client.put(
        f"/api/prices/{chips.id}",
        headers=headers,
        params={"dataset_version_id": dataset.id},
        json={"name": "薯片", "unit_price": 6.5, "currency": "CNY"},
    )
    assert configured.status_code == 200, configured.text
    assert configured.json()["has_price"] is True
    assert configured.json()["product_id"] == chips.id
    assert db_session.query(ProductPrice).filter_by(product_id=chips.id).one().unit_price == 6.5

    rejected = client.put(
        f"/api/prices/{unrelated.id}",
        headers=headers,
        params={"dataset_version_id": dataset.id},
        json={"unit_price": 1},
    )
    assert rejected.status_code == 404

    assert client.post("/api/prices", headers=headers, json={}).status_code in {404, 405}
    assert client.post("/api/prices/batch-delete", headers=headers, json=[101]).status_code in {404, 405}
    assert client.post("/api/prices/batch", headers=headers, json=[]).status_code in {404, 405}


def test_clear_price_keeps_product_and_dataset_mapping(client, db_session):
    from app.entity.db_models import DatasetClassMapping, Product, ProductPrice

    headers, dataset, cola, _chips, unrelated = _seed_dataset(client, db_session)
    rejected = client.delete(
        f"/api/prices/{unrelated.id}",
        headers=headers,
        params={"dataset_version_id": dataset.id},
    )
    assert rejected.status_code == 404
    assert db_session.query(ProductPrice).filter_by(product_id=unrelated.id).count() == 1

    deleted = client.delete(
        f"/api/prices/{cola.id}",
        headers=headers,
        params={"dataset_version_id": dataset.id},
    )
    assert deleted.status_code == 204, deleted.text
    assert db_session.query(ProductPrice).filter_by(product_id=cola.id).count() == 0
    assert db_session.query(Product).filter_by(id=cola.id).count() == 1
    assert (
        db_session.query(DatasetClassMapping)
        .filter_by(dataset_version_id=dataset.id, product_id=cola.id)
        .count()
        == 1
    )
