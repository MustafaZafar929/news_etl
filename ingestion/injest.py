import feedparser
import psycopg2
import os
from datetime import datetime, timedelta, timezone
from time import mktime
from dagster import asset, Output, Definitions, ScheduleDefinition, define_asset_job
from dotenv import load_dotenv

load_dotenv()


# --- CONFIGURATION ---
RSS_FEEDS = [
    # ---- Center / Straight News ----
    "https://www.reuters.com/rssFeed/worldNews",
    "https://www.reuters.com/rssFeed/businessNews",
    "https://apnews.com/apf-topnews?format=rss",
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://feeds.npr.org/1001/rss.xml",

    # ---- Center-Left / International ----
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.theguardian.com/world/rss",
    "https://www.dw.com/en/top-stories/rss",
    "https://www.ft.com/world?format=rss",

    # ---- Left / Progressive ----
    "https://www.msnbc.com/feeds/latest",
    "https://www.thenation.com/feed/",
    "https://truthout.org/feed/",
    "https://www.democracynow.org/democracynow.rss",

    # ---- Center-Right ----
    "https://www.wsj.com/xml/rss/3_7031.xml",
    "https://www.economist.com/rss",
    "https://www.politico.com/rss/politics08.xml",
    "https://thehill.com/rss/syndicator/19110",

    # ---- Right / Conservative ----
    "https://moxie.foxnews.com/google-publisher/latest.xml",
    "https://www.washingtontimes.com/rss/headlines/news/",
    "https://www.nationalreview.com/feed/",
    "https://dailycaller.com/feed/",

    # ---- Geopolitics / Conflict / Analysis ----
    "https://www.foreignaffairs.com/rss.xml",
    "https://www.foreignpolicy.com/rss",
    "https://www.crisisgroup.org/rss.xml",
    "https://www.defensenews.com/arc/outboundfeeds/rss/"
]


def get_db_conn():
    """Establishes a connection to Supabase using the Env Var"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is missing!")
    return psycopg2.connect(db_url)

@asset
def raw_news_articles():
    """
    Scrapes RSS feeds, FILTERS out old news, and saves to Postgres.
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    
    # 1. Define the Cutoff (24 Hours ago)
    # We use UTC to ensure consistent comparison regardless of server location
    cutoff_date = datetime.now(timezone.utc) - timedelta(hours=24)
    print(f"Filtering articles older than: {cutoff_date}")

    total_inserted = 0
    
    for feed_url in RSS_FEEDS:
        print(f"Scraping: {feed_url}")
        feed = feedparser.parse(feed_url)
        
        for entry in feed.entries:
            # --- THE FIX: Date Filtering ---
            # feedparser gives us 'published_parsed', which is a time struct
            if not hasattr(entry, 'published_parsed') or not entry.published_parsed:
                continue # Skip articles with no date

            # Convert struct_time to a timezone-aware datetime object
            article_dt = datetime.fromtimestamp(mktime(entry.published_parsed), timezone.utc)

            # The Gatekeeper: If it's old, skip it.
            if article_dt < cutoff_date:
                continue

            # --- Data Preparation ---
            title = entry.get('title', '')
            link = entry.get('link', '')
            summary = entry.get('summary', '')
            source_domain = feed_url.split('/')[2] # naive domain extraction
            
            # --- Insertion ---
            # We use ON CONFLICT DO NOTHING to ensure we don't crash if we
            # pick up the same article twice in one day.
            # (Requires a UNIQUE constraint on 'link' or 'title' in your DB)
            try:
                cursor.execute("""
                    INSERT INTO articles (title, content_summary, source_domain, published_date, link)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (link) DO NOTHING; 
                """, (title, summary, source_domain, article_dt, link))
                
                # Check if a row was actually inserted
                if cursor.rowcount > 0:
                    total_inserted += 1
                    
            except Exception as e:
                print(f"Error inserting {title}: {e}")
                conn.rollback() # Reset transaction on error
                continue

    conn.commit()
    conn.close()

    return Output(
        total_inserted, 
        metadata={
            "New Articles": total_inserted, 
            "Sources Scraped": len(RSS_FEEDS)
        }
    )

# --- JOB & SCHEDULE ---
news_job = define_asset_job(name="ingest_news_job", selection=["raw_news_articles"])

news_schedule = ScheduleDefinition(
    job=news_job,
    cron_schedule="0 8,16 * * *", 
    execution_timezone="Asia/Karachi",
    name="bi_daily_ingestion"
)

defs = Definitions(
    assets=[raw_news_articles],
    jobs=[news_job],
    schedules=[news_schedule]
)





# ... (End of your existing code) ...

# Add this at the bottom to allow running via "python ingest_job.py"
if __name__ == "__main__":
    from dagster import materialize
    import os
    
    # Load env vars manually for local testing if not set
    # (Or make sure you have your .env file in the same folder)
    if not os.getenv("DATABASE_URL"):
        print("⚠️ WARNING: DATABASE_URL not found. Setting manually for test...")
        # Paste your Supabase URL here for testing ONLY
        os.environ["DATABASE_URL"] = "postgresql://postgres.xxxx:pass@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"

    print("🚀 Starting local test run...")
    result = materialize([raw_news_articles])
    
    if result.success:
        print("✅ Success!")
    else:
        print("❌ Failed!")