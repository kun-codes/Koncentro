# Copyright: (c) 2018, Aniket Panjwani <aniket@addictedto.tech>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Filter URLs according to rules."""

import os
import sys

# append directory containing constants.py to path so that BLOCK_HTML_MESSAGE can be imported correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mitmproxy import ctx, http

from website_blocker.constants import BLOCK_HTML_MESSAGE, MITMDUMP_SHUTDOWN_URL


def load(loader):
    loader.add_option("addresses_str", str, "", "Concatenated addresses.")
    loader.add_option("block_type", str, "", "Whitelist or blacklist.")


def request(flow):
    # https://docs.mitmproxy.org/stable/addons-examples/#shutdown
    if flow.request.pretty_url == MITMDUMP_SHUTDOWN_URL:
        print("Shutting down mitmdump...")
        # Send confirmation response before shutdown
        flow.response = http.Response.make(
            200,
            b"Shutting down mitmproxy...\n",
            {"Content-Type": "text/plain"}
        )
        ctx.master.shutdown()
        return

    addresses = ctx.options.addresses_str.split(",")
    addresses = set(addresses)

    addresses = {address for address in addresses if address}

    has_match = any(address in flow.request.pretty_url for address in addresses)
    if ctx.options.block_type == "allowlist" and not has_match or ctx.options.block_type == "blocklist" and has_match:
        flow.response = http.Response.make(200, BLOCK_HTML_MESSAGE.encode(), {"Content-Type": "text/html"})
