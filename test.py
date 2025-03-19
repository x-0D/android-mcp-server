from ppadb.client import Client as AdbClient
import os
from PIL import Image as PILImage

client = AdbClient()
device = client.device("google-pixel-7-pro:41291")

# print(device.shell("getprop ro.product.model"))
# print(device.shell("getprop ro.product.manufacturer"))
# print(device.shell("getprop ro.build.version.release"))
# print(device.shell("getprop ro.build.version.sdk"))
# print(device.shell("getprop ro.product.brand"))
# print(device.shell("getprop ro.product.name"))

# device.shell("uiautomator dump")
# device.pull("/sdcard/window_dump.xml", "window_dump.xml")
# device.shell("rm /sdcard/window_dump.xml")

command = "pm list packages"
packages = device.shell(command).strip().split("\n")
result = [package[8:] for package in packages]
output = "\n".join(result)
print(output)