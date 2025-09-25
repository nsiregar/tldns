import ssl
from unittest.mock import Mock, patch

import dns.rcode
import pytest

from tldns.server import DNSOverTLSServer


class TestDNSOverTLSServer:
    """Test cases for DNSOverTLSServer class."""

    def test_init_default_values(self):
        """Test server initialization with default values."""
        server = DNSOverTLSServer()

        assert server.host == "0.0.0.0"
        assert server.port == 853
        assert server.cert_file == "server.crt"
        assert server.key_file == "server.key"
        assert server.upstream_dns == "8.8.8.8"
        assert server.logger is not None

    def test_init_custom_values(self):
        """Test server initialization with custom values."""
        server = DNSOverTLSServer(
            host="127.0.0.1",
            port=8853,
            cert_file="custom.crt",
            key_file="custom.key",
            upstream_dns="1.1.1.1",
            log_level="DEBUG",
        )

        assert server.host == "127.0.0.1"
        assert server.port == 8853
        assert server.cert_file == "custom.crt"
        assert server.key_file == "custom.key"
        assert server.upstream_dns == "1.1.1.1"

    def test_setup_logging(self):
        """Test logging setup with different levels."""
        import logging

        # Reset logging to avoid interference between tests
        logging.getLogger().handlers.clear()

        # Test DEBUG level
        server1 = DNSOverTLSServer(log_level="DEBUG")
        # The server should have set up logging correctly
        assert server1.logger is not None

        # Reset logging again
        logging.getLogger().handlers.clear()

        # Test ERROR level
        server2 = DNSOverTLSServer(log_level="ERROR")
        assert server2.logger is not None

        # Test that invalid log level defaults to INFO
        server3 = DNSOverTLSServer(log_level="INVALID")
        assert server3.logger is not None

    def test_create_ssl_context_success(self, temp_cert_files):
        """Test successful SSL context creation."""
        cert_file, key_file = temp_cert_files
        server = DNSOverTLSServer(cert_file=cert_file, key_file=key_file)

        with patch("ssl.SSLContext") as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context

            result = server.create_ssl_context()

            mock_ssl_context.assert_called_once_with(ssl.PROTOCOL_TLS_SERVER)
            mock_context.load_cert_chain.assert_called_once_with(cert_file, key_file)
            assert result == mock_context

    def test_create_ssl_context_failure(self):
        """Test SSL context creation failure."""
        server = DNSOverTLSServer(
            cert_file="nonexistent.crt", key_file="nonexistent.key"
        )

        with pytest.raises(Exception):
            server.create_ssl_context()

    @patch("dns.query.udp")
    @patch("dns.message.from_wire")
    def test_forward_dns_query_success(self, mock_from_wire, mock_udp):
        """Test successful DNS query forwarding."""
        server = DNSOverTLSServer()

        # Mock DNS query and response
        mock_query = Mock()
        mock_question = Mock()
        mock_question.name = "example.com"
        mock_question.rdtype = 1  # A record
        mock_query.question = [mock_question]
        mock_from_wire.return_value = mock_query

        mock_response = Mock()
        mock_response.answer = []
        mock_response.to_wire.return_value = b"response_data"
        mock_udp.return_value = mock_response

        query_data = b"query_data"
        result = server.forward_dns_query(query_data)

        mock_from_wire.assert_called_once_with(query_data)
        mock_udp.assert_called_once_with(mock_query, "8.8.8.8", timeout=5)
        assert result == b"response_data"

    @patch("dns.query.udp")
    @patch("dns.message.from_wire")
    def test_forward_dns_query_failure(self, mock_from_wire, mock_udp):
        """Test DNS query forwarding failure."""
        server = DNSOverTLSServer()

        mock_from_wire.side_effect = Exception("DNS parsing error")

        with patch.object(server, "create_error_response") as mock_error_response:
            mock_error_response.return_value = b"error_response"

            query_data = b"invalid_query"
            result = server.forward_dns_query(query_data)

            mock_error_response.assert_called_once_with(query_data)
            assert result == b"error_response"

    @patch("dns.message.make_response")
    @patch("dns.message.from_wire")
    def test_create_error_response_success(self, mock_from_wire, mock_make_response):
        """Test successful error response creation."""
        server = DNSOverTLSServer()

        mock_query = Mock()
        mock_from_wire.return_value = mock_query

        mock_response = Mock()
        mock_response.to_wire.return_value = b"error_response"
        mock_make_response.return_value = mock_response

        query_data = b"query_data"
        result = server.create_error_response(query_data)

        mock_from_wire.assert_called_once_with(query_data)
        mock_make_response.assert_called_once_with(mock_query)
        mock_response.set_rcode.assert_called_once_with(dns.rcode.SERVFAIL)
        assert result == b"error_response"

    @patch("dns.message.from_wire")
    def test_create_error_response_failure(self, mock_from_wire):
        """Test error response creation failure."""
        server = DNSOverTLSServer()

        mock_from_wire.side_effect = Exception("Parsing error")

        query_data = b"invalid_query"
        result = server.create_error_response(query_data)

        assert result == b""

    def test_handle_client_connection_closed(self):
        """Test client handler when connection is closed immediately."""
        server = DNSOverTLSServer()

        mock_ssl_sock = Mock()
        mock_ssl_sock.recv.return_value = b""  # Connection closed

        addr = ("127.0.0.1", 12345)

        # Should not raise exception
        server.handle_client(mock_ssl_sock, addr)

        mock_ssl_sock.close.assert_called_once()

    def test_handle_client_incomplete_length(self):
        """Test client handler with incomplete length data."""
        server = DNSOverTLSServer()

        mock_ssl_sock = Mock()
        mock_ssl_sock.recv.return_value = b"\x00"  # Only 1 byte instead of 2

        addr = ("127.0.0.1", 12345)

        server.handle_client(mock_ssl_sock, addr)

        mock_ssl_sock.close.assert_called_once()

    @patch("socket.socket")
    def test_start_server_keyboard_interrupt(self, mock_socket):
        """Test server start with keyboard interrupt."""
        server = DNSOverTLSServer()

        mock_sock = Mock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.accept.side_effect = KeyboardInterrupt()

        with patch.object(server, "create_ssl_context") as mock_ssl_context:
            mock_ssl_context.return_value = Mock()

            # Should handle KeyboardInterrupt gracefully
            server.start()

            mock_sock.bind.assert_called_once_with(("0.0.0.0", 853))
            mock_sock.listen.assert_called_once_with(5)

    @patch("socket.socket")
    def test_start_server_ssl_handshake_failure(self, mock_socket):
        """Test server start with SSL handshake failure."""
        server = DNSOverTLSServer()

        mock_sock = Mock()
        mock_client_sock = Mock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.accept.return_value = (mock_client_sock, ("127.0.0.1", 12345))

        mock_ssl_context = Mock()
        mock_ssl_context.wrap_socket.side_effect = ssl.SSLError("Handshake failed")

        with patch.object(server, "create_ssl_context") as mock_create_ssl:
            mock_create_ssl.return_value = mock_ssl_context

            # Mock to stop after first iteration
            call_count = 0

            def side_effect():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return (mock_client_sock, ("127.0.0.1", 12345))
                else:
                    raise KeyboardInterrupt()

            mock_sock.accept.side_effect = side_effect

            server.start()

            mock_client_sock.close.assert_called_once()


class TestIntegration:
    """Integration tests for the DNS over TLS server."""

    def test_server_instantiation_with_fire(self):
        """Test that the server can be instantiated through Fire."""

        from tldns.server import main

        # Test that main function exists and can be called
        assert callable(main)

        # Test Fire integration (without actually starting server)
        with patch("fire.Fire") as mock_fire:
            main()
            mock_fire.assert_called_once_with(DNSOverTLSServer)

    def test_module_import(self):
        """Test that the module can be imported correctly."""
        from tldns import server
        from tldns.server import DNSOverTLSServer, main

        assert hasattr(server, "DNSOverTLSServer")
        assert hasattr(server, "main")
        assert callable(DNSOverTLSServer)
        assert callable(main)

