# DNS Server (TXT Records Only)

A simple TypeScript DNS server built with [dns2](https://www.npmjs.com/package/dns2) that responds only to TXT record queries.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Edit `.env` to configure your server settings.

## Configuration

The server can be configured using environment variables in a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `53` | Port number for the DNS server |
| `HOST` | `127.0.0.1` | Host/IP address to bind to |
| `DEFAULT_TXT_RESPONSE` | `v=spf1 include:_spf.google.com ~all` | Default TXT record response |
| `DNS_TTL` | `300` | Time To Live for DNS responses (seconds) |
| `ENABLE_LOGGING` | `true` | Enable/disable request logging |

## Running the Server

### Development
```bash
npm run dev
```

### Production
```bash
npm run build
npm start
```

### Watch Mode
```bash
npm run watch
```

## Testing

Test your DNS server using the `dig` command:

```bash
# Test TXT record (this will work)
dig @127.0.0.1 -p5353 TXT example.com

# Test different domains
dig @127.0.0.1 -p5353 TXT mydomain.com
dig @127.0.0.1 -p5353 TXT test.example.org

# Other record types will return empty responses
dig @127.0.0.1 -p5353 A example.com     # No response
dig @127.0.0.1 -p5353 MX example.com    # No response
```

## Notes

- **TXT Only**: This server ONLY responds to TXT record queries
- **Other Records**: A, AAAA, MX, CNAME, and other record types will receive empty responses
- **Port 53**: The default DNS port (53) requires administrator privileges on most systems
- **Development**: Use port 5353 or higher for development to avoid privilege issues
- **Binding**: Use `HOST=0.0.0.0` to accept connections from any IP address
- **Logging**: Set `ENABLE_LOGGING=false` to disable request logging

## Example TXT Responses

You can configure different TXT responses by setting `DEFAULT_TXT_RESPONSE`:

```bash
# SPF record
DEFAULT_TXT_RESPONSE="v=spf1 include:_spf.google.com ~all"

# Domain verification
DEFAULT_TXT_RESPONSE="google-site-verification=abc123def456"

# Custom text
DEFAULT_TXT_RESPONSE="This is my custom DNS response"
```

## Features

- ✅ UDP and TCP support
- ✅ TXT record responses only
- ✅ Configurable TXT response content
- ✅ Configurable via environment variables
- ✅ Request logging
- ✅ Graceful shutdown
- ✅ TypeScript support
- ✅ Ignores non-TXT queries (returns empty response) 