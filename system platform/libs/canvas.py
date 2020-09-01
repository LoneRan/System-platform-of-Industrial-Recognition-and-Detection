# -*- coding: utf8 -*-
try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

#from PyQt4.QtOpenGL import *

from shape import Shape
from lib import distance
import math

#一系列鼠标形状
CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_POINT = Qt.PointingHandCursor
CURSOR_DRAW = Qt.CrossCursor
CURSOR_MOVE = Qt.ClosedHandCursor
CURSOR_GRAB = Qt.OpenHandCursor

#Canvas类
class Canvas(QWidget):
    zoomRequest = pyqtSignal(int) #pyqtSignal自定义信号
    scrollRequest = pyqtSignal(int, int)
    newShape = pyqtSignal()
    selectionChanged = pyqtSignal(bool)
    shapeMoved = pyqtSignal()
    drawingPolygon = pyqtSignal(bool)

    hideRRect = pyqtSignal(bool)
    hideNRect = pyqtSignal(bool)
    status = pyqtSignal(str)

    CREATE, EDIT = list(range(2))

    epsilon = 11.0



    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__(*args, **kwargs)
        # Initialise local state.
        self.mode = self.EDIT
        self.shapes = []
        self.current = None
        self.selectedShape = None  # save the selected shape here
        self.selectedShapeCopy = None
        self.lineColor = QColor(0, 255, 0)
        self.line = Shape(line_color=self.lineColor)
        self.prevPoint = QPointF()
        self.offsets = QPointF(), QPointF()
        self.scale = 1.0
        self.pixmap = QPixmap()
        self.visible = {}
        self._hideBackround = False
        self.hideBackround = False
        self.hShape = None
        self.hVertex = None
        self._painter = QPainter()
        self._cursor = CURSOR_DEFAULT #鼠标形状初始化为默认形状
        # Menus:
        self.menus = (QMenu(), QMenu())
        # Set widget options.
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)  #通过鼠标滚轮来获取焦点事件
        self.verified = False
        # judge can draw rotate rect
        self.canDrawRotatedRect = True
        self.hideRotated = False
        self.hideNormal = False
        self.canOutOfBounding = False
        self.showCenter = False

    #通过光标状态启动事件
    def enterEvent(self, ev):
        self.overrideCursor(self._cursor)

    #弹出光标退出事件
    def leaveEvent(self, ev):
        self.restoreCursor()

    #弹出光标离焦事件
    def focusOutEvent(self, ev):
        self.restoreCursor()

    #判断当前标注框是否可见（若该标注框不存在于字典中，则返回默认值True）
    def isVisible(self, shape):
        return self.visible.get(shape, True) #字典(Dictionary) get() 函数返回指定键的值，如果值不在字典中返回默认值

    #绘制时mode为Create
    def drawing(self):
        return self.mode == self.CREATE

    #编辑时mode为Edit
    def editing(self):
        return self.mode == self.EDIT

    def setEditing(self, value=True):
        self.mode = self.EDIT if value else self.CREATE
        if not value:  # Create
            self.unHighlight()
            self.deSelectShape()

    def unHighlight(self):
        if self.hShape:
            self.hShape.highlightClear()
        self.hVertex = self.hShape = None

    #返回选中的顶点
    def selectedVertex(self):
        return self.hVertex is not None

    
    def mouseMoveEvent(self, ev):
        """Update line with last point and current coordinates."""
        pos = self.transformPos(ev.pos()) #获取当前鼠标位置在图像坐标系下的坐标

        self.restoreCursor()

        # Polygon drawing.
        if self.drawing():

            self.overrideCursor(CURSOR_DRAW) #修改鼠标形状为绘制状态
            if self.current:
                color = self.lineColor
                if self.outOfPixmap(pos): #当鼠标位置超出图像区域时，选取与图像四边最近的交点作为当前鼠标位置
                    # Don't allow the user to draw outside the pixmap.
                    # Project the point to the pixmap's edges.
                    pos = self.intersectionPoint(self.current[-1], pos)
                elif len(self.current) > 1 and self.closeEnough(pos, self.current[0]):
                    # Attract line to starting point and colorise to alert the
                    # user:  吸引线到起点并着色以提醒用户                  
                    pos = self.current[0]
                    color = self.current.line_color
                    self.overrideCursor(CURSOR_POINT)
                    self.current.highlightVertex(0, Shape.NEAR_VERTEX)
                self.line[1] = pos
                self.line.line_color = color
                self.repaint()
                self.current.highlightClear()
                self.status.emit("width is %d, height is %d." % (pos.x()-self.line[0].x(), pos.y()-self.line[0].y())) #在状态栏中显示当前矩形框的长和宽
            return

        # Polygon copy moving. 当鼠标右键按下且满足旋转条件时执行旋转操作
        if Qt.RightButton & ev.buttons(): 
            # print("right button")
            # if self.selectedShapeCopy and self.prevPoint:
            #     print("select shape copy")
            #     self.overrideCursor(CURSOR_MOVE)
            #     self.boundedMoveShape(self.selectedShapeCopy, pos)
            #     self.repaint()
            # elif self.selectedShape:
            #     print("select shape")
            #     self.selectedShapeCopy = self.selectedShape.copy()
            #     self.repaint()
            if self.selectedVertex() and self.selectedShape.isRotated: #如果选中了某一顶点且该矩形框是有向框，则执行旋转
                self.boundedRotateShape(pos) #执行旋转
                self.shapeMoved.emit()
                self.repaint()
            self.status.emit("(%d,%d)." % (pos.x(), pos.y()))
            return

        # Polygon/Vertex moving. 当鼠标左键按下时，响应移动某一顶点或移动整个矩形框
        if Qt.LeftButton & ev.buttons():
            if self.selectedVertex():
                # if self.outOfPixmap(pos):
                #     print("chule ")
                #     return
                # else:
                # print("meiyou chujie")
                self.boundedMoveVertex(pos) #计算出某点移动后的矩形框
                self.shapeMoved.emit()
                self.repaint()
            elif self.selectedShape and self.prevPoint:
                self.overrideCursor(CURSOR_MOVE) #改变光标形状
                self.boundedMoveShape(self.selectedShape, pos) #计算整个矩形框平移后的坐标值
                self.shapeMoved.emit()
                self.repaint()
                self.status.emit("(%d,%d)." % (pos.x(), pos.y()))
            return

        # Just hovering over the canvas, 2 posibilities:
        # - Highlight shapes
        # - Highlight vertex
        # Update shape/vertex fill and tooltip value accordingly.
        self.setToolTip("Image")
        for shape in reversed([s for s in self.shapes if self.isVisible(s)]):
            # Look for a nearby vertex to highlight. If that fails,
            # check if we happen to be inside a shape.
            index = shape.nearestVertex(pos, self.epsilon) #取出最为接近的顶点索引号
            if index is not None:
                if self.selectedVertex():
                    self.hShape.highlightClear()
                self.hVertex, self.hShape = index, shape
                shape.highlightVertex(index, shape.MOVE_VERTEX)
                self.overrideCursor(CURSOR_POINT) #改变光标形状
                # self.setToolTip("Click & drag to move point.")
                # self.setStatusTip(self.toolTip())
                self.update()
                break
            elif shape.containsPoint(pos): #如果该点落在了另一标注框内
                if self.selectedVertex():
                    self.hShape.highlightClear()
                self.hVertex, self.hShape = None, shape
                # self.setToolTip(
                #     "Click & drag to move shape '%s'" % shape.label)
                # self.setStatusTip(self.toolTip())
                self.overrideCursor(CURSOR_GRAB)
                self.update()
                break
        else:  # Nothing found, clear highlights, reset state. 其余情况下，不做任何相关响应
            if self.hShape:
                self.hShape.highlightClear()
                self.update()
            self.hVertex, self.hShape = None, None
        
        self.status.emit("(%d,%d)." % (pos.x(), pos.y())) #状态栏实时显示当前鼠标光标位置（在图像坐标系下）
        
    #响应鼠标左右键按下
    def mousePressEvent(self, ev):
        pos = self.transformPos(ev.pos()) #获取当前鼠标光标位置
        # print('sldkfj %d %d' % (pos.x(), pos.y()))
        if ev.button() == Qt.LeftButton: #如果是左键按下
            self.hideBackroundShapes(True)
            if self.drawing():
                self.handleDrawing(pos) #绘制标注框，并保存标注框信息
            else:                
                self.selectShapePoint(pos)
                self.prevPoint = pos
                self.repaint()
        elif ev.button() == Qt.RightButton and self.editing():
            self.selectShapePoint(pos)
            self.hideBackroundShapes(True)
            # if self.selectedShape is not None:
            #     print('point is (%d, %d)' % (pos.x(), pos.y()))
            #     self.selectedShape.rotate(10)

            self.prevPoint = pos
            self.repaint()

    #响应鼠标左右键释放
    def mouseReleaseEvent(self, ev):  
        self.hideBackroundShapes(False)      
        if ev.button() == Qt.RightButton and not self.selectedVertex(): #右键释放时           
            menu = self.menus[bool(self.selectedShapeCopy)]
            self.restoreCursor()
            if not menu.exec_(self.mapToGlobal(ev.pos()))\
               and self.selectedShapeCopy:
                # Cancel the move by deleting the shadow copy.
                self.selectedShapeCopy = None
                self.repaint()
        elif ev.button() == Qt.LeftButton and self.selectedShape: #左键释放时
            self.overrideCursor(CURSOR_GRAB) #改变光标形状
        elif ev.button() == Qt.LeftButton:
            pos = self.transformPos(ev.pos())
            if self.drawing():
                self.handleDrawing(pos)

    #根据copy选择复制或是移动
    def endMove(self, copy=False):
        assert self.selectedShape and self.selectedShapeCopy
        shape = self.selectedShapeCopy
        #del shape.fill_color
        #del shape.line_color
        if copy:
            self.shapes.append(shape)
            self.selectedShape.selected = False
            self.selectedShape = shape
            self.repaint()
        else:
            self.selectedShape.points = [p for p in shape.points]
        self.selectedShapeCopy = None

    #如果选中某一标注框，则隐藏其余标注框
    def hideBackroundShapes(self, value):
        # print("hideBackroundShapes")
        self.hideBackround = value
        if self.selectedShape:
            # Only hide other shapes if there is a current selection.
            # Otherwise the user will not be able to select a shape.
            self.setHiding(True)
            self.repaint()

    #真正的绘制函数
    def handleDrawing(self, pos):
        if self.current and self.current.reachMaxPoints() is False: #再压入标注框的其余三个顶点
            initPos = self.current[0]
            minX = initPos.x()
            minY = initPos.y()
            targetPos = self.line[1]
            maxX = targetPos.x()
            maxY = targetPos.y()
            self.current.addPoint(QPointF(maxX, minY))
            self.current.addPoint(targetPos)
            self.current.addPoint(QPointF(minX, maxY))
            self.current.addPoint(initPos) #加入第一个点的目的是为了判断是否可以关闭当前绘制的标注框，并不会真正加入
            self.line[0] = self.current[-1]
            if self.current.isClosed():
                self.finalise()
        elif not self.outOfPixmap(pos): #先压入标注框的第一个顶点
            self.current = Shape()
            self.current.addPoint(pos)
            self.line.points = [pos, pos]
            self.setHiding()
            self.drawingPolygon.emit(True)
            self.update()

    #设置是否隐藏
    def setHiding(self, enable=True):
        self._hideBackround = self.hideBackround if enable else False

    #判断是否已经完成某标注框的绘制
    def canCloseShape(self):
        return self.drawing() and self.current and len(self.current) > 2

   
    #响应鼠标双击 
    def mouseDoubleClickEvent(self, ev):
        # We need at least 4 points here, since the mousePress handler
        # adds an extra one before this handler is called.
        if self.canCloseShape() and len(self.current) > 3:
            self.current.popPoint()
            self.finalise()

    #绑定选中关系
    def selectShape(self, shape):
        self.deSelectShape()
        shape.selected = True
        self.selectedShape = shape
        self.setHiding()
        self.selectionChanged.emit(True)
        self.update()

    #根据当前鼠标光标位置来选择标注框，并响应相应的动作
    def selectShapePoint(self, point):
        """Select the first shape created which contains this point."""
        self.deSelectShape() #先解除与其余标注框的绑定关系
        if self.selectedVertex():  # A vertex is marked for selection.
            index, shape = self.hVertex, self.hShape
            shape.highlightVertex(index, shape.MOVE_VERTEX)

            shape.selected = True
            self.selectedShape = shape
            self.calculateOffsets(shape, point) #计算偏移量
            self.setHiding()
            self.selectionChanged.emit(True)

            return
        for shape in reversed(self.shapes): #reversed返回一个反转的迭代器
            if self.isVisible(shape) and shape.containsPoint(point):
                shape.selected = True
                self.selectedShape = shape
                self.calculateOffsets(shape, point)
                self.setHiding()
                self.selectionChanged.emit(True)
                return

    #计算标注框左上角和右下角相对于point的偏移量
    def calculateOffsets(self, shape, point):
        rect = shape.boundingRect()
        x1 = rect.x() - point.x()
        y1 = rect.y() - point.y()
        x2 = (rect.x() + rect.width()) - point.x()
        y2 = (rect.y() + rect.height()) - point.y()
        self.offsets = QPointF(x1, y1), QPointF(x2, y2)

    #计算标注框某一顶点移动后其余三点的坐标值
    def boundedMoveVertex(self, pos):
        # print("Moving Vertex")
        index, shape = self.hVertex, self.hShape
        point = shape[index]

        if not self.canOutOfBounding and self.outOfPixmap(pos):
            return
            # pos = self.intersectionPoint(point, pos)

        # print("index is %d" % index)
        sindex = (index + 2) % 4 #获取该点对应的对角线上的顶点的索引号
        # get the other 3 points after transformed
        p2,p3,p4 = self.getAdjointPoints(shape.direction, shape[sindex], pos, index) #计算出某一顶点移动后其余三个顶点的坐标值
        
        pcenter = (pos+p3)/2 #计算矩形框中心坐标        
        if self.canOutOfBounding and self.outOfPixmap(pcenter):
            return
        # if one pixal out of map , do nothing
        if not self.canOutOfBounding and (self.outOfPixmap(p2) or
            self.outOfPixmap(p3) or
            self.outOfPixmap(p4)):
                return

        # move 4 pixal one by one 按原来的顺序调整移动后的顶点坐标
        shape.moveVertexBy(index, pos - point)
        lindex = (index + 1) % 4
        
        rindex = (index + 3) % 4
        shape[lindex] = p2
        # shape[sindex] = p3
        shape[rindex] = p4
        shape.close()

        # calculate the height and weight, and show it 此处计算出来的长和宽是有问题的，没有考虑顺序问题，当然对于标注来说没啥问题
        w = math.sqrt((p4.x()-p3.x()) ** 2 + (p4.y()-p3.y()) ** 2)
        h = math.sqrt((p3.x()-p2.x()) ** 2 + (p3.y()-p2.y()) ** 2)
        self.status.emit("width is %d, height is %d." % (w,h))


    #通过几何学求出其余三点坐标值    
    def getAdjointPoints(self, theta, p3, p1, index):
        # p3 = center
        # p3 = 2*center-p1
        a1 = math.tan(theta) #无需担心90/270度时，正切值趋于无穷大（math本身进行了处理）
        if (a1 == 0): #当为无向框或有向框角度为0时
            if index % 2 == 0:
                p2 = QPointF(p3.x(), p1.y()) #只需改变y坐标
                p4 = QPointF(p1.x(), p3.y()) #只需改变x坐标
            else:            
                p4 = QPointF(p3.x(), p1.y()) #只需改变y坐标
                p2 = QPointF(p1.x(), p3.y()) #只需改变x坐标
        else: #当为有向框且角度不为0时（以下通过几何学求出）   
            a3 = a1
            a2 = - 1/a1
            a4 = - 1/a1
            b1 = p1.y() - a1 * p1.x()
            b2 = p1.y() - a2 * p1.x()
            b3 = p3.y() - a1 * p3.x()
            b4 = p3.y() - a2 * p3.x()

            if index % 2 == 0:
                p2 = self.getCrossPoint(a1,b1,a4,b4)
                p4 = self.getCrossPoint(a2,b2,a3,b3)
            else:            
                p4 = self.getCrossPoint(a1,b1,a4,b4)
                p2 = self.getCrossPoint(a2,b2,a3,b3)

        return p2,p3,p4

    def getCrossPoint(self,a1,b1,a2,b2):
        x = (b2-b1)/(a1-a2)
        y = (a1*b2 - a2*b1)/(a1-a2)
        return QPointF(x,y)

    #判断旋转后的标注矩形框是否完整在图像区域内，如果不完整，则此旋转无效
    def boundedRotateShape(self, pos):
        # print("Rotate Shape2")          
        # judge if some vertex is out of pixma
        index, shape = self.hVertex, self.hShape
        point = shape[index]

        angle = self.getAngle(shape.center,pos,point) #获取旋转角度
        # for i, p in enumerate(shape.points):
        #     if self.outOfPixmap(shape.rotatePoint(p,angle)):
        #         # print("out of pixmap")
        #         return
        if not self.rotateOutOfBound(angle): #只有旋转后完整在图像区域内，才执行旋转
            shape.rotate(angle) #执行旋转变换
            self.prevPoint = pos

    def getAngle(self, center, p1, p2):
        dx1 = p1.x() - center.x();
        dy1 = p1.y() - center.y();

        dx2 = p2.x() - center.x();
        dy2 = p2.y() - center.y();

        c = math.sqrt(dx1*dx1 + dy1*dy1) * math.sqrt(dx2*dx2 + dy2*dy2)
        if c == 0: return 0
        y = (dx1*dx2+dy1*dy2)/c  #计算两个向量间的余弦值
        if y>1: return 0
        angle = math.acos(y) #得到的是弧度值

        if (dx1*dy2-dx2*dy1)>0:   
            return angle
        else:
            return -angle

    #计算平移后的标注框位置
    def boundedMoveShape(self, shape, pos):
        if shape.isRotated and self.canOutOfBounding:
            c = shape.center
            dp = pos - self.prevPoint
            dc = c + dp
            if dc.x() < 0:
                dp -= QPointF(min(0,dc.x()), 0)
            if dc.y() < 0:                
                dp -= QPointF(0, min(0,dc.y()))                
            if dc.x() >= self.pixmap.width():
                dp += QPointF(min(0, self.pixmap.width() - 1  - dc.x()), 0)
            if dc.y() >= self.pixmap.height():
                dp += QPointF(0, min(0, self.pixmap.height() - 1 - dc.y()))

        else:            
            if self.outOfPixmap(pos):
                return False  # No need to move
            o1 = pos + self.offsets[0]
            if self.outOfPixmap(o1):
                pos -= QPointF(min(0, o1.x()), min(0, o1.y()))
            o2 = pos + self.offsets[1]
            if self.outOfPixmap(o2):
                pos += QPointF(min(0, self.pixmap.width() - 1 - o2.x()),
                               min(0, self.pixmap.height() - 1 - o2.y()))
            dp = pos - self.prevPoint
        # The next line tracks the new position of the cursor
        # relative to the shape, but also results in making it
        # a bit "shaky" when nearing the border and allows it to
        # go outside of the shape's area for some reason. XXX
        #self.calculateOffsets(self.selectedShape, pos)
        
        if dp:
            shape.moveBy(dp) #计算平移后的坐标值
            self.prevPoint = pos
            shape.close()
            return True
        return False


    def boundedMoveShape2(self, shape, pos):
        if self.outOfPixmap(pos):
            return False  # No need to move
        o1 = pos + self.offsets[0]
        if self.outOfPixmap(o1):
            pos -= QPointF(min(0, o1.x()), min(0, o1.y()))
        o2 = pos + self.offsets[1]
        if self.outOfPixmap(o2):
            pos += QPointF(min(0, self.pixmap.width() - o2.x()),
                           min(0, self.pixmap.height() - o2.y()))
        # The next line tracks the new position of the cursor
        # relative to the shape, but also results in making it
        # a bit "shaky" when nearing the border and allows it to
        # go outside of the shape's area for some reason. XXX
        #self.calculateOffsets(self.selectedShape, pos) 
        dp = pos - self.prevPoint
        if dp:
            shape.moveBy(dp)
            self.prevPoint = pos
            shape.close()
            return True
        return False

    #解除选中状态
    def deSelectShape(self):
        if self.selectedShape:
            self.selectedShape.selected = False
            self.selectedShape = None
            self.setHiding(False) #设置为可见
            self.selectionChanged.emit(False)
            self.update()

    #删除选中的标注框
    def deleteSelected(self):
        if self.selectedShape:
            shape = self.selectedShape
            self.shapes.remove(self.selectedShape)
            self.selectedShape = None
            self.update()
            return shape

    #复制选中的标注框
    def copySelectedShape(self):
        if self.selectedShape:
            shape = self.selectedShape.copy()
            self.deSelectShape()
            self.shapes.append(shape)
            shape.selected = True
            self.selectedShape = shape
            self.boundedShiftShape(shape)
            return shape

    #复制标注框时使用，复制的标注框比原始框稍微偏移一小点
    def boundedShiftShape(self, shape):
        # Try to move in one direction, and if it fails in another.
        # Give up if both fail.
        point = shape[0]
        offset = QPointF(2.0, 2.0)
        self.calculateOffsets(shape, point) #计算偏移量
        self.prevPoint = point
        if not self.boundedMoveShape(shape, point - offset):
            self.boundedMoveShape(shape, point + offset)

    #绘制所有
    def paintEvent(self, event):
        if not self.pixmap:
            return super(Canvas, self).paintEvent(event)

        p = self._painter
        p.begin(self)
        p.setRenderHint(QPainter.Antialiasing) #防锯齿
        p.setRenderHint(QPainter.HighQualityAntialiasing) #高质量防锯齿
        p.setRenderHint(QPainter.SmoothPixmapTransform) #使用平滑的pixmap变换算法(双线性插值算法)

        p.scale(self.scale, self.scale) #缩放
        p.translate(self.offsetToCenter()) #平移，使得图像中心与画布中心重合

        p.drawPixmap(0, 0, self.pixmap) #绘制，(0,0)为要被绘制的绘制设备的左上点
        Shape.scale = self.scale
        for shape in self.shapes:
            if (shape.selected or not self._hideBackround) and self.isVisible(shape):
                if (shape.isRotated and not self.hideRotated) or (not shape.isRotated and not self.hideNormal):
                    shape.fill = shape.selected or shape == self.hShape
                    shape.paint(p) #绘制标注框（包括四条边，四个顶点，中心点）
                elif self.showCenter:
                    shape.fill = shape.selected or shape == self.hShape
                    shape.paintNormalCenter(p)

        if self.current:
            self.current.paint(p)
            self.line.paint(p)
        if self.selectedShapeCopy:
            self.selectedShapeCopy.paint(p)

        # Paint rect
        if self.current is not None and len(self.line) == 2:
            leftTop = self.line[0]
            rightBottom = self.line[1]
            rectWidth = rightBottom.x() - leftTop.x()
            rectHeight = rightBottom.y() - leftTop.y()
            color = QColor(0, 225, 0)
            p.setPen(color)
            brush = QBrush(QColor(255, 255, 255), Qt.Dense6Pattern) #画刷
            #setBrush()
            p.setBrush(brush)
            p.drawRect(leftTop.x(), leftTop.y(), rectWidth, rectHeight)
            
            #draw dialog line of rectangle 绘制标注过程中标注框的对角线
            p.setPen(self.lineColor)
            p.drawLine(leftTop.x(),rightBottom.y(),rightBottom.x(),leftTop.y())

        self.setAutoFillBackground(True)
        if self.verified:
            pal = self.palette()
            pal.setColor(self.backgroundRole(), QColor(184, 239, 38, 128))
            self.setPalette(pal)
        else:
            pal = self.palette()
            pal.setColor(self.backgroundRole(), QColor(232, 232, 232, 255))
            self.setPalette(pal)

        p.end()

    #从控件坐标系转到图像坐标系
    def transformPos(self, point):
        """Convert from widget-logical coordinates to painter-logical coordinates."""
        return point / self.scale - self.offsetToCenter()

    #函数名字取的不好，其实是图像左上角相对画布左上角的偏移量
    #注：图像中心点与画布中心点是重合的
    def offsetToCenter(self):
        s = self.scale
        area = super(Canvas, self).size()
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        aw, ah = area.width(), area.height()
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QPointF(x, y)

    #判断当前鼠标光标位置p是否在图像区域内
    def outOfPixmap(self, p):
        w, h = self.pixmap.width(), self.pixmap.height()
        return not (0 <= p.x() < w and 0 <= p.y() < h)

    #绘制完毕，将当前标注框存入shapes中
    def finalise(self):
        assert self.current
        self.current.isRotated = self.canDrawRotatedRect
        # print(self.canDrawRotatedRect)
        self.current.close()
        self.shapes.append(self.current)
        self.current = None
        self.setHiding(False)
        self.newShape.emit()
        self.update()

    #判断两点是否足够接近
    def closeEnough(self, p1, p2):
        #d = distance(p1 - p2)
        #m = (p1-p2).manhattanLength()
        # print "d %.2f, m %d, %.2f" % (d, m, d - m)
        return distance(p1 - p2) < self.epsilon

    #以顺时针方式循环每个图像边缘，并找到与当前线段相交的那个
    def intersectionPoint(self, p1, p2):
        # Cycle through each image edge in clockwise fashion,
        # and find the one intersecting the current line segment.
        # http://paulbourke.net/geometry/lineline2d/
        size = self.pixmap.size()
        #points存储图像四个顶点坐标
        points = [(0, 0),
                  (size.width(), 0),
                  (size.width(), size.height()),
                  (0, size.height())]
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        d, i, (x, y) = min(self.intersectingEdges((x1, y1), (x2, y2), points)) #获取与图像四边最近的交点
        x3, y3 = points[i]
        x4, y4 = points[(i + 1) % 4]
        if (x, y) == (x1, y1):
            # Handle cases where previous point is on one of the edges. 处理前一个点在图像边缘上的情况
            if x3 == x4:
                return QPointF(x3, min(max(0, y2), max(y3, y4)))
            else:  # y3 == y4
                return QPointF(min(max(0, x2), max(x3, x4)), y3)
        return QPointF(x, y)

    #计算出当前直线与图像四条边最近的交点（最近指交点与直线末尾点(x2,y2)的距离最短）
    def intersectingEdges(self, x1y1, x2y2, points):
        """For each edge formed by `points', yield the intersection
        with the line segment `(x1,y1) - (x2,y2)`, if it exists.
        Also return the distance of `(x2,y2)' to the middle of the
        edge along with its index, so that the one closest can be chosen."""
        x1, y1 = x1y1
        x2, y2 = x2y2
        for i in range(4):
            x3, y3 = points[i]
            x4, y4 = points[(i + 1) % 4]
            denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
            nua = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
            nub = (x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)
            if denom == 0:
                # This covers two cases:
                #   nua == nub == 0: Coincident
                #   otherwise: Parallel
                continue
            ua, ub = nua / denom, nub / denom
            if 0 <= ua <= 1 and 0 <= ub <= 1:
                x = x1 + ua * (x2 - x1)
                y = y1 + ua * (y2 - y1)
                m = QPointF((x3 + x4) / 2, (y3 + y4) / 2)
                d = distance(m - QPointF(x2, y2))
                #print("return=",d,i,(x,y))
                yield d, i, (x, y)  #返回生成器，可用于迭代

    # These two, along with a call to adjustSize are required for the
    # scroll area.
    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        if self.pixmap:
            return self.scale * self.pixmap.size()
        return super(Canvas, self).minimumSizeHint()

    #响应鼠标滚轮
    # Modified by Chenbin Zheng, Fix angle error 2018/11/26
    def wheelEvent(self, ev):
        qt_version = 4 if hasattr(ev, "delta") else 5
        if qt_version == 4:
            if ev.orientation() == Qt.Vertical:
                v_delta = ev.delta()
                h_delta = 0
            else:
                h_delta = ev.delta()
                v_delta = 0
        else:
            delta = ev.angleDelta()
            h_delta = delta.x()
            v_delta = delta.y()
        #print('scrolling vdelta is %d, hdelta is %d' % (v_delta, h_delta))
        mods = ev.modifiers()
        '''
        if Qt.ControlModifier == int(mods) and v_delta: #当按下Ctrl键时，对图像进行缩放操作
            self.zoomRequest.emit(v_delta)
        else:
            v_delta and self.scrollRequest.emit(v_delta, Qt.Vertical)
            h_delta and self.scrollRequest.emit(h_delta, Qt.Horizontal)
        '''
        if Qt.ControlModifier == int(mods): #当按下Ctrl键时，对图像进行缩放操作
            v_delta and self.scrollRequest.emit(v_delta, Qt.Vertical)
            h_delta and self.scrollRequest.emit(h_delta, Qt.Horizontal)
        elif v_delta:
            self.zoomRequest.emit(v_delta)
        ev.accept()
     

    #响应键盘按键
    def keyPressEvent(self, ev):
        key = ev.key()
        
        if key == Qt.Key_Escape and self.current:
            print('ESC press')
            self.current = None
            self.drawingPolygon.emit(False)
            self.update()
        elif key == Qt.Key_Return and self.canCloseShape():
            self.finalise()
        elif key == Qt.Key_Left and self.selectedShape:
            self.moveOnePixel('Left')
        elif key == Qt.Key_Right and self.selectedShape:
            self.moveOnePixel('Right')
        elif key == Qt.Key_Up and self.selectedShape:
            self.moveOnePixel('Up')
        elif key == Qt.Key_Down and self.selectedShape:
            self.moveOnePixel('Down')
        elif key == Qt.Key_Z and self.selectedShape and\
             self.selectedShape.isRotated and not self.rotateOutOfBound(0.1):
            self.selectedShape.rotate(0.1)
            self.shapeMoved.emit() 
            self.update()  
        elif key == Qt.Key_X and self.selectedShape and\
             self.selectedShape.isRotated and not self.rotateOutOfBound(0.01):
            self.selectedShape.rotate(0.01) 
            self.shapeMoved.emit()
            self.update()  
        elif key == Qt.Key_C and self.selectedShape and\
             self.selectedShape.isRotated and not self.rotateOutOfBound(-0.01):
            self.selectedShape.rotate(-0.01) 
            self.shapeMoved.emit()
            self.update()  
        elif key == Qt.Key_V and self.selectedShape and\
             self.selectedShape.isRotated and not self.rotateOutOfBound(-0.1):
            self.selectedShape.rotate(-0.1)
            self.shapeMoved.emit()
            self.update()
        elif key == Qt.Key_R:
            self.hideRotated = not self.hideRotated
            self.hideRRect.emit(self.hideRotated)
            self.update()
        elif key == Qt.Key_N:
            self.hideNormal = not self.hideNormal
            self.hideNRect.emit(self.hideNormal)
            self.update()
        elif key == Qt.Key_O:
            self.canOutOfBounding = not self.canOutOfBounding
        elif key == Qt.Key_B:
            self.showCenter = not self.showCenter
            self.update()


    #检查有向矩形框是否完整在图像区域内
    def rotateOutOfBound(self, angle):
        if self.canOutOfBounding:
            return False
        for i, p in enumerate(self.selectedShape.points):
            if self.outOfPixmap(self.selectedShape.rotatePoint(p,angle)): #逐点判断是否在图像区域内
                return True
        return False

    #移动一个像素位置
    def moveOnePixel(self, direction):
        # print(self.selectedShape.points)
        if direction == 'Left' and not self.moveOutOfBound(QPointF(-1.0, 0)):
            # print("move Left one pixel")
            self.selectedShape.points[0] += QPointF(-1.0, 0)
            self.selectedShape.points[1] += QPointF(-1.0, 0)
            self.selectedShape.points[2] += QPointF(-1.0, 0)
            self.selectedShape.points[3] += QPointF(-1.0, 0)
            self.selectedShape.center += QPointF(-1.0, 0)
        elif direction == 'Right' and not self.moveOutOfBound(QPointF(1.0, 0)):
            # print("move Right one pixel")
            self.selectedShape.points[0] += QPointF(1.0, 0)
            self.selectedShape.points[1] += QPointF(1.0, 0)
            self.selectedShape.points[2] += QPointF(1.0, 0)
            self.selectedShape.points[3] += QPointF(1.0, 0)
            self.selectedShape.center += QPointF(1.0, 0)
        elif direction == 'Up' and not self.moveOutOfBound(QPointF(0, -1.0)):
            # print("move Up one pixel")
            self.selectedShape.points[0] += QPointF(0, -1.0)
            self.selectedShape.points[1] += QPointF(0, -1.0)
            self.selectedShape.points[2] += QPointF(0, -1.0)
            self.selectedShape.points[3] += QPointF(0, -1.0)
            self.selectedShape.center += QPointF(0, -1.0)
        elif direction == 'Down' and not self.moveOutOfBound(QPointF(0, 1.0)):
            # print("move Down one pixel")
            self.selectedShape.points[0] += QPointF(0, 1.0)
            self.selectedShape.points[1] += QPointF(0, 1.0)
            self.selectedShape.points[2] += QPointF(0, 1.0)
            self.selectedShape.points[3] += QPointF(0, 1.0)
            self.selectedShape.center += QPointF(0, 1.0)
        self.shapeMoved.emit()
        self.repaint()

    #判断在移动step(有方向)后，标注框是否完整在图像区域内
    def moveOutOfBound(self, step):
        points = [p1+p2 for p1, p2 in zip(self.selectedShape.points, [step]*4)]
        return True in map(self.outOfPixmap, points)

    #设置最新标签
    def setLastLabel(self, text):
        assert text
        self.shapes[-1].label = text
        return self.shapes[-1]

    def undoLastLine(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.setOpen()
        self.line.points = [self.current[-1], self.current[0]]
        self.drawingPolygon.emit(True)

    
    def resetAllLines(self):
        assert self.shapes
        self.current = self.shapes.pop() #移除最后一个标注框
        self.current.setOpen()
        self.line.points = [self.current[-1], self.current[0]]
        self.drawingPolygon.emit(True)
        self.current = None
        self.drawingPolygon.emit(False)
        self.update()

    #加载图像
    def loadPixmap(self, pixmap):
        self.pixmap = pixmap
        self.shapes = []
        self.repaint()

    #加载所有标注框
    def loadShapes(self, shapes):
        self.shapes = list(shapes)
        self.current = None
        self.repaint()

    #设置标注框可见
    def setShapeVisible(self, shape, value):
        self.visible[shape] = value
        self.repaint()

    #将光标状态压入栈中
    def overrideCursor(self, cursor):
        self.restoreCursor()
        self._cursor = cursor
        QApplication.setOverrideCursor(cursor) #把光标压到栈中

    #将光标从栈中弹出
    def restoreCursor(self):
        QApplication.restoreOverrideCursor() #把激活的光标从栈中弹出

    #重置
    def resetState(self):
        self.restoreCursor()
        self.pixmap = None
        self.update()
