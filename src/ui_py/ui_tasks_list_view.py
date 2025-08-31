# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tasks_list_view.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

from qfluentwidgets import (SingleDirectionScrollArea, ToolButton)

class Ui_TaskView(object):
    def setupUi(self, TaskView):
        if not TaskView.objectName():
            TaskView.setObjectName(u"TaskView")
        TaskView.resize(800, 600)
        self.verticalLayout = QVBoxLayout(TaskView)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.SingleDirectionScrollArea = SingleDirectionScrollArea(TaskView)
        self.SingleDirectionScrollArea.setObjectName(u"SingleDirectionScrollArea")
        self.SingleDirectionScrollArea.setStyleSheet(u"QScrollArea{background: transparent; border: none}")
        self.SingleDirectionScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 782, 582))
        self.scrollAreaWidgetContents.setStyleSheet(u"QWidget#scrollAreaWidgetContents { background: transparent }")
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setSpacing(12)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(24, 24, 24, 24)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.editTaskTimeButton = ToolButton(self.scrollAreaWidgetContents)
        self.editTaskTimeButton.setObjectName(u"editTaskTimeButton")

        self.horizontalLayout.addWidget(self.editTaskTimeButton)

        self.addTaskButton = ToolButton(self.scrollAreaWidgetContents)
        self.addTaskButton.setObjectName(u"addTaskButton")

        self.horizontalLayout.addWidget(self.addTaskButton)

        self.addSubTaskButton = ToolButton(self.scrollAreaWidgetContents)
        self.addSubTaskButton.setObjectName(u"addSubTaskButton")

        self.horizontalLayout.addWidget(self.addSubTaskButton)

        self.deleteTaskButton = ToolButton(self.scrollAreaWidgetContents)
        self.deleteTaskButton.setObjectName(u"deleteTaskButton")

        self.horizontalLayout.addWidget(self.deleteTaskButton)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.SingleDirectionScrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.SingleDirectionScrollArea)


        self.retranslateUi(TaskView)

        QMetaObject.connectSlotsByName(TaskView)
    # setupUi

    def retranslateUi(self, TaskView):
        TaskView.setWindowTitle(QCoreApplication.translate("TaskView", u"Form", None))
    # retranslateUi

