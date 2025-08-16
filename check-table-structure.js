const mysql = require('mysql2/promise');

async function checkTableStructure() {
    const connection = await mysql.createConnection({
        host: 'caboose.proxy.rlwy.net',
        port: 41629,
        user: 'root',
        password: 'IVIwxOEAWLTsPRfbhNKOmeCqVXdphTVV',
        database: 'railway'
    });

    try {
        console.log('Connected to Railway MySQL\n');
        
        // Check sys_user table structure
        console.log('=== sys_user Table Structure ===');
        const [userColumns] = await connection.execute(`
            SHOW COLUMNS FROM sys_user
        `);
        console.table(userColumns);
        
        // Check ai_device table structure
        console.log('\n=== ai_device Table Structure ===');
        const [deviceColumns] = await connection.execute(`
            SHOW COLUMNS FROM ai_device
        `);
        console.table(deviceColumns);
        
        // Check child_profile table structure
        console.log('\n=== child_profile Table Structure ===');
        const [childColumns] = await connection.execute(`
            SHOW COLUMNS FROM child_profile
        `);
        console.table(childColumns);
        
    } catch (error) {
        console.error('Error:', error);
    } finally {
        await connection.end();
    }
}

checkTableStructure().catch(console.error);