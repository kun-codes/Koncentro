# Copyright: (c) 2018, Aniket Panjwani <aniket@addictedto.tech>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Entry point for the mitmproxy subprocess used by WebsiteBlockerManager."""

import argparse
import asyncio

from mitmproxy.options import Options
from mitmproxy.tools.dump import DumpMaster

from website_blocker.block import BlockAddon


def main() -> None:
    """Run mitmproxy DumpMaster with the BlockAddon in a separate process."""
    parser = argparse.ArgumentParser(description="Run mitmproxy for website blocking.")
    parser.add_argument("--port", type=int, required=True, help="Listening port for mitmproxy")
    parser.add_argument("--addresses", type=str, default="", help="Comma-separated list of addresses to block/allow")
    parser.add_argument("--block-type", type=str, default="blocklist", help="Block type: blocklist or allowlist")
    args = parser.parse_args()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    opts = Options(listen_host="127.0.0.1", listen_port=args.port, showhost=True)
    master = DumpMaster(opts, loop=loop)
    master.addons.add(BlockAddon())
    master.options.addresses_str = args.addresses
    master.options.block_type = args.block_type

    loop.run_until_complete(master.run())


if __name__ == "__main__":
    main()
