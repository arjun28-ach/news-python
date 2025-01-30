import requests
from bs4 import BeautifulSoup
from newspaper import Article
import logging
from functools import lru_cache
from datetime import datetime, timedelta
from django.utils import timezone
import concurrent.futures
import pytz
import random
import math
from django.core.cache import cache
import time

logger = logging.getLogger(__name__)

# Configure requests session
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

# List of reliable Nepali news websites with correct paths
NEWS_SITES = [
    {
        'url': 'https://kathmandupost.com',
        'language': 'en',
        'name': 'The Kathmandu Post',
        'limit': 200,
        'article_selector': 'article.article-item, .article-image',
        'title_selector': 'h3 a, .article-header a',
        'summary_selector': '.article-excerpt, p.text-gray-600',
        'image_selector': 'img.img-responsive, img.article-image',
        'date_selector': 'time, .article-date',
        'categories': [
            {'path': '', 'category': 'all'}  # Main page
        ]
    },
    {
        'url': 'https://thehimalayantimes.com',
        'language': 'en',
        'name': 'The Himalayan Times',
        'limit': 200,
        'article_selector': '.post-card, article.post',
        'title_selector': 'h2.title a, h2.post-title a',
        'summary_selector': '.excerpt, .post-excerpt',
        'image_selector': '.featured-image img, .post-thumbnail img',
        'date_selector': '.post-date, time',
        'categories': [
            {'path': '', 'category': 'all'}  # Main page
        ]
    },
    {
        'url': 'https://english.onlinekhabar.com',
        'language': 'en',
        'name': 'Online Khabar',
        'limit': 200,
        'article_selector': 'article.list-item, .ok-news-post',
        'title_selector': 'h2 a',
        'summary_selector': '.excerpt',
        'image_selector': '.featured-image img',
        'date_selector': '.post-date',
        'categories': [
            {'path': '', 'category': 'all'}  # Main page
        ]
    },
    {
        'url': 'https://myrepublica.nagariknetwork.com',
        'language': 'en',
        'name': 'Republica',
        'limit': 200,
        'article_selector': '.article-item, .news-item',
        'title_selector': 'h3 a, .title a',
        'summary_selector': '.summary, .excerpt',
        'image_selector': '.featured-image img, .article-image img',
        'date_selector': '.date, .published-date',
        'categories': [
            {'path': '', 'category': 'all'}  # Main page
        ]
    },
    {
        'url': 'https://nepalnews.com',
        'language': 'en',
        'name': 'Nepal News',
        'limit': 200,
        'article_selector': '.news-card, article',
        'title_selector': '.card-title a, h2 a',
        'summary_selector': '.card-text, .excerpt',
        'image_selector': '.card-img-top, .featured-image img',
        'date_selector': '.date, time',
        'categories': [
            {'path': '', 'category': 'all'}  # Main page
        ]
    },
    {
        'url': 'https://risingnepaldaily.com',
        'language': 'en',
        'name': 'The Rising Nepal',
        'limit': 200,
        'article_selector': '.news-post, article',
        'title_selector': '.entry-title a, h2 a',
        'summary_selector': '.entry-content p, .excerpt',
        'image_selector': '.entry-thumbnail img, .featured-image img',
        'date_selector': '.entry-date, .post-date',
        'categories': [
            {'path': '', 'category': 'all'}  # Main page
        ]
    }
]

def fetch_article(url):
    """Fetch and parse a single article"""
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        # Add site-specific parsing rules
        if 'kathmandupost.com' in url:
            # Remove subscription prompts
            article.text = article.text.split('Read full story')[0]
        elif 'thehimalayantimes.com' in url:
            # Clean up any ads or related articles
            article.text = article.text.split('Related News')[0]
        elif 'onlinekhabar.com' in url:
            # Remove recommended content
            article.text = article.text.split('You might also like')[0]
        
        # Clean up common issues
        article.text = article.text.strip()
        article.text = ' '.join(article.text.split())  # Remove extra whitespace
        
        return article
    except Exception as e:
        logger.error(f"Error fetching article {url}: {e}")
        return None

def fetch_site_news(site):
    """Fetch news from a single site"""
    articles = []
    processed_urls = set()
    page = 1
    max_pages = 5
    retries = 3

    while len(articles) < site['limit'] and page <= max_pages:
        try:
            # Handle pagination
            if page > 1:
                page_url = f"{site['url']}/page/{page}"
            else:
                page_url = site['url']

            # Add retry logic
            for attempt in range(retries):
                try:
                    response = session.get(page_url, timeout=10)
                    if response.status_code == 404:
                        break
                    response.raise_for_status()
                    break
                except requests.exceptions.RequestException:
                    if attempt == retries - 1:
                        logger.warning(f"Failed to fetch {page_url} after {retries} attempts")
                        break
                    time.sleep(1)
                    continue

            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = soup.select(site['article_selector'])

            if not news_items:
                break

            for item in news_items:
                if len(articles) >= site['limit']:
                    break

                try:
                    # Extract title and URL
                    title_elem = item.select_one(site['title_selector'])
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    article_url = title_elem.get('href', '')

                    if not article_url or article_url in processed_urls:
                        continue

                    if article_url.startswith('/'):
                        article_url = site['url'] + article_url
                    elif not article_url.startswith('http'):
                        continue

                    processed_urls.add(article_url)

                    # Try to get full article for better content
                    try:
                        article = Article(article_url, timeout=5)
                        article.download()
                        article.parse()
                        
                        # Get the main image
                        image_url = article.top_image
                        
                        # Get or generate summary
                        article.nlp()
                        summary = article.summary
                        if summary:
                            summary = ' '.join(summary.split()[:60]) + '...'
                    except:
                        # Fallback to preview content if full article fails
                        summary_elem = item.select_one(site['summary_selector'])
                        summary = summary_elem.get_text(strip=True) if summary_elem else title
                        summary = ' '.join(summary.split()[:60]) + '...'
                        
                        # Get image from preview
                        image_elem = item.select_one(site['image_selector'])
                        image_url = image_elem.get('src', '') if image_elem else ''

                    # Clean up image URL
                    if image_url and not image_url.startswith('http'):
                        image_url = site['url'] + image_url if image_url.startswith('/') else None

                    articles.append({
                        'title': title,
                        'summary': summary,
                        'url': article_url,
                        'image_url': image_url or 'https://via.placeholder.com/400x300?text=News+Image',
                        'published_at': timezone.now(),
                        'category': site['categories'][0]['category'],
                        'source': site['name'],
                        'language': site['language']
                    })

                except Exception as e:
                    logger.error(f"Error processing article: {e}")
                    continue

            page += 1

        except Exception as e:
            logger.warning(f"Error on page {page} for {site['url']}: {str(e)}")
            break

    return articles

def parse_date(date_str):
    """Parse date string to datetime object"""
    try:
        # Add your date parsing logic here based on the format from each site
        return timezone.now()  # Temporary fallback
    except Exception:
        return timezone.now()

def clear_news_cache():
    """Clear the news cache"""
    try:
        # Clear the all articles cache
        cache.delete('all_articles_cache')
        
        # Clear first few pages of cached results
        for i in range(1, 11):  # Clear first 10 pages
            cache_key = f'news_cache_{i}'
            cache.delete(cache_key)
            
        logger.info("News cache cleared successfully")
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")

# Update the cache clearing schedule
last_cache_clear = timezone.now()

def maybe_clear_cache():
    """Check and clear cache if needed"""
    global last_cache_clear
    now = timezone.now()
    if now - last_cache_clear > timedelta(hours=1):
        clear_news_cache()
        last_cache_clear = now
        return True
    return False

def fetch_and_summarize_news(page=1, per_page=30):
    """Fetch and summarize news with pagination"""
    try:
        cache_key = f'news_cache_{page}'
        cached_news = cache.get(cache_key)
        
        if cached_news:
            return cached_news

        all_articles = []
        # Load more sites as we go deeper in pages
        if page <= 2:
            active_sites = NEWS_SITES[:3]  # First 3 sites for first 2 pages
            articles_per_site = 30  # 30 articles each
        elif page <= 4:
            active_sites = NEWS_SITES[:4]  # 4 sites for pages 3-4
            articles_per_site = 40  # 40 articles each
        else:
            active_sites = NEWS_SITES  # All sites for later pages
            articles_per_site = 50  # 50 articles each
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_site = {
                executor.submit(
                    fetch_site_news, 
                    {**site, 'limit': articles_per_site}
                ): site for site in active_sites
            }
            
            for future in concurrent.futures.as_completed(future_to_site):
                site = future_to_site[future]
                try:
                    articles = future.result()
                    if articles:
                        all_articles.extend(articles)
                except Exception as e:
                    logger.error(f"Error processing site {site['url']}: {e}")
                    continue
        
        if len(all_articles) < 10:  # Minimum requirement
            raise Exception("Not enough articles could be fetched. Please try again later.")

        # Shuffle articles for random display
        random.shuffle(all_articles)
        
        # Calculate pagination
        total_articles = len(all_articles)
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_articles)
        
        paginated_articles = all_articles[start_idx:end_idx]
        
        result = {
            'articles': paginated_articles,
            'total': total_articles,
            'page': page,
            'per_page': per_page,
            'total_pages': math.ceil(total_articles / per_page),
            'has_next': end_idx < total_articles
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, result, 300)
        
        # Pre-fetch next page in background
        if end_idx < total_articles:
            next_page_key = f'news_cache_{page + 1}'
            if not cache.get(next_page_key):
                next_result = {
                    'articles': all_articles[end_idx:end_idx + per_page],
                    'total': total_articles,
                    'page': page + 1,
                    'per_page': per_page,
                    'total_pages': math.ceil(total_articles / per_page),
                    'has_next': (end_idx + per_page) < total_articles
                }
                cache.set(next_page_key, next_result, 300)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in fetch_and_summarize_news: {e}")
        raise Exception("Failed to fetch news. Please try again later.")

if __name__ == '__main__':
    news_articles = fetch_and_summarize_news()
    for article in news_articles:
        print(article)
