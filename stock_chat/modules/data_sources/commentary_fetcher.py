"""
modules/data_sources/commentary_fetcher.py

Fetches earnings-related news commentary using Google News.
This is particularly useful for stocks where direct transcripts are not available,
like those on Indian exchanges.
"""
from typing import List, Dict, Optional
from pygooglenews import GoogleNews
import feedparser
import time
import logging

logger = logging.getLogger(__name__)

# Default candidate news sources for Indian companies
DEFAULT_SITES = ["moneycontrol.com", "economictimes.indiatimes.com", "business-standard.com", "livemint.com", "thehindubusinessline.com"]

class CommentaryFetcher:
    """
    Fetches earnings commentary from Google News. It uses pygooglenews with an RSS fallback.
    """
    def __init__(self, country: str = "IN"):
        self.gn = GoogleNews(lang='en', country=country)
        self.site_filters = DEFAULT_SITES
    
    def _build_search_variants(self, company_name: str, quarter: str, year: str) -> List[str]:
        y_short = year[-2:]
        qnum = quarter[-1] if quarter.upper().startswith("Q") else quarter
        variants = [
            f"{company_name} {quarter} {year} results",
            f"{company_name} quarterly results",
            f"{company_name} FY{y_short} results",
            f"{company_name} earnings",
            f"{company_name} Q{qnum} FY{y_short} results",
            f"{company_name} Q{qnum} results",
        ]
        seen = set()
        return [v for v in variants if not (v in seen or seen.add(v))]
    
    def _pygn_search(self, query: str) -> List[Dict]:
        try:
            news = self.gn.search(query)
            return [{
                "title": e.get("title", ""), "link": e.get("link", ""),
                "published": e.get("published", None), "query": query,
            } for e in news.get("entries", [])]
        except Exception as e:
            logger.debug("pygooglenews search failed for '%s': %s", query, e)
            return []
    
    def _rss_search(self, query: str) -> List[Dict]:
        try:
            url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
            feed = feedparser.parse(url)
            return [{
                "title": getattr(e, "title", ""), "link": getattr(e, "link", ""),
                "published": getattr(e, "published", None), "query": query,
            } for e in getattr(feed, "entries", [])]
        except Exception as e:
            logger.debug("RSS search failed for '%s': %s", query, e)
            return []
    
    def fetch(self, company_name: str, quarter: str, year: str, max_results: int = 5) -> List[Dict]:
        variants = self._build_search_variants(company_name, quarter, year)
        raw_articles: List[Dict] = []
        
        for q in variants:
            raw_articles.extend(self._pygn_search(q))
            time.sleep(0.1)
        
        if not raw_articles:
            for q in variants:
                raw_articles.extend(self._rss_search(q))
                time.sleep(0.1)
        
        name_part = company_name.lower().split()[0]
        filtered: List[Dict] = []
        seen_links = set()
        
        for a in raw_articles:
            title = a.get('title', '') or ''
            link = a.get('link', '') or ''
            if not link or link in seen_links:
                continue
            
            relevant = (name_part in title.lower()) or (name_part in link.lower())
            site_match = any(site in link.lower() for site in self.site_filters)
            
            if relevant and (site_match or len(filtered) < max_results):
                seen_links.add(link)
                filtered.append({
                    'title': title.strip(),
                    'link': link,
                    'published': a.get('published'),
                    'source': link.split('/')[2] if '/' in link else '',
                    'query': a.get('query'),
                })
                if len(filtered) >= max_results:
                    break
        
        return filtered
