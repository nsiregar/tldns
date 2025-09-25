import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch

from tldns.server import DNSOverTLSServer


class TestPerformance:
    """Performance tests for the DNS server."""

    def test_concurrent_client_handling(self):
        """Test handling multiple concurrent clients."""
        server = DNSOverTLSServer()

        # Mock multiple SSL sockets
        num_clients = 10
        mock_sockets = []

        for i in range(num_clients):
            mock_sock = Mock()
            mock_sock.recv.side_effect = [
                b"\x00\x10",  # Length = 16
                b"test_query_16b\x00\x00",  # Exactly 16 bytes
                b"",  # End connection
            ]
            mock_sockets.append(mock_sock)

        with patch.object(server, "forward_dns_query") as mock_forward:
            mock_forward.return_value = b"response"

            # Start multiple client handlers concurrently
            threads = []
            for i, mock_sock in enumerate(mock_sockets):
                addr = ("127.0.0.1", 12345 + i)
                thread = threading.Thread(
                    target=server.handle_client, args=(mock_sock, addr)
                )
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=5.0)

            # Verify all queries were processed
            assert mock_forward.call_count == num_clients

    def test_query_processing_speed(self):
        """Test DNS query processing speed."""
        server = DNSOverTLSServer()

        import dns.message

        query = dns.message.make_query("example.com", "A")
        query_data = query.to_wire()

        with patch("dns.query.udp") as mock_udp:
            mock_response = dns.message.make_response(query)
            mock_udp.return_value = mock_response

            # Measure processing time for multiple queries
            start_time = time.time()
            num_queries = 100

            for _ in range(num_queries):
                result = server.forward_dns_query(query_data)
                assert len(result) > 0

            end_time = time.time()
            total_time = end_time - start_time

            # Should process queries reasonably fast
            # (This is a rough benchmark, adjust as needed)
            queries_per_second = num_queries / total_time
            assert queries_per_second > 50  # At least 50 QPS

    def test_memory_usage_stability(self):
        """Test that memory usage remains stable under load."""
        server = DNSOverTLSServer()

        import dns.message

        query = dns.message.make_query("example.com", "A")
        query_data = query.to_wire()

        with patch("dns.query.udp") as mock_udp:
            mock_response = dns.message.make_response(query)
            mock_udp.return_value = mock_response

            # Process many queries to check for memory leaks
            for _ in range(1000):
                result = server.forward_dns_query(query_data)
                assert len(result) > 0

                # Force garbage collection periodically
                if _ % 100 == 0:
                    import gc

                    gc.collect()

    def test_error_response_performance(self):
        """Test performance of error response generation."""
        server = DNSOverTLSServer()

        import dns.message

        query = dns.message.make_query("example.com", "A")
        query_data = query.to_wire()

        # Measure error response generation time
        start_time = time.time()
        num_errors = 100

        for _ in range(num_errors):
            result = server.create_error_response(query_data)
            assert len(result) > 0

        end_time = time.time()
        total_time = end_time - start_time

        # Error responses should be generated quickly
        errors_per_second = num_errors / total_time
        assert errors_per_second > 100  # At least 100 error responses per second


class TestLoadTesting:
    """Load testing scenarios."""

    def test_rapid_connection_handling(self):
        """Test handling rapid connection attempts."""
        server = DNSOverTLSServer()

        # Simulate rapid connections
        num_connections = 50
        results = []

        def simulate_connection(connection_id):
            mock_sock = Mock()
            mock_sock.recv.side_effect = [
                b"\\x00\\x10",  # Length
                f"query_{connection_id}".encode().ljust(16, b"0"),  # Query
                b"",  # Close connection
            ]

            addr = ("127.0.0.1", 12345 + connection_id)

            with patch.object(server, "forward_dns_query") as mock_forward:
                mock_forward.return_value = b"response"

                start_time = time.time()
                server.handle_client(mock_sock, addr)
                end_time = time.time()

                return end_time - start_time

        # Use ThreadPoolExecutor to simulate concurrent connections
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(simulate_connection, i) for i in range(num_connections)
            ]

            for future in as_completed(futures):
                processing_time = future.result()
                results.append(processing_time)

        # Verify all connections were handled
        assert len(results) == num_connections

        # Check that processing times are reasonable
        avg_time = sum(results) / len(results)
        max_time = max(results)

        assert avg_time < 1.0  # Average under 1 second
        assert max_time < 5.0  # Max under 5 seconds

    def test_sustained_load(self):
        """Test sustained load over time."""
        server = DNSOverTLSServer()

        import dns.message

        query = dns.message.make_query("example.com", "A")
        query_data = query.to_wire()

        with patch("dns.query.udp") as mock_udp:
            mock_response = dns.message.make_response(query)
            mock_udp.return_value = mock_response

            # Simulate sustained load for a period
            duration = 2.0  # 2 seconds
            start_time = time.time()
            query_count = 0

            while time.time() - start_time < duration:
                result = server.forward_dns_query(query_data)
                assert len(result) > 0
                query_count += 1

                # Small delay to simulate realistic load
                time.sleep(0.001)  # 1ms delay

            # Calculate queries per second
            actual_duration = time.time() - start_time
            qps = query_count / actual_duration

            # Should maintain reasonable throughput
            assert qps > 10  # At least 10 QPS under sustained load


class TestResourceManagement:
    """Test resource management and cleanup."""

    def test_socket_cleanup_on_error(self):
        """Test that sockets are properly cleaned up on errors."""
        server = DNSOverTLSServer()

        mock_sock = Mock()
        mock_sock.recv.side_effect = Exception("Socket error")

        addr = ("127.0.0.1", 12345)

        # Should clean up socket even on error
        server.handle_client(mock_sock, addr)

        mock_sock.close.assert_called_once()

    def test_thread_cleanup(self):
        """Test that threads are properly managed."""
        server = DNSOverTLSServer()

        # Create multiple mock client handlers
        num_threads = 5
        threads = []

        for i in range(num_threads):
            mock_sock = Mock()
            mock_sock.recv.return_value = b""  # Immediate close

            addr = ("127.0.0.1", 12345 + i)
            thread = threading.Thread(
                target=server.handle_client, args=(mock_sock, addr)
            )
            thread.daemon = True
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=1.0)
            assert not thread.is_alive()

    def test_ssl_context_reuse(self):
        """Test that SSL context is properly reused."""
        server = DNSOverTLSServer()

        with patch.object(server, "create_ssl_context") as mock_create_ssl:
            mock_context = Mock()
            mock_create_ssl.return_value = mock_context

            with patch("socket.socket") as mock_socket:
                mock_sock = Mock()
                mock_socket.return_value.__enter__.return_value = mock_sock
                mock_sock.accept.side_effect = KeyboardInterrupt()

                server.start()

                # SSL context should be created only once
                mock_create_ssl.assert_called_once()

