# -*- coding: utf8 -*-


try:
    from PyQt5.QtGui import QImage
except ImportError:
    from PyQt4.QtGui import QImage

from base64 import b64encode, b64decode
from pascal_voc_io import PascalVocWriter
from pascal_voc_io import XML_EXT
import os.path
import sys
import math

class LabelFileError(Exception):
    pass


class LabelFile(object):
    # It might be changed as window creates. By default, using XML ext
    # suffix = '.lif'
    suffix = XML_EXT

    def __init__(self, filename=None):
        self.shapes = ()
        self.imagePath = None
        self.imageData = None
        self.verified = False

    #按VOC格式存储标注信息
    def savePascalVocFormat(self, filename, shapes, imagePath, imageData,
                            lineColor=None, fillColor=None, databaseSrc=None):
        imgFolderPath = os.path.dirname(imagePath) #加载文件所在路径
        imgFolderName = os.path.split(imgFolderPath)[-1] #获取文件所在文件夹名称
        imgFileName = os.path.basename(imagePath) #获取文件名（包含文件扩展名，即形如1.jpg）
        imgFileNameWithoutExt = os.path.splitext(imgFileName)[0] #os.path.splitext将文件名和扩展名分开，这里只取文件名
        # Read from file path because self.imageData might be empty if saving to
        # Pascal format
        image = QImage()
        image.load(imagePath) #加载图像
        imageShape = [image.height(), image.width(),
                      1 if image.isGrayscale() else 3] #获取图像的width,height和depth
        writer = PascalVocWriter(imgFolderName, imgFileNameWithoutExt,
                                 imageShape, localImgPath=imagePath)
        writer.verified = self.verified

        for shape in shapes:
            points = shape['points']
            label = shape['label']
            # Add Chris
            difficult = int(shape['difficult'])           
            direction = shape['direction']
            isRotated = shape['isRotated']
            # if shape is normal box, save as bounding box 
            # print('direction is %lf' % direction)
            if not isRotated:
                bndbox = LabelFile.convertPoints2BndBox(points)
                writer.addBndBox(bndbox[0], bndbox[1], bndbox[2], 
                    bndbox[3], label, difficult)
            else: #if shape is rotated box, save as rotated bounding box
                robndbox = LabelFile.convertPoints2RotatedBndBox(shape)
                writer.addRotatedBndBox(robndbox[0],robndbox[1],
                    robndbox[2],robndbox[3],robndbox[4],label,difficult)

        writer.save(targetFile=filename) #保存
        return

    #切换Verify（即反转）
    def toggleVerify(self):
        self.verified = not self.verified
 
    #静态函数，无需实例化即可直接调用
    #判断是否为标注文件（按文件的后缀名是否为.xml进行判断）
    @staticmethod
    def isLabelFile(filename):
        fileSuffix = os.path.splitext(filename)[1].lower()
        return fileSuffix == LabelFile.suffix

    #将四个定点坐标对应的矩形框转化为左上角和右下角形式（针对无向矩形框而言）
    @staticmethod 
    def convertPoints2BndBox(points):
        xmin = float('inf')
        ymin = float('inf')
        xmax = float('-inf')
        ymax = float('-inf')
        for p in points:
            x = p[0]
            y = p[1]
            xmin = min(x, xmin)
            ymin = min(y, ymin)
            xmax = max(x, xmax)
            ymax = max(y, ymax)

        # Martin Kersner, 2015/11/12
        # 0-valued coordinates of BB caused an error while 坐标为0时会导致训练出错，所以将1以下的坐标强制转化为1
        # training faster-rcnn object detector.
        if xmin < 1:
            xmin = 1

        if ymin < 1:
            ymin = 1

        return (int(xmin), int(ymin), int(xmax), int(ymax)) #返回的是整数坐标

    # You Hao, 2017/06/12
    #将四个定点坐标对应的矩形框转化为中心点+长宽+旋转角度形式（针对有向矩形框而言）
    @staticmethod
    def convertPoints2RotatedBndBox(shape):
        points = shape['points']
        center = shape['center']
        direction = shape['direction']

        #print(points)

        cx = center.x()
        cy = center.y()
        
        w = math.sqrt((points[0][0]-points[1][0]) ** 2 +
            (points[0][1]-points[1][1]) ** 2)

        h = math.sqrt((points[2][0]-points[1][0]) ** 2 +
            (points[2][1]-points[1][1]) ** 2)

        # Modified by Chenbin Zheng, Fix angle error 2018/11/25
        angle = direction % (2*math.pi)  #由此可见最后写入xml文件的角度信息是弧度制

        #验证旋转角度的正确性
        '''
        theta = math.acos((points[1][0]-points[0][0]) / w)
        if points[1][1]-points[0][1] < 0:
           theta = 2*math.pi - theta
        print("rotate angle:",theta)
        '''

        return (round(cx,4),round(cy,4),round(w,4),round(h,4),round(angle,6)) #round按指定位数进行四舍五入
