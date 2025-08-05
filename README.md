<div align="center">
  <img src="gpt.png" alt="GPT53 Plane" width="400">
    <h3>🤖 GPT-53</h3>
  <p>Authenticated LLM Chat over DNS</p>
</div>

---

# GPT-53: DNS-based LLM Chat System

A complete system for chatting with Large Language Models (LLMs) through DNS TXT record queries. Includes a TypeScript DNS server and Python client for secure, authenticated AI conversations.

## Usage

### DNS Query Format

Predefined Endpoints (no authentication):
- `PING` → Returns `PONG`
- `LIST` → Returns available models

Chat Format: `[10-char API key][1-char model index][user prompt]`

### Direct DNS Queries

```bash
# Test server connectivity
dig @127.0.0.1 -p5333 TXT "PING"

# Get available models
dig @127.0.0.1 -p5333 TXT "LIST"

# Chat examples (API key: my-api-key, and using Model 0)
dig @127.0.0.1 -p5333 TXT "my-api-key0What is AI?"
dig @127.0.0.1 -p5333 TXT "my-api-key0Tell me a programming joke"
dig @127.0.0.1 -p5333 TXT "my-api-key0How do I center a div in CSS?"
```

### Python Client Usage

#### Python client

```bash
# Call using python
python dns_chat.py ping

# Or install it for direct use
pip install -e .
gpt53 ping

# Example usage
gpt53 --api-key my-api-key --host 127.0.0.1 --port 5333 interactive
```

#### Available Commands

- `ping`: Test server connectivity
- `list`: List available AI models  
- `interactive`: Start interactive chat mode

#### Client Options

- `--host TEXT`: DNS server host (default: 127.0.0.1)
- `--port INTEGER`: DNS server port (default: 5333)
- `--api-key TEXT`: 10-character API key for authentication (required for interactive mode)

## 🔑 API Key Generation

Generate a secure 10-character API key:

```bash
# OpenSSL
openssl rand -base64 32 | tr -d "=+/" | cut -c1-10
```

💡 This should be set in the server's `API_KEY` and set by the client when requestion a chat generation.
