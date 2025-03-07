# IP Tracker Tool (Educational Purpose Only)

This tool is designed for educational purposes only. It helps track IP addresses from various file types and sends the results to a Discord webhook.

## Disclaimer

This tool is for educational purposes only. Do not use it for any malicious purposes or unauthorized tracking of IP addresses.

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

The tool supports three types of sources:
- PDF files
- Image files
- Websites

### Basic Usage

```bash
python ip_tracker.py --webhook YOUR_DISCORD_WEBHOOK_URL --type [pdf|img|website] --source [FILE_PATH|URL]
```

### Examples

1. For PDF files:
```bash
python ip_tracker.py --webhook https://discord.com/api/webhooks/... --type pdf --source document.pdf
```

2. For Image files:
```bash
python ip_tracker.py --webhook https://discord.com/api/webhooks/... --type img --source image.jpg
```

3. For Websites:
```bash
python ip_tracker.py --webhook https://discord.com/api/webhooks/... --type website --source https://example.com
```

## Features

- Extracts IP addresses from PDF documents
- Extracts IP addresses from image metadata
- Extracts IP addresses from website content
- Sends results to Discord webhook
- Logging functionality for tracking operations

## Requirements

- Python 3.6 or higher
- Required packages listed in requirements.txt
- Discord webhook URL 