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
from time import sleep
from random import uniform
import nltk
import os

# Download NLTK data silently
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

# Update logging configuration to be less verbose
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Change from INFO to WARNING

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
        'limit': 500,
        'article_selector': 'article.article-item, .article-image',
        'title_selector': 'h3 a, .article-header a',
        'summary_selector': '.article-excerpt, p.text-gray-600',
        'image_selector': '.article-image img, meta[property="og:image"], .image img, img.featured-image',
        'date_selector': 'time, .article-date',
        'categories': [
            {'path': '', 'category': 'all'},
            {'path': '/national', 'category': 'national'},
            {'path': '/politics', 'category': 'politics'},
            {'path': '/valley', 'category': 'valley'},
            {'path': '/opinion', 'category': 'opinion'},
            {'path': '/money', 'category': 'money'},
            {'path': '/sports', 'category': 'sports'},
            {'path': '/art-culture', 'category': 'art-culture'}
        ]
    },
    {
        'url': 'https://thehimalayantimes.com',
        'language': 'en',
        'name': 'The Himalayan Times',
        'limit': 500,
        'article_selector': '.jeg_posts article, .jeg_post',
        'title_selector': '.jeg_post_title a',
        'summary_selector': '.jeg_post_excerpt p, .jeg_excerpt',
        'image_selector': '.jeg_thumb img',
        'date_selector': '.jeg_meta_date',
        'categories': [
            {'path': '', 'category': 'all'}  # Keep only main page for now
        ]
    },
    {
        'url': 'https://english.onlinekhabar.com',
        'language': 'en',
        'name': 'Online Khabar',
        'limit': 500,
        'article_selector': 'article.list-item, .ok-news-post',
        'title_selector': 'h2 a',
        'summary_selector': '.excerpt',
        'image_selector': '.featured-image img',
        'date_selector': '.post-date',
        'categories': [
            {'path': '', 'category': 'all'}  # Keep only main page for now
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

def validate_category_url(site, category):
    """Validate if a category URL exists"""
    url = f"{site['url']}{category['path']}"
    try:
        response = session.head(url, timeout=10)  # Use HEAD request for efficiency
        if response.status_code == 404:
            # Try alternative paths
            alternatives = [
                f"/category/{category['category'].lower()}",
                f"/categories/{category['category'].lower()}",
                f"/{category['category'].lower()}"
            ]
            for alt_path in alternatives:
                alt_url = f"{site['url']}{alt_path}"
                alt_response = session.head(alt_url, timeout=10)
                if alt_response.status_code == 200:
                    logger.info(f"Found alternative path for {category['category']}: {alt_path}")
                    category['path'] = alt_path
                    return True
            return False
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Error validating category URL {url}: {str(e)}")
        return False

def fetch_site_news(site):
    """Fetch news from a single site"""
    articles = []
    processed_urls = set()
    retries = 3

    # Skip validation for now to reduce logs
    for category in site['categories']:
        page = 1
        max_pages = 2  # Reduced from 3 to 2
        
        while len(articles) < site['limit'] and page <= max_pages:
            try:
                sleep(uniform(2.0, 4.0))
                
                page_url = f"{site['url']}{category['path']}"
                if page > 1:
                    page_url += f"/page/{page}"

                response = None
                for attempt in range(retries):
                    try:
                        response = session.get(page_url, timeout=10)  # Reduced timeout
                        if response.status_code == 200:
                            break
                        sleep((attempt + 1) * 2)  # Reduced wait time
                    except Exception:
                        if attempt == retries - 1:
                            raise
                        sleep((attempt + 1) * 2)

                if not response or response.status_code != 200:
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                news_items = soup.select(site['article_selector'])

                if not news_items:
                    break

                for item in news_items[:10]:  # Limit items per page
                    if len(articles) >= site['limit']:
                        break

                    try:
                        # Basic article extraction without full article fetch
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

                        # Get image URL first from preview
                        image_elem = item.select_one(site['image_selector'])
                        image_url = None
                        
                        if image_elem:
                            # Try data-src first (lazy loading images)
                            image_url = image_elem.get('data-src') or image_elem.get('src', '')
                            
                            # Clean up image URL
                            if image_url:
                                if not image_url.startswith('http'):
                                    image_url = site['url'] + image_url if image_url.startswith('/') else None
                        
                        # If no image found in preview, try to get from article page
                        if not image_url and article_url:
                            try:
                                article_response = session.get(article_url, timeout=5)
                                if article_response.status_code == 200:
                                    article_soup = BeautifulSoup(article_response.text, 'html.parser')
                                    
                                    # Try multiple image selectors
                                    image_selectors = [
                                        'meta[property="og:image"]',
                                        'meta[name="twitter:image"]',
                                        '.article-image img',
                                        '.featured-image img',
                                        'article img:first-child'
                                    ]
                                    
                                    for selector in image_selectors:
                                        img = article_soup.select_one(selector)
                                        if img:
                                            image_url = img.get('content') or img.get('src')
                                            if image_url:
                                                # Clean up image URL
                                                if not image_url.startswith('http'):
                                                    image_url = site['url'] + image_url if image_url.startswith('/') else None
                                                break
                            except Exception as e:
                                logger.warning(f"Failed to fetch article page for image: {str(e)}")

                        # Update site-specific image selectors
                        if site['name'] == 'The Kathmandu Post':
                            image_url = image_url or 'https://kathmandupost.com/images/default-fallback.png'
                        
                        # Get summary from preview
                        summary_elem = item.select_one(site['summary_selector'])
                        summary = summary_elem.get_text(strip=True) if summary_elem else title
                        summary = ' '.join(summary.split()[:60]) + '...'

                        articles.append({
                            'title': title,
                            'summary': summary,
                            'url': article_url,
                            'image_url': image_url or 'https://via.placeholder.com/400x300?text=News+Image',
                            'published_at': timezone.now(),
                            'category': category['category'],
                            'source': site['name'],
                            'language': site['language']
                        })

                    except Exception as e:
                        logger.warning(f"Error processing article: {str(e)}")
                        continue

                page += 1

            except Exception:
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

def normalize_category(category):
    """Normalize category name by taking first 3 letters and lowercase"""
    return category.lower()[:3]

def categories_match(cat1, cat2):
    """Check if two categories match based on first 3 letters"""
    return normalize_category(cat1) == normalize_category(cat2)

def get_matching_category(target_category, available_categories):
    """Find matching category from available categories"""
    target_norm = normalize_category(target_category)
    for category in available_categories:
        if normalize_category(category) == target_norm:
            return category
    return None

def fetch_and_summarize_news(page=1, per_page=30):
    """Fetch and summarize news with pagination"""
    try:
        cache_key = f'news_cache_{page}'
        cached_news = cache.get(cache_key)
        
        if cached_news:
            return cached_news

        all_articles = []
        errors = []
        
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
        
        category_mapping = {}  # Cache for category mappings
        
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
                        # Normalize categories before adding to all_articles
                        for article in articles:
                            orig_category = article['category']
                            # Cache the mapping to avoid recalculating
                            if orig_category not in category_mapping:
                                category_mapping[orig_category] = normalize_category(orig_category)
                            article['category'] = category_mapping[orig_category]
                        all_articles.extend(articles)
                    else:
                        errors.append(f"No articles fetched from {site['name']}")
                except Exception as e:
                    errors.append(f"Error processing site {site['url']}: {str(e)}")
                    logger.error(f"Error processing site {site['url']}: {str(e)}")
                    continue
        
        if not all_articles:
            error_msg = "Failed to fetch news. " + " ".join(errors)
            logger.error(error_msg)
            raise Exception(error_msg)

        # Group articles by normalized category
        categorized_articles = {}
        for article in all_articles:
            norm_category = article['category']
            if norm_category not in categorized_articles:
                categorized_articles[norm_category] = []
            categorized_articles[norm_category].append(article)

        # Shuffle articles for random display
        random.shuffle(all_articles)
        
        # Calculate pagination
        total_articles = len(all_articles)
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_articles)
        
        result = {
            'articles': all_articles[start_idx:end_idx],
            'total': total_articles,
            'page': page,
            'per_page': per_page,
            'total_pages': math.ceil(total_articles / per_page),
            'has_next': end_idx < total_articles
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, result, 300)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in fetch_and_summarize_news: {str(e)}")
        raise Exception(f"Failed to fetch news: {str(e)}")

def validate_site_config(site):
    """Validate and test site configuration"""
    try:
        logger.info(f"Testing configuration for {site['name']}")
        
        # Test main page first
        response = session.get(site['url'], timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Test each selector
        selectors = {
            'article': site['article_selector'],
            'title': site['title_selector'],
            'summary': site['summary_selector'],
            'image': site['image_selector'],
            'date': site['date_selector']
        }
        
        for name, selector in selectors.items():
            elements = soup.select(selector)
            logger.info(f"Found {len(elements)} {name} elements using selector: {selector}")
            
            if len(elements) == 0:
                # Try alternative selectors
                if name == 'article':
                    alternatives = ['article', '.post', '.news-item', '.article']
                    for alt in alternatives:
                        count = len(soup.select(alt))
                        logger.info(f"Alternative '{alt}' found {count} elements")
                
        # Test a few categories
        for category in site['categories'][:2]:
            cat_url = site['url'] + category['path']
            logger.info(f"Testing category URL: {cat_url}")
            cat_response = session.get(cat_url, timeout=20)
            if cat_response.status_code != 200:
                logger.warning(f"Category {category['path']} returned status {cat_response.status_code}")
            
    except Exception as e:
        logger.error(f"Error validating site config: {str(e)}", exc_info=True)

if __name__ == '__main__':
    news_articles = fetch_and_summarize_news()
    for article in news_articles:
        print(article)

    # Add this to the main scraper execution
    for site in NEWS_SITES:
        if site['name'] == 'The Himalayan Times':
            validate_site_config(site)
