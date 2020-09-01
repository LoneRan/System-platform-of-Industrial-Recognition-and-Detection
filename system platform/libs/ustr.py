# -*- coding: utf8 -*-
import sys

#针对py2/py3以及pyqt4/pyqt5分别进行字符串解码
def ustr(x):
    '''py2/py3 unicode helper'''

    if sys.version_info < (3, 0, 0):
        from PyQt4.QtCore import QString
        if type(x) == str:
            return x.decode('utf-8')
        if type(x) == QString:
            return unicode(x)
        return x
    else:
        return x  # py3
