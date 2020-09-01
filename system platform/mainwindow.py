#!/usr/bin/env python
# -*- coding: utf8 -*-
import codecs
import os.path
import re
import sys
import subprocess
import random

from functools import partial
from collections import defaultdict




try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
    from PyQt5 import QtCore, QtGui, QtWidgets
    import numpy as np
    from PIL import Image
    import matplotlib.pyplot as plt
    from skimage import io
    import glob
    import os
    from shutil import copyfile

except ImportError:
    # needed for py3+qt4
    # Ref:
    # http://pyqt.sourceforge.net/Docs/PyQt4/incompatible_apis.html
    # http://stackoverflow.com/questions/21217399/pyqt4-qtcore-qvariant-object-instead-of-a-string
    if sys.version_info.major >= 3:
        import sip
        sip.setapi('QVariant', 2)
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

import resources
# Add internal libs
dir_name = os.path.abspath(os.path.dirname(__file__))
libs_path = os.path.join(dir_name, 'libs')
sys.path.insert(0, libs_path)
from lib import struct, newAction, newIcon, addActions, fmtShortcut
from shape import Shape
from canvas import Canvas
from zoomWidget import ZoomWidget
from labelDialog import LabelDialog
from labelFile import LabelFile, LabelFileError
from toolBar import ToolBar
from pascal_voc_io import PascalVocReader
from pascal_voc_io import XML_EXT
from ustr import ustr
from ClassifyWindow import Ui_classify
from DetectionWindow import Ui_detect
from DataenhancementWindow import Ui_dataenhance
from StateWindow import Ui_state

__appname__ = '工业视觉检测系统'


# Utility functions and classes.
def have_qstring():
    '''p3/qt5 get rid of QString wrapper as py3 has native unicode str type'''
    return not (sys.version_info.major >= 3 or QT_VERSION_STR.startswith('5.'))


def util_qt_strlistclass():
    return QStringList if have_qstring() else list


class WindowMixin(object):

    def menu(self, title, actions=None):
        menu = self.menuBar().addMenu(title)
        if actions:
            addActions(menu, actions)
        return menu

    def toolbar(self, title, actions=None):
        toolbar = ToolBar(title)
        toolbar.setObjectName(u'%sToolBar' % title)
        # toolbar.setOrientation(Qt.Vertical)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        if actions:
            addActions(toolbar, actions)
        self.addToolBar(Qt.LeftToolBarArea, toolbar)
        return toolbar


# PyQt5: TypeError: unhashable type: 'QListWidgetItem'
class HashableQListWidgetItem(QListWidgetItem):

    def __init__(self, *args):
        super(HashableQListWidgetItem, self).__init__(*args)

    def __hash__(self):
        return hash(id(self))

#wangyibo 20190325 build a child window

class ChildWindow(QWidget):
    def __init__(self, parent=None):
        super(ChildWindow, self).__init__(parent)
        self.resize(200, 200)
        self.setStyleSheet("background: black")

    def handle_click(self):
        if not self.isVisible():
            self.show()

    def handle_close(self):
        self.close()


class MainWindow(QMainWindow, WindowMixin):
    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = list(range(3))
    close_signal = pyqtSignal()

    def __init__(self, defaultFilename=None, defaultPrefdefClassFile=None, parent=None):
        # super这个用法是调用父类的构造函数
        # parent=None表示默认没有父Widget，如果指定父亲Widget，则调用之
        super(MainWindow, self).__init__(parent)
       # super(MainWindow, self).__init__()
        self.setWindowTitle(__appname__) #设置APP名称
        # Save as Pascal voc xml
        self.defaultSaveDir = "/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/Annotations" #标注文件默认存放路径
        self.usingPascalVocFormat = True #默认存储格式为VOC的格式
        # For loading all image under a directory
        self.mImgList = []
        self.dirname = None
        self.labelHist = []
        self.lastOpenDir = None

        # Whether we need to save or not.
        self.dirty = False






        # ////////////////////////////////



        #初始状态下使能
        #self.isEnableCreate = True
        self.isEnableCreateRo = True

        # Enble auto saving if pressing next
        self.autoSaving = True #默认为自动保存，防止标注过程中意外点到下一张图像
        self._noSelectionSlot = False
        self._beginner = True
        if sys.platform == "MacOS":
           self.screencastViewer = "/Applications/Google\ Chrome.app"
        elif sys.platform == "linux":
            self.screencastViewer = "firefox"
        #print(self.screencastViewer)
        self.screencast = "https://youtu.be/p0nR2YsCY_U" #演示视频地址

        # Main widgets and related state.
        self.labelDialog = LabelDialog(parent=self, listItem=self.labelHist)
        
        self.itemsToShapes = {}
        self.shapesToItems = {}
        self.prevLabelText = ''

        listLayout = QVBoxLayout() #创建一个垂直布局管理器
        listLayout.setContentsMargins(0, 0, 0, 0) #左、上、右、下的外边距设置
        
        # Create a widget for using default label
        self.useDefautLabelCheckbox = QCheckBox(u'Use default label') #创建一个复选框控件（是否使用默认标签）
        self.useDefautLabelCheckbox.setChecked(False)
        self.defaultLabelTextLine = QLineEdit() #创建一个单行文本编辑控件
        useDefautLabelQHBoxLayout = QHBoxLayout() #创建一个水平布局管理器       
        useDefautLabelQHBoxLayout.addWidget(self.useDefautLabelCheckbox)
        useDefautLabelQHBoxLayout.addWidget(self.defaultLabelTextLine)
        useDefautLabelContainer = QWidget() #创建一个基础窗口
        useDefautLabelContainer.setLayout(useDefautLabelQHBoxLayout) #启用相应的水平布局

        # Create a widget for edit and diffc button
        self.diffcButton = QCheckBox(u'difficult') #困难标注复选框控件（有些标注框难以检测，可以勾选为difficult）
        self.diffcButton.setChecked(False)
        self.diffcButton.stateChanged.connect(self.btnstate) #当状态改变时信号触发事件
        self.editButton = QToolButton() #创建一个工具按钮控件
        self.editButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # Add some of widgets to listLayout 启动相应的垂直布局
        listLayout.addWidget(self.editButton)
        listLayout.addWidget(self.diffcButton)
        listLayout.addWidget(useDefautLabelContainer)

        # Create and add a widget for showing current label items
        self.labelList = QListWidget() #创建一个列表框控件，用于显示当前图像上的所有标注框的标注类别
        labelListContainer = QWidget()
        labelListContainer.setLayout(listLayout)
        self.labelList.itemActivated.connect(self.labelSelectionChanged)
        self.labelList.itemSelectionChanged.connect(self.labelSelectionChanged)
        self.labelList.itemDoubleClicked.connect(self.editLabel)
        # Connect to itemChanged to detect checkbox changes.
        self.labelList.itemChanged.connect(self.labelItemChanged)
        listLayout.addWidget(self.labelList)

        self.dock = QDockWidget(u'有向框类别标签', self) #创建一个停靠窗口
        self.dock.setObjectName(u'Label')
        self.dock.setWidget(labelListContainer)

        #wangyibo 20190325 deeplearning widget dock


        # Tzutalin 20160906 : Add file list and dock to move faster
        self.fileListWidget = QListWidget()
        self.fileListWidget.itemDoubleClicked.connect(self.fileitemDoubleClicked)
        filelistLayout = QVBoxLayout()
        filelistLayout.setContentsMargins(0, 0, 0, 0)
        filelistLayout.addWidget(self.fileListWidget)
        fileListContainer = QWidget()
        fileListContainer.setLayout(filelistLayout)
        self.filedock = QDockWidget(u'文件列表', self)
        self.filedock.setObjectName(u'File')
        self.filedock.setWidget(fileListContainer)

        #wangyibo 20190325 try to add deep learning widget
        self.DL = QWidget()
        DLLayout = QGridLayout()
        DLLayout.addWidget(self.DL)
        DLContainer = QWidget()
        DLContainer.setLayout(DLLayout)

        self.classifyButton=QToolButton(self)
        self.classifyButton.setText("分类")
        #self.classifyButton.setIcon(QIcon("/Users/wangyibo/Downloads/LabelRorect/icons/autoname.png"))
        self.detectButton = QToolButton(self)
        self.detectButton.setText("检测")
        self.stateButton=QToolButton(self)
        self.stateButton.setText("状态窗口")


        DLLayout.addWidget(self.classifyButton,0,0)
        DLLayout.addWidget(self.detectButton,0,1)
        DLLayout.addWidget(self.stateButton,0,2)

        self.DLdock = QDockWidget(u'深度学习', self)
        self.DLdock.setObjectName(u'DL')
        self.DLdock.setWidget(DLContainer)

        self.classifyButton.clicked.connect(self.classifyTrans)
        self.detectButton.clicked.connect(self.detectTrans)
        self.stateButton.clicked.connect(self.stateTrans)








        # /////////////////////

        self.zoomWidget = ZoomWidget() #创建一个缩放窗口控件（自定义的）
        

        self.canvas = Canvas() #创建一个画布（自定义的）
        self.canvas.zoomRequest.connect(self.zoomRequest)

        scroll = QScrollArea() #创建一个滚动窗口控件
        scroll.setWidget(self.canvas)
        scroll.setWidgetResizable(True) #默认可以自动改变窗口大小
        self.scrollBars = {
            Qt.Vertical: scroll.verticalScrollBar(),
            Qt.Horizontal: scroll.horizontalScrollBar()
        }
        self.canvas.scrollRequest.connect(self.scrollRequest)

        self.canvas.newShape.connect(self.newShape)
        self.canvas.shapeMoved.connect(self.setDirty)
        self.canvas.selectionChanged.connect(self.shapeSelectionChanged)
        self.canvas.drawingPolygon.connect(self.toggleDrawingSensitive)
        self.canvas.status.connect(self.status)

        #self.enableCreateRo一旦改变，hideRRect会作出相应的响应（是否隐藏有向框标注按钮）
        self.canvas.hideRRect.connect(self.enableCreateRo) #是否隐藏有向框标注按钮

        self.setCentralWidget(scroll)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        # Tzutalin 20160906 : Add file list and dock to move faster
        self.addDockWidget(Qt.RightDockWidgetArea, self.filedock)

        #wangyibo 20190325
        self.addDockWidget(Qt.RightDockWidgetArea, self.DLdock)


        self.dockFeatures = QDockWidget.DockWidgetClosable\
            | QDockWidget.DockWidgetFloatable
        self.dock.setFeatures(self.dock.features() ^ self.dockFeatures)
        self.filedock.setFeatures(self.filedock.features() ^ self.dockFeatures)

        # Actions 添加各种动作
        action = partial(newAction, self) #partial对象调用func时连同已经被冻结的参数一同传给func函数，从而简化了调用过程

        quit = action(u'&退出', self.close,
                      'Ctrl+Q', 'quit', u'Quit application') 

        open = action(u'&打开图像', self.openFile,
                      'Ctrl+O', 'open', u'Open image or label file')

        opendir = action(u'&打开文件夹', self.openDir,
                         'Ctrl+u', 'open-dir', u'Open Dir')

        changeSavedir = action(u'&更改标注文件默认存储路径', self.changeSavedir,
                               'Ctrl+r', 'open-dir', u'Change default saved Annotation dir')

        openAnnotation = action(u'&打开标注文件', self.openAnnotation,
                                'Ctrl+Shift+O', 'openAnnotation', u'Open Annotation')

        openNextImg = action(u'&下一张图像', self.openNextImg,
                             'd', 'next', u'Open Next')

        openPrevImg = action(u'&上一张图像', self.openPrevImg,
                             'a', 'prev', u'Open Prev')

        verify = action(u'&确认', self.verifyImg,
                        'space', 'verify', u'Verify Image')

        save = action(u'&保存标注', self.saveFile,
                      'Ctrl+S', 'save', u'Save labels to file', enabled=False)
        saveAs = action(u'&另存为', self.saveFileAs,
                        'Ctrl+Shift+S', 'save-as', u'Save labels to a different file',
                        enabled=False)
        close = action(u'&关闭当前图像', self.closeFile,
                       'Ctrl+W', 'close', u'Close current file')
        #color1 = action('Box &Line Color', self.chooseColor1,
                        #'Ctrl+L', 'color_line', u'Choose Box line color')
        #color2 = action('Box &Fill Color', self.chooseColor2,
                        #'Ctrl+Shift+L', 'color', u'Choose Box fill color')

        createMode = action('Create\nRectBox', self.setCreateMode,
                            'Ctrl+N', 'new', u'Start drawing Boxs', enabled=False)
        editMode = action('&Edit\nRectBox', self.setEditMode,
                          'Ctrl+J', 'edit', u'Move and edit Boxs', enabled=False)

        #create = action('Create\nRectBox', self.createShape,
                        #'w', 'new', u'Draw a new Box', enabled=False)

        createRo = action(u'绘制有向框', self.createRoShape,
                        'e', 'robjects', u'Draw a new RotatedRBox', enabled=False)

        delete = action(u'删除有向框', self.deleteSelectedShape,
                        'Delete', 'delete', u'Delete', enabled=False)
        copy = action(u'&复制有向框', self.copySelectedShape,
                      'Ctrl+D', 'copy', u'Create a duplicate of the selected Box',
                      enabled=False)

        advancedMode = action(u'&简略风格界面', self.toggleAdvancedMode,
                              'Ctrl+Shift+A', 'expert', u'Switch to advanced mode',
                              checkable=True)

        hideAll = action(u'&隐藏所有有向框', partial(self.togglePolygons, False),
                         'Ctrl+H', 'hide', u'Hide all Boxs',
                         enabled=False)
        showAll = action(u'&显示所有有向框', partial(self.togglePolygons, True),
                         'Ctrl+A', 'show', u'Show all Boxs',
                         enabled=False)

        help = action(u'&视频指导', self.tutorial, 'Ctrl+T', 'help',
                      u'Show demos')

        zoom = QWidgetAction(self) #将自定义的widget插入基于action的容器
        zoom.setDefaultWidget(self.zoomWidget)
        self.zoomWidget.setWhatsThis(
            u"Zoom in or out of the image. Also accessible with"
            " %s and %s from the canvas." % (fmtShortcut("Ctrl+[-+]"),
                                             fmtShortcut("Ctrl+Wheel"))) #手动++——放缩或滚轮放缩
        self.zoomWidget.setEnabled(False)

        zoomIn = action(u'&放大', partial(self.addZoom, 10),
                        'Ctrl++', 'zoom-in', u'Increase zoom level', enabled=False)
        zoomOut = action(u'&缩小', partial(self.addZoom, -10),
                         'Ctrl+-', 'zoom-out', u'Decrease zoom level', enabled=False)
        zoomOrg = action(u'&原始大小', partial(self.setZoom, 100),
                         'Ctrl+=', 'zoom', u'Zoom to original size', enabled=False)
        fitWindow = action(u'&适应窗口', self.setFitWindow,
                           'Ctrl+F', 'fit-window', u'Zoom follows window size',
                           checkable=True, enabled=False)
        fitWidth = action(u'&适应窗口宽度', self.setFitWidth,
                          'Ctrl+Shift+F', 'fit-width', u'Zoom follows window width',
                          checkable=True, enabled=False)
        #wangyibo 2019.3.25 deep learning widget
        classification = action(u'&分类', self.Classification,
                                'Ctrl+Shift+C', 'classifi-cation', u'use deep learning to classify images')
        detection = action(u'&检测', self.Detection,
                           'Ctrl+Shift+D', 'detec-tion', u'use deep learning to detect images')
        autoname = action(u'&自动命名', self.AutoName,
                          'Ctrl+Shift+A', 'autoname', u'rename the images automatismly')

        dataenhancement = action(u'&扩充数据集', self.Dataenhancement,
                                 'Ctrl+Shift+E', 'data-enhancement', u'data enhancement')
        deletefile = action(u'清空数据', self.del_file,
                        'Ctrl+Shift+F', 'delete-file', u'Successfully delete all the images')
        generatetxt = action(u'生成包含文件名的txt文件', self.GenerateTxt,
                             'Ctrl+shift+G', 'generate-txt', u'Successfully generated')



        # Group zoom controls into a list for easier toggling.
        zoomActions = (self.zoomWidget, zoomIn, zoomOut,
                       zoomOrg, fitWindow, fitWidth)
        self.zoomMode = self.MANUAL_ZOOM
        self.scalers = {
            self.FIT_WINDOW: self.scaleFitWindow,
            self.FIT_WIDTH: self.scaleFitWidth,
            # Set to one to scale to 100% when loading files.
            self.MANUAL_ZOOM: lambda: 1,
        }

        edit = action(u'&编辑标签', self.editLabel,
                      'Ctrl+E', 'edit', u'Modify the label of the selected Box',
                      enabled=False) #编辑标注框类别动作
        self.editButton.setDefaultAction(edit)
        
        '''
        shapeLineColor = action('Shape &Line Color', self.chshapeLineColor,
                                icon='color_line', tip=u'Change the line color for this specific shape',
                                enabled=False)
        
        shapeFillColor = action('Shape &Fill Color', self.chshapeFillColor,
                                icon='color', tip=u'Change the fill color for this specific shape',
                                enabled=False)
        '''

        labels = self.dock.toggleViewAction()
        labels.setText(u'显示/隐藏标签面板')
        labels.setShortcut('Ctrl+Shift+L')

        # Lavel list context menu.
        labelMenu = QMenu()
        addActions(labelMenu, (edit, delete))
        self.labelList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.labelList.customContextMenuRequested.connect(
            self.popLabelListMenu)

        # Store actions for further handling.
        self.actions = struct(save=save, saveAs=saveAs, open=open, close=close,
                              #lineColor=color1, fillColor=color2,
                              #create=create, 
                              createRo=createRo, delete=delete, edit=edit, copy=copy,
                              createMode=createMode, editMode=editMode, advancedMode=advancedMode,
                              #shapeLineColor=shapeLineColor, shapeFillColor=shapeFillColor,
                              zoom=zoom, zoomIn=zoomIn, zoomOut=zoomOut, zoomOrg=zoomOrg,
                              fitWindow=fitWindow, fitWidth=fitWidth,
                              zoomActions=zoomActions,
                              autoname=autoname,
                              dataenhancement=dataenhancement,
                              deletefile=deletefile,
                              fileMenuActions=(
                                  open, opendir, save, saveAs, close, quit),
                              beginner=(), advanced=(),
                              editMenu=(edit, copy, delete),
                                        #None, color1, color2),
                              #beginnerContext=(create, edit, copy, delete),
                              beginnerContext=(createRo, edit, copy, delete),
                              advancedContext=(createMode, editMode, edit, copy,
                                               delete), #shapeLineColor, shapeFillColor),
                              #onLoadActive=(close, create, createMode, editMode),
                              onLoadActive=(close, createRo, createMode, editMode),
                              onShapesPresent=(saveAs, hideAll, showAll))

        # 菜单栏
        self.menus = struct(
            file=self.menu(u'&文件'),
            edit=self.menu(u'&编辑'),
            view=self.menu(u'&显示'),
            deeplearning=self.menu(u'&深度学习'),
            help=self.menu(u'&帮助'),
            recentFiles=QMenu(u'&打开最近文件'),
            labelList=labelMenu)

      # 具体的操作
        addActions(self.menus.file,
                   (open, opendir, changeSavedir, openAnnotation, generatetxt, self.menus.recentFiles, save, saveAs, close, None, quit)) #None相当于分界线
        addActions(self.menus.help, (help,))
        addActions(self.menus.view, (
            labels, advancedMode, None,
            hideAll, showAll, None,
            zoomIn, zoomOut, zoomOrg, None,
            fitWindow, fitWidth))
        addActions(self.menus.deeplearning,(
            classification, detection
        ))

        self.menus.file.aboutToShow.connect(self.updateFileMenu)

        # Custom context menu for the canvas widget:
        addActions(self.canvas.menus[0], self.actions.beginnerContext)
        addActions(self.canvas.menus[1], (
            action('&Copy here', self.copyShape),
            action('&Move here', self.moveShape)))

        self.tools = self.toolbar('Tools')
        self.actions.beginner = (
            #open, opendir, openNextImg, openPrevImg, verify, save, None, create, createRo, copy, delete, None,
            open, opendir, autoname, dataenhancement, deletefile, openNextImg, openPrevImg, verify, save, None, createRo, copy, delete, None,
            zoomIn, zoom, zoomOut, fitWindow, fitWidth)

        self.actions.advanced = (
            open, save, None,
            createMode, editMode, None,
            hideAll, showAll)

        self.statusBar().showMessage('%s started.' % __appname__) #状态栏
        self.statusBar().show()

        # Application state.
        self.image = QImage()
        self.filePath = ustr(defaultFilename)
        self.recentFiles = []
        self.maxRecent = 7 #能预览的最近打开过的图像的数目
        self.lineColor = None
        self.fillColor = None
        self.zoom_level = 100
        self.fit_window = False
        # Add Chris
        self.difficult = False

        # Load predefined classes to the list
        self.loadPredefinedClasses(defaultPrefdefClassFile)
        # XXX: Could be completely declarative.
        # Restore application settings.
        #根据安装的QT版本，设置不同类型
        if have_qstring():
            types = {
                'filename': QString,
                'recentFiles': QStringList,
                'window/size': QSize,
                'window/position': QPoint,
                'window/geometry': QByteArray,
                'line/color': QColor,
                'fill/color': QColor,
                'advanced': bool,
                # Docks and toolbars:
                'window/state': QByteArray,
                'savedir': QString,
                'lastOpenDir': QString,
            }
        else:
            types = {
                'filename': str,
                'recentFiles': list,
                'window/size': QSize,
                'window/position': QPoint,
                'window/geometry': QByteArray,
                'line/color': QColor,
                'fill/color': QColor,
                'advanced': bool,
                # Docks and toolbars:
                'window/state': QByteArray,
                'savedir': str,
                'lastOpenDir': str,
            }

        self.settings = settings = Settings(types)
        self.recentFiles = list(settings.get('recentFiles', []))
        size = settings.get('window/size', QSize(600, 500)) #图像窗口默认大小为(600,500)
        position = settings.get('window/position', QPoint(0, 0))
        self.resize(size)
        self.move(position)
        saveDir = ustr(settings.get('savedir', None))
        self.lastOpenDir = ustr(settings.get('lastOpenDir', None))
        if saveDir is not None and os.path.exists(saveDir):
            self.defaultSaveDir = saveDir
            self.statusBar().showMessage('%s started. Annotation will be saved to %s' %
                                         (__appname__, self.defaultSaveDir))
            self.statusBar().show()

        # or simply:
        # self.restoreGeometry(settings['window/geometry']
        self.restoreState(settings.get('window/state', QByteArray()))
        self.lineColor = QColor(settings.get('line/color', Shape.line_color))
        self.fillColor = QColor(settings.get('fill/color', Shape.fill_color))
        Shape.line_color = self.lineColor
        Shape.fill_color = self.fillColor
        # Add chris
        Shape.difficult = self.difficult

        def xbool(x):
            if isinstance(x, QVariant): #isinstance用来判断一个对象的变量类型
                return x.toBool()
            return bool(x)

        if xbool(settings.get('advanced', False)):
            self.actions.advancedMode.setChecked(True)
            self.toggleAdvancedMode()

        # Populate the File menu dynamically.
        self.updateFileMenu()
        # Since loading the file may take some time, make sure it runs in the
        # background.
        self.queueEvent(partial(self.loadFile, self.filePath or ""))

        # Callbacks:
        self.zoomWidget.valueChanged.connect(self.paintCanvas)

        self.populateModeActions()

    ## Support Functions ##

    def noShapes(self):
        return not self.itemsToShapes

    def toggleAdvancedMode(self, value=True):
        self._beginner = not value
        self.canvas.setEditing(True)
        self.populateModeActions()
        self.editButton.setVisible(not value) #编辑按钮不使能
        if value:
            self.actions.createMode.setEnabled(True) #可以创建标注框
            self.actions.editMode.setEnabled(False) #编辑模式不使能
            # self.dock.setFeatures(self.dock.features() | self.dockFeatures)
        else:
            pass
            # self.dock.setFeatures(self.dock.features() ^ self.dockFeatures)

    def populateModeActions(self):
        if self.beginner():
            tool, menu = self.actions.beginner, self.actions.beginnerContext
        else:
            tool, menu = self.actions.advanced, self.actions.advancedContext
        self.tools.clear()
        addActions(self.tools, tool)
        self.canvas.menus[0].clear()
        addActions(self.canvas.menus[0], menu)
        self.menus.edit.clear()
        #actions = (self.actions.create,) if self.beginner()\
        actions = (self.actions.createRo,) if self.beginner()\
            else (self.actions.createMode, self.actions.editMode)
        addActions(self.menus.edit, actions + self.actions.editMenu)

    def setBeginner(self):
        self.tools.clear()
        addActions(self.tools, self.actions.beginner)

    def setAdvanced(self):
        self.tools.clear()
        addActions(self.tools, self.actions.advanced)

    def setDirty(self):
        self.dirty = True
        self.canvas.verified = False
        self.actions.save.setEnabled(True)

    def setClean(self):
        self.dirty = False
        self.actions.save.setEnabled(False)
        #self.actions.create.setEnabled(True)
        self.actions.createRo.setEnabled(True)

    #创建无向框的按钮是否使能
    '''
    def enableCreate(self,b):
        self.isEnableCreate = not b
        self.actions.create.setEnabled(self.isEnableCreate)
    '''

    #创建有向框的按钮是否使能
    def enableCreateRo(self,b):
        self.isEnableCreateRo = not b
        self.actions.createRo.setEnabled(self.isEnableCreateRo)
    
    #根据输入的value值开启或关闭部分控件的功能
    def toggleActions(self, value=True):
        """Enable/Disable widgets which depend on an opened image."""
        for z in self.actions.zoomActions:
            z.setEnabled(value)
        for action in self.actions.onLoadActive:
            action.setEnabled(value)

    def queueEvent(self, function):
        QTimer.singleShot(0, function)

    #显示状态栏信息函数
    def status(self, message, delay=5000):
        # print(message)
        self.statusBar().showMessage(message, delay)
        self.statusBar().show()

    #重置整个APP状态
    def resetState(self):
        self.itemsToShapes.clear()
        self.shapesToItems.clear()
        self.labelList.clear()
        self.filePath = None
        self.imageData = None
        self.labelFile = None  #标注文件的名称
        self.canvas.resetState()

    #获取当前条目信息
    def currentItem(self):
        items = self.labelList.selectedItems()
        if items:
            return items[0]
        return None

    #向最近打开的文件中添加当前打开文件路径
    def addRecentFile(self, filePath):
        if filePath in self.recentFiles:
            self.recentFiles.remove(filePath)
        elif len(self.recentFiles) >= self.maxRecent:
            self.recentFiles.pop() #移除列表中的一个元素（默认最后一个元素）
        self.recentFiles.insert(0, filePath)

    #返回_beginner（bool型）
    def beginner(self):
        return self._beginner

    #返回_beginner的反面
    def advanced(self):
        return not self.beginner()

    ## Callbacks ##
    def tutorial(self):
        subprocess.Popen([self.screencastViewer, self.screencast]) #开启一个子进程来执行Popen中的shell指令

    # create Normal Rect
    '''
    def createShape(self):
        assert self.beginner()
        self.canvas.setEditing(False)
        self.canvas.canDrawRotatedRect = False
        self.actions.create.setEnabled(False)
        self.actions.createRo.setEnabled(False)
    '''

    # create Rotated Rect 定义点下创建有向矩形框时所需完成的动作函数
    def createRoShape(self):
        assert self.beginner()
        self.canvas.setEditing(False)
        self.canvas.canDrawRotatedRect = True
        #self.actions.create.setEnabled(False)
        self.actions.createRo.setEnabled(False)

    #正在绘制时设置边界框无法编辑和移动;不绘制时开启等候绘制的相关动作
    def toggleDrawingSensitive(self, drawing=True):
        """In the middle of drawing, toggling between modes should be disabled."""
        self.actions.editMode.setEnabled(not drawing)
        if not drawing and self.beginner():
            # Cancel creation.
            print('Cancel creation.')
            self.canvas.setEditing(True)
            self.canvas.restoreCursor()
            #self.actions.create.setEnabled(True)
            self.actions.createRo.setEnabled(True)
            

    def toggleDrawMode(self, edit=True):
        self.canvas.setEditing(edit)
        self.actions.createMode.setEnabled(edit)
        self.actions.editMode.setEnabled(not edit)

    def setCreateMode(self):
        print('setCreateMode')
        assert self.advanced()
        self.toggleDrawMode(False)

    def setEditMode(self):
        assert self.advanced()
        self.toggleDrawMode(True)

    def updateFileMenu(self):
        currFilePath = self.filePath #当前文件路径

        def exists(filename):
            return os.path.exists(filename)
        menu = self.menus.recentFiles #加载最近打开的文件
        menu.clear()
        files = [f for f in self.recentFiles if f !=
                 currFilePath and exists(f)]
        for i, f in enumerate(files):
            icon = newIcon('labels')
            action = QAction(
                icon, '&%d %s' % (i + 1, QFileInfo(f).fileName()), self) #在menu下的open recent一栏中显示之前打开过的文件预览
            action.triggered.connect(partial(self.loadRecent, f)) #做好加载相应注释框的准备
            menu.addAction(action)

    def popLabelListMenu(self, point):
        self.menus.labelList.exec_(self.labelList.mapToGlobal(point)) #mapToGlobal将当前控件的相对位置转化为屏幕上的绝对位置

    #编辑标签函数
    def editLabel(self, item=None):
        if not self.canvas.editing():
            return
        item = item if item else self.currentItem()
        text = self.labelDialog.popUp(item.text())
        if text is not None:
            item.setText(text)
            self.setDirty()

    # Tzutalin 20160906 : Add file list and dock to move faster
    #双击File List区域中的图像路径直接加载图像
    def fileitemDoubleClicked(self, item=None):
        currIndex = self.mImgList.index(ustr(item.text()))
        if currIndex < len(self.mImgList):
            filename = self.mImgList[currIndex]
            if filename:
                self.loadFile(filename) #加载对应图像

    # Add chris
    def btnstate(self, item= None):
        """ Function to handle difficult examples
         date on each object """
        if not self.canvas.editing():
            return

        item = self.currentItem()
        if not item: # If not selected Item, take the first one
            item = self.labelList.item(self.labelList.count()-1)

        difficult = self.diffcButton.isChecked()

        try:
            shape = self.itemsToShapes[item]
        except:
            pass #当前item不存在标注框直接跳过
        # Checked and Update
        try:
            if difficult != shape.difficult:
                shape.difficult = difficult
                self.setDirty()
            else:  # User probably changed item visibility 用户可能改变了当前item的可见
                self.canvas.setShapeVisible(shape, item.checkState() == Qt.Checked)
        except:
            pass

    # React to canvas signals. 响应canvas信号
    def shapeSelectionChanged(self, selected=False):
        if self._noSelectionSlot:
            self._noSelectionSlot = False
        else:
            shape = self.canvas.selectedShape
            if shape:
                self.shapesToItems[shape].setSelected(True)
            else:
                self.labelList.clearSelection()
        #根据selected对一系列控件设置使能
        self.actions.delete.setEnabled(selected)
        self.actions.copy.setEnabled(selected)
        self.actions.edit.setEnabled(selected)
        #self.actions.shapeLineColor.setEnabled(selected)
        #self.actions.shapeFillColor.setEnabled(selected)

    #添加标签（将当前标签加入labelList）
    def addLabel(self, shape):
        item = HashableQListWidgetItem(shape.label)
        print('add label')
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked)
        self.itemsToShapes[item] = shape
        self.shapesToItems[shape] = item
        self.labelList.addItem(item)
        for action in self.actions.onShapesPresent:
            action.setEnabled(True) #使与添加标签相关的动作全部使能

    #移除标签（从labelList中移除当前标签）
    def remLabel(self, shape):
        if shape is None:
            # print('rm empty label')
            return
        item = self.shapesToItems[shape]
        self.labelList.takeItem(self.labelList.row(item)) #takeItem用于删除当前item
        del self.shapesToItems[shape] #del删除当前变量
        del self.itemsToShapes[item]

    #加载标签（并显示在当前画布上）
    def loadLabels(self, shapes):
        s = []
        for label, points, direction, isRotated, line_color, fill_color, difficult in shapes:
            shape = Shape(label=label)
            for x, y in points:
                shape.addPoint(QPointF(x, y)) #循环加入当前标注框的四个顶点坐标信息
            shape.difficult = difficult
            shape.direction = direction
            shape.isRotated = isRotated
            shape.close()
            s.append(shape)
            self.addLabel(shape)

            if line_color:
                shape.line_color = QColor(*line_color)
            if fill_color:
                shape.fill_color = QColor(*fill_color)

        self.canvas.loadShapes(s)

    #保存标签
    def saveLabels(self, annotationFilePath):
        annotationFilePath = ustr(annotationFilePath)
        if self.labelFile is None:  #如果还没有保存过当图像的标注信息，则创立一个保存文件
            self.labelFile = LabelFile() #创立保存文件
            self.labelFile.verified = self.canvas.verified

        #按一定格式存储标签信息，为后续写入文件做准备
        def format_shape(s):
            return dict(label=s.label,
                        line_color=s.line_color.getRgb()
                        if s.line_color != self.lineColor else None,
                        fill_color=s.fill_color.getRgb()
                        if s.fill_color != self.fillColor else None,
                        points=[(p.x(), p.y()) for p in s.points],
                       # add chris
                        difficult = s.difficult,
                        # You Hao 2017/06/21
                        # add for rotated bounding box
                        direction = s.direction,
                        center = s.center,
                        isRotated = s.isRotated)

        shapes = [format_shape(shape) for shape in self.canvas.shapes]
        # Can add differrent annotation formats here
        try:
            if self.usingPascalVocFormat is True:
                print ('Img: ' + self.filePath + ' -> Its xml: ' + annotationFilePath)
                self.labelFile.savePascalVocFormat(annotationFilePath, shapes, self.filePath, self.imageData,
                                                   self.lineColor.getRgb(), self.fillColor.getRgb()) #按VOC格式写入xml文件中
            else:
                self.labelFile.save(annotationFilePath, shapes, self.filePath, self.imageData,
                                    self.lineColor.getRgb(), self.fillColor.getRgb()) #此函数似乎没有定义
            return True
        except LabelFileError as e:
            self.errorMessage(u'Error saving label data',
                              u'<b>%s</b>' % e)
            return False

    #拷贝选中的标注框
    def copySelectedShape(self):
        self.addLabel(self.canvas.copySelectedShape())
        # fix copy and delete
        self.shapeSelectionChanged(True)

    def labelSelectionChanged(self):
        item = self.currentItem()
        if item and self.canvas.editing():
            self._noSelectionSlot = True
            self.canvas.selectShape(self.itemsToShapes[item])
            shape = self.itemsToShapes[item]
            # Add Chris
            self.diffcButton.setChecked(shape.difficult)

    def labelItemChanged(self, item):
        shape = self.itemsToShapes[item]
        label = item.text()
        if label != shape.label:
            shape.label = item.text()
            self.setDirty()
        else:  # User probably changed item visibility
            self.canvas.setShapeVisible(shape, item.checkState() == Qt.Checked)

    # Callback functions:
    #回调函数
    def newShape(self):
        """Pop-up and give focus to the label editor.

        position MUST be in global coordinates. 位置必须相对于全局坐标系
        """
        if not self.useDefautLabelCheckbox.isChecked() or not self.defaultLabelTextLine.text():
            if len(self.labelHist) > 0:
                self.labelDialog = LabelDialog(
                    parent=self, listItem=self.labelHist)

            text = self.labelDialog.popUp(text=self.prevLabelText)
        else:
            text = self.defaultLabelTextLine.text()

        # Add Chris
        self.diffcButton.setChecked(False)
        if text is not None:
            self.prevLabelText = text
            self.addLabel(self.canvas.setLastLabel(text))
            if self.beginner():  # Switch to edit mode.
                self.canvas.setEditing(True)
                #self.actions.create.setEnabled(self.isEnableCreate)
                self.actions.createRo.setEnabled(self.isEnableCreateRo)
            else:
                self.actions.editMode.setEnabled(True)
            self.setDirty()

            if text not in self.labelHist:
                self.labelHist.append(text)
        else:
            # self.canvas.undoLastLine()
            self.canvas.resetAllLines()

    #响应滑动条请求（用于调整图像的位置）
    def scrollRequest(self, delta, orientation):
        units = - delta / (8 * 15) #滚轮移动一步输出的delta的绝对值为120
        bar = self.scrollBars[orientation] #滑动方向
        bar.setValue(bar.value() + bar.singleStep() * units)

    #设置缩放(实现缩放)
    def setZoom(self, value):
        self.actions.fitWidth.setChecked(False)
        self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.MANUAL_ZOOM
        self.zoomWidget.setValue(value)

    #在原始基础上添加缩放量
    def addZoom(self, increment=10):
        self.setZoom(self.zoomWidget.value() + increment)

    #用于响应鼠标滚轮，从而实现缩放
    # Modified by Chenbin Zheng, Fix angle error 2018/11/26
    def zoomRequest(self, delta):
        units = delta / (8 * 15) #滚轮移动一步输出的delta的绝对值为120
        #scale = 1
        #self.addZoom(scale * units)
        self.addZoom(units)

    #调整画布大小以合适原始设定的窗口大小
    def setFitWindow(self, value=True):
        if value:
            self.actions.fitWidth.setChecked(False)
        self.zoomMode = self.FIT_WINDOW if value else self.MANUAL_ZOOM
        self.adjustScale()

    #调整画布大小以合适原始设定的窗口宽度
    def setFitWidth(self, value=True):
        if value:
            self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.FIT_WIDTH if value else self.MANUAL_ZOOM
        self.adjustScale()

    #用于显示或隐藏所有标注，当value为True时显示所有，为False时隐藏所有
    def togglePolygons(self, value):
        for item, shape in self.itemsToShapes.items():
            item.setCheckState(Qt.Checked if value else Qt.Unchecked)

    #加载文件函数（可以是图像文件也可以是标注文件，但通过程序可以发现实际上只支持加载图像文件，故后续可以把这部分补全或直接删除）
    def loadFile(self, filePath=None):
        """Load the specified file, or the last opened file if None."""
        self.resetState()
        self.canvas.setEnabled(False)
        if filePath is None:
            filePath = self.settings.get('filename')

        unicodeFilePath = ustr(filePath)
        # Tzutalin 20160906 : Add file list and dock to move faster
        # Highlight the file item
        if unicodeFilePath and self.fileListWidget.count() > 0:
            index = self.mImgList.index(unicodeFilePath)
            fileWidgetItem = self.fileListWidget.item(index)
            fileWidgetItem.setSelected(True)

        if unicodeFilePath and os.path.exists(unicodeFilePath):
            if LabelFile.isLabelFile(unicodeFilePath): #若加载的文件为标注文件，则self.labelFile不是None
                try:
                    self.labelFile = LabelFile(unicodeFilePath)
                except LabelFileError as e:
                    self.errorMessage(u'Error opening file',
                                      (u"<p><b>%s</b></p>"
                                       u"<p>Make sure <i>%s</i> is a valid label file.")
                                      % (e, unicodeFilePath))
                    self.status("Error reading %s" % unicodeFilePath)
                    return False
                self.imageData = self.labelFile.imageData
                self.lineColor = QColor(*self.labelFile.lineColor)
                self.fillColor = QColor(*self.labelFile.fillColor)
            else:  #否则直接加载图像（即当前所要加载的是图像文件不是标注文件）
                # Load image:
                # read data first and store for saving into label file.
                self.imageData = read(unicodeFilePath, None)
                self.labelFile = None #当前加载的是图像文件时设置为None
            image = QImage.fromData(self.imageData)
            if image.isNull():
                self.errorMessage(u'Error opening file',
                                  u"<p>Make sure <i>%s</i> is a valid image file." % unicodeFilePath)
                self.status("Error reading %s" % unicodeFilePath)
                return False
            self.status("Loaded %s" % os.path.basename(unicodeFilePath))
            self.image = image
            #print(unicodeFilePath)
            img = Image.open(unicodeFilePath)

            #filename1 = os.path.splitext(unicodeFilePath)[0];  # 文件名
            filetype1 = os.path.splitext(unicodeFilePath)[1];  # 文件类型
            #print(filename1)

            '''
            将打开的图片保存到指定文件夹
            '''
            img.save(os.path.join('/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/JPEGImage', unicodeFilePath.split("/")[-1]))
            self.filePath = unicodeFilePath
            self.canvas.loadPixmap(QPixmap.fromImage(image))
            if self.labelFile:
                self.loadLabels(self.labelFile.shapes) #如果之前标注过，则先加载之前的标注信息
            self.setClean() #进行标注前的操作
            self.canvas.setEnabled(True)
            self.adjustScale(initial=True)  #初始为FIT_WINDOW模式
            self.paintCanvas() #绘制画布
            self.addRecentFile(self.filePath) #加入最近打开文件队列
            self.toggleActions(True) #部分控件初始化（使能/不使能）

            # Label xml file and show bound box according to its filename
            if self.usingPascalVocFormat is True:
                if self.defaultSaveDir is not None:
                    basename = os.path.basename(
                        os.path.splitext(self.filePath)[0]) + XML_EXT #os.path.basename返回对应路径下的文件名（即文件名，且不含扩展名）
                    xmlPath = os.path.join(self.defaultSaveDir, basename) #获取该图像对应的标注文件完整路径
                    self.loadPascalXMLByFilename(xmlPath) #加载相应的标注框，并显示在画布上
                else:
                    xmlPath = filePath.split(".")[0] + XML_EXT
                    if os.path.isfile(xmlPath):
                        self.loadPascalXMLByFilename(xmlPath)

            self.setWindowTitle(__appname__ + ' ' + filePath) #修改此时的主窗口名

            # Default : select last item if there is at least one item 将标注框中最后一个标注Item设置为当前Item
            if self.labelList.count():
                self.labelList.setCurrentItem(self.labelList.item(self.labelList.count()-1))
                # self.labelList.setItemSelected(self.labelList.item(self.labelList.count()-1), True)

            self.canvas.setFocus(True)
            return True
        return False

    def resizeEvent(self, event):
        if self.canvas and not self.image.isNull()\
           and self.zoomMode != self.MANUAL_ZOOM:
            self.adjustScale()
        super(MainWindow, self).resizeEvent(event)

    #绘制画布
    def paintCanvas(self):
        assert not self.image.isNull(), "cannot paint null image"
        self.canvas.scale = 0.01 * self.zoomWidget.value()
        self.canvas.adjustSize()
        self.canvas.update()

    #根据zoomMode调整zoomWidget大小
    def adjustScale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoomMode]() #此代码会调用scaleFitWindow函数完成缩放因子的计算
        self.zoomWidget.setValue(int(100 * value))

    #如果zoomMode为FIT_WINDOW，则根据下面函数计算出所需要缩放的比例
    def scaleFitWindow(self):
        """Figure out the size of the pixmap in order to fit the main widget."""
        e = 2.0  # So that no scrollbars are generated.
        w1 = self.centralWidget().width() - e
        h1 = self.centralWidget().height() - e
        a1 = w1 / h1 #原始设定的窗口宽高比
        # Calculate a new scale value based on the pixmap's aspect ratio.
        w2 = self.canvas.pixmap.width() - 0.0
        h2 = self.canvas.pixmap.height() - 0.0
        a2 = w2 / h2 #当前画布的宽高比
        return w1 / w2 if a2 >= a1 else h1 / h2

    #如果zoomMode为FIT_WIDTH，则根据下面函数计算出所需要缩放的比例
    def scaleFitWidth(self):
        # The epsilon does not seem to work too well here.
        w = self.centralWidget().width() - 2.0
        return w / self.canvas.pixmap.width()

    def closeEvent(self, event):
        if not self.mayContinue():
            event.ignore()
        s = self.settings
        # If it loads images from dir, don't load it at the begining
        if self.dirname is None:
            s['filename'] = self.filePath if self.filePath else ''
        else:
            s['filename'] = ''

        s['window/size'] = self.size()
        s['window/position'] = self.pos()
        s['window/state'] = self.saveState()
        s['line/color'] = self.lineColor
        s['fill/color'] = self.fillColor
        s['recentFiles'] = self.recentFiles
        s['advanced'] = not self._beginner
        if self.defaultSaveDir is not None and len(self.defaultSaveDir) > 1:
            s['savedir'] = ustr(self.defaultSaveDir)
        else:
            s['savedir'] = ""

        if self.lastOpenDir is not None and len(self.lastOpenDir) > 1:
            s['lastOpenDir'] = self.lastOpenDir
        else:
            s['lastOpenDir'] = ""

    ## User Dialogs ##
    #加载最近的文件
    def loadRecent(self, filename):
        if self.mayContinue():
            self.loadFile(filename)

    #扫描文件夹中所有文件，并返回所有文件的绝对路径
    def scanAllImages(self, folderPath):
        extensions = ['.jpeg', '.jpg', '.png', '.bmp']
        images = []

        for root, dirs, files in os.walk(folderPath):
            for file in files:
                if file.lower().endswith(tuple(extensions)):
                    relatviePath = os.path.join(root, file) #相对路径
                    path = ustr(os.path.abspath(relatviePath)) #绝对路径
                    images.append(path)
        images.sort(key=lambda x: x.lower())
        return images

    #改变保存路径
    def changeSavedir(self, _value=False):
        if self.defaultSaveDir is not None:
            path = ustr(self.defaultSaveDir)
        else:
            path = '.'

        dirpath = ustr(QFileDialog.getExistingDirectory(self,
                                                       '%s - Save to the directory' % __appname__, path,  QFileDialog.ShowDirsOnly
                                                       | QFileDialog.DontResolveSymlinks))

        if dirpath is not None and len(dirpath) > 1:
            self.defaultSaveDir = dirpath

        self.statusBar().showMessage('%s . Annotation will be saved to %s' %
                                     ('Change saved folder', self.defaultSaveDir))
        self.statusBar().show()

    #打开标注文件（通过浏览器打开）
    # Modified by Chenbin Zheng, 2018/11/26
    def openAnnotation(self, _value=False):
        '''
        if self.filePath is None:
            return

        path = os.path.dirname(ustr(self.filePath))\
            if self.filePath else '.'
        '''
        path = "/home/"
        if self.usingPascalVocFormat:
            filters = "Open Annotation XML file (%s)" % \
                      ' '.join(['*.xml'])
            filename = QFileDialog.getOpenFileName(self,'%s - Choose a xml file' % __appname__, path, filters)
            if filename:
                if isinstance(filename, (tuple, list)):
                    filename = filename[0]
            #print("filename:",filename)
            if have_qstring():
               filename = str(filename)
            subprocess.Popen([self.screencastViewer, filename])
            #self.loadPascalXMLByFilename(filename)

    #打开文件夹
    def openDir(self, _value=False):
        if not self.mayContinue():
            return

        path = os.path.dirname(self.filePath)\
            if self.filePath else '.'

        if self.lastOpenDir is not None and len(self.lastOpenDir) > 1:
            path = self.lastOpenDir

        dirpath = ustr(QFileDialog.getExistingDirectory(self,
                                                     '%s - Open Directory' % __appname__, path,  QFileDialog.ShowDirsOnly
                                                     | QFileDialog.DontResolveSymlinks))

        if dirpath is not None and len(dirpath) > 1:
            self.lastOpenDir = dirpath

        self.dirname = dirpath
        self.filePath = None
        self.fileListWidget.clear()
        self.mImgList = self.scanAllImages(dirpath) #扫描文件夹中的所有文件，也可以看出self.mImgList里保存的是所有文件的绝对路径
        self.openNextImg() #打开下一张图像
        for imgPath in self.mImgList:
            img = Image.open(imgPath)
            img.save(os.path.join('/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/JPEGImage',
                                  imgPath.split("/")[-1]))
            item = QListWidgetItem(imgPath)
            self.fileListWidget.addItem(item) #加载入File List中

    #校验图像
    def verifyImg(self, _value=False):
        # Proceding next image without dialog if having any label
         if self.filePath is not None:
            try:
                self.labelFile.toggleVerify()
            except AttributeError:
                # If the labelling file does not exist yet, create if and
                # re-save it with the verified attribute.
                self.saveFile()
                if self.labelFile is not None:
                    self.labelFile.toggleVerify()
            if self.labelFile is not None:
                self.canvas.verified = True
            self.paintCanvas()
            self.saveFile()

    #打开前一张图像
    def openPrevImg(self, _value=False):
        if not self.mayContinue():
            return

        if len(self.mImgList) <= 0:
            return

        if self.filePath is None:
            return

        currIndex = self.mImgList.index(self.filePath)
        if currIndex - 1 >= 0:
            filename = self.mImgList[currIndex - 1]
            if filename:
                self.loadFile(filename)

    #打开下一张图像
    def openNextImg(self, _value=False):
        # Proceding next image without dialog if having any label 如果点下打开下一张图像，会对当前图像的标注结果自动进行保存
        if self.autoSaving is True and self.defaultSaveDir is not None:
            if self.dirty is True: 
                self.dirty = False
                self.canvas.verified = True               
                self.saveFile()

        if not self.mayContinue():
            return

        if len(self.mImgList) <= 0:
            return

        filename = None
        if self.filePath is None:
            filename = self.mImgList[0]
        else:
            currIndex = self.mImgList.index(self.filePath)
            if currIndex + 1 < len(self.mImgList):
                filename = self.mImgList[currIndex + 1]

        if filename:
            self.loadFile(filename)

    #打开文件
    def openFile(self, _value=False):
        if not self.mayContinue():
            return
        path = os.path.dirname(ustr(self.filePath)) if self.filePath else '.'
        formats = ['*.%s' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats()]
        filters = "Image & Label files (%s)" % ' '.join(formats + ['*%s' % LabelFile.suffix])
        filename = QFileDialog.getOpenFileName(self, '%s - Choose Image or Label file' % __appname__, path, filters)
        if filename:
            if isinstance(filename, (tuple, list)):
                filename = filename[0]
            self.loadFile(filename)

    #先获取保存的标注文件名称，再调用_saveFile函数保存标注文件
    def saveFile(self, _value=False):
        if self.defaultSaveDir is not None and len(ustr(self.defaultSaveDir)):
            if self.filePath:
                imgFileName = os.path.basename(self.filePath)
                savedFileName = os.path.splitext(imgFileName)[0] + XML_EXT
                savedPath = os.path.join(ustr(self.defaultSaveDir), savedFileName) #保存路径
                self._saveFile(savedPath)
        else:
            imgFileDir = os.path.dirname(self.filePath)
            imgFileName = os.path.basename(self.filePath)
            savedFileName = os.path.splitext(imgFileName)[0] + XML_EXT
            savedPath = os.path.join(imgFileDir, savedFileName)
            self._saveFile(savedPath if self.labelFile
                           else self.saveFileDialog())

    #另存为
    def saveFileAs(self, _value=False):
        assert not self.image.isNull(), "cannot save empty image"
        self._saveFile(self.saveFileDialog())

    #保存文件对话框
    def saveFileDialog(self):
        caption = '%s - Choose File' % __appname__
        filters = 'File (*%s)' % LabelFile.suffix
        openDialogPath = self.currentPath() #当前文件路径
        dlg = QFileDialog(self, caption, openDialogPath, filters)
        dlg.setDefaultSuffix(LabelFile.suffix[1:])
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        filenameWithoutExtension = os.path.splitext(self.filePath)[0]
        dlg.selectFile(filenameWithoutExtension)
        dlg.setOption(QFileDialog.DontUseNativeDialog, False)
        if dlg.exec_():
            return dlg.selectedFiles()[0]
        return ''

    #调用saveLabels进行保存标注信息
    def _saveFile(self, annotationFilePath):
        if annotationFilePath and self.saveLabels(annotationFilePath):
            self.setClean()
            self.statusBar().showMessage('Saved to  %s' % annotationFilePath)
            self.statusBar().show()

    #关闭文件
    def closeFile(self, _value=False):
        if not self.mayContinue():
            return
        self.resetState()
        self.setClean()
        self.toggleActions(False)
        self.canvas.setEnabled(False)
        self.actions.saveAs.setEnabled(False)

    #判断是否接着进行标注
    def mayContinue(self):
        return not (self.dirty and not self.discardChangesDialog())

    #是否丢弃当前的改动
    def discardChangesDialog(self):
        yes, no = QMessageBox.Yes, QMessageBox.No
        #msg = u'You have unsaved changes, proceed anyway?'
        msg = u'你有未保存的改动，是否舍弃这些改动?'
        return yes == QMessageBox.warning(self, u'注意', msg, yes | no)

    #使用QMessageBox显示报错信息
    def errorMessage(self, title, message):
        return QMessageBox.critical(self, title,
                                    '<p><b>%s</b></p>%s' % (title, message)) #QMessageBox.critical为QMessageBox的一类窗口，用于提示严重错误

    #获取当前文件的路径（不含文件名）
    def currentPath(self):
        return os.path.dirname(self.filePath) if self.filePath else '.' #os.path.dirname去掉文件名，返回目录 

    '''
    def chooseColor1(self):
        color = self.colorDialog.getColor(self.lineColor, u'Choose line color',
                                          default=DEFAULT_LINE_COLOR)
        if color:
            self.lineColor = color
            # Change the color for all shape lines:
            Shape.line_color = self.lineColor
            self.canvas.update()
            self.setDirty()

    def chooseColor2(self):
        color = self.colorDialog.getColor(self.fillColor, u'Choose fill color',
                                          default=DEFAULT_FILL_COLOR)
        if color:
            self.fillColor = color
            Shape.fill_color = self.fillColor
            self.canvas.update()
            self.setDirty()
    '''

    #删除选中的标注边界框
    def deleteSelectedShape(self):
        self.remLabel(self.canvas.deleteSelected())  #调用remLabel函数删除选中的边界框
        self.setDirty()
        if self.noShapes():
            for action in self.actions.onShapesPresent:
                action.setEnabled(False)
 
    '''
    def chshapeLineColor(self):
        color = self.colorDialog.getColor(self.lineColor, u'Choose line color',
                                          default=DEFAULT_LINE_COLOR)
        if color:
            self.canvas.selectedShape.line_color = color
            self.canvas.update()
            self.setDirty()

    def chshapeFillColor(self):
        color = self.colorDialog.getColor(self.fillColor, u'Choose fill color',
                                          default=DEFAULT_FILL_COLOR)
        if color:
            self.canvas.selectedShape.fill_color = color
            self.canvas.update()
            self.setDirty()
    '''

    #复制一个选中的边界框
    def copyShape(self):
        self.canvas.endMove(copy=True) #关闭边界框移动功能
        self.addLabel(self.canvas.selectedShape) #对复制的该边界框添加一个标签
        self.setDirty()

    #移动边界框
    def moveShape(self):
        self.canvas.endMove(copy=False) #开启边界框移动功能
        self.setDirty()

    def loadPredefinedClasses(self, predefClassesFile):
        if os.path.exists(predefClassesFile) is True:
            with codecs.open(predefClassesFile, 'r', 'utf8') as f:
                for line in f:
                    line = line.strip() #返回移除字符串头尾空格后生成的新字符串
                    if self.labelHist is None:
                        self.lablHist = [line]
                    else:
                        self.labelHist.append(line)

    #加载VOC格式的标注文件
    def loadPascalXMLByFilename(self, xmlPath):
        if self.filePath is None:
            return
        if os.path.isfile(xmlPath) is False:
            return

        tVocParseReader = PascalVocReader(xmlPath) #读取xmlPath路径对应的标注文件，并解析
        shapes = tVocParseReader.getShapes()
        self.loadLabels(shapes)
        self.canvas.verified = tVocParseReader.verified

    def Classification(self, item=None):
        self.classifyN = Ui_classify()
        self.classifyN.show()
    def Detection(self):
        self.detectN = Ui_detect()
        self.detectN.show()
    def AutoName(self):

        path = "/Users/wangyibo/Downloads/LabelRorect/LabelWork"
        i=0
        filelist = os.listdir(path)  # 该文件夹下所有的文件（包括文件夹）
        for files in filelist:  # 遍历所有文件
            i = i + 1
            Olddir = os.path.join(path, files);  # 原来的文件路径
            if os.path.isdir(Olddir):  # 如果是文件夹则跳过
                continue;
            filename = os.path.splitext(files)[0];  # 文件名
            filetype = os.path.splitext(files)[1];  # 文件扩展名
            Newdir = os.path.join(path, '00000'+str(i) + filetype);  # 新的文件路径
            os.rename(Olddir, Newdir)  # 重命名
        self.setClean()
        self.statusBar().showMessage('all the files are successfully autonamed')
        self.statusBar().show()

    def classifyTrans(self):
        self.classifyN = Ui_classify()
        self.classifyN.show()

        # self.haoN.exec_()
    def detectTrans(self):
        self.detectN = Ui_detect()
        self.detectN.show()

        # self.haoN.exec_()
    def stateTrans(self):
        self.stateN = Ui_state()
        self.stateN.show()



    def Dataenhancement(self):
        self.dataenhanceN = Ui_dataenhance()
        self.dataenhanceN.show()

    def del_file(self):
        path1 = '/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/JPEGImage'
        ls = os.listdir(path1)
        for i in ls:
            c_path = os.path.join(path1, i)
            if os.path.isdir(c_path):
                del_file(c_path)
            else:
                os.remove(c_path)

        path2 = '/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/ImageSets/Main'
        ls = os.listdir(path2)
        for i in ls:
            c_path = os.path.join(path2, i)
            if os.path.isdir(c_path):
                del_file(c_path)
            else:
                os.remove(c_path)

        path3 = '/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/Annotations'
        ls = os.listdir(path3)
        for i in ls:
            c_path = os.path.join(path3, i)
            if os.path.isdir(c_path):
                del_file(c_path)
            else:
                os.remove(c_path)


    def GenerateTxt(self):
        #copyfile('/Users/wangyibo/Downloads/LabelRorect/生成txt.BAT', '/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/JPEGImage/生成txt.BAT')
        #NetInput_name, NetInput_type = QFileDialog.getOpenFileName(self, '选择文件', '', 'BAT files(*.BAT)')
        #os.system('cd /Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/JPEGImage')
        #os.system('DIR  *.*/B>train.txt')

        trainval_percent = 1# trainval数据集占所有数据的比例
        train_percent = 0.5# train数据集占trainval数据的比例
        xmlfilepath = '/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/Annotations'
        txtsavepath = '/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/ImageSets/Main'
        total_xml = os.listdir(xmlfilepath)
        num = len(total_xml)
        list = range(num)
        tv = int(num * trainval_percent)
        tr = int(tv * train_percent)
        trainval = random.sample(list, tv)
        train = random.sample(trainval, tr)
        ftrainval = open('/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/ImageSets/Main/trainval.txt', 'w')
        ftest = open('/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/ImageSets/Main/test.txt', 'w')
        ftrain = open('/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/ImageSets/Main/train.txt', 'w')
        fval = open('/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/ImageSets/Main/val.txt', 'w')
        for i in list:
            name = total_xml[i][:-4] + '\n'
            if i in trainval:
                ftrainval.write(name)
                if i in train:
                    ftrain.write(name)
                else:
                    fval.write(name)
            else:
                ftest.write(name)
        ftrainval.close()
        ftrain.close()
        fval.close()
        ftest.close()








#QSettings的便利字典封装
class Settings(object):
    """Convenience dict-like wrapper around QSettings."""

    def __init__(self, types=None):
        self.data = QSettings() #保存很多基础类型的设置
        self.types = defaultdict(lambda: QVariant, types if types else {}) #defaultdict:当key不存在时，返回的是工厂函数的默认值

    def __setitem__(self, key, value):
        t = self.types[key]
        self.data.setValue(key,
                           t() if not isinstance(value, t) else value)

    def __getitem__(self, key):
        return self._cast(key, self.data.value(key))

    def get(self, key, default=None):
        return self._cast(key, self.data.value(key, default))

    def _cast(self, key, value):
        # XXX: Very nasty way of converting types to QVariant methods :P
        t = self.types.get(key)
        if t is not None and t != QVariant:
            if t is str:
                return ustr(value)
            else:
                try:
                    method = getattr(QVariant, re.sub(
                        '^Q', 'to', t.__name__, count=1))
                    return method(value)
                except AttributeError as e:
                    # print(e)
                    return value
        return value

#反转颜色（未用到的函数）
def inverted(color):
    return QColor(*[255 - v for v in color.getRgb()])

#更改图像分辨率为1280*720
def convertjpg(jpgfile, outdir, width=1280, height=720):
    img = Image.open(jpgfile)
    new_img = img.resize((width, height), Image.BILINEAR)
    new_img.save(os.path.join(outdir, os.path.basename(jpgfile)))

#翻转图片
def FlipImg(jpgfile, outdir):
    img = Image.open(jpgfile)
    flipped_img = np.fliplr(img)
    flipped_img.save(os.path.join(outdir, os.path.basename(jpgfile)))

#图像加噪
def NoiseImg(jpgfile, outdir):
    img = Image.open(jpgfile)
    noise = np.random.randint(5, size=(164, 278, 4), dtype='uint8')

    for i in range(WIDTH):
        for j in range(HEIGHT):
            for k in range(DEPTH):
                if (img[i][j][k] != 255):
                    img[i][j][k] += noise[i][j][k]

#读入图像（使用open实现）
def read(filename, default=None):
    try:
        with open(filename, 'rb') as f:
            return f.read()
    except:
        return default


def get_main_app(argv=[]):
    """
    Standard boilerplate Qt application code.
    Do everything but app.exec_() -- so that we can test the application in one thread
    """
    app = QApplication(argv)
    app.setApplicationName(__appname__)
    app.setWindowIcon(newIcon("app"))
    # Tzutalin 201705+: Accept extra agruments to change predefined class file
    # Usage : labelImg.py image predefClassFile
    win = MainWindow(argv[1] if len(argv) >= 2 else None,
                     argv[2] if len(argv) >= 3 else os.path.join('data', 'predefined_classes.txt'))
    win.show()
    return app, win
'''
#wangyibo 20190325 Try to add childwindow
    win = MainWindow(argv[1] if len(argv) >= 2 else None,
                    argv[2] if len(argv) >= 3 else os.path.join('data', 'predefined_classes.txt'))
    s = ChildWindow()
    win.classifyButton.clicked.connect(s.handle_click)
    win.classifyButton.clicked.connect(win.hide)
    win.close_signal.connect(win.close)
    win.show()
    return app, win
    '''


def main(argv=[]):
    '''construct main app and run it'''
    app, _win = get_main_app(argv)
    return app.exec_()

if __name__ == '__main__':

    sys.exit(main(sys.argv))
