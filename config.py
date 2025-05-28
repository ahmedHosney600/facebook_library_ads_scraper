# config.py
"""Configuration settings for the Facebook Ads scraper"""

import os

class Config:
    # File paths
    DEFAULT_KEYWORDS_FILE = "main_input.txt"
    OUTPUT_DIR = "scraped_data"
    
    # Scraping settings
    MAX_STALLS = 3
    SCROLL_WAIT_TIME = 2
    LOAD_WAIT_TIME = 5
    
    # Selectors
    AD_WRAPPER_SELECTOR = ".xrvj5dj > div"
    LIBRARY_ID_SELECTOR = ".x1rg5ohu span.xw23nyj"
    START_DATE_SELECTOR = "div.x3nfvp2:nth-of-type(3) span"
    CATEGORY_SELECTOR = ".xb2kyzz div._4ik4"
    CTA_SELECTOR = ".x1h6gzvc div.x8t9es0"
    PAGE_NAME_SELECTOR = "span.x108nfp6.x1fvot60"
    PAGE_IMAGE_LINK_SELECTOR = "a"
    AD_DESCRIPTION_SELECTOR = ".x8t9es0 div ._4ik4 span"
    MEDIA_CONTAINER_SELECTOR = "div._7jyg"
    
    # Media file extensions
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico', '.tiff'}
    VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v'}
    AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac', '.wma'}

