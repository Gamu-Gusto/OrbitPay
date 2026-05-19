#!/usr/bin/env python3

from auth import create_access_token, decode_token
import traceback

# Test token creation and validation
def test_token():
    print("Testing JWT token creation and validation...")
    
    # Test data
    user_id = "1"
    roles = ["super_admin"]
    
    try:
        # Create token
        token = create_access_token(user_id, roles)
        print(f"Token created successfully: {len(token)} characters")
        print(f"Token preview: {token[:50]}...")
        
        # Decode token
        payload = decode_token(token)
        print(f"Token decoded successfully: {payload}")
        
        # Verify payload
        assert payload.get("sub") == user_id
        assert payload.get("roles") == roles
        print("Token payload validation passed")
        
        return True
        
    except Exception as e:
        print(f"Token test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_token()

