#!/usr/bin/env python3
"""
Check the version key specifically
"""

import redis

# Railway Redis Configuration
redis_client = redis.Redis(
    host='caboose.proxy.rlwy.net',
    port=45879,
    password='mJwoNsjrRcbAkElEWATNOxmqUNraCKIT',
    username='default',
    db=0,
    decode_responses=True
)

def check_version_key():
    try:
        # Check the specific version key
        version_key = "sys:version"
        if redis_client.exists(version_key):
            value = redis_client.get(version_key)
            print(f"Key '{version_key}' value: {repr(value)}")
            print(f"Value type: {type(value)}")
            print(f"Value length: {len(str(value))}")
            
            # Delete it and set a proper string value
            redis_client.delete(version_key)
            redis_client.set(version_key, "0.7.5")
            print("Replaced with proper string value")
        else:
            print(f"Key '{version_key}' does not exist")
            redis_client.set(version_key, "0.7.5")
            print("Created version key with proper value")
            
        # Check all remaining keys for debugging
        all_keys = redis_client.keys("*")
        print(f"All remaining keys: {all_keys}")
        
    except Exception as e:
        print(f"Error checking version key: {e}")

if __name__ == "__main__":
    check_version_key()