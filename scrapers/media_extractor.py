# scrapers/media_extractor.py
"""Media extraction utilities"""

import re
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional
from bs4 import BeautifulSoup, Tag

class MediaExtractor:
    def __init__(self):
        from config import Config
        self.image_extensions = Config.IMAGE_EXTENSIONS
        self.video_extensions = Config.VIDEO_EXTENSIONS  
        self.audio_extensions = Config.AUDIO_EXTENSIONS
    
    def is_media_url(self, url, extensions):
        """Check if URL has media extension"""
        try:
            parsed = urlparse(url.lower())
            path = parsed.path
            return any(path.endswith(ext) for ext in extensions)
        except:
            return False
    
    def resolve_url(self, url, base_url = None):
        """Resolve relative URLs if base_url is provided"""
        if base_url and url and not url.startswith(('http://', 'https://', '//')):
            return urljoin(base_url, url)
        return url
    
    def extract_from_img_tags(self, element, base_url = None):
        """Extract image URLs from img tags"""
        images = []
        img_tags = element.find_all('img')
        
        for img in img_tags:
            # Regular src
            src = img.get('src')
            if src:
                images.append(self.resolve_url(src, base_url))
            
            # Lazy loading data-src
            data_src = img.get('data-src')
            if data_src:
                images.append(self.resolve_url(data_src, base_url))
        
        return images
    
    def extract_from_video_tags(self, element, base_url = None):
        """Extract video URLs from video tags"""
        videos = []
        video_tags = element.find_all('video')
        
        for video in video_tags:
            # Video src
            src = video.get('src')
            if src:
                videos.append(self.resolve_url(src, base_url))
            
            # Source tags within video
            source_tags = video.find_all('source')
            for source in source_tags:
                src = source.get('src')
                if src:
                    videos.append(self.resolve_url(src, base_url))
        
        return videos
    
    def extract_from_audio_tags(self, element, base_url = None):
        """Extract audio URLs from audio tags"""
        audio = []
        audio_tags = element.find_all('audio')
        
        for audio_tag in audio_tags:
            # Audio src
            src = audio_tag.get('src')
            if src:
                audio.append(self.resolve_url(src, base_url))
            
            # Source tags within audio
            source_tags = audio_tag.find_all('source')
            for source in source_tags:
                src = source.get('src')
                if src:
                    audio.append(self.resolve_url(src, base_url))
        
        return audio
    
    def extract_from_css(self, element, base_url = None):
        """Extract URLs from CSS background-image and mask-image"""
        images = []
        all_elements = element.find_all(True)
        
        for elem in all_elements:
            style = elem.get('style', '')
            if style:
                # Background-image URLs
                bg_matches = re.findall(r'background-image:\s*url\(["\']?([^"\']+)["\']?\)', style)
                for match in bg_matches:
                    resolved_url = self.resolve_url(match, base_url)
                    if self.is_media_url(resolved_url, self.image_extensions):
                        images.append(resolved_url)
                
                # Mask-image URLs
                mask_matches = re.findall(r'mask-image:\s*url\(["\']?([^"\']+)["\']?\)', style)
                for match in mask_matches:
                    resolved_url = self.resolve_url(match, base_url)
                    if self.is_media_url(resolved_url, self.image_extensions):
                        images.append(resolved_url)
        
        return images
    
    def extract_from_links(self, element, base_url = None):
        """Extract media URLs from anchor tags"""
        media_links = {'images': [], 'videos': [], 'audio': []}
        a_tags = element.find_all('a', href=True)
        
        for a in a_tags:
            href = a.get('href')
            if href:
                resolved_url = self.resolve_url(href, base_url)
                if self.is_media_url(resolved_url, self.image_extensions):
                    media_links['images'].append(resolved_url)
                elif self.is_media_url(resolved_url, self.video_extensions):
                    media_links['videos'].append(resolved_url)
                elif self.is_media_url(resolved_url, self.audio_extensions):
                    media_links['audio'].append(resolved_url)
        
        return media_links
    
    def extract_from_text(self, element, base_url = None):
        """Extract media URLs from text content and attributes"""
        media_links = {'images': [], 'videos': [], 'audio': []}
        
        all_text = element.get_text() + ' ' + str(element)
        all_extensions = self.image_extensions | self.video_extensions | self.audio_extensions
        url_pattern = r'https?://[^\s<>"\']+\.(?:' + '|'.join(ext.strip('.') for ext in all_extensions) + r')'
        text_urls = re.findall(url_pattern, all_text, re.IGNORECASE)
        
        for url in text_urls:
            resolved_url = self.resolve_url(url, base_url)
            if self.is_media_url(resolved_url, self.image_extensions):
                media_links['images'].append(resolved_url)
            elif self.is_media_url(resolved_url, self.video_extensions):
                media_links['videos'].append(resolved_url)
            elif self.is_media_url(resolved_url, self.audio_extensions):
                media_links['audio'].append(resolved_url)
        
        return media_links
    
    def extract_media_links(self, element: Optional[Tag], base_url = None):
        """Extract all media links from an element"""
        if not element:
            return {'images': [], 'videos': [], 'audio': []}
        
        media_links = {'images': [], 'videos': [], 'audio': []}
        
        # Extract from different sources
        media_links['images'].extend(self.extract_from_img_tags(element, base_url))
        media_links['videos'].extend(self.extract_from_video_tags(element, base_url))
        media_links['audio'].extend(self.extract_from_audio_tags(element, base_url))
        media_links['images'].extend(self.extract_from_css(element, base_url))
        
        # Extract from links
        link_media = self.extract_from_links(element, base_url)
        for key in media_links:
            media_links[key].extend(link_media[key])
        
        # Extract from text
        text_media = self.extract_from_text(element, base_url)
        for key in media_links:
            media_links[key].extend(text_media[key])
        
        # Remove duplicates while preserving order
        for key in media_links:
            media_links[key] = list(dict.fromkeys(media_links[key]))
        
        return media_links
