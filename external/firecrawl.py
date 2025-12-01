from firecrawl import Firecrawl
import trafilatura

from utils import get_env_var


def get_url_content(url: str) -> str:
    firecrawl = Firecrawl(api_key=get_env_var("FIRECRAWL_KEY"))
    content = firecrawl.scrape(url, formats=["html"])
    extracted_text = trafilatura.extract(content.html)
    return extracted_text
