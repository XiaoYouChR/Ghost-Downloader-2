# coding:utf-8

from PySide2.QtCore import QSize, Qt
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QToolButton


class MaximizeButton(QToolButton):
    """ 最大化按钮 """

    def __init__(self, skinName, parent=None):

        super().__init__(parent)

        self.skinName = skinName

        self.iconPathDict_list = [
            {'normal': f'{self.skinName}/title_bar/最大化按钮_normal_57_40.png',
             'hover': f'{self.skinName}/title_bar/最大化按钮_hover_57_40.png',
             'pressed': f'{self.skinName}/title_bar/最大化按钮_pressed_57_40.png'},
            {'normal': f'{self.skinName}/title_bar/向下还原按钮_normal_57_40.png',
             'hover': f'{self.skinName}/title_bar/向下还原按钮_hover_57_40.png',
             'pressed': f'{self.skinName}/title_bar/向下还原按钮_pressed_57_40.png'}
        ]
        self.resize(28, 28)
        # 设置标志位
        self.isMax = False
        self.setIcon(
            QIcon(f'{self.skinName}/title_bar/最大化按钮_normal_57_40.png'))
        self.setIconSize(QSize(28, 28))

    def __updateIcon(self, iconState: str):
        """ change the icon based on the iconState """
        self.setIcon(
            QIcon(self.iconPathDict_list[self.isMax][iconState]))

    def enterEvent(self, e):
        self.__updateIcon('hover')

    def leaveEvent(self, e):
        self.__updateIcon('normal')

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            return
        self.__updateIcon('pressed')
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.RightButton:
            return
        self.isMax = not self.isMax
        self.__updateIcon('normal')
        super().mouseReleaseEvent(e)

    def setMaxState(self, isMax: bool):
        """ update the maximized state and icon """
        if self.isMax == isMax:
            return
        self.isMax = isMax
        self.__updateIcon('normal')


class ThreeStateToolButton(QToolButton):
    """ A ToolButton with different icons in normal, hover and pressed states """

    def __init__(self, iconPath_dict: dict, icon_size: tuple = (50, 50), parent=None):
        super().__init__(parent)
        self.iconPath_dict = iconPath_dict
        self.resize(*icon_size)
        self.setCursor(Qt.ArrowCursor)
        self.setIconSize(self.size())
        self.setIcon(QIcon(self.iconPath_dict['normal']))
        self.setStyleSheet('border: none; margin: 0px')

    def enterEvent(self, e):
        """ hover时更换图标 """
        self.setIcon(QIcon(self.iconPath_dict['hover']))

    def leaveEvent(self, e):
        """ leave时更换图标 """
        self.setIcon(QIcon(self.iconPath_dict['normal']))

    def mousePressEvent(self, e):
        """ 鼠标左键按下时更换图标 """
        if e.button() == Qt.RightButton:
            return
        self.setIcon(QIcon(self.iconPath_dict['pressed']))
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        """ 鼠标左键按下时更换图标 """
        if e.button() == Qt.RightButton:
            return
        self.setIcon(QIcon(self.iconPath_dict['normal']))
        super().mouseReleaseEvent(e)
