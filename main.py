import typer
import logging
from typing import Optional
from src.utils.config import settings
from src.core.database import db_manager, NewsItem
from src.core.scraper import FeedScraper
from src.engines.factory import EngineFactory
from src.core.filter import FilterEngine, FilterAction
from sqlalchemy.orm import Session

from sqlalchemy import text  # Ensure this is imported

from rich import print as rprint  # Elite printing

# Initialize Typer App
app = typer.Typer(help="AWS-Brief: Secure AWS Intelligence Tool")

# Setup Logging
logging.basicConfig(level=settings.LOG_LEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("aws-brief")

from src.utils.constants import AWS_FEEDS

DEFAULT_FEED_URL = "all"

@app.command()
def init_db():
    """
    Initialize the database tables.
    """
    try:
        db_manager._init_db()
        typer.echo("Database initialized successfully.")
    except Exception as e:
        typer.echo(f"Failed to initialize database: {e}")

@app.command()
def scan(url: str = typer.Option(DEFAULT_FEED_URL, help="Feed URL to scan, or 'all' for all default feeds.")):
    """
    Trigger a manual scan of AWS news sources.
    """
    logger.info(f"Starting scan request for: {url}")
    scraper = FeedScraper()
    filter_engine = FilterEngine() # Load filters if available
    
    targets = []
    if url == "all":
        targets = AWS_FEEDS
    else:
        targets = [{"name": "Custom", "url": url}]

    total_new = 0
    
    for target in targets:
        feed_url = target["url"]
        logger.info(f"Scanning {target['name']} ({feed_url})...")
        try:
            content = scraper.fetch(feed_url)
            parsed_items = scraper.parse(content)
            
            db = db_manager.get_session()
            count = 0
            
            for item_data in parsed_items:
                # Check for duplicates using source_id
                exists = db.query(NewsItem).filter(NewsItem.source_id == item_data["source_id"]).first()
                if not exists:
                    # Append Feed Name to tags
                    base_tag = target["name"]
                    
                    # --- FILTER EVALUATION ---
                    action = filter_engine.evaluate(item_data["title"])
                    
                    # Default state
                    should_notify = False # Pending processing
                    tag_suffix = ""

                    if action == FilterAction.IGNORE:
                        should_notify = True # Mark as 'read' so it's skipped
                        tag_suffix = " [IGNORED]"
                    elif action == FilterAction.DIGEST_ONLY:
                        should_notify = True # Mark as 'read' so it's skipped by realtime cycle
                        tag_suffix = " [DIGEST]"
                    
                    item_data["tags"] = f"{base_tag}{tag_suffix}"
                    item_data["is_notified"] = should_notify
                    
                    new_item = NewsItem(**item_data)
                    db.add(new_item)
                    
                    # Log action if filtered
                    if action != FilterAction.NOTIFY:
                         logger.info(f"  -> Rule Applied: {item_data['title'][:30]}... -> {action}")

                    count += 1
            
            db.commit()
            db.close()
            total_new += count
            logger.info(f"  > Added {count} new items from {target['name']}.")
            
        except Exception as e:
            logger.error(f"Failed to scan {feed_url}: {e}")
            # Continue to next feed
    
    typer.echo(f"Scan complete. Total added: {total_new} new items.")

@app.command()
def summarize(
    item_id: int = typer.Option(..., help="The ID of the news item to summarize"), 
    engine: str = typer.Option(settings.DEFAULT_AI_ENGINE, help="AI Engine to use (ollama, openai)"), 
    model: Optional[str] = typer.Option(settings.DEFAULT_AI_MODEL, help="Specific model name (e.g. llama2, gpt-4)")
):
    """
    Summarize a specific news item by ID using the specified AI engine.
    """
    db = db_manager.get_session()
    try:
        item = db.query(NewsItem).filter(NewsItem.id == item_id).first()
        if not item:
            typer.echo(f"Item {item_id} not found.")
            raise typer.Exit(code=1)
        
        # Use settings defaults if None (though Typer handles default, explicit fallback is safe)
        target_model = model or settings.DEFAULT_AI_MODEL
        
        if item.summary:
            typer.echo(f"Item {item_id} already has a summary.")
            # Optional: Add flag to force re-summarize, but for now just return
            return

        typer.echo(f"Summarizing '{item.title}' using {engine} ({target_model})...")
        
        ai_engine = EngineFactory.get_engine(engine, target_model)
        summary = ai_engine.summarize(item.content or item.title)
        
        item.summary = summary
        db.commit()
        
        typer.echo("Summary generated successfully:")
        typer.echo(summary)
        
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise typer.Exit(code=1)
    finally:
        db.close()

@app.command()
def list_news(limit: int = 10, pending_summary: bool = False):
    """
    List news items.
    """
    db = db_manager.get_session()
    try:
        query = db.query(NewsItem)
        if pending_summary:
            query = query.filter(NewsItem.summary == None)
        
        items = query.order_by(NewsItem.published_at.desc()).limit(limit).all()
        
        if not items:
            typer.echo("No items found.")
            return

        for item in items:
            status = "[SUMMARIZED]" if item.summary else "[PENDING]"
            category = f"[{item.tags}]" if item.tags else "[General]"
            typer.echo(f"{item.id}: {status} {category} {item.title} ({item.published_at})")
            
    finally:
        db.close()

@app.command()
def mark_all_read(confirmation: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt")):
    """
    Mark ALL items in the database as 'Notified' (Read).
    Useful for initial setup to ignore past news and only track future updates.
    """
    db = db_manager.get_session()
    try:
        if not confirmation:
            count_pending = db.query(NewsItem).filter(NewsItem.is_notified == False).count()
            if count_pending == 0:
                typer.echo("All items are already marked as read.")
                return
            
            confirm = typer.confirm(f"This will mark {count_pending} items as Read/Notified. You won't receive notifications for them. Are you sure?")
            if not confirm:
                typer.echo("Operation cancelled.")
                return

        # Bulk update
        db.query(NewsItem).filter(NewsItem.is_notified == False).update({NewsItem.is_notified: True})
        db.commit()
        typer.echo("✅ All items marked as read. You will only be notified of updates from now on.")
        
    except Exception as e:
        logger.error(f"Failed to mark all read: {e}")
        typer.echo(f"Error: {e}")
    finally:
        db.close()

from src.notify.factory import NotificationFactory

@app.command()
def verify_config():
    """
    Test your configuration (AI & Notifications) with a dummy item.
    Verifies API Keys and Webhook URLs without waiting for real news.
    """
    typer.echo("🔍 Starting Configuration Verification...\n")
    
    # 1. Database Check
    try:
        db = db_manager.get_session()
        db.execute(text("SELECT 1"))
        db.close()
        typer.echo("✅ Database Connection: OK")
    except Exception as e:
        typer.echo(f"❌ Database Connection: FAILED ({e})")
        typer.echo("👉 SUGGESTION: Run 'python main.py init-db' to create the database file.")
        return

    # 2. AI Engine Check
    engine_type = settings.DEFAULT_AI_ENGINE
    model = settings.DEFAULT_AI_MODEL
    rprint(f"\n🧠 Testing AI Engine: [bold]{engine_type}[/bold] ({model})...")
    
    dummy_text = "AWS-Brief is an autonomous agent that monitors cloud news. This is a test content to verify summarization."
    summary = ""
    
    try:
        engine = EngineFactory.get_engine(engine_type, model)
        if not engine:
            typer.echo(f"❌ AI Init: Failed (Library not installed?)")
        else:
            summary = engine.summarize(dummy_text)
            if summary:
                typer.echo(f"✅ AI Summarization: OK (Length: {len(summary)})")
            else:
                 typer.echo(f"❌ AI Summarization: Returned empty response")
    except Exception as e:
        typer.echo(f"❌ AI Summarization: FAILED ({e})")
        typer.echo(f"👉 SUGGESTION: Check your API Key in .env and ensure '{engine_type}' library is in requirements.txt")
        # Proceeding to notification anyway, using dummy summary

    # 3. Notification Check
    channels = settings.DEFAULT_NOTIFY_CHANNELS.split(",")
    rprint(f"\n📢 Testing Notifications: {channels}...")
    
    test_title = "AWS-Brief Configuration Test"
    test_msg = summary if summary else "This is a test notification. Your AI engine might have failed, but notifications work!"
    test_url = "https://github.com/your-repo/aws-brief"
    
    notifiers = NotificationFactory.get_notifiers(channels)
    
    for notifier in notifiers:
        provider_name = notifier.__class__.__name__.replace("Notifier", "")
        try:
            success = notifier.send(
                title=test_title, 
                message=test_msg, 
                url=test_url, 
                category="System Test"
            )
            if success:
                typer.echo(f"✅ Notification ({provider_name}): SENT")
            else:
                typer.echo(f"❌ Notification ({provider_name}): FAILED (Check URL) - See logs.")
                typer.echo(f"👉 SUGGESTION: Verify {provider_name.upper()}_WEBHOOK_URL in .env")
        except Exception as e:
            typer.echo(f"❌ Notification ({provider_name}): ERROR ({e})")
            typer.echo(f"👉 SUGGESTION: Check network connection or webhook format.")

    typer.echo("\n✨ Verification Complete.")

@app.command()
def process_cycle(
    channels: str = typer.Option(settings.DEFAULT_NOTIFY_CHANNELS, help="Comma separated list of channels"), 
    engine: str = typer.Option(settings.DEFAULT_AI_ENGINE, help="AI Engine to use"),
    model: Optional[str] = typer.Option(settings.DEFAULT_AI_MODEL, help="Model name"),
    limit: int = 5
):
    """
    Run a full automation cycle: Scan -> Summarize -> Notify.
    Designed for Cron or Daemon usage.
    """
    logger.info(f"Starting automation cycle (Engine: {engine}, Channels: {channels})...")
    
    # 1. Scan
    scan()
    
    # 2. Process Pending Items
    db = db_manager.get_session()
    try:
        # Find unsummarized OR unnotified items (Logic: If summarized but not notified, we should notify)
        # But simpler: Find items that are NOT notified. 
        # If they lack summary, generate it first.
        
        pending_items = db.query(NewsItem).filter(
            NewsItem.is_notified == False
        ).order_by(NewsItem.published_at.desc()).limit(limit).all()
        
        if not pending_items:
            logger.info("No pending items to process.")
            return

        # --- SMART INIT / SPAM PREVENTION ---
        # If this is the first run (no notified items yet) and we have too many pending items,
        # assumption is: User just scanned a full history. Don't spam.
        total_notified_count = db.query(NewsItem).filter(NewsItem.is_notified == True).count()
        total_pending_count = db.query(NewsItem).filter(NewsItem.is_notified == False).count()
        
        # Threshold: If > 50 items pending and 0 history, likely an initial import.
        if total_notified_count == 0 and total_pending_count > 50:
            logger.warning(f"Initial setup detected with {total_pending_count} pending items.")
            logger.warning("Auto-marking them as READ to prevent notification spam.")
            db.query(NewsItem).filter(NewsItem.is_notified == False).update({NewsItem.is_notified: True})
            db.commit()
            logger.info("All old items marked as read. System ready for FUTURE updates.")
            return
        # ------------------------------------

        notifiers = NotificationFactory.get_notifiers(channels.split(","))

        for item in pending_items:
            try:
                # Summarize if needed
                if not item.summary:
                    target_model = model or settings.DEFAULT_AI_MODEL
                    logger.info(f"Summarizing item {item.id} with {target_model}...")
                    ai_engine = EngineFactory.get_engine(engine, target_model)
                    item.summary = ai_engine.summarize(item.content or item.title)
                    db.commit() # Commit summary immediately so we don't lose it if notification fails

                # Notify
                all_sent = True
                for notifier in notifiers:
                    success = notifier.send(
                        title=item.title,
                        message=item.summary,
                        url=item.url,
                        category=item.tags or "General"
                    )
                    if not success:
                        all_sent = False
                
                if all_sent:
                    item.is_notified = True
                    db.commit()
                    logger.info(f"Processed and Notified item {item.id}")
                else:
                    logger.warning(f"Failed to fully notify for item {item.id}, keeping is_notified=False")
                    
            except Exception as e:
                logger.error(f"Error processing item {item.id}: {e}")
                # Continue to next item even if one fails
                continue
                
    finally:
        db.close()
    
    logger.info("Automation cycle complete.")

from datetime import datetime, timedelta

@app.command()
def send_digest(
    days: int = typer.Option(7, help="Number of days to look back"),
    channels: str = typer.Option(settings.DEFAULT_NOTIFY_CHANNELS, help="Comma separated list of channels"),
    engine: str = typer.Option(settings.DEFAULT_AI_ENGINE, help="AI Engine to use"),
    model: Optional[str] = typer.Option(settings.DEFAULT_AI_MODEL, help="Model name")
):
    """
    Generate and send a Weekly/Daily Digest of AWS updates.
    """
    logger.info(f"Generating digest for last {days} days...")
    
    db = db_manager.get_session()
    try:
        since_date = datetime.now() - timedelta(days=days)
        # Assuming published_at is stored as string/datetime compatible. SQLite stores as string.
        # Simple query directly on recent items
        # Ideally we parse date, but for now let's grab last 50 items and filter via python or simple limit
        # Better: Items created_at >= since_date
        
        items = db.query(NewsItem).filter(NewsItem.created_at >= since_date).all()
        
        if not items:
            logger.info("No news found in the specified period.")
            return

        logger.info(f"Found {len(items)} items. Preparing summary...")
        
        # Create a consolidated text for AI
        digest_content = ""
        for item in items:
            category = item.tags or "General"
            
            # Skip IGNORED items from Digest
            if "[IGNORED]" in category:
                continue
                
            digest_content += f"- [{category}] {item.title}: {item.summary or 'No summary'}\n"
        
        # Limit content length to avoid token limits (arbitrary safety cut)
        digest_content = digest_content[:15000] 

        prompt = f"""
        Review the following list of AWS updates from the last {days} days.
        Group them by category (e.g., Security, Compute, Database).
        Provide a "Weekly Executive Summary" highlighting the most critical updates.
        Language: {settings.SUMMARY_LANGUAGE}.
        
        Updates:
        {digest_content}
        """
        
        target_model = model or settings.DEFAULT_AI_MODEL
        ai_engine = EngineFactory.get_engine(engine, target_model)
        
        try:
            full_report = ai_engine.summarize(prompt)
        except Exception as e:
            logger.error(f"Failed to generate digest: {e}")
            return

        # Send Report
        logger.info("Sending Digest...")
        notifiers = NotificationFactory.get_notifiers(channels.split(","))
        
        title = f"AWS Weekly Digest ({datetime.now().strftime('%Y-%m-%d')})"
        
        for notifier in notifiers:
            notifier.send(
                title=title,
                message=full_report,
                url="https://aws.amazon.com/new/" # Fallback link
            )
            
        logger.info("Digest sent successfully.")

    finally:
        db.close()

if __name__ == "__main__":
    app()
