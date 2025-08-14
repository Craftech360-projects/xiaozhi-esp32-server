#!/usr/bin/env node
/**
 * Railway MySQL Connection Test
 * Tests connection to your Railway MySQL database
 */

const mysql = require('mysql2/promise');
require('dotenv').config({ path: '.env.railway' });

// Connection configuration
const config = {
    host: 'caboose.proxy.rlwy.net',
    port: 41629,
    user: 'root',
    password: 'IVIwxOEAWLTsPRfbhNKOmeCqVXdphTVV',
    database: 'railway',
    connectTimeout: 30000,
    ssl: {
        rejectUnauthorized: false
    }
};

async function testConnection() {
    console.log('🚂 Testing Railway MySQL Connection...\n');
    console.log('Host:', config.host);
    console.log('Port:', config.port);
    console.log('Database:', config.database);
    console.log('User:', config.user);
    console.log('-----------------------------------\n');

    try {
        // Create connection
        console.log('📡 Connecting to Railway MySQL...');
        const connection = await mysql.createConnection(config);
        console.log('✅ Connected successfully!\n');

        // Test 1: Check MySQL version
        console.log('📊 Database Information:');
        const [versionRows] = await connection.execute('SELECT VERSION() as version');
        console.log('   MySQL Version:', versionRows[0].version);

        // Test 2: Check database
        const [dbRows] = await connection.execute('SELECT DATABASE() as db');
        console.log('   Current Database:', dbRows[0].db);

        // Test 3: Show existing tables
        console.log('\n📋 Existing Tables:');
        const [tables] = await connection.execute('SHOW TABLES');
        if (tables.length === 0) {
            console.log('   No tables found (database is empty)');
        } else {
            tables.forEach(table => {
                const tableName = Object.values(table)[0];
                console.log('   -', tableName);
            });
        }

        // Test 4: Check character set
        const [charsetRows] = await connection.execute(`
            SELECT @@character_set_database as charset, 
                   @@collation_database as collation
        `);
        console.log('\n🔤 Character Set:');
        console.log('   Charset:', charsetRows[0].charset);
        console.log('   Collation:', charsetRows[0].collation);

        // Test 5: Check connection limits
        const [maxConnRows] = await connection.execute('SHOW VARIABLES LIKE "max_connections"');
        console.log('\n⚙️  Server Settings:');
        console.log('   Max Connections:', maxConnRows[0].Value);

        // Test 6: Create a test table
        console.log('\n🔨 Creating Test Table...');
        await connection.execute(`
            CREATE TABLE IF NOT EXISTS connection_test (
                id INT AUTO_INCREMENT PRIMARY KEY,
                test_name VARCHAR(100),
                test_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        `);
        console.log('✅ Test table created successfully');

        // Test 7: Insert test data
        const [insertResult] = await connection.execute(
            'INSERT INTO connection_test (test_name) VALUES (?)',
            ['Railway Connection Test']
        );
        console.log('✅ Test data inserted, ID:', insertResult.insertId);

        // Test 8: Query test data
        const [testRows] = await connection.execute('SELECT * FROM connection_test ORDER BY id DESC LIMIT 1');
        console.log('✅ Test data retrieved:', testRows[0]);

        // Clean up
        await connection.execute('DROP TABLE IF EXISTS connection_test');
        console.log('🧹 Cleaned up test table');

        // Close connection
        await connection.end();
        console.log('\n✨ All tests passed successfully!');
        console.log('🎉 Your Railway MySQL database is ready to use!\n');

        // Show connection strings for different frameworks
        console.log('📝 Connection Strings for Your Apps:\n');
        console.log('Spring Boot (application.yml):');
        console.log(`  url: jdbc:mysql://caboose.proxy.rlwy.net:41629/railway?useSSL=true&allowPublicKeyRetrieval=true`);
        console.log(`  username: root`);
        console.log(`  password: IVIwxOEAWLTsPRfbhNKOmeCqVXdphTVV\n`);
        
        console.log('Python (mysql-connector):');
        console.log(`  host='caboose.proxy.rlwy.net'`);
        console.log(`  port=41629`);
        console.log(`  database='railway'`);
        console.log(`  user='root'`);
        console.log(`  password='IVIwxOEAWLTsPRfbhNKOmeCqVXdphTVV'\n`);
        
        console.log('Node.js (mysql2):');
        console.log(`  host: 'caboose.proxy.rlwy.net'`);
        console.log(`  port: 41629`);
        console.log(`  database: 'railway'`);
        console.log(`  user: 'root'`);
        console.log(`  password: 'IVIwxOEAWLTsPRfbhNKOmeCqVXdphTVV'`);

    } catch (error) {
        console.error('\n❌ Connection failed!');
        console.error('Error:', error.message);
        
        // Provide troubleshooting tips
        console.log('\n🔧 Troubleshooting Tips:');
        if (error.code === 'ETIMEDOUT') {
            console.log('   - Check if your Railway database is running');
            console.log('   - Verify the host and port are correct');
            console.log('   - Check your internet connection');
        } else if (error.code === 'ER_ACCESS_DENIED_ERROR') {
            console.log('   - Verify your username and password');
            console.log('   - Check if the database exists');
        } else if (error.code === 'ER_NOT_SUPPORTED_AUTH_MODE') {
            console.log('   - The authentication method might not be supported');
            console.log('   - Try updating your MySQL client');
        }
        process.exit(1);
    }
}

// Run the test
console.log('🚀 Railway MySQL Connection Test');
console.log('================================\n');
testConnection().catch(console.error);