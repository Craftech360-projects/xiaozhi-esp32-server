#!/usr/bin/env python3
"""
Script to clear corrupted Redis version key
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

def clear_corrupted_keys():
    try:
        # Clear the version key that's causing issues
        version_key = "server:version"
        if redis_client.exists(version_key):
            redis_client.delete(version_key)
            print(f"Deleted corrupted key: {version_key}")
        
        # Clear server config key too if it exists
        config_key = "server:config"
        if redis_client.exists(config_key):
            redis_client.delete(config_key)
            print(f"Deleted corrupted key: {config_key}")
            
        # List all keys to see what's there
        keys = redis_client.keys("server:*")
        print(f"Remaining server keys: {keys}")
        
        print("Redis cleanup completed successfully")
        
    except Exception as e:
        print(f"Error clearing Redis keys: {e}")

if __name__ == "__main__":
    clear_corrupted_keys()