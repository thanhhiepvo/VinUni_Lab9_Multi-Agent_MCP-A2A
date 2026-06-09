import asyncio
from crawl4ai import AsyncWebCrawler
async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://vnexpress.net/dien-vien-hai-huu-tin-bi-de-nghi-truy-to-7-15-nam-tu-4530802.html", css_selector="article.fck_detail")
        print("ATTRIBUTES:", [x for x in dir(result) if not x.startswith('_')])
        if hasattr(result, 'extracted_content'):
            print("extracted_content:", len(result.extracted_content) if result.extracted_content else None)
        if hasattr(result, 'fit_markdown'):
            print("fit_markdown:", len(result.fit_markdown) if result.fit_markdown else None)
        if hasattr(result, 'markdown_v2'):
            print("markdown_v2.fit_markdown:", len(result.markdown_v2.fit_markdown) if result.markdown_v2 and hasattr(result.markdown_v2, 'fit_markdown') else None)
            
asyncio.run(main())
