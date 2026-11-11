"""Unit tests for OTP generation and HMAC hashing (backend/auth/otp.py)."""

from datetime import datetime, timezone

from backend.auth.otp import generate_otp, hash_otp, otp_expiry, verify_otp_hash

KEY = b"k" * 32


def test_generate_otp_is_6_digits():
    otp = generate_otp()
    assert otp.isdigit()
    assert len(otp) == 6


def test_generate_otp_is_random():
    otps = {generate_otp() for _ in range(20)}
    assert len(otps) > 1


def test_hash_otp_is_deterministic():
    assert hash_otp("123456", "9876543210", KEY) == hash_otp("123456", "9876543210", KEY)


def test_hash_otp_different_phones_differ():
    assert hash_otp("123456", "9876543210", KEY) != hash_otp("123456", "9000000000", KEY)


def test_hash_otp_depends_on_server_key():
    assert hash_otp("123456", "9876543210", b"a" * 32) != hash_otp("123456", "9876543210", b"b" * 32)


def test_hash_is_hmac_sha256_hex():
    h = hash_otp("123456", "9876543210", KEY)
    assert len(h) == 64 and "123456" not in h


def test_verify_otp_hash_correct():
    stored = hash_otp("654321", "9876543210", KEY)
    assert verify_otp_hash("654321", "9876543210", stored, KEY) is True


def test_verify_otp_hash_wrong_otp():
    stored = hash_otp("999999", "9876543210", KEY)
    assert verify_otp_hash("000000", "9876543210", stored, KEY) is False


def test_otp_expiry_is_five_minutes_ahead():
    now = datetime.now(timezone.utc)
    exp = otp_expiry(now)
    assert (exp - now).total_seconds() == 300
