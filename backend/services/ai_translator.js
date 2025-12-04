/**
 * AI Translation Service using OpenAI ChatGPT or Groq
 * Translates Chinese product descriptions to target language
 */

const OpenAI = require('openai');

class AITranslator {
    constructor() {
        this.targetLanguage = process.env.TARGET_LANGUAGE || 'en';

        // Try Groq first (free), fallback to OpenAI
        if (process.env.GROQ_API_KEY) {
            console.log('Using Groq API for translation');
            this.apiKey = process.env.GROQ_API_KEY;
            this.client = new OpenAI({
                apiKey: this.apiKey,
                baseURL: 'https://api.groq.com/openai/v1'
            });
            this.model = 'llama-3.3-70b-versatile'; // Free and fast
        } else if (process.env.OPENAI_API_KEY) {
            console.log('Using OpenAI API for translation');
            this.apiKey = process.env.OPENAI_API_KEY;
            this.client = new OpenAI({
                apiKey: this.apiKey
            });
            this.model = 'gpt-4o-mini'; // Fast and cost-effective
        } else {
            throw new Error('Neither GROQ_API_KEY nor OPENAI_API_KEY provided in environment variables');
        } this.languageNames = {
            'ro': 'Romanian',
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'nl': 'Dutch',
            'pl': 'Polish'
        };
    }

    /**
     * Translate Chinese text to target language
     */
    async translateText(chineseText, context = '') {
        try {
            const targetLangName = this.languageNames[this.targetLanguage] || 'English';

            const prompt = `Translate the following Chinese text to ${targetLangName}. 
Context: ${context}

Chinese text:
${chineseText}

Requirements:
- Translate naturally and accurately
- Remove ALL Chinese characters
- Keep the meaning intact
- Return only the translated text, no explanations`;

            const response = await this.client.chat.completions.create({
                model: this.model,
                messages: [
                    {
                        role: "system",
                        content: "You are a professional translator specializing in e-commerce product descriptions. You translate Chinese to other languages accurately and naturally."
                    },
                    {
                        role: "user",
                        content: prompt
                    }
                ],
                temperature: 0.3, // Lower temperature for more consistent translation
                max_tokens: 2000
            });

            const translatedText = response.choices[0].message.content.trim();

            return {
                success: true,
                translated_text: translatedText,
                original_length: chineseText.length,
                translated_length: translatedText.length
            };

        } catch (error) {
            console.error('Translation error:', error.message);
            return {
                success: false,
                error: error.message,
                translated_text: chineseText // Fallback to original
            };
        }
    }

    /**
     * Translate and rewrite product description for e-commerce
     */
    async translateAndRewrite(chineseText, productTitle = '') {
        try {
            const targetLangName = this.languageNames[this.targetLanguage] || 'English';

            const prompt = `You are a professional e-commerce copywriter for a Romanian online store.

Task: Translate and POLISH this Chinese product description into PROFESSIONAL ${targetLangName} for Shopify.

Product Title: ${productTitle}

Chinese Description:
${chineseText}

Requirements:
1. Translate ALL Chinese text to ${targetLangName}
2. Remove ALL Chinese characters completely
3. POLISH and make it sound PROFESSIONAL and APPEALING
4. Use proper ${targetLangName} grammar and business language
5. Structure with paragraphs and bullet points for readability
6. Highlight key features and benefits (what customer gets)
7. Make it persuasive and engaging
8. NO emojis, NO special characters, NO informal language
9. Return ONLY clean HTML: <p>, <ul>, <li>, <strong>, <br>
10. Keep it 200-500 words
11. Sound like a premium brand, not cheap marketplace
12. For Romanian: Use professional tone, avoid literal translations

Output format: Clean HTML for Shopify (start with <p> tag, no intro text).`;

            const response = await this.client.chat.completions.create({
                model: this.model,
                messages: [
                    {
                        role: "system",
                        content: "You are a professional e-commerce copywriter and translator specializing in polished, high-quality product descriptions. You write in a professional business tone that appeals to customers and builds trust. You never use informal language or direct translations - you adapt the content to sound natural and professional in the target language."
                    },
                    {
                        role: "user",
                        content: prompt
                    }
                ],
                temperature: 0.7,
                max_tokens: 1500
            });

            let translatedText = response.choices[0].message.content.trim();

            // Clean up the response
            translatedText = this.cleanHtml(translatedText);

            return {
                success: true,
                translated_text: translatedText,
                original_length: chineseText.length,
                translated_length: translatedText.length
            };

        } catch (error) {
            console.error('Translation and rewrite error:', error.message);
            return {
                success: false,
                error: error.message,
                translated_text: chineseText // Fallback to original
            };
        }
    }

    /**
     * Generate SEO title and meta description
     */
    async generateSeoFields(productTitle, description = '') {
        try {
            const targetLangName = this.languageNames[this.targetLanguage] || 'English';

            const prompt = `Generate SEO-optimized fields for this e-commerce product in ${targetLangName}:

Product Title: ${productTitle}
Description: ${description.substring(0, 500)}

Generate:
1. SEO Title (50-60 characters, include product name and key benefit)
2. Meta Description (150-160 characters, compelling with call-to-action)

Return ONLY a valid JSON object with keys: "seo_title" and "seo_description"
No markdown, no code blocks, just pure JSON.`;

            const response = await this.client.chat.completions.create({
                model: this.model,
                messages: [
                    {
                        role: "system",
                        content: "You are an SEO expert. Return only valid JSON format."
                    },
                    {
                        role: "user",
                        content: prompt
                    }
                ],
                temperature: 0.5,
                max_tokens: 200
            });

            let resultText = response.choices[0].message.content.trim();

            // Remove markdown code blocks if present
            resultText = resultText.replace(/```json\s*/g, '').replace(/```\s*/g, '');

            const seoData = JSON.parse(resultText);

            return {
                success: true,
                seo_title: seoData.seo_title || productTitle.substring(0, 60),
                seo_description: seoData.seo_description || description.substring(0, 160)
            };

        } catch (error) {
            console.error('SEO generation error:', error.message);
            // Fallback to simple truncation
            return {
                success: true,
                seo_title: productTitle.substring(0, 60),
                seo_description: description.substring(0, 160) || `Buy ${productTitle} online`
            };
        }
    }

    /**
     * Clean and validate HTML output
     */
    cleanHtml(htmlText) {
        // Remove markdown code blocks
        htmlText = htmlText.replace(/```html\s*/g, '').replace(/```\s*/g, '');

        // Remove any remaining Chinese characters
        htmlText = htmlText.replace(/[\u4e00-\u9fff]+/g, '');

        // Ensure proper HTML structure
        if (!htmlText.trim().startsWith('<')) {
            // Wrap plain text in paragraph
            htmlText = `<p>${htmlText}</p>`;
        }

        // Remove excessive newlines
        htmlText = htmlText.replace(/\n{3,}/g, '\n\n');

        return htmlText.trim();
    }

    /**
     * Translate product title
     */
    async translateTitle(chineseTitle) {
        try {
            const targetLangName = this.languageNames[this.targetLanguage] || 'English';

            const prompt = `You are a professional e-commerce copywriter. Translate and polish this product title from Chinese to ${targetLangName}.

Chinese Title: ${chineseTitle}

Requirements:
1. Translate to ${targetLangName} accurately
2. Remove ALL Chinese characters
3. Make it PROFESSIONAL and POLISHED for e-commerce
4. Use proper capitalization (Title Case for English, Sentence case for Romanian)
5. Remove any weird characters or numbers that don't make sense
6. Make it clear, concise, and appealing to customers
7. Keep it under 70 characters
8. NO quotes, NO extra punctuation

Return ONLY the polished title, nothing else.`;

            const response = await this.client.chat.completions.create({
                model: this.model,
                messages: [
                    {
                        role: "system",
                        content: "You are a professional e-commerce copywriter and translator. Create polished, professional product titles."
                    },
                    {
                        role: "user",
                        content: prompt
                    }
                ],
                temperature: 0.5,
                max_tokens: 150
            });

            let translatedTitle = response.choices[0].message.content.trim();

            // Remove quotes if AI added them
            translatedTitle = translatedTitle.replace(/^["']|["']$/g, '');

            // Remove any remaining Chinese characters
            translatedTitle = translatedTitle.replace(/[\u4e00-\u9fff]+/g, '');

            // Clean up extra spaces
            translatedTitle = translatedTitle.replace(/\s+/g, ' ').trim();

            return {
                success: true,
                translated_text: translatedTitle
            };

        } catch (error) {
            console.error('Title translation error:', error.message);
            return {
                success: false,
                error: error.message,
                translated_text: chineseTitle
            };
        }
    }
}

module.exports = AITranslator;
