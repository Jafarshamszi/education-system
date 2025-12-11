#!/usr/bin/env python3
"""
Test password verification directly
"""

from app.auth.password import verify_legacy_password, decode_base64_password

# Test data
stored_password = "SHVtYXkyMDAy"  # This is what's in the database
test_password = "testpass"

print("Testing password verification...")
print(f"Stored password: {stored_password}")
print(f"Test password: {test_password}")

# Decode the stored password
decoded = decode_base64_password(stored_password)
print(f"Decoded stored password: {decoded}")

# Test verification
result = verify_legacy_password(test_password, stored_password)
print(f"Password verification result: {result}")

# Also test with the actual decoded password
print(f"Direct comparison: {test_password} == {decoded}: {test_password == decoded}")