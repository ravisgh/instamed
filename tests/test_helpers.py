import pytest
from bson import ObjectId
from fastapi import HTTPException
from pydantic import BaseModel, ValidationError

from app.core.ids import ObjectIdStr, document_to_out, parse_object_id


def test_parse_object_id_accepts_valid_id():
    oid = ObjectId()

    assert parse_object_id(str(oid)) == oid


@pytest.mark.parametrize("bad", ["abc", "", "123", "zzzzzzzzzzzzzzzzzzzzzzzz"])
def test_parse_object_id_rejects_invalid_id_with_400(bad):
    with pytest.raises(HTTPException) as exc:
        parse_object_id(bad)

    assert exc.value.status_code == 400


def test_object_id_str_field_validates_format():
    class Model(BaseModel):
        ref: ObjectIdStr

    good = str(ObjectId())
    assert Model(ref=good).ref == good
    with pytest.raises(ValidationError):
        Model(ref="not-an-id")


def test_document_to_out_renames_mongo_id():
    oid = ObjectId()

    out = document_to_out({"_id": oid, "name": "Dolo"})

    assert out == {"id": str(oid), "name": "Dolo"}
