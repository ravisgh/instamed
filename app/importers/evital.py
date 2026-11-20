"""Turn an eVital stock export (xlsx) into clean InstaMed medicines + inventory rows.

Only rows with full details are kept: salt, HSN, valid schedule/GST/MRP, at least one
full pack in stock and at least 30 days to expiry. The purchase price (PTR) column is
never read.
"""

import calendar
import re
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.models.medicine import PRESCRIPTION_SCHEDULES, MedicineCreate

SHEET_PREFIX = "FINAL"
MIN_SHELF_LIFE = timedelta(days=30)
_EXPIRY = re.compile(r"(\d{2})/(\d{2})")
_BLANK = {"", "-", "na", "n/a", "null"}
_SCHEDULES = {"H", "H1", "X", "G"}


@dataclass(frozen=True)
class CleanRow:
    medicine: MedicineCreate
    quantity: int
    price: float
    earliest_expiry: date
    batch_count: int
    location: str | None


@dataclass(frozen=True)
class Dropped:
    row_number: int
    name: str
    reason: str


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _is_blank(value: Any) -> bool:
    return _text(value).lower() in _BLANK


def parse_expiry(raw: Any) -> date:
    """'07/28' (MM/YY) -> 2028-07-31. Medicines expire at the end of the printed month."""
    match = _EXPIRY.fullmatch(_text(raw))
    if not match:
        raise ValueError(f"expected MM/YY, got {raw!r}")
    month, year = int(match.group(1)), 2000 + int(match.group(2))
    if not 1 <= month <= 12:
        raise ValueError(f"bad month in {raw!r}")
    return date(year, month, calendar.monthrange(year, month)[1])


def schedule_from(raw: Any) -> tuple[str, bool]:
    """eVital schedule -> (schedule, prescription_required). Blank means OTC."""
    if _is_blank(raw):
        return "OTC", False
    schedule = _text(raw).upper()
    if schedule not in _SCHEDULES:
        raise ValueError(f"unknown schedule {raw!r}")
    return schedule, schedule in PRESCRIPTION_SCHEDULES


def clean_row(row: dict[str, Any], today: date) -> CleanRow | str:
    """Return a CleanRow, or a short reason string if the row is dropped."""
    if _is_blank(row.get("Salt")):
        return "missing salt"
    if _is_blank(row.get("HSN")):
        return "missing HSN"
    try:
        schedule, prescription_required = schedule_from(row.get("Schedule"))
    except ValueError:
        return "unknown schedule"
    try:
        expiry = parse_expiry(row.get("Jaldi expiry"))
    except ValueError:
        return "invalid expiry"
    if expiry < today + MIN_SHELF_LIFE:
        return "expired or expiring within 30 days"
    packs = row.get("Stock (Strip)")
    if not isinstance(packs, int) or packs < 1:
        return "partial pack only"

    try:
        medicine = MedicineCreate(
            name=_text(row.get("Medicine Name")),
            composition=_text(row.get("Salt")),
            manufacturer=_text(row.get("Manufacturer")),
            pack_size=_text(row.get("Pack Size")),
            mrp=row.get("MRP"),
            schedule=schedule,
            prescription_required=prescription_required,
            gst_percent=row.get("GST %"),
            hsn_code=_text(row.get("HSN")),
        )
    except ValidationError as exc:
        return f"invalid {exc.errors()[0]['loc'][0]}"

    batches = row.get("Stock wale batch")
    return CleanRow(
        medicine=medicine,
        quantity=packs,
        price=medicine.mrp,  # sell at MRP
        earliest_expiry=expiry,
        batch_count=batches if isinstance(batches, int) and batches >= 1 else 1,
        location=_text(row.get("Rio IMS Location")) or None,
    )


def clean_rows(
    rows: Iterable[dict[str, Any]], today: date
) -> tuple[list[CleanRow], list[Dropped]]:
    """Clean every row and drop all copies of any (name, pack_size) seen more than once.

    Row numbers are spreadsheet rows: the header is row 1, so data starts at row 2.
    """
    results = [(number, row, clean_row(row, today)) for number, row in enumerate(rows, start=2)]

    def key(result: CleanRow) -> tuple[str, str]:
        return result.medicine.name.lower(), result.medicine.pack_size.lower()

    counts = Counter(key(r) for _, _, r in results if isinstance(r, CleanRow))
    clean: list[CleanRow] = []
    dropped: list[Dropped] = []
    for number, row, result in results:
        if isinstance(result, CleanRow) and counts[key(result)] > 1:
            result = "duplicate name + pack"
        if isinstance(result, CleanRow):
            clean.append(result)
        else:
            dropped.append(Dropped(number, _text(row.get("Medicine Name")), result))
    return clean, dropped


def read_rows(path: Path) -> Iterator[dict[str, Any]]:
    """Yield rows (as header -> value dicts) from the workbook's FINAL sheet."""
    from openpyxl import load_workbook  # dev-only dependency, imported lazily

    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = next(ws for ws in workbook.worksheets if ws.title.startswith(SHEET_PREFIX))
    except StopIteration:
        raise ValueError(f"no sheet starting with {SHEET_PREFIX!r} in {path.name}") from None
    values = sheet.iter_rows(values_only=True)
    header = [_text(h) for h in next(values)]
    try:
        for raw in values:
            if any(v is not None for v in raw):
                yield dict(zip(header, raw, strict=False))
    finally:
        workbook.close()
