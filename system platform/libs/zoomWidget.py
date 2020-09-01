# -*- coding: utf8 -*-
try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *


class ZoomWidget(QSpinBox):

    def __init__(self, value=100):
        super(ZoomWidget, self).__init__()
        #创建一个不显示按钮的可上下调节数字的文本框（可通过+-/鼠标滚轮进行调节），详见http://doc.qt.io/archives/qt-4.8/qabstractspinbox.html#details
        self.setButtonSymbols(QAbstractSpinBox.NoButtons) 
        self.setRange(1, 500) #调节范围为1到500
        self.setSuffix(' %') #后缀为%，即缩放百分之多少
        self.setValue(value) #设置默认值
        self.setToolTip(u'Zoom Level') #设置控件名称
        self.setStatusTip(self.toolTip()) 
        self.setAlignment(Qt.AlignCenter) #中心对齐

    def minimumSizeHint(self):
        height = super(ZoomWidget, self).minimumSizeHint().height()
        fm = QFontMetrics(self.font())
        width = fm.width(str(self.maximum()))
        return QSize(width, height)
