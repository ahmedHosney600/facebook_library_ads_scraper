# utils/date_utils.py
"""Date and time parsing utilities"""

import re
from datetime import datetime
from typing import Dict, Any

def parse_duration_to_seconds(duration_str):
    """Convert duration string like '3 hrs', '2 days', '1 hr 30 mins' to seconds"""
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

def format_duration_from_seconds(seconds):
    """Format seconds into human-readable duration"""
    duration_parts = []
    remaining_seconds = seconds
    
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
    
    return ' '.join(duration_parts) if duration_parts else "less than 1 min"

def extract_ad_times(start_text):
    """Extract and parse ad timing information"""
    ad_data = {}
    
    try:
        if not start_text:
            return {
                'start_date': '',
                'start_date_timestamp': '',
                'activity_duration': '',
                'activity_duration_timestamp': '',
                'start_at': start_text
            }
        
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
            
            try:
                duration_seconds = parse_duration_to_seconds(duration_str)
                ad_data['activity_duration_timestamp'] = duration_seconds
            except:
                ad_data['activity_duration_timestamp'] = ""
        else:
            # Calculate duration if we have start date
            if ad_data.get('start_date_timestamp'):
                try:
                    current_timestamp = int(datetime.now().timestamp())
                    calculated_duration = current_timestamp - ad_data['start_date_timestamp']
                    
                    formatted_duration = format_duration_from_seconds(calculated_duration)
                    ad_data['activity_duration'] = f"Calculated: {formatted_duration}"
                    ad_data['activity_duration_timestamp'] = calculated_duration
                except:
                    ad_data['activity_duration'] = ""
                    ad_data['activity_duration_timestamp'] = ""
            else:
                ad_data['activity_duration'] = ""
                ad_data['activity_duration_timestamp'] = ""
        
        ad_data['start_at'] = start_text
        return ad_data
        
    except Exception as e:
        return {
            'start_date': '',
            'start_date_timestamp': '',
            'activity_duration': '',
            'activity_duration_timestamp': '',
            'start_at': start_text
        }