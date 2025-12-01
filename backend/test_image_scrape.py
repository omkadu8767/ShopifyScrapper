#!/usr/bin/env python
"""Test image scraping for a specific 1688 URL"""

from scrapers.scraper_1688 import Product1688Scraper

def test():
    url = 'https://detail.1688.com/offer/716502772067.html'
    print(f"Testing scrape for: {url}\n")
    
    scraper = Product1688Scraper(url)
    result = scraper.scrape()
    
    if not result.get('success'):
        print(f"Scraping failed: {result.get('error')}")
        return result
    
    data = result.get('data', {})
    
    print(f"\n=== RESULTS ===")
    print(f"Title: {data.get('title', 'N/A')}")
    print(f"Images in data: {len(data.get('images', []))}")
    print(f"Description images: {len(data.get('description_images', []))}")
    
    all_imgs = data.get('images', []) + data.get('description_images', [])
    print(f"Total images: {len(all_imgs)}")
    
    if all_imgs:
        print("\nAll Image URLs:")
        for i, img in enumerate(all_imgs[:15], 1):
            print(f"  {i}. {img}")
    else:
        print("\nNo images found at all!")
    
    return data

if __name__ == "__main__":
    test()
