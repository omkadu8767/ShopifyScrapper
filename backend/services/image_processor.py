"""
Image Processing Module
Downloads, optimizes, and processes product images
"""

import os
import sys
import json
import requests
from PIL import Image
from io import BytesIO
import hashlib
from pathlib import Path
import re


class ImageProcessor:
    def __init__(self, output_dir='downloads/images', image_format='webp', quality=85, max_width=2048):
        self.output_dir = output_dir
        self.image_format = image_format.lower()
        self.quality = quality
        self.max_width = max_width
        
        # Create output directory
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def download_and_process(self, image_url, product_name='product', index=0):
        """
        Download image from URL and process it
        Returns: dict with success status, local_path, and optimized size
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
                'original_url': image_url
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'original_url': image_url
            }

    def process_multiple(self, image_urls, product_name='product'):
        """
        Process multiple images
        Returns: list of results
        """
        results = []
        for index, url in enumerate(image_urls):
            result = self.download_and_process(url, product_name, index)
            results.append(result)
        
        # Summary
        successful = sum(1 for r in results if r.get('success'))
        failed = len(results) - successful
        total_size = sum(r.get('size_kb', 0) for r in results if r.get('success'))
        
        return {
            'images': results,
            'summary': {
                'total': len(results),
                'successful': successful,
                'failed': failed,
                'total_size_kb': round(total_size, 2),
                'total_size_mb': round(total_size / 1024, 2)
            }
        }

    def _sanitize_filename(self, name):
        """
        Create SEO-friendly filename from product name
        """
        # Convert to lowercase
        name = name.lower()
        
        # Remove special characters
        name = re.sub(r'[^\w\s-]', '', name)
        
        # Replace spaces with hyphens
        name = re.sub(r'[\s_]+', '-', name)
        
        # Remove multiple hyphens
        name = re.sub(r'-+', '-', name)
        
        # Limit length
        name = name[:50]
        
        # Remove leading/trailing hyphens
        name = name.strip('-')
        
        return name or 'product'

    def cleanup_temp_files(self):
        """
        Remove temporary downloaded files
        """
        try:
            import shutil
            if os.path.exists(self.output_dir):
                shutil.rmtree(self.output_dir)
                Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}


def main():
    """Command line interface for testing"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'Usage: python image_processor.py <image_url> [product_name]'
        }))
        sys.exit(1)
    
    image_url = sys.argv[1]
    product_name = sys.argv[2] if len(sys.argv) > 2 else 'product'
    
    processor = ImageProcessor()
    result = processor.download_and_process(image_url, product_name)
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
