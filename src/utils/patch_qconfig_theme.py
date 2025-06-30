import platform

import darkdetect
from loguru import logger
from PySide6.QtDBus import QDBusInterface, QDBusMessage, QDBusVariant
from qfluentwidgets import Theme, qconfig


@property
def theme_override(self):
    """Get theme mode"""
    return self._theme


@theme_override.setter
def theme_override(self, t):
    """Change the theme without modifying the config file"""
    if t == Theme.AUTO:
        # Try dbus first
        try:
            iface = QDBusInterface(
                "org.freedesktop.portal.Desktop",
                "/org/freedesktop/portal/desktop",
                "org.freedesktop.portal.Settings",
            )

            # Check if the interface is valid
            if not iface.isValid():
                raise ValueError("DBus interface is not valid")

            reply: QDBusMessage = iface.call("Read", "org.freedesktop.appearance", "color-scheme")

            # Handle QDBusMessage reply
            value = None
            if isinstance(reply, QDBusMessage):
                if reply.type() == QDBusMessage.MessageType.ReplyMessage:
                    args = reply.arguments()
                    if args:
                        value: QDBusVariant = args[0]
                    else:
                        raise ValueError("No arguments in DBus reply")
                else:
                    raise ValueError(f"DBus error: {reply.errorMessage()}")

            # Extract the actual value from QDBusVariant with recursive unwrapping
            actual_value: QDBusVariant = value
            max_unwrap_attempts = 5  # Prevent infinite loops
            unwrap_count = 0

            # Keep unwrapping variants until we get the actual value
            while unwrap_count < max_unwrap_attempts:
                logger.debug(f"Unwrap attempt {unwrap_count + 1}: {actual_value} (type: {type(actual_value)})")

                if hasattr(actual_value, "variant") and callable(actual_value.variant):
                    actual_value = actual_value.variant()
                    unwrap_count += 1
                else:
                    # No more unwrapping possible
                    logger.debug("No 'variant' attribute found, breaking out of unwrapping loop.")
                    break

            logger.debug(f"Final unwrapped value: {actual_value} (type: {type(actual_value)})")

            # The Portal Settings returns the value in a specific format
            # It should be a variant containing (namespace, key, value) tuple or just the value
            if actual_value is not None and isinstance(actual_value, (int, float)):
                color_scheme = int(actual_value)
            else:
                raise ValueError("Expected an int or a tuple/list with an int value")

            logger.debug(f"Extracted color scheme from dbus: {color_scheme}")

            if color_scheme is not None:
                if color_scheme == 1:  # Dark mode
                    t = Theme.DARK
                    logger.debug("Using theme from dbus: DARK")
                elif color_scheme == 2:  # Light mode
                    t = Theme.LIGHT
                    logger.debug("Using theme from dbus: LIGHT")
                else:  # 0 = no preference, fall through to other methods
                    raise ValueError(f"No preference set (color-scheme: {color_scheme})")
            else:
                raise ValueError("Could not extract color scheme value")

        except Exception as e:
            # fallback to darkdetect
            logger.debug(f"DBus error or fallback: {e}")
            try:
                detected_theme = darkdetect.theme()
                t = Theme(detected_theme) if detected_theme else Theme.LIGHT
                logger.debug(f"Detected theme: {detected_theme}, using {t}")
            except ImportError:
                logger.debug("darkdetect not available, using LIGHT theme")
                t = Theme.LIGHT

    self._theme = t


def apply_qconfig_theme_patch():
    """Apply the patch to QConfig to override the theme property."""
    if platform.system().lower() == "linux":
        qconfig.__class__.theme = theme_override
