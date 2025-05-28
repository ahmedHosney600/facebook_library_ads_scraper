from seleniumbase import SB
import os
import time
DEFAULT_KEYWORDS_FILE = "main_input.txt"


def search_facebook_ads(sb, keyword):
    
    sb.open(f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=EG&is_targeted_country=false&media_type=all&publisher_platforms[0]=facebook&publisher_platforms[1]=instagram&q={keyword}&search_type=keyword_unordered")
    scroll_to_bottom(sb)
    
    # Wait for results to load
    sb.sleep(2)



def load_keywords_from_file(filename):
    if not os.path.exists(filename):
        print(f"Keywords file {filename} not found")
        return []
        
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith('#')]
            
        print(f"Loaded {len(keywords)} keywords from {filename}")
        return keywords
    except Exception as e:
        print(f"Error loading keywords from {filename}: {e}")
        return []


def get_user_input_for_keyword():
    global DEFAULT_KEYWORDS_FILE
    print(f"Default keywords file: {DEFAULT_KEYWORDS_FILE}")

    user_input = input("Enter keyword to search(or press Enter for default): ").strip()
    
    if not os.path.isfile(user_input):
        return [user_input]
    
    keywords_file = user_input if user_input else DEFAULT_KEYWORDS_FILE
    # Try to load keywords from file
    keywords = []
    if os.path.exists(keywords_file):
        keywords = load_keywords_from_file(keywords_file)
        
    return keywords


def scroll_to_bottom(sb):
    is_stop = input("Please Enter any value TO stop scrolling and start scraping now(dont click enter) : ")
    while True:
        if not is_stop:
            print(f"Scrolling to bottom - attempt {i+1}/5")
            sb.scroll_to_bottom()
            time.sleep(10)

# ==================== Main Entry Point ====================
# Replace the current main function with this updated version
def test_main():
    """Main entry point for the script"""
    global KEYWORDS
    
    try:
        # keyword = get_user_input_for_keyword()
        keyword = "accessories"

        # with SB(test=True, uc=True, headless=False) as sb:
        with SB(test=True, uc=True, headless=False, extension_dir="./Buster-Captcha-Solver-for-Humans-Chrome-Web-Store") as sb:
        # with SB(test=True, uc=True, headless=True, incognito=True) as sb:
            # Apply proxy if available
            # if proxy_manager.working_proxies:
            # current_proxy = proxy_manager.get_next_proxy()
            # if current_proxy:
            #     print(f"Starting with proxy: {current_proxy}")
            #     proxy_manager.apply_proxy_to_browser(sb)
            
            # Run the main test function
            search_facebook_ads(sb, keyword)
            # time.sleep(5000)
    except Exception as e:
        print(f"An error occurred in main: {e}")
        print(f"Error: {e}")
        # sys.exit(1)

# Run script if executed directly
if __name__ == "__main__":
    test_main()