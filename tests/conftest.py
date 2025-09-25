import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_cert_files():
    """Create temporary SSL certificate files for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cert_file = Path(temp_dir) / "test.crt"
        key_file = Path(temp_dir) / "test.key"

        # Create minimal self-signed cert for testing
        cert_content = """-----BEGIN CERTIFICATE-----
MIIBkTCB+wIJAK5J5J5J5J5JMA0GCSqGSIb3DQEBCwUAMBQxEjAQBgNVBAMMCWxv
Y2FsaG9zdDAeFw0yNDA5MjUwMDAwMDBaFw0yNTA5MjUwMDAwMDBaMBQxEjAQBgNV
BAMMCWxvY2FsaG9zdDBcMA0GCSqGSIb3DQEBAQUAA0sAMEgCQQC5J5J5J5J5J5J5
J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5
J5J5AgMBAAEwDQYJKoZIhvcNAQELBQADQQA5J5J5J5J5J5J5J5J5J5J5J5J5J5J5
J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5J5
-----END CERTIFICATE-----"""

        key_content = """-----BEGIN PRIVATE KEY-----
MIIBVAIBADANBgkqhkiG9w0BAQEFAASCAT4wggE6AgEAAkEAuSeSeSeSeSeSeSeS
eSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeS
eQIDAQABAkEAuSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeS
eSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeS
eQIhALknknknknknknknknknknknknknknknknknknknknknknknknknknknknknkn
AiEAuSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeS
eQIhALknknknknknknknknknknknknknknknknknknknknknknknknknknknknknkn
AiEAuSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeSeS
eQIgALknknknknknknknknknknknknknknknknknknknknknknknknknknknknknk
-----END PRIVATE KEY-----"""

        cert_file.write_text(cert_content)
        key_file.write_text(key_content)

        yield str(cert_file), str(key_file)


@pytest.fixture
def mock_dns_server():
    """Mock DNS server for testing."""
    import socket
    import threading

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("127.0.0.1", 0))
    port = server_socket.getsockname()[1]

    def handle_requests():
        while True:
            try:
                data, addr = server_socket.recvfrom(1024)
                # Simple DNS response (minimal)
                response = data[:2] + b"\x81\x80" + data[4:]  # Set response flag
                server_socket.sendto(response, addr)
            except:
                break

    thread = threading.Thread(target=handle_requests, daemon=True)
    thread.start()

    yield f"127.0.0.1:{port}"

    server_socket.close()
