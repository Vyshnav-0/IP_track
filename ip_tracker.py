#!/usr/bin/env python3
import os
import sys
import requests
import PyPDF2
from PIL import Image
import io
import re
import argparse
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IPTracker:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'

    def extract_ips_from_text(self, text):
        """Extract IP addresses from text using regex."""
        return re.findall(self.ip_pattern, text)

    def send_to_discord(self, ips, source):
        """Send extracted IPs to Discord webhook."""
        if not ips:
            message = f"No IP addresses found in {source}"
        else:
            message = f"IP addresses found in {source}:\n" + "\n".join(ips)
        
        payload = {"content": message}
        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            logger.info(f"Successfully sent results to Discord for {source}")
        except Exception as e:
            logger.error(f"Failed to send to Discord: {str(e)}")

    def process_pdf(self, file_path):
        """Extract IPs from PDF file."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                ips = self.extract_ips_from_text(text)
                self.send_to_discord(ips, f"PDF: {file_path}")
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")

    def process_image(self, file_path):
        """Extract IPs from image metadata."""
        try:
            with Image.open(file_path) as img:
                # Extract metadata
                metadata = img.info
                text = str(metadata)
                ips = self.extract_ips_from_text(text)
                self.send_to_discord(ips, f"Image: {file_path}")
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {str(e)}")

    def process_website(self, url):
        """Extract IPs from website content."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            ips = self.extract_ips_from_text(response.text)
            self.send_to_discord(ips, f"Website: {url}")
        except Exception as e:
            logger.error(f"Error processing website {url}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='IP Tracker Tool for Educational Purposes')
    parser.add_argument('--webhook', required=True, help='Discord webhook URL')
    parser.add_argument('--type', choices=['pdf', 'img', 'website'], required=True, help='Type of file to process')
    parser.add_argument('--source', required=True, help='File path or URL to process')
    
    args = parser.parse_args()
    
    tracker = IPTracker(args.webhook)
    
    if args.type == 'pdf':
        tracker.process_pdf(args.source)
    elif args.type == 'img':
        tracker.process_image(args.source)
    elif args.type == 'website':
        tracker.process_website(args.source)

if __name__ == "__main__":
    main() 