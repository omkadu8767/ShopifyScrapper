/**
 * Shopify Integration Module
 * Handles product upload to Shopify store
 */

const axios = require('axios');

class ShopifyService {
    constructor() {
        this.storeUrl = process.env.SHOPIFY_STORE_URL;
        this.accessToken = process.env.SHOPIFY_ACCESS_TOKEN;
        this.apiVersion = process.env.SHOPIFY_API_VERSION || '2024-10';

        if (!this.storeUrl || !this.accessToken) {
            throw new Error('Shopify credentials not configured');
        }

        this.baseUrl = `https://${this.storeUrl}/admin/api/${this.apiVersion}`;
        this.headers = {
            'X-Shopify-Access-Token': this.accessToken,
            'Content-Type': 'application/json'
        };
    }

    /**
     * Apply pricing rules to a price
     */
    calculatePrice(priceInCNY) {
        const markupPercentage = parseFloat(process.env.PRICE_MARKUP_PERCENTAGE || 2.5);
        const markupFixed = parseFloat(process.env.PRICE_MARKUP_FIXED || 15);
        const cnyToRonRate = parseFloat(process.env.CNY_TO_RON_RATE || 0.68);
        const enable99Rounding = process.env.ENABLE_99_ROUNDING === 'true';

        // Convert CNY to RON
        let price = priceInCNY * cnyToRonRate;

        // Apply percentage markup
        price = price * markupPercentage;

        // Apply fixed markup
        price = price + markupFixed;

        // Apply .99 rounding
        if (enable99Rounding) {
            price = Math.floor(price) + 0.99;
        } else {
            price = Math.round(price * 100) / 100;
        }

        return price;
    }

    /**
     * Sanitize variant value to meet Shopify requirements
     */
    sanitizeVariantValue(value) {
        if (!value || typeof value !== 'string') {
            return 'Default';
        }

        // Trim and limit to 255 characters (Shopify's limit)
        let sanitized = value.trim();
        if (sanitized.length > 255) {
            sanitized = sanitized.substring(0, 252) + '...';
        }

        // Return default if empty after sanitization
        return sanitized || 'Default';
    }

    /**
     * Generate variants from variant data
     */
    generateVariants(variantData, basePrice) {
        if (!variantData || variantData.length === 0) {
            // No variants, return single default variant
            return [{
                option1: 'Default',
                price: this.calculatePrice(basePrice).toFixed(2),
                inventory_quantity: 0,
                inventory_management: 'shopify'
            }];
        }

        // Generate all combinations
        const variants = [];
        const MAX_VARIANTS = 100; // Shopify limit

        if (variantData.length === 1) {
            // Single option (e.g., only color)
            variantData[0].values.slice(0, MAX_VARIANTS).forEach(value => {
                variants.push({
                    option1: this.sanitizeVariantValue(value),
                    price: this.calculatePrice(basePrice).toFixed(2),
                    inventory_quantity: 0,
                    inventory_management: 'shopify'
                });
            });
        } else if (variantData.length === 2) {
            // Two options (e.g., color and size)
            variantData[0].values.forEach(value1 => {
                variantData[1].values.forEach(value2 => {
                    if (variants.length >= MAX_VARIANTS) return;
                    variants.push({
                        option1: this.sanitizeVariantValue(value1),
                        option2: this.sanitizeVariantValue(value2),
                        price: this.calculatePrice(basePrice).toFixed(2),
                        inventory_quantity: 0,
                        inventory_management: 'shopify'
                    });
                });
            });
        } else if (variantData.length >= 3) {
            // Three options (e.g., color, size, material)
            variantData[0].values.forEach(value1 => {
                variantData[1].values.forEach(value2 => {
                    variantData[2].values.forEach(value3 => {
                        if (variants.length >= MAX_VARIANTS) return;
                        variants.push({
                            option1: this.sanitizeVariantValue(value1),
                            option2: this.sanitizeVariantValue(value2),
                            option3: this.sanitizeVariantValue(value3),
                            option3: value3,
                            price: this.calculatePrice(basePrice).toFixed(2),
                            inventory_quantity: 0,
                            inventory_management: 'shopify'
                        });
                    });
                });
            });
        }

        return variants;
    }

    /**
     * Upload image to Shopify and get the uploaded image data
     */
    async uploadImage(imageUrl) {
        try {
            // Shopify can accept image URLs directly
            return {
                src: imageUrl,
                alt: ''
            };
        } catch (error) {
            console.error('Error uploading image:', error);
            throw error;
        }
    }

    /**
     * Create product in Shopify
     */
    async createProduct(productData) {
        try {
            const {
                title,
                description,
                vendor = 'China Supplier',
                productType = '1688 Import',
                tags = [],
                images = [],
                variants = [],
                seoTitle,
                seoDescription,
                priceMin,
                priceMax,
                variantData = []
            } = productData;

            // Calculate base price
            const basePrice = priceMin || priceMax || 0;

            // Generate current date tag
            const currentDate = new Date().toISOString().split('T')[0];
            const productTags = ['import_1688', currentDate, ...tags];

            // Prepare options
            const options = [];
            if (variantData && variantData.length > 0) {
                variantData.forEach((variant, index) => {
                    if (index < 3) { // Shopify supports max 3 options
                        options.push({
                            name: variant.name,
                            values: variant.values
                        });
                    }
                });
            } else {
                options.push({
                    name: 'Title',
                    values: ['Default']
                });
            }

            // Generate variants
            const shopifyVariants = this.generateVariants(variantData, basePrice);

            // Prepare images
            const shopifyImages = images.map((img, index) => ({
                src: img,
                alt: `${title} - image ${index + 1}`
            }));

            // Create product payload
            const payload = {
                product: {
                    title,
                    body_html: description,
                    vendor,
                    product_type: productType,
                    tags: productTags.join(', '),
                    options,
                    variants: shopifyVariants,
                    images: shopifyImages,
                    metafields_global_title_tag: seoTitle || title,
                    metafields_global_description_tag: seoDescription || description.substring(0, 160)
                }
            };

            // Make API request
            const response = await axios.post(
                `${this.baseUrl}/products.json`,
                payload,
                { headers: this.headers }
            );

            return {
                success: true,
                product: response.data.product,
                productId: response.data.product.id
            };

        } catch (error) {
            console.error('Shopify API Error:', error.response?.data || error.message);
            return {
                success: false,
                error: error.response?.data?.errors || error.message
            };
        }
    }

    /**
     * Update product in Shopify
     */
    async updateProduct(productId, updateData) {
        try {
            const response = await axios.put(
                `${this.baseUrl}/products/${productId}.json`,
                { product: updateData },
                { headers: this.headers }
            );

            return {
                success: true,
                product: response.data.product
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.errors || error.message
            };
        }
    }

    /**
     * Get product from Shopify
     */
    async getProduct(productId) {
        try {
            const response = await axios.get(
                `${this.baseUrl}/products/${productId}.json`,
                { headers: this.headers }
            );

            return {
                success: true,
                product: response.data.product
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.errors || error.message
            };
        }
    }

    /**
     * Test Shopify connection
     */
    async testConnection() {
        try {
            const response = await axios.get(
                `${this.baseUrl}/shop.json`,
                { headers: this.headers }
            );

            return {
                success: true,
                shop: response.data.shop
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.errors || error.message
            };
        }
    }
}

module.exports = ShopifyService;
