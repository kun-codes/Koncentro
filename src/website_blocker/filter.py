# Copyright: (c) 2018, Aniket Panjwani <aniket@addictedto.tech>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Filter URLs according to rules."""

import os
import sys
import re
import urllib.parse

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

    def strip_www(domain):
        return domain[4:] if domain.startswith("www.") else domain

    addresses = ctx.options.addresses_str.split(",")
    addresses = {strip_www(address.strip()) for address in addresses if address.strip()}
    patterns = {re.compile(rf"^{re.escape(address)}$") for address in addresses}

    parsed_url = urllib.parse.urlparse(flow.request.pretty_url)
    url_domain = strip_www(parsed_url.netloc)

    # Only match if the domain matches exactly (no subdomain matching unless listed)
    has_match = any(pattern.fullmatch(url_domain) for pattern in patterns)
    if (ctx.options.block_type == "allowlist" and not has_match) or \
       (ctx.options.block_type == "blocklist" and has_match):
        flow.response = http.Response.make(200, BLOCK_HTML_MESSAGE.encode(), {"Content-Type": "text/html"})
