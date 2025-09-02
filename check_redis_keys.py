#!/usr/bin/env python3
"""
Script to check all Redis keys and their values to identify corrupted data
"""

import redis
import json

# Railway Redis Configuration
redis_client = redis.Redis(
    host='caboose.proxy.rlwy.net',
    port=45879,
    password='mJwoNsjrRcbAkElEWATNOxmqUNraCKIT',
    username='default',
    db=0,
    decode_responses=True
)

def check_all_keys():
    try:
        # Get all keys
        all_keys = redis_client.keys("*")
        print(f"Total keys in Redis: {len(all_keys)}")
        
        for key in all_keys:
            try:
                # Get the type of the key
                key_type = redis_client.type(key)
                print(f"\nKey: {key} (type: {key_type})")
                
                if key_type == 'string':
                    value = redis_client.get(key)
                    print(f"  Value: {value[:200]}..." if len(str(value)) > 200 else f"  Value: {value}")
                    
                    # Try to parse as JSON if it looks like JSON
                    if value and (value.strip().startswith('{') or value.strip().startswith('[')):
                        try:
                            json.loads(value)
                            print("  ✓ Valid JSON")
                        except json.JSONDecodeError as e:
                            print(f"  ✗ Invalid JSON: {e}")
                            print(f"  Deleting corrupted key: {key}")
                            redis_client.delete(key)
                            
            except Exception as e:
                print(f"  Error checking key {key}: {e}")
                print(f"  Deleting problematic key: {key}")
                redis_client.delete(key)
        
        print("\nRedis key check completed")
        
    except Exception as e:
        print(f"Error checking Redis keys: {e}")

if __name__ == "__main__":
    check_all_keys()