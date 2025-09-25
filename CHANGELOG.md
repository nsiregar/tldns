# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release preparation

## [0.1.0] - 2024-09-25

### Added
- DNS over TLS server implementation
- Command-line interface with Python Fire
- Configurable upstream DNS servers (default: 8.8.8.8)
- SSL/TLS encryption support
- Multi-threaded client handling
- Comprehensive logging with configurable levels
- Type hints throughout codebase
- Comprehensive test suite with 96% coverage
- Performance and load testing
- Cross-platform support (Linux, Windows, macOS)
- Installable Python package with hatchling
- GitHub Actions CI/CD workflows
- Automated releases and PyPI publishing

### Features
- RFC 7858 DNS over TLS compliance
- Configurable bind address and port
- Custom SSL certificate support
- Error handling with SERVFAIL responses
- Connection lifecycle logging
- Query tracking and statistics

### Testing
- Unit tests for all major components
- Protocol compliance tests
- Performance and concurrency tests
- Mock-based testing for network components
- Coverage reporting with pytest-cov

### Documentation
- Comprehensive README with usage examples
- API documentation with docstrings
- GitHub Actions workflow documentation
- Installation and development guides