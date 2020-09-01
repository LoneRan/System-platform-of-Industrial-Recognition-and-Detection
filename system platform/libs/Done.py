try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
    from PyQt5 import QtCore, QtGui, QtWidgets
    import os


except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

class Ui_done(QtWidgets.QWidget):

    def __init__(self):
        super(Ui_done, self).__init__()
        self.setObjectName("done")
        self.resize(200, 30)
        self.setWindowTitle("扩充数据集成功！")

        layout = QHBoxLayout(self)

        self.ConfirmButton = QToolButton(self)
        self.ConfirmButton.setText("确定")
        layout.addWidget(self.ConfirmButton)
        #self.ConfirmButton.clicked.connect(login.close)
