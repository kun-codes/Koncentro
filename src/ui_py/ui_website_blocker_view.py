# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'website_blocker_view.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

from prefabs.codeEditor import CodeEditor
from qfluentwidgets import (BodyLabel, ComboBox, PrimaryPushButton, PushButton,
    SingleDirectionScrollArea, TitleLabel)

class Ui_WebsiteBlockView(object):
    def setupUi(self, WebsiteBlockView) -> None:
        if not WebsiteBlockView.objectName():
            WebsiteBlockView.setObjectName(u"WebsiteBlockView")
        WebsiteBlockView.resize(534, 532)
        self.horizontalLayout = QHBoxLayout(WebsiteBlockView)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.SingleDirectionScrollArea = SingleDirectionScrollArea(WebsiteBlockView)
        self.SingleDirectionScrollArea.setObjectName(u"SingleDirectionScrollArea")
        self.SingleDirectionScrollArea.setStyleSheet(u"QScrollArea{background: transparent; border: none}")
        self.SingleDirectionScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 534, 532))
        self.scrollAreaWidgetContents.setStyleSheet(u"QWidget#scrollAreaWidgetContents{background: transparent}")
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setSpacing(12)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(24, 24, 24, 24)
        self.titleLabel = TitleLabel(self.scrollAreaWidgetContents)
        self.titleLabel.setObjectName(u"titleLabel")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.titleLabel.sizePolicy().hasHeightForWidth())
        self.titleLabel.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.titleLabel)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.blockTypeLabel = BodyLabel(self.scrollAreaWidgetContents)
        self.blockTypeLabel.setObjectName(u"blockTypeLabel")
        sizePolicy.setHeightForWidth(self.blockTypeLabel.sizePolicy().hasHeightForWidth())
        self.blockTypeLabel.setSizePolicy(sizePolicy)

        self.horizontalLayout_2.addWidget(self.blockTypeLabel)

        self.blockTypeComboBox = ComboBox(self.scrollAreaWidgetContents)
        self.blockTypeComboBox.setObjectName(u"blockTypeComboBox")

        self.horizontalLayout_2.addWidget(self.blockTypeComboBox)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.blockListTextEdit = CodeEditor(self.scrollAreaWidgetContents)
        self.blockListTextEdit.setObjectName(u"blockListTextEdit")
        self.blockListTextEdit.setFrameShape(QFrame.Shape.StyledPanel)
        self.blockListTextEdit.setFrameShadow(QFrame.Shadow.Raised)

        self.verticalLayout.addWidget(self.blockListTextEdit)

        self.allowListTextEdit = CodeEditor(self.scrollAreaWidgetContents)
        self.allowListTextEdit.setObjectName(u"allowListTextEdit")
        self.allowListTextEdit.setFrameShape(QFrame.Shape.StyledPanel)
        self.allowListTextEdit.setFrameShadow(QFrame.Shadow.Raised)

        self.verticalLayout.addWidget(self.allowListTextEdit)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer)

        self.cancelButton = PushButton(self.scrollAreaWidgetContents)
        self.cancelButton.setObjectName(u"cancelButton")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.cancelButton.sizePolicy().hasHeightForWidth())
        self.cancelButton.setSizePolicy(sizePolicy1)

        self.horizontalLayout_4.addWidget(self.cancelButton)

        self.saveButton = PrimaryPushButton(self.scrollAreaWidgetContents)
        self.saveButton.setObjectName(u"saveButton")

        self.horizontalLayout_4.addWidget(self.saveButton)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.SingleDirectionScrollArea.setWidget(self.scrollAreaWidgetContents)

        self.horizontalLayout.addWidget(self.SingleDirectionScrollArea)


        self.retranslateUi(WebsiteBlockView)

        QMetaObject.connectSlotsByName(WebsiteBlockView)
    # setupUi

    def retranslateUi(self, WebsiteBlockView) -> None:
        WebsiteBlockView.setWindowTitle(QCoreApplication.translate("WebsiteBlockView", u"Form", None))
        self.titleLabel.setText(QCoreApplication.translate("WebsiteBlockView", u"Website Blocker", None))
        self.blockTypeLabel.setText(QCoreApplication.translate("WebsiteBlockView", u"Select type of website blocking: ", None))
        self.cancelButton.setText(QCoreApplication.translate("WebsiteBlockView", u"Cancel", None))
        self.saveButton.setText(QCoreApplication.translate("WebsiteBlockView", u"Save", None))
    # retranslateUi

