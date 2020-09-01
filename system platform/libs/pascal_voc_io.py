#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement

try:
  from lxml import etree
  print("running with lxml.etree")
except ImportError:
  try:
    # Python 2.5
    import xml.etree.cElementTree as etree
    print("running with cElementTree on Python 2.5+")
  except ImportError:
    try:
      # Python 2.5
      import xml.etree.ElementTree as etree
      print("running with ElementTree on Python 2.5+")
    except ImportError:
      try:
        # normal cElementTree install
        import cElementTree as etree
        print("running with cElementTree")
      except ImportError:
        try:
          # normal ElementTree install
          import elementtree.ElementTree as etree
          print("running with ElementTree")
        except ImportError:
          print("Failed to import ElementTree from any known place")

import codecs
import math

#后缀
XML_EXT = '.xml'

#VOC标注格式写入类
class PascalVocWriter:

    def __init__(self, foldername, filename, imgSize,databaseSrc='Unknown', localImgPath=None):
        self.foldername = foldername #文件夹名称
        self.filename = filename #文件名称（不包含扩展名）
        self.databaseSrc = databaseSrc #默认为Unknown
        self.imgSize = imgSize #图像长宽+深度
        self.boxlist = []
        self.roboxlist = []
        self.localImgPath = localImgPath #文件所在的完整路径
        self.verified = False


    def prettify(self, elem):
        """
            Return a pretty-printed XML string for the Element.
        """
        rough_string = ElementTree.tostring(elem, 'utf8')
        root = etree.fromstring(rough_string)
        try:
            return etree.tostring(root, pretty_print=True)
        except TypeError:
            return etree.tostring(root)

    #先生成标注文件中必须含有的信息（例如文件名等）
    def genXML(self):
        """
            Return XML root
        """
        # Check conditions
        if self.filename is None or \
                self.foldername is None or \
                self.imgSize is None:
            return None

        top = Element('annotation')
        top.set('verified', 'yes' if self.verified else 'no')

        folder = SubElement(top, 'folder')
        folder.text = self.foldername  #文件夹名

        filename = SubElement(top, 'filename')
        filename.text = self.filename #文件名（不含扩展名）

        localImgPath = SubElement(top, 'path')
        localImgPath.text = self.localImgPath #文件所在的完整路径

        source = SubElement(top, 'source')
        database = SubElement(source, 'database')
        database.text = self.databaseSrc

        size_part = SubElement(top, 'size')
        width = SubElement(size_part, 'width')
        height = SubElement(size_part, 'height')
        depth = SubElement(size_part, 'depth')
        width.text = str(self.imgSize[1])
        height.text = str(self.imgSize[0])
        if len(self.imgSize) == 3:
            depth.text = str(self.imgSize[2])
        else:
            depth.text = '1'

        segmented = SubElement(top, 'segmented')
        segmented.text = '0'
        return top

    #将无向矩形框信息存入boxlist中
    def addBndBox(self, xmin, ymin, xmax, ymax, name, difficult):
        bndbox = {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax}
        bndbox['name'] = name
        bndbox['difficult'] = difficult
        self.boxlist.append(bndbox)

    # You Hao 2017/06/21
    # add to analysis robndbox
    #将有向矩形框信息存入roboxlist中
    def addRotatedBndBox(self, cx, cy, w, h, angle, name, difficult):
        robndbox = {'cx': cx, 'cy': cy, 'w': w, 'h': h, 'angle': angle}
        robndbox['name'] = name
        robndbox['difficult'] = difficult
        self.roboxlist.append(robndbox)

    #按照xml的格式，往top中添加标注框信息
    def appendObjects(self, top):
        #先写入所有无向矩形框信息
        for each_object in self.boxlist:
            object_item = SubElement(top, 'object')  #在top下创建一个子元素，名称为object
            typeItem = SubElement(object_item, 'type') #在object_item下创建一个子元素，名称为type（object_item为top下的子元素）
            typeItem.text = "bndbox" #typeItem中要写入的文本为bndbox
            name = SubElement(object_item, 'name')
            try:
                name.text = unicode(each_object['name'])
            except NameError:
                # Py3: NameError: name 'unicode' is not defined  python3中不存在unicode函数
                name.text = each_object['name']
            pose = SubElement(object_item, 'pose')
            pose.text = "Unspecified"  #目标检测不需要指定pose
            truncated = SubElement(object_item, 'truncated') #是否有截断
            #当标注框有边在图像的四边上时，可判定该矩形框存在截断
            if int(each_object['ymax']) == int(self.imgSize[0]) or (int(each_object['ymin'])== 1):
                truncated.text = "1" # max == height or min
            elif (int(each_object['xmax'])==int(self.imgSize[1])) or (int(each_object['xmin'])== 1):
                truncated.text = "1" # max == width or min
            else:
                truncated.text = "0"
            difficult = SubElement(object_item, 'difficult')
            difficult.text = str( bool(each_object['difficult']) & 1 )            
            bndbox = SubElement(object_item, 'bndbox')
            xmin = SubElement(bndbox, 'xmin')
            xmin.text = str(each_object['xmin'])
            ymin = SubElement(bndbox, 'ymin')
            ymin.text = str(each_object['ymin'])
            xmax = SubElement(bndbox, 'xmax')
            xmax.text = str(each_object['xmax'])
            ymax = SubElement(bndbox, 'ymax')
            ymax.text = str(each_object['ymax'])

        # You Hao 2017/06/21
        # add to store robndbox
        #再写入有向矩形框信息
        for each_object in self.roboxlist:
            object_item = SubElement(top, 'object')
            typeItem = SubElement(object_item, 'type')
            typeItem.text = "robndbox"
            name = SubElement(object_item, 'name')
            try:
                name.text = unicode(each_object['name'])
            except NameError:
                # Py3: NameError: name 'unicode' is not defined
                name.text = each_object['name']
            pose = SubElement(object_item, 'pose')
            pose.text = "Unspecified"
            truncated = SubElement(object_item, 'truncated')
            # if int(each_object['ymax']) == int(self.imgSize[0]) or (int(each_object['ymin'])== 1):
            #     truncated.text = "1" # max == height or min
            # elif (int(each_object['xmax'])==int(self.imgSize[1])) or (int(each_object['xmin'])== 1):
            #     truncated.text = "1" # max == width or min
            # else:
            truncated.text = "0"
            difficult = SubElement(object_item, 'difficult')
            difficult.text = str( bool(each_object['difficult']) & 1 )
            robndbox = SubElement(object_item, 'robndbox')
            cx = SubElement(robndbox, 'cx')
            cx.text = str(each_object['cx'])
            cy = SubElement(robndbox, 'cy')
            cy.text = str(each_object['cy'])
            w = SubElement(robndbox, 'w')
            w.text = str(each_object['w'])
            h = SubElement(robndbox, 'h')
            h.text = str(each_object['h'])
            angle = SubElement(robndbox, 'angle')
            angle.text = str(each_object['angle'])

    
    def save(self, targetFile=None):
        root = self.genXML() #先产生必要信息
        self.appendObjects(root) #在必要信息之后存入所有标注框信息
        out_file = None
        if targetFile is None:
            out_file = codecs.open(
                self.filename + XML_EXT, 'w', encoding='utf-8')
        else:
            out_file = codecs.open(targetFile, 'w', encoding='utf-8')

        prettifyResult = self.prettify(root)
        out_file.write(prettifyResult.decode('utf8'))
        out_file.close()


class PascalVocReader:

    def __init__(self, filepath):
        # shapes type:
        # [labbel, [(x1,y1), (x2,y2), (x3,y3), (x4,y4)], color, color, difficult]
        self.shapes = []
        self.filepath = filepath
        self.verified = False
        self.parseXML()

    def getShapes(self):
        return self.shapes

    #只适合无向框
    def addShape(self, label, bndbox, difficult):
        xmin = int(bndbox.find('xmin').text)
        ymin = int(bndbox.find('ymin').text)
        xmax = int(bndbox.find('xmax').text)
        ymax = int(bndbox.find('ymax').text)
        points = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
        self.shapes.append((label, points, 0, False, None, None, difficult))

    # You Hao 2017/06/21
    # add to analysis robndbox load from xml
    # Modified by Chenbin Zheng, 2018/11/25
    def addRotatedShape(self, label, robndbox, difficult):
        cx = float(robndbox.find('cx').text)
        cy = float(robndbox.find('cy').text)
        w = float(robndbox.find('w').text)
        h = float(robndbox.find('h').text)
        angle = float(robndbox.find('angle').text)

        #p0x,p0y = self.rotatePoint(cx,cy, cx - w/2, cy - h/2, -angle) #由于定义逆时针为正，故需要取反送入旋转变换中
        #p1x,p1y = self.rotatePoint(cx,cy, cx + w/2, cy - h/2, -angle)
        #p2x,p2y = self.rotatePoint(cx,cy, cx + w/2, cy + h/2, -angle)
        #p3x,p3y = self.rotatePoint(cx,cy, cx - w/2, cy + h/2, -angle)

        p0x,p0y = self.rotatePoint(cx,cy, -w/2, -h/2, -angle) #由于定义逆时针为正，故需要取反送入旋转变换中
        p1x,p1y = self.rotatePoint(cx,cy, w/2, -h/2, -angle)
        p2x,p2y = self.rotatePoint(cx,cy, w/2, h/2, -angle)
        p3x,p3y = self.rotatePoint(cx,cy, -w/2, h/2, -angle)


        points = [(p0x, p0y), (p1x, p1y), (p2x, p2y), (p3x, p3y)]
        self.shapes.append((label, points, angle, True, None, None, difficult))

    #将有向框的中心点,长宽和旋转角度转化为四点坐标形式(通过旋转矩阵实现)
    # Modified by Chenbin Zheng, 2018/11/25
    def rotatePoint(self, xc,yc, xp,yp, theta):        
        #xoff = xp-xc; #实际上算的其实是当旋转角度为0（即无向框时），且假设中心点为原点时各顶点的坐标
        #yoff = yp-yc;

        cosTheta = math.cos(theta)
        sinTheta = math.sin(theta)
        #旋转变换
        #pResx = cosTheta * xoff + sinTheta * yoff
        #pResy = - sinTheta * xoff + cosTheta * yoff
        pResx = cosTheta * xp + sinTheta * yp
        pResy = - sinTheta * xp + cosTheta * yp
        # pRes = (xc + pResx, yc + pResy)
        return xc+pResx,yc+pResy

    #解析.xml文件
    def parseXML(self):
        assert self.filepath.endswith(XML_EXT), "Unsupport file format"
        parser = etree.XMLParser(encoding='utf-8')
        xmltree = ElementTree.parse(self.filepath, parser=parser).getroot()
        filename = xmltree.find('filename').text
        try:
            verified = xmltree.attrib['verified']
            if verified == 'yes':
                self.verified = True
        except KeyError:
            self.verified = False

        for object_iter in xmltree.findall('object'):
            typeItem = object_iter.find('type')

            # print(typeItem.text)
            if typeItem.text == 'bndbox':
                bndbox = object_iter.find("bndbox")
                label = object_iter.find('name').text
                # Add chris
                difficult = False
                if object_iter.find('difficult') is not None:
                    difficult = bool(int(object_iter.find('difficult').text))
                self.addShape(label, bndbox, difficult)

            # You Hao 2017/06/21
            # add to load robndbox
            elif typeItem.text == 'robndbox':
                robndbox = object_iter.find('robndbox')
                label = object_iter.find('name').text
                difficult = False
                if object_iter.find('difficult') is not None:
                    difficult = bool(int(object_iter.find('difficult').text))
                self.addRotatedShape(label, robndbox, difficult)
            
            else: 
                pass

        return True
