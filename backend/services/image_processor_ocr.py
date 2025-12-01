"""
Advanced Image Processing Module with OCR
Downloads, optimizes, detects Chinese text, and translates text in images
"""

import os
import sys
import json
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import re
from pathlib import Path

try:
    import pytesseract
    import cv2
    import numpy as np
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    print("Warning: pytesseract/opencv not available. OCR features disabled.", file=sys.stderr)


class ImageProcessorOCR:
    def __init__(self, translator_service=None, output_dir='downloads/images', 
                 image_format='webp', quality=85, max_width=2048):
        self.translator = translator_service
        self.output_dir = output_dir
        self.image_format = image_format.lower()
        self.quality = quality
        self.max_width = max_width
        
        # Create output directory
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        self.ocr_available = PYTESSERACT_AVAILABLE

    def has_chinese_text(self, text):
        """Check if text contains Chinese characters"""
        if not text:
            return False
        # Chinese Unicode range: \u4e00-\u9fff
        return bool(re.search(r'[\u4e00-\u9fff]', text))

    def extract_text_from_image(self, image):
        """Extract text from image using OCR"""
        if not self.ocr_available:
            return None
        
        try:
            # Convert PIL image to numpy array for OpenCV
            img_array = np.array(image)
            
            # Convert RGB to BGR for OpenCV
            if len(img_array.shape) == 3:
                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            else:
                img_cv = img_array
            
            # Enhance image for better OCR
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            # Apply thresholding to make text clearer
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Extract text using Tesseract with Chinese language support
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(thresh, lang='chi_sim+eng', config=custom_config)
            
            return text.strip()
        except Exception as e:
            print(f"OCR extraction error: {e}", file=sys.stderr)
            return None

    def detect_text_regions(self, image):
        """Detect regions in image that contain text"""
        if not self.ocr_available:
            return []
        
        try:
            img_array = np.array(image)
            
            if len(img_array.shape) == 3:
                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            else:
                img_cv = img_array
            
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Get detailed OCR data with bounding boxes
            data = pytesseract.image_to_data(gray, lang='chi_sim+eng', 
                                            output_type=pytesseract.Output.DICT)
            
            text_regions = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                if text and self.has_chinese_text(text):
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    conf = int(data['conf'][i])
                    
                    if conf > 30:  # Confidence threshold
                        text_regions.append({
                            'text': text,
                            'bbox': (x, y, w, h),
                            'confidence': conf
                        })
            
            return text_regions
        except Exception as e:
            print(f"Text region detection error: {e}", file=sys.stderr)
            return []

    async def translate_text_in_image(self, image, text_regions):
        """Replace Chinese text with English in image (simplified version)"""
        # This is a complex feature that would require:
        # 1. Advanced image inpainting to remove original text
        # 2. Font matching and rendering
        # 3. Text positioning and sizing
        # For now, we'll just detect and report Chinese text
        # A full implementation would need additional libraries like:
        # - opencv-contrib for inpainting
        # - pillow with custom fonts
        # - more advanced text removal algorithms
        
        print(f"Detected {len(text_regions)} Chinese text regions in image", file=sys.stderr)
        for region in text_regions:
            print(f"  - '{region['text']}' at {region['bbox']}", file=sys.stderr)
        
        return image  # Return original for now

    def download_and_process(self, image_url, product_name='product', index=0, 
                            check_chinese=True, translate_text=False):
        """
        Download and process image with optional OCR and translation
        """
        try:
            # Download image
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Open image
            img = Image.open(BytesIO(response.content))
            
            # Check for Chinese text if requested
            has_chinese = False
            chinese_texts = []
            
            if check_chinese and self.ocr_available:
                extracted_text = self.extract_text_from_image(img)
                if extracted_text and self.has_chinese_text(extracted_text):
                    has_chinese = True
                    chinese_texts.append(extracted_text)
                    print(f"⚠️ Chinese text detected in image {index + 1}", file=sys.stderr)
                    
                    # If translation requested, detect regions (future enhancement)
                    if translate_text:
                        text_regions = self.detect_text_regions(img)
                        # Full text translation in images would be implemented here
                        pass
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large
            if img.width > self.max_width:
                ratio = self.max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((self.max_width, new_height), Image.Resampling.LANCZOS)
            
            # Generate SEO-friendly filename
            safe_name = self._sanitize_filename(product_name)
            filename = f"{safe_name}-{index + 1:02d}.{self.image_format}"
            filepath = os.path.join(self.output_dir, filename)
            
            # Save optimized image
            if self.image_format == 'webp':
                img.save(filepath, 'WEBP', quality=self.quality, optimize=True)
            elif self.image_format == 'jpg' or self.image_format == 'jpeg':
                img.save(filepath, 'JPEG', quality=self.quality, optimize=True)
            elif self.image_format == 'png':
                img.save(filepath, 'PNG', optimize=True)
            else:
                img.save(filepath, quality=self.quality, optimize=True)
            
            # Get file size
            file_size = os.path.getsize(filepath)
            
            return {
                'success': True,
                'local_path': filepath,
                'filename': filename,
                'size_bytes': file_size,
                'size_kb': round(file_size / 1024, 2),
                'width': img.width,
                'height': img.height,
                'original_url': image_url,
                'has_chinese_text': has_chinese,
                'chinese_texts': chinese_texts if has_chinese else []
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'original_url': image_url
            }

    def _sanitize_filename(self, name):
        """Create SEO-friendly filename from product name"""
        name = name.lower()
        name = re.sub(r'[^\w\s-]', '', name)
        name = re.sub(r'[\s_]+', '-', name)
        name = re.sub(r'-+', '-', name)
        name = name[:50]
        name = name.strip('-')
        return name or 'product'


def main():
    """Command line interface for testing"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'Usage: python image_processor_ocr.py <image_url> [product_name]'
        }))
        sys.exit(1)
    
    image_url = sys.argv[1]
    product_name = sys.argv[2] if len(sys.argv) > 2 else 'product'
    
    processor = ImageProcessorOCR()
    result = processor.download_and_process(image_url, product_name, check_chinese=True)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
