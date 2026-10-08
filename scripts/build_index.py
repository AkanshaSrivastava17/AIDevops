"""
Build and pre-index all repositories configured in configs/ directory.
Usage: python scripts/build_index.py
"""
import os
import sys
import glob
import yaml
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from rich.console import Console
from app.repository.models import RepositoryConfig
from app.ingestion.core import IngestionPipeline

logging.basicConfig(level=logging.INFO)
console = Console()


def build_all():
    config_files = glob.glob("configs/*.yaml")
    console.print(f"[bold cyan]Found {len(config_files)} configuration files to index.[/bold cyan]")

    for cf in config_files:
        with open(cf, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        config = RepositoryConfig(**data)
        console.print(f"[yellow]Indexing {config.repository_id}...[/yellow]")
        pipeline = IngestionPipeline(config=config)
        res = pipeline.run()
        console.print(
            f"[green]Indexed {config.repository_id}: {res['total_documents_indexed']} documents "
            f"(Mode: {res['profile']['analysis_mode']})[/green]"
        )

    console.print("[bold green]All configured repositories successfully indexed![/bold green]")


if __name__ == "__main__":
    build_all()
