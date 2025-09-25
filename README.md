# tldns - DNS over TLS Server

A DNS over TLS (DoT) server implementation using Python and dnspython with CLI support via Python Fire.

## Features

- DNS over TLS (RFC 7858) support on port 853
- Forwards queries to upstream DNS server (default: 8.8.8.8)
- Multi-threaded client handling
- SSL/TLS encryption
- Command-line interface with configurable parameters
- Structured logging with multiple levels

## Installation

### From source
```bash
git clone git@github.com:nsiregar/tldns.git
cd tldns
uv pip install -e .
```

### Using pip (when published)
```bash
pip install tldns
```

## Setup

1. Generate SSL certificate (for testing):
```bash
./scripts/generate_cert.sh
```

2. Run the server:
```bash
tldns start
```

## Usage

### Basic usage
```bash
# Start with default settings (port 853, upstream 8.8.8.8)
tldns start

# Show help
tldns --help
```

### Configuration options
```bash
# Custom port and upstream DNS
tldns --port 8853 --upstream_dns 1.1.1.1 start

# Custom host binding
tldns --host 127.0.0.1 --port 8853 start

# Custom SSL certificates
tldns --cert_file custom.crt --key_file custom.key start

# Enable debug logging
tldns --log_level DEBUG start

# Quiet mode (errors only)
tldns --log_level ERROR start
```

### Available parameters
- `--host`: Bind address (default: '0.0.0.0')
- `--port`: Port number (default: 853)
- `--cert_file`: SSL certificate file (default: 'server.crt')
- `--key_file`: SSL private key file (default: 'server.key')
- `--upstream_dns`: Upstream DNS server (default: '8.8.8.8')
- `--log_level`: Logging level - DEBUG, INFO, WARNING, ERROR (default: 'INFO')

## Testing

Test with dig:
```bash
dig @127.0.0.1 -p 853 +tls example.com
```

Or with kdig:
```bash
kdig @127.0.0.1 -p 853 +tls example.com
```

## Development

### Running from source
```bash
# Install in development mode
uv pip install -e .

# Run directly from source
python -m tldns.server start
```

### Running tests
```bash
# Install test dependencies
uv pip install -e ".[test]"

# Run all tests
python -m pytest

# Run tests with coverage
python -m pytest --cov=tldns

# Run specific test categories
python -m pytest -m unit
python -m pytest -m integration
python -m pytest -m "not slow"
```

### Test structure
- `tests/test_server.py` - Unit tests for server functionality
- `tests/test_protocol.py` - DNS and TLS protocol tests
- `tests/test_performance.py` - Performance and load tests
- `tests/conftest.py` - Test fixtures and configuration

## Dependencies

- dnspython: DNS library for Python
- fire: Command-line interface generation
