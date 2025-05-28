from seleniumbase import SB
import os
import time
import threading
from datetime import datetime
from bs4 import BeautifulSoup
import json
import csv
import re
from urllib.parse import urljoin, urlparse


DEFAULT_KEYWORDS_FILE = "main_input.txt"


def count_ad_elements(sb):
    """Count elements matching the .xrvj5dj > div selector"""
    try:
        elements = sb.find_elements(".xrvj5dj > div")
        return len(elements)
    except Exception as e:
        print(f"Error counting elements: {e}")
        return 0

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

def parse_duration_to_seconds(duration_str):
    """
    Convert duration string like "3 hrs", "2 days", "1 hr 30 mins" to seconds
    """
    total_seconds = 0
    duration_str = duration_str.lower()
    
    # Handle days
    days_match = re.search(r'(\d+)\s*(?:day|days)', duration_str)
    if days_match:
        total_seconds += int(days_match.group(1)) * 24 * 3600
    
    # Handle hours
    hours_match = re.search(r'(\d+)\s*(?:hr|hrs|hour|hours)', duration_str)
    if hours_match:
        total_seconds += int(hours_match.group(1)) * 3600
    
    # Handle minutes
    minutes_match = re.search(r'(\d+)\s*(?:min|mins|minute|minutes)', duration_str)
    if minutes_match:
        total_seconds += int(minutes_match.group(1)) * 60
    
    # Handle seconds
    seconds_match = re.search(r'(\d+)\s*(?:sec|secs|second|seconds)', duration_str)
    if seconds_match:
        total_seconds += int(seconds_match.group(1))
    
    return total_seconds

def extract_ad_times(start_text):
    ad_data = {}
    
    # Parse "Started running on 28 May 2025 · Total active time 3 hrs"
    try:
        if start_text:
            # Extract start date
            start_date_match = re.search(r'Started running on\s+(\d{1,2}\s+\w+\s+\d{4})', start_text)
            if start_date_match:
                start_date_str = start_date_match.group(1)
                ad_data['start_date'] = start_date_str
                # Convert to timestamp
                try:
                    start_date_obj = datetime.strptime(start_date_str, '%d %B %Y')
                    ad_data['start_date_timestamp'] = int(start_date_obj.timestamp())
                except ValueError:
                    # Try alternative date format
                    try:
                        start_date_obj = datetime.strptime(start_date_str, '%d %b %Y')
                        ad_data['start_date_timestamp'] = int(start_date_obj.timestamp())
                    except ValueError:
                        ad_data['start_date_timestamp'] = ""
            else:
                ad_data['start_date'] = ""
                ad_data['start_date_timestamp'] = ""
            
            # Extract activity duration
            duration_match = re.search(r'Total active time\s+(.+?)(?:\s*$|·)', start_text)
            if duration_match:
                duration_str = duration_match.group(1).strip()
                ad_data['activity_duration'] = duration_str
                # Convert duration to timestamp (seconds)
                try:
                    duration_seconds = parse_duration_to_seconds(duration_str)
                    ad_data['activity_duration_timestamp'] = duration_seconds
                except:
                    ad_data['activity_duration_timestamp'] = ""
            else:
                # If no duration found, but we have start_date_timestamp, calculate duration
                if ad_data.get('start_date_timestamp'):
                    try:
                        current_timestamp = int(datetime.now().timestamp())
                        calculated_duration = current_timestamp - ad_data['start_date_timestamp']
                        
                        # Format duration with years, months, days, hours, minutes
                        duration_parts = []
                        remaining_seconds = calculated_duration
                        
                        # Years (approximate: 365.25 days)
                        years = remaining_seconds // (365.25 * 24 * 3600)
                        if years >= 1:
                            duration_parts.append(f"{int(years)} {'year' if years == 1 else 'years'}")
                            remaining_seconds %= (365.25 * 24 * 3600)
                        
                        # Months (approximate: 30.44 days)
                        months = remaining_seconds // (30.44 * 24 * 3600)
                        if months >= 1:
                            duration_parts.append(f"{int(months)} {'month' if months == 1 else 'months'}")
                            remaining_seconds %= (30.44 * 24 * 3600)
                        
                        # Days
                        days = remaining_seconds // (24 * 3600)
                        if days >= 1:
                            duration_parts.append(f"{int(days)} {'day' if days == 1 else 'days'}")
                            remaining_seconds %= (24 * 3600)
                        
                        # Hours
                        hours = remaining_seconds // 3600
                        if hours >= 1:
                            duration_parts.append(f"{int(hours)} {'hr' if hours == 1 else 'hrs'}")
                            remaining_seconds %= 3600
                        
                        # Minutes
                        minutes = remaining_seconds // 60
                        if minutes >= 1:
                            duration_parts.append(f"{int(minutes)} {'min' if minutes == 1 else 'mins'}")
                        
                        # If no significant time units found, show "less than 1 min"
                        if not duration_parts:
                            duration_parts.append("less than 1 min")
                        
                        ad_data['activity_duration'] = f"Calculated: {' '.join(duration_parts)}"
                        ad_data['activity_duration_timestamp'] = calculated_duration
                    except:
                        ad_data['activity_duration'] = ""
                        ad_data['activity_duration_timestamp'] = ""
                else:
                    ad_data['activity_duration'] = ""
                    ad_data['activity_duration_timestamp'] = ""
            
            # Keep original full text for reference
            ad_data['start_at'] = start_text
            
            return ad_data
            
    except Exception as e:
        ad_data['start_at'] = start_text
        return ad_data

def scroll_to_bottom_and_get_html(sb):
    """Improved infinite scrolling function for Facebook Ads Library with element counting"""
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
        sb.sleep(2)
        print("Page loaded, starting scroll...")
        
        # Count initial elements
        initial_count = count_ad_elements(sb)
        print(f"📊 Initial element count : {initial_count}")
        
        while not stop_scrolling:
            scroll_count += 1
            
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
            
            # Count elements after scrolling
            element_count = count_ad_elements(sb)
            print(f"📊 Current element count (.xrvj5dj > div): {element_count}")
            
            # Check for new content with multiple attempts
            new_height = sb.execute_script("return document.body.scrollHeight")
            
            if new_height > last_height:
                # print(f"✓ New content loaded! Height: {last_height} -> {new_height}")
                last_height = new_height
                stall_count = 0
            else:
                stall_count += 1
                # print(f"⚠ No new content. Stall count: {stall_count}/{max_stalls}")
                
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
                            # print("Found loading indicator, waiting...")
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
                                # print(f"Found load more button: {selector}")
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
                    
                    # Check again after all attempts and count elements
                    final_height = sb.execute_script("return document.body.scrollHeight")
                    final_element_count = count_ad_elements(sb)
                    print(f"📊 Current element count (.xrvj5dj > div): {final_element_count}")
                    
                    if final_height > last_height:
                        # print(f"✓ Alternative methods worked! Height: {last_height} -> {final_height}")
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
    
    return sb.get_page_source()

def extract_media_links(element, base_url=None):
    if not element:
        return {
            'images': [],
            'videos': [],
            'audio': [],
        }
    
    media_links = {
        'images': [],
        'videos': [],
        'audio': [],
    }
    
    # Image extensions and patterns
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico', '.tiff'}
    
    # Video extensions and patterns
    video_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v'}
    
    # Audio extensions
    audio_extensions = {'.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac', '.wma'}
    
    def is_media_url(url, extensions):
        """Check if URL has media extension"""
        try:
            parsed = urlparse(url.lower())
            path = parsed.path
            return any(path.endswith(ext) for ext in extensions)
        except:
            return False
    
    def resolve_url(url):
        """Resolve relative URLs if base_url is provided"""
        if base_url and url and not url.startswith(('http://', 'https://', '//')):
            return urljoin(base_url, url)
        return url
    
    # 1. Extract from img tags
    img_tags = element.find_all('img')
    for img in img_tags:
        src = img.get('src')
        if src:
            resolved_url = resolve_url(src)
            media_links['images'].append(resolved_url)
        
        # Check data-src for lazy loading
        data_src = img.get('data-src')
        if data_src:
            resolved_url = resolve_url(data_src)
            media_links['images'].append(resolved_url)
    
    # 2. Extract from video tags
    video_tags = element.find_all('video')
    for video in video_tags:
        src = video.get('src')
        if src:
            resolved_url = resolve_url(src)
            media_links['videos'].append(resolved_url)
        
        # Check source tags within video
        source_tags = video.find_all('source')
        for source in source_tags:
            src = source.get('src')
            if src:
                resolved_url = resolve_url(src)
                media_links['videos'].append(resolved_url)
    
    # 3. Extract from audio tags
    audio_tags = element.find_all('audio')
    for audio in audio_tags:
        src = audio.get('src')
        if src:
            resolved_url = resolve_url(src)
            media_links['audio'].append(resolved_url)
        
        # Check source tags within audio
        source_tags = audio.find_all('source')
        for source in source_tags:
            src = source.get('src')
            if src:
                resolved_url = resolve_url(src)
                media_links['audio'].append(resolved_url)
    
    # 4. Extract from CSS background-image and mask-image
    all_elements = element.find_all(True)  # Find all elements
    for elem in all_elements:
        style = elem.get('style', '')
        if style:
            # Find background-image URLs
            bg_matches = re.findall(r'background-image:\s*url\(["\']?([^"\']+)["\']?\)', style)
            for match in bg_matches:
                resolved_url = resolve_url(match)
                if is_media_url(resolved_url, image_extensions):
                    media_links['images'].append(resolved_url)
            
            # Find mask-image URLs
            mask_matches = re.findall(r'mask-image:\s*url\(["\']?([^"\']+)["\']?\)', style)
            for match in mask_matches:
                resolved_url = resolve_url(match)
                if is_media_url(resolved_url, image_extensions):
                    media_links['images'].append(resolved_url)
    
    # 5. Extract from anchor tags linking to media files
    a_tags = element.find_all('a', href=True)
    for a in a_tags:
        href = a.get('href')
        if href:
            resolved_url = resolve_url(href)
            if is_media_url(resolved_url, image_extensions):
                media_links['images'].append(resolved_url)
            elif is_media_url(resolved_url, video_extensions):
                media_links['videos'].append(resolved_url)
            elif is_media_url(resolved_url, audio_extensions):
                media_links['audio'].append(resolved_url)
    
    # 6. Find URLs in text content and attributes
    all_text = element.get_text() + ' ' + str(element)
    url_pattern = r'https?://[^\s<>"\']+\.(?:' + '|'.join(ext.strip('.') for ext in image_extensions | video_extensions | audio_extensions) + r')'
    text_urls = re.findall(url_pattern, all_text, re.IGNORECASE)
    
    for url in text_urls:
        resolved_url = resolve_url(url)
        if is_media_url(resolved_url, image_extensions):
            media_links['images'].append(resolved_url)
        elif is_media_url(resolved_url, video_extensions):
            media_links['videos'].append(resolved_url)
        elif is_media_url(resolved_url, audio_extensions):
            media_links['audio'].append(resolved_url)
    
    # Remove duplicates while preserving order
    for key in media_links:
        media_links[key] = list(dict.fromkeys(media_links[key]))
    
    return media_links

def scrape_facebook_ads(html_content, keyword):
    """Scrape Facebook ads data using BeautifulSoup and the provided selector map"""
    try:
        print("\n🔍 Starting data extraction...")
        
        # Get the current page HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all ad wrapper elements
        ad_wrappers = soup.select(".xrvj5dj > div")
        print(f"📊 Found {len(ad_wrappers)} ad elements to scrape")
        
        scraped_data = []
        
        for i, ad_wrapper in enumerate(ad_wrappers, 1):
            print(f"Processing ad {i}/{len(ad_wrappers)}", end='\r')
            
            ad_data = {}
            
            # Extract library_id
            # Extract library ID and parse actual ID
            try:
                library_id_elem = ad_wrapper.select_one(".x1rg5ohu span.xw23nyj")
                library_id_text = library_id_elem.get_text(strip=True) if library_id_elem else ""
                
                # Extract actual numeric ID from "Library ID: 1665798290789134"
                library_id_match = re.search(r'Library ID:\s*(\d+)', library_id_text)
                ad_data['library_id'] = library_id_match.group(1) if library_id_match else library_id_text
            except Exception as e:
                ad_data['library_id'] = ""

            # Extract start date
            try:
                start_elem = ad_wrapper.select_one("div.x3nfvp2:nth-of-type(3) span")
                start_text = start_elem.get_text(strip=True) if start_elem else ""
                start_text_obj = extract_ad_times(start_text)
                ad_data = {**ad_data, **start_text_obj}
            except Exception as e:
                ad_data['start_at'] = ""
                
            # Extract category name
            try:
                category_elem = ad_wrapper.select_one(".xb2kyzz div._4ik4")
                ad_data['category_name'] = category_elem.get_text(strip=True) if category_elem else ""
            except Exception as e:
                ad_data['category_name'] = ""
            
            # Extract CTA
            try:
                cta_elem = ad_wrapper.select_one(".x1h6gzvc div.x8t9es0")
                ad_data['cta'] = cta_elem.get_text(strip=True) if cta_elem else ""
            except Exception as e:
                ad_data['cta'] = ""
            
            # Extract page name
            try:
                page_name_elem = ad_wrapper.select_one("span.x108nfp6.x1fvot60")
                ad_data['page_name'] = page_name_elem.get_text(strip=True) if page_name_elem else ""
            except Exception as e:
                ad_data['page_name'] = ""
            
            # Extract page image link (href attribute)
            try:
                page_img_elem = ad_wrapper.select_one("a")
                ad_data['page_image_link'] = page_img_elem.get('href', '') if page_img_elem else ""
            except Exception as e:
                ad_data['page_image_link'] = ""
            
            # Extract ad description
            try:
                # ._7jyg > div.x6ikm8r div._a25-
                desc_elem = ad_wrapper.select_one(".x8t9es0 div ._4ik4 span")
                ad_data['ad_description'] = desc_elem.get_text(strip=True) if desc_elem else ""
            except Exception as e:
                ad_data['ad_description'] = ""
            
            # Extract media and assets
            try:
                target_element = ad_wrapper.select_one("div._7jyg")
                
                if target_element:
                    media_data = extract_media_links(target_element)    
                    ad_data['media_links'] = media_data  # All media links
                else:
                    ad_data['media_links'] = []
                    print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx : ", ad_data['page_name'])
                    
            except Exception as e:
                ad_data['media_links'] = []

            # Extract page link
            try:
                page_link_elem = ad_wrapper.select_one("a")
                ad_data['page_link'] = page_link_elem.get_text(strip=True) if page_link_elem else ""
            except Exception as e:
                ad_data['page_link'] = ""
            
            # Add metadata
            ad_data['keyword'] = keyword
            ad_data['scraped_at'] = datetime.now().isoformat()
            
            scraped_data.append(ad_data)
        
        print(f"\n✓ Successfully scraped {len(scraped_data)} ads")
        
        return scraped_data
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        return []

def save_scraped_data(html_content, data, keyword):
    """Save scraped data to JSON and CSV files"""
    try:
        # Create output directory if it doesn't exist
        output_dir = "scraped_data"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Create safe filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_keyword = safe_keyword.replace(' ', '_')
        
        # Create output directory if it doesn't exist
        output_dir = "scraped_data"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        base_filename = f"facebook_ads_{safe_keyword}_{timestamp}"
        base_filepath = os.path.join(output_dir, base_filename)

        # save as HTML
        html_filepath = f"{base_filepath}.html"

        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✓ HTML file saved to: {html_filepath}")
        

        # Save as JSON
        json_filepath = f"{base_filepath}.json"
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ JSON data saved to: {json_filepath}")
        
        # Save as CSV
        if data:
            csv_filepath = f"{base_filepath}.csv"
            
            # Get all unique keys from all records
            all_keys = set()
            for record in data:
                all_keys.update(record.keys())
            
            fieldnames = sorted(list(all_keys))
            
            with open(csv_filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for record in data:
                    # Convert lists to strings for CSV
                    csv_record = {}
                    for key, value in record.items():
                        if isinstance(value, list):
                            csv_record[key] = '; '.join(str(v) for v in value)
                        else:
                            csv_record[key] = value
                    writer.writerow(csv_record)
            
            print(f"✓ CSV data saved to: {csv_filepath}")
            print(f"✓ Total records saved: {len(data)}")
        
    except Exception as e:
        print(f"Error saving scraped data: {e}")

# ==================== Main Entry Point ====================
def test_main():
    """Main entry point for the script"""
    try:
        keyword = "accessories"
        
        with SB(test=True, uc=True) as sb:
            # Navigate to Facebook Ads Library
            sb.open(f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=EG&is_targeted_country=false&media_type=all&publisher_platforms[0]=facebook&publisher_platforms[1]=instagram&q={keyword}&search_type=keyword_unordered")
            
            final_html = scroll_to_bottom_and_get_html(sb)
            scraped_data = scrape_facebook_ads(final_html, keyword)
            save_scraped_data(final_html, scraped_data, keyword)

    except Exception as e:
        print(f"An error occurred in main: {e}")
