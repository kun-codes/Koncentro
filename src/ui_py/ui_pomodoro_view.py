# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'pomodoro_view.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLayout, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

from qfluentwidgets import (PillToolButton, ProgressBar, ProgressRing, TitleLabel,
    ToggleToolButton, ToolButton)

class Ui_PomodoroView(object):
    def setupUi(self, PomodoroView) -> None:
        if not PomodoroView.objectName():
            PomodoroView.setObjectName(u"PomodoroView")
        PomodoroView.resize(486, 489)
        self.verticalLayout_2 = QVBoxLayout(PomodoroView)
        self.verticalLayout_2.setSpacing(12)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(24, 24, 24, 24)
        self.pomodoroLabel = TitleLabel(PomodoroView)
        self.pomodoroLabel.setObjectName(u"pomodoroLabel")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pomodoroLabel.sizePolicy().hasHeightForWidth())
        self.pomodoroLabel.setSizePolicy(sizePolicy)

        self.verticalLayout_2.addWidget(self.pomodoroLabel)

        self.topVerticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.topVerticalSpacer)

        self.ProgressRing = ProgressRing(PomodoroView)
        self.ProgressRing.setObjectName(u"ProgressRing")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.ProgressRing.sizePolicy().hasHeightForWidth())
        self.ProgressRing.setSizePolicy(sizePolicy1)
        self.ProgressRing.setMinimumSize(QSize(220, 220))
        self.ProgressRing.setMaximumSize(QSize(220, 220))
        self.ProgressRing.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_2.addWidget(self.ProgressRing, 0, Qt.AlignmentFlag.AlignHCenter)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(21)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.leftHorizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.leftHorizontalSpacer)

        self.stopButton = PillToolButton(PomodoroView)
        self.stopButton.setObjectName(u"stopButton")
        self.stopButton.setMinimumSize(QSize(68, 68))
        self.stopButton.setIconSize(QSize(21, 21))
        self.stopButton.setChecked(False)

        self.horizontalLayout.addWidget(self.stopButton)

        self.pauseResumeButton = PillToolButton(PomodoroView)
        self.pauseResumeButton.setObjectName(u"pauseResumeButton")
        self.pauseResumeButton.setMinimumSize(QSize(68, 68))
        self.pauseResumeButton.setIconSize(QSize(21, 21))
        self.pauseResumeButton.setChecked(False)

        self.horizontalLayout.addWidget(self.pauseResumeButton)

        self.skipButton = PillToolButton(PomodoroView)
        self.skipButton.setObjectName(u"skipButton")
        self.skipButton.setMinimumSize(QSize(68, 68))
        self.skipButton.setIconSize(QSize(21, 21))
        self.skipButton.setChecked(False)

        self.horizontalLayout.addWidget(self.skipButton)

        self.rightHorizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.rightHorizontalSpacer)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.bottomVerticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.bottomVerticalSpacer)


        self.retranslateUi(PomodoroView)

        QMetaObject.connectSlotsByName(PomodoroView)
    # setupUi

    def retranslateUi(self, PomodoroView) -> None:
        PomodoroView.setWindowTitle(QCoreApplication.translate("PomodoroView", u"Form", None))
        self.pomodoroLabel.setText(QCoreApplication.translate("PomodoroView", u"Pomodoro", None))
    # retranslateUi

