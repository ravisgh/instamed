"""eVital importer tests. All rows here are made up; no real store data."""

from datetime import date

import pytest

from app.importers.evital import (
    CleanRow,
    clean_row,
    clean_rows,
    parse_expiry,
    schedule_from,
)

TODAY = date(2026, 11, 21)


def row(**overrides):
    base = {
        "Rio IMS Location": "IPM-SR1-R01",
        "Medicine Name": "  Testocin 500 Tablet ",
        "Pack Size": "10 Tablet",
        "Manufacturer": "Example Pharma Ltd",
        "Salt": "Testocin (500mg)",
        "Schedule": "H",
        "GST %": 5,
        "HSN": "30049099",
        "MRP": 120.5,
        "PTR": 90.0,
        "Stock (Loose)": 30,
        "Stock (Strip)": 3,
        "Stock wale batch": 2,
        "Jaldi expiry": "07/28",
    }
    return {**base, **overrides}


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("07/28", date(2028, 7, 31)), ("02/28", date(2028, 2, 29)), ("12/26", date(2026, 12, 31))],
)
def test_parse_expiry_uses_last_day_of_month(raw, expected):
    assert parse_expiry(raw) == expected


@pytest.mark.parametrize("raw", ["2028-07", "13/28", "7/2028", None, ""])
def test_parse_expiry_rejects_bad_format(raw):
    with pytest.raises(ValueError):
        parse_expiry(raw)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("H", ("H", True)),
        ("H1", ("H1", True)),
        ("X", ("X", True)),
        ("G", ("G", False)),
        (None, ("OTC", False)),
        ("-", ("OTC", False)),
        (" h1 ", ("H1", True)),
    ],
)
def test_schedule_mapping(raw, expected):
    assert schedule_from(raw) == expected


def test_schedule_rejects_unknown():
    with pytest.raises(ValueError):
        schedule_from("Q")


def test_clean_row_maps_all_fields():
    result = clean_row(row(), TODAY)

    assert isinstance(result, CleanRow)
    medicine = result.medicine
    assert medicine.name == "Testocin 500 Tablet"
    assert medicine.composition == "Testocin (500mg)"
    assert medicine.pack_size == "10 Tablet"
    assert medicine.mrp == 120.5
    assert medicine.schedule == "H"
    assert medicine.prescription_required is True
    assert medicine.gst_percent == 5
    assert medicine.hsn_code == "30049099"
    assert result.quantity == 3
    assert result.price == 120.5
    assert result.batch_count == 2
    assert result.earliest_expiry == date(2028, 7, 31)
    assert result.location == "IPM-SR1-R01"


def test_clean_row_never_carries_ptr():
    result = clean_row(row(PTR=777.77), TODAY)

    assert "777.77" not in repr(result)
    assert "ptr" not in repr(result).lower()


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"Salt": None}, "missing salt"),
        ({"Salt": " - "}, "missing salt"),
        ({"HSN": None}, "missing HSN"),
        ({"HSN": "30A4"}, "invalid hsn_code"),
        ({"Jaldi expiry": "11/26"}, "expired or expiring within 30 days"),
        ({"Jaldi expiry": "bad"}, "invalid expiry"),
        ({"Stock (Strip)": 0}, "partial pack only"),
        ({"MRP": 0}, "invalid mrp"),
        ({"GST %": 7}, "invalid gst_percent"),
        ({"Schedule": "Q"}, "unknown schedule"),
    ],
)
def test_clean_row_drop_reasons(overrides, reason):
    assert clean_row(row(**overrides), TODAY) == reason


def test_clean_rows_drops_every_copy_of_a_duplicate():
    rows = [
        row(),
        row(**{"Medicine Name": "testocin 500 tablet"}),  # same name + pack, other case
        row(**{"Medicine Name": "Othermed Syrup", "Pack Size": "100 Ml"}),
        row(Salt=None),
    ]

    clean, dropped = clean_rows(rows, TODAY)

    assert [c.medicine.name for c in clean] == ["Othermed Syrup"]
    assert sorted(d.reason for d in dropped) == [
        "duplicate name + pack",
        "duplicate name + pack",
        "missing salt",
    ]
    assert {d.row_number for d in dropped} == {2, 3, 5}  # spreadsheet rows (header is 1)
