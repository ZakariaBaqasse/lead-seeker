from dataclasses import dataclass


@dataclass
class RawArticle:
    headline: str
    body_snippet: str
    url: str
    source_name: str


def dedupe_by_url(articles: list[RawArticle]) -> list[RawArticle]:
    seen = set()
    result = []
    for article in articles:
        if article.url not in seen:
            seen.add(article.url)
            result.append(article)
    return result
