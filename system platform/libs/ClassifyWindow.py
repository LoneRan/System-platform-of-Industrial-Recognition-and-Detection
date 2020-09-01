
try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
    from PyQt5 import QtCore, QtGui, QtWidgets
    import os
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *
items_list=["AlexNet", "VGG19(bn)", "ResNet-110", "ResNet-1202", "PreResNet-110", "ResNeXt-29, 8x64d", "ResNeXt-29, 16x64d", "WRN-28-10-drop"]
'''
from cifar import *
args.arch = {}
args.epochs = {}
args.schedule = {}
args.gamma = {}
args.checkpoint = {}
args.depth = {}
args.wd = {}
args.cardinality = {}
#args.widen-factor = {}
args.drop = {}
'''
'''
from cifar import *
a = 'w'
e = {}
s = {}
g = {}
c = {}
d = {}
w = {}
ca = {}
dr = {}
l = {}
b = {}
tb = {}
dp = {}
args.arch = a
args.epochs = e
args.schedule = s
args.gamma = g
args.checkpoint = c
args.depth = d
args.wd = w
args.cardinality = ca
args.lr = l
args.widen_factor = {}
args.drop = dr
args.train_batch = tb
args.depth = dp
'''
class Ui_classify(QtWidgets.QWidget):

    def __init__(self):
        super(Ui_classify, self).__init__()
        self.setObjectName("classify")
        self.resize(700, 600)
        self.setWindowTitle("分类")

        # layout = QtWidgets.QListWidget(self.gridLayoutWidget)

        layout = QVBoxLayout(self)

        # wangyibo 2019.03.27 选择网络模型下拉选项框
        self.combobox1 = QComboBox(self, minimumWidth=100)
        layout.addWidget(QLabel("选择网络模型", self))
        layout.addWidget(self.combobox1)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.init_combobox1()
        self.combobox1.activated.connect(self.on_combobox1_Activate)

        # 网络导入按键
        self.NetInputButton = QToolButton(self)
        self.NetInputButton.setText("网络导入")
        layout.addWidget(self.NetInputButton)
        self.NetInputButton.clicked.connect(self.NetInput)

        # 超参数设置
        hyperparametersLabel1 = QLabel("Learning rate")
        self.Hyperparameters1LineEdit = QLineEdit(" ")
        hyperparametersLabel2 = QLabel("Batch size")
        self.Hyperparameters2LineEdit = QLineEdit(" ")
        hyperparametersLabel3 = QLabel("Epoch")
        self.Hyperparameters3LineEdit = QLineEdit(" ")
        hyperparametersLabel4 = QLabel("Gamma")
        self.Hyperparameters4LineEdit = QLineEdit(" ")
        hyperparametersLabel5 = QLabel("depth")
        self.Hyperparameters5LineEdit = QLineEdit(" ")
        layout.addWidget(hyperparametersLabel1)
        layout.addWidget(self.Hyperparameters1LineEdit)
        layout.addWidget(hyperparametersLabel2)
        layout.addWidget(self.Hyperparameters2LineEdit)
        layout.addWidget(hyperparametersLabel3)
        layout.addWidget(self.Hyperparameters3LineEdit)
        layout.addWidget(hyperparametersLabel4)
        layout.addWidget(self.Hyperparameters4LineEdit)
        layout.addWidget(hyperparametersLabel5)
        layout.addWidget(self.Hyperparameters5LineEdit)
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

        # self.addDockWidget(Qt.RightDockWidgetArea, self.AVdock)

    def opensublimetext(self):
        os.system('open /Applications/Utilities/Terminal.app')

    def affairviewer(self):



        main()


        #self.AffairViewer.addItem('当前字母 :' + letter)


    def init_combobox1(self):
        for i in range(len(items_list)):
           self.combobox1.addItem(items_list[i])
        self.combobox1.setCurrentIndex(-1)

    # wangyibo 2019.03.27 选择模型后触发的效果


    def on_combobox1_Activate(self, index):

        print(self.combobox1.count())  # 返回列表框下拉项数目
        print(self.combobox1.currentIndex())  # 返回选中项索引
        print(self.combobox1.currentText())  # 返回选中项的文本内容
        print(self.combobox1.currentData())  # 返回当前数据
        print(self.combobox1.itemData(self.combobox1.currentIndex()))
        print(self.combobox1.itemText(self.combobox1.currentIndex()))

        global a
        global e
        global s
        global g
        global c
        global d
        global w
        global ca
        global dr
        if self.combobox1.currentIndex() == 0:
            print('da')

        elif self.combobox1.currentIndex() == 1:
            # global a
            a = 'vgg19_bn'
            args.arch = a
            # global e
            e = 164
            args.epochs = e
            # global s
            s = (81, 122)
            args.schedule = s
            # global g
            g = 0.1
            args.gamma = g
            # global c
            c = 'checkpoints/cifar10/vgg19_bn'
            args.checkpoint = c
            '''
            args.arch = 'vgg19_bn'
            args.epochs = 164
            args.schedule = (81,122)
            args.gamma = 0.1
            args.checkpoint = 'checkpoints/cifar10/vgg19_bn'
            '''
        elif self.combobox1.currentIndex() == 2:
            # global a
            a = 'resnet'
            args.arch = a
            # global d
            d = 110
            args.depth = d
            # global e
            e = 164
            args.epochs = e
            # global s
            s = (81, 122)
            args.schedule = s
            # global g
            g = 0.1
            args.gamma = g
            # global w
            w = 1e-4
            args.wd = w
            # global c
            c = 'checkpoints/cifar10/resnet-110'
            args.checkpoint = c

            '''
            args.arch = 'resnet'
            args.depth = 110
            args.epochs = 164
            args.schedule = (81,122)
            args.gamma = 0.1
            args.wd = 1e-4
            args.checkpoint = 'checkpoints/cifar10/resnet-110'
            '''
        elif self.combobox1.currentIndex() == 3:
            # global a
            a = 'resnet'
            args.arch = a
            # global d
            d = 1202
            args.depth = d
            # global e
            e = 164
            args.epochs = e
            # global s
            s = (81, 122)
            args.schedule = s
            # global g
            g = 0.1
            args.gamma = g
            # global w
            w = 1e-4
            args.wd = w
            # global c
            c = 'checkpoints/cifar10/resnet-1202'
            args.checkpoint = c

            '''
            args.arch = 'resnet'
            args.depth = 1202
            args.epochs = 164
            args.schedule = (81,122)
            args.gamma = 0.1
            args.wd = 1e-4
            args.checkpoint = 'checkpoints/cifar10/resnet-1202'
            '''
        elif self.combobox1.currentIndex() == 4:
            # global a
            a = 'preresnet'
            args.arch = a
            # global d
            d = 110
            args.depth = d
            # global e
            e = 164
            args.epochs = e
            # global s
            s = (81, 122)
            args.schedule = s
            # global g
            g = 0.1
            args.gamma = g
            # global w
            w = 1e-4
            args.wd = w
            # global c
            c = 'checkpoints/cifar10/preresnet-110'
            args.checkpoint = c
            '''
            args.arch = 'preresnet'
            args.depth = 110
            args.epochs = 164
            args.schedule = (81,122)
            args.gamma = 0.1
            args.wd = 1e-4
            args.checkpoint = 'checkpoints/cifar10/preresnet-110'
            '''
        elif self.combobox1.currentIndex() == 5:
            # global a
            a = 'resnext'
            args.arch = a
            # global d
            d = 29
            args.depth = d
            # global ca
            ca = 8
            args.cardinality = ca

            # global s
            s = (150, 225)
            args.schedule = s
            # global g
            g = 0.1
            args.gamma = g
            # global w
            w = 5e-4
            args.wd = w
            # global c
            c = 'checkpoints/cifar10/resnext-8x64d'
            args.checkpoint = c
            '''
            args.arch = 'resnext'
            args.depth = 29
            args.cardinality = 8
            #args.widen-factor = '4'
            args.schedule = (150,225)
            args.gamma = 0.1
            args.wd = 5e-4
            args.checkpoint = 'checkpoints/cifar10/resnext-8x64d'
            '''


    def NetInput(self):
        NetInput_name, NetInput_type = QFileDialog.getOpenFileName(self, '选择文件', '', 'python files(*.py)')
    # cmd = ('open -a /Applications/Sublime\ Text.app 'NetInput_name'')
        os.system('open -a /Applications/Sublime\ Text.app ' + NetInput_name)
    # filepath = self.settings.get('NetInput_name')


    def run(self):
        filepath = self.settings.get('filename')


    def addNum(self):
        global a
        global e
        global s
        global g
        global c
        global d
        global w
        global ca
        global dr
        global l
        l = self.Hyperparameters1LineEdit.text()  # 获取文本框内容
        args.lr = l
        tb = self.Hyperparameters2LineEdit.text()
        args.train_batch = tb
        e = self.Hyperparameters3LineEdit.text()
        args.epochs = e
        g = self.Hyperparameters4LineEdit.text()
        args.gamma = g
        d = self.Hyperparameters5LineEdit.text()
        args.depth = d




