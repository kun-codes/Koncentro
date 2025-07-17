# Copyright: (c) 2018, Aniket Panjwani <aniket@addictedto.tech>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Block URLs according to rules."""

import os
import sys
import urllib.parse

# append directory containing constants.py to path so that BLOCK_HTML_MESSAGE can be imported correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mitmproxy import ctx, http

from website_blocker.constants import BLOCK_HTML_MESSAGE, MITMDUMP_CHECK_URL, MITMDUMP_SHUTDOWN_URL


def load(loader) -> None:
    loader.add_option("addresses_str", str, "", "Concatenated addresses.")
    loader.add_option("block_type", str, "", "Allowlist or blocklist.")


def request(flow) -> None:
    # https://docs.mitmproxy.org/stable/addons-examples/#shutdown
    if flow.request.pretty_url == MITMDUMP_SHUTDOWN_URL:
        print("Shutting down mitmdump...")
        # Send confirmation response before shutdown
        flow.response = http.Response.make(200, b"Shutting down mitmproxy...\n", {"Content-Type": "text/plain"})
        ctx.master.shutdown()
        return

    if flow.request.method != MITMDUMP_CHECK_URL:
        print("Mitmdump is running, sending back confirmation response.")
        flow.response = http.Response.make(200, b"Mitmdump is running.\n", {"Content-Type": "text/plain"})
        return

    def strip_www(domain):
        return domain[4:] if domain.startswith("www.") else domain

    # if reddit.com is in the addresses_str, it will match both www.reddit.com and reddit.com
    # but won't match old.reddit.com or any other subdomains

    # if old.reddit.com is in the addresses_str, it will match both old.reddit.com only and
    # no other subdomains

    addresses = ctx.options.addresses_str.split(",")
    # Normalize addresses by stripping whitespace and leading www.
    addresses = {strip_www(address.strip()) for address in addresses if address.strip()}

    parsed_url = urllib.parse.urlparse(flow.request.pretty_url)
    url_domain = strip_www(parsed_url.netloc)

    # Use direct string matching for exact domain match
    has_match = url_domain in addresses
    if (ctx.options.block_type == "allowlist" and not has_match) or (
        ctx.options.block_type == "blocklist" and has_match
    ):
        flow.response = http.Response.make(200, BLOCK_HTML_MESSAGE.encode(), {"Content-Type": "text/html"})
