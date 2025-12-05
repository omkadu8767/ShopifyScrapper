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

            const prompt = `You are a premium Shopify product description writer for successful ${targetLangName} e-commerce stores. Write like top brands: Zara, H&M, Sephora, IKEA.

Product: ${productTitle}

Chinese Description:
${chineseText}

❌ BAD Description (what NOT to write):
"Această geantă este produsă din materiale de înaltă calitate. Are un design modern și este foarte bună. Vă va plăcea cu siguranță acest produs. Este perfectă pentru utilizare zilnică."

Why BAD?
- Generic phrases ("high quality", "modern design", "you will love")
- No specific details
- Sounds like machine translation
- No personality or brand voice

✅ GOOD Description Example:
"<p>Această geantă elegantă din piele ecologică îmbină stilul contemporan cu funcționalitatea practică. Perfectă pentru femeia modernă care apreciază detaliile rafinate și organizarea eficientă.</p>

<ul>
<li><strong>Design versatil</strong> – se potrivește atât pentru birou cât și pentru ieșirile casual</li>
<li><strong>Compartimente multiple</strong> – buzunar pentru laptop până la 14", buzunare interioare pentru telefon și card-uri</li>
<li><strong>Material durabil</strong> – piele ecologică rezistentă la zgârieturi, cusături întărite</li>
<li><strong>Dimensiuni optime</strong> – 35cm x 28cm x 12cm, suficient spațiu fără să fie voluminoasă</li>
</ul>

<p>Cu bareta ajustabilă și mânerele ergonomice, această geantă oferă confort pe tot parcursul zilei. Închiderea cu fermoar asigură protecția obiectelor personale.</p>"

Why GOOD?
- Specific details (dimensions, materials, features)
- Benefits explained (not just listed)
- Professional Romanian phrasing
- Structured with HTML
- Sounds human, not translated

YOUR TASK - Create description following this structure:

1. Opening Paragraph (2-3 sentences):
   - What is it + main appeal
   - Who is it for
   - Key benefit that makes it special

2. Feature List (4-6 bullet points with <strong> tags):
   - Each point: Feature name + specific benefit
   - Use measurements, materials, technical details
   - Explain WHY it matters (benefit)

3. Closing Paragraph (1-2 sentences):
   - Additional value points
   - Usage scenario or final benefit

STRICT Rules:
1. ZERO Chinese characters
2. NO generic phrases: "high quality", "fashionable", "perfect gift", "you will love"
3. BE SPECIFIC: use actual numbers, materials, dimensions
4. NATURAL ${targetLangName}: sound like a native speaker, not translation
5. HTML format: <p>, <ul>, <li>, <strong>
6. 250-450 words
7. Professional tone: confident but not pushy
8. Focus on BENEFITS not just features
9. For Romanian: use diacritice (ă, â, î, ș, ț)
10. NO time references (2024, 2025, new, latest)

Start directly with <p> tag. NO intro, NO explanations, just the description:`;

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

            const prompt = `You are an expert Shopify product title writer. Transform this Chinese title into a PREMIUM, PROFESSIONAL ${targetLangName} product title that would appear on high-end online stores.

Chinese Title: ${chineseTitle}

❌ BAD Examples (cheap marketplace style):
- "Geanta de mana pentru femei 2024 noua moda umar"
- "Fashion Ladies Bag Wholesale Price Hot Sale"
- "New Arrival Women Handbag Latest Design"
- Any title with: wholesale, factory, 2024, 2025, hot, new, latest

✅ GOOD Examples (premium Shopify style):
- "Geantă Elegantă din Piele Naturală"
- "Rucsac Urban Impermeabil cu Port USB"
- "Ceas Inteligent cu Monitor Cardiac"
- "Cercei din Argint 925 cu Cristale"
- "Rochie de Seară cu Decolteu în V"

STRICT Rules:
1. ZERO Chinese characters - must be 100% ${targetLangName}
2. NO direct translation - completely rewrite
3. NO marketplace words: wholesale, factory, supplier, bulk, MOQ, OEM
4. NO time references: 2024, 2025, new, latest, trending, hot
5. Focus on WHAT IT IS + KEY FEATURE (material, style, function)
6. Sound like luxury brands: Zara, H&M, Sephora style
7. Maximum 70 characters
8. Romanian style: capitalize only first word
9. NO quotes, NO punctuation at end
10. Make it sound like something you'd buy yourself

Return ONLY the professional title, nothing else:`;

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
