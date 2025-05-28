# scrapers/ad_scraper.py
"""Facebook ads data scraper"""

import re
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup

class FacebookAdScraper:
    def __init__(self):
        from config import Config
        from scrapers.media_extractor import MediaExtractor
        from utils.date_utils import extract_ad_times
        
        self.config = Config()
        self.media_extractor = MediaExtractor()
        self.extract_ad_times = extract_ad_times
    
    def extract_library_id(self, ad_wrapper):
        """Extract library ID from ad wrapper"""
        try:
            library_id_elem = ad_wrapper.select_one(self.config.LIBRARY_ID_SELECTOR)
            library_id_text = library_id_elem.get_text(strip=True) if library_id_elem else ""
            
            # Extract numeric ID from "Library ID: 1665798290789134"
            library_id_match = re.search(r'Library ID:\s*(\d+)', library_id_text)
            return library_id_match.group(1) if library_id_match else library_id_text
        except Exception as e:
            return ""
    
    def extract_start_date_info(self, ad_wrapper):
        """Extract start date and timing information"""
        try:
            start_elem = ad_wrapper.select_one(self.config.START_DATE_SELECTOR)
            start_text = start_elem.get_text(strip=True) if start_elem else ""
            return self.extract_ad_times(start_text)
        except Exception as e:
            return {'start_at': ""}
    
    def extract_basic_info(self, ad_wrapper):
        """Extract basic ad information"""
        info = {}
        
        # Category name
        try:
            category_elem = ad_wrapper.select_one(self.config.CATEGORY_SELECTOR)  
            info['category_name'] = category_elem.get_text(strip=True) if category_elem else ""
        except:
            info['category_name'] = ""
        
        # CTA
        try:
            cta_elem = ad_wrapper.select_one(self.config.CTA_SELECTOR)
            info['cta'] = cta_elem.get_text(strip=True) if cta_elem else ""
        except:
            info['cta'] = ""
        
        # Page name
        try:
            page_name_elem = ad_wrapper.select_one(self.config.PAGE_NAME_SELECTOR)
            info['page_name'] = page_name_elem.get_text(strip=True) if page_name_elem else ""
        except:
            info['page_name'] = ""
        
        # Page image link
        try:
            page_img_elem = ad_wrapper.select_one(self.config.PAGE_IMAGE_LINK_SELECTOR)
            info['page_image_link'] = page_img_elem.get('href', '') if page_img_elem else ""
        except:
            info['page_image_link'] = ""
        
        # Ad description
        try:
            desc_elem = ad_wrapper.select_one(self.config.AD_DESCRIPTION_SELECTOR)
            info['ad_description'] = desc_elem.get_text(strip=True) if desc_elem else ""
        except:
            info['ad_description'] = ""
        
        # Page link
        try:
            page_link_elem = ad_wrapper.select_one(self.config.PAGE_IMAGE_LINK_SELECTOR)
            info['page_link'] = page_link_elem.get_text(strip=True) if page_link_elem else ""
        except:
            info['page_link'] = ""
        
        return info
    
    def extract_media_info(self, ad_wrapper):
        """Extract media links and assets"""
        try:
            target_element = ad_wrapper.select_one(self.config.MEDIA_CONTAINER_SELECTOR)
            
            if target_element:
                return self.media_extractor.extract_media_links(target_element)
            else:
                return {'images': [], 'videos': [], 'audio': []}
                
        except Exception as e:
            return {'images': [], 'videos': [], 'audio': []}
    
    def scrape_single_ad(self, ad_wrapper, keyword):
        """Scrape data from a single ad wrapper element"""
        ad_data = {}
        
        # Extract library ID
        ad_data['library_id'] = self.extract_library_id(ad_wrapper)
        
        # Extract timing information
        timing_info = self.extract_start_date_info(ad_wrapper)
        ad_data.update(timing_info)
        
        # Extract basic information
        basic_info = self.extract_basic_info(ad_wrapper)
        ad_data.update(basic_info)
        
        # Extract media information
        ad_data['media_links'] = self.extract_media_info(ad_wrapper)
        
        # Add metadata
        ad_data['keyword'] = keyword
        ad_data['scraped_at'] = datetime.now().isoformat()
        
        return ad_data
    
    def scrape_facebook_ads(self, html_content, keyword):
        """Scrape Facebook ads data from HTML content"""
        try:
            print("\n🔍 Starting data extraction...")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            ad_wrappers = soup.select(self.config.AD_WRAPPER_SELECTOR)
            print(f"📊 Found {len(ad_wrappers)} ad elements to scrape")
            
            scraped_data = []
            
            for i, ad_wrapper in enumerate(ad_wrappers, 1):
                print(f"Processing ad {i}/{len(ad_wrappers)}", end='\r')
                
                ad_data = self.scrape_single_ad(ad_wrapper, keyword)
                scraped_data.append(ad_data)
            
            print(f"\n✓ Successfully scraped {len(scraped_data)} ads")
            return scraped_data
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            return []
