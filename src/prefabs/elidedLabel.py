from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics, QPainter
from qfluentwidgets import StrongBodyLabel


class ElidedStrongBodyLabel(StrongBodyLabel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

    def paintEvent(self, event) -> None:
        if not self.text():
            return

        painter = QPainter(self)
        metrics = QFontMetrics(self.font())

        # Account for margins
        margin = 2
        available_width = self.width() - 2 * margin

        # Create elided text
        elided_text = metrics.elidedText(self.text(), Qt.TextElideMode.ElideRight, available_width)

        # Draw the text
        painter.drawText(self.rect().adjusted(margin, 0, -margin, 0), int(self.alignment()), elided_text)
