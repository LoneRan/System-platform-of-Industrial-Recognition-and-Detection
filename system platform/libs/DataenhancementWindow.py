try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
    from PyQt5 import QtCore, QtGui, QtWidgets
    import glob
    from PIL import Image
    import numpy as np
    import os.path
    from PIL import Image
    import matplotlib
    import matplotlib.pyplot as plt
    import cv2
    import os
    import random
    from numpy import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

from Done import Ui_done
class Ui_dataenhance(QtWidgets.QWidget):
    def __init__(self):
        super(Ui_dataenhance, self).__init__()
        self.setObjectName("detect")
        self.resize(400, 150)
        self.setWindowTitle("扩充数据集")

        layout = QHBoxLayout(self)

        self.ResolutionButton = QToolButton(self)
        self.ResolutionButton.setText("改变分辨率")
        layout.addWidget(self.ResolutionButton)
        self.ResolutionButton.clicked.connect(self.Resolution)
        self.ResolutionButton.clicked.connect(self.DoneTrans)

        self.FlipButton = QToolButton(self)
        self.FlipButton.setText("图像翻转")
        layout.addWidget(self.FlipButton)
        self.FlipButton.clicked.connect(self.Flip)

        self.NoiseButton = QToolButton(self)
        self.NoiseButton.setText("图像加噪")
        layout.addWidget(self.NoiseButton)
        self.NoiseButton.clicked.connect(self.Noise)





    def Resolution(self):
        for jpgfile in glob.glob("/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/JPEGImage/*.jpg"):
            convertjpg(jpgfile, "/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/JPEGImage")


    def Flip(self):
        for jpgfile in glob.glob("/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/JPEGImage/*.jpg"):
            FlipImg(jpgfile, "/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/JPEGImage/")

    def Noise(self):
        for jpgfile in glob.glob("/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/JPEGImage/*.jpg"):
            NoiseImg(jpgfile, "/Users/wangyibo/Downloads/LabelRorect/data/PascalVOC/JPEGImage/")

    def DoneTrans(self):
        self.doneN = Ui_done()
        self.doneN.show()


#更改图像分辨率为1280*720
def convertjpg(jpgfile, outdir, width=240, height=180):
    img = Image.open(jpgfile)
    new_img = img.resize((width, height), Image.BILINEAR)
    filename = os.path.splitext(jpgfile)[0];  # 文件名
    filetype = os.path.splitext(jpgfile)[1];  # 文件类型
    new_img.save(os.path.join(outdir, filename+'_converted'+filetype))
    print('sds')

#翻转图片
def FlipImg(jpgfile, outdir):
    img = Image.open(jpgfile)
    filename = os.path.splitext(jpgfile)[0];  # 文件名
    filetype = os.path.splitext(jpgfile)[1];  # 文件类型
    flipped_img = np.fliplr(img)
    flippedimg = Image.fromarray(flipped_img)
    flippedimg.save(os.path.join(outdir, filename+'_flipped'+filetype))
    #matplotlib.image.imsave(outdir+filename+'_fllipped'+filetype, flipped_img)

#图像加噪
def NoiseImg(jpgfile, outdir):
    #img = Image.open(jpgfile)
    img = cv2.imread(jpgfile)
    filename = os.path.splitext(jpgfile)[0];  # 文件名
    filetype = os.path.splitext(jpgfile)[1];  # 文件类型
    '''
    noise = np.random.randint(5, size=(240, 180, 4), dtype='uint8')
    HEIGHT, WIDTH , DEPTH= img.shape
    
    print(HEIGHT)
    print(WIDTH)

    for i in range(WIDTH):
        for j in range(HEIGHT):
            for k in range(DEPTH):
                if (img[i][j][k] != 255):
                    img[i][j][k] += noise[i][j][k]
    '''

    img1 = PepperandSalt(img, 0.2)
    #img1.save(os.path.join(outdir, filename+'_noise'+filetype))
    cv2.imwrite(filename+'_noise'+filetype, img1)
    print(filename)
def PepperandSalt(src,percetage):
    NoiseImg=src
    NoiseNum=int(percetage*src.shape[0]*src.shape[1])
    for i in range(NoiseNum):
        randX=random.randint(0,src.shape[0]-1)
        randY=random.randint(0,src.shape[1]-1)
        if random.random_integers(0,1)<=0.5:
            NoiseImg[randX,randY]=0
        else:
            NoiseImg[randX,randY]=255
    return NoiseImg

