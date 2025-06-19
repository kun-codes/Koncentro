# Monkey patch for qfluentwidgets.components.widgets.tool_tip.ToolTip because of bug in qfluentwidgets
# This patch sets window flags correctly to Qt.ToolTip

from loguru import logger

def apply_patches():
    """Apply monkey patches to fix the ToolTip window flags"""
    try:
        from PySide6.QtCore import Qt
        from qfluentwidgets.components.widgets.tool_tip import ToolTip

        original_init = ToolTip.__init__

        def patched_init(self, text='', parent=None):
            original_init(self, text, parent)
            self.setWindowFlags(Qt.ToolTip)
            logger.debug("Tooltip window flags patched successfully!")

        # Replace the original __init__ with patched version
        ToolTip.__init__ = patched_init

        logger.debug("Successfully applied tooltip window flags patch")
        return True
    except Exception as e:
        logger.debug(f"Error applying tooltip patch: {e}")
        return False

apply_patches()

if __name__ == "__main__":
    apply_patches()
