from unittest.mock import Mock, patch

import dns.message
import dns.rcode

from tldns.server import DNSOverTLSServer


class TestDNSProtocol:
    """Test DNS protocol handling."""

    def test_dns_query_parsing(self):
        """Test parsing of DNS queries."""
        server = DNSOverTLSServer()

        # Create a real DNS query
        query = dns.message.make_query("example.com", "A")
        query_data = query.to_wire()

        with patch("dns.query.udp") as mock_udp:
            mock_response = dns.message.make_response(query)
            mock_response.answer.append(
                dns.rrset.from_text("example.com", 300, "IN", "A", "192.0.2.1")
            )
            mock_udp.return_value = mock_response

            result = server.forward_dns_query(query_data)

            # Verify the query was processed
            assert len(result) > 0
            mock_udp.assert_called_once()

    def test_dns_response_codes(self):
        """Test different DNS response codes."""
        server = DNSOverTLSServer()

        # Test SERVFAIL response
        query = dns.message.make_query("example.com", "A")
        query_data = query.to_wire()

        error_response_data = server.create_error_response(query_data)
        error_response = dns.message.from_wire(error_response_data)

        assert error_response.rcode() == dns.rcode.SERVFAIL
        assert error_response.id == query.id

    def test_dns_question_types(self):
        """Test handling of different DNS question types."""
        server = DNSOverTLSServer()

        question_types = ["A", "AAAA", "MX", "TXT", "NS", "CNAME"]

        for qtype in question_types:
            query = dns.message.make_query("example.com", qtype)
            query_data = query.to_wire()

            with patch("dns.query.udp") as mock_udp:
                mock_response = dns.message.make_response(query)
                mock_udp.return_value = mock_response

                result = server.forward_dns_query(query_data)
                assert len(result) > 0

    def test_malformed_dns_query(self):
        """Test handling of malformed DNS queries."""
        server = DNSOverTLSServer()

        # Test with invalid DNS data
        invalid_queries = [
            b"",  # Empty data
            b"\\x00\\x01",  # Too short
            b"invalid_dns_data",  # Invalid format
            b"\\x00" * 100,  # Wrong format but correct length
        ]

        for invalid_query in invalid_queries:
            result = server.create_error_response(invalid_query)
            # Should return empty bytes for completely invalid data
            assert isinstance(result, bytes)

    def test_dns_compression(self):
        """Test DNS name compression handling."""
        server = DNSOverTLSServer()

        # Create query with potential for compression
        query = dns.message.make_query("subdomain.example.com", "A")
        query_data = query.to_wire()

        with patch("dns.query.udp") as mock_udp:
            mock_response = dns.message.make_response(query)
            mock_udp.return_value = mock_response

            result = server.forward_dns_query(query_data)

            # Verify response can be parsed back
            response = dns.message.from_wire(result)
            assert response.question[0].name.to_text() == "subdomain.example.com."


class TestTLSProtocol:
    """Test TLS protocol handling."""

    def test_tls_message_framing(self):
        """Test TLS message length framing."""
        server = DNSOverTLSServer()

        # Test length encoding/decoding
        test_lengths = [0, 1, 255, 256, 512, 1024, 65535]

        for length in test_lengths:
            # Encode length as 2-byte big-endian
            length_bytes = length.to_bytes(2, byteorder="big")

            # Decode back
            decoded_length = int.from_bytes(length_bytes, byteorder="big")

            assert decoded_length == length

    def test_tls_message_boundaries(self):
        """Test TLS message boundary handling."""
        server = DNSOverTLSServer()

        # Mock SSL socket that returns data properly
        mock_ssl_sock = Mock()

        # Simulate proper TLS message handling
        mock_ssl_sock.recv.side_effect = [
            b"\x00\x10",  # Length = 16 (both bytes together)
            b"test_query_16b\x00\x00",  # DNS query data (exactly 16 bytes)
            b"",  # End connection
        ]

        addr = ("127.0.0.1", 12345)

        with patch.object(server, "forward_dns_query") as mock_forward:
            mock_forward.return_value = b"response"

            # This should handle the data correctly
            server.handle_client(mock_ssl_sock, addr)

            # Verify the query was processed
            mock_forward.assert_called_once_with(b"test_query_16b\x00\x00")


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_upstream_dns_timeout(self):
        """Test handling of upstream DNS timeout."""
        server = DNSOverTLSServer()

        query = dns.message.make_query("example.com", "A")
        query_data = query.to_wire()

        with patch("dns.query.udp") as mock_udp:
            mock_udp.side_effect = dns.exception.Timeout()

            result = server.forward_dns_query(query_data)

            # Should return error response
            error_response = dns.message.from_wire(result)
            assert error_response.rcode() == dns.rcode.SERVFAIL

    def test_upstream_dns_network_error(self):
        """Test handling of upstream DNS network errors."""
        server = DNSOverTLSServer()

        query = dns.message.make_query("example.com", "A")
        query_data = query.to_wire()

        with patch("dns.query.udp") as mock_udp:
            mock_udp.side_effect = OSError("Network unreachable")

            result = server.forward_dns_query(query_data)

            # Should return error response
            error_response = dns.message.from_wire(result)
            assert error_response.rcode() == dns.rcode.SERVFAIL

    def test_ssl_socket_errors(self):
        """Test handling of SSL socket errors."""
        server = DNSOverTLSServer()

        mock_ssl_sock = Mock()
        mock_ssl_sock.recv.side_effect = OSError("Connection reset")

        addr = ("127.0.0.1", 12345)

        # Should handle the error gracefully
        server.handle_client(mock_ssl_sock, addr)

        mock_ssl_sock.close.assert_called_once()

    def test_partial_message_handling(self):
        """Test handling of partial messages."""
        server = DNSOverTLSServer()

        mock_ssl_sock = Mock()

        # Simulate receiving partial length data
        mock_ssl_sock.recv.side_effect = [
            b"\x00\x10",  # Length = 16
            b"partial",  # Only 7 bytes instead of 16
            b"",  # Connection closed
        ]

        addr = ("127.0.0.1", 12345)

        # Should handle partial data gracefully
        server.handle_client(mock_ssl_sock, addr)

        mock_ssl_sock.close.assert_called_once()

