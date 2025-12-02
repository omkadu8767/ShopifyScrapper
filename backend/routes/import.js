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

        // Validate minimum required data
        if (!productData.title || productData.title.length < 5) {
            throw new Error('No product title found. The page might require CAPTCHA verification or the product does not exist.');
        }

        if (!productData.images || productData.images.length === 0) {
            throw new Error('No product images found. The page might require CAPTCHA verification or the product does not exist.');
        }

        console.log(`[${importId}] Scraped: ${productData.title}`);
        console.log(`[${importId}] Found ${productData.images.length} images`);

        // Update import with title
        await db.updateImport(importId, { title: productData.title });

        // Step 2: Translate title and description
        console.log(`[${importId}] Step 2: Translating content...`);
        const AITranslator = require('../services/ai_translator');
        const translator = new AITranslator();

        // Translate title
        const titleResult = await translator.translateTitle(productData.title);
        productData.translatedTitle = titleResult.translated_text;
        console.log(`[${importId}] Translated title: ${productData.translatedTitle}`);

        // Translate and rewrite description
        const descResult = await translator.translateAndRewrite(
            productData.description || 'High quality product from China',
            productData.translatedTitle
        );
        productData.translatedDescription = descResult.translated_text;
        console.log(`[${importId}] Description translated: ${descResult.success}`);

        // Translate variants (colors, sizes, etc.)
        if (productData.variants && productData.variants.length > 0) {
            console.log(`[${importId}] Translating ${productData.variants.length} variant options...`);
            for (let variant of productData.variants) {
                // Translate variant name (e.g., "颜色" -> "Color")
                const nameResult = await translator.translateText(variant.name, 'variant option name');
                variant.translatedName = nameResult.translated_text;

                // Translate all variant values (e.g., "红色" -> "Red")
                variant.translatedValues = [];
                for (let value of variant.values) {
                    // Skip empty or very long values
                    if (!value || value.length > 500) continue;

                    const valueResult = await translator.translateText(value, `variant value for ${variant.name}`);
                    let translatedValue = valueResult.translated_text;

                    // Truncate to 50 characters max (Shopify limit is 255, but we want clean short values)
                    if (translatedValue.length > 50) {
                        translatedValue = translatedValue.substring(0, 47) + '...';
                    }

                    // Clean up the value
                    translatedValue = translatedValue.trim();

                    if (translatedValue) {
                        variant.translatedValues.push(translatedValue);
                    }
                }

                console.log(`[${importId}] Translated variant "${variant.name}" -> "${variant.translatedName}" with ${variant.translatedValues.length} values`);
            }
        }

        // Update database with translated title
        await db.updateImport(importId, { title: productData.translatedTitle });

        // Step 3: Generate SEO fields
        console.log(`[${importId}] Step 3: Generating SEO fields...`);
        const seoResult = await translator.generateSeoFields(
            productData.translatedTitle,
            productData.translatedDescription
        );
        console.log(`[${importId}] SEO generated: ${seoResult.seo_title}`);

        // Step 4: Filter and process images
        console.log(`[${importId}] Step 4: Filtering ${productData.images.length} images...`);

        // Filter out videos and invalid images
        const validImages = productData.images.filter(url => {
            const lowerUrl = url.toLowerCase();

            // Skip video files
            if (lowerUrl.includes('.mp4') ||
                lowerUrl.includes('.webm') ||
                lowerUrl.includes('.mov') ||
                lowerUrl.includes('.avi') ||
                lowerUrl.includes('.flv') ||
                lowerUrl.includes('/video/') ||
                lowerUrl.includes('videocover')) {
                return false;
            }

            // Allow all images from alicdn (1688's CDN) - they're already validated by scraper
            if (lowerUrl.includes('img.alicdn.com') || lowerUrl.includes('cbu01.alicdn.com')) {
                return true;
            }

            // For other domains, check for valid image extensions
            return lowerUrl.includes('.jpg') ||
                lowerUrl.includes('.jpeg') ||
                lowerUrl.includes('.png') ||
                lowerUrl.includes('.webp');
        });

        console.log(`[${importId}] Filtered to ${validImages.length} valid images (removed ${productData.images.length - validImages.length} videos/invalid)`);

        // Ensure all images have proper HTTPS URLs
        const processedImages = validImages
            .map(url => {
                // Ensure HTTPS protocol
                if (url.startsWith('//')) {
                    return 'https:' + url;
                }
                // Fix http to https for alicdn (they support https)
                if (url.startsWith('http://') && url.includes('alicdn.com')) {
                    return url.replace('http://', 'https://');
                }
                return url;
            })
            .filter(url => url.startsWith('https://')) // Only HTTPS images
            .slice(0, 10); // Limit to 10 images for Shopify

        console.log(`[${importId}] Using ${processedImages.length} images for Shopify`);
        if (processedImages.length > 0) {
            console.log(`[${importId}] First image (thumbnail): ${processedImages[0].substring(0, 80)}...`);
        }

        // Step 5: Upload to Shopify
        console.log(`[${importId}] Step 5: Creating product in Shopify...`);
        const shopifyService = new ShopifyService();

        // Prepare translated variant data for Shopify
        let translatedVariantData = [];

        if (productData.variants && productData.variants.length > 0) {
            translatedVariantData = productData.variants
                .filter(v => {
                    // Only include variants with valid translated values
                    const hasValues = (v.translatedValues && v.translatedValues.length > 0) || (v.values && v.values.length > 0);
                    const hasName = (v.translatedName || v.name);
                    return hasValues && hasName;
                })
                .map(v => {
                    const name = (v.translatedName || v.name).substring(0, 50).trim();
                    const values = (v.translatedValues || v.values)
                        .filter(val => val && val.length > 0 && typeof val === 'string')
                        .map(val => val.trim())
                        .filter(val => val.length > 0) // Remove empty after trim
                        .slice(0, 100) // Shopify limit: 100 variants per option
                        .map(val => {
                            // Ensure each value is within Shopify's 255 char limit
                            if (val.length > 255) {
                                return val.substring(0, 252) + '...';
                            }
                            return val;
                        });

                    // Only return if we have valid values
                    if (values.length > 0) {
                        return {
                            name: name,
                            values: [...new Set(values)] // Remove duplicates
                        };
                    }
                    return null;
                })
                .filter(v => v !== null) // Remove null entries
                .slice(0, 3); // Shopify allows max 3 variant options
        }

        if (translatedVariantData.length === 0) {
            console.log(`[${importId}] No valid variants found - will create single default variant`);
        } else {
            console.log(`[${importId}] Prepared ${translatedVariantData.length} variant options for Shopify`);
            translatedVariantData.forEach(v => {
                console.log(`[${importId}]   - ${v.name}: ${v.values.length} values (${v.values.slice(0, 3).join(', ')}${v.values.length > 3 ? '...' : ''})`);
            });
        }

        const shopifyResult = await shopifyService.createProduct({
            title: productData.translatedTitle,
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
            variantData: translatedVariantData
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
