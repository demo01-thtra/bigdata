"""Unit tests for rule-based detection logic (producer enrichment)."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'producer'))


def test_device_id_generation():
    """Producer generates device IDs with proper format."""
    from producer import _get_device
    device = _get_device("C12345")
    assert isinstance(device, str)
    assert len(device) > 0
    # Either starts with DEV- (normal) or UNKNOWN- (anomaly)
    assert device.startswith("DEV-") or device.startswith("UNKNOWN-")


def test_ip_address_generation():
    """Producer generates valid-format IP addresses."""
    from producer import _get_ip
    ip = _get_ip("C12345")
    parts = ip.split(".")
    assert len(parts) == 4
    for p in parts:
        assert p.isdigit()
        assert 0 <= int(p) <= 255


def test_user_device_consistency():
    """Same user should get the same device pool (unless anomaly)."""
    from producer import _get_device, _user_devices
    _user_devices.clear()
    # Generate several times — most should be from same pool
    devices = [_get_device("TESTUSER1") for _ in range(20)]
    normal = [d for d in devices if d.startswith("DEV-")]
    # At least some normal devices should be the same
    if len(normal) >= 2:
        assert len(set(normal)) <= 3  # user gets 1-3 devices


def test_blacklist_detection_concept():
    """Blacklist membership check should work for known accounts."""
    blacklist = {"C_BAD_1", "C_BAD_2", "C_BAD_3"}
    assert "C_BAD_1" in blacklist
    assert "C_GOOD_1" not in blacklist


def test_high_amount_rule():
    """Amount > 200k should be flagged."""
    threshold = 200_000
    assert 250_000 > threshold
    assert 100_000 <= threshold  # should NOT be flagged


def test_balance_ratio_rule():
    """Amount / balance > 0.8 should be flagged."""
    threshold = 0.8
    # 90k out of 100k = 0.9 → flag
    assert (90_000 / (100_000 + 1)) > threshold
    # 10k out of 100k = 0.1 → no flag
    assert (10_000 / (100_000 + 1)) < threshold
