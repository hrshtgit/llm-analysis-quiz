from playwright.async_api import async_playwright


async def get_page_text(url: str) -> str:
    """
    Load URL with JS enabled and return visible text in <body>.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        text = await page.text_content("body")
        await browser.close()
        return text or ""


async def get_page_html(url: str) -> str:
    """
    Load URL with JS enabled and return full HTML content.
    Useful when we need <a href="...csv"> etc.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        html = await page.content()
        await browser.close()
        return html