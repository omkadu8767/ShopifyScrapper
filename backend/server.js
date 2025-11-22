require('dotenv').config({ path: require('path').join(__dirname, '..', '.env') });
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const importRoutes = require('./routes/import');
const db = require('./database/db');

const app = express();
const PORT = process.env.PORT || 5000;

// Security middleware
app.use(helmet());

// CORS configuration
app.use(cors({
    origin: process.env.FRONTEND_URL || 'http://localhost:3000',
    credentials: true
}));

// Body parsing middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Logging middleware
app.use(morgan('combined'));

// Rate limiting - DISABLED FOR TESTING
// const importLimiter = rateLimit({
//     windowMs: (process.env.RATE_LIMIT_WINDOW || 15) * 60 * 1000,
//     max: process.env.RATE_LIMIT_MAX_REQUESTS || 10,
//     message: 'Too many import requests. Please try again later.',
//     skip: (req) => req.method !== 'POST'
// });
// app.use('/api/import', importLimiter);

// Routes
app.use('/api/import', importRoutes);

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        uptime: process.uptime()
    });
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error('Error:', err);
    res.status(err.status || 500).json({
        success: false,
        error: err.message || 'Internal server error',
        timestamp: new Date().toISOString()
    });
});

// Initialize database
db.initialize()
    .then(() => {
        app.listen(PORT, () => {
            console.log(`🚀 Backend server running on port ${PORT}`);
            console.log(`📊 Environment: ${process.env.NODE_ENV || 'development'}`);
            console.log(`🛡️  Rate limit: ${process.env.RATE_LIMIT_MAX_REQUESTS || 10} requests per ${process.env.RATE_LIMIT_WINDOW || 15} minutes`);
        });
    })
    .catch(err => {
        console.error('Failed to initialize database:', err);
        process.exit(1);
    });

module.exports = app;
