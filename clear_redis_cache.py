import redis

# Connect to Redis using the connection details from application.yml
r = redis.Redis(
    host='shortline.proxy.rlwy.net',
    port=54353,
    password='mClDIOpuKWkawXKBcfhWFDwHHnhuWegp',
    decode_responses=True
)

try:
    # Delete the server config cache
    deleted = r.delete('server:config')
    print(f"Deleted server:config cache: {deleted}")
    
    # Delete all sys:params entries
    deleted = r.delete('sys:params')
    print(f"Deleted sys:params cache: {deleted}")
    
    print("Redis cache cleared successfully!")
except Exception as e:
    print(f"Error clearing Redis cache: {e}")