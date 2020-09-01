try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
    from PyQt5 import QtCore, QtGui, QtWidgets
    import os


except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *
items_list=["VGG-19", "ResNet", "Inception"]

class Ui_detect(QtWidgets.QWidget):

    def __init__(self):
        super(Ui_detect, self).__init__()
        self.setObjectName("detect")
        self.resize(700, 600)
        self.setWindowTitle("检测")

        #layout = QtWidgets.QListWidget(self.gridLayoutWidget)

        layout = QVBoxLayout(self)

        #wangyibo 2019.03.27 选择网络模型下拉选项框
        self.combobox1 = QComboBox(self, minimumWidth=100)
        layout.addWidget(QLabel("选择网络模型", self))
        layout.addWidget(self.combobox1)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.init_combobox1()
        self.combobox1.activated.connect(self.on_combobox1_Activate)

        #网络导入按键
        self.NetInputButton=QToolButton(self)
        self.NetInputButton.setText("网络导入")
        layout.addWidget(self.NetInputButton)
        self.NetInputButton.clicked.connect(self.NetInput)

        #超参数设置
        hyperparametersLabel1 = QLabel("超参数1")
        self.Hyperparameters1LineEdit = QLineEdit(" ")
        hyperparametersLabel2 = QLabel("超参数2")
        self.Hyperparameters2LineEdit = QLineEdit(" ")
        hyperparametersLabel3 = QLabel("超参数3")
        self.Hyperparameters3LineEdit = QLineEdit(" ")
        hyperparametersLabel4 = QLabel("超参数4")
        self.Hyperparameters4LineEdit = QLineEdit(" ")
        layout.addWidget(hyperparametersLabel1)
        layout.addWidget(self.Hyperparameters1LineEdit)
        layout.addWidget(hyperparametersLabel2)
        layout.addWidget(self.Hyperparameters2LineEdit)
        layout.addWidget(hyperparametersLabel3)
        layout.addWidget(self.Hyperparameters3LineEdit)
        layout.addWidget(hyperparametersLabel4)
        layout.addWidget(self.Hyperparameters4LineEdit)
        save_Btn = QPushButton('保存')
        cancle_Btn = QPushButton('取消')
        cancle_Btn.clicked.connect(self.opensublimetext)
        save_Btn.clicked.connect(self.addNum)
        layout.addWidget(save_Btn)
        layout.addWidget(cancle_Btn)




        self.AffairViewer = QListWidget()
        AVLayout = QGridLayout()
        AVLayout.setContentsMargins(0, 0, 0, 0)
        AVLayout.addWidget(self.AffairViewer)
        AVContainer = QWidget()
        AVContainer.setLayout(AVLayout)


        self.RunButton = QToolButton(self)
        self.RunButton.setText("运行")
        AVLayout.addWidget(self.RunButton)

        self.AVdock = QDockWidget('训练情况', self)
        self.AVdock.setObjectName(u'AV')
        self.AVdock.setWidget(AVContainer)
        self.AVdock.setFloating(True)

        self.AffairViewer.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        # 这里以滚动窗口显示)
        self.RunButton.clicked.connect(self.affairviewer)

        #self.addDockWidget(Qt.RightDockWidgetArea, self.AVdock)




    def opensublimetext(self):
        os.system('open /Applications/Utilities/Terminal.app')

    def affairviewer(self):


            self.AffairViewer.addItem('当前字母 :' + letter)








    def init_combobox1(self):
        for i in range(len(items_list)):
                 self.combobox1.addItem(items_list[i])
        self.combobox1.setCurrentIndex(-1)


# wangyibo 2019.03.27 选择模型后触发的效果
    def on_combobox1_Activate(self, index):
        print(self.combobox1.count())# 返回列表框下拉项数目
        print(self.combobox1.currentIndex()) # 返回选中项索引
        print(self.combobox1.currentText())# 返回选中项的文本内容
        print(self.combobox1.currentData())# 返回当前数据
        print(self.combobox1.itemData(self.combobox1.currentIndex()))
        print(self.combobox1.itemText(self.combobox1.currentIndex()))
        print(self.combobox1.itemText(index))

    #打开要导入的模型，用sublime text展开

    def NetInput(self):
        NetInput_name, NetInput_type = QFileDialog.getOpenFileName(self, '选择文件', '', 'python files(*.py)')
        #cmd = ('open -a /Applications/Sublime\ Text.app 'NetInput_name'')
        os.system('open -a /Applications/Sublime\ Text.app '+NetInput_name)
        #filepath = self.settings.get('NetInput_name')


    def run(self):


        filepath = self.settings.get('filename')

    def addNum(self):
        name = self.nameLineEdit.text()  # 获取文本框内容
        sex = self.sexLineEdit.text()
        phone = self.phoneLineEdit.text()
        mail = self.mailEdit.text()
