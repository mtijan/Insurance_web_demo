from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional

DEFAULT_ADMIN_FEE = Decimal("35000.00")

TLO_RATE = Decimal("0.02")          # 2.0%
TLO_PLUS_RATE = Decimal("0.031")    # 3.1%
KOMPRE_PLUS_RATE = Decimal("0.043") # 4.3%

TLO_PLUS_DEPRECIATION = {
    1: (Decimal("1.00"), "100%"),
    2: (Decimal("0.85"), "85%"),
    3: (Decimal("0.75"), "75%"),
    4: (Decimal("0.65"), "65%"),
    5: (Decimal("0.55"), "55%"),
}


def round_currency(value: Decimal) -> Decimal:
    """Rounds a decimal value to standard 2 decimal places."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def coverage_pricing(hp: Decimal, coverage_type: str, tenor_years: int):
    """Return effective value, depreciation label, rate label and base premium."""
    if coverage_type == "TLO":
        depreciation_str = "100%"
        effective_hp = hp
        rate_str = "2.0%"
        base_prem = round_currency(effective_hp * TLO_RATE)
    elif coverage_type == "TLO_PLUS":
        factor, depreciation_str = TLO_PLUS_DEPRECIATION.get(tenor_years, (Decimal("1.00"), "100%"))
        effective_hp = round_currency(hp * factor)
        rate_str = "3.1%"
        base_prem = round_currency(effective_hp * TLO_PLUS_RATE)
    elif coverage_type == "KOMPRE_PLUS":
        depreciation_str = "100%"
        effective_hp = hp
        rate_str = "4.3%"
        base_prem = round_currency(effective_hp * KOMPRE_PLUS_RATE)
    else:
        raise ValueError(f"Unknown coverage type: '{coverage_type}'.")
    return effective_hp, depreciation_str, rate_str, base_prem


def calculate_premium(
    sum_insured: Decimal,
    coverage_type: str,
    tenor_years: int = 1,
    admin_fee: Optional[Decimal] = None
) -> Dict[str, Any]:
    """Calculate premiums using an explicit fee snapshot or the default fee."""
    if sum_insured <= Decimal("0"):
        raise ValueError("Sum insured must be greater than zero.")
    if tenor_years < 1 or tenor_years > 5:
        raise ValueError("Tenor must be between 1 and 5 years.")
    fee = round_currency(admin_fee if admin_fee is not None else DEFAULT_ADMIN_FEE)
    hp = round_currency(sum_insured)
    effective_hp, depreciation_str, rate_str, base_prem = coverage_pricing(
        hp, coverage_type, tenor_years,
    )

    total_prem = round_currency(base_prem + fee)

    return {
        "sum_insured": f"{hp:.2f}",
        "coverage_type": coverage_type,
        "tenor_years": tenor_years,
        "depreciation_rate": depreciation_str,
        "effective_sum_insured": f"{effective_hp:.2f}",
        "rate_percentage": rate_str,
        "base_premium": f"{base_prem:.2f}",
        "admin_fee": f"{fee:.2f}",
        "total_premium": f"{total_prem:.2f}",
    }
