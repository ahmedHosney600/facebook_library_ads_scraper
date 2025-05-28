# main.py
"""Main entry point for the Facebook Ads scraper"""

from seleniumbase import SB
from scrapers.browser_controller import BrowserController
from scrapers.ad_scraper import FacebookAdScraper
from utils.file_utils import get_user_input_for_keyword, save_scraped_data

class FacebookAdsScraper:
    def __init__(self):
        self.browser_controller = None
        self.ad_scraper = FacebookAdScraper()
    
    def build_facebook_url(self, keyword):
        """Build Facebook Ads Library URL"""
        base_url = "https://www.facebook.com/ads/library/"
        params = [
            "active_status=active",
            "ad_type=all", 
            "country=EG",
            "is_targeted_country=false",
            "media_type=all",
            "publisher_platforms[0]=facebook",
            "publisher_platforms[1]=instagram",
            f"q={keyword}",
            "search_type=keyword_unordered"
        ]
        return f"{base_url}?{'&'.join(params)}"
    
    def scrape_keyword(self, keyword):
        """Scrape ads for a single keyword"""
        try:
            print(f"\n🔍 Starting scrape for keyword: '{keyword}'")
            
            with SB(test=True, uc=True) as sb:
                # Initialize browser controller
                self.browser_controller = BrowserController(sb)
                
                # Navigate to Facebook Ads Library
                url = self.build_facebook_url(keyword)
                sb.open(url)
                
                # Scroll and get HTML content
                final_html = self.browser_controller.scroll_to_bottom_and_get_html()
                
                # Scrape the data
                scraped_data = self.ad_scraper.scrape_facebook_ads(final_html, keyword)
                
                # Save the results
                save_scraped_data(final_html, scraped_data, keyword)
                
                print(f"✅ Successfully completed scraping for '{keyword}'")
                return True
                
        except Exception as e:
            print(f"❌ Error scraping keyword '{keyword}': {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def scrape_multiple_keywords(self, keywords):
        """Scrape ads for multiple keywords"""
        successful = 0
        failed = 0
        
        for i, keyword in enumerate(keywords, 1):
            print(f"\n{'='*50}")
            print(f"Processing keyword {i}/{len(keywords)}: '{keyword}'")
            print(f"{'='*50}")
            
            if self.scrape_keyword(keyword):
                successful += 1
            else:
                failed += 1
        
        print(f"\n{'='*50}")
        print(f"📊 SCRAPING SUMMARY")  
        print(f"{'='*50}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📝 Total: {len(keywords)}")
        print(f"{'='*50}")
    
    def run_interactive(self):
        """Run the scraper in interactive mode"""
        print("🚀 Facebook Ads Scraper - Interactive Mode")
        print("=" * 50)
        
        keywords = get_user_input_for_keyword()
        
        if not keywords:
            print("❌ No keywords provided. Exiting...")
            return
        
        print(f"📝 Keywords to scrape: {keywords}")
        
        if len(keywords) == 1:
            self.scrape_keyword(keywords[0])
        else:
            self.scrape_multiple_keywords(keywords)
    
    def run_with_keyword(self, keyword):
        """Run the scraper with a specific keyword"""
        print(f"🚀 Facebook Ads Scraper - Single Keyword Mode")
        print("=" * 50)
        self.scrape_keyword(keyword)


def test_main():
    """Main entry point"""
    scraper = FacebookAdsScraper()
    scraper.run_interactive()

if __name__ == "__main__":
    test_main()