import asyncio

import pytest

from newswatch.utils import AsyncScraper


@pytest.mark.asyncio
async def test_fetch_success():
    scraper = AsyncScraper()
    async with scraper:
        response = await scraper.fetch("https://httpbin.org/get")
        assert response is not None


@pytest.mark.asyncio
async def test_fetch_failure():
    scraper = AsyncScraper()
    async with scraper:
        response = await scraper.fetch("https://httpbin.org/status/404")
        assert response is None
