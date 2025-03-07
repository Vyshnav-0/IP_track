#!/usr/bin/env python3
import os
import sys
import subprocess
import venv
from pathlib import Path
import requests
import PyPDF2
from PIL import Image
import re
import logging
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
console = Console()

def setup_environment():
    """Set up the virtual environment and install requirements."""
    try:
        venv_path = Path("venv")
        if not venv_path.exists():
            console.print("[yellow]Creating virtual environment...[/yellow]")
            venv.create("venv", with_pip=True)
        
        python_executable = "venv\\Scripts\\python.exe" if sys.platform == "win32" else "venv/bin/python"
        console.print("[yellow]Checking and installing required packages...[/yellow]")
        subprocess.check_call([python_executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True
    except Exception as e:
        console.print(f"[red]Error during setup: {str(e)}[/red]")
        return False

class IPTracker:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'

    def extract_ips_from_text(self, text):
        return re.findall(self.ip_pattern, text)

    def send_to_discord(self, ips, source):
        message = f"No IP addresses found in {source}" if not ips else f"IP addresses found in {source}:\n" + "\n".join(ips)
        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
                progress.add_task("Sending to Discord...", total=None)
                response = requests.post(self.webhook_url, json={"content": message})
                response.raise_for_status()
                logger.info(f"Successfully sent results to Discord for {source}")
        except Exception as e:
            logger.error(f"Failed to send to Discord: {str(e)}")
            console.print(f"[red]Error sending to Discord: {str(e)}[/red]")

    def process_pdf(self, file_path):
        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
                progress.add_task("Processing PDF...", total=None)
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = "".join(page.extract_text() for page in pdf_reader.pages)
                    self.send_to_discord(self.extract_ips_from_text(text), f"PDF: {file_path}")
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")
            console.print(f"[red]Error processing PDF: {str(e)}[/red]")

    def process_image(self, file_path):
        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
                progress.add_task("Processing Image...", total=None)
                with Image.open(file_path) as img:
                    self.send_to_discord(self.extract_ips_from_text(str(img.info)), f"Image: {file_path}")
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {str(e)}")
            console.print(f"[red]Error processing image: {str(e)}[/red]")

    def process_website(self, url):
        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
                progress.add_task("Processing Website...", total=None)
                response = requests.get(url)
                response.raise_for_status()
                self.send_to_discord(self.extract_ips_from_text(response.text), f"Website: {url}")
        except Exception as e:
            logger.error(f"Error processing website {url}: {str(e)}")
            console.print(f"[red]Error processing website: {str(e)}[/red]")

def get_webhook_url():
    while True:
        webhook_url = Prompt.ask("\n[bold blue]Enter your Discord webhook URL[/bold blue]")
        if webhook_url.startswith('https://discord.com/api/webhooks/'):
            return webhook_url
        console.print("[red]Invalid webhook URL. Please enter a valid Discord webhook URL.[/red]")

def show_menu():
    console.clear()
    console.print(Panel.fit(
        "[bold blue]IP Tracker Tool[/bold blue]\n"
        "[italic]Educational Purpose Only[/italic]",
        title="Welcome",
        border_style="blue"
    ))
    
    table = Table(show_header=False, box=None)
    table.add_row("1", "Process PDF file")
    table.add_row("2", "Process Image file")
    table.add_row("3", "Process Website")
    table.add_row("4", "Exit")
    console.print(table)
    
    while True:
        try:
            choice = Prompt.ask("\n[bold blue]Enter your choice[/bold blue]", choices=["1", "2", "3", "4"])
            return int(choice)
        except ValueError:
            console.print("[red]Please enter a valid number.[/red]")

def main():
    if not setup_environment():
        console.print("[red]Failed to set up the environment. Please check your Python installation and try again.[/red]")
        sys.exit(1)
    
    console.clear()
    console.print(Panel.fit(
        "[bold blue]Welcome to IP Tracker Tool![/bold blue]\n"
        "[italic]This tool is for educational purposes only.[/italic]",
        title="Disclaimer",
        border_style="blue"
    ))
    
    webhook_url = get_webhook_url()
    tracker = IPTracker(webhook_url)
    
    while True:
        choice = show_menu()
        
        if choice == 1:
            file_path = Prompt.ask("\n[bold blue]Enter the path to your PDF file[/bold blue]")
            if os.path.exists(file_path) and file_path.lower().endswith('.pdf'):
                tracker.process_pdf(file_path)
            else:
                console.print("[red]Invalid PDF file path or file does not exist.[/red]")
        
        elif choice == 2:
            file_path = Prompt.ask("\n[bold blue]Enter the path to your image file[/bold blue]")
            if os.path.exists(file_path):
                tracker.process_image(file_path)
            else:
                console.print("[red]Invalid image file path or file does not exist.[/red]")
        
        elif choice == 3:
            url = Prompt.ask("\n[bold blue]Enter the website URL[/bold blue]")
            if url.startswith(('http://', 'https://')):
                tracker.process_website(url)
            else:
                console.print("[red]Invalid URL. Please enter a valid URL starting with http:// or https://[/red]")
        
        elif choice == 4:
            console.print(Panel.fit(
                "[bold green]Thank you for using IP Tracker Tool![/bold green]",
                title="Goodbye",
                border_style="green"
            ))
            break
        
        if Confirm.ask("\n[bold blue]Do you want to continue?[/bold blue]"):
            continue
        break

if __name__ == "__main__":
    main() 