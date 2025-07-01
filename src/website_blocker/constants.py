# Don't add any 3rd party imports here, as this file is used by mitmdump directly through block.py

APPLICATION_NAME = "Koncentro"

MITMDUMP_SHUTDOWN_URL = f"http://shutdown.{APPLICATION_NAME.lower()}.internal/"
BLOCK_HTML_MESSAGE = f"<h1>Website blocked by {APPLICATION_NAME}!</h1>"
