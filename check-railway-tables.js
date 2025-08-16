const mysql = require('mysql2/promise');
require('dotenv').config({ path: '.env.railway' });

async function checkRailwayDatabase() {
    const connection = await mysql.createConnection({
        host: process.env.RAILWAY_MYSQL_HOST || 'caboose.proxy.rlwy.net',
        port: process.env.RAILWAY_MYSQL_PORT || 41629,
        user: process.env.RAILWAY_MYSQL_USER || 'root',
        password: process.env.RAILWAY_MYSQL_PASSWORD || 'IVIwxOEAWLTsPRfbhNKOmeCqVXdphTVV',
        database: process.env.RAILWAY_MYSQL_DATABASE || 'railway'
    });

    try {
        console.log('========================================');
        console.log('Connected to YOUR Railway MySQL Database');
        console.log('Host:', process.env.RAILWAY_MYSQL_HOST);
        console.log('Database:', process.env.RAILWAY_MYSQL_DATABASE);
        console.log('========================================\n');
        
        // 1. List ALL tables that exist
        console.log('=== ALL TABLES IN YOUR DATABASE ===');
        const [allTables] = await connection.execute(`
            SELECT 
                TABLE_NAME as table_name,
                TABLE_ROWS as row_count,
                CREATE_TIME as created,
                UPDATE_TIME as updated,
                TABLE_COMMENT as comment
            FROM information_schema.tables 
            WHERE table_schema = 'railway'
            ORDER BY TABLE_NAME
        `);
        
        if (allTables.length === 0) {
            console.log('❌ No tables found! Database is empty.');
            console.log('You need to run the initialization script first.');
        } else {
            console.log(`Found ${allTables.length} tables:\n`);
            console.table(allTables.map(t => ({
                Table: t.table_name,
                Rows: t.row_count || 0,
                Comment: t.comment || '',
                Created: t.created ? new Date(t.created).toLocaleDateString() : 'N/A'
            })));
        }
        
        // 2. Check which type of database schema you have
        console.log('\n=== IDENTIFYING DATABASE SCHEMA TYPE ===');
        
        // Check for Xiaozhi original tables
        const xiaozhiTables = ['ai_agent', 'ai_device', 'ai_model_config', 'ai_agent_chat_history'];
        let hasXiaozhi = false;
        
        for (const table of xiaozhiTables) {
            const [exists] = await connection.execute(
                'SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema = "railway" AND table_name = ?',
                [table]
            );
            if (exists[0].count > 0) {
                hasXiaozhi = true;
                break;
            }
        }
        
        // Check for parental analytics tables
        const parentalTables = ['child_profile', 'chat_sessions', 'chat_messages', 'parental_settings'];
        let hasParental = false;
        
        for (const table of parentalTables) {
            const [exists] = await connection.execute(
                'SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema = "railway" AND table_name = ?',
                [table]
            );
            if (exists[0].count > 0) {
                hasParental = true;
                break;
            }
        }
        
        if (hasXiaozhi) {
            console.log('✅ You have the XIAOZHI (original Chinese) database schema');
            console.log('This is for the AI toy server with agent configurations');
        } else if (hasParental) {
            console.log('✅ You have the PARENTAL ANALYTICS database schema');
            console.log('This is for child monitoring and parental controls');
        } else {
            console.log('⚠️  Unknown or empty database schema');
        }
        
        // 3. Show table details if tables exist
        if (allTables.length > 0) {
            console.log('\n=== TABLE DETAILS ===');
            
            // Show structure of first 3 tables as examples
            const tablesToCheck = allTables.slice(0, 3).map(t => t.table_name);
            
            for (const tableName of tablesToCheck) {
                console.log(`\n📋 Table: ${tableName}`);
                const [columns] = await connection.execute(`SHOW COLUMNS FROM ${tableName}`);
                console.table(columns.map(col => ({
                    Field: col.Field,
                    Type: col.Type,
                    Null: col.Null,
                    Key: col.Key,
                    Default: col.Default
                })));
            }
        }
        
        // 4. Check for ESP32 device registration
        console.log('\n=== CHECKING FOR ESP32 DEVICE (MAC: 68:25:dd:bc:03:7c) ===');
        
        // Try different table names depending on schema
        const deviceTables = ['ai_device', 'devices', 'device'];
        let deviceFound = false;
        
        for (const tableName of deviceTables) {
            try {
                const [devices] = await connection.execute(
                    `SELECT * FROM ${tableName} WHERE mac_address LIKE '%68:25:dd:bc:03:7c%' OR mac_address LIKE '%68_25_dd_bc_03_7c%'`
                );
                
                if (devices.length > 0) {
                    console.log(`✅ Device found in ${tableName} table:`);
                    console.table(devices[0]);
                    deviceFound = true;
                    break;
                }
            } catch (e) {
                // Table doesn't exist, continue
            }
        }
        
        if (!deviceFound) {
            console.log('❌ ESP32 device not registered yet');
            console.log('MAC address 68:25:dd:bc:03:7c needs to be registered');
        }
        
        // 5. Summary and next steps
        console.log('\n========================================');
        console.log('SUMMARY');
        console.log('========================================');
        console.log(`Total tables: ${allTables.length}`);
        console.log(`Total rows: ${allTables.reduce((sum, t) => sum + (t.row_count || 0), 0)}`);
        
        if (allTables.length === 0) {
            console.log('\n⚠️  ACTION REQUIRED:');
            console.log('1. Your database is empty');
            console.log('2. Run an initialization script to create tables');
            console.log('3. Then register your ESP32 device');
        } else {
            console.log('\n✅ Database is initialized');
            if (!deviceFound) {
                console.log('⚠️  Next step: Register your ESP32 device');
            }
        }
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        
        if (error.code === 'ER_NO_SUCH_TABLE') {
            console.log('\n⚠️  Some tables are missing');
        } else if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
            console.log('\n⚠️  Cannot connect to Railway database');
            console.log('Please check:');
            console.log('1. Railway database is running');
            console.log('2. Connection details in .env.railway are correct');
            console.log('3. Try again in a few seconds (Railway may be waking up)');
        }
    } finally {
        await connection.end();
        console.log('\n========================================');
        console.log('Database check complete');
        console.log('========================================');
    }
}

// Run the check
console.log('Checking YOUR Railway database...\n');
checkRailwayDatabase().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
});