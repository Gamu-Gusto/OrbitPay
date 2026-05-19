#!/usr/bin/env python3

from auth import hash_password, _truncate_for_bcrypt
import traceback

# Test with different password lengths
test_passwords = [
    "short",  # 5 chars
    "a" * 72,  # Exactly 72 bytes
    "a" * 73,  # 73 bytes (too long)
    "ü" * 50,  # Unicode characters (each ü is 2 bytes in UTF-8)
]

for i, password in enumerate(test_passwords):
    print(f"\nTest {i+1}:")
    print(f"Password: {repr(password[:20])}{'...' if len(password) > 20 else ''}")
    print(f"Length: {len(password)} chars")
    print(f"UTF-8 bytes: {len(password.encode('utf-8'))}")

    try:
        truncated = _truncate_for_bcrypt(password)
        print(f"Truncated: {repr(truncated[:20])}{'...' if len(truncated) > 20 else ''}")
        print(f"Truncated length: {len(truncated)} chars")
        print(f"Truncated bytes: {len(truncated.encode('utf-8'))}")

        hashed = hash_password(password)
        print(f"Hash successful: {len(hashed)} characters")

    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
