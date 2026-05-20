import asyncio
import threading
from typing import Optional

from loguru import logger
from mitmproxy.options import Options
from mitmproxy.tools.dump import DumpMaster
from PySide6.QtCore import QObject
from uniproxy import Uniproxy

from configValues import ConfigValues
from website_blocker.block import BlockAddon


class WebsiteBlockerManager(QObject):
    """
    this method manages the mitmproxy instance in background threads for website blocking.

    Ordering guarantees (to avoid temporary internet loss):
      - Start: mitmproxy binds its port → *then* system proxy is joined
      - Stop:  system proxy is deleted → *then* mitmproxy is shut down
    """

    def __init__(self) -> None:
        super().__init__()
        self.proxy: Uniproxy = Uniproxy("127.0.0.1", ConfigValues.PROXY_PORT)

        self._master: Optional[DumpMaster] = None
        self._proxy_thread: Optional[threading.Thread] = None
        self._stop_thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._master_lock = threading.Lock()

    def start_blocking(
        self,
        listening_port: int,
        joined_addresses: str,
        block_type: str,
    ) -> None:
        """
        starts mitmproxy + join system proxy in a background thread (non-blocking).

        Order within the thread:
          delete old proxy -> shutdown old mitm
          -> start new mitm -> join new system proxy
        """
        logger.debug("Inside WebsiteBlockerManager.start_blocking().")

        def run() -> None:
            self._stop_current_master(delete_proxy=True)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            master: Optional[DumpMaster] = None
            try:
                opts = Options(
                    listen_host="127.0.0.1",
                    listen_port=listening_port,
                    showhost=True,
                )
                master = DumpMaster(opts, loop=loop)
                master.addons.add(BlockAddon())
                master.options.addresses_str = joined_addresses
                master.options.block_type = block_type

                # make the new master visible so stop_blocking can find it
                with self._master_lock:
                    self._master = master
                self._loop = loop

                # mitm is now listening -> safe to point the system proxy at it
                logger.debug("Joining system proxy.")
                self.proxy.join()

                loop.run_until_complete(master.run())
            except Exception as e:
                logger.error(f"Failed to run mitmproxy: {e}")
            finally:
                with self._master_lock:
                    if self._master is master:
                        self._master = None
                self._loop = None

        self._proxy_thread = threading.Thread(target=run, daemon=True)
        self._proxy_thread.start()
        logger.debug("Proxy starting in background thread.")

    def stop_blocking(self, delete_proxy: bool = True) -> None:
        """
        stops mitmproxy and optionally delete the system proxy (non-blocking).

        when *delete_proxy* is ``True`` the work is done in a background
        thread with the correct order: delete system proxy -> shutdown mitm.
        """
        logger.debug("Inside WebsiteBlockerManager.stop_blocking().")

        if delete_proxy:

            def stop_sequence() -> None:
                with self._master_lock:
                    master = self._master
                    self._master = None

                if master is None:
                    return

                logger.debug("Deleting system proxy.")
                self.proxy.delete_proxy()
                logger.debug("Shutting down mitmproxy master.")
                master.shutdown()

            self._stop_thread = threading.Thread(target=stop_sequence, daemon=True)
            self._stop_thread.start()
        else:
            with self._master_lock:
                master = self._master
                self._master = None
            if master is not None:
                master.shutdown()

    def cleanup(self) -> None:
        """
        clean up resources
        this method is blocking and is intended for use from a background thread.
        """
        logger.debug("Inside WebsiteBlockerManager.cleanup().")

        self._stop_current_master(delete_proxy=True)

        for attr in ("_stop_thread", "_proxy_thread"):
            t: Optional[threading.Thread] = getattr(self, attr, None)
            if t is not None and t.is_alive():
                t.join(timeout=5)
                setattr(self, attr, None)

        self.proxy.delete_proxy()
        logger.debug("Cleanup complete.")

    def _stop_current_master(self, delete_proxy: bool) -> None:
        """
        Stop whichever master is currently stored (runs in caller's thread).
        """
        with self._master_lock:
            master = self._master
            self._master = None

        if master is None:
            return

        if delete_proxy:
            logger.debug("Deleting system proxy (old instance).")
            self.proxy.delete_proxy()

        logger.debug("Shutting down previous mitmproxy master.")
        master.shutdown()
        self._loop = None
