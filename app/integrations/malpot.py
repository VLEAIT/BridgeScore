def verify_land_record(district: str, citizenship_number: str, farmer_name: str) -> dict:
    """Mock Malpot LRIMS — returns verified for known districts."""
    return {"verified": True, "source": "mock_malpot"}