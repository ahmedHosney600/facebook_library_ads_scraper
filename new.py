# performance_improvements.py
"""
Performance & Efficiency Improvements for Facebook Ads Scraper
This file contains optimized versions of key components with performance enhancements
"""

import asyncio
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import deque
import json
import os
from datetime import datetime
import weakref
import gc

# ============================================================================
# 1. ASYNC/CONCURRENT PROCESSING IMPROVEMENTS
# ============================================================================

class AsyncDataProcessor:
    """Async data processing for I/O operations"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def save_data_async(self, data: Dict[str, Any], filepath: str) -> bool:
        """Async file writing"""
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                self.executor, 
                self._write_json_file, 
                data, 
                filepath
            )
            return True
        except Exception as e:
            print(f"Error saving {filepath}: {e}")
            return False
    
    def _write_json_file(self, data: Dict[str, Any], filepath: str):
        """Blocking JSON write operation"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    async def process_multiple_files(self, data_list: List[Dict], base_path: str):
        """Process multiple files concurrently"""
        tasks = []
        for i, data in enumerate(data_list):
            filepath = f"{base_path}_{i}.json"
            task = self.save_data_async(data, filepath)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful = sum(1 for r in results if r is True)
        print(f"Successfully saved {successful}/{len(data_list)} files")
        return results


class ConcurrentKeywordProcessor:
    """Process multiple keywords concurrently with rate limiting"""
    
    def __init__(self, max_concurrent: int = 3, delay_between_batches: float = 10.0):
        self.max_concurrent = max_concurrent
        self.delay_between_batches = delay_between_batches
        self.results = {}
        self.failed_keywords = []
    
    def process_keywords_batch(self, keywords: List[str], scraper_instance) -> Dict[str, Any]:
        """Process keywords in batches to avoid overwhelming the server"""
        all_results = {}
        
        # Split keywords into batches
        batches = [keywords[i:i + self.max_concurrent] 
                  for i in range(0, len(keywords), self.max_concurrent)]
        
        for batch_idx, batch in enumerate(batches):
            print(f"\n🚀 Processing batch {batch_idx + 1}/{len(batches)}: {batch}")
            
            # Process current batch concurrently
            batch_results = self._process_single_batch(batch, scraper_instance)
            all_results.update(batch_results)
            
            # Delay between batches (except for the last one)
            if batch_idx < len(batches) - 1:
                print(f"⏳ Waiting {self.delay_between_batches}s before next batch...")
                time.sleep(self.delay_between_batches)
        
        return all_results
    
    def _process_single_batch(self, keywords: List[str], scraper_instance) -> Dict[str, Any]:
        """Process a single batch of keywords concurrently"""
        batch_results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            # Submit all tasks
            future_to_keyword = {
                executor.submit(scraper_instance.scrape_keyword, keyword): keyword 
                for keyword in keywords
            }
            
            # Process completed tasks
            for future in as_completed(future_to_keyword):
                keyword = future_to_keyword[future]
                try:
                    result = future.result()
                    batch_results[keyword] = {
                        'success': result,
                        'timestamp': datetime.now().isoformat()
                    }
                    print(f"✅ Completed: {keyword}")
                except Exception as e:
                    print(f"❌ Failed: {keyword} - {e}")
                    batch_results[keyword] = {
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                    self.failed_keywords.append(keyword)
        
        return batch_results


class BatchAdProcessor:
    """Process ads in batches for better memory management"""
    
    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size
    
    def process_ads_in_batches(self, ad_elements: List, scraper_instance, keyword: str) -> List[Dict]:
        """Process ads in batches to reduce memory usage"""
        all_ads = []
        total_batches = (len(ad_elements) + self.batch_size - 1) // self.batch_size
        
        for batch_idx in range(0, len(ad_elements), self.batch_size):
            batch_num = (batch_idx // self.batch_size) + 1
            batch = ad_elements[batch_idx:batch_idx + self.batch_size]
            
            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} ads)")
            
            batch_results = []
            for ad_element in batch:
                try:
                    ad_data = scraper_instance.scrape_single_ad(ad_element, keyword)
                    batch_results.append(ad_data)
                except Exception as e:
                    print(f"Error processing ad: {e}")
                    continue
            
            all_ads.extend(batch_results)
            
            # Force garbage collection after each batch
            del batch_results
            gc.collect()
            
            # Small delay between batches
            time.sleep(0.1)
        
        return all_ads


# ============================================================================
# 2. MEMORY OPTIMIZATION IMPROVEMENTS
# ============================================================================

class StreamingJSONWriter:
    """Write JSON data incrementally to handle large datasets"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file_handle = None
        self.first_item = True
    
    def __enter__(self):
        self.file_handle = open(self.filepath, 'w', encoding='utf-8')
        self.file_handle.write('[\n')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file_handle:
            self.file_handle.write('\n]')
            self.file_handle.close()
    
    def write_item(self, item: Dict[str, Any]):
        """Write a single item to the JSON array"""
        if not self.first_item:
            self.file_handle.write(',\n')
        else:
            self.first_item = False
        
        json.dump(item, self.file_handle, ensure_ascii=False, indent=2)
        self.file_handle.flush()  # Ensure data is written immediately


class MemoryOptimizedHTMLProcessor:
    """Process HTML in chunks to reduce memory usage"""
    
    def __init__(self, chunk_size: int = 1000000):  # 1MB chunks
        self.chunk_size = chunk_size
    
    def process_html_in_chunks(self, html_content: str, processor_func) -> List[Any]:
        """Process large HTML content in smaller chunks"""
        results = []
        
        # Split HTML into logical chunks (by div elements)
        chunks = self._split_html_content(html_content)
        
        for i, chunk in enumerate(chunks):
            print(f"Processing HTML chunk {i+1}/{len(chunks)}")
            
            try:
                chunk_results = processor_func(chunk)
                results.extend(chunk_results)
            except Exception as e:
                print(f"Error processing chunk {i+1}: {e}")
                continue
            
            # Clean up processed chunk from memory
            del chunk
            
            if i % 5 == 0:  # Garbage collect every 5 chunks
                gc.collect()
        
        return results
    
    def _split_html_content(self, html_content: str) -> List[str]:
        """Split HTML content into logical chunks"""
        # Simple implementation - split by ad wrapper divs
        chunks = []
        current_chunk = ""
        
        lines = html_content.split('\n')
        for line in lines:
            current_chunk += line + '\n'
            
            # If chunk is getting large and we hit a natural break point
            if (len(current_chunk) > self.chunk_size and 
                'class="xrvj5dj"' in line):  # Ad wrapper class
                chunks.append(current_chunk)
                current_chunk = ""
        
        # Add remaining content
        if current_chunk.strip():
            chunks.append(current_chunk)
        
        return chunks


class MemoryMonitor:
    """Monitor and manage memory usage during scraping"""
    
    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_mb = max_memory_mb
        self.weak_refs = weakref.WeakSet()
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def check_memory_limit(self) -> bool:
        """Check if memory usage exceeds limit"""
        current_memory = self.get_memory_usage()
        if current_memory > self.max_memory_mb:
            print(f"⚠️  Memory usage ({current_memory:.1f}MB) exceeds limit ({self.max_memory_mb}MB)")
            return True
        return False
    
    def force_cleanup(self):
        """Force garbage collection and cleanup"""
        print("🧹 Performing memory cleanup...")
        
        # Clear weak references
        self.weak_refs.clear()
        
        # Force garbage collection
        collected = gc.collect()
        print(f"Collected {collected} objects")
        
        # Print new memory usage
        new_memory = self.get_memory_usage()
        print(f"Memory usage after cleanup: {new_memory:.1f}MB")


# ============================================================================
# 3. SMART SCROLLING OPTIMIZATION
# ============================================================================

@dataclass
class ScrollMetrics:
    """Track scrolling performance metrics"""
    scroll_attempts: int = 0
    successful_scrolls: int = 0
    average_load_time: float = 0.0
    elements_loaded: int = 0
    last_element_count: int = 0


class AdaptiveScrollController:
    """Smart scrolling with adaptive timing and performance monitoring"""
    
    def __init__(self, initial_wait_time: float = 2.0):
        self.base_wait_time = initial_wait_time
        self.current_wait_time = initial_wait_time
        self.metrics = ScrollMetrics()
        self.load_times = deque(maxlen=10)  # Keep last 10 load times
        self.performance_threshold = 0.8  # Minimum success rate
    
    def adaptive_scroll_and_wait(self, browser_controller) -> bool:
        """Perform adaptive scrolling with dynamic timing"""
        start_time = time.time()
        
        # Get initial element count
        initial_count = browser_controller.count_ad_elements()
        
        # Perform scroll
        browser_controller.sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # Wait with adaptive timing
        time.sleep(self.current_wait_time)
        
        # Check if new content loaded
        final_count = browser_controller.count_ad_elements()
        load_time = time.time() - start_time
        
        # Update metrics
        self._update_metrics(initial_count, final_count, load_time)
        
        # Adjust timing based on performance
        self._adjust_timing()
        
        return final_count > initial_count
    
    def _update_metrics(self, initial_count: int, final_count: int, load_time: float):
        """Update performance metrics"""
        self.metrics.scroll_attempts += 1
        
        if final_count > initial_count:
            self.metrics.successful_scrolls += 1
            self.metrics.elements_loaded += (final_count - initial_count)
        
        self.load_times.append(load_time)
        self.metrics.average_load_time = sum(self.load_times) / len(self.load_times)
        self.metrics.last_element_count = final_count
    
    def _adjust_timing(self):
        """Adjust scroll timing based on performance"""
        success_rate = (self.metrics.successful_scrolls / 
                       max(1, self.metrics.scroll_attempts))
        
        if success_rate < self.performance_threshold:
            # Poor performance - increase wait time
            self.current_wait_time = min(self.current_wait_time * 1.2, 8.0)
            print(f"📈 Increased wait time to {self.current_wait_time:.1f}s (success rate: {success_rate:.2f})")
        elif success_rate > 0.95 and self.current_wait_time > self.base_wait_time:
            # Excellent performance - try reducing wait time
            self.current_wait_time = max(self.current_wait_time * 0.9, self.base_wait_time)
            print(f"📉 Reduced wait time to {self.current_wait_time:.1f}s (success rate: {success_rate:.2f})")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report"""
        success_rate = (self.metrics.successful_scrolls / 
                       max(1, self.metrics.scroll_attempts))
        
        return {
            'total_scrolls': self.metrics.scroll_attempts,
            'successful_scrolls': self.metrics.successful_scrolls,
            'success_rate': success_rate,
            'average_load_time': self.metrics.average_load_time,
            'current_wait_time': self.current_wait_time,
            'total_elements_loaded': self.metrics.elements_loaded,
            'last_element_count': self.metrics.last_element_count
        }


class ViewportBasedScroller:
    """Scroll by viewport height for more natural behavior"""
    
    def __init__(self, viewport_multiplier: float = 0.8):
        self.viewport_multiplier = viewport_multiplier
    
    def scroll_by_viewport(self, browser_controller) -> bool:
        """Scroll by viewport height"""
        try:
            # Get viewport height
            viewport_height = browser_controller.sb.execute_script(
                "return window.innerHeight"
            )
            
            # Calculate scroll distance
            scroll_distance = int(viewport_height * self.viewport_multiplier)
            
            # Perform smooth scroll
            browser_controller.sb.execute_script(f"""
                window.scrollBy({{
                    top: {scroll_distance},
                    behavior: 'smooth'
                }});
            """)
            
            return True
            
        except Exception as e:
            print(f"Error in viewport scrolling: {e}")
            return False
    
    def check_viewport_position(self, browser_controller) -> Dict[str, int]:
        """Get current viewport position information"""
        try:
            position_info = browser_controller.sb.execute_script("""
                return {
                    scrollTop: window.pageYOffset,
                    scrollHeight: document.body.scrollHeight,
                    viewportHeight: window.innerHeight,
                    scrollPercentage: Math.round((window.pageYOffset / 
                        (document.body.scrollHeight - window.innerHeight)) * 100)
                };
            """)
            return position_info
        except:
            return {}


class ElementVisibilityDetector:
    """Detect when new elements become visible"""
    
    def __init__(self):
        self.last_visible_elements = set()
        self.element_selector = ".xrvj5dj > div"  # Ad wrapper selector
    
    def get_visible_elements(self, browser_controller) -> set:
        """Get currently visible element identifiers"""
        try:
            visible_elements = browser_controller.sb.execute_script(f"""
                const elements = document.querySelectorAll('{self.element_selector}');
                const visible = new Set();
                
                elements.forEach((el, index) => {{
                    const rect = el.getBoundingClientRect();
                    const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
                    if (isVisible) {{
                        // Use a unique identifier (position + partial content)
                        const id = index + '_' + (el.textContent || '').substring(0, 50);
                        visible.add(id);
                    }}
                }});
                
                return Array.from(visible);
            """)
            
            return set(visible_elements)
            
        except Exception as e:
            print(f"Error detecting visible elements: {e}")
            return set()
    
    def check_new_content_loaded(self, browser_controller) -> bool:
        """Check if new content has become visible"""
        current_visible = self.get_visible_elements(browser_controller)
        
        # Check if there are new elements
        new_elements = current_visible - self.last_visible_elements
        has_new_content = len(new_elements) > 0
        
        # Update tracking
        self.last_visible_elements = current_visible
        
        if has_new_content:
            print(f"🆕 Detected {len(new_elements)} new visible elements")
        
        return has_new_content


# ============================================================================
# ENHANCED BROWSER CONTROLLER WITH PERFORMANCE OPTIMIZATIONS
# ============================================================================

class OptimizedBrowserController:
    """Enhanced browser controller with all performance optimizations"""
    
    def __init__(self, sb, config):
        self.sb = sb
        self.config = config
        self.adaptive_scroller = AdaptiveScrollController()
        self.viewport_scroller = ViewportBasedScroller()
        self.visibility_detector = ElementVisibilityDetector()
        self.memory_monitor = MemoryMonitor()
    
    def optimized_scroll_to_bottom(self) -> str:
        """Optimized infinite scrolling with all performance enhancements"""
        print("🚀 Starting optimized infinite scroll...")
        
        scroll_count = 0
        stall_count = 0
        stop_scrolling = False
        
        # Setup stop mechanism
        def check_for_stop():
            nonlocal stop_scrolling
            try:
                input("Press Enter to stop scrolling...\n")
                stop_scrolling = True
            except:
                pass
        
        stop_thread = threading.Thread(target=check_for_stop, daemon=True)
        stop_thread.start()
        
        try:
            while not stop_scrolling:
                scroll_count += 1
                
                # Check memory usage
                if self.memory_monitor.check_memory_limit():
                    self.memory_monitor.force_cleanup()
                
                # Use adaptive scrolling
                content_loaded = self.adaptive_scroller.adaptive_scroll_and_wait(self)
                
                # Alternative: viewport-based scrolling
                if not content_loaded:
                    self.viewport_scroller.scroll_by_viewport(self)
                    time.sleep(1)
                    content_loaded = self.visibility_detector.check_new_content_loaded(self)
                
                # Update stall counter
                if content_loaded:
                    stall_count = 0
                else:
                    stall_count += 1
                
                # Print progress
                if scroll_count % 10 == 0:
                    report = self.adaptive_scroller.get_performance_report()
                    print(f"📊 Scroll #{scroll_count} | Elements: {report['last_element_count']} | "
                          f"Success Rate: {report['success_rate']:.2f} | "
                          f"Memory: {self.memory_monitor.get_memory_usage():.1f}MB")
                
                # Continue scrolling even with stalls (for infinite scroll)
                if stall_count >= self.config.MAX_STALLS:
                    print("Max stalls reached, but continuing...")
                    stall_count = 0
                    time.sleep(self.config.LOAD_WAIT_TIME)
        
        except KeyboardInterrupt:
            print("\n⏹️  Scrolling stopped by user")
        except Exception as e:
            print(f"❌ Error during optimized scrolling: {e}")
        
        # Final performance report
        final_report = self.adaptive_scroller.get_performance_report()
        print("\n📈 FINAL PERFORMANCE REPORT:")
        for key, value in final_report.items():
            print(f"  {key}: {value}")
        
        return self.sb.get_page_source()
    
    def count_ad_elements(self) -> int:
        """Count ad elements (required by adaptive scroller)"""
        try:
            elements = self.sb.find_elements(self.config.AD_WRAPPER_SELECTOR)
            return len(elements)
        except Exception:
            return 0


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

class PerformanceOptimizedScraper:
    """Example implementation using all performance improvements"""
    
    def __init__(self):
        self.async_processor = AsyncDataProcessor()
        self.concurrent_processor = ConcurrentKeywordProcessor()
        self.batch_processor = BatchAdProcessor()
        self.memory_monitor = MemoryMonitor()
    
    async def scrape_with_performance_optimizations(self, keywords: List[str]):
        """Main scraping function with all optimizations"""
        
        # Process keywords concurrently
        results = self.concurrent_processor.process_keywords_batch(
            keywords, self
        )
        
        # Save results asynchronously
        save_tasks = []
        for keyword, result in results.items():
            if result['success']:
                filepath = f"output_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                task = self.async_processor.save_data_async(result, filepath)
                save_tasks.append(task)
        
        # Wait for all saves to complete
        await asyncio.gather(*save_tasks)
        
        print("✅ All optimized processing complete!")
        return results


# Example usage:
"""
# To use the optimized scraper:

async def main():
    scraper = PerformanceOptimizedScraper()
    keywords = ["technology", "fashion", "automotive"]
    
    results = await scraper.scrape_with_performance_optimizations(keywords)
    print(f"Processed {len(results)} keywords")

# Run with:
# asyncio.run(main())
"""