module.exports = {
    apps: [
        {
            name: '1688-shopify-backend',
            script: './backend/server.js',
            instances: 1,
            autorestart: true,
            watch: false,
            max_memory_restart: '1G',
            env: {
                NODE_ENV: 'production',
                PORT: 3001
            },
            error_file: './logs/backend-error.log',
            out_file: './logs/backend-out.log',
            log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
        },
        {
            name: '1688-shopify-frontend',
            script: 'serve',
            env: {
                PM2_SERVE_PATH: './frontend/dist',
                PM2_SERVE_PORT: 3000,
                PM2_SERVE_SPA: 'true'
            }
        }
    ]
};
