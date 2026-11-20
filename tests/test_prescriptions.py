import pytest
from bson import ObjectId

from tests.conftest import NO_AUTH, create_user

PDF = ("rx.pdf", b"%PDF-1.4 fake prescription", "application/pdf")


def upload(client, user, file=PDF):
    return client.post("/prescriptions", files={"file": file}, headers=user["headers"])


def test_customer_uploads_prescription(client, customer):
    response = upload(client, customer)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["user_id"] == customer["id"]
    assert body["original_filename"] == "rx.pdf"
    assert body["content_type"] == "application/pdf"
    assert body["size_bytes"] == len(PDF[1])
    assert "stored_name" not in body  # server-side path stays private


@pytest.mark.parametrize(
    "file",
    [
        ("notes.txt", b"hello", "text/plain"),
        ("empty.pdf", b"", "application/pdf"),
        ("big.pdf", b"x" * (5 * 1024 * 1024 + 1), "application/pdf"),
    ],
)
def test_rejects_bad_files(client, customer, file):
    assert upload(client, customer, file).status_code in (413, 415, 422)


def test_upload_needs_login(client):
    assert client.post("/prescriptions", files={"file": PDF}, headers=NO_AUTH).status_code == 401


def test_owner_and_staff_can_read_others_cannot(client, customer, pharmacist):
    rx = upload(client, customer).json()
    stranger = create_user("customer", email="stranger@example.com")

    assert client.get(f"/prescriptions/{rx['id']}", headers=customer["headers"]).status_code == 200
    assert (
        client.get(f"/prescriptions/{rx['id']}", headers=pharmacist["headers"]).status_code == 200
    )
    assert client.get(f"/prescriptions/{rx['id']}", headers=stranger["headers"]).status_code == 404

    file = client.get(f"/prescriptions/{rx['id']}/file", headers=customer["headers"])
    assert file.status_code == 200
    assert file.content == PDF[1]


def test_list_is_scoped_to_the_customer(client, customer, pharmacist):
    upload(client, customer)
    other = create_user("customer", email="other@example.com")
    upload(client, other)

    assert len(client.get("/prescriptions", headers=customer["headers"]).json()) == 1
    assert len(client.get("/prescriptions", headers=pharmacist["headers"]).json()) == 2
    pending = client.get("/prescriptions?status=pending", headers=pharmacist["headers"]).json()
    assert len(pending) == 2


def test_pharmacist_reviews(client, customer, pharmacist):
    rx = upload(client, customer).json()

    review = client.patch(
        f"/prescriptions/{rx['id']}/review",
        json={"status": "approved", "note": "Valid, signed"},
        headers=pharmacist["headers"],
    )

    assert review.status_code == 200
    assert review.json()["status"] == "approved"
    assert review.json()["reviewed_by"] == pharmacist["id"]
    again = client.patch(
        f"/prescriptions/{rx['id']}/review",
        json={"status": "rejected"},
        headers=pharmacist["headers"],
    )
    assert again.status_code == 409  # already reviewed


def test_customer_cannot_review(client, customer):
    rx = upload(client, customer).json()

    response = client.patch(
        f"/prescriptions/{rx['id']}/review",
        json={"status": "approved"},
        headers=customer["headers"],
    )

    assert response.status_code == 403


def test_unknown_prescription_is_404(client, pharmacist):
    assert (
        client.get(f"/prescriptions/{ObjectId()}", headers=pharmacist["headers"]).status_code == 404
    )
