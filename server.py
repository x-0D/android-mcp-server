import os
import sys
import argparse
import contextlib

import yaml
from starlette.applications import Starlette
from starlette.routing import Mount
from mcp.server.fastmcp import FastMCP, Image

from adbdevicemanager import AdbDeviceManager

CONFIG_FILE = "config.yaml"
CONFIG_FILE_EXAMPLE = "config.yaml.example"

# Load config (make config file optional)
config = {}
device_name = None

if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f.read()) or {}
        device_config = config.get("device", {})
        configured_device_name = device_config.get(
            "name") if device_config else None

        # Support multiple ways to specify auto-selection:
        # 1. name: null (None in Python)
        # 2. name: "" (empty string)
        # 3. name field completely missing
        if configured_device_name and configured_device_name.strip():
            device_name = configured_device_name.strip()
            print(f"Loaded config from {CONFIG_FILE}")
            print(f"Configured device: {device_name}")
        else:
            print(f"Loaded config from {CONFIG_FILE}")
            print(
                "No device specified in config, will auto-select if only one device connected")
    except Exception as e:
        print(f"Error loading config file {CONFIG_FILE}: {e}", file=sys.stderr)
        print(
            f"Please check the format of your config file or recreate it from {CONFIG_FILE_EXAMPLE}", file=sys.stderr)
        sys.exit(1)
else:
    print(
        f"Config file {CONFIG_FILE} not found, using auto-selection for device")

# Initialize MCP and device manager
# AdbDeviceManager will handle auto-selection if device_name is None
mcp = FastMCP("android")
deviceManager = AdbDeviceManager(device_name)

# Configure paths to avoid nesting
mcp.settings.streamable_http_path = "/"
mcp.settings.sse_path = "/"
mcp.settings.message_path = "/messages/"

# Create combined lifespan to manage session manager
@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    async with mcp.session_manager.run():
        yield


@mcp.tool()
def get_packages() -> str:
    """
    Get all installed packages on the device
    Returns:
        str: A list of all installed packages on the device as a string
    """
    result = deviceManager.get_packages()
    return result


@mcp.tool()
def execute_adb_shell_command(command: str) -> str:
    """Executes an ADB command and returns the output or an error.
    Args:
        command (str): The ADB shell command to execute
    Returns:
        str: The output of the ADB command
    """
    result = deviceManager.execute_adb_shell_command(command)
    return result


@mcp.tool()
def get_uilayout() -> str:
    """
    Retrieves information about clickable elements in the current UI.
    Returns a formatted string containing details about each clickable element,
    including its text, content description, bounds, and center coordinates.

    Returns:
        str: A formatted list of clickable elements with their properties
    """
    result = deviceManager.get_uilayout()
    return result


@mcp.tool()
def get_screenshot() -> Image:
    """Takes a screenshot of the device and returns it.
    Returns:
        Image: the screenshot
    """
    deviceManager.take_screenshot()
    return Image(path="compressed_screenshot.png")


@mcp.tool()
def get_package_action_intents(package_name: str) -> list[str]:
    """
    Get all non-data actions from Activity Resolver Table for a package
    Args:
        package_name (str): The name of the package to get actions for
    Returns:
        list[str]: A list of all non-data actions from the Activity Resolver Table for the package
    """
    result = deviceManager.get_package_action_intents(package_name)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Android MCP Server")
    parser.add_argument("--transport", default="stdio", 
                       choices=["stdio", "streamable-http", "sse", "all"],
                       help="Transport method(s) for MCP server")
    parser.add_argument("--host", default="0.0.0.0",
                       help="Host for HTTP-based transports")
    parser.add_argument("--port", type=int, default=8000,
                       help="Port for HTTP-based transports")
    
    args = parser.parse_args()
    
    if args.transport == "stdio":
        print("Starting Android MCP server with stdio transport")
        mcp.run(transport="stdio")
    else:
        try:
            import uvicorn
            from starlette.applications import Starlette
            from starlette.routing import Mount
        except ImportError:
            print("Error: uvicorn and starlette are required for HTTP-based transports.")
            print("Please install them with: pip install uvicorn starlette")
            sys.exit(1)
            
        # Configure paths to avoid nesting
        mcp.settings.streamable_http_path = "/"
        mcp.settings.sse_path = "/"
        mcp.settings.message_path = "/messages/"
        
        routes = []
        if args.transport in ["streamable-http", "all"]:
            routes.append(Mount("/mcp", mcp.streamable_http_app()))
        if args.transport in ["sse", "all"]:
            routes.append(Mount("/sse", mcp.sse_app()))
            
        if not routes:
            print("Error: No valid transport selected")
            sys.exit(1)
            
        app = Starlette(
            routes=routes,
            lifespan=lifespan,
        )
        
        print(f"Starting Android MCP server on http://{args.host}:{args.port}")
        if args.transport in ["streamable-http", "all"]:
            print(f"- StreamableHTTP endpoint: http://{args.host}:{args.port}/mcp")
        if args.transport in ["sse", "all"]:
            print(f"- SSE endpoint: http://{args.host}:{args.port}/sse")
            print(f"- SSE messages endpoint: http://{args.host}:{args.port}/sse/messages/")
            
        uvicorn.run(app, host=args.host, port=args.port)
