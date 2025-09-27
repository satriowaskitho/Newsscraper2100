"""
Improved error handling for the news scraper application
author: Okky Mabruri <okkymbrur@gmail.com>
maintainer: Okky Mabruri <okkymbrur@gmail.com>
"""

import asyncio
import csv
import logging
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import signal
import sys

from .scrapers.antaranews import AntaranewsScraper
# from .scrapers.batampos import BatamposScraper
from .scrapers.bisnis import BisnisScraper
from .scrapers.bloombergtechnoz import BloombergTechnozScraper
from .scrapers.cnbcindonesia import CNBCScraper
from .scrapers.detik import DetikScraper
from .scrapers.jawapos import JawaposScraper
from .scrapers.katadata import KatadataScraper
from .scrapers.kompas import KompasScraper
from .scrapers.kontan import KontanScraper
from .scrapers.kepriantaranews import KepriAntaranewsScraper
from .scrapers.mediaindonesia import MediaIndonesiaScraper
from .scrapers.metrotvnews import MetrotvnewsScraper
from .scrapers.okezone import OkezoneScraper
from .scrapers.tempo import TempoScraper
from .scrapers.viva import VivaScraper

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# Global shutdown event for graceful cleanup
shutdown_event = asyncio.Event()


class ScrapingError(Exception):
    """Custom exception for scraping-related errors"""
    pass


class FileWriteError(Exception):
    """Custom exception for file writing errors"""
    pass


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def write_csv(queue: asyncio.Queue, keywords: str, filename: Optional[str] = None) -> bool:
    """
    Write scraped data to CSV file with improved error handling
    Returns True if successful, False otherwise
    """
    fieldnames = [
        "title", "publish_date", "author", "content", 
        "keyword", "category", "source", "link"
    ]

    current_time = datetime.now().strftime("%Y%m%d_%H")
    keywords_list = keywords.split(",")
    keywords_short = ".".join(keywords_list[:2]) + ("..." if len(keywords_list) > 2 else "")
    
    if not filename:
        # Create output directory if it doesn't exist
        output_dir = Path.cwd() / "output"
        output_dir.mkdir(exist_ok=True)
        filename = output_dir / f"news-watch-{keywords_short}-{current_time}.csv"

    items_written = 0
    csvfile = None
    csv_writer = None

    try:
        csvfile = open(filename, mode="w", newline="", encoding="utf-8")
        csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        csv_writer.writeheader()
        logger.info(f"Started writing CSV to {filename}")

        while not shutdown_event.is_set():
            try:
                # Use shorter timeout to check shutdown event more frequently
                item = await asyncio.wait_for(queue.get(), timeout=5.0)
                
                if item is None:  # Sentinel value to stop
                    logger.info("Received stop signal for CSV writer")
                    break

                # Format datetime objects as strings
                if isinstance(item.get("publish_date"), datetime):
                    item["publish_date"] = item["publish_date"].strftime("%Y-%m-%d %H:%M:%S")
                
                csv_writer.writerow(item)
                csvfile.flush()
                items_written += 1
                
                if items_written % 10 == 0:  # Log progress every 10 items
                    logger.debug(f"Written {items_written} items to CSV")

            except asyncio.TimeoutError:
                # Check if we should continue waiting
                continue
            except asyncio.CancelledError:
                logger.info("CSV writer task was cancelled")
                break
            except Exception as e:
                logger.error(f"Error processing item for CSV: {e}")
                continue

        logger.info(f"CSV writing completed. {items_written} items written to {filename}")
        return True

    except Exception as e:
        logger.error(f"Critical error in CSV writer: {e}")
        raise FileWriteError(f"Failed to write CSV file: {e}")
    
    finally:
        if csvfile:
            try:
                csvfile.close()
                logger.info("CSV file closed successfully")
            except Exception as e:
                logger.error(f"Error closing CSV file: {e}")


async def write_xlsx(queue: asyncio.Queue, keywords: str, filename: Optional[str] = None) -> bool:
    """
    Write scraped data to XLSX file with improved error handling
    Returns True if successful, False otherwise
    """
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas not installed, cannot write XLSX files")
        raise FileWriteError("pandas is required for XLSX output")

    fieldnames = [
        "title", "publish_date", "author", "content",
        "keyword", "category", "source", "link"
    ]
    
    current_time = datetime.now().strftime("%Y%m%d_%H")
    keywords_list = keywords.split(",")
    keywords_short = ".".join(keywords_list[:2]) + ("..." if len(keywords_list) > 2 else "")
    
    if not filename:
        # Create output directory if it doesn't exist
        output_dir = Path.cwd() / "output"
        output_dir.mkdir(exist_ok=True)
        filename = output_dir / f"news-watch-{keywords_short}-{current_time}.xlsx"

    items = []
    items_collected = 0

    try:
        logger.info(f"Started collecting data for XLSX file: {filename}")

        while not shutdown_event.is_set():
            try:
                # Use shorter timeout to check shutdown event more frequently
                item = await asyncio.wait_for(queue.get(), timeout=5.0)
                
                if item is None:  # Sentinel value to stop
                    logger.info("Received stop signal for XLSX writer")
                    break

                # Format datetime objects as strings
                if isinstance(item.get("publish_date"), datetime):
                    item["publish_date"] = item["publish_date"].strftime("%Y-%m-%d %H:%M:%S")
                
                items.append(item)
                items_collected += 1
                
                if items_collected % 10 == 0:  # Log progress every 10 items
                    logger.debug(f"Collected {items_collected} items for XLSX")

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                logger.info("XLSX writer task was cancelled")
                break
            except Exception as e:
                logger.error(f"Error processing item for XLSX: {e}")
                continue

        # Write to file
        if items:
            try:
                df = pd.DataFrame(items, columns=fieldnames)
                df.to_excel(filename, index=False)
                logger.info(f"XLSX writing completed. {len(items)} items written to {filename}")
                return True
            except Exception as e:
                logger.error(f"Error writing DataFrame to XLSX: {e}")
                raise FileWriteError(f"Failed to write XLSX file: {e}")
        else:
            logger.warning("No items collected for XLSX file")
            return False

    except Exception as e:
        logger.error(f"Critical error in XLSX writer: {e}")
        raise FileWriteError(f"Failed to write XLSX file: {e}")


def get_available_scrapers():
    """Get list of available scrapers based on platform"""
    scraper_classes = {
        "antaranews": {"class": AntaranewsScraper, "params": {"concurrency": 7}},
        # "batampos": {"class": BatamposScraper, "params": {"concurrency": 8}},
        "bisnis": {"class": BisnisScraper, "params": {"concurrency": 5}},
        "bloombergtechnoz": {"class": BloombergTechnozScraper, "params": {}},
        "cnbcindonesia": {"class": CNBCScraper, "params": {"concurrency": 5}},
        "detik": {"class": DetikScraper, "params": {"concurrency": 5}},
        "kompas": {"class": KompasScraper, "params": {"concurrency": 7}},
        "kepriantaranews": {"class": KepriAntaranewsScraper, "params": {"concurrency": 7}},
        "metrotvnews": {"class": MetrotvnewsScraper, "params": {"concurrency": 2}},
        "okezone": {"class": OkezoneScraper, "params": {"concurrency": 7}},
        "tempo": {"class": TempoScraper, "params": {"concurrency": 1}},
        "viva": {"class": VivaScraper, "params": {"concurrency": 7}},
        "mediaindonesia": {"class": MediaIndonesiaScraper, "params": {}},
    }

    linux_excluded_scrapers = {
        "katadata": {"class": KatadataScraper, "params": {}},
        "jawapos": {"class": JawaposScraper, "params": {"concurrency": 5}},
        "kontan": {"class": KontanScraper, "params": {}},
    }

    if platform.system().lower() != "linux":
        scraper_classes.update(linux_excluded_scrapers)

    return scraper_classes, linux_excluded_scrapers


async def cleanup_tasks(tasks: List[asyncio.Task], timeout: float = 10.0):
    """Gracefully cleanup tasks with timeout"""
    if not tasks:
        return

    logger.info(f"Cleaning up {len(tasks)} tasks...")
    
    # Cancel all tasks
    for task in tasks:
        if not task.done():
            task.cancel()
    
    # Wait for tasks to complete or timeout
    try:
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)
        logger.info("All tasks cleaned up successfully")
    except asyncio.TimeoutError:
        logger.warning(f"Some tasks didn't complete within {timeout}s timeout")
    except Exception as e:
        logger.error(f"Error during task cleanup: {e}")


async def run_scrapers(scrapers: List, queue: asyncio.Queue, timeout: float = 300.0) -> bool:
    """
    Run scrapers with proper error handling and timeout
    Returns True if at least one scraper completed successfully
    """
    if not scrapers:
        logger.error("No scrapers provided")
        return False

    scraper_tasks = []
    successful_scrapers = 0

    try:
        # Create tasks for all scrapers
        for scraper in scrapers:
            try:
                task = asyncio.create_task(scraper.scrape())
                scraper_tasks.append(task)
                logger.info(f"Started scraper: {scraper.__class__.__name__}")
            except Exception as e:
                logger.error(f"Failed to start scraper {scraper.__class__.__name__}: {e}")

        if not scraper_tasks:
            logger.error("No scraper tasks could be started")
            return False

        # Run scrapers with timeout and handle results
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*scraper_tasks, return_exceptions=True), 
                timeout=timeout
            )
            
            # Check results
            for i, result in enumerate(results):
                scraper_name = scrapers[i].__class__.__name__
                if isinstance(result, Exception):
                    logger.error(f"Scraper {scraper_name} failed: {result}")
                else:
                    logger.info(f"Scraper {scraper_name} completed successfully")
                    successful_scrapers += 1

        except asyncio.TimeoutError:
            logger.warning(f"Scraping timed out after {timeout}s")
            await cleanup_tasks(scraper_tasks, timeout=30.0)

    except Exception as e:
        logger.error(f"Critical error during scraping: {e}")
        await cleanup_tasks(scraper_tasks, timeout=30.0)
    
    logger.info(f"Scraping completed. {successful_scrapers}/{len(scrapers)} scrapers successful")
    return successful_scrapers > 0


async def main(args):
    """Main function with comprehensive error handling"""
    setup_signal_handlers()
    
    try:
        # Validate input arguments
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError as e:
            logger.error(f"Invalid date format: {e}")
            return 1

        keywords = args.keywords
        selected_scrapers = args.scrapers
        
        if not keywords or not keywords.strip():
            logger.error("Keywords cannot be empty")
            return 1

        # Initialize queue and writer task
        queue_ = asyncio.Queue()
        writer_task = None

        try:
            output_format = getattr(args, "output_format", "xlsx").lower()
            
            if output_format == "xlsx":
                writer_task = asyncio.create_task(write_xlsx(queue_, args.keywords))
            else:
                writer_task = asyncio.create_task(write_csv(queue_, args.keywords))
            
            logger.info(f"Started {output_format.upper()} writer task")

        except Exception as e:
            logger.error(f"Failed to start writer task: {e}")
            return 1

        # Setup scrapers
        try:
            scraper_classes, linux_excluded_scrapers = get_available_scrapers()
            
            force_all_scrapers = selected_scrapers.lower() == "all"
            
            if force_all_scrapers and platform.system().lower() == "linux":
                scraper_classes.update(linux_excluded_scrapers)
                logger.warning(
                    f"Forcing all scrapers on Linux - may cause errors: {', '.join(linux_excluded_scrapers.keys())}"
                )

            if selected_scrapers.lower() in ["all", "auto"]:
                scrapers_to_run = list(scraper_classes.keys())
            else:
                scrapers_to_run = [name.strip().lower() for name in selected_scrapers.split(",")]

            # Initialize scrapers
            scrapers = []
            for scraper_name in scrapers_to_run:
                scraper_info = scraper_classes.get(scraper_name)
                if scraper_info:
                    try:
                        scraper_class = scraper_info["class"]
                        scraper_params = scraper_info["params"]
                        scraper_instance = scraper_class(
                            keywords, start_date=start_date, queue_=queue_, **scraper_params
                        )
                        scrapers.append(scraper_instance)
                        logger.info(f"Initialized scraper: {scraper_name}")
                    except Exception as e:
                        logger.error(f"Failed to initialize scraper '{scraper_name}': {e}")
                else:
                    logger.warning(f"Scraper '{scraper_name}' is not recognized")

            if not scrapers:
                logger.error("No valid scrapers initialized")
                raise ScrapingError("No valid scrapers available")

        except Exception as e:
            logger.error(f"Error setting up scrapers: {e}")
            if writer_task:
                writer_task.cancel()
            return 1

        # Run scrapers
        try:
            scraping_successful = await run_scrapers(scrapers, queue_, timeout=300.0)
            
            if not scraping_successful:
                logger.warning("No scrapers completed successfully")
            
        except Exception as e:
            logger.error(f"Error during scraping execution: {e}")
        
        finally:
            # Signal writer to stop
            try:
                await queue_.put(None)
                logger.info("Sent stop signal to writer")
            except Exception as e:
                logger.error(f"Error sending stop signal: {e}")

        # Wait for writer to finish
        if writer_task:
            try:
                await asyncio.wait_for(writer_task, timeout=60.0)
                logger.info("Writer task completed successfully")
            except asyncio.TimeoutError:
                logger.warning("Writer task timed out")
                writer_task.cancel()
                try:
                    await writer_task
                except asyncio.CancelledError:
                    logger.info("Writer task cancelled successfully")
            except Exception as e:
                logger.error(f"Error in writer task: {e}")

        logger.info("Scraping process completed")
        return 0

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        return 1
    finally:
        # Final cleanup
        shutdown_event.set()
        
        # Cancel any remaining tasks
        current_task = asyncio.current_task()
        all_tasks = [task for task in asyncio.all_tasks() if task is not current_task]
        
        if all_tasks:
            await cleanup_tasks(all_tasks, timeout=10.0)


if __name__ == "__main__":
    # Example usage for testing
    class Args:
        def __init__(self):
            self.start_date = "2024-01-01"
            self.keywords = "teknologi,AI"
            self.scrapers = "auto"
            self.output_format = "xlsx"
    
    args = Args()
    exit_code = asyncio.run(main(args))
    sys.exit(exit_code)