import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

async def main():
    browser_config = BrowserConfig()  # Default browser configuration
    run_config = CrawlerRunConfig()   # Default crawl run configuration

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.betteratenglish.com/050-horrible-neighbor-transcript",
            config=run_config
        )
        print(result.cleaned_html)  # Print clean HTML content
        with open("crawl4ai_output_html.txt", "w", encoding="utf-8") as file:
            file.write(result.html)
            file.close()
        with open("crawl4ai_output_cleaned_html.txt", "w", encoding="utf-8") as file:
            file.write(result.cleaned_html)
            file.close()
        with open("crawl4ai_output_markdown.txt", "w", encoding="utf-8") as file:
            file.write(result.markdown)
            file.close()

if __name__ == "__main__":
    asyncio.run(main())