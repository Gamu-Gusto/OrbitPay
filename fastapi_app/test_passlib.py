from passlib.context import CryptContext

# Test the passlib context directly
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Test with a long password
long_password = "a" * 100

try:
    result = pwd_ctx.hash(long_password)
    print(f"Hash successful: {len(result)} characters")
except Exception as e:
    print(f"Error: {e}")
    print(f"Password length: {len(long_password)} chars")
    print(f"Password bytes: {len(long_password.encode('utf-8'))} bytes")
