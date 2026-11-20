def test_lifespan_opens_the_test_database(client):
    assert client.app.state.db.name == "instamed_test"


def test_lifespan_creates_indexed_collections(client):
    response = client.get("/test-db")

    assert response.status_code == 200
    assert "pincode_zones" in response.json()["collections"]
