"""
Entry point for Facebook Ads MCP Server.

This module provides the main() function that initializes and runs the MCP server.
"""

import logging
from server import mcp
from fb_ads.api import init_config_from_args

# Configure logging to stderr (stdout must be reserved for JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the Facebook Ads MCP Server."""
    try:
        logger.info("Starting Facebook Ads MCP Server...")
        # Configuration is already initialized at module import time
        # via init_config_from_args() call in server.py
        mcp.run()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()
