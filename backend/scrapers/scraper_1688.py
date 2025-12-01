# -*- coding: utf-8 -*-
"""
1688.com Product Scraper
Extracts product data from 1688.com product pages
"""

import json
import sys
import io
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import time

class Product1688Scraper:
    def __init__(self, url, timeout=60000):
        self.url = url
        self.timeout = timeout
        self.data = {
            'url': url,
            'title': '',
            'price_min': 0,
            'price_max': 0,
            'images': [],
            'description': '',
            'description_images': [],
            'variants': [],
            'attributes': {},
            'sku': ''
        }

    def scrape(self):
        """Main scraping method"""
        try:
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()
                
                # Set longer timeout for page navigation
                page.set_default_timeout(self.timeout)

                # Navigate to page - use 'load' instead of 'networkidle' for faster loading
                page.goto(self.url, timeout=self.timeout, wait_until='load')
                
                # Wait for content to load
                time.sleep(5)
                
                # Get page content
                content = page.content()
                soup = BeautifulSoup(content, 'lxml')

                # Extract data
                self._extract_title(page, soup)
                self._extract_price(page, soup)
                self._extract_images(page, soup)
                self._extract_variants(page, soup)
                self._extract_description(page, soup)
                self._extract_attributes(page, soup)
                self._extract_sku(page, soup)

                browser.close()

                return {
                    'success': True,
                    'data': self.data
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _extract_title(self, page, soup):
        """Extract product title"""
        try:
            # Try multiple selectors
            selectors = [
                'h1.title',
                '.d-title',
                'h1[class*="title"]',
                '.mod-detail-title h1',
                'div[class*="title"] h1'
            ]
            
            for selector in selectors:
                element = page.query_selector(selector)
                if element:
                    self.data['title'] = element.inner_text().strip()
                    break
            
            # Fallback to soup
            if not self.data['title']:
                title_elem = soup.find('h1', class_=re.compile('title|Title'))
                if title_elem:
                    self.data['title'] = title_elem.get_text().strip()

        except Exception as e:
            print(f"Error extracting title: {e}", file=sys.stderr)

    def _extract_price(self, page, soup):
        """Extract price range"""
        try:
            # Look for price in page text
            price_text = page.evaluate('''() => {
                const priceElements = document.querySelectorAll('[class*="price"], [class*="Price"]');
                return Array.from(priceElements).map(el => el.innerText).join(' ');
            }''')
            
            # Extract numbers from price text
            prices = re.findall(r'[\d,]+\.?\d*', price_text)
            if prices:
                # Convert to float and clean
                price_values = [float(p.replace(',', '')) for p in prices if float(p.replace(',', '')) > 0]
                if price_values:
                    self.data['price_min'] = min(price_values)
                    self.data['price_max'] = max(price_values)

            # Fallback: try common price patterns
            if self.data['price_min'] == 0:
                price_pattern = re.compile(r'¥\s*([\d,]+\.?\d*)\s*-\s*¥\s*([\d,]+\.?\d*)')
                match = price_pattern.search(page.content())
                if match:
                    self.data['price_min'] = float(match.group(1).replace(',', ''))
                    self.data['price_max'] = float(match.group(2).replace(',', ''))

        except Exception as e:
            print(f"Error extracting price: {e}", file=sys.stderr)

    def _extract_images(self, page, soup):
        """Extract all product images with improved strategy"""
        try:
            # Scroll to trigger lazy loading
            page.evaluate('window.scrollTo(0, document.body.scrollHeight / 3)')
            time.sleep(2)
            
            # Try to click on image thumbnails to load high-res versions
            try:
                page.evaluate('''() => {
                    const thumbs = document.querySelectorAll('[class*="gallery"] img, [class*="thumb"] img, [class*="preview"] img');
                    thumbs.forEach(thumb => thumb.click());
                }''')
                time.sleep(1)
            except:
                pass
            
            # Extract images with multiple strategies
            images = page.evaluate('''() => {
                const imageUrls = new Set();
                
                // Strategy 1: Gallery/Preview images
                const galleryImages = document.querySelectorAll(
                    '.gallery img, .image-gallery img, [class*="gallery"] img, ' +
                    '[class*="preview"] img, [class*="thumb"] img, [id*="gallery"] img'
                );
                
                // Strategy 2: Main product images
                const productImages = document.querySelectorAll(
                    '.detail-gallery img, .mod-detail-gallery img, ' +
                    '[class*="detail-image"] img, [class*="product-image"] img'
                );
                
                // Strategy 3: All alicdn images (fallback)
                const allImages = document.querySelectorAll('img[src*="img.alicdn.com"], img[data-src*="img.alicdn.com"]');
                
                // Combine all strategies
                [...galleryImages, ...productImages, ...allImages].forEach(img => {
                    // Try multiple attributes
                    let src = img.src || 
                             img.getAttribute('data-src') || 
                             img.getAttribute('data-lazy-src') ||
                             img.getAttribute('data-original') ||
                             img.getAttribute('data-img');
                    
                    if (src) {
                        // Comprehensive video filtering
                        const lowerSrc = src.toLowerCase();
                        if (lowerSrc.includes('video') || 
                            lowerSrc.includes('.mp4') ||
                            lowerSrc.includes('.webm') ||
                            lowerSrc.includes('.mov') ||
                            lowerSrc.includes('.avi') ||
                            lowerSrc.includes('.flv') ||
                            lowerSrc.includes('.m4v') ||
                            lowerSrc.includes('/video/') ||
                            lowerSrc.includes('videocover') ||
                            lowerSrc.includes('video-cover') ||
                            lowerSrc.includes('icon') || 
                            lowerSrc.includes('logo') ||
                            lowerSrc.includes('placeholder') ||
                            lowerSrc.includes('/tb/') ||
                            lowerSrc.includes('40x40') ||
                            lowerSrc.includes('50x50') ||
                            lowerSrc.includes('60x60')) {
                            return;
                        }
                        
                        // Check if image appears to be a video thumbnail/poster
                        const imgClass = (img.className || '').toLowerCase();
                        const imgId = (img.id || '').toLowerCase();
                        const imgAlt = (img.alt || '').toLowerCase();
                        if (imgClass.includes('video') || 
                            imgId.includes('video') ||
                            imgAlt.includes('video') ||
                            imgAlt.includes('play')) {
                            return;
                        }
                        
                        // Check parent elements for video context
                        let parent = img.parentElement;
                        for (let i = 0; i < 3 && parent; i++) {
                            const parentClass = (parent.className || '').toLowerCase();
                            const parentId = (parent.id || '').toLowerCase();
                            if (parentClass.includes('video') || 
                                parentId.includes('video') || 
                                parent.tagName === 'VIDEO') {
                                return;
                            }
                            parent = parent.parentElement;
                        }
                        
                        // Get highest resolution version
                        src = src.replace(/_\\d+x\\d+\\./, '_800x800.');
                        src = src.replace(/\\.jpg_.*?\\.jpg/, '.jpg');
                        src = src.replace(/\\.png_.*?\\.png/, '.png');
                        src = src.replace(/\\.webp_.*?\\.webp/, '.webp');
                        
                        // Remove query parameters that might limit size
                        src = src.split('?')[0];
                        
                        // Ensure https protocol
                        if (src.startsWith('//')) {
                            src = 'https:' + src;
                        }
                        
                        if (src.startsWith('http')) {
                            imageUrls.add(src);
                        }
                    }
                });
                
                return Array.from(imageUrls);
            }''')

            # Deduplicate and add to data
            seen = set()
            for img_url in images:
                # Normalize URL for deduplication
                normalized = img_url.split('?')[0].replace('_800x800', '')
                if normalized not in seen:
                    seen.add(normalized)
                    self.data['images'].append(img_url)
            
            print(f"Found {len(self.data['images'])} unique images", file=sys.stderr)

        except Exception as e:
            print(f"Error extracting images: {e}", file=sys.stderr)

    def _extract_variants(self, page, soup):
        """Extract product variants (colors, sizes, etc.)"""
        try:
            # Get variant data from page
            variants_data = page.evaluate('''() => {
                const variants = [];
                const skuElements = document.querySelectorAll('[class*="sku"], [class*="Sku"]');
                
                skuElements.forEach(sku => {
                    const label = sku.querySelector('[class*="label"]')?.innerText || '';
                    const values = [];
                    
                    const items = sku.querySelectorAll('[class*="item"], li, span[class*="value"]');
                    items.forEach(item => {
                        const text = item.innerText.trim();
                        if (text) values.push(text);
                    });
                    
                    if (label && values.length > 0) {
                        variants.push({
                            name: label,
                            values: values
                        });
                    }
                });
                
                return variants;
            }''')

            self.data['variants'] = variants_data

        except Exception as e:
            print(f"Error extracting variants: {e}", file=sys.stderr)

    def _extract_description(self, page, soup):
        """Extract product description and description images"""
        try:
            # Scroll to description section
            page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2)')
            time.sleep(1)

            # Extract description HTML
            desc_html = page.evaluate('''() => {
                const descSelectors = [
                    '.detail-desc',
                    '[class*="desc-container"]',
                    '[class*="description"]',
                    '#mod-detail-description'
                ];
                
                for (let selector of descSelectors) {
                    const elem = document.querySelector(selector);
                    if (elem) {
                        return elem.innerHTML;
                    }
                }
                return '';
            }''')

            if desc_html:
                # Parse description HTML
                desc_soup = BeautifulSoup(desc_html, 'lxml')
                
                # Extract text
                self.data['description'] = desc_soup.get_text(separator='\n', strip=True)
                
                # Extract description images
                desc_images = desc_soup.find_all('img')
                for img in desc_images:
                    src = img.get('src') or img.get('data-src')
                    if src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        if src not in self.data['description_images']:
                            self.data['description_images'].append(src)

        except Exception as e:
            print(f"Error extracting description: {e}", file=sys.stderr)

    def _extract_attributes(self, page, soup):
        """Extract product attributes/specifications"""
        try:
            attributes = page.evaluate('''() => {
                const attrs = {};
                const attrElements = document.querySelectorAll('[class*="attribute"], [class*="spec"]');
                
                attrElements.forEach(attr => {
                    const labels = attr.querySelectorAll('[class*="label"], dt');
                    const values = attr.querySelectorAll('[class*="value"], dd');
                    
                    for (let i = 0; i < Math.min(labels.length, values.length); i++) {
                        const key = labels[i].innerText.trim();
                        const val = values[i].innerText.trim();
                        if (key && val) {
                            attrs[key] = val;
                        }
                    }
                });
                
                return attrs;
            }''')

            self.data['attributes'] = attributes

        except Exception as e:
            print(f"Error extracting attributes: {e}", file=sys.stderr)

    def _extract_sku(self, page, soup):
        """Extract original SKU if available"""
        try:
            # Look for SKU patterns in page
            sku_text = page.evaluate('''() => {
                const text = document.body.innerText;
                const skuMatch = text.match(/SKU[:\\s]*([A-Z0-9-]+)/i);
                return skuMatch ? skuMatch[1] : '';
            }''')

            self.data['sku'] = sku_text

        except Exception as e:
            print(f"Error extracting SKU: {e}", file=sys.stderr)


def main():
    # Set UTF-8 encoding for stdout on Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', line_buffering=True)
    
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'No URL provided'
        }))
        sys.exit(1)

    url = sys.argv[1]
    
    # Validate URL
    if 'detail.1688.com' not in url and '1688.com/offer/' not in url:
        print(json.dumps({
            'success': False,
            'error': 'Invalid 1688.com URL'
        }))
        sys.exit(1)

    scraper = Product1688Scraper(url)
    result = scraper.scrape()
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
