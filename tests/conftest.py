"""
Pytest configuration and fixtures for the test suite.
"""

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests requiring API keys"
    )
    config.addinivalue_line("markers", "slow: marks tests as slow running tests")


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests (requires API keys)",
    )


def pytest_collection_modifyitems(config, items):
    """Automatically skip integration tests unless --integration flag is used."""
    if config.getoption("--integration"):
        # --integration given in cli: do not skip integration tests
        return

    skip_integration = pytest.mark.skip(reason="need --integration option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
