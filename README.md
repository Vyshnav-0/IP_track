# IP Tracker Tool (Educational Purpose Only)

This tool is designed for educational purposes only. It helps track IP addresses from various file types and sends the results to a Discord webhook.

## Disclaimer

This tool is for educational purposes only. Do not use it for any malicious purposes or unauthorized tracking of IP addresses.

## Requirements

- Python 3.6 or higher
- Internet connection for package installation

## Installation & Running

### Windows Users
Simply double-click `ip_tracker.py` or run from command prompt:
```bash
python ip_tracker.py
```

### Linux/Mac Users
Run the script:
```bash
python3 ip_tracker.py
```

The tool will automatically:
1. Create a virtual environment
2. Install all required dependencies
3. Start the IP Tracker Tool

## Features

- Extracts IP addresses from PDF documents
- Extracts IP addresses from image metadata
- Extracts IP addresses from website content
- Sends results to Discord webhook
- Logging functionality for tracking operations
- Professional command-line interface
- Automatic dependency management
- One-click setup and run

## Usage

The tool supports three types of sources:
- PDF files
- Image files
- Websites

When you run the tool, you'll be prompted to:
1. Enter your Discord webhook URL
2. Choose the type of file to process
3. Provide the file path or URL
4. View the results in your Discord channel

## Note

The tool creates a virtual environment in the `venv` directory. This keeps the dependencies isolated from your system Python installation. 