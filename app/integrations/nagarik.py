def verify_citizen(citizenship_number: str, farmer_name: str) -> dict:
    """Mock Nagarik App — always verifies for demo."""
    return {"verified": True, "source": "mock_nagarik"}