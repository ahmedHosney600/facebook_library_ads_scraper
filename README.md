# Facebook Ads Scraper - Modular Version

A modular, maintainable Facebook Ads Library scraper built with Python.

## Project Structure

```
facebook_ads_scraper/
├── config.py                 # Configuration settings
├── utils/
│   ├── __init__.py
│   ├── file_utils.py         # File handling utilities
│   └── date_utils.py         # Date/time parsing utilities
├── scrapers/
│   ├── __init__.py
│   ├── browser_controller.py # Browser control and scrolling
│   ├── media_extractor.py    # Media extraction utilities
│   └── ad_scraper.py         # Main ad scraping logic
├── main.py                   # Main entry point
├── main_input.txt            # Default keywords file
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Features

- **Modular Design**: Separated concerns into logical modules
- **Configurable**: Easy to modify selectors and settings
- **Media Extraction**: Comprehensive media link extraction
- **Multiple Output Formats**: JSON, CSV, and HTML
- **Interactive Mode**: User-friendly keyword input
- **Infinite Scrolling**: Automated page scrolling with progress tracking
- **Error Handling**: Robust error handling throughout
- **Date Parsing**: Smart date and duration parsing

## Installation

1. Install requirements:

```bash
pip install -r requirements.txt
```

2. Create a keywords file (optional):

```
# main_input.txt
accessories
fashion
technology
# Lines starting with # are comments
```

## Usage

###

### Command Line

```bash
python main.py
```

## Configuration

Modify `config.py` to change:

- CSS selectors
- File paths
- Scroll timing
- Media file extensions
- Output settings

## Modules Overview

### `config.py`

Central configuration for all settings including selectors, file paths, and timing parameters.

### `utils/file_utils.py`

- File I/O operations
- Data saving (JSON, CSV, HTML)
- Keyword loading from files

### `utils/date_utils.py`

- Date parsing and formatting
- Duration calculations
- Timestamp conversions

### `scrapers/browser_controller.py`

- Browser automation
- Infinite scrolling logic
- Element counting
- Load more content detection

### `scrapers/media_extractor.py`

- Media URL extraction from various sources
- Image, video, and audio detection
- CSS background-image parsing
- Link resolution

### `scrapers/ad_scraper.py`

- Main ad data extraction
- HTML parsing with BeautifulSoup
- Ad element processing
- Data structure creation

### `main.py`

- Entry point and orchestration
- Interactive user interface
- Multi-keyword processing
- Error handling and reporting

## Output

The scraper generates three types of output files:

- `facebook_ads_[keyword]_[timestamp].html` - Raw HTML content
- `facebook_ads_[keyword]_[timestamp].json` - Structured JSON data
- `facebook_ads_[keyword]_[timestamp].csv` - CSV format for analysis

## Error Handling

- Graceful handling of missing elements
- Continuation on individual ad failures
- Comprehensive error logging
- Fallback mechanisms for data extraction

## Extensibility

The modular design makes it easy to:

- Add new data extraction fields
- Modify scraping behavior
- Change output formats
- Add new media types
- Integrate with other tools
