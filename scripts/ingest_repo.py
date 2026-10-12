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
from app.repository.adapter import parse_github_url
from app.ingestion.core import IngestionPipeline

logging.basicConfig(level=logging.INFO)
console = Console()


def main():
    parser = argparse.ArgumentParser(description="Ingest and index repository.")
    parser.add_argument("--repo", default=None, help="Repository ID (e.g. netbox, fastapi_demo, requests_demo)")
    parser.add_argument("--url", default=None, help="GitHub or Git repository URL to clone and index")
    parser.add_argument("--config", default=None, help="Path to config YAML")
    args = parser.parse_args()

    repo_id = args.repo
    repo_url = args.url

    if repo_url and not repo_id:
        _, _, repo_id = parse_github_url(repo_url)
    elif not repo_id and not repo_url:
        repo_id = "netbox"

    config_path = args.config or os.path.join("configs", f"{repo_id}.yaml")
    
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        config = RepositoryConfig(**config_data)
        if repo_url:
            config.repository_url = repo_url
    else:
        # Create config dynamically from URL or repo_id
        config = RepositoryConfig(
            repository_id=repo_id,
            name=repo_id.replace("_", " ").title(),
            repository_url=repo_url or f"https://github.com/unknown/{repo_id}",
            description=f"Repository {repo_id}"
        )
        os.makedirs("configs", exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config.model_dump(), f)
        console.print(f"[green]Created repository configuration: {config_path}[/green]")

    console.print(f"[bold blue]Starting ingestion for {config.name or config.repository_id} ({config.repository_url})...[/bold blue]")
    pipeline = IngestionPipeline(config=config)
    result = pipeline.run()

    # Display Profile Card
    profile = result["profile"]
    table = Table(title=f"Repository Profile Card: {profile['repository_id']}")
    table.add_column("Attribute", style="cyan")
    table.add_column("Value", style="magenta")

    mode_val = profile['analysis_mode'].value if hasattr(profile['analysis_mode'], 'value') else str(profile['analysis_mode'])
    table.add_row("Language", profile["language"])
    table.add_row("Test Framework", profile.get("test_framework") or "Generic")
    table.add_row("Analysis Mode", f"[bold green]{mode_val}[/bold green]")
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
    console.print(f"[green]Ingestion completed successfully for {config.name or config.repository_id}.[/green]")


if __name__ == "__main__":
    main()
