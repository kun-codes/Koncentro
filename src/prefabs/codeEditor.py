from PySide6.QtCore import QRect, QSize, Qt, Slot
from PySide6.QtGui import QColor, QFont, QPainter, QTextCharFormat, QTextCursor, QTextFormat
from PySide6.QtWidgets import QTextEdit, QWidget
from qfluentwidgets import PlainTextEdit, isDarkTheme, qconfig, setCustomStyleSheet

from models.config import AppSettings

# from: https://doc.qt.io/qtforpython-6.2/examples/example_widgets__codeeditor.html


class LineNumberArea(QWidget):
    def __init__(self, editor) -> None:
        QWidget.__init__(self, editor)
        self._code_editor = editor

    def sizeHint(self):
        return QSize(self._code_editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        self._code_editor.lineNumberAreaPaintEvent(event)


class CodeEditor(PlainTextEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.line_number_area = LineNumberArea(self)

        self._lineNumberAreaDarkBackgroundColor = Qt.GlobalColor.transparent
        self._lineNumberAreaLightBackgroundColor = Qt.GlobalColor.transparent

        self._currentLineHighlightLightColor = QColor(230, 230, 230)
        self._currentLineHighlightDarkColor = QColor(53, 53, 53)

        self._underline_selections = []

        self.blockCountChanged[int].connect(self.update_line_number_area_width)
        self.updateRequest[QRect, int].connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        qconfig.themeChanged.connect(self.highlight_current_line)
        qconfig.themeColorChanged.connect(self.lineNumberAreaPaintEvent)

        self.update_line_number_area_width(0)

        qss = """
                PlainTextEdit {
                    padding: 0px 0px 2px 8px;
                }
            """
        setCustomStyleSheet(self, qss, qss)

    def line_number_area_width(self) -> int:
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num *= 0.1
            digits += 1

        base_space = 20
        space = base_space + self.fontMetrics().horizontalAdvance("9") * digits
        return space

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        cr = self.contentsRect()
        width = self.line_number_area_width()
        rect = QRect(cr.left(), cr.top(), width, cr.height())
        self.line_number_area.setGeometry(rect)

    def lineNumberAreaPaintEvent(self, event) -> None:
        painter = QPainter(self.line_number_area)
        painter.fillRect(
            event.rect(),
            self._lineNumberAreaDarkBackgroundColor if isDarkTheme() else self._lineNumberAreaLightBackgroundColor,
        )
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        offset = self.contentOffset()
        top = self.blockBoundingGeometry(block).translated(offset).top()
        bottom = top + self.blockBoundingRect(block).height()

        font = painter.font()
        font.setFamily("Monospace")
        painter.setFont(font)

        current_block_number = self.textCursor().blockNumber()
        selection_start = self.textCursor().selectionStart()
        selection_end = self.textCursor().selectionEnd()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)

                block_start = block.position()
                block_end = block_start + block.length() - 1

                # render the current line number in bold and the line numbers corresponding to the selection and
                # CodeEditor is in focus
                if (
                    block_number == current_block_number
                    or (selection_start <= block_end and selection_end >= block_start)
                ) and self.hasFocus():
                    painter.setPen(AppSettings.get(AppSettings, AppSettings.themeColor))
                    font.setWeight(QFont.Weight.Bold)  # Bold font for current line
                    painter.setFont(font)
                else:
                    painter.setPen(Qt.GlobalColor.white if isDarkTheme() else Qt.GlobalColor.black)
                width = self.line_number_area.width()
                height = self.fontMetrics().height()

                horizontal_offset = 7

                painter.drawText(
                    0,
                    top,
                    width - horizontal_offset,
                    height,
                    Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight,
                    number,
                )
                if block_number == current_block_number or (
                    selection_start <= block_end and selection_end >= block_start
                ):
                    # reset font to normal for other lines
                    font.setWeight(QFont.Weight.Normal)
                    painter.setFont(font)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

        # QPainter needs an explicit end() in PyPy. This will become a context manager in 6.3.
        painter.end()

    @Slot()
    def update_line_number_area_width(self, newBlockCount) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    @Slot()
    def update_line_number_area(self, rect, dy) -> None:
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            width = self.line_number_area.width()
            self.line_number_area.update(0, rect.y(), width, rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    @Slot()
    def highlight_current_line(self) -> None:
        extra_selections = []

        if not self.isReadOnly() and self.hasFocus():
            selection = QTextEdit.ExtraSelection()
            line_color = self._currentLineHighlightDarkColor if isDarkTheme() else self._currentLineHighlightLightColor
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        extra_selections.extend(self._underline_selections)

        self.setExtraSelections(extra_selections)

    def focusOutEvent(self, e) -> None:
        super().focusOutEvent(e)
        self.setExtraSelections(self._underline_selections)

    def underline_lines(self, line_numbers: list[int]) -> None:
        self._underline_selections = []
        for line_number in line_numbers:
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(Qt.GlobalColor.red)
            format = QTextCharFormat()
            format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
            format.setUnderlineColor(line_color)
            selection.format = format

            cursor = QTextCursor(self.document().findBlockByNumber(line_number - 1))
            cursor.select(QTextCursor.BlockUnderCursor)
            selection.cursor = cursor

            self._underline_selections.append(selection)

        self.highlight_current_line()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

    app = QApplication([])

    widget = QWidget()
    layout = QVBoxLayout(widget)
    codeEdit = CodeEditor()
    layout.addWidget(codeEdit)
    widget.show()

    app.exec()
