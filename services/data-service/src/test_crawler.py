"""
Test script to demonstrate ChosunCrawler with JSON output (Mock Kafka)
This script crawls a few articles and saves them to JSON instead of Kafka
"""
import asyncio
import json
from datetime import datetime
import logging
from pathlib import Path
from crawlers.news.chosun_crawler import ChosunCrawler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_crawl_and_save():
    """Test crawling and save results to JSON"""
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Initialize crawler
    crawler = ChosunCrawler()
    
    try:
        async with crawler:
            # Test connection first
            logger.info("Testing connection to Chosun Ilbo...")
            connection_ok = await crawler.test_connection()
            
            if not connection_ok:
                logger.error("Failed to connect to Chosun Ilbo")
                return
            
            logger.info("Connection successful! Starting crawl...")
            
            # Fetch articles (limit to 5 for testing)
            articles = await crawler.fetch_articles(max_articles=5)
            
            if not articles:
                logger.warning("No articles found")
                return
            
            logger.info(f"Successfully crawled {len(articles)} articles")
            
            # Save to JSON file (simulating Kafka message)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"chosun_articles_{timestamp}.json"
            
            # Create Kafka-like message format
            kafka_messages = []
            for article in articles:
                kafka_message = {
                    "topic": "raw-news",
                    "key": article["id"],
                    "value": article,
                    "timestamp": datetime.now().isoformat(),
                    "partition": 0,  # Mock partition
                    "offset": len(kafka_messages)  # Mock offset
                }
                kafka_messages.append(kafka_message)
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(kafka_messages, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(articles)} articles to {output_file}")
            
            # Print summary
            print("\n" + "="*50)
            print("CRAWL SUMMARY")
            print("="*50)
            print(f"Source: {crawler.source_id}")
            print(f"Articles crawled: {len(articles)}")
            print(f"Output file: {output_file}")
            print("\nFirst 3 articles:")
            for i, article in enumerate(articles[:3]):
                print(f"\n{i+1}. {article['title']}")
                print(f"   URL: {article['url']}")
                print(f"   Published: {article.get('published_at', 'N/A')}")
                print(f"   Category: {article.get('category', 'N/A')}")
                if article.get('summary'):
                    print(f"   Summary: {article['summary'][:100]}...")
            
            print("\n" + "="*50)
            print("This is a mock Kafka implementation.")
            print("In production, these messages would be sent to Kafka topic 'raw-news'")
            print("="*50)
            
    except Exception as e:
        logger.exception(f"Error during crawling: {e}")
        raise


async def test_single_article():
    """Test crawling a single article for debugging"""
    crawler = ChosunCrawler()
    
    async with crawler:
        # You can put a specific article URL here for testing
        test_url = "https://www.chosun.com/economy/2024/01/15/example"
        
        try:
            logger.info(f"Fetching single article: {test_url}")
            html = await crawler.fetch_page(test_url)
            article = await crawler.parse_article(test_url, html)
            
            print("\nParsed Article:")
            print(json.dumps(article, ensure_ascii=False, indent=2))
            
        except Exception as e:
            logger.error(f"Failed to fetch article: {e}")


if __name__ == "__main__":
    # Run the main test
    asyncio.run(test_crawl_and_save())
    
    # Uncomment to test single article parsing
    # asyncio.run(test_single_article())