const mysql = require('mysql2/promise');

async function checkAllTables() {
    const connection = await mysql.createConnection({
        host: 'caboose.proxy.rlwy.net',
        port: 41629,
        user: 'root',
        password: 'IVIwxOEAWLTsPRfbhNKOmeCqVXdphTVV',
        database: 'railway'
    });

    try {
        console.log('Connected to Railway MySQL\n');
        
        const tables = [
            'sys_user', 
            'sys_user_token',
            'ai_device', 
            'child_profile', 
            'parental_settings',
            'chat_sessions', 
            'chat_messages', 
            'daily_analytics'
        ];
        
        for (const table of tables) {
            console.log(`\n=== ${table} Table Structure ===`);
            const [columns] = await connection.execute(`SHOW COLUMNS FROM ${table}`);
            console.table(columns.map(col => ({
                Field: col.Field,
                Type: col.Type,
                Null: col.Null,
                Key: col.Key,
                Default: col.Default
            })));
        }
        
    } catch (error) {
        console.error('Error:', error);
    } finally {
        await connection.end();
    }
}

checkAllTables().catch(console.error);