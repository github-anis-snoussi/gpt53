#!/usr/bin/env python3
"""
Setup script for DNS Chat Client
"""

from setuptools import setup, find_packages

long_description = """
# DNS Chat Client

A Python client for communicating with DNS-based LLM chat servers. This client provides both command-line and interactive modes for chatting with AI models through DNS TXT record queries.

## Quick Start

```bash
# Install the package
pip install dns-chat-client

# Test connectivity
gpt53 ping

# Start interactive mode
gpt53 --api-key YOUR_10_CHAR_KEY interactive

# Connect to custom server
gpt53 --host 192.168.1.100 --port 5353 ping
```

## Usage

The client works with DNS servers that implement the GPT-53 protocol for authenticated LLM chat over DNS.

For complete documentation, visit: https://github.com/github-anis-snoussi/gpt53
"""

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="dns-chat-client",
    version="1.0.0",
    author="Anis Snoussi",
    author_email="anis@snoussi.me",
    description="A Python client for DNS-based LLM chat",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/github-anis-snoussi/gpt53",
    py_modules=["dns_chat"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "gpt53=dns_chat:cli",
        ],
    },
)