import asyncio
from playwright.async_api import async_playwright, expect

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("http://127.0.0.1:8000/")

        # Wait for the chart to be ready by looking for the canvas element
        await page.wait_for_selector('canvas', timeout=60000)

        # Wait for the red line to appear, which indicates the "Fluxo Compra"
        # Since we can't directly select the line, we'll wait for a bit and take a screenshot.
        await page.wait_for_timeout(5000) # 5 seconds delay to ensure data is loaded

        await page.screenshot(path="jules-scratch/verification/verification.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())