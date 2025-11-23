"""Search tools initialization and configuration."""

from typing import Any, Dict

from langchain_tavily import TavilySearch


def get_tavily_search(
    max_results: int = 5,
    topic: str = "general",
    search_depth: str = "basic",
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
) -> TavilySearch:
    """
    Initialize Tavily search tool with configuration.

    Args:
        max_results: Maximum number of search results to return.
        topic: Search topic type ('general' or 'news').
        search_depth: Depth of search ('basic' or 'advanced').
        include_domains: List of domains to include in search.
        exclude_domains: List of domains to exclude from search.

    Returns:
        TavilySearch: Configured Tavily search tool.

    Example:
        >>> search = get_tavily_search(max_results=3, topic="news")
        >>> results = search.invoke("latest AI developments")
    """
    kwargs: Dict[str, Any] = {
        "max_results": max_results,
        "topic": topic,
    }

    # Only add optional parameters if provided
    if search_depth != "basic":
        kwargs["search_depth"] = search_depth

    if include_domains:
        kwargs["include_domains"] = include_domains

    if exclude_domains:
        kwargs["exclude_domains"] = exclude_domains

    return TavilySearch(**kwargs)


def get_social_media_search() -> TavilySearch:
    """
    Get Tavily search configured for social media trends.

    Returns:
        TavilySearch: Search tool optimized for social media content.
    """
    return get_tavily_search(
        max_results=5,
        topic="general",
        # Focus on social media platforms
        include_domains=[
            "tiktok.com",
            "twitter.com",
            "x.com",
            "instagram.com",
            "youtube.com",
        ],
    )


def get_educational_content_search() -> TavilySearch:
    """
    Get Tavily search configured for educational content.

    Returns:
        TavilySearch: Search tool optimized for educational resources.
    """
    return get_tavily_search(
        max_results=5,
        topic="general",
        search_depth="advanced",
    )


def get_news_search(max_results: int = 3) -> TavilySearch:
    """
    Get Tavily search configured for news articles.

    Args:
        max_results: Maximum number of news results.

    Returns:
        TavilySearch: Search tool for news content.
    """
    return get_tavily_search(max_results=max_results, topic="news")
