# Copyright: (c) 2018, Aniket Panjwani <aniket@addictedto.tech>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Block URLs according to rules."""

import urllib.parse
from typing import Set

import mitmproxy.addonmanager
from mitmproxy import ctx, http

from website_blocker.constants import BLOCK_HTML_MESSAGE, MITMDUMP_CHECK_URL, MITMDUMP_SHUTDOWN_URL


class BlockAddon:
    """Mitmproxy addon that blocks or allows URLs based on configuration."""

    def load(self, loader: mitmproxy.addonmanager.Loader) -> None:
        loader.add_option("addresses_str", str, "", "Concatenated addresses.")
        loader.add_option("block_type", str, "", "Allowlist or blocklist.")

    def request(self, flow: mitmproxy.http.HTTPFlow) -> None:
        # Respond to shutdown requests
        if flow.request.pretty_url == MITMDUMP_SHUTDOWN_URL:
            print("Shutting down mitmproxy...")
            flow.response = http.Response.make(200, b"Shutting down mitmproxy...\n", {"Content-Type": "text/plain"})
            ctx.master.shutdown()
            return

        # Respond to health-check requests
        if flow.request.pretty_url == MITMDUMP_CHECK_URL:
            print("Mitmdump is running, sending back confirmation response.")
            flow.response = http.Response.make(200, b"Mitmdump is running.\n", {"Content-Type": "text/plain"})
            return

        def strip_www(domain: str) -> str:
            return domain[4:] if domain.startswith("www.") else domain

        # if reddit.com is in the addresses_str, it will match both www.reddit.com and reddit.com
        # but won't match old.reddit.com or any other subdomains

        # if old.reddit.com is in the addresses_str, it will match both old.reddit.com only and
        # no other subdomains

        addresses: Set[str] = {
            strip_www(address.strip()) for address in ctx.options.addresses_str.split(",") if address.strip()
        }

        # Normalize addresses by stripping whitespace and leading www.
        addresses = {strip_www(address.strip()) for address in addresses if address.strip()}

        parsed_url: urllib.parse.ParseResult = urllib.parse.urlparse(flow.request.pretty_url)
        url_domain: str = strip_www(parsed_url.netloc)

        # Use direct string matching for exact domain match
        has_match: bool = url_domain in addresses
        if (ctx.options.block_type == "allowlist" and not has_match) or (
            ctx.options.block_type == "blocklist" and has_match
        ):
            flow.response = http.Response.make(200, BLOCK_HTML_MESSAGE.encode(), {"Content-Type": "text/html"})
