def fetch_remittance_history(citizenship_number: str, channel: str) -> dict:
    """Mock IME/Prabhu — returns 6 months history with 1 gap."""
    return {"months_history": 6, "gap_months": 1, "source": "mock_ime"}