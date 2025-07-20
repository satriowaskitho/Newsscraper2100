# Changelog

All notable changes to news-watch will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.5] - 2025-01-15

### Added
- **Python API Module**: Complete synchronous API for programmatic access
  - `scrape()` - Returns list of articles as dictionaries
  - `scrape_to_dataframe()` - Returns pandas DataFrame
  - `scrape_to_file()` - Saves to CSV or Excel files
  - `list_scrapers()` - Lists available news sources
  - `quick_scrape()` - Convenient recent news collection
  - `scrape_ihsg_news()` - Specialized IHSG/stock market news
- **Antaranews scraper** - Official government news agency support
- **Enhanced error handling** with custom exceptions (`ValidationError`, `NewsWatchError`)
- **Improved timeout handling** with configurable timeout parameters
- **Better date parsing** to handle None values and edge cases

### Changed
- **Metrotvnews scraper improvements** - Updated base URL and search format
- **Concurrency optimization** - Reduced from 12 to 10 concurrent connections for better stability
- **Producer-consumer architecture** - Async queue-based article collection for better memory management
- **Input validation** - Stricter validation for dates, keywords, and scraper selection

### Fixed
- **Okezone scraper reliability** - Fixed parsing errors and improved article extraction
- **Date extraction robustness** - Better handling of various date formats across sources
- **Linux platform stability** - Automatic exclusion of problematic scrapers on Linux

### Dependencies
- **Updated aiohttp** from 3.11.18 to 3.12.14 for security and performance
- **Updated requests** from 2.32.3 to 2.32.4 for security fixes

### Documentation
- **Complete API documentation** with usage examples
- **Jupyter notebook examples** for data analysis workflows
- **Enhanced README** with comprehensive installation and usage guides

## [0.2.4] - 2024-12-15

### Added
- **Multi-platform support** with automatic scraper selection based on OS
- **Verbose logging mode** for debugging and monitoring scrape progress
- **Excel output format** in addition to CSV
- **Keyword filtering** with comma-separated multiple keyword support

### Changed
- **Async architecture** - Complete rewrite using aiohttp for better performance
- **Error recovery** - Improved retry logic with exponential backoff
- **Memory efficiency** - Streaming output to reduce memory usage

### Fixed
- **Date filtering accuracy** - More precise date range filtering
- **Content extraction** - Better handling of article content across different sites

## [0.2.3] - 2024-11-20

### Added
- **Playwright integration** for JavaScript-heavy news sites
- **Content quality filtering** - Minimum content length requirements
- **Source diversity** - Support for 14+ Indonesian news websites

### Changed
- **CLI interface** - More intuitive command-line arguments
- **Output formatting** - Standardized article structure across all scrapers

### Fixed
- **Rate limiting** - Better handling of website rate limits
- **Character encoding** - Improved Unicode handling for Indonesian text

## [0.2.2] - 2024-10-15

### Added
- **Detik.com scraper** - Major Indonesian news portal support
- **Kompas.com scraper** - Leading newspaper website
- **Tempo.co scraper** - Weekly magazine website
- **Date range filtering** - Precise date-based article filtering

### Changed
- **Base scraper architecture** - Unified interface for all news sources
- **Error handling** - More graceful failure handling per scraper

## [0.2.1] - 2024-09-10

### Added
- **CNBC Indonesia scraper** - Financial news coverage
- **Kontan scraper** - Business and economic news
- **Bisnis.com scraper** - Comprehensive business news

### Fixed
- **URL parsing** - Better handling of relative and absolute URLs
- **Content extraction** - Improved article text extraction algorithms

## [0.2.0] - 2024-08-05

### Added
- **Async scraping engine** - Complete rewrite for better performance
- **Multiple news sources** - Support for major Indonesian news websites
- **CLI interface** - Command-line tool for easy usage
- **CSV output** - Structured data export functionality

### Changed
- **Breaking change**: New CLI syntax and Python API
- **Performance**: 10x faster scraping with async/await
- **Architecture**: Modular scraper design for easy extension

## [0.1.5] - 2024-07-01

### Added
- **Basic scraping functionality** for select Indonesian news sites
- **Keyword search** - Simple keyword-based article filtering
- **JSON output** - Basic structured data export

### Fixed
- **HTTP handling** - Basic error handling for network requests
- **Text encoding** - Indonesian character support

## [0.1.0] - 2024-06-01

### Added
- **Initial release** - Basic news scraping prototype
- **Single source support** - Limited to one news website
- **Proof of concept** - Basic article extraction functionality

---

## Migration Guide

### From v0.2.4 to v0.2.5

The new Python API provides much easier programmatic access:

**Old CLI-only approach:**
```bash
newswatch --keywords "ekonomi,politik" --start_date 2025-01-01 --output_format xlsx
```

**New API approach:**
```python
import newswatch as nw
df = nw.scrape_to_dataframe(keywords="ekonomi,politik", start_date="2025-01-01")
```

### From v0.1.x to v0.2.x

Version 0.2.0 introduced breaking changes:

- **CLI syntax changed** - Use `newswatch` instead of previous commands
- **Output format** - New standardized article structure
- **Dependencies** - Requires Python 3.10+ and async libraries

## Support

For bug reports and feature requests, please visit our [GitHub Issues](https://github.com/okkymabruri/news-watch/issues).

For general questions and discussion, see our [documentation](https://github.com/okkymabruri/news-watch/tree/main/docs).