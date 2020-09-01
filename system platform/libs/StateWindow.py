try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
    from PyQt5 import QtCore, QtGui, QtWidgets
    import os


except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *


class Ui_state(QtWidgets.QWidget):

    def __init__(self):
        super(Ui_state, self).__init__()
        self.setObjectName("state")
        self.resize(250, 200)
        self.setWindowTitle("状态监测")

        self.fileListWidget = QListWidget()

        filelistLayout = QVBoxLayout()
        filelistLayout.setContentsMargins(0, 0, 0, 0)
        filelistLayout.addWidget(self.fileListWidget)
        fileListContainer = QWidget()
        fileListContainer.setLayout(filelistLayout)
        self.filedock = QDockWidget(u'Statement', self)
        self.filedock.setObjectName(u'File')
        self.filedock.setWidget(fileListContainer)
'''
        self.AffairViewer = QListWidget()
        AVLayout = QGridLayout()
        AVLayout.setContentsMargins(0, 0, 0, 0)
        AVLayout.addWidget(self.AffairViewer)
        AVContainer = QWidget()
        AVContainer.setLayout(AVLayout)

        self.AffairViewer.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
'''
