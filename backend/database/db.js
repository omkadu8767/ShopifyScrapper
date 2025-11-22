const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

const dbPath = process.env.DATABASE_PATH || path.join(__dirname, 'database.sqlite');

let db;

function initialize() {
    return new Promise((resolve, reject) => {
        // Ensure directory exists
        const dbDir = path.dirname(dbPath);
        if (!fs.existsSync(dbDir)) {
            fs.mkdirSync(dbDir, { recursive: true });
        }

        db = new sqlite3.Database(dbPath, (err) => {
            if (err) {
                reject(err);
            } else {
                console.log('📦 Connected to SQLite database');
                createTables()
                    .then(resolve)
                    .catch(reject);
            }
        });
    });
}

function createTables() {
    return new Promise((resolve, reject) => {
        db.run(`
      CREATE TABLE IF NOT EXISTS imports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        shopify_product_id TEXT,
        title TEXT,
        status TEXT DEFAULT 'pending',
        error_message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME
      )
    `, (err) => {
            if (err) {
                reject(err);
            } else {
                console.log('✅ Database tables initialized');
                resolve();
            }
        });
    });
}

function insertImport(url, title = null) {
    return new Promise((resolve, reject) => {
        db.run(
            'INSERT INTO imports (url, title, status) VALUES (?, ?, ?)',
            [url, title, 'processing'],
            function (err) {
                if (err) reject(err);
                else resolve(this.lastID);
            }
        );
    });
}

function updateImport(id, data) {
    const fields = [];
    const values = [];

    if (data.shopify_product_id) {
        fields.push('shopify_product_id = ?');
        values.push(data.shopify_product_id);
    }
    if (data.title) {
        fields.push('title = ?');
        values.push(data.title);
    }
    if (data.status) {
        fields.push('status = ?');
        values.push(data.status);
    }
    if (data.error_message !== undefined) {
        fields.push('error_message = ?');
        values.push(data.error_message);
    }
    if (data.status === 'completed' || data.status === 'failed') {
        fields.push('completed_at = CURRENT_TIMESTAMP');
    }

    if (fields.length === 0) {
        return Promise.resolve(0);
    }

    values.push(id);

    return new Promise((resolve, reject) => {
        db.run(
            `UPDATE imports SET ${fields.join(', ')} WHERE id = ?`,
            values,
            function (err) {
                if (err) reject(err);
                else resolve(this.changes);
            }
        );
    });
}

function getRecentImports(limit = 20) {
    return new Promise((resolve, reject) => {
        db.all(
            'SELECT * FROM imports ORDER BY created_at DESC LIMIT ?',
            [limit],
            (err, rows) => {
                if (err) reject(err);
                else resolve(rows);
            }
        );
    });
}

function getImportById(id) {
    return new Promise((resolve, reject) => {
        db.get(
            'SELECT * FROM imports WHERE id = ?',
            [id],
            (err, row) => {
                if (err) reject(err);
                else resolve(row);
            }
        );
    });
}

module.exports = {
    initialize,
    insertImport,
    updateImport,
    getRecentImports,
    getImportById
};
