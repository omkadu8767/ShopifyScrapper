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

            const prompt = `You are an expert Shopify copywriter for premium Romanian e-commerce stores.

Product: ${productTitle}

Chinese Description:
${chineseText}

Your task: Create a PROFESSIONAL Shopify product description in ${targetLangName}.

BAD Description (what NOT to do):
❌ Direct translation of Chinese
❌ "This product is made of high quality material"
❌ Listing random specs without context
❌ Cheap marketplace language

GOOD Description Structure:
✅ Opening paragraph: What it is + main benefit (2-3 sentences)
✅ Key features in bullet points (3-5 points)
✅ Quality/materials highlight
✅ Usage scenarios or who it's for
✅ Closing with value proposition

Rules:
1. NO Chinese characters - completely rewrite
2. Professional ${targetLangName} business language
3. Focus on BENEFITS not just features
4. Use persuasive copywriting (without being salesy)
5. Structure: <p>intro</p><ul><li>feature</li></ul><p>closing</p>
6. 200-400 words total
7. Sound like a premium brand (think IKEA, H&M style)
8. For Romanian: Natural phrasing, not translated from Chinese

Format: Clean HTML starting with <p> tag. NO intro text, start directly with description.`;

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

            const prompt = `You are a professional Shopify store copywriter. Transform this raw Chinese title into a POLISHED, PROFESSIONAL ${targetLangName} product title.

Chinese Title: ${chineseTitle}

BAD Examples (what NOT to do):
❌ "Geanta de mana pentru femei 2024 noua moda umar"
❌ "Wholesale fashion lady handbag 2024 new style"
❌ "女士手提包2024新款时尚" (Chinese characters left)

GOOD Examples (what to do):
✅ "Geantă Elegantă din Piele pentru Femei"
✅ "Rucsac Modern Impermeabil cu Port USB"
✅ "Ceas Inteligent Multifuncțional"

Rules:
1. NO Chinese characters whatsoever
2. NO literal translation - REWRITE professionally
3. NO marketplace language ("wholesale", "factory", "2024", "new arrival")
4. Focus on WHAT IT IS, not when it was made
5. Use professional ${targetLangName} that sounds premium
6. Maximum 65 characters
7. Capitalize first word only (Romanian style)
8. NO quotes, NO punctuation at end

Return ONLY the professional title:`;

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
                temperature: 0.7,
                max_tokens: 200
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
