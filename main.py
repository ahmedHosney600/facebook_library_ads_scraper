from seleniumbase import SB
import os
import time
import threading
from datetime import datetime

DEFAULT_KEYWORDS_FILE = "main_input.txt"

def search_facebook_ads(sb, keyword):
    sb.open(f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=EG&is_targeted_country=false&media_type=all&publisher_platforms[0]=facebook&publisher_platforms[1]=instagram&q={keyword}&search_type=keyword_unordered")
    scroll_to_bottom(sb)
    # Wait for results to load
    sb.sleep(2)

def save_html_content(sb, keyword):
    """Save the current page HTML content to a file"""
    try:
        # Get the full HTML content
        html_content = sb.get_page_source()
        
        # Create filename with timestamp and keyword
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_keyword = safe_keyword.replace(' ', '_')
        filename = f"facebook_ads_{safe_keyword}_{timestamp}.html"
        
        # Create output directory if it doesn't exist
        output_dir = "scraped_html"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filepath = os.path.join(output_dir, filename)
        
        # Save HTML content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ HTML content saved to: {filepath}")
        print(f"✓ File size: {len(html_content):,} characters")
        
        return filepath
        
    except Exception as e:
        print(f"Error saving HTML content: {e}")
        return None

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

def scroll_to_bottom(sb, keyword):
    """Improved infinite scrolling function for Facebook Ads Library"""
    print("Starting infinite scroll...")
    print("Press Ctrl+C to stop scrolling, or close the browser window")
    
    scroll_count = 0
    stop_scrolling = False
    last_height = 0
    stall_count = 0
    max_stalls = 3
    
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
        # Wait for initial page load
        sb.sleep(5)
        print("Page loaded, starting scroll...")
        
        while not stop_scrolling:
            scroll_count += 1
            print(f"Scrolling attempt #{scroll_count}")
            
            # Method 1: Scroll using JavaScript (more reliable for Facebook)
            sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for initial load
            time.sleep(2)
            
            # Method 2: Also try seleniumbase scroll methods
            try:
                sb.scroll_to_bottom()
            except:
                pass
            
            # Method 3: Multiple smaller scrolls to trigger loading
            current_position = sb.execute_script("return window.pageYOffset;")
            page_height = sb.execute_script("return document.body.scrollHeight")
            
            # If we're not at the bottom, do incremental scrolls
            if current_position < page_height - 1000:
                for i in range(3):
                    sb.execute_script(f"window.scrollBy(0, {page_height // 4});")
                    time.sleep(1)
            
            # Final scroll to absolute bottom
            sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait longer for Facebook's lazy loading
            time.sleep(5)
            
            # Check for new content with multiple attempts
            new_height = sb.execute_script("return document.body.scrollHeight")
            
            if new_height > last_height:
                print(f"✓ New content loaded! Height: {last_height} -> {new_height}")
                last_height = new_height
                stall_count = 0
            else:
                stall_count += 1
                print(f"⚠ No new content. Stall count: {stall_count}/{max_stalls}")
                
                # Try alternative loading triggers
                if stall_count < max_stalls:
                    print("Trying alternative scroll methods...")
                    
                    # Method A: Scroll up a bit then back down
                    sb.execute_script("window.scrollBy(0, -500);")
                    time.sleep(1)
                    sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    
                    # Method B: Try clicking or hovering to trigger loading
                    try:
                        # Look for "See More" or loading elements
                        if sb.is_element_present("div[role='progressbar']"):
                            print("Found loading indicator, waiting...")
                            time.sleep(5)
                        
                        # Try to find and click load more buttons
                        load_more_selectors = [
                            "[data-testid='more-items-button']",
                            "button:contains('See more')",
                            "button:contains('Load more')",
                            "[aria-label*='more']"
                        ]
                        
                        for selector in load_more_selectors:
                            if sb.is_element_present(selector):
                                print(f"Found load more button: {selector}")
                                sb.click(selector)
                                time.sleep(3)
                                break
                                
                    except Exception as e:
                        print(f"Error trying load more: {e}")
                    
                    # Method C: Simulate user interaction
                    sb.execute_script("""
                        // Trigger scroll events
                        window.dispatchEvent(new Event('scroll'));
                        window.dispatchEvent(new Event('resize'));
                        
                        // Simulate mouse movement
                        const event = new MouseEvent('mousemove', {
                            view: window,
                            bubbles: true,
                            cancelable: true,
                            clientX: window.innerWidth / 2,
                            clientY: window.innerHeight / 2
                        });
                        document.dispatchEvent(event);
                    """)
                    
                    time.sleep(3)
                    
                    # Check again after all attempts
                    final_height = sb.execute_script("return document.body.scrollHeight")
                    if final_height > last_height:
                        print(f"✓ Alternative methods worked! Height: {last_height} -> {final_height}")
                        last_height = final_height
                        stall_count = 0
            
            # Even if stalled, continue trying (as requested for infinite scroll)
            if stall_count >= max_stalls:
                print("Reached max stalls, but continuing infinite scroll as requested...")
                stall_count = 0  # Reset to keep trying
                time.sleep(5)  # Longer wait before retrying
            
            # Additional wait between scroll attempts
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nScrolling stopped by user (Ctrl+C)")
    except Exception as e:
        print(f"Error during scrolling: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"Finished scrolling. Total attempts: {scroll_count}, Final height: {last_height}")
    

    # Save HTML content after scrolling stops
    return sb
    print("\nSaving HTML content...")
    saved_file = save_html_content(sb, keyword)
    if saved_file:
        print(f"✓ Successfully saved HTML to: {saved_file}")
    else:
        print("✗ Failed to save HTML content")

# Alternative simpler version without threading
def scroll_to_bottom_simple(sb, keyword):
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
        # Save HTML content after stopping
        print("\nSaving HTML content...")
        saved_file = save_html_content(sb, keyword)
        if saved_file:
            print(f"✓ Successfully saved HTML to: {saved_file}")
        else:
            print("✗ Failed to save HTML content")
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
            scroll_to_bottom(sb, keyword)
            
            # Method 2: Simple version (alternative)
            # scroll_to_bottom_simple(sb, keyword)
            
    except Exception as e:
        print(f"An error occurred in main: {e}")

# Enhanced main function with keyword input
def main():
    """Enhanced main function with keyword selection"""
    try:
        # Get keywords from user input or file
        keywords = get_user_input_for_keyword()
        
        if not keywords:
            print("No keywords provided. Using default keyword: accessories")
            keywords = ["accessories"]
        
        for keyword in keywords:
            print(f"\n{'='*50}")
            print(f"Processing keyword: {keyword}")
            print(f"{'='*50}")
            
            with SB(test=True, uc=True, headless=False, extension_dir="./Buster-Captcha-Solver-for-Humans-Chrome-Web-Store") as sb:
                # Navigate to Facebook Ads Library
                sb.open(f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=EG&is_targeted_country=false&media_type=all&publisher_platforms[0]=facebook&publisher_platforms[1]=instagram&q={keyword}&search_type=keyword_unordered")
                
                # Wait for initial page load
                sb.sleep(3)
                
                # Start scrolling and save HTML when stopped
                sb = scroll_to_bottom(sb, keyword)
                # start scraping items now
            print(f"Finished processing keyword: {keyword}")
            
            # Ask if user wants to continue with next keyword (if multiple)
            if len(keywords) > 1 and keyword != keywords[-1]:
                continue_choice = input("\nDo you want to continue with the next keyword? (y/n): ").strip().lower()
                if continue_choice not in ['y', 'yes']:
                    print("Stopping processing of remaining keywords.")
                    break
                    
    except Exception as e:
        print(f"An error occurred in main: {e}")

# Run script if executed directly
if __name__ == "__main__":
    # Use main() for full functionality or test_main() for single keyword testing
    main()
    # test_main()