"""
AI Translation and Description Rewriting Module
Uses Google Gemini API to translate and rewrite product descriptions
"""

import os
import json
import sys
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from openai import OpenAI
except ImportError:
    print(json.dumps({
        'success': False,
        'error': 'openai not installed. Run: pip install openai'
    }))
    sys.exit(1)


class AITranslator:
    def __init__(self, api_key=None, target_language='ro'):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.target_language = target_language or os.getenv('TARGET_LANGUAGE', 'ro')
        
        if not self.api_key:
            raise ValueError('OPENAI_API_KEY not provided')
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = 'gpt-4o-mini'  # Fast and cost-effective
        
        # Language mapping
        self.lang_names = {
            'ro': 'Romanian',
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian'
        }

    def translate_and_rewrite(self, chinese_text, product_title=''):
        """
        Translate Chinese text to target language and rewrite as professional product description
        """
        try:
            target_lang_name = self.lang_names.get(self.target_language, 'English')
            
            prompt = f"""You are a professional e-commerce product description writer.

Task: Translate the following Chinese product description to {target_lang_name} and rewrite it as a professional, engaging Shopify product description.

Product Title: {product_title}

Chinese Description:
{chinese_text}

Requirements:
1. Translate ALL Chinese text to {target_lang_name}
2. Remove ALL Chinese characters completely
3. Rewrite in a professional, marketing-friendly style
4. Use proper paragraphs and bullet points
5. Highlight key features and benefits
6. Make it SEO-friendly
7. NO emojis
8. Return ONLY clean HTML using these tags: <p>, <ul>, <li>, <strong>, <br>
9. Start directly with the description, no titles or labels
10. Keep it between 150-300 words

Output format: Clean HTML suitable for Shopify product description field."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional e-commerce product description writer and translator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            translated_text = response.choices[0].message.content
            
            # Clean up the response
            translated_text = self._clean_html(translated_text)
            
            return {
                'success': True,
                'translated_text': translated_text,
                'original_length': len(chinese_text),
                'translated_length': len(translated_text)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def generate_seo_fields(self, product_title, description=''):
        """
        Generate SEO title and meta description
        """
        try:
            target_lang_name = self.lang_names.get(self.target_language, 'English')
            
            prompt = f"""Generate SEO-optimized fields for this product in {target_lang_name}:

Product Title: {product_title}
Description: {description[:500]}

Generate:
1. SEO Title (50-60 characters, including product name and key benefit)
2. SEO Meta Description (150-160 characters, compelling and includes call-to-action)

Return ONLY a JSON object with keys: "seo_title" and "seo_description"
No markdown, no code blocks, just the JSON object."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an SEO expert. Return only valid JSON, no markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=200
            )
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON from response
            # Remove markdown code blocks if present
            result_text = re.sub(r'```json\s*', '', result_text)
            result_text = re.sub(r'```\s*', '', result_text)
            
            seo_data = json.loads(result_text)
            
            return {
                'success': True,
                'seo_title': seo_data.get('seo_title', product_title[:60]),
                'seo_description': seo_data.get('seo_description', description[:160])
            }
            
        except Exception as e:
            # Fallback to simple truncation
            return {
                'success': True,
                'seo_title': product_title[:60],
                'seo_description': description[:160] if description else f'Buy {product_title} online'
            }

    def generate_image_alt_text(self, product_title, image_index=0):
        """
        Generate SEO-friendly alt text for product images
        """
        try:
            target_lang_name = self.lang_names.get(self.target_language, 'English')
            
            if image_index == 0:
                # Main image
                return f"{product_title} - main product image"
            else:
                # Additional images
                descriptors = ['detail view', 'close-up', 'side view', 'back view', 'features', 'usage example']
                descriptor = descriptors[min(image_index - 1, len(descriptors) - 1)]
                return f"{product_title} - {descriptor}"
                
        except Exception as e:
            return f"{product_title} - image {image_index + 1}"

    def _clean_html(self, html_text):
        """
        Clean and validate HTML output
        """
        # Remove markdown code blocks
        html_text = re.sub(r'```html\s*', '', html_text)
        html_text = re.sub(r'```\s*', '', html_text)
        
        # Remove any remaining Chinese characters
        html_text = re.sub(r'[\u4e00-\u9fff]+', '', html_text)
        
        # Ensure proper HTML structure
        if not html_text.strip().startswith('<'):
            # Wrap plain text in paragraph
            html_text = f'<p>{html_text}</p>'
        
        # Remove excessive newlines
        html_text = re.sub(r'\n{3,}', '\n\n', html_text)
        
        return html_text.strip()


def main():
    """Command line interface for testing"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'Usage: python ai_translator.py "<chinese_text>" [product_title]'
        }))
        sys.exit(1)
    
    chinese_text = sys.argv[1]
    product_title = sys.argv[2] if len(sys.argv) > 2 else ''
    
    translator = AITranslator()
    result = translator.translate_and_rewrite(chinese_text, product_title)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
