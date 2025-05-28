from seleniumbase import SB
import os
import time
import threading

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
    """Infinite scrolling function that continues until user stops it"""
    print("Starting infinite scroll...")
    print("Press Ctrl+C to stop scrolling, or close the browser window")
    
    scroll_count = 0
    stop_scrolling = False
    
    def check_for_stop():
        nonlocal stop_scrolling
        try:
            input("Press Enter to stop scrolling...\n")
            stop_scrolling = True
        except:
            pass
    
    # Start a thread to listen for user input to stop scrolling
    stop_thread = threading.Thread(target=check_for_stop, daemon=True)
    stop_thread.start()
    
    try:
        while not stop_scrolling:
            scroll_count += 1
            print(f"Scrolling to bottom - scroll #{scroll_count}")
            
            # Get current page height before scrolling
            current_height = sb.execute_script("return document.body.scrollHeight")
            
            # Scroll to bottom
            sb.scroll_to_bottom()
            
            # Wait for new content to load
            time.sleep(3)
            
            # Check if new content loaded
            new_height = sb.execute_script("return document.body.scrollHeight")
            
            if new_height == current_height:
                print("No new content loaded, continuing to scroll...")
                # Even if no new content, continue scrolling as requested
                time.sleep(2)
            else:
                print(f"New content loaded! Page height: {current_height} -> {new_height}")
            
            # Small delay between scrolls
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nScrolling stopped by user (Ctrl+C)")
    except Exception as e:
        print(f"Error during scrolling: {e}")
    
    print(f"Finished scrolling. Total scrolls: {scroll_count}")

# Alternative simpler version without threading
def scroll_to_bottom_simple(sb):
    """Simple infinite scrolling - stops only when browser is closed or Ctrl+C"""
    print("Starting infinite scroll...")
    print("Press Ctrl+C to stop scrolling, or close the browser window")
    
    scroll_count = 0
    
    try:
        while True:
            scroll_count += 1
            print(f"Scrolling to bottom - scroll #{scroll_count}")
            
            # Scroll to bottom
            sb.scroll_to_bottom()
            
            # Wait between scrolls
            time.sleep(5)  # Adjust this delay as needed
            
    except KeyboardInterrupt:
        print(f"\nScrolling stopped by user. Total scrolls: {scroll_count}")
    except Exception as e:
        print(f"Error during scrolling: {e}")
        print(f"Total scrolls before error: {scroll_count}")

# ==================== Main Entry Point ====================
def test_main():
    """Main entry point for the script"""
    try:
        keyword = "accessories"
        
        with SB(test=True, uc=True, headless=False, extension_dir="./Buster-Captcha-Solver-for-Humans-Chrome-Web-Store") as sb:
            # Navigate to Facebook Ads Library
            sb.open(f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=EG&is_targeted_country=false&media_type=all&publisher_platforms[0]=facebook&publisher_platforms[1]=instagram&q={keyword}&search_type=keyword_unordered")
            
            # Wait for initial page load
            sb.sleep(3)
            
            # Choose which scrolling method you prefer:
            # Method 1: With user input to stop (recommended)
            scroll_to_bottom(sb)
            
            # Method 2: Simple infinite scroll (uncomment to use instead)
            # scroll_to_bottom_simple(sb)
            
    except Exception as e:
        print(f"An error occurred in main: {e}")

# Run script if executed directly
if __name__ == "__main__":
    test_main()