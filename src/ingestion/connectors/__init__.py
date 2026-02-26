"""Data ingestion connectors"""
from src.ingestion.connectors.csv_connector import CSVConnector
from src.ingestion.connectors.web_scraper_connector import WebScraperConnector

__all__ = ['CSVConnector', 'WebScraperConnector']
