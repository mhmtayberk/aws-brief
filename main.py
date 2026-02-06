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
    except (IOError, OSError) as e:
        typer.echo(f"Database initialization failed: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Unexpected error during database initialization: {e}", err=True)
        raise typer.Exit(1)

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

# ============================================================================
# Smart Digest Helper Functions
# ============================================================================

def _get_recent_items(days: int):
    """
    Get news items from the last N days.
    
    Args:
        days: Number of days to look back
        
    Returns:
        List of NewsItem objects
    """
    from datetime import datetime, timedelta
    
    db = db_manager.get_session()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        items = db.query(NewsItem).filter(
            NewsItem.published_at >= cutoff_date
        ).order_by(NewsItem.published_at.desc()).all()
        
        return items
    finally:
        db.close()


def _generate_smart_digest(items, engine_type: str, model: str, days: int = 7) -> str:
    """
    Generate AI-powered smart digest with categorization.
    
    Args:
        items: List of news items
        engine_type: AI engine to use
        model: AI model name
        days: Number of days for date range display
        
    Returns:
        Formatted smart digest string
    """
    if not items:
        return "No items to analyze."
    
    # Limit to 50 items to avoid token limits
    if len(items) > 50:
        logger.warning(f"Too many items ({len(items)}). Using first 50 for analysis.")
        items = items[:50]
    
    # Prepare items summary for AI
    items_text = ""
    for i, item in enumerate(items, 1):
        items_text += f"{i}. {item.title}\n"
        if item.summary:
            items_text += f"   Summary: {item.summary[:200]}...\n"
        items_text += f"   Published: {item.published_at.strftime('%Y-%m-%d')}\n"
        items_text += f"   Category: {item.tags or 'General'}\n\n"
    
    # AI Prompt
    prompt = f"""Analyze these AWS updates and create a smart digest.

Updates to analyze:
{items_text}

Instructions:
1. Categorize each update into ONE of these categories:
   - CRITICAL: Security patches, breaking changes, action required
   - COST_OPTIMIZATION: Cost savings, efficiency improvements
   - NEW_FEATURES: New services, features, capabilities
   - GENERAL: Other updates

2. For CRITICAL items, specify:
   - Impact level (HIGH/MEDIUM/LOW)
   - Required action
   - Deadline (if applicable)

3. For COST_OPTIMIZATION items, specify:
   - Potential savings or benefit
   - How to implement

4. Format the output as:

🚨 CRITICAL - Action Required (X items)
[List critical items with details]

💰 COST OPTIMIZATION (X opportunities)
[List cost optimization items]

✨ NEW FEATURES (X items)
[List new features briefly]

📌 SUMMARY
Total Updates: X
Critical Actions: X
Cost Savings: X opportunities
New Features: X

Keep it concise and actionable. Use emojis for visual appeal.
Language: {settings.SUMMARY_LANGUAGE}
"""
    
    # Generate with AI
    try:
        ai_engine = EngineFactory.get_engine(engine_type, model)
        digest = ai_engine.summarize(prompt)
        
        # Add header and footer
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        header = f"📊 AWS Brief - Smart Digest ({start_date.strftime('%b %d')}-{end_date.strftime('%b %d, %Y')})\n\n"
        header += "━" * 60 + "\n\n"
        
        footer = "\n" + "━" * 60
        
        return header + digest + footer
        
    except Exception as e:
        logger.error(f"Failed to generate smart digest with AI: {e}")
        # Fallback to simple digest
        return _generate_simple_digest_fallback(items)


def _generate_simple_digest_fallback(items) -> str:
    """
    Fallback to simple digest if AI fails.
    
    Args:
        items: List of news items
        
    Returns:
        Simple formatted digest
    """
    digest = "📊 AWS Brief - Digest\n\n"
    digest += "━" * 60 + "\n\n"
    digest += "⚠️ Note: AI analysis unavailable. Showing simple list.\n\n"
    
    for i, item in enumerate(items, 1):
        digest += f"{i}. {item.title}\n"
        if item.summary:
            summary_preview = item.summary[:200]
            if len(item.summary) > 200:
                summary_preview += "..."
            digest += f"   {summary_preview}\n"
        digest += f"   Published: {item.published_at.strftime('%Y-%m-%d')}\n"
        digest += f"   URL: {item.url}\n\n"
    
    digest += "━" * 60 + "\n"
    digest += f"Total Updates: {len(items)}\n"
    
    return digest


# ============================================================================
# Smart Digest Command
# ============================================================================

@app.command()
def send_smart_digest(
    days: int = typer.Option(7, help="Number of days to look back"),
    channels: str = typer.Option(settings.DEFAULT_NOTIFY_CHANNELS, help="Comma-separated channels"),
    engine: str = typer.Option(settings.DEFAULT_AI_ENGINE, help="AI engine to use"),
    model: Optional[str] = typer.Option(settings.DEFAULT_AI_MODEL, help="AI model name")
):
    """
    Send an AI-powered smart digest with categorization and prioritization.
    
    Categories items into:
    - CRITICAL (action required)
    - COST_OPTIMIZATION (savings opportunities)  
    - NEW_FEATURES (relevant updates)
    - GENERAL (other updates)
    
    Example:
        python main.py send-smart-digest --days 7 --channels slack
        python main.py send-smart-digest --days 14 --engine openai --model gpt-4
    """
    logger.info(f"Generating smart digest for last {days} days...")
    typer.echo(f"🔍 Analyzing AWS updates from the last {days} days...")
    
    # 1. Get items from database
    items = _get_recent_items(days)
    
    if not items:
        typer.echo(f"No items found in the last {days} days.")
        logger.info("No items to process for smart digest.")
        return
    
    typer.echo(f"📊 Found {len(items)} items. Generating AI-powered analysis...")
    
    # 2. Generate smart digest using AI
    target_model = model or settings.DEFAULT_AI_MODEL
    smart_digest = _generate_smart_digest(items, engine, target_model, days)
    
    # 3. Send via notifiers
    notifiers = NotificationFactory.get_notifiers(channels.split(","))
    
    success_count = 0
    for notifier in notifiers:
        try:
            success = notifier.send(
                title=f"AWS Brief - Smart Digest ({days} days)",
                message=smart_digest,
                url="",  # No specific URL for digest
                category="Smart Digest"
            )
            if success:
                logger.info(f"Smart digest sent via {type(notifier).__name__}")
                success_count += 1
            else:
                logger.error(f"Failed to send smart digest via {type(notifier).__name__}")
        except Exception as e:
            logger.error(f"Error sending smart digest via {type(notifier).__name__}: {e}")
    
    if success_count > 0:
        typer.echo(f"✅ Smart digest sent successfully to {success_count} channel(s)!")
    else:
        typer.echo("❌ Failed to send smart digest to any channels.", err=True)
        raise typer.Exit(1)


@app.command()
def export(
    format: str = typer.Option("json", help="Export format: json, csv, markdown, txt"),
    output: str = typer.Option("export", help="Output filename (without extension)"),
    days: int = typer.Option(7, help="Export items from last N days"),
    filter_tags: str = typer.Option(None, help="Filter by tags (comma-separated)")
):
    """
    Export news items to various formats (JSON, CSV, Markdown, TXT).
    """
    from datetime import datetime, timedelta
    import json
    import csv
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        db = db_manager.get_session()
        query = db.query(NewsItem).filter(NewsItem.published_at >= cutoff_date)
        
        if filter_tags:
            tags_list = [tag.strip() for tag in filter_tags.split(",")]
            from sqlalchemy import or_
            tag_filters = [NewsItem.tags.like(f"%{tag}%") for tag in tags_list]
            query = query.filter(or_(*tag_filters))
        
        items = query.order_by(NewsItem.published_at.desc()).all()
        
        if not items:
            typer.echo("❌ No items to export")
            return
        
        filename = f"{output}.{format}"
        
        if format == "json":
            data = [
                {
                    "id": item.id,
                    "title": item.title,
                    "url": item.url,
                    "content": item.content,
                    "summary": item.summary,
                    "published_at": item.published_at.isoformat(),
                    "created_at": item.created_at.isoformat(),
                    "tags": item.tags,
                    "is_notified": item.is_notified
                }
                for item in items
            ]
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        elif format == "csv":
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Title", "URL", "Summary", "Published At", "Tags", "Notified"])
                for item in items:
                    writer.writerow([
                        item.id,
                        item.title,
                        item.url,
                        item.summary or "",
                        item.published_at.isoformat(),
                        item.tags or "",
                        "Yes" if item.is_notified else "No"
                    ])
        
        elif format == "markdown":
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# AWS-Brief Export\n\n")
                f.write(f"**Period**: Last {days} days\n")
                f.write(f"**Total Items**: {len(items)}\n")
                f.write(f"**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n")
                f.write("---\n\n")
                
                for item in items:
                    f.write(f"## {item.title}\n\n")
                    f.write(f"**Published**: {item.published_at.strftime('%Y-%m-%d %H:%M')} UTC\n")
                    f.write(f"**Tags**: {item.tags or 'None'}\n")
                    f.write(f"**Notified**: {'Yes' if item.is_notified else 'No'}\n\n")
                    if item.summary:
                        f.write(f"### Summary\n\n{item.summary}\n\n")
                    f.write(f"[Read Full Article]({item.url})\n\n")
                    f.write("---\n\n")
        
        elif format == "txt":
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"AWS-Brief Export\n")
                f.write(f"Period: Last {days} days\n")
                f.write(f"Total Items: {len(items)}\n")
                f.write(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, item in enumerate(items, 1):
                    f.write(f"{i}. {item.title}\n")
                    f.write(f"   Published: {item.published_at.strftime('%Y-%m-%d %H:%M')} UTC\n")
                    f.write(f"   Tags: {item.tags or 'None'}\n")
                    f.write(f"   Notified: {'Yes' if item.is_notified else 'No'}\n")
                    if item.summary:
                        summary_lines = item.summary.split("\n")
                        f.write(f"   Summary:\n")
                        for line in summary_lines:
                            f.write(f"     {line}\n")
                    f.write(f"   URL: {item.url}\n")
                    f.write("\n" + "-" * 80 + "\n\n")
        
        else:
            typer.echo(f"❌ Unsupported format: {format}. Use: json, csv, markdown, txt")
            return
        
        typer.echo(f"✅ Exported {len(items)} items to {filename}")
        db.close()
        
    except Exception as e:
        typer.echo(f"❌ Export failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def cleanup(
    days: int = typer.Option(30, help="Delete items older than N days"),
    dry_run: bool = typer.Option(False, help="Show what would be deleted without deleting")
):
    """
    Clean up old news items to save disk space.
    """
    from datetime import datetime, timedelta
    from sqlalchemy import text
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        db = db_manager.get_session()
        old_items = db.query(NewsItem).filter(NewsItem.published_at < cutoff_date).all()
        
        if not old_items:
            typer.echo(f"✅ No items older than {days} days found")
            return
        
        if dry_run:
            typer.echo(f"🔍 Would delete {len(old_items)} items older than {days} days:")
            for item in old_items[:10]:
                typer.echo(f"  - {item.title[:60]}... ({item.published_at.strftime('%Y-%m-%d')})")
            if len(old_items) > 10:
                typer.echo(f"  ... and {len(old_items) - 10} more items")
            typer.echo(f"\n💡 Run without --dry-run to actually delete")
        else:
            # Delete items
            for item in old_items:
                db.delete(item)
            db.commit()
            typer.echo(f"✅ Deleted {len(old_items)} items older than {days} days")
            
            # Vacuum database to reclaim space
            try:
                db.execute(text("VACUUM"))
                typer.echo("✅ Database vacuumed (disk space reclaimed)")
            except Exception as e:
                logger.warning(f"Could not vacuum database: {e}")
        
        db.close()
        
    except Exception as e:
        typer.echo(f"❌ Cleanup failed: {e}", err=True)
        raise typer.Exit(1)

