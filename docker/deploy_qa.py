"""
QA Deployment and Health Check script.
Automates candidate image deployment and verifies the GET /health gate.
Used in GitHub Actions CI step 9 and 10 (Section 13, 13.1, 13.3).
"""
import time
import argparse
import logging
import requests
import subprocess
from rich.console import Console

console = Console()
logging.basicConfig(level=logging.INFO)


def check_health(url: str = "http://localhost:8000/health", max_retries: int = 15, delay: int = 2) -> bool:
    console.print(f"[bold cyan]Checking QA Health Check at {url}...[/bold cyan]")
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                console.print(f"[bold green]✓ QA Health Check PASSED on attempt {attempt}:[/bold green]")
                console.print(f"  Service: {data.get('service')} | Status: {data.get('status')} | Version: {data.get('version')}")
                return True
            else:
                console.print(f"[yellow]Attempt {attempt}: returned HTTP {resp.status_code}, retrying...[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Attempt {attempt}: connection failed ({e}), retrying in {delay}s...[/yellow]")
        time.sleep(delay)

    console.print("[bold red]✗ QA Health Check FAILED after max retries.[/bold red]")
    return False


def main():
    parser = argparse.ArgumentParser(description="QA Deployment and Verification")
    parser.add_argument("--url", default="http://localhost:8000/health", help="Health check endpoint URL")
    parser.add_argument("--retries", type=int, default=10, help="Max retry attempts")
    args = parser.parse_args()

    success = check_health(url=args.url, max_retries=args.retries)
    if not success:
        exit(1)
    console.print("[bold green]QA deployment verified healthy. Ready for validation.[/bold green]")


if __name__ == "__main__":
    main()
