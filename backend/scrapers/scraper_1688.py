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
    def __init__(self, url, timeout=120000):  # Increased to 2 minutes
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
                # Launch browser in visible mode to handle CAPTCHA
                browser = p.chromium.launch(
                    headless=False,
                    args=[
                        '--start-maximized',
                        '--disable-blink-features=AutomationControlled'  # Hide automation
                    ]
                )
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    no_viewport=True,  # Use full window size
                    accept_downloads=False,
                    java_script_enabled=True,
                    locale='zh-CN',  # Set Chinese locale for better compatibility
                    timezone_id='Asia/Shanghai'
                )
                page = context.new_page()
                
                # Set longer timeout for page navigation
                page.set_default_timeout(self.timeout)

                print(f"Loading page: {self.url}", file=sys.stderr)
                
                # Navigate to page - use 'domcontentloaded' for faster initial load
                try:
                    page.goto(self.url, timeout=self.timeout, wait_until='domcontentloaded')
                    print("Page loaded, waiting for content...", file=sys.stderr)
                    time.sleep(3)  # Give page time to initialize
                except Exception as e:
                    print(f"Page load warning: {e}", file=sys.stderr)
                
                # Wait for key elements to load (with timeout)
                try:
                    # Wait for either title or images to appear
                    page.wait_for_selector('h1, img[src*="alicdn"]', timeout=15000)
                    print("Key elements detected on page", file=sys.stderr)
                except:
                    print("Warning: Key elements not detected, proceeding anyway...", file=sys.stderr)
                
                # Wait additional time for JavaScript to render content
                time.sleep(8)
                
                # Check if we're blocked or need verification
                try:
                    # Wait for page to be stable first
                    page.wait_for_load_state('domcontentloaded', timeout=10000)
                    page_text = page.evaluate('() => document.body ? document.body.innerText : ""')
                except Exception as e:
                    if 'navigation' in str(e).lower() or 'context' in str(e).lower():
                        print(f"Page is navigating, waiting...", file=sys.stderr)
                        time.sleep(5)
                        try:
                            page.wait_for_load_state('domcontentloaded', timeout=15000)
                            page_text = page.evaluate('() => document.body ? document.body.innerText : ""')
                        except:
                            page_text = ""
                    else:
                        print(f"Warning: Could not check page text: {e}", file=sys.stderr)
                        page_text = ""
                
                if '验证' in page_text or 'verify' in page_text.lower() or 'captcha' in page_text.lower() or '人机' in page_text or '滑动' in page_text:
                    print("⚠️  CAPTCHA DETECTED! Please solve it in the browser window NOW.", file=sys.stderr)
                    print("⚠️  The browser will wait for you to complete the verification.", file=sys.stderr)
                    
                    # Wait and check multiple times if CAPTCHA is solved
                    max_wait_time = 120  # 2 minutes max
                    check_interval = 5   # Check every 5 seconds
                    elapsed = 0
                    
                    while elapsed < max_wait_time:
                        time.sleep(check_interval)
                        elapsed += check_interval
                        
                        # Check if CAPTCHA is gone - with error handling for navigation
                        try:
                            current_text = page.evaluate('() => document.body ? document.body.innerText : ""')
                        except Exception as nav_error:
                            # Page might be navigating during CAPTCHA solving
                            if 'navigation' in str(nav_error).lower() or 'context' in str(nav_error).lower():
                                print("Page is navigating, waiting for it to stabilize...", file=sys.stderr)
                                time.sleep(5)
                                try:
                                    # Wait for navigation to complete
                                    page.wait_for_load_state('domcontentloaded', timeout=10000)
                                    current_text = page.evaluate('() => document.body ? document.body.innerText : ""')
                                except:
                                    # Still navigating, continue waiting
                                    continue
                            else:
                                continue
                        
                        if '验证' not in current_text and '人机' not in current_text and '滑动' not in current_text:
                            print("✓ CAPTCHA appears to be solved! Continuing...", file=sys.stderr)
                            time.sleep(5)  # Extra wait for page to stabilize
                            break
                        
                        if elapsed % 15 == 0:  # Print reminder every 15 seconds
                            print(f"Still waiting for CAPTCHA... ({max_wait_time - elapsed}s remaining)", file=sys.stderr)
                    
                    if elapsed >= max_wait_time:
                        raise Exception("CAPTCHA was not solved within the time limit. Please try again.")
                    
                    print("✓ CAPTCHA solved! Waiting for page to reload content...", file=sys.stderr)
                    
                    # Wait for any navigation to complete after CAPTCHA
                    try:
                        page.wait_for_load_state('networkidle', timeout=15000)
                        print("✓ Page navigation completed", file=sys.stderr)
                    except:
                        print("Using domcontentloaded fallback", file=sys.stderr)
                        try:
                            page.wait_for_load_state('domcontentloaded', timeout=10000)
                        except:
                            pass
                    
                    # Wait for page to reload and content to appear after CAPTCHA
                    time.sleep(5)
                    
                    # Wait for product content to load
                    try:
                        page.wait_for_selector('h1, img[src*="alicdn"]', timeout=20000)
                        print("✓ Product content detected after CAPTCHA", file=sys.stderr)
                    except:
                        print("Warning: Product content not immediately visible, continuing...", file=sys.stderr)
                    
                    time.sleep(3)  # Extra stabilization time
                    
                    # Scroll to trigger lazy loading after CAPTCHA
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight / 3)')
                    time.sleep(2)
                    page.evaluate('window.scrollTo(0, 0)')
                    time.sleep(2)
                
                # Get fresh page content
                content = page.content()
                soup = BeautifulSoup(content, 'lxml')
                
                # Verify page loaded successfully
                if len(content) < 1000:
                    raise Exception("Page content too short - page may not have loaded properly")
                
                print(f"Page content loaded: {len(content)} bytes", file=sys.stderr)
                
                # Final check - make sure we're not still on CAPTCHA page or error page
                final_check = page.evaluate('() => document.body ? document.body.innerText : ""')
                final_check_lower = final_check.lower()
                
                if '验证' in final_check or '人机' in final_check or '滑动' in final_check:
                    raise Exception("Still on CAPTCHA page. Please refresh and try again.")
                
                # Check for error messages
                if ('出错' in final_check or 'error' in final_check_lower or 
                    '错误' in final_check or 'something went wrong' in final_check_lower or
                    '页面不存在' in final_check or 'page not found' in final_check_lower or
                    '找不到' in final_check or '系统繁忙' in final_check):
                    print(f"⚠️  Error page detected after CAPTCHA. Attempting to refresh...", file=sys.stderr)
                    
                    # Try refreshing the page once
                    try:
                        page.reload(wait_until='domcontentloaded', timeout=30000)
                        time.sleep(5)
                        
                        # Check again
                        retry_check = page.evaluate('() => document.body ? document.body.innerText : ""')
                        if ('出错' in retry_check or 'error' in retry_check.lower() or 
                            '错误' in retry_check or '找不到' in retry_check):
                            raise Exception("Page still shows error after refresh. The product may not exist or URL is invalid.")
                        
                        print("✓ Page refreshed successfully", file=sys.stderr)
                        
                        # Get fresh content after refresh
                        content = page.content()
                        soup = BeautifulSoup(content, 'lxml')
                        
                    except Exception as e:
                        raise Exception(f"1688 page shows an error. The product may not exist or there's a temporary issue: {str(e)}")

                # Extract data
                self._extract_title(page, soup)
                self._extract_price(page, soup)
                self._extract_images(page, soup)
                self._extract_variants(page, soup)
                self._extract_description(page, soup)
                self._extract_attributes(page, soup)
                self._extract_sku(page, soup)
                
                print("Data extraction complete", file=sys.stderr)
                time.sleep(2)  # Brief pause before closing

                browser.close()

                # Validate minimum required data
                if not self.data['title'] or len(self.data['title']) < 5:
                    return {
                        'success': False,
                        'error': 'Failed to extract product title. Page might require CAPTCHA verification.'
                    }
                
                if len(self.data['images']) == 0:
                    return {
                        'success': False,
                        'error': 'Failed to extract any images. Page might require CAPTCHA verification.'
                    }

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
            # Company name keywords to filter out
            company_keywords = ['公司', '有限公司', '科技有限', '集团', '股份', '企业']
            
            # Priority 1: Try #productTitle ID (most reliable for product title)
            title_by_id = page.query_selector('#productTitle')
            if title_by_id:
                title = title_by_id.inner_text().strip()
                if title and len(title) > 5:
                    self.data['title'] = title
                    print(f"Found title by #productTitle: {title}", file=sys.stderr)
                    return
            
            # Priority 2: Try common title selectors
            selectors = [
                '.title-text',
                '.d-title',
                'h1.title',
                'h1[class*="title"]',
                '.mod-detail-title h1',
                'div[class*="title"] h1'
            ]
            
            for selector in selectors:
                element = page.query_selector(selector)
                if element:
                    title = element.inner_text().strip()
                    # Filter out company names - they usually contain company keywords
                    if title and len(title) > 5 and not any(keyword in title for keyword in company_keywords):
                        self.data['title'] = title
                        print(f"Found title by {selector}: {title}", file=sys.stderr)
                        return
            
            # Priority 3: Fallback to soup
            if not self.data['title']:
                title_elem = soup.find('h1', class_=re.compile('title|Title'))
                if title_elem:
                    title = title_elem.get_text().strip()
                    # Check for company name
                    if title and len(title) > 5 and not any(keyword in title for keyword in company_keywords):
                        self.data['title'] = title
                        print(f"Found title by soup: {title}", file=sys.stderr)
                        return
            
            # Priority 4: Try meta tags
            if not self.data['title']:
                meta_title = soup.find('meta', property='og:title')
                if meta_title and meta_title.get('content'):
                    title = meta_title.get('content').strip()
                    if title and len(title) > 5 and not any(keyword in title for keyword in company_keywords):
                        self.data['title'] = title
                        print(f"Found title in meta: {title}", file=sys.stderr)
                        return
            
            if not self.data['title']:
                print("Warning: Could not find product title", file=sys.stderr)

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
                        } else if (src.startsWith('http://')) {
                            src = src.replace('http://', 'https://');
                        }
                        
                        // Only add valid HTTPS image URLs from alicdn
                        if (src.startsWith('https://') && src.includes('alicdn.com')) {
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
