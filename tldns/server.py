#!/usr/bin/env python3

import socket
import ssl
import threading
import logging
from typing import Tuple

import dns.message
import dns.query
import dns.rcode
import fire


class DNSOverTLSServer:
    """DNS over TLS server that forwards queries to upstream DNS servers."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 853,
        cert_file: str = "server.crt",
        key_file: str = "server.key",
        upstream_dns: str = "8.8.8.8",
        log_level: str = "INFO",
    ):
        self.host: str = host
        self.port: int = port
        self.cert_file: str = cert_file
        self.key_file: str = key_file
        self.upstream_dns: str = upstream_dns

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self._setup_logging(log_level)

    def _setup_logging(self, log_level: str) -> None:
        """Setup logging configuration."""
        level = getattr(logging, log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for TLS connections."""
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(self.cert_file, self.key_file)

            self.logger.info(
                f"SSL context created with cert: {self.cert_file}, key: {self.key_file}"
            )
            return context
        except Exception as e:
            self.logger.error(f"Failed to create SSL context: {e}")
            raise

    def forward_dns_query(self, query_data: bytes) -> bytes:
        """Forward DNS query to upstream server."""
        try:
            query = dns.message.from_wire(query_data)
            question = query.question[0] if query.question else None
            query_name = question.name if question else "unknown"
            query_type = question.rdtype if question else "unknown"

            self.logger.debug(
                f"Forwarding query: {query_name} {query_type} to {self.upstream_dns}"
            )

            response = dns.query.udp(query, self.upstream_dns, timeout=5)

            self.logger.debug(
                f"Received response for {query_name} {query_type}: {len(response.answer)} answers"
            )
            return response.to_wire()
        except Exception as e:
            self.logger.warning(f"Error forwarding DNS query: {e}")
            return self.create_error_response(query_data)

    def create_error_response(self, query_data: bytes) -> bytes:
        """Create SERVFAIL response for failed queries."""
        try:
            query = dns.message.from_wire(query_data)
            response = dns.message.make_response(query)
            response.set_rcode(dns.rcode.SERVFAIL)
            self.logger.debug("Created SERVFAIL response")
            return response.to_wire()
        except Exception as e:
            self.logger.error(f"Failed to create error response: {e}")
            return b""

    def handle_client(self, ssl_sock: ssl.SSLSocket, addr: Tuple[str, int]) -> None:
        """Handle individual client connections."""
        self.logger.info(f"New connection from {addr[0]}:{addr[1]}")
        query_count = 0

        try:
            while True:
                length_data = ssl_sock.recv(2)
                if not length_data:
                    break

                if len(length_data) < 2:
                    self.logger.warning(
                        f"Incomplete length data from {addr[0]}:{addr[1]}"
                    )
                    break

                query_length = int.from_bytes(length_data, byteorder="big")
                self.logger.debug(
                    f"Expecting {query_length} bytes from {addr[0]}:{addr[1]}"
                )

                query_data: bytes = b""
                while len(query_data) < query_length:
                    chunk = ssl_sock.recv(query_length - len(query_data))
                    if not chunk:
                        break
                    query_data += chunk

                if len(query_data) != query_length:
                    self.logger.warning(
                        f"Incomplete query data from {addr[0]}:{addr[1]} (expected {query_length}, got {len(query_data)})"
                    )
                    break

                query_count += 1
                response_data: bytes = self.forward_dns_query(query_data)

                response_length: bytes = len(response_data).to_bytes(2, byteorder="big")
                ssl_sock.send(response_length + response_data)

                self.logger.debug(
                    f"Sent {len(response_data)} byte response to {addr[0]}:{addr[1]}"
                )

        except Exception as e:
            self.logger.error(f"Error handling client {addr[0]}:{addr[1]}: {e}")
        finally:
            ssl_sock.close()
            self.logger.info(
                f"Connection closed for {addr[0]}:{addr[1]} (processed {query_count} queries)"
            )

    def start(self) -> None:
        """Start the DNS over TLS server."""
        self.logger.info(f"Starting DNS over TLS server on {self.host}:{self.port}")
        self.logger.info(f"Upstream DNS server: {self.upstream_dns}")

        context: ssl.SSLContext = self.create_ssl_context()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, self.port))
            sock.listen(5)

            self.logger.info(
                f"DNS over TLS server listening on {self.host}:{self.port}"
            )

            try:
                while True:
                    client_sock: socket.socket
                    addr: Tuple[str, int]
                    client_sock, addr = sock.accept()

                    try:
                        ssl_sock: ssl.SSLSocket = context.wrap_socket(
                            client_sock, server_side=True
                        )
                    except Exception as e:
                        self.logger.error(
                            f"SSL handshake failed for {addr[0]}:{addr[1]}: {e}"
                        )
                        client_sock.close()
                        continue

                    client_thread: threading.Thread = threading.Thread(
                        target=self.handle_client, args=(ssl_sock, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()

            except KeyboardInterrupt:
                self.logger.info("Received shutdown signal, stopping server...")


def main():
    """Entry point for the tldns command."""
    fire.Fire(DNSOverTLSServer)
