# scrapers/browser_controller.py
"""Browser control and scrolling functionality"""

import time
import threading
from typing import Optional

class BrowserController:
    def __init__(self, sb):
        self.sb = sb
        from config import Config
        self.config = Config()
    
    def count_ad_elements(self):
        """Count elements matching the ad selector"""
        try:
            elements = self.sb.find_elements(self.config.AD_WRAPPER_SELECTOR)
            return len(elements)
        except Exception as e:
            print(f"Error counting elements: {e}")
            return 0
    
    def try_load_more_content(self):
        """Try various methods to trigger loading more content"""
        try:
            # Check for loading indicators
            if self.sb.is_element_present("div[role='progressbar']"):
                print("Found loading indicator, waiting...")
                time.sleep(self.config.LOAD_WAIT_TIME)
            
            # Try to find and click load more buttons
            load_more_selectors = [
                "[data-testid='more-items-button']",
                "button:contains('See more')",
                "button:contains('Load more')",
                "[aria-label*='more']"
            ]
            
            for selector in load_more_selectors:
                if self.sb.is_element_present(selector):
                    print(f"Found load more button: {selector}")
                    self.sb.click(selector)
                    time.sleep(3)
                    break
                    
        except Exception as e:
            print(f"Error trying load more: {e}")
    
    def simulate_user_interaction(self):
        """Simulate user interactions to trigger content loading"""
        self.sb.execute_script("""
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
    
    def scroll_to_bottom_and_get_html(self):
        """Improved infinite scrolling function for Facebook Ads Library"""
        print("Starting infinite scroll...")
        print("Press Ctrl+C to stop scrolling, or close the browser window")
        
        scroll_count = 0
        stop_scrolling = False
        last_height = 0
        stall_count = 0
        
        def check_for_stop():
            nonlocal stop_scrolling
            try:
                input("Press Enter to stop scrolling...\n")
                stop_scrolling = True
            except:
                pass
        
        # Start a thread to listen for user input
        stop_thread = threading.Thread(target=check_for_stop, daemon=True)
        stop_thread.start()
        
        try:
            # Wait for initial page load
            self.sb.sleep(2)
            print("Page loaded, starting scroll...")
            
            # Count initial elements
            initial_count = self.count_ad_elements()
            print(f"📊 Initial element count: {initial_count}")
            
            while not stop_scrolling:
                scroll_count += 1
                
                # Multiple scroll methods
                self.sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                try:
                    self.sb.scroll_to_bottom()
                except:
                    pass
                
                # Incremental scrolls
                current_position = self.sb.execute_script("return window.pageYOffset;")
                page_height = self.sb.execute_script("return document.body.scrollHeight")
                
                if current_position < page_height - 1000:
                    for i in range(3):
                        self.sb.execute_script(f"window.scrollBy(0, {page_height // 4});")
                        time.sleep(1)
                
                # Final scroll to bottom
                self.sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(self.config.LOAD_WAIT_TIME)
                
                # Count elements and check for new content
                element_count = self.count_ad_elements()
                print(f"📊 Current element count: {element_count}")
                
                new_height = self.sb.execute_script("return document.body.scrollHeight")
                
                if new_height > last_height:
                    last_height = new_height
                    stall_count = 0
                else:
                    stall_count += 1
                    
                    if stall_count < self.config.MAX_STALLS:
                        print("Trying alternative scroll methods...")
                        
                        # Alternative loading methods
                        self.sb.execute_script("window.scrollBy(0, -500);")
                        time.sleep(1)
                        self.sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(3)
                        
                        self.try_load_more_content()
                        self.simulate_user_interaction()
                        time.sleep(3)
                        
                        # Check again
                        final_height = self.sb.execute_script("return document.body.scrollHeight")
                        final_element_count = self.count_ad_elements()
                        print(f"📊 Final element count: {final_element_count}")
                        
                        if final_height > last_height:
                            last_height = final_height
                            stall_count = 0
                
                # Continue even if stalled (infinite scroll)
                if stall_count >= self.config.MAX_STALLS:
                    print("Reached max stalls, but continuing infinite scroll...")
                    stall_count = 0
                    time.sleep(self.config.LOAD_WAIT_TIME)
                
                time.sleep(self.config.SCROLL_WAIT_TIME)
                
        except KeyboardInterrupt:
            print("\nScrolling stopped by user (Ctrl+C)")
        except Exception as e:
            print(f"Error during scrolling: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"Finished scrolling. Total attempts: {scroll_count}, Final height: {last_height}")
        return self.sb.get_page_source()
