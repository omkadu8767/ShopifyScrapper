import axios from 'axios';
import { useEffect, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

function App() {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState(null);
    const [history, setHistory] = useState([]);
    const [logs, setLogs] = useState([]);

    useEffect(() => {
        loadHistory();
    }, []);

    const addLog = (message, type = 'info') => {
        const timestamp = new Date().toLocaleTimeString();
        setLogs(prev => [...prev, { timestamp, message, type }]);
    };

    const loadHistory = async () => {
        try {
            const response = await axios.get(`${API_BASE}/import/history`);
            if (response.data.success) {
                setHistory(response.data.imports);
            }
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!url) {
            setMessage({ type: 'error', text: 'Please enter a 1688 URL' });
            return;
        }

        if (!url.includes('1688.com')) {
            setMessage({ type: 'error', text: 'Please enter a valid 1688.com URL' });
            return;
        }

        setLoading(true);
        setMessage(null);
        setLogs([]);
        addLog('Starting import process...', 'info');

        try {
            addLog('Sending request to server...', 'info');
            const response = await axios.post(`${API_BASE}/import`, { url });

            if (response.data.success) {
                const importId = response.data.importId;
                addLog(`Import started with ID: ${importId}`, 'success');
                addLog('Scraping product data from 1688.com...', 'info');

                setMessage({
                    type: 'success',
                    text: `Import started successfully! Import ID: ${importId}. Check the history table below for status.`
                });

                pollImportStatus(importId);
            } else {
                addLog(`Error: ${response.data.error}`, 'error');
                setMessage({ type: 'error', text: response.data.error });
                setLoading(false);
            }
        } catch (error) {
            const errorMsg = error.response?.data?.error || error.message || 'Import failed';
            addLog(`Error: ${errorMsg}`, 'error');
            setMessage({ type: 'error', text: errorMsg });
            setLoading(false);
        }
    };

    const pollImportStatus = async (importId) => {
        const maxAttempts = 60;
        let attempts = 0;
        let lastTitle = '';

        const poll = async () => {
            try {
                const response = await axios.get(`${API_BASE}/import/${importId}`);
                const importData = response.data.import;

                // Show translated title when available
                if (importData.title && importData.title !== lastTitle) {
                    lastTitle = importData.title;
                    addLog(`📝 Product: ${importData.title}`, 'success');
                }

                if (importData.status === 'completed') {
                    addLog('✅ Product successfully imported to Shopify!', 'success');
                    addLog(`Shopify Product ID: ${importData.shopify_product_id}`, 'success');
                    if (importData.shopify_product_id) {
                        addLog(`View product in Shopify admin`, 'info');
                    }
                    setLoading(false);
                    loadHistory();
                    setUrl('');
                } else if (importData.status === 'failed') {
                    addLog(`❌ Import failed: ${importData.error_message}`, 'error');
                    setMessage({ type: 'error', text: importData.error_message });
                    setLoading(false);
                    loadHistory();
                } else if (attempts < maxAttempts) {
                    attempts++;

                    // Show progress indicators based on time
                    if (attempts === 2) {
                        addLog('🔍 Scraping product details...', 'info');
                    } else if (attempts === 4) {
                        addLog('🌐 Translating title and description...', 'info');
                    } else if (attempts === 6) {
                        addLog('🎨 Translating variants and options...', 'info');
                    } else if (attempts === 8) {
                        addLog('📸 Processing images...', 'info');
                    } else if (attempts === 10) {
                        addLog('🚀 Uploading to Shopify...', 'info');
                    } else if (attempts % 5 === 0) {
                        addLog('⏳ Still processing... please wait', 'info');
                    }

                    setTimeout(poll, 3000); // Poll every 3 seconds
                } else {
                    addLog('⏱️ Timeout: Import is taking longer than expected. Check history for status.', 'error');
                    setLoading(false);
                    loadHistory();
                }
            } catch (error) {
                console.error('Polling error:', error);
                if (attempts < maxAttempts) {
                    attempts++;
                    setTimeout(poll, 3000);
                } else {
                    setLoading(false);
                    loadHistory();
                }
            }
        };

        poll();
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleString();
    };

    const getStatusBadge = (status) => {
        const statusMap = {
            completed: 'status-badge status-completed',
            processing: 'status-badge status-processing',
            failed: 'status-badge status-failed',
            pending: 'status-badge status-pending'
        };

        return (
            <span className={statusMap[status] || 'status-badge'}>
                {status}
            </span>
        );
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-gradient-to-r from-primary-500 to-secondary-500 text-white shadow-lg">
                <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
                    <div className="text-center">
                        <h1 className="text-4xl font-bold mb-2">
                            🚀 1688 → Shopify Importer
                        </h1>
                        <p className="text-lg text-white/90">
                            Automatically import products from 1688.com to your Shopify store
                        </p>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
                {/* Import Form */}
                <div className="card p-8 mb-8">
                    <h2 className="text-2xl font-bold text-gray-900 mb-6">
                        Import New Product
                    </h2>

                    {message && (
                        <div className={`alert alert-${message.type}`}>
                            <p className="font-medium">{message.text}</p>
                        </div>
                    )}

                    <form onSubmit={handleSubmit}>
                        <div className="mb-6">
                            <label
                                htmlFor="url"
                                className="block text-sm font-semibold text-gray-700 mb-2"
                            >
                                1688 Product URL
                            </label>
                            <input
                                type="url"
                                id="url"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                placeholder="https://detail.1688.com/offer/..."
                                disabled={loading}
                                required
                                className="input-field"
                            />
                            <p className="mt-2 text-sm text-gray-500">
                                Paste a product link from 1688.com to import
                            </p>
                        </div>

                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={loading}
                        >
                            {loading ? (
                                <span className="flex items-center">
                                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Importing...
                                </span>
                            ) : (
                                'Import Product'
                            )}
                        </button>
                    </form>

                    {/* Logs Section */}
                    {logs.length > 0 && (
                        <div className="mt-6 bg-slate-900 rounded-lg p-4 logs-container overflow-y-auto max-h-80">
                            <div className="text-sm font-semibold text-gray-300 mb-3">
                                📋 Import Logs:
                            </div>
                            <div className="space-y-1 font-mono text-sm">
                                {logs.map((log, index) => (
                                    <div
                                        key={index}
                                        className={`${log.type === 'success' ? 'text-green-400' :
                                            log.type === 'error' ? 'text-red-400' :
                                                'text-blue-300'
                                            }`}
                                    >
                                        <span className="text-gray-500">[{log.timestamp}]</span>{' '}
                                        {log.message}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Import History */}
                <div className="card p-8">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-2xl font-bold text-gray-900">
                            Import History
                        </h2>
                        <button
                            onClick={loadHistory}
                            className="text-primary-600 hover:text-primary-700 font-medium text-sm flex items-center"
                        >
                            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            Refresh
                        </button>
                    </div>

                    {history.length === 0 ? (
                        <div className="text-center py-12">
                            <svg className="mx-auto h-16 w-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                            </svg>
                            <p className="mt-4 text-gray-500 text-lg">
                                No imports yet. Start by importing your first product!
                            </p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                            ID
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                            Title
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                            Status
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                            Shopify ID
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                            Date
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {history.map((item) => (
                                        <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                #{item.id}
                                            </td>
                                            <td className="px-6 py-4 text-sm text-gray-900">
                                                {item.title || <span className="text-gray-400 italic">Processing...</span>}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                {getStatusBadge(item.status)}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {item.shopify_product_id || '-'}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {formatDate(item.created_at)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </main>

            {/* Footer */}
            <footer className="mt-12 pb-8">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <p className="text-center text-gray-500 text-sm">
                        © 2025 SHOPGURU INTERNATIONAL SRL - 1688 to Shopify Importer
                    </p>
                </div>
            </footer>
        </div>
    );
}

export default App;
