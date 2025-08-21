import pymysql

# Database connection parameters
connection = pymysql.connect(
    host='caboose.proxy.rlwy.net',
    port=41629,
    user='root',
    password='IVIwxOEAWLTsPRfbhNKOmeCqVXdphTVV',
    database='railway'
)

try:
    with connection.cursor() as cursor:
        # Query to get server.secret
        cursor.execute("SELECT param_value FROM sys_params WHERE param_code = 'server.secret'")
        result = cursor.fetchone()
        
        if result:
            print(f"server.secret value: {result[0]}")
        else:
            print("server.secret not found in database")
            
        # Let's also check what parameters exist
        cursor.execute("SELECT param_code, param_value FROM sys_params")
        all_params = cursor.fetchall()
        
        print("\nAll parameters in sys_params table:")
        for param in all_params:
            print(f"{param[0]}: {param[1]}")
            
finally:
    connection.close()