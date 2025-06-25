# Don't add any 3rd party imports here, as this file is used by mitmdump directly through filter.py

import os
import platform

APPLICATION_NAME = "Koncentro"

# from: https://stackoverflow.com/a/75284996
if platform.system() == 'Linux' and os.environ.get('container') is not None:  # is running in flatpak
    MITMDUMP_SHUTDOWN_URL = "http://127.0.0.1:8080/shutdown-mitmdump"  # inside flatpak, dns resolution is sandboxed
else:
    MITMDUMP_SHUTDOWN_URL = f"http://shutdown.{APPLICATION_NAME.lower()}.internal/"

BLOCK_HTML_MESSAGE = f"<h1>Website blocked by {APPLICATION_NAME}!</h1>"
