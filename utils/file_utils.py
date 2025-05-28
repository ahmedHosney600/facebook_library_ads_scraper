# utils/file_utils.py
"""File handling utilities"""

import os
import json
import csv
from datetime import datetime
from typing import List, Dict, Any

def load_keywords_from_file(filename):
    """Load keywords from a text file"""
    if not os.path.exists(filename):
        print(f"Keywords file {filename} not found")
        return []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f.readlines() 
                       if line.strip() and not line.strip().startswith('#')]
        print(f"Loaded {len(keywords)} keywords from {filename}")
        return keywords
    except Exception as e:
        print(f"Error loading keywords from {filename}: {e}")
        return []

def get_user_input_for_keyword():
    """Get keywords from user input or file"""
    from config import Config
    
    print(f"Default keywords file: {Config.DEFAULT_KEYWORDS_FILE}")
    user_input = input("Enter keyword to search(or press Enter for default): ").strip()
    
    if not os.path.isfile(user_input):
        return [user_input] if user_input else []
    
    keywords_file = user_input if user_input else Config.DEFAULT_KEYWORDS_FILE
    return load_keywords_from_file(keywords_file) if os.path.exists(keywords_file) else []

def create_safe_filename(keyword):
    """Create a safe filename from keyword"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_keyword = safe_keyword.replace(' ', '_')
    return f"facebook_ads_{safe_keyword}_{timestamp}"

def save_scraped_data(html_content, data, keyword):
    """Save scraped data to JSON, CSV, and HTML files"""
    from config import Config
    
    try:
        # Create output directory
        if not os.path.exists(Config.OUTPUT_DIR):
            os.makedirs(Config.OUTPUT_DIR)
        
        base_filename = create_safe_filename(keyword)
        base_filepath = os.path.join(Config.OUTPUT_DIR, base_filename)
        
        # Save HTML
        html_filepath = f"{base_filepath}.html"
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✓ HTML file saved to: {html_filepath}")
        
        # Save JSON
        json_filepath = f"{base_filepath}.json"
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✓ JSON data saved to: {json_filepath}")
        
        # Save CSV
        if data:
            csv_filepath = f"{base_filepath}.csv"
            save_as_csv(data, csv_filepath)
            print(f"✓ CSV data saved to: {csv_filepath}")
            print(f"✓ Total records saved: {len(data)}")
            
    except Exception as e:
        print(f"Error saving scraped data: {e}")

def save_as_csv(data, filepath):
    """Save data as CSV file"""
    # Get all unique keys
    all_keys = set()
    for record in data:
        all_keys.update(record.keys())
    
    fieldnames = sorted(list(all_keys))
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in data:
            # Convert complex types to strings for CSV
            csv_record = {}
            for key, value in record.items():
                if isinstance(value, (list, dict)):
                    csv_record[key] = json.dumps(value) if isinstance(value, dict) else '; '.join(str(v) for v in value)
                else:
                    csv_record[key] = value
            writer.writerow(csv_record)
