# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'app_blocker_view.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QSizePolicy, QVBoxLayout,
    QWidget)

from qfluentwidgets import (BodyLabel, CardWidget, ListView, PrimaryPushButton,
    PushButton, SimpleCardWidget, SingleDirectionScrollArea, TitleLabel,
    ToolButton)

class Ui_AppBlockView(object):
    def setupUi(self, AppBlockView):
        if not AppBlockView.objectName():
            AppBlockView.setObjectName(u"AppBlockView")
        AppBlockView.resize(638, 532)
        self.horizontalLayout = QHBoxLayout(AppBlockView)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.SingleDirectionScrollArea = SingleDirectionScrollArea(AppBlockView)
        self.SingleDirectionScrollArea.setObjectName(u"SingleDirectionScrollArea")
        self.SingleDirectionScrollArea.setStyleSheet(u"QScrollArea{background: transparent; border: none}")
        self.SingleDirectionScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 638, 532))
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
        self.descriptionLabel = BodyLabel(self.scrollAreaWidgetContents)
        self.descriptionLabel.setObjectName(u"descriptionLabel")

        self.horizontalLayout_2.addWidget(self.descriptionLabel)

        self.addAppsButton = PrimaryPushButton(self.scrollAreaWidgetContents)
        self.addAppsButton.setObjectName(u"addAppsButton")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.addAppsButton.sizePolicy().hasHeightForWidth())
        self.addAppsButton.setSizePolicy(sizePolicy1)

        self.horizontalLayout_2.addWidget(self.addAppsButton)

        self.deleteAppButton = ToolButton(self.scrollAreaWidgetContents)
        self.deleteAppButton.setObjectName(u"deleteAppButton")

        self.horizontalLayout_2.addWidget(self.deleteAppButton)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.SimpleCardWidget = SimpleCardWidget(self.scrollAreaWidgetContents)
        self.SimpleCardWidget.setObjectName(u"SimpleCardWidget")
        self.verticalLayout_2 = QVBoxLayout(self.SimpleCardWidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.blockedAppsListView = ListView(self.SimpleCardWidget)
        self.blockedAppsListView.setObjectName(u"blockedAppsListView")

        self.verticalLayout_2.addWidget(self.blockedAppsListView)


        self.verticalLayout.addWidget(self.SimpleCardWidget)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")

        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.SingleDirectionScrollArea.setWidget(self.scrollAreaWidgetContents)

        self.horizontalLayout.addWidget(self.SingleDirectionScrollArea)


        self.retranslateUi(AppBlockView)

        QMetaObject.connectSlotsByName(AppBlockView)
    # setupUi

    def retranslateUi(self, AppBlockView):
        AppBlockView.setWindowTitle(QCoreApplication.translate("AppBlockView", u"Form", None))
        self.titleLabel.setText(QCoreApplication.translate("AppBlockView", u"App Blocker", None))
        self.descriptionLabel.setText(QCoreApplication.translate("AppBlockView", u"Add apps to block them during focus sessions", None))
        self.addAppsButton.setText(QCoreApplication.translate("AppBlockView", u"Add apps", None))
    # retranslateUi

