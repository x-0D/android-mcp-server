from adbdevicemanager import AdbDeviceManager
from mcp.server.fastmcp import FastMCP, Image
import shutil
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f.read())

mcp = FastMCP("android")
deviceManager = AdbDeviceManager(config["device"]["name"])

def command_exists(command):
    return shutil.which(command) is not None

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
def execute_adb_command(args: str) -> str:
    """Executes an ADB command and returns the output or an error.
    Args:
        args (str): The ADB args to execute
    Returns:
        str: The output of the ADB command
    """

    executables = ['adb']

    found = False

    for executable in executables:
        exists = command_exists(executable)
        if exists:
            found = exists
            command = executable
            break

    if found:
        result = deviceManager.execute_adb_command(command + " " + args)
        return result
    else:
        commands = ', '.join(executables)
        return commands + " not found"


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
    mcp.run(transport="stdio")
