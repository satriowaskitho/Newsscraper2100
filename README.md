# news-watch

news-watch is a Python package that allows you to scrape news articles from various Indonesian news websites based on specific keywords and date ranges.


## Installation

You can install newswatch via pip:

```bash
pip install news-watch
```

## Usage

To run the scraper from the command line:

```bash
newswatch -k <keywords> -sd <start_date> -s [<scrapers>] [-v]
```
Command-Line Arguments

`--keywords`, `-k`: Required. A comma-separated list of keywords to scrape (e.g., -k "ojk,bank,npl").

`--start_date`, `-sd`: Required. The start date for scraping in YYYY-MM-DD format (e.g., -sd 2023-01-01).

`--scrapers`, `-s`: Optional. A comma-separated list of scrapers to use (e.g., -s "kompas,viva"). If not provided, all scrapers will be used by default.

`--verbose`, `-v`: Optional. Increase verbosity level (e.g., `-v`, `-vv`, `-vvv`).



### Examples

Scrape articles related to "ihsg" from October 28, 2024:

```bash
newswatch -k ihsg -sd 2024-10-28
```

Scrape articles for multiple keywords and increase verbosity:

```bash
newswatch -k "ihsg,bank,keuangan" -sd 2024-10-28 -vv
```

## Output

The scraped articles are saved as a CSV file in the current working directory with the format `news-watch-YYYYMMDD_HH.csv`.

The CSV file contains the following fields:

- `title`
- `publish_date`
- `author`
- `content`
- `keyword`
- `category`
- `source`
- `link`

## Supported Websites

- Bisnis Indonesia
- CNBC Indonesia
- Detik
- Kompas
- Kontan

    > Note: Running this on the cloud currently leads to errors due to Cloudflare restrictions.
    >
    > Limitation: The scraper can process a maximum of 50 pages.

- Viva

## Contributing

Contributions are welcome! If you'd like to add support for more websites or improve the existing code, please open an issue or submit a pull request.

### Running Tests

To run the test suite:

```bash
pytest tests/
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
