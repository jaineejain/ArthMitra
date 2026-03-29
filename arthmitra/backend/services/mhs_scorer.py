from arthmitra.backend.services.finance_engine import calculate_mhs


def calculate_mhs_score(profile: dict) -> dict:
    """
    Thin wrapper around `finance_engine.calculate_mhs` for readability.
    """
    return calculate_mhs(profile)

