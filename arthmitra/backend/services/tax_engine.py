from arthmitra.backend.services.finance_engine import calculate_tax


def find_missed_deductions(profile: dict) -> list:
    raw = calculate_tax(profile)
    return raw.get("missed_deductions") or []


def format_tax_result(raw_result: dict) -> dict:
    # Keep paise integers for consistency; frontend formats as INR.
    # This helper exists mainly to enforce a stable shape for ResultCards.
    return {
        "old_tax": raw_result.get("old_tax", 0),
        "new_tax": raw_result.get("new_tax", 0),
        "recommended": raw_result.get("recommended", "new"),
        "savings": raw_result.get("savings", 0),
        "old_taxable": raw_result.get("old_taxable", 0),
        "new_taxable": raw_result.get("new_taxable", 0),
        "missed_deductions": raw_result.get("missed_deductions") or [],
        "hra_exempt": raw_result.get("hra_exempt", 0),
        "used_80c": raw_result.get("used_80c", 0),
    }

