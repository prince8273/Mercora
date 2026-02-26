"""CLI commands for data ingestion"""
import click
import asyncio
from uuid import UUID
from pathlib import Path

from src.ingestion.connectors.csv_connector import CSVConnector
from src.ingestion.connectors.web_scraper_connector import WebScraperConnector
from src.ingestion.ingestion_service import IngestionService
from src.ingestion.scheduler_service import get_scheduler_service


@click.group()
def ingestion():
    """Data ingestion commands"""
    pass


@ingestion.command()
@click.option('--tenant-id', required=True, help='Tenant UUID')
@click.option('--file-path', required=True, help='Path to CSV file')
@click.option('--source-name', required=True, help='Source name')
@click.option('--id-column', default='sku', help='ID column name')
@click.option('--data-type', default='product', help='Data type (product, review, etc.)')
def ingest_csv(tenant_id: str, file_path: str, source_name: str, id_column: str, data_type: str):
    """Ingest data from CSV file"""
    click.echo(f"Starting CSV ingestion from {file_path}...")
    
    try:
        # Validate inputs
        tenant_uuid = UUID(tenant_id)
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            click.echo(f"Error: File not found: {file_path}", err=True)
            return
        
        # Create connector
        connector = CSVConnector(
            tenant_id=tenant_uuid,
            file_path=str(file_path_obj),
            source_name=source_name,
            id_column=id_column,
            data_type=data_type
        )
        
        # Ingest data
        service = IngestionService(tenant_id=tenant_uuid)
        result = service.ingest_from_connector(connector)
        
        # Display results
        click.echo("\n✓ Ingestion completed successfully!")
        click.echo(f"\nStatistics:")
        click.echo(f"  Records Fetched: {result['statistics']['records_fetched']}")
        click.echo(f"  Records Saved: {result['statistics']['records_saved']}")
        click.echo(f"  Duplicates Skipped: {result['statistics']['records_skipped_duplicate']}")
        click.echo(f"  Failed: {result['statistics']['records_failed']}")
        click.echo(f"  Duration: {result['duration_seconds']:.2f}s")
        
    except ValueError as e:
        click.echo(f"Error: Invalid tenant ID: {e}", err=True)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@ingestion.command()
@click.option('--tenant-id', required=True, help='Tenant UUID')
@click.option('--urls', required=True, help='Comma-separated URLs to scrape')
@click.option('--source-name', required=True, help='Source name')
@click.option('--rate-limit', default=0.5, help='Requests per second')
def scrape_urls(tenant_id: str, urls: str, source_name: str, rate_limit: float):
    """Scrape data from URLs"""
    click.echo(f"Starting web scraping...")
    
    try:
        # Validate inputs
        tenant_uuid = UUID(tenant_id)
        url_list = [url.strip() for url in urls.split(',')]
        
        click.echo(f"  URLs to scrape: {len(url_list)}")
        click.echo(f"  Rate limit: {rate_limit} req/s")
        
        # Create connector
        connector = WebScraperConnector(
            tenant_id=tenant_uuid,
            urls=url_list,
            source_name=source_name,
            requests_per_second=rate_limit
        )
        
        # Ingest data
        service = IngestionService(tenant_id=tenant_uuid)
        result = service.ingest_from_connector(connector)
        
        # Display results
        click.echo("\n✓ Scraping completed!")
        click.echo(f"\nStatistics:")
        click.echo(f"  Records Fetched: {result['statistics']['records_fetched']}")
        click.echo(f"  Records Saved: {result['statistics']['records_saved']}")
        click.echo(f"  Duplicates Skipped: {result['statistics']['records_skipped_duplicate']}")
        click.echo(f"  Failed: {result['statistics']['records_failed']}")
        click.echo(f"  Duration: {result['duration_seconds']:.2f}s")
        
        # Display scraper stats
        scraper_stats = connector.get_statistics()
        click.echo(f"\nScraper Statistics:")
        click.echo(f"  URLs Attempted: {scraper_stats['urls_attempted']}")
        click.echo(f"  URLs Scraped: {scraper_stats['urls_scraped']}")
        click.echo(f"  Blocked by robots.txt: {scraper_stats['urls_blocked_robots']}")
        click.echo(f"  Failed: {scraper_stats['urls_failed']}")
        
    except ValueError as e:
        click.echo(f"Error: Invalid tenant ID: {e}", err=True)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@ingestion.command()
@click.option('--tenant-id', required=True, help='Tenant UUID')
@click.option('--file-path', required=True, help='Path to CSV file')
@click.option('--source-name', required=True, help='Source name')
@click.option('--schedule', required=True, help='Cron expression or interval (e.g., "0 2 * * *" or "6h")')
@click.option('--id-column', default='sku', help='ID column name')
def schedule_csv(tenant_id: str, file_path: str, source_name: str, schedule: str, id_column: str):
    """Schedule periodic CSV ingestion"""
    click.echo(f"Scheduling CSV ingestion...")
    
    try:
        tenant_uuid = UUID(tenant_id)
        scheduler = get_scheduler_service()
        
        # Parse schedule
        if schedule.endswith('h'):
            # Interval in hours
            interval_hours = int(schedule[:-1])
            job_id = scheduler.schedule_csv_ingestion(
                tenant_id=tenant_uuid,
                file_path=file_path,
                source_name=source_name,
                id_column=id_column,
                interval_hours=interval_hours
            )
        else:
            # Cron expression
            job_id = scheduler.schedule_csv_ingestion(
                tenant_id=tenant_uuid,
                file_path=file_path,
                source_name=source_name,
                id_column=id_column,
                cron_expression=schedule
            )
        
        click.echo(f"✓ Scheduled CSV ingestion: {job_id}")
        click.echo(f"  Source: {source_name}")
        click.echo(f"  Schedule: {schedule}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@ingestion.command()
@click.option('--tenant-id', required=True, help='Tenant UUID')
@click.option('--urls', required=True, help='Comma-separated URLs to scrape')
@click.option('--source-name', required=True, help='Source name')
@click.option('--schedule', required=True, help='Cron expression or interval (e.g., "0 2 * * *" or "6h")')
@click.option('--rate-limit', default=0.5, help='Requests per second')
def schedule_scraping(tenant_id: str, urls: str, source_name: str, schedule: str, rate_limit: float):
    """Schedule periodic web scraping"""
    click.echo(f"Scheduling web scraping...")
    
    try:
        tenant_uuid = UUID(tenant_id)
        url_list = [url.strip() for url in urls.split(',')]
        scheduler = get_scheduler_service()
        
        # Parse schedule
        if schedule.endswith('h'):
            # Interval in hours
            interval_hours = int(schedule[:-1])
            job_id = scheduler.schedule_web_scraping(
                tenant_id=tenant_uuid,
                urls=url_list,
                source_name=source_name,
                interval_hours=interval_hours,
                requests_per_second=rate_limit
            )
        else:
            # Cron expression
            job_id = scheduler.schedule_web_scraping(
                tenant_id=tenant_uuid,
                urls=url_list,
                source_name=source_name,
                cron_expression=schedule,
                requests_per_second=rate_limit
            )
        
        click.echo(f"✓ Scheduled web scraping: {job_id}")
        click.echo(f"  Source: {source_name}")
        click.echo(f"  URLs: {len(url_list)}")
        click.echo(f"  Schedule: {schedule}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@ingestion.command()
def list_jobs():
    """List all scheduled ingestion jobs"""
    try:
        scheduler = get_scheduler_service()
        jobs = scheduler.get_jobs()
        
        if not jobs:
            click.echo("No scheduled jobs found.")
            return
        
        click.echo(f"\nScheduled Jobs ({len(jobs)}):")
        click.echo("=" * 70)
        
        for job in jobs:
            click.echo(f"\nJob ID: {job['id']}")
            click.echo(f"  Name: {job['name']}")
            click.echo(f"  Next Run: {job['next_run_time']}")
            click.echo(f"  Trigger: {job['trigger']}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@ingestion.command()
@click.argument('job_id')
def remove_job(job_id: str):
    """Remove a scheduled job"""
    try:
        scheduler = get_scheduler_service()
        scheduler.remove_job(job_id)
        click.echo(f"✓ Removed job: {job_id}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@ingestion.command()
def status():
    """Show ingestion system status"""
    try:
        scheduler = get_scheduler_service()
        stats = scheduler.get_statistics()
        
        click.echo("\nIngestion System Status:")
        click.echo("=" * 70)
        click.echo(f"  Scheduler Running: {stats['is_running']}")
        click.echo(f"  Total Jobs: {stats['total_jobs']}")
        click.echo(f"  Total Executions: {stats['total_executions']}")
        click.echo(f"  Failed Executions: {stats['failed_executions']}")
        click.echo(f"  Success Rate: {stats['success_rate']:.1%}")
        
        # Show recent executions
        history = scheduler.get_execution_history(limit=5)
        if history:
            click.echo(f"\nRecent Executions:")
            for execution in history:
                status_icon = "✓" if execution['status'] == 'success' else "✗"
                click.echo(f"  {status_icon} {execution['job_id']} - {execution['timestamp']}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


if __name__ == '__main__':
    ingestion()
