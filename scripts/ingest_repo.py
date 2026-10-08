"""
CLI script to ingest and index a repository into SQLite and ChromaDB.
Usage: python scripts/ingest_repo.py --repo netbox
"""
import os
import sys
import argparse
import logging
import yaml

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from rich.console import Console
from rich.table import Table

from app.repository.models import RepositoryConfig
from app.ingestion.core import IngestionPipeline

logging.basicConfig(level=logging.INFO)
console = Console()


def main():
    parser = argparse.ArgumentParser(description="Ingest and index repository.")
    parser.add_argument("--repo", default="netbox", help="Repository ID (e.g. netbox, fastapi_demo, requests_demo)")
    parser.add_argument("--config", default=None, help="Path to config YAML")
    args = parser.parse_args()

    config_path = args.config or os.path.join("configs", f"{args.repo}.yaml")
    if not os.path.exists(config_path):
        console.print(f"[bold red]Config not found at {config_path}[/bold red]")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
    config = RepositoryConfig(**config_data)

    console.print(f"[bold blue]Starting ingestion for {config.name or config.repository_id}...[/bold blue]")
    pipeline = IngestionPipeline(config=config)
    result = pipeline.run()

    # Display Profile Card
    profile = result["profile"]
    table = Table(title=f"Repository Profile Card: {profile['repository_id']}")
    table.add_column("Attribute", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Language", profile["language"])
    table.add_row("Test Framework", profile.get("test_framework") or "Generic")
    table.add_row("Analysis Mode", f"[bold green]{profile['analysis_mode']}[/bold green]")
    table.add_row("Git History Available", "Yes" if profile["git_history"] else "No")
    table.add_row("Issues Available", "Yes" if profile["issues"] else "No")
    table.add_row("PRs Available", "Yes" if profile["prs"] else "No")
    table.add_row("Tests Found", "Yes" if profile["tests"] else "No")
    table.add_row("Python AST Capable", "Yes" if profile["python_ast"] else "No")
    table.add_row("Import Analysis Capable", "Yes" if profile["import_analysis"] else "No")
    table.add_row("Discovered Components", ", ".join(profile["discovered_components"]))
    table.add_row("Total Documents Indexed", str(result["total_documents_indexed"]))
    table.add_row("Dependencies Linked", str(result["dependencies_recorded"]))
    
    console.print(table)
    console.print(f"[green]Ingestion completed successfully for {args.repo}.[/green]")


if __name__ == "__main__":
    main()
