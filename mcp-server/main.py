import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools import mcp

if __name__ == "__main__":
    # Start the MCP server using stdio transport
    mcp.run()
