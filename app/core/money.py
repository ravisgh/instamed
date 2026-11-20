"""Money in rupees: validated to 2 decimals at the edge, added up with Decimal.

Prices travel as JSON numbers and are stored as doubles, but every amount is checked to
have at most 2 decimal places, and totals are computed with Decimal (ROUND_HALF_UP) so
they never pick up float noise like 0.1 + 0.2 = 0.30000000000000004.
"""

from collections.abc import Iterable
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated

from pydantic import AfterValidator

PAISA = Decimal("0.01")


def to_money(value: float | int | str | Decimal) -> Decimal:
    """Round to paise, half up, starting from the number's decimal text (not its binary)."""
    return Decimal(str(value)).quantize(PAISA, rounding=ROUND_HALF_UP)


def _two_decimals(value: float) -> float:
    if Decimal(str(value)) != Decimal(str(value)).quantize(PAISA):
        raise ValueError("amount can have at most 2 decimal places")
    return value


# Use for any rupee amount in request models.
Rupees = Annotated[float, AfterValidator(_two_decimals)]


def line_total(unit_price: float, quantity: int) -> float:
    return float(to_money(Decimal(str(unit_price)) * quantity))


def order_total(line_totals: Iterable[float]) -> float:
    return float(to_money(sum((Decimal(str(t)) for t in line_totals), Decimal("0"))))
