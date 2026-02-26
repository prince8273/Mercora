#!/usr/bin/env python3
"""Management CLI for E-commerce Intelligence Agent"""
import click

from src.cli.ingestion_commands import ingestion


@click.group()
def cli():
    """E-commerce Intelligence Agent Management CLI"""
    pass


# Register command groups
cli.add_command(ingestion)


if __name__ == '__main__':
    cli()
