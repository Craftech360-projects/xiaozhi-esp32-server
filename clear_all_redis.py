#!/usr/bin/env python3
"""
Clear all Redis data to start fresh
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

def clear_all_redis():
    try:
        # Clear all data
        redis_client.flushdb()
        print("All Redis data cleared")
        
        # Verify it's empty
        keys = redis_client.keys("*")
        print(f"Remaining keys after flush: {keys}")
        
    except Exception as e:
        print(f"Error clearing Redis: {e}")

if __name__ == "__main__":
    clear_all_redis()