const express = require('express');
const router = express.Router();
const { spawn } = require('child_process');
const path = require('path');
const db = require('../database/db');
const ShopifyService = require('../services/shopify_service');
const fs = require('fs').promises;

/**
 * Execute Python script and get result
 */
function executePython(scriptPath, args = []) {
    return new Promise((resolve, reject) => {
        const pythonPath = process.env.PYTHON_PATH || 'python';
        const pythonProcess = spawn(pythonPath, [scriptPath, ...args]);

        let stdout = '';
        let stderr = '';

        pythonProcess.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        pythonProcess.on('close', (code) => {
            if (code !== 0) {
                reject(new Error(stderr || `Process exited with code ${code}`));
            } else {
                try {
                    const result = JSON.parse(stdout);
                    resolve(result);
                } catch (e) {
                    reject(new Error(`Failed to parse JSON: ${stdout}`));
                }
            }
        });

        pythonProcess.on('error', (error) => {
            reject(error);
        });
    });
}

/**
 * POST /api/import
 * Import product from 1688 to Shopify
 */
router.post('/', async (req, res) => {
    const { url } = req.body;

    if (!url) {
        return res.status(400).json({
            success: false,
            error: 'URL is required'
        });
    }

    // Validate 1688 URL
    if (!url.includes('1688.com')) {
        return res.status(400).json({
            success: false,
            error: 'Invalid 1688.com URL'
        });
    }

    let importId;

    try {
        // Create import record
        importId = await db.insertImport(url);

        res.json({
            success: true,
            message: 'Import started',
            importId
        });

        // Process in background
        processImport(importId, url).catch(error => {
            console.error(`Import ${importId} failed:`, error);
            db.updateImport(importId, {
                status: 'failed',
                error_message: error.message
            });
        });

    } catch (error) {
        console.error('Error starting import:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

/**
 * Process import workflow
 */
async function processImport(importId, url) {
    console.log(`Starting import ${importId} for URL: ${url}`);

    try {
        // Step 1: Scrape 1688 product
        console.log(`[${importId}] Step 1: Scraping product data...`);
        const scraperPath = path.join(__dirname, '../scrapers/scraper_1688.py');
        const scrapeResult = await executePython(scraperPath, [url]);

        if (!scrapeResult.success) {
            throw new Error(`Scraping failed: ${scrapeResult.error}`);
        }

        const productData = scrapeResult.data;
        console.log(`[${importId}] Scraped: ${productData.title}`);

        // Update import with title
        await db.updateImport(importId, { title: productData.title });

        // Step 2: Translate and rewrite description
        console.log(`[${importId}] Step 2: Translating description...`);
        const translatorPath = path.join(__dirname, '../services/ai_translator.py');
        const translateResult = await executePython(translatorPath, [
            productData.description,
            productData.title
        ]);

        if (!translateResult.success) {
            console.warn(`[${importId}] Translation failed, using original text`);
            productData.translatedDescription = productData.description;
        } else {
            productData.translatedDescription = translateResult.translated_text;
        }

        // Step 3: Generate SEO fields
        console.log(`[${importId}] Step 3: Generating SEO fields...`);
        const seoScript = `
import sys
import json
from services.ai_translator import AITranslator

title = sys.argv[1]
description = sys.argv[2] if len(sys.argv) > 2 else ''

translator = AITranslator()
result = translator.generate_seo_fields(title, description)
print(json.dumps(result))
`;

        const seoScriptPath = path.join(__dirname, '../temp_seo_script.py');
        await fs.writeFile(seoScriptPath, seoScript);

        let seoResult;
        try {
            seoResult = await executePython(seoScriptPath, [
                productData.title,
                productData.translatedDescription
            ]);
        } catch (error) {
            console.warn(`[${importId}] SEO generation failed, using defaults`);
            seoResult = {
                success: true,
                seo_title: productData.title.substring(0, 60),
                seo_description: productData.translatedDescription.substring(0, 160)
            };
        } finally {
            // Clean up temp script
            await fs.unlink(seoScriptPath).catch(() => { });
        }

        // Step 4: Process images (optional optimization)
        console.log(`[${importId}] Step 4: Processing ${productData.images.length} images...`);
        // For now, use images directly. Can add processing later.
        const processedImages = productData.images.slice(0, 10); // Limit to 10 images

        // Step 5: Upload to Shopify
        console.log(`[${importId}] Step 5: Creating product in Shopify...`);
        const shopifyService = new ShopifyService();

        const shopifyResult = await shopifyService.createProduct({
            title: productData.title,
            description: productData.translatedDescription,
            vendor: 'China Supplier',
            productType: '1688 Import',
            tags: [],
            images: processedImages,
            variants: [],
            seoTitle: seoResult.seo_title,
            seoDescription: seoResult.seo_description,
            priceMin: productData.price_min,
            priceMax: productData.price_max,
            variantData: productData.variants
        });

        if (!shopifyResult.success) {
            throw new Error(`Shopify upload failed: ${JSON.stringify(shopifyResult.error)}`);
        }

        console.log(`[${importId}] ✅ Successfully created Shopify product: ${shopifyResult.productId}`);

        // Update import record
        await db.updateImport(importId, {
            status: 'completed',
            shopify_product_id: shopifyResult.productId.toString()
        });

        return {
            success: true,
            productId: shopifyResult.productId,
            importId
        };

    } catch (error) {
        console.error(`[${importId}] Import failed:`, error);
        await db.updateImport(importId, {
            status: 'failed',
            error_message: error.message
        });
        throw error;
    }
}

/**
 * GET /api/import/history
 * Get import history
 */
router.get('/history', async (req, res) => {
    try {
        const limit = parseInt(req.query.limit) || 20;
        const imports = await db.getRecentImports(limit);

        res.json({
            success: true,
            imports
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

/**
 * GET /api/import/:id
 * Get specific import status
 */
router.get('/:id', async (req, res) => {
    try {
        const importData = await db.getImportById(req.params.id);

        if (!importData) {
            return res.status(404).json({
                success: false,
                error: 'Import not found'
            });
        }

        res.json({
            success: true,
            import: importData
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

module.exports = router;
