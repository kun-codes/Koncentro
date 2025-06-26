# Monkey patch for qfluentwidgets.components.widgets.tool_tip.ToolTip because of bug in qfluentwidgets
# This patch sets window flags correctly to Qt.ToolTip
# Needed for wayland linux sessions only. Shows a box around the tooltip in macOS and Windows

from loguru import logger
from utils.check_flatpak_sandbox import is_flatpak_sandbox


def apply_patches():
    """Apply monkey patches to fix the ToolTip window flags"""
    try:
        from PySide6.QtCore import Qt
        from qfluentwidgets.components.widgets.tool_tip import ToolTip

        original_init = ToolTip.__init__

        def patched_init(self, text='', parent=None):
            original_init(self, text, parent)
            if is_flatpak_sandbox():
                self.setWindowFlags(Qt.FramelessWindowHint)
            else:
                self.setWindowFlags(Qt.ToolTip)
            logger.debug("Tooltip window flags patched successfully!")

        # Replace the original __init__ with patched version
        ToolTip.__init__ = patched_init

        logger.debug("Successfully applied tooltip window flags patch")
        return True
    except Exception as e:
        logger.debug(f"Error applying tooltip patch: {e}")
        return False


if __name__ == "__main__":
    apply_patches()
