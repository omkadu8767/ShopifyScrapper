# -*- coding: utf-8 -*-
"""
1688.com Product Scraper
Extracts product data from 1688.com product pages
"""

import json
import sys
import io
import re
import random
import math
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import time
import requests as req_lib

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
        
        # Session storage for persistent cookies
        self.session_dir = Path(__file__).parent.parent / 'browser_sessions'
        self.session_dir.mkdir(exist_ok=True)
        
        # CapSolver API key (from environment variable)
        self.capsolver_key = os.environ.get('CAPSOLVER_API_KEY', '')
        
        # Log CapSolver status
        if self.capsolver_key:
            masked_key = self.capsolver_key[:10] + '...' + self.capsolver_key[-10:]
            print(f"✅ CapSolver API key loaded: {masked_key}", file=sys.stderr)
        else:
            print("⚠️ CapSolver API key NOT found - will use automatic slider solving", file=sys.stderr)
        
        # Realistic user agents pool (latest versions)
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        ]
    
    def extract_offer_id(self, url):
        """Extract offer ID from 1688 URL for API scraping"""
        # https://detail.1688.com/offer/123456789.html
        match = re.search(r'/offer/(\d+)', url)
        if match:
            return match.group(1)
        return None
    
    def try_api_scraping(self, offer_id):
        """Attempt to scrape via 1688 API endpoints (CAPTCHA-free)"""
        try:
            import requests
            
            # 1688 has mobile API endpoints that are less protected
            api_url = f'https://m.1688.com/offer/{offer_id}.html'
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/json',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Referer': 'https://m.1688.com/',
            }
            
            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code == 200:
                print("✅ API scraping successful, parsing mobile page...", file=sys.stderr)
                # Parse mobile HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup
            
        except Exception as e:
            print(f"⚠️ API scraping failed: {e}", file=sys.stderr)
        
        return None
    
    def get_stealth_scripts(self):
        """Return JavaScript to hide automation and randomize fingerprints"""
        return """
            // Overwrite the `webdriver` property
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            
            // Overwrite the `plugins` property
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
                ]
            });
            
            // Overwrite the `languages` property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en-US', 'en']
            });
            
            // Remove automation indicators
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            
            // Randomize canvas fingerprint
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                const shift = Math.random() * 0.0001;
                const context = this.getContext('2d');
                if (context) {
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += shift;
                    }
                    context.putImageData(imageData, 0, 0);
                }
                return originalToDataURL.apply(this, arguments);
            };
            
            // Randomize WebGL fingerprint
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.call(this, parameter);
            };
            
            // Add realistic chrome object
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Randomize screen properties slightly
            const originalScreen = { ...window.screen };
            Object.defineProperty(window, 'screen', {
                get: () => ({
                    ...originalScreen,
                    availWidth: originalScreen.availWidth,
                    availHeight: originalScreen.availHeight,
                    width: originalScreen.width,
                    height: originalScreen.height,
                    colorDepth: 24,
                    pixelDepth: 24
                })
            });
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            console.log('🛡️ Stealth mode activated');
        """
    
    def simulate_human_mouse_movement(self, page):
        """Simulate realistic human mouse movements"""
        try:
            # Random starting position
            start_x = random.randint(100, 400)
            start_y = random.randint(100, 400)
            
            # Move in a curved path
            for i in range(random.randint(3, 6)):
                target_x = random.randint(200, 800)
                target_y = random.randint(200, 600)
                
                # Calculate curved path
                steps = random.randint(8, 15)
                for step in range(steps):
                    progress = step / steps
                    # Add bezier curve effect
                    curve = math.sin(progress * math.pi) * random.uniform(10, 50)
                    
                    current_x = start_x + (target_x - start_x) * progress + curve
                    current_y = start_y + (target_y - start_y) * progress + random.uniform(-10, 10)
                    
                    page.mouse.move(current_x, current_y)
                    time.sleep(random.uniform(0.01, 0.03))
                
                start_x, start_y = target_x, target_y
                time.sleep(random.uniform(0.1, 0.3))
        except:
            pass
    
    def random_scroll(self, page):
        """Simulate human scrolling behavior"""
        try:
            scroll_count = random.randint(2, 5)
            for _ in range(scroll_count):
                # Random scroll amount
                scroll_y = random.randint(100, 500)
                page.evaluate(f'window.scrollBy(0, {scroll_y})')
                time.sleep(random.uniform(0.5, 1.5))
                
                # Sometimes scroll back up
                if random.random() > 0.6:
                    page.evaluate(f'window.scrollBy(0, -{random.randint(50, 200)})')
                    time.sleep(random.uniform(0.3, 0.8))
        except:
            pass
    
    def human_like_track(self, distance):
        """
        Generate extremely human-like mouse movement for slider CAPTCHA.
        Includes:
        - non-linear speed
        - overshoot
        - micro corrections
        - jitters
        """
        track = []

        # Target overshoot (human error)
        overshoot = random.randint(8, 15)
        total_distance = distance + overshoot

        # Human-like acceleration & deceleration
        current = 0
        mid = total_distance * random.uniform(0.4, 0.6)

        while current < total_distance:
            if current < mid:
                # Accelerating
                move = random.randint(6, 12)
            else:
                # Decelerating
                move = random.randint(2, 6)

            # Random jitter (very important)
            move = max(1, int(move * random.uniform(0.7, 1.3)))
            current += move
            track.append(move)

            # Random micro-pause
            if random.random() < 0.20:
                track.append(0)

        # After overshoot → human corrects back
        correction = -overshoot + random.randint(-2, 2)
        track.append(correction)

        return track

    def solve_with_capsolver(self, page):
        """Use CapSolver API to solve slider CAPTCHA"""
        if not self.capsolver_key:
            print("⚠️ CapSolver API key not configured", file=sys.stderr)
            return False
        
        try:
            print("=" * 60, file=sys.stderr)
            print("🔧 CAPSOLVER: Starting CAPTCHA solving process...", file=sys.stderr)
            print(f"🔑 CAPSOLVER: API Key present: {self.capsolver_key[:15]}...", file=sys.stderr)
            
            # Get current page URL and screenshot
            page_url = page.url
            print(f"🌐 CAPSOLVER: Page URL: {page_url}", file=sys.stderr)
            
            # CapSolver API endpoint
            api_url = "https://api.capsolver.com/createTask"
            print(f"📡 CAPSOLVER: API endpoint: {api_url}", file=sys.stderr)
            
            # Prepare task for CapSolver (Alibaba slider type)
            task_data = {
                "clientKey": self.capsolver_key,
                "task": {
                    "type": "AntiAlibabaSlideTask",  # Specific for Alibaba/1688 slider
                    "websiteURL": page_url,
                    "slideImage": page.screenshot(type='png'),  # CAPTCHA image
                }
            }
            
            print("📤 CAPSOLVER: Sending task to CapSolver API...", file=sys.stderr)
            
            # Create task
            response = req_lib.post(api_url, json=task_data, timeout=30)
            print(f"📥 CAPSOLVER: Response status: {response.status_code}", file=sys.stderr)
            
            result = response.json()
            print(f"📋 CAPSOLVER: Response data: {json.dumps(result, indent=2)}", file=sys.stderr)
            
            if result.get('errorId') != 0:
                error_msg = result.get('errorDescription', 'Unknown error')
                print(f"❌ CAPSOLVER ERROR: {error_msg}", file=sys.stderr)
                print(f"❌ CAPSOLVER: Error ID: {result.get('errorId')}", file=sys.stderr)
                print(f"❌ CAPSOLVER: Full response: {result}", file=sys.stderr)
                return False
            
            task_id = result.get('taskId')
            print(f"✅ CAPSOLVER: Task created successfully!", file=sys.stderr)
            print(f"📋 CAPSOLVER: Task ID: {task_id}", file=sys.stderr)
            
            # Poll for result (max 60 seconds)
            get_result_url = "https://api.capsolver.com/getTaskResult"
            max_attempts = 30
            
            print(f"⏳ CAPSOLVER: Polling for solution (max {max_attempts * 2} seconds)...", file=sys.stderr)
            
            for attempt in range(max_attempts):
                time.sleep(2)
                
                result_response = req_lib.post(
                    get_result_url,
                    json={"clientKey": self.capsolver_key, "taskId": task_id},
                    timeout=10
                )
                result_data = result_response.json()
                
                print(f"🔄 CAPSOLVER: Attempt {attempt + 1}/{max_attempts} - Status: {result_data.get('status')}", file=sys.stderr)
                
                if result_data.get('status') == 'ready':
                    solution = result_data.get('solution', {})
                    slide_distance = solution.get('distance', 0)
                    
                    print(f"🎉 CAPSOLVER: Solution received!", file=sys.stderr)
                    print(f"📊 CAPSOLVER: Solution data: {solution}", file=sys.stderr)
                    
                    if slide_distance > 0:
                        print(f"✅ CAPSOLVER: Slide distance: {slide_distance}px", file=sys.stderr)
                        
                        # Apply the solution to the slider
                        slider_selectors = [
                            'span[id*="nc_"][id*="n1z"]',
                            '.nc_iconfont.btn_slide',
                            '.nc-lang-cnt',
                            '#nc_1_n1z',
                            'span.btn_slide',
                        ]
                        
                        slider = None
                        for selector in slider_selectors:
                            try:
                                slider = page.wait_for_selector(selector, timeout=3000, state='visible')
                                if slider:
                                    break
                            except:
                                continue
                        
                        if not slider:
                            print("❌ CAPSOLVER: Slider element not found on page", file=sys.stderr)
                            return False
                        
                        print("✅ CAPSOLVER: Slider element found, applying solution...", file=sys.stderr)
                        
                        slider_box = slider.bounding_box()
                        start_x = slider_box['x'] + slider_box['width'] / 2
                        start_y = slider_box['y'] + slider_box['height'] / 2
                        
                        print(f"📍 CAPSOLVER: Slider position: ({start_x}, {start_y})", file=sys.stderr)
                        
                        # Use human-like movement with CapSolver's distance
                        track = self.human_like_track(slide_distance)
                        print(f"🎯 CAPSOLVER: Generated {len(track)} movement steps", file=sys.stderr)
                        
                        page.mouse.move(start_x, start_y)
                        time.sleep(random.uniform(0.2, 0.4))
                        page.mouse.down()
                        
                        print("🖱️ CAPSOLVER: Executing slider movement...", file=sys.stderr)
                        
                        current_x = start_x
                        for x_move in track:
                            y_jitter = random.uniform(-1, 1)
                            current_x += x_move
                            page.mouse.move(current_x, start_y + y_jitter)
                            time.sleep(random.uniform(0.006, 0.018))
                        
                        page.mouse.up()
                        print("✅ CAPSOLVER: Slider movement completed!", file=sys.stderr)
                        time.sleep(3)
                        
                        print("=" * 60, file=sys.stderr)
                        return True
                    
                elif result_data.get('status') == 'failed':
                    print(f"❌ CAPSOLVER FAILED: {result_data.get('errorDescription')}", file=sys.stderr)
                    print(f"❌ CAPSOLVER: Error code: {result_data.get('errorId')}", file=sys.stderr)
                    print("=" * 60, file=sys.stderr)
                    return False
                
                # Show progress every 5 attempts
                if attempt > 0 and attempt % 5 == 0:
                    print(f"⏳ CAPSOLVER: Still waiting... ({attempt * 2}s elapsed)", file=sys.stderr)
            
            print("⏰ CAPSOLVER TIMEOUT: No solution received within 60 seconds", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            return False
            
        except Exception as e:
            print(f"❌ CAPSOLVER EXCEPTION: {type(e).__name__}: {e}", file=sys.stderr)
            import traceback
            print(f"🔍 CAPSOLVER: Traceback:\n{traceback.format_exc()}", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            return False

    def solve_alibaba_slider(self, page, max_retries=3):
        """
        Automatically solve Alibaba/1688 slider CAPTCHA with retry handling
        Returns True if solved successfully, False otherwise
        """
        for retry_attempt in range(max_retries):
            try:
                if retry_attempt > 0:
                    print(f"🔄 Retry attempt {retry_attempt}/{max_retries} for slider CAPTCHA...", file=sys.stderr)
                else:
                    print("🤖 Attempting to solve slider CAPTCHA automatically...", file=sys.stderr)
                
                # Wait for slider to fully load and become interactive
                time.sleep(3)
                
                # Take screenshot for debugging
                try:
                    screenshot_path = f"captcha_debug_{int(time.time())}.png"
                    page.screenshot(path=screenshot_path)
                    print(f"📸 Screenshot saved: {screenshot_path}", file=sys.stderr)
                except:
                    pass
                
                # Find the slider button - try multiple selectors with better logging
                slider_selectors = [
                    'span[id*="nc_"][id*="n1z"]',  # Alibaba slider ID pattern
                    '.nc_iconfont.btn_slide',
                    '.nc-lang-cnt',
                    '#nc_1_n1z',
                    'span.btn_slide',
                    '.btn_slide',
                    'span.nc-lang-cnt',
                    '#nc_1__scale_text > span'  # More specific selector
                ]
                
                slider = None
                for selector in slider_selectors:
                    try:
                        slider = page.wait_for_selector(selector, timeout=5000, state='visible')
                        if slider:
                            # Check if element is actually visible and has dimensions
                            is_visible = page.evaluate(f"""
                                (selector) => {{
                                    const el = document.querySelector('{selector}');
                                    if (!el) return false;
                                    const rect = el.getBoundingClientRect();
                                    return rect.width > 0 && rect.height > 0 && 
                                           window.getComputedStyle(el).visibility !== 'hidden' &&
                                           window.getComputedStyle(el).display !== 'none';
                                }}
                            """, selector)
                            
                            if is_visible:
                                print(f"✅ Found visible slider using selector: {selector}", file=sys.stderr)
                                break
                            else:
                                print(f"⚠️ Found slider but not visible: {selector}", file=sys.stderr)
                                slider = None
                    except Exception as e:
                        print(f"❌ Selector failed: {selector} - {e}", file=sys.stderr)
                        continue
                
                if not slider:
                    print("❌ Could not find visible slider element after trying all selectors", file=sys.stderr)
                    print("🔍 Available elements on page:", file=sys.stderr)
                    try:
                        elements_info = page.evaluate("""
                            () => {
                                const nc = document.querySelectorAll('[id*="nc"]');
                                const slides = document.querySelectorAll('[class*="slide"]');
                                return {
                                    nc_elements: Array.from(nc).map(el => ({ id: el.id, class: el.className })),
                                    slide_elements: Array.from(slides).map(el => ({ id: el.id, class: el.className }))
                                };
                            }
                        """)
                        print(f"NC elements: {elements_info['nc_elements'][:3]}", file=sys.stderr)
                        print(f"Slide elements: {elements_info['slide_elements'][:3]}", file=sys.stderr)
                    except:
                        pass
                    
                    if retry_attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    return False
                
                # Get slider position
                slider_box = slider.bounding_box()
                if not slider_box:
                    print("❌ Could not get slider bounding box", file=sys.stderr)
                    if retry_attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return False
                
                print(f"📍 Slider position: x={slider_box['x']}, y={slider_box['y']}", file=sys.stderr)
                
                # Highly randomized slide distance to avoid pattern detection
                base_distance = random.randint(250, 290)
                distance_variation = random.randint(-15, 15)
                slide_distance = base_distance + distance_variation
                
                # Start position (center of slider button)
                start_x = slider_box['x'] + slider_box['width'] / 2
                start_y = slider_box['y'] + slider_box['height'] / 2
                
                print(f"🎯 Starting drag from ({start_x}, {start_y}), distance: {slide_distance}px", file=sys.stderr)
                
                # Generate realistic movement track
                track = self.human_like_track(slide_distance)
                print(f"🚶 Generated {len(track)} movement steps with human-like behavior", file=sys.stderr)
                
                # Initial position
                page.mouse.move(start_x, start_y)
                time.sleep(random.uniform(0.2, 0.4))
                page.mouse.down()
                
                current_x = start_x
                current_y = start_y
                
                # Execute human-like movement
                for x_move in track:
                    # Small vertical jitter (very important for human behavior)
                    y_jitter = random.uniform(-1, 1)
                    
                    current_x += x_move
                    page.mouse.move(current_x, start_y + y_jitter)
                    
                    # Small human micro-delays
                    time.sleep(random.uniform(0.006, 0.018))
                
                page.mouse.up()
                
                print("✓ Slider drag completed, waiting for verification...", file=sys.stderr)
                time.sleep(3)
                
                # Check result
                page_text = page.evaluate('() => document.body ? document.body.innerText : ""')
                
                # Check for failure message "验证失败，点击框体重试"
                if '验证失败' in page_text or 'error:91qpc3' in page_text or '点击框体重试' in page_text:
                    print(f"⚠️  Verification failed (error:91qpc3 or similar). Clicking to retry...", file=sys.stderr)
                    
                    # Click on the CAPTCHA box to retry
                    try:
                        # Try clicking on the failure message or CAPTCHA container
                        retry_click_selectors = [
                            '.nc-container',
                            '[id*="nc_"]',
                            '.nc-lang-cnt',
                            'div:has-text("验证失败")',
                            'div:has-text("点击框体重试")'
                        ]
                        
                        clicked = False
                        for selector in retry_click_selectors:
                            try:
                                element = page.query_selector(selector)
                                if element:
                                    element.click()
                                    clicked = True
                                    print(f"✓ Clicked retry element: {selector}", file=sys.stderr)
                                    break
                            except:
                                continue
                        
                        if not clicked:
                            # Generic click on CAPTCHA area
                            page.mouse.click(start_x, start_y)
                            print("✓ Clicked CAPTCHA area to retry", file=sys.stderr)
                        
                        time.sleep(2)
                        # Continue to next retry attempt
                        continue
                        
                    except Exception as click_error:
                        print(f"⚠️  Could not click retry: {click_error}", file=sys.stderr)
                        if retry_attempt < max_retries - 1:
                            continue
                        return False
                
                # Check if still on verification page
                if '请拖动下方滑块完成验证' in page_text or '滑动' in page_text:
                    print("⚠️  CAPTCHA verification text still present", file=sys.stderr)
                    if retry_attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return False
                
                # Check if page is loading (success indicator)
                try:
                    page.wait_for_load_state('domcontentloaded', timeout=5000)
                    print(f"✅ CAPTCHA solved successfully on attempt {retry_attempt + 1}!", file=sys.stderr)
                    return True
                except:
                    # Even if timeout, might be solved
                    print(f"✓ CAPTCHA appears to be solved on attempt {retry_attempt + 1}", file=sys.stderr)
                    return True
                    
            except Exception as e:
                print(f"❌ Error on slider attempt {retry_attempt + 1}: {e}", file=sys.stderr)
                if retry_attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return False
        
        print(f"❌ Failed to solve slider after {max_retries} attempts", file=sys.stderr)
        return False

    def scrape(self):
        """Main scraping method with CAPTCHA bypass"""
        # Disable mobile API - triggers bot detection
        # Go directly to browser with stealth mode
        if False:  # Disabled mobile API
            offer_id = self.extract_offer_id(self.url)
            if offer_id:
                print(f"🔍 Attempting API scraping for offer ID: {offer_id}", file=sys.stderr)
                api_soup = self.try_api_scraping(offer_id)
                if api_soup:
                    try:
                        self._extract_from_mobile_page(api_soup)
                        if self.data['title']:  # If we got data
                            print("✅ Successfully scraped via API (bypassed CAPTCHA)!", file=sys.stderr)
                            return self.data
                    except Exception as e:
                        print(f"⚠️ API parsing failed: {e}, falling back to browser", file=sys.stderr)
        
        # Use browser scraping with full stealth
        try:
            with sync_playwright() as p:
                # Determine headless mode from environment
                # Default to headless on Linux (servers don't have displays)
                headless_mode = os.environ.get('HEADLESS_BROWSER', 'false').lower() == 'true'
                
                # Force headless on Linux servers (no display available)
                import platform
                if platform.system() == 'Linux' and not os.environ.get('DISPLAY'):
                    headless_mode = True
                    print("🐧 Linux server detected - forcing HEADLESS mode", file=sys.stderr)
                
                # Launch browser with maximum stealth
                if headless_mode:
                    print("🌐 Launching browser in HEADLESS mode (production)...", file=sys.stderr)
                else:
                    print("🌐 Launching browser in VISIBLE mode (development)...", file=sys.stderr)
                
                try:
                    # Try to use Chrome (more trusted than Chromium)
                    browser = p.chromium.launch(
                        channel="chrome",
                        headless=headless_mode,
                        args=[
                            '--disable-blink-features=AutomationControlled',
                            '--no-sandbox',
                            '--disable-infobars',
                            '--window-size=1920,1080',
                            '--start-maximized',
                            '--enable-automation=false',
                        ]
                    )
                    print("✅ Using Chrome browser (less detectable)", file=sys.stderr)
                except:
                    # Fallback to Chromium
                    print("⚠️ Chrome not found, using Chromium", file=sys.stderr)
                    browser = p.chromium.launch(
                        headless=headless_mode,
                        args=[
                            '--disable-blink-features=AutomationControlled',
                            '--disable-dev-shm-usage',
                            '--no-sandbox',
                            '--disable-setuid-sandbox',
                            '--disable-infobars',
                            '--disable-gpu',
                            '--disable-software-rasterizer',
                            '--disable-features=IsolateOrigins,site-per-process,BlockInsecurePrivateNetworkRequests',
                            '--disable-web-security',
                            '--allow-running-insecure-content',
                            '--ignore-certificate-errors',
                            '--window-size=1920,1080',
                            '--start-maximized',
                            '--no-first-run',
                            '--no-default-browser-check',
                            '--disable-popup-blocking',
                            '--disable-translate',
                            '--disable-background-timer-throttling',
                            '--disable-backgrounding-occluded-windows',
                            '--disable-renderer-backgrounding',
                            '--disable-hang-monitor',
                            '--disable-prompt-on-repost',
                            '--disable-sync',
                            '--metrics-recording-only',
                            '--enable-automation=false',
                        ]
                    )
                
                # Use persistent context to save cookies between runs
                session_path = str(self.session_dir / '1688_session')
                print(f"💾 Using persistent session: {session_path}", file=sys.stderr)
                
                selected_ua = random.choice(self.user_agents)
                
                # Create or reuse persistent context (keeps cookies/localStorage)
                context = browser.new_context(
                    storage_state=session_path if os.path.exists(session_path) else None,
                    user_agent=selected_ua,
                    viewport={'width': 1920, 'height': 1080},
                    locale='zh-CN',
                    timezone_id='Asia/Shanghai',
                    geolocation={'longitude': 121.4737, 'latitude': 31.2304},
                    permissions=['geolocation'],
                    extra_http_headers={
                        'Accept-Language': 'zh-CN,zh;q=0.9',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Referer': 'https://www.1688.com/',
                        'DNT': '1',
                    }
                )
                
                page = context.new_page()
                
                # Block images, CSS, fonts to load faster and avoid tracking pixels
                print("🚫 Blocking unnecessary resources...", file=sys.stderr)
                page.route('**/*', lambda route: (
                    route.abort() if route.request.resource_type in ['image', 'stylesheet', 'font', 'media']
                    else route.continue_()
                ))
                
                # Inject stealth scripts
                page.add_init_script(self.get_stealth_scripts())
                
                page.set_default_timeout(30000)  # 30 seconds
                
                # Visit homepage first (more human-like behavior)
                print("🏠 Visiting 1688 homepage first...", file=sys.stderr)
                try:
                    page.goto('https://www.1688.com/', wait_until='domcontentloaded', timeout=15000)
                    time.sleep(random.uniform(3, 5))  # Human-like pause
                    
                    # Simulate some mouse movement on homepage
                    page.mouse.move(random.randint(300, 700), random.randint(200, 400))
                    time.sleep(random.uniform(1, 2))
                    
                    print("✅ Homepage visited", file=sys.stderr)
                except Exception as e:
                    print(f"⚠️ Homepage visit issue: {e}, continuing anyway...", file=sys.stderr)
                
                print(f"🚀 Navigating to product: {self.url}", file=sys.stderr)
                
                # Now go to product page
                try:
                    response = page.goto(self.url, wait_until='domcontentloaded', timeout=30000)
                    print(f"✅ Page loaded: {response.status}", file=sys.stderr)
                    
                    # Human simulation
                    time.sleep(random.uniform(3, 5))
                    page.mouse.move(random.randint(200, 800), random.randint(200, 600))
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    print(f"⚠️ Navigation error: {e}", file=sys.stderr)
                
                # Wait for page to fully load and check for CAPTCHA
                print("⏳ Waiting for page content to load...", file=sys.stderr)
                time.sleep(5)
                
                page_text = page.evaluate('() => document.body ? document.body.innerText : ""')
                
                # Check if CAPTCHA is present
                captcha_keywords = ['验证', '滑动', '拖动', '人机', 'verify', 'captcha', '点击查看源网页']
                has_captcha = any(keyword in page_text for keyword in captcha_keywords)
                
                if has_captcha:
                    print("🔐 CAPTCHA detected! Attempting to solve...", file=sys.stderr)
                    
                    # Try CapSolver first (if API key available)
                    capsolver_solved = False
                    if self.capsolver_key:
                        capsolver_solved = self.solve_with_capsolver(page)
                    
                    if capsolver_solved:
                        print("✅ CAPTCHA solved by CapSolver!", file=sys.stderr)
                        time.sleep(5)
                    else:
                        # Fallback to automatic slider solve
                        if self.capsolver_key:
                            print("⚠️ CapSolver failed, trying automatic slider...", file=sys.stderr)
                        
                        auto_solved = self.solve_alibaba_slider(page)
                        
                        if auto_solved:
                            print("✅ CAPTCHA solved automatically!", file=sys.stderr)
                            time.sleep(5)
                        else:
                            print("⚠️ Automatic solving failed.", file=sys.stderr)
                        print("👤 Please solve the CAPTCHA manually in the browser window...", file=sys.stderr)
                        print("⏰ Waiting up to 120 seconds for manual solving...", file=sys.stderr)
                        
                        # Wait for manual CAPTCHA solving (2 minutes)
                        max_wait = 120
                        waited = 0
                        check_interval = 5
                        
                        while waited < max_wait:
                            time.sleep(check_interval)
                            waited += check_interval
                            
                            # Check if CAPTCHA is gone
                            try:
                                current_text = page.evaluate('() => document.body ? document.body.innerText : ""')
                                if not any(kw in current_text for kw in captcha_keywords):
                                    print("✅ CAPTCHA cleared! Continuing...", file=sys.stderr)
                                    break
                            except:
                                pass
                            
                            if waited % 20 == 0:
                                print(f"⏳ Still waiting... ({max_wait - waited}s remaining)", file=sys.stderr)
                        
                        # Final check
                        time.sleep(3)
                        final_text = page.evaluate('() => document.body ? document.body.innerText : ""')
                        if any(kw in final_text for kw in captcha_keywords):
                            print("❌ CAPTCHA still present after waiting.", file=sys.stderr)
                            # Don't fail - try to scrape anyway
                        else:
                            print("✅ CAPTCHA passed!", file=sys.stderr)
                else:
                    print("✅ No CAPTCHA detected, proceeding...", file=sys.stderr)
                
                # Save session state for next run (after CAPTCHA is solved)
                try:
                    context.storage_state(path=session_path)
                    print("💾 Session saved for reuse (CAPTCHA won't appear next time)", file=sys.stderr)
                except:
                    pass
                
                # Continue with scraping regardless of CAPTCHA status
                time.sleep(3)
                
                # Dummy loop to maintain code structure
                captcha_attempts = 0
                max_captcha_attempts = 1
                
                while captcha_attempts < max_captcha_attempts:
                    # Proceed with scraping
                    captcha_attempts += 1
                    print("📊 Starting data extraction...", file=sys.stderr)
                    
                    # Wait a bit more for any dynamic content
                    time.sleep(2)
                    
                    # Check one more time if we're on product page
                    try:
                        current_url = page.url
                        print(f"📍 Current URL: {current_url}", file=sys.stderr)
                        
                        # If still on CAPTCHA or verification page, skip orange button logic
                        if 'verify' in current_url.lower() or 'captcha' in current_url.lower():
                            print("⚠️ Still on verification page, but proceeding to extract anyway...", file=sys.stderr)
                    except:
                        pass
                    
                    # Skip orange button detection - proceed directly to scraping
                    orange_button_found = False  # Initialize variable
                    if False:  # Disabled orange button logic
                        # Try generic approach - find any clickable orange element
                        try:
                            orange_element = page.evaluate("""
                                () => {
                                    const elements = document.querySelectorAll('button, a, span, div[onclick]');
                                    for (let el of elements) {
                                        const style = window.getComputedStyle(el);
                                        const bgColor = style.backgroundColor;
                                        const color = style.color;
                                        const text = el.innerText;
                                        
                                        // Check for orange background or orange text
                                        if ((bgColor.includes('255, 106') || bgColor.includes('255, 102') || 
                                             color.includes('255, 106') || color.includes('255, 102')) ||
                                            (text && (text.includes('确认') || text.includes('验证') || 
                                                     text.includes('继续') || text.includes('查看原网页')))) {
                                            return true;
                                        }
                                    }
                                    return false;
                                }
                            """)
                            
                            if orange_element:
                                page.evaluate("""
                                    () => {
                                        const elements = document.querySelectorAll('button, a, span, div[onclick]');
                                        for (let el of elements) {
                                            const style = window.getComputedStyle(el);
                                            const bgColor = style.backgroundColor;
                                            const color = style.color;
                                            const text = el.innerText;
                                            
                                            if ((bgColor.includes('255, 106') || bgColor.includes('255, 102') || 
                                                 color.includes('255, 106') || color.includes('255, 102')) ||
                                                (text && (text.includes('确认') || text.includes('验证') || 
                                                         text.includes('继续') || text.includes('查看原网页')))) {
                                                el.click();
                                                return;
                                            }
                                        }
                                    }
                                """)
                                orange_button_found = True
                                print("🟠 Found and clicked orange element via JavaScript", file=sys.stderr)
                                time.sleep(3)
                        except:
                            pass
                    
                    if orange_button_found:
                        print("⚠️  Orange button clicked, another CAPTCHA may appear...", file=sys.stderr)
                        time.sleep(3)
                    else:
                        print("ℹ️  No orange button found, proceeding...", file=sys.stderr)
                    
                    # Wait for any navigation to complete
                    try:
                        page.wait_for_load_state('networkidle', timeout=10000)
                        print("✓ Page navigation completed", file=sys.stderr)
                    except:
                        try:
                            page.wait_for_load_state('domcontentloaded', timeout=10000)
                        except:
                            pass
                    
                    time.sleep(3)
                    
                    # Check if product page loaded successfully or if another CAPTCHA appeared
                    try:
                        page_text = page.evaluate('() => document.body ? document.body.innerText : ""')
                        
                        # Check if we're on the product page now
                        has_product_content = False
                        try:
                            # Look for product indicators
                            product_indicators = page.evaluate("""
                                () => {
                                    return !!(
                                        document.querySelector('h1') ||
                                        document.querySelector('img[src*="alicdn"]') ||
                                        document.querySelector('.detail-gallery') ||
                                        document.querySelector('[class*="price"]')
                                    );
                                }
                            """)
                            has_product_content = product_indicators
                        except:
                            pass
                        
                        if has_product_content and '验证' not in page_text and '滑动' not in page_text:
                            print("✅ Product page loaded successfully! Exiting CAPTCHA loop.", file=sys.stderr)
                            break  # Exit the CAPTCHA loop - we're on product page
                        elif '验证' in page_text or '人机' in page_text or '滑动' in page_text:
                            print("⚠️  Another CAPTCHA appeared after clicking orange button! Continuing loop...", file=sys.stderr)
                            continue  # Go back to start of while loop to solve next CAPTCHA
                        else:
                            print("✓ No more CAPTCHAs detected!", file=sys.stderr)
                            break  # Exit the CAPTCHA loop
                    except:
                        break  # If error, assume no more CAPTCHAs
                
                if captcha_attempts >= max_captcha_attempts:
                    print("⚠️  Too many consecutive CAPTCHAs. Proceeding anyway...", file=sys.stderr)
                
                # Scroll to trigger lazy loading after all CAPTCHAs
                try:
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight / 3)')
                    time.sleep(2)
                    page.evaluate('window.scrollTo(0, 0)')
                    time.sleep(2)
                except:
                    pass
                
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
                    # Debug: show what's actually on the page
                    page_preview = page.evaluate('() => document.body ? document.body.innerText.substring(0, 500) : ""')
                    print(f"⚠️ Page preview (first 500 chars): {page_preview}", file=sys.stderr)
                    
                    return {
                        'success': False,
                        'error': f'Failed to extract product title. Page might require CAPTCHA verification. Page preview: {page_preview[:200]}'
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

    def _extract_from_mobile_page(self, soup):
        """Extract data from mobile API page"""
        try:
            # Mobile page has simpler structure
            title = soup.find('h1')
            if title:
                self.data['title'] = title.get_text(strip=True)
            
            # Price from mobile
            price_elem = soup.find('span', class_=re.compile('price|Price'))
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                prices = re.findall(r'\d+\.?\d*', price_text)
                if prices:
                    self.data['price_min'] = float(prices[0])
                    self.data['price_max'] = float(prices[-1])
            
            # Images from mobile
            img_tags = soup.find_all('img', src=re.compile('alicdn'))
            for img in img_tags[:10]:
                img_url = img.get('src') or img.get('data-src')
                if img_url and 'http' in img_url:
                    self.data['images'].append(img_url)
            
            print(f"📱 Mobile scraping extracted: {self.data['title'][:50]}...", file=sys.stderr)
        except Exception as e:
            print(f"⚠️ Mobile extraction error: {e}", file=sys.stderr)
    
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
