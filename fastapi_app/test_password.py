#!/usr/bin/env python3

from auth import hash_password, _truncate_for_bcrypt
import traceback

# Test with a long password
long_password = "a" * 100  # 100 character password

print(f"Original password length: {len(long_password)}")
print(f"Original password bytes: {len(long_password.encode('utf-8'))}")

try:
    truncated = _truncate_for_bcrypt(long_password)
    print(f"Truncated password length: {len(truncated)}")
    print(f"Truncated password bytes: {len(truncated.encode('utf-8'))}")

    hashed = hash_password(long_password)
    print(f"Hash generated successfully: {len(hashed)} characters")
    print("SUCCESS: Password truncation and hashing works correctly")

except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
