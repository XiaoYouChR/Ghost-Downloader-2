import ssl
import sys
import threading
import time
import winreg
from datetime import timedelta
from glob import glob
from multiprocessing import freeze_support
from os import path, getcwd, makedirs, access, W_OK, startfile, remove
from re import findall, IGNORECASE, compile, sub
from urllib import request
from webbrowser import open_new_tab

import requests
from PySide2.QtCore import QRect, Signal, QSize, QLockFile, QObject,QPropertyAnimation, QEasingCurve
from PySide2.QtGui import Qt, QPixmap, QIcon, QMovie
from PySide2.QtWidgets import QScrollArea, QWidget, QPushButton, QSizePolicy, QLabel, QApplication, QMessageBox, \
    QComboBox, QGroupBox, QHBoxLayout, QVBoxLayout, QTextEdit, QLineEdit, QSpacerItem, QFileDialog, \
    QSystemTrayIcon, QFrame, QPlainTextEdit, QTableWidget, QTableWidgetItem, QRadioButton

from DownloadEngine import DownloadEngine
from framelesswindow import AcrylicWindow, AcrylicDialog
from titlebar import MainWindowTitleBar


# 槽
def Move(object, x, y):
    object.move(x, y)


def SetText(object, text: str):
    object.setText(text)


def Resize(object, width: int, height: int):
    object.resize(width, height)


def MessageBox(icon: QPixmap, title: str, content: str):
    MyMessageBox(icon, title, content)


# 全局信号类
class GlobalSignal(QObject):
    # 自定义信号
    move_object = Signal(QWidget, int, int)
    change_text = Signal(QLabel, str)
    resize_object = Signal(QWidget, int, int)
    message_box = Signal(QPixmap, str, str)


# 实例化信号类并Connect
globalSignal = GlobalSignal()
globalSignal.move_object.connect(Move)
globalSignal.change_text.connect(SetText)
globalSignal.resize_object.connect(Resize)
globalSignal.message_box.connect(MessageBox)


# 全局函数
def countActionValues(start: int, end: int):
    temp = end - start
    # actionValuesList = [1 / 24, 1 / 24, 1 / 16, 1 / 12, 1 / 8, 1 / 4, 1 / 6, 1 / 12, 1 / 12, 1 / 16]
    # actionValuesList = [0.015,0.05,0.1,0.2,0.35,0.6,0.8,0.9,0.95,1]
    actionValuesList = [0.005, 0.015, 0.03, 0.05, 0.07, 0.1, 0.14, 0.2, 0.27, 0.35, 0.4, 0.6, 0.72, 0.8, 0.84, 0.9,
                        0.94, 0.96, 0.98, 1]
    actionValuesList = [i * temp + start for i in actionValuesList]
    return actionValuesList


def resizeAction(object, width: int, height: int):
    def action():

        objW = object.width()
        objH = object.height()

        if objW != width and objH != height:
            actionWidthesList = countActionValues(objW, width)
            actionHeightsList = countActionValues(objH, height)

            for i in range(len(actionWidthesList)):
                globalSignal.resize_object.emit(object, actionWidthesList[i], actionHeightsList[i])
                time.sleep(0.013)

        elif objW != width:
            actionWidthesList = countActionValues(objW, width)

            for i in actionWidthesList:
                globalSignal.resize_object.emit(object, i, height)
                time.sleep(0.013)

        elif objH != height:
            actionHeightsList = countActionValues(objH, height)

            for i in actionHeightsList:
                globalSignal.resize_object.emit(object, width, i)
                time.sleep(0.013)

    threading.Thread(target=action, daemon=True).start()


def moveAction(object, x: int, y: int, close=False):
    def action():

        objX = object.x()
        objY = object.y()

        if objX != x and objY != y:

            actionXsList = countActionValues(objX, x)
            actionYsList = countActionValues(objY, y)

            for i in range(len(actionXsList)):
                globalSignal.move_object.emit(object, actionXsList[i], actionYsList[i])
                time.sleep(0.013)

        elif objX != x:

            actionValuesList = countActionValues(objX, x)

            for i in actionValuesList:
                globalSignal.move_object.emit(object, i, objY)
                time.sleep(0.013)

        elif objY != y:

            actionValuesList = countActionValues(objY, y)

            for i in actionValuesList:
                globalSignal.move_object.emit(object, objX, i)
                time.sleep(0.013)

        if close == True:
            object.close()

    threading.Thread(target=action, daemon=True).start()


def changeConfig():
    with open("config.cfg", "w", encoding="utf-8") as f:
        f.write(f"{threadNum}\n{defaultPath}\n{skinName}\n{reduceSpeed}\n{reduceSpeed_2}\n{GUI}")
        print(f"{threadNum}\n{defaultPath}\n{skinName}\n{reduceSpeed}\n{reduceSpeed_2}\n{GUI}")
        f.close()


def decidePathWin(parent, texiEdit, default=False):
    global defaultPath
    filePath = QFileDialog.getExistingDirectory(parent, "选择文件夹", dir=defaultPath)
    if not filePath == "":
        if not default:
            texiEdit.setText(filePath)
        elif default:
            defaultPath = filePath
            texiEdit.setText(defaultPath)
            changeConfig()


def newDownloadTask(iconPath: str, url: str, filename: str, download_dir: str, blocks_num: int, parent=None,
                    autoStarted=False):
    global DownGroupBoxesList

    if not autoStarted:
        if path.exists("history.xml") == True:
            with open("history.xml", "r", encoding="utf-8") as f:
                tmp = f.read()
                f.close()

                tmp = findall(f"<hst><filename>{filename}</filename><downdir>{download_dir}</downdir>", tmp)
                print(tmp)
                if tmp:
                    globalSignal.message_box.emit(parent.logoImg, "你这是故意找茬啊", "有把同一个文件下载到同一个文件夹的人吗？")
                    return  # 结束
                elif not tmp:
                    with open("history.xml", "a", encoding="utf-8") as t:
                        t.write(f"<hst><filename>{filename}</filename><downdir>{download_dir}</downdir>"
                                f"<downurl>{url}</downurl><threadnum>{blocks_num}</threadnum><icon>{iconPath}</icon></hst>")
                        t.close()

        else:
            with open("history.xml", "w", encoding="utf-8") as f:
                f.write(f"<hst><filename>{filename}</filename><downdir>{download_dir}</downdir>"
                        f"<downurl>{url}</downurl><threadnum>{blocks_num}</threadnum><icon>{iconPath}</icon></hst>")
                f.close()

    icon = QPixmap(iconPath)

    DownGroupBoxesList.append(DownGroupBox(icon, url, filename, download_dir, blocks_num, parent))
    ID = len(DownGroupBoxesList) - 1

    try:
        DownGroupBoxesList[ID].resize(window.w - 20, 73)
    except:
        DownGroupBoxesList[ID].resize(580, 73)

    DownGroupBoxesList[ID].move(3, ID * 78 + 5)
    DownGroupBoxesList[ID].show()

    parent.downWidget.resize(parent.downWidget.width(), (ID + 1) * 78 + 5)


# 类
class PictureLabel(QLabel):
    def __init__(self, parent, pixmap: QPixmap=None):
        super(PictureLabel, self).__init__(parent)
        self.setScaledContents(True)

        if pixmap:
            self.setPixmap(pixmap)


class BeggingWindow(AcrylicWindow):
    def __init__(self, parent=None):
        super(BeggingWindow, self).__init__(parent=parent, skinName=skinName)

        # QSS
        with open(f"{skinName}/GlobalQSS.qss", "r", encoding="utf-8") as f:
            GlobalQSS = f.read()
            # self.setStyleSheet(_)
            f.close()

        with open(f"{skinName}/MainQSS.qss", "r", encoding="utf-8") as f:
            MainQSS = f.read()
            # self.setStyleSheet(_)
            f.close()

        self.setStyleSheet(GlobalQSS + MainQSS)

        self.setWindowTitle("赞助晓游ChR写出更好的 /病毒(划掉)/ 程序.")
        self.setObjectName("BeggingWindow")
        self.setFixedSize(800, 600)

        self.QQLabel = PictureLabel(self)
        self.QQLabel.setGeometry(20,40,210,300)
        self.WechatLabel = PictureLabel(self)
        self.WechatLabel.setGeometry(250,40,210,300)
        self.AlipayLabel = PictureLabel(self)
        self.AlipayLabel.setGeometry(480,40,210,300)

        self.Label = QLabel(self)
        self.setObjectName("Label")
        self.Label.move(310,15)
        self.Label.setText("感谢Thanks♪(･ω･)ﾉ捐赠!~ 谢谢您!~")

        threading.Thread(target=lambda: self.__setPixmap("https://s1.ax1x.com/2022/12/27/zza3Of.png","QQ",self.QQLabel), daemon=True).start()  # 设置图片
        threading.Thread(target=lambda: self.__setPixmap("https://s1.ax1x.com/2022/12/27/zza16P.png","Wechat",self.WechatLabel), daemon=True).start()  # 设置图片
        threading.Thread(target=lambda: self.__setPixmap("https://s1.ax1x.com/2022/12/27/zzaGm8.jpg","Alipay",self.AlipayLabel), daemon=True).start()  # 设置图片

        self.textEdit = QTextEdit(self)
        self.textEdit.setObjectName(u"textEdit")
        self.textEdit.setGeometry(QRect(20,350,760,230))
        self.textEdit.setReadOnly(True)

        # response = requests.get("https://obs.cstcloud.cn/share/obs/xiaoyouchr/JuanZengInfomation.txt",headers=headers,proxies=proxies,verify=False)
        # response.encoding = "utf-8"
        # response = response.text
        response = "感谢各位的每一笔捐赠鸭~!\n留下付款备注的话将会把您的大名写入捐赠榜哦！"

        self.textEdit.setText(response)

        self.show()
        self.exec_()
        
    def __setPixmap(self, url:str, name:str, label:QLabel):
        global proxies

        finished = False
        while not finished:
            try:
                self.icon = requests.get(url, headers=headers, proxies=proxies).content
                finished = True
            except Exception as err:
                print(err)
            time.sleep(0.15)

        with open(f'temp/{name}-icon', 'wb') as f:
            f.write(self.icon)
            f.close()
        self.icon = QPixmap(f'temp/{name}-icon')

        label.setPixmap(self.icon)


class CheckProxyServer:

    def __init__(self):
        self.__path = r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
        self.__INTERNET_SETTINGS = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER,
                                                    self.__path, 0, winreg.KEY_ALL_ACCESS)

    def get_server_form_Win(self):
        """获取代理配置的ip和端口号"""
        ip, port = "", ""
        if self.is_open_proxy_form_Win():
            try:
                ip, port = winreg.QueryValueEx(self.__INTERNET_SETTINGS, "ProxyServer")[0].split(":")
                print("获取到代理信息：{}:{}".format(ip, port))
            except FileNotFoundError as err:
                print("没有找到代理信息：" + str(err))
            except Exception as err:
                print("有其他报错：" + str(err))
            return f"{ip}:{port}"
        else:
            print("系统没有开启代理")
            return False

    def is_open_proxy_form_Win(self):
        """判断是否开启了代理"""
        try:
            if winreg.QueryValueEx(self.__INTERNET_SETTINGS, "ProxyEnable")[0] == 1:
                return True
        except FileNotFoundError as err:
            print("没有找到代理信息：" + str(err))
        except Exception as err:
            print("有其他报错：" + str(err))
        return False


class DownGroupBox(QGroupBox):
    def __init__(self, icon: QPixmap, url: str, filename: str, download_dir: str, blocks_num: int, parent=None):
        super().__init__(parent=parent.downWidget)

        assert 1 <= blocks_num <= 2048

        self.w = self.width()
        self.h = self.height()

        self.url = url
        self.filename = filename
        self.download_dir = download_dir
        self.cache_dir = f"{self.download_dir}/.cache/"
        self.blocks_num = blocks_num
        self.__bad_url_flag = False
        self.fileSize = self.__get_size()

        if self.fileSize == 0:
            self.clear()

        else:

            print(self.fileSize)

            self.Paused = False

            # setUpGUI
            self.setStyleSheet(".QLabel {color: rgb(70, 70, 70);}")

            self.imgLable = QLabel(self)
            self.imgLable.setScaledContents(True)
            self.imgLable.setPixmap(icon)
            self.imgLable.setGeometry(QRect(5, 5, 64, 64))

            self.progressBar = MyProgressBar(self)
            self.progressBar.move(74, 26)
            self.progressBar.resize(492, 21)
            self.progressBar.setValue(100)

            self.openFileBtn = QPushButton(self)
            self.openFileBtn.setGeometry(QRect(441, 50, 71, 21))
            self.openFileBtn.setProperty("round", True)

            self.fileSizeLabel = QLabel(self)
            self.fileSizeLabel.setGeometry(QRect(201, 49, 131, 18))

            self.fileNameLabel = QLabel(self)
            self.fileNameLabel.setGeometry(QRect(75, 5, 389, 18))

            self.speedLabel = QLabel(self)
            self.speedLabel.setGeometry(QRect(75, 49, 131, 18))

            self.timeLabel = QLabel(self)
            self.timeLabel.setGeometry(QRect(306, 49, 131, 18))

            self.stateLabel = QLabel(self)
            self.stateLabel.setGeometry(QRect(74, 25, 492, 21))
            self.stateLabel.setStyleSheet("color: rgb(84, 84, 84)")
            self.stateLabel.setAlignment(Qt.AlignCenter)

            self.pauseBtn = QPushButton(self)
            self.pauseBtn.setGeometry(QRect(521, 50, 21, 21))

            self.threadNumLabel = QLabel(self)
            self.threadNumLabel.setGeometry(QRect(464, 5, 200, 18))

            self.JuanZengBtn = QPushButton(self)
            self.JuanZengBtn.setGeometry(QRect(360, 5, 46, 21))
            self.JuanZengBtn.setObjectName(u"JuanZengBtn")
            self.JuanZengBtn.setProperty("round", True)

            # Icon
            self.pauseIcon = QIcon()
            self.pauseIcon.addFile(f"{skinName}/pause", QSize(), QIcon.Normal, QIcon.Off)
            self.playIcon = QIcon()
            self.playIcon.addFile(f"{skinName}/play", QSize(), QIcon.Normal, QIcon.Off)

            self.pauseBtn.setIcon(self.pauseIcon)

            self.cancelBtn = QPushButton(self)
            self.cancelBtn.setGeometry(QRect(551, 50, 21, 21))

            # retranslateUi
            self.JuanZengBtn.setText("Beg")
            self.openFileBtn.setText("打开目录")
            self.stateLabel.setText("正在准备...")
            self.cancelBtn.setText("╳")
            self.fileNameLabel.setText(self.filename)
            self.fileSizeLabel.setText("大小:%s" % self.__get_readable_size(self.fileSize))
            self.timeLabel.setText("剩余时间:Check...")
            self.threadNumLabel.setText(f"线程数:{self.blocks_num}")
            self.speedLabel.setText("速度:Check...")
            # 连接函数
            self.openFileBtn.clicked.connect(lambda: startfile(self.download_dir))
            self.pauseBtn.clicked.connect(self.pause)
            self.cancelBtn.clicked.connect(self.cancel)
            self.JuanZengBtn.clicked.connect(BeggingWindow)

            # CreatingProcess
            self.Process = DownloadEngine(url, filename, download_dir, blocks_num, proxies)
            self.Process.start()
            threading.Thread(target=self.Supervise, daemon=True).start()

    def Supervise(self):
        """万恶的督导：监视下载速度、进程数；提出整改意见；"""
        REFRESH_INTERVAL = 1  # 每多久输出一次监视状态
        LAG_COUNT = 10  # 计算过去多少次测量的平均速度
        self.__download_record = []
        percentage = 0
        while True:
            if percentage < 100:
                dwn_size = sum([path.getsize(cachefile) for cachefile in self.__get_cache_filenames()])
                self.__download_record.append({"timestamp": time.time(), "size": dwn_size})
                if len(self.__download_record) > LAG_COUNT:
                    self.__download_record.pop(0)
                s = self.__download_record[-1]["size"] - self.__download_record[0]["size"]
                t = self.__download_record[-1]["timestamp"] - self.__download_record[0]["timestamp"]
                if not t == 0 and self.Paused == False:
                    speed = s / t
                    readable_speed = self.__get_readable_size(speed)  # 变成方便阅读的样式
                    percentage = self.__download_record[-1]["size"] / self.fileSize * 100
                    status_msg = f"\r[info] {percentage:.1f} % | {readable_speed}/s | {self.blocks_num}"
                    sys.stdout.write(status_msg)
                    # 更改界面
                    self.progressBar.setValue(percentage)

                    globalSignal.change_text.emit(self.stateLabel,
                                                  f"正在下载:{percentage:.1f}% ({self.__get_readable_size(self.__download_record[-1]['size'])})")
                    globalSignal.change_text.emit(self.speedLabel, f"速度:{readable_speed}/s")
                    if speed == 0:
                        globalSignal.change_text.emit(self.timeLabel, "剩余时间:Check...")
                    else:
                        globalSignal.change_text.emit(self.timeLabel, f"剩余时间:%s" % timedelta(seconds=
                                                                                             round((self.fileSize -
                                                                                                    self.__download_record[
                                                                                                        -1][
                                                                                                        'size']) / speed)))
                    globalSignal.change_text.emit(self.threadNumLabel,
                                                  f"线程数:{self.blocks_num}")

                time.sleep(REFRESH_INTERVAL)

            elif percentage == 100:
                time.sleep(0.3)
                sewed_size = path.getsize(f"{self.download_dir}/{self.filename}")
                sew_progress = (sewed_size / self.fileSize) * 100
                sys.stdout.write(f"[info] sew_progress {sew_progress} %\n")
                globalSignal.change_text.emit(self.stateLabel,
                                              f"正在合并:{sew_progress}% ({self.__get_readable_size(sewed_size)})")
                self.progressBar.setValue(sew_progress)
                if (self.fileSize - sewed_size) == 0:
                    globalSignal.change_text.emit(self.stateLabel, "下载完成!")
                    self.progressBar.setValue(sew_progress)
                    systemTray.showMessage("Hey--下载完成了!", f"{self.filename} 已完成下载!", logoIcon)
                    systemTray.messageClicked.connect(lambda: startfile(self.download_dir))
                    break
            else:
                self.stop()
                self.clear()
                systemTray.showMessage("Hey--下载失败了!", f"{self.filename} 已失败下载!", logoIcon)
                systemTray.messageClicked.connect(window.show)
                globalSignal.change_text.emit(self.stateLabel, "下载完成!")
                break

    def __get_readable_size(self, size):
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        unit_index = 0
        K = 1024.0
        while size >= K:
            size = size / K
            unit_index += 1
        return "%.2f %s" % (size, units[unit_index])

    def __get_size(self):
        try:
            req = request.urlopen(self.url)
            content_length = req.headers["Content-Length"]
            req.close()
            return int(content_length)
        except Exception as err:
            self.__bad_url_flag = True
            print(f"[Error] {err}")
            return 0

    def resizeEvent(self, event):
        self.w = self.width()
        self.h = self.height()

        self.progressBar.resize(self.w - 88, 21)
        self.stateLabel.resize(self.w - 88, 21)
        self.openFileBtn.move(self.w - 123, 49)
        self.cancelBtn.move(self.w - 23, 49)
        self.pauseBtn.move(self.w - 48, 49)
        self.threadNumLabel.move(self.w - 116, 5)
        self.JuanZengBtn.move(self.w - 220, 5)

        self.speedLabel.move(self.w / 6 - 19, 50)
        self.fileSizeLabel.move(self.w / 3 + 14, 50)
        self.timeLabel.move(self.w / 2 + 26, 50)

    def __get_readable_size(self, size):
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        unit_index = 0
        K = 1024.0
        while size >= K:
            size = size / K
            unit_index += 1
        return "%.2f %s" % (size, units[unit_index])

    def stop(self):
        self.Process.kill()

    def pause(self):
        """接受Pause按钮发出的暂停信号并进行操作"""
        if self.Paused == False:  # 没暂停就暂停

            self.Paused = True

            self.pauseBtn.setEnabled(False)
            self.cancelBtn.setEnabled(False)
            self.pauseBtn.setIcon(self.playIcon)
            globalSignal.change_text.emit(self.stateLabel, "正在暂停:正在停止线程...")

            self.stop()

            self.pauseBtn.setEnabled(True)
            self.cancelBtn.setEnabled(True)
            globalSignal.change_text.emit(self.stateLabel, "正在暂停...")

        elif self.Paused == True:  # 暂停了就开始
            self.pauseBtn.setEnabled(False)
            self.cancelBtn.setEnabled(False)
            self.pauseBtn.setIcon(self.pauseIcon)
            globalSignal.change_text.emit(self.stateLabel, "正在开始:正在召回线程...")
            # 再次召集 worker。不调用 start 的原因是希望他继续卡住主线程。
            self.again()

            self.pauseBtn.setEnabled(True)
            self.cancelBtn.setEnabled(True)

            self.Paused = False

    def again(self):
        self.Process = DownloadEngine(self.url, self.filename, self.download_dir, self.blocks_num, proxiesIP)
        self.Process.start()

    def cancel(self):
        self.pauseBtn.setEnabled(False)
        self.cancelBtn.setEnabled(False)
        globalSignal.change_text.emit(self.stateLabel, "正在取消任务:正在暂停线程...")
        self.Paused = True
        self.stop()
        globalSignal.change_text.emit(self.stateLabel, "正在取消任务:正在清理缓存...")
        moveAction(self, self.w + 35, self.y(), True)
        if len(DownGroupBoxesList) == 1:
            del DownGroupBoxesList[0]
        else:
            ID = DownGroupBoxesList.index(self)
            del DownGroupBoxesList[ID]
            for i in range(len(DownGroupBoxesList)):
                moveAction(DownGroupBoxesList[i], DownGroupBoxesList[i].x(), i * 78 + 5)
        self.clear()

    def clear(self, all_cache=False):
        # 清除历史
        with open("history.xml", "r", encoding="utf-8") as f:
            tmp = f.read()
            f.close()
            tmp = sub(f"<hst><filename>{self.filename}</filename><downdir>{self.download_dir}</downdir>", "Deleted",
                      tmp)
            print(tmp)

        with open("history.xml", "w", encoding="utf-8") as f:
            f.write(tmp)
            f.close()

        delSuccess = False
        while not delSuccess:
            try:
                if all_cache:  # TODO 需要交互提醒即将删除的文件夹 [Y]/N 确认。由于不安全，先不打算实现。
                    pass
                else:
                    for filename in self.__get_cache_filenames():
                        remove(filename)
                    delSuccess = True
            except PermissionError:
                print("删除失败,正在重试!")
                delSuccess = False
            time.sleep(0.15)

    def __get_cache_filenames(self):
        return glob(f"{self.cache_dir}{self.filename}.*.gd2")


class NewNetTaskWindow(AcrylicDialog):
    def __init__(self, icon, downurl, filename, parent=None):
        super().__init__(skinName, parent)
        self.icon = icon
        self.parent = parent

        self.threadNum = threadNum
        # QSS
        with open(f"{skinName}/GlobalQSS.qss", "r", encoding="utf-8") as f:
            GlobalQSS = f.read()
            # self.setStyleSheet(_)
            f.close()
        with open(f"{skinName}/MainQSS.qss", "r", encoding="utf-8") as f:
            MainQSS = f.read()
            # self.setStyleSheet(_)
            f.close()
        self.setStyleSheet(GlobalQSS + MainQSS)

        print(f"{icon}\n{downurl}\n{filename}")
        self.setUp()
        # 自定义功能区
        # WPSsupport = compile(u"\^\^\^\^\^", IGNORECASE).search(downurl)
        # WPSSupport_2 = compile(u"\^\^\^\^\^\$\$\$\$\$", IGNORECASE).search(downurl)
        # CSTsupport = compile(u"\$\$\$\$\$", IGNORECASE).search(downurl)
        # print(WPSSupport_2)

        # print("OD支持")
        # self.WPSRadioBtn.setDisabled(True)
        # self.CSTRadioBtn.setDisabled(True)
        self.ODurl = downurl
        self.ODname = filename
        self.ODRadioBtn.setChecked(True)  # 默认Onedrive

        # if CSTsupport:
        #     print("CST支持")
        #     self.CSTRadioBtn.setDisabled(False)
        #     self.ODurl = findall(u"([\S\s]*)\^\^\^\^\^", downurl)[0]
        #     self.CSTurl = findall(u"\$\$\$\$\$([\S\s]*)", downurl)[0]
        #     self.ODname = findall(u"([\S\s]*)\^\^\^\^\^", filename)[0]
        #     self.CSTname = findall(u"\$\$\$\$\$([\S\s]*)", filename)[0]
        # if WPSsupport and not WPSSupport_2:
        #     print("WPS支持")
        #     self.WPSRadioBtn.setDisabled(False)
        #     self.WPSurl = findall(u"\^\^\^\^\^([\S\s]*)\$\$\$\$\$", downurl)[0]
        #     self.WPSurl = findall(u",?([\S\s]*?),", self.WPSurl)
        #     print(self.WPSurl)
        #     self.WPSname = findall(u"\^\^\^\^\^([\S\s]*)\$\$\$\$\$", filename)[0]
        #     self.WPSname = findall(u",?([\S\s]*?),", self.WPSname)
        #     print(self.WPSname)
        #     self.WPSRadioBtn.setChecked(True)  # 默认WPS

        # 连接函数
        self.threadNumC.currentIndexChanged.connect(self.changeThreadNum)
        self.decidePathBtn.clicked.connect(lambda: decidePathWin(self, self.decidePathEdit, False))
        self.startBtn.clicked.connect(self.startDownload)
        # 保持运行
        self.exec_()

    def changeThreadNum(self):
        temp = self.threadNum
        self.threadNum = int(self.threadNumC.currentText())
        print(self.threadNum)
        if temp >= 32:
            if self.threadNum < 32:
                warning = MyQuestionBox(
                    '警告！',
                    '你选择的线程过低！很可能会造成下载速度过慢或其他BUG！\n\n你确定要选择小于32个下载线程吗？').Question()
                if warning == QMessageBox.No:
                    self.threadNum = temp
                    self.threadNumC.setCurrentIndex(self.threadNum - 1)
            elif temp <= 256:
                if self.threadNum > 256:
                    counts = 3
                    warning = MyQuestionBox(    
                        '警告！',
                        '你选择的线程过高！把您的电脑淦爆！\n\n你确定要选择大于256个下载线程吗？').Question()
                    while warning == QMessageBox.Yes:
                        warning = MyQuestionBox(        
                            '警告！',
                            f'你选择的线程过高！可能会把您的电脑淦爆！\n\n你确定要选择大于256个下载线程吗？({counts})').Question()
                        if warning == QMessageBox.Yes:
                            counts -= 1
                            print(counts)
                        if counts == 0:
                            break
                        if warning == QMessageBox.No:
                            break
                    if warning == QMessageBox.No:
                        self.threadNum = temp
                        self.threadNumC.setCurrentIndex(self.threadNum - 1)

    def setUp(self):
        self.setObjectName(u"NewNetTaskWindow")
        self.resize(500, 250)
        self.setMinimumSize(QSize(500, 250))
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(10, 26, 10, 10)
        self.threadNumG = QGroupBox(self)
        self.threadNumG.setObjectName(u"threadNumG")
        self.horizontalLayout_2 = QHBoxLayout(self.threadNumG)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.warningLabel = QLabel(self.threadNumG)
        self.warningLabel.setObjectName(u"warningLabel")

        self.horizontalLayout_2.addWidget(self.warningLabel)

        self.threadNumC = QComboBox(self.threadNumG)
        self.threadNumC.setObjectName(u"threadNumC")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.threadNumC.sizePolicy().hasHeightForWidth())
        self.threadNumC.setSizePolicy(sizePolicy)

        self.horizontalLayout_2.addWidget(self.threadNumC)

        self.verticalLayout.addWidget(self.threadNumG)

        self.decidePathG = QGroupBox(self)
        self.decidePathG.setObjectName(u"decidePathG")
        self.horizontalLayout = QHBoxLayout(self.decidePathG)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.decidePathEdit = QLineEdit(self.decidePathG)
        self.decidePathEdit.setObjectName(u"decidePathEdit")
        self.decidePathEdit.setReadOnly(True)
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.decidePathEdit.sizePolicy().hasHeightForWidth())
        self.decidePathEdit.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.decidePathEdit)

        self.decidePathBtn = QPushButton(self.decidePathG)
        self.decidePathBtn.setObjectName(u"decidePathBtn")
        self.decidePathBtn.setProperty("round", True)
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Ignored)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.decidePathBtn.sizePolicy().hasHeightForWidth())
        self.decidePathBtn.setSizePolicy(sizePolicy2)

        self.horizontalLayout.addWidget(self.decidePathBtn)

        self.verticalLayout.addWidget(self.decidePathG)

        self.decideSourceG = QGroupBox(self)
        self.decideSourceG.setObjectName(u"decideSourceG")
        self.horizontalLayout_3 = QHBoxLayout(self.decideSourceG)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        # self.WPSRadioBtn = QRadioButton(self.decideSourceG)
        # self.WPSRadioBtn.setObjectName(u"WPSRadioBtn")
        # sizePolicy2.setHeightForWidth(self.WPSRadioBtn.sizePolicy().hasHeightForWidth())
        # self.WPSRadioBtn.setSizePolicy(sizePolicy2)
        #
        # self.horizontalLayout_3.addWidget(self.WPSRadioBtn)

        self.ODRadioBtn = QRadioButton(self.decideSourceG)
        self.ODRadioBtn.setObjectName(u"ODRadioBtn")
        sizePolicy2.setHeightForWidth(self.ODRadioBtn.sizePolicy().hasHeightForWidth())
        self.ODRadioBtn.setSizePolicy(sizePolicy2)

        self.horizontalLayout_3.addWidget(self.ODRadioBtn)

        # self.CSTRadioBtn = QRadioButton(self.decideSourceG)
        # self.CSTRadioBtn.setObjectName(u"CSTRadioBtn")
        # sizePolicy2.setHeightForWidth(self.CSTRadioBtn.sizePolicy().hasHeightForWidth())
        # self.CSTRadioBtn.setSizePolicy(sizePolicy2)
        #
        # self.horizontalLayout_3.addWidget(self.CSTRadioBtn)

        self.ODRadioBtn.raise_()
        # self.WPSRadioBtn.raise_()
        # self.CSTRadioBtn.raise_()

        self.verticalLayout.addWidget(self.decideSourceG)

        self.startBtn = QPushButton(self)
        self.startBtn.setObjectName(u"startBtn")
        self.startBtn.setProperty("round", True)
        sizePolicy3 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.startBtn.sizePolicy().hasHeightForWidth())
        self.startBtn.setSizePolicy(sizePolicy3)

        self.verticalLayout.addWidget(self.startBtn)

        # 设置文本
        self.setWindowTitle(u"\u65b0\u5efa\u4e0b\u8f7d\u4efb\u52a1")
        self.threadNumG.setTitle(u"\u786e\u5b9a\u60a8\u7684\u4e0b\u8f7d\u7ebf\u7a0b\u6570")
        self.threadNumC.addItems([str(i + 1) for i in range(2048)])
        self.threadNumC.setCurrentIndex(threadNum - 1)
        self.warningLabel.setText(
            u"\u8bf7\u52ff\u8bbe\u7f6e\u8fc7\u9ad8\u7684\u4e0b\u8f7d\u7ebf\u7a0b,\u56e0\u4e3a\u8fd9\u53ef\u80fd\u9020\u6210\u7535\u8111\u5361\u987f\u548c\u4e0b\u8f7d\u5931\u8d25!")
        self.decidePathG.setTitle(u"\u786e\u5b9a\u60a8\u7684\u4e0b\u8f7d\u8def\u5f84")
        self.decidePathEdit.setText(defaultPath)
        self.decidePathBtn.setText(u"\u9009\u62e9\u8def\u5f84")
        self.decideSourceG.setTitle(u"\u9009\u62e9\u60a8\u7684\u4e0b\u8f7d\u6e90!")
        # self.WPSRadioBtn.setText(u"金山云(移动电信)")
        self.ODRadioBtn.setText(u"OneDrive (因资金原因暂时停用其他下载方式)")
        # self.CSTRadioBtn.setText(u"科技网(三网优化)")
        self.startBtn.setText(u"\u5f00\u59cb\u4e0b\u8f7d")
        
    # def getWPSDownloadLink(self):
    #     DownloadLink = []  # 生成空列表
    #     session = requests.Session()
    #     session.headers.update(headers)
    #     for i in self.WPSurl:
    #         session.get("https://www.kdocs.cn/view/l/ssazQO5dfN4s")
    #         response = session.get(url=i, allow_redirects=False).text
    #         URL = findall(r"\"url\":\"([\S\s]*)\",\"sha1", response)
    #         URL = URL[0].encode("utf-8").decode("unicode_escape")
    #         print(URL)
    #         DownloadLink.append(URL)
    #     return DownloadLink

    def startDownload(self):
        print(self.threadNum)
        print(self.decidePathEdit.text())
        # if self.WPSRadioBtn.isChecked() == True:  # WPS
        #     DownloadLink = self.getWPSDownloadLink()
        #     for i in range(len(DownloadLink)):
        #         newDownloadTask(self.icon, DownloadLink[i], self.WPSname[i], self.decidePathEdit.text(), self.threadNum,
        #                         window)
        # elif self.ODRadioBtn.isChecked() == True:  # OD
        newDownloadTask(self.icon, self.ODurl, self.ODname, self.decidePathEdit.text(), self.threadNum, window)
        # elif self.CSTRadioBtn.isChecked() == True:  # CST
        #     newDownloadTask(self.icon, self.CSTurl, self.CSTname, self.decidePathEdit.text(), self.threadNum, window)
        self.close()


class NewTaskWindow(AcrylicWindow):
    def __init__(self, parent=None):
        super().__init__(parent=parent, skinName=skinName)
        self.titleBar.maxBtn.setEnabled(True)
        self.setObjectName("NewTaskWindow")
        self.resize(400, 400)
        self.setMinimumSize(QSize(360, 292))
        # QSS
        with open(f"{skinName}/GlobalQSS.qss", "r", encoding="utf-8") as f:
            GlobalQSS = f.read()
            # self.setStyleSheet(_)
            f.close()
        with open(f"{skinName}/MainQSS.qss", "r", encoding="utf-8") as f:
            MainQSS = f.read()
            # self.setStyleSheet(_)
            f.close()
        self.setStyleSheet(GlobalQSS + MainQSS)
        # logo
        self.logoPixmap = QPixmap(f"{skinName}/logo.png")

        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(6, 30, 6, 6)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setSpacing(3)

        self.urlEdit = QPlainTextEdit(self)
        self.urlEdit.setObjectName("urlEdit")
        self.horizontalLayout.addWidget(self.urlEdit)

        self.addTableButton = QPushButton(self)
        self.addTableButton.setObjectName("addTableButton")
        self.addTableButton.setProperty("round", True)

        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.addTableButton.sizePolicy().hasHeightForWidth())

        self.addTableButton.setSizePolicy(sizePolicy)
        self.horizontalLayout.addWidget(self.addTableButton)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.infoTableWidget = QTableWidget(self)
        self.infoTableWidget.setObjectName("infoTableWidget")
        self.infoTableWidget.setColumnCount(3)

        __qtablewidgetitem = QTableWidgetItem()
        self.infoTableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.infoTableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.infoTableWidget.setHorizontalHeaderItem(2, __qtablewidgetitem2)

        self.infoTableWidget.setColumnWidth(0, 225)
        self.infoTableWidget.setColumnWidth(1, 50)
        self.infoTableWidget.setColumnWidth(2, 90)

        self.verticalLayout.addWidget(self.infoTableWidget)

        self.allSizeLabel = QLabel(self)

        self.verticalLayout.addWidget(self.allSizeLabel)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")

        self.pathEdit = QLineEdit(self)
        self.pathEdit.setObjectName("pathEdit")
        self.horizontalLayout_2.addWidget(self.pathEdit)

        self.decidePathBtn = QPushButton(self)
        self.decidePathBtn.setObjectName("decidePathBtn")
        self.decidePathBtn.setProperty("round", True)

        self.horizontalLayout_2.addWidget(self.decidePathBtn)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.addTaskBtn = QPushButton(self)
        self.addTaskBtn.setObjectName("addTaskBtn")
        self.addTaskBtn.setProperty("round", True)

        self.verticalLayout.addWidget(self.addTaskBtn)

        self.verticalLayout.setStretch(0, 2)
        self.verticalLayout.setStretch(1, 6)

        self.addTaskBtn.setEnabled(False)

        # retranslateUi
        self.setWindowTitle(u"\u65b0\u5efa\u4e0b\u8f7d\u4efb\u52a1")
        self.urlEdit.setPlaceholderText(
            u"\u5728\u8fd9\u91cc\u952e\u5165\u4e0b\u8f7d\u8fde\u63a5 (\u5982\u9700\u52a0\u5165\u591a\u4e2a,\u8bf7\u7528\u6362\u884c\u7b26\u5206\u9694)")
        self.addTableButton.setText(u"\u6dfb\u52a0")
        ___qtablewidgetitem = self.infoTableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(u"\u6587\u4ef6\u540d")
        ___qtablewidgetitem1 = self.infoTableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(u"\u7c7b\u578b")
        ___qtablewidgetitem2 = self.infoTableWidget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(u"\u5927\u5c0f")

        __sortingEnabled = self.infoTableWidget.isSortingEnabled()
        self.infoTableWidget.setSortingEnabled(False)
        self.infoTableWidget.setSortingEnabled(__sortingEnabled)

        self.pathEdit.setPlaceholderText(u"\u5728\u6b64\u952e\u5165\u4e0b\u8f7d\u8def\u5f84.")
        self.decidePathBtn.setText(u"\u9009\u62e9\u8def\u5f84")
        self.addTaskBtn.setText(u"\u4e0b\u8f7d")

        self.pathEdit.setText(defaultPath)
        self.pathEdit.setEnabled(False)

        # 连接函数
        self.addTableButton.clicked.connect(self.addTabel)
        self.decidePathBtn.clicked.connect(lambda: decidePathWin(self, self.pathEdit))
        self.addTaskBtn.clicked.connect(self.addTask)

        self.show()

    def addTabel(self):
        self.addTableButton.setEnabled(False)
        self.addTaskBtn.setEnabled(False)
        self.addTableButton.setText("正在\n添加")
        # 清空QTableWidget & 二维列表
        self.tableList = []
        self.infoTableWidget.setColumnCount(3)
        self.infoTableWidget.setRowCount(0)
        self.allSizeLabel.setText("")

        self.url = self.urlEdit.toPlainText()
        self.url = self.url.split('\n')
        print(self.url)

        def analysis():
            allSize = 0

            for i in range(len(self.url)):
                _ = urlRe.search(self.url[i])
                if _:
                    print("进入getinfo")
                    info = self.getFileInfo(self.url[i])
                    print(info)
                    if info == 0:
                        continue
                    else:
                        # 增加数据
                        self.infoTableWidget.setRowCount(self.infoTableWidget.rowCount() + 1)
                        self.tableList.append([0, 0, 0, 0])
                        # 文件名
                        self.tableList[i][1] = QTableWidgetItem()
                        self.infoTableWidget.setItem(i, 0, self.tableList[i][1])
                        self.tableList[i][1].setText(info[1])
                        # 类型
                        self.tableList[i][2] = QTableWidgetItem()
                        self.infoTableWidget.setItem(i, 1, self.tableList[i][2])
                        self.tableList[i][2].setText(info[2])
                        self.tableList[i][2].setFlags(Qt.ItemIsEnabled)  # 禁止修改
                        # 大小
                        self.tableList[i][3] = QTableWidgetItem()
                        self.infoTableWidget.setItem(i, 2, self.tableList[i][3])
                        self.tableList[i][3].setText(f"{round(info[0] / 1048576, 2)}MB")
                        self.tableList[i][3].setFlags(Qt.ItemIsEnabled)  # 禁止修改
                        # 修改Url
                        self.url[i] = info[3]
                        print(self.url)
                        # 重新计算总大小
                        for i in self.tableList:
                            allSize += float(i[3].text()[:-2])
                        self.allSizeLabel.setText(f"总: {len(self.tableList)}个文件（{allSize}MB)")
                else:
                    globalSignal.message_box.emit(self.logoPixmap, "ERROR", f"第{i + 1}个连接似乎有问题,请输入合法的链接!\n已自动跳过.")
                    continue

            self.addTableButton.setEnabled(True)
            self.addTaskBtn.setEnabled(True)
            self.addTableButton.setText("添加")

        threading.Thread(target=analysis, daemon=True).start()

    def getFileInfo(self, url: str):
        try:
            response = requests.head(url=url, headers=headers, allow_redirects=False, verify=False)
            print(response)

            if response.status_code == 400:  # Bad Requests
                globalSignal.message_box.emit(self.logoPixmap, "ERROR!", "HTTP400!Bad Url!\n请尝试更换下载链接!")
                return 0

            while response.status_code == 302:  # 当302的时候
                rs = response.headers["location"]  # 获取重定向信息
                print(rs)
                # 看它返回的是不是完整的URL
                t = urlRe.search(rs)
                if t:  # 是的话直接跳转
                    url = rs
                elif not t:  # 不是在前面加上URL
                    url = findall(r"((?:https?|ftp)://[\s\S]*?)", url)
                    url = url[0] + rs

                    print(url)

                response = requests.head(url=url, headers=headers, allow_redirects=False, verify=False)  # 再访问一次

            try:
                fileSize = int(response.headers["Content-Length"])
            except Exception as err:
                fileSize = 0
                globalSignal.message_box.emit(self.logoPixmap, 'ERROR!', f'{url}获取文件大小失败!\n{err}')

            try:  # 如果是onedrive形式的连接获取filename
                fileName = response.headers["Content-Disposition"]
                print(response.headers)
                fileName = findall(r"filename=\"([\s\S]*)\"", fileName)
                fileName = fileName[0]
            except:
                fileName = url.split("/")[-1]

            try:
                fileType = fileName.split(".")[-1]
            except:
                fileType = ""

            return fileSize, fileName, fileType, url

        except requests.exceptions.ConnectionError as err:
            globalSignal.message_box.emit(self.logoPixmap, "网络连接失败！", f"请检查网络连接！\n{err}")
            return 0
        except ValueError as err:
            globalSignal.message_box.emit(self.logoPixmap, "网络连接失败！", f"请尝试关闭代理！\n{err}")
            return 0

    def addTask(self):
        self.addTaskBtn.setEnabled(False)
        for i in range(len(self.url)):
            newDownloadTask(f"{skinName}/logo.png", self.url[i], self.tableList[i][1].text(), self.pathEdit.text(),
                            threadNum, window)
        self.close()


class MyProgressBar(QWidget):

    changeValue = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MyProgressBar")
        self.setStyleSheet("* {\n"
                           "    border: 1px solid rgb(100, 160, 220);\n"
                           "    border-radius: 10px;"
                           "}")

        self.progresser = QWidget(self)
        self.progresser.setObjectName("progresser")
        self.progresser.setStyleSheet("  background:rgb(100, 160, 220);")
        self.progresser.move(0, 0)
        self.progresser.resize(0, self.height())

        self.animation = QPropertyAnimation(self.progresser, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

        self.value = 0

        self.progresser.resize(self.value * self.width() / 100, self.height())

        self.changeValue.connect(self.__setValue)

        self.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.progresser.resize(self.value * self.width() / 100, self.height())

    def setValue(self,value):
        self.changeValue.emit(value)

    def __setValue(self, value):
        self.value = value
        self.animation.setEndValue(QRect(0, 0, self.value * self.width() / 100, self.height()))
        self.animation.start()


class SettingsWindow(AcrylicWindow):
    def __init__(self, parent=None):
        super().__init__(skinName, parent)
        self.titleBar.maxBtn.setEnabled(True)
        # QSS
        with open(f"{skinName}/GlobalQSS.qss", "r", encoding="utf-8") as f:
            GlobalQSS = f.read()
            # self.setStyleSheet(_)
            f.close()

        with open(f"{skinName}/MainQSS.qss", "r", encoding="utf-8") as f:
            MainQSS = f.read()
            # self.setStyleSheet(_)
            f.close()

        self.setStyleSheet(GlobalQSS + MainQSS)

        self.logoImg = QPixmap(f"{skinName}/logo.png")

        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(10, 26, 10, 10)

        self.decidePathG = QGroupBox(self)
        self.decidePathG.setObjectName(u"decidePathG")

        self.horizontalLayout_3 = QHBoxLayout(self.decidePathG)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")

        self.DefaultPathEdit = QLineEdit(self.decidePathG)
        self.DefaultPathEdit.setObjectName(u"DefaultPathEdit")
        self.horizontalLayout_3.addWidget(self.DefaultPathEdit)

        self.decidePathBtn = QPushButton(self.decidePathG)
        self.decidePathBtn.setObjectName(u"decidePathBtn")
        self.decidePathBtn.setProperty("round", True)
        self.horizontalLayout_3.addWidget(self.decidePathBtn)

        self.horizontalLayout_3.setStretch(0, 6)
        self.horizontalLayout_3.setStretch(1, 1)

        self.verticalLayout.addWidget(self.decidePathG)

        self.threadNumG = QGroupBox(self)
        self.threadNumG.setObjectName(u"threadNumG")

        self.horizontalLayout_2 = QHBoxLayout(self.threadNumG)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(9, 9, 9, 9)

        self.tipLabel = QLabel(self.threadNumG)
        self.tipLabel.setObjectName(u"tipLabel")
        self.tipLabel.setStyleSheet(u"")
        self.tipLabel.setProperty("blue", True)
        self.horizontalLayout_2.addWidget(self.tipLabel)

        self.threadNumC = QComboBox(self.threadNumG)
        self.threadNumC.setObjectName(u"threadNumC")
        self.horizontalLayout_2.addWidget(self.threadNumC)

        self.horizontalLayout_2.setStretch(0, 6)
        self.horizontalLayout_2.setStretch(1, 1)

        self.verticalLayout.addWidget(self.threadNumG)

        # self.restartG = QGroupBox(self)
        # self.restartG.setObjectName(u"restartG")
        #
        # self.horizontalLayout_5 = QHBoxLayout(self.restartG)
        # self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        #
        # self.label = QLabel(self.restartG)
        # self.label.setObjectName(u"label")
        # self.label.setProperty("blue", True)
        # self.horizontalLayout_5.addWidget(self.label)
        #
        # self.reduceSpeedEdit = QLineEdit(self.restartG)
        # self.reduceSpeedEdit.setObjectName(u"reduceSpeedEdit")
        # self.horizontalLayout_5.addWidget(self.reduceSpeedEdit)
        #
        # self.label_2 = QLabel(self.restartG)
        # self.label_2.setObjectName(u"label_2")
        # self.label_2.setProperty("blue", True)
        # self.horizontalLayout_5.addWidget(self.label_2)
        #
        # self.reduceSpeedEdit_2 = QLineEdit(self.restartG)
        # self.reduceSpeedEdit_2.setObjectName(u"reduceSpeedEdit_2")
        # self.horizontalLayout_5.addWidget(self.reduceSpeedEdit_2)
        #
        # self.label_3 = QLabel(self.restartG)
        # self.label_3.setObjectName(u"label_3")
        # self.label_3.setProperty("blue", True)
        # self.horizontalLayout_5.addWidget(self.label_3)
        #
        # self.verticalLayout.addWidget(self.restartG)

        self.GUIG = QGroupBox(self)
        self.GUIG.setObjectName(u"GUIG")

        self.horizontalLayout_6 = QHBoxLayout(self.GUIG)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")

        self.label_4 = QLabel(self.GUIG)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setProperty("blue", True)
        self.horizontalLayout_6.addWidget(self.label_4)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_6.addItem(self.horizontalSpacer_2)

        self.GUIC = QComboBox(self.GUIG)
        self.GUIC.setObjectName(u"GUIC")
        self.horizontalLayout_6.addWidget(self.GUIC)

        self.verticalLayout.addWidget(self.GUIG)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")

        self.getUpBtn = QPushButton(self)
        self.getUpBtn.setObjectName(u"getUpBtn")
        self.getUpBtn.setProperty("round", True)
        self.horizontalLayout_4.addWidget(self.getUpBtn)

        self.nowVerLable = QLabel(self)
        self.nowVerLable.setObjectName(u"nowVerLable")
        self.horizontalLayout_4.addWidget(self.nowVerLable)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(self.horizontalSpacer)

        self.horizontalLayout_4.setStretch(0, 2)
        self.horizontalLayout_4.setStretch(1, 8)
        self.horizontalLayout_4.setStretch(1, 10)

        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.BtnLayout = QHBoxLayout()
        self.BtnLayout.setObjectName(u"BtnLayout")
        
        self.JuanZengBtn = QPushButton(self)
        self.JuanZengBtn.setObjectName(u"JuanZengBtn")
        self.JuanZengBtn.setProperty("round", True)
        self.BtnLayout.addWidget(self.JuanZengBtn)
        
        self.jiaQunBtn = QPushButton(self)
        self.jiaQunBtn.setObjectName(u"jiaQunBtn")
        self.jiaQunBtn.setProperty("round", True)
        self.BtnLayout.addWidget(self.jiaQunBtn)

        self.shengMingBtn = QPushButton(self)
        self.shengMingBtn.setObjectName(u"shengMingBtn")
        self.shengMingBtn.setProperty("round", True)
        self.BtnLayout.addWidget(self.shengMingBtn)

        self.myIndexBtn = QPushButton(self)
        self.myIndexBtn.setObjectName(u"myIndexBtn")
        self.myIndexBtn.setProperty("round", True)
        self.BtnLayout.addWidget(self.myIndexBtn)

        self.BtnLayout.setStretch(0, 12)
        self.BtnLayout.setStretch(1, 3)
        self.BtnLayout.setStretch(2, 6)

        self.verticalLayout.addLayout(self.BtnLayout)

        self.verticalSpacer = QSpacerItem(20, 280, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(self.verticalSpacer)

        # 设置文本
        self.decidePathG.setTitle("下载路径设置")
        self.decidePathBtn.setText("选择路径")
        self.threadNumG.setTitle("\u4e0b\u8f7d\u7ebf\u7a0b\u8bbe\u7f6e")
        self.tipLabel.setText("请勿设置过高的下载线程,因为这可能造成电脑卡顿和下载失败!")
        # self.restartG.setTitle("\u81ea\u52a8\u91cd\u8fde\u8bbe\u7f6e")
        # self.label.setText("\u5f53\u4e0b\u8f7d\u964d\u901f\u9ad8\u4e8e")
        # self.label_2.setText("%, 且下载速度低于")
        # self.label_3.setText("KB/s\u65f6, \u81ea\u52a8\u91cd\u8fde.")
        self.GUIG.setTitle("界面设置")
        self.label_4.setText("在这里选择你想要的界面样式")
        self.getUpBtn.setText("\u68c0\u67e5\u66f4\u65b0")
        self.nowVerLable.setText("当前版本:2.0.2(22.12.27),已是最新!")
        self.JuanZengBtn.setText("捐赠晓游ChR吧！~")
        self.jiaQunBtn.setText(
            "\u70b9\u51fb\u52a0\u5165\u7fa4\u804a: \u6770\u514b\u59da\u306e\u5c0f\u5c4b \u4ee5\u83b7\u53d6\u652f\u6301")
        self.shengMingBtn.setText("\u4f7f\u7528\u58f0\u660e")
        self.myIndexBtn.setText("\u6253\u5f00\u6653\u6e38ChR\u7684\u4e3b\u9875")

        # self.reduceSpeedEdit.setText(str(reduceSpeed))
        # self.reduceSpeedEdit_2.setText(str(reduceSpeed_2))
        self.DefaultPathEdit.setText(defaultPath)
        self.threadNumC.addItems([str(i + 1) for i in range(2048)])
        self.GUIC.addItems(["图标型(实验性功能)", "列表型"])

        self.threadNumC.setCurrentIndex(threadNum - 1)
        self.GUIC.setCurrentIndex(GUI)
        # 连接函数
        self.DefaultPathEdit.editingFinished.connect(self.changePath)
        self.jiaQunBtn.clicked.connect(lambda: open_new_tab("https://jq.qq.com/?_wv=1027&k=Q4yTwvag"))
        self.myIndexBtn.clicked.connect(lambda: open_new_tab("https://space.bilibili.com/437313511"))
        self.decidePathBtn.clicked.connect(lambda: decidePathWin(self, self.DefaultPathEdit, True))
        self.threadNumC.currentIndexChanged.connect(self.changeThreadNum)
        # self.reduceSpeedEdit.editingFinished.connect(self.changeReduceSpeed)
        # self.reduceSpeedEdit_2.editingFinished.connect(self.changereduceSpeed_2)
        self.shengMingBtn.clicked.connect(lambda: globalSignal.message_box.emit(self.logoImg, "使用声明", ("               软件使用声明\n"
                                                                                         "本软件下载的系统仅供个人用户学习、研究使用。\n"
                                                                                         "任何用户不得将其用于任何商业用途\n"
                                                                                         "本软件下载来源\n"
                                                                                         "bilibili平台:杰克姚发布的内容(包括但不限于视频及其简介等)\n"
                                                                                         "QQ群:杰克姚の小屋(1045814906)(包括但不限于群文件和公告等)\n"
                                                                                         # "网站:www.xiaoyouchr.cn/jod\n"
                                                                                         "本声明解释权归晓游ChR所有\n"
                                                                                         "若你从以上声明的下载来源以外的途径下载了本软件，本软件制作方概不负责！")
                                                                                ))
        self.GUIC.currentIndexChanged.connect(self.changeGUI)
        self.JuanZengBtn.clicked.connect(BeggingWindow)

    # def changeReduceSpeed(self):
    #     global reduceSpeed
    #     temp = self.reduceSpeedEdit.text()
    #     try:
    #         temp = int(temp)
    #         if temp >= 0 and temp <= 100:
    #             reduceSpeed = temp
    #             changeConfig()
    #         else:
    #             self.reduceSpeedEdit.setText(str(reduceSpeed))
    #     except:
    #         self.reduceSpeedEdit.setText(str(reduceSpeed))
    #
    # def changereduceSpeed_2(self):
    #     global reduceSpeed_2
    #     temp = self.reduceSpeedEdit_2.text()
    #     try:
    #         temp = int(temp)
    #         if temp >= 0 and temp <= 10240:
    #             reduceSpeed_2 = temp
    #             changeConfig()
    #         else:
    #             self.reduceSpeedEdit_2.setText(str(reduceSpeed_2))
    #     except:
    #         self.reduceSpeedEdit_2.setText(str(reduceSpeed_2))

    def changePath(self):
        # 修改之前备份
        global defaultPath
        backup = defaultPath
        # 现在修改的
        temp = self.DefaultPathEdit.text()
        # 去除多打的斜杠
        if temp[-1] != "/" or "\\":
            temp = temp
        else:
            temp = temp[:-1]

        # 判断路径是否存在
        if path.exists(temp):
            defaultPath = temp
            self.DefaultPathEdit.setText(defaultPath)
            print(defaultPath)
            changeConfig()

        elif access(path.dirname(temp), W_OK):
            defaultPath = temp
            self.DefaultPathEdit.setText(defaultPath)
            print(defaultPath)
            changeConfig()

        else:
            MyMessageBox(
                errorIcon,
                'Error!',
                '请输入正确路径！')
            defaultPath = backup
            self.DefaultPathEdit.setText(defaultPath)
            print(defaultPath)

    def changeThreadNum(self):
        global threadNum
        temp = threadNum
        threadNum = int(self.threadNumC.currentText())
        print(threadNum)
        if temp >= 32:
            if threadNum < 32:
                warning = MyQuestionBox(
                    '警告！',
                    '你选择的线程过低！很可能会造成下载速度过慢或其他BUG！\n\n你确定要选择小于32个下载线程吗？').Question()
                if warning == QMessageBox.Yes:
                    changeConfig()
                if warning == QMessageBox.No:
                    threadNum = temp
                    self.threadNumC.setCurrentIndex(threadNum - 1)
            elif temp <= 256:
                if threadNum > 256:
                    counts = 3
                    warning = MyQuestionBox(    
                        '警告！',
                        '你选择的线程过高！把您的电脑淦爆！\n\n你确定要选择大于256个下载线程吗？').Question()
                    while warning == QMessageBox.Yes:
                        warning = MyQuestionBox(        
                            '警告！',
                            f'你选择的线程过高！可能会把您的电脑淦爆！\n\n你确定要选择大于256个下载线程吗？({counts})').Question()
                        if warning == QMessageBox.Yes:
                            counts -= 1
                            print(counts)
                        if counts == 0:
                            changeConfig()
                            break
                        if warning == QMessageBox.No:
                            break
                    if warning == QMessageBox.No:
                        threadNum = temp
                        self.threadNumC.setCurrentIndex(threadNum - 1)
            else:
                changeConfig()
        else:
            changeConfig()

    def changeGUI(self):
        global GUI
        GUI = int(self.GUIC.currentIndex())
        changeConfig()


class MyMessageBox(AcrylicWindow):
    def __init__(self, icon: QPixmap, title: str, content: str, parent=None):
        super().__init__(parent=parent, skinName=skinName)
        self.setObjectName("MyMessageBox")
        self.setMinimumSize(400, 300)
        self.resize(400, 300)
        # QSS
        with open(f"{skinName}/GlobalQSS.qss", "r", encoding="utf-8") as f:
            _ = f.read()
            self.setStyleSheet(_)
            f.close()

        self.icon = QLabel(self)
        self.icon.setObjectName(u"icon")
        self.icon.setGeometry(QRect(10, 250, 41, 41))
        self.icon.setScaledContents(True)
        self.icon.setPixmap(icon)

        self.textEdit = QTextEdit(self)
        self.textEdit.setObjectName(u"textEdit")
        self.textEdit.setGeometry(QRect(10, 30, 381, 211))
        self.textEdit.setReadOnly(True)

        self.ok = QPushButton(self)
        self.ok.setObjectName(u"ok")
        self.ok.setGeometry(QRect(310, 260, 75, 23))
        self.ok.setProperty("round", True)

        # retranslateUi
        self.setWindowTitle(title)
        self.textEdit.setText(content)
        self.ok.setText("我知道了")
        self.ok.clicked.connect(self.close)

        self.show()
        self.exec_()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Escape:
            self.close()  # 关闭程序


class MyQuestionBox(AcrylicDialog):
    def __init__(self, title: str, content: str, parent=None):
        super().__init__(parent=parent, skinName=skinName)
        self.setObjectName("MyQuestionBox")
        self.setFixedSize(400, 300)
        # QSS
        with open(f"{skinName}/GlobalQSS.qss", "r", encoding="utf-8") as f:
            _ = f.read()
            self.setStyleSheet(_)
            f.close()

        self.state = None

        self.icon = QLabel(self)
        self.icon.setObjectName(u"icon")
        self.icon.setGeometry(QRect(10, 250, 41, 41))
        self.icon.setScaledContents(True)
        self.icon.setPixmap(questionIcon)

        self.textEdit = QTextEdit(self)
        self.textEdit.setObjectName(u"textEdit")
        self.textEdit.setGeometry(QRect(10, 30, 381, 211))
        self.textEdit.setReadOnly(True)

        self.okBtn = QPushButton(self)
        self.okBtn.setObjectName(u"ok")
        self.okBtn.setGeometry(QRect(310, 260, 75, 23))
        self.okBtn.setProperty("round", True)

        self.noBtn = QPushButton(self)
        self.noBtn.setObjectName(u"no")
        self.noBtn.setGeometry(QRect(210, 260, 75, 23))
        self.noBtn.setProperty("round", True)

        # retranslateUi
        self.setWindowTitle(title)
        self.textEdit.setText(content)
        self.okBtn.setText("确定")
        self.okBtn.clicked.connect(self.ok)
        self.noBtn.setText("取消")
        self.noBtn.clicked.connect(self.no)

    def Question(self):
        self.show()
        self.exec_()

        if self.state:
            return self.state
    
    def ok(self):
        self.close()
        self.state = QMessageBox.Yes
    
    def no(self):
        self.close()
        self.state = QMessageBox.No
    
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Escape:
            self.close()  # 关闭程序


class ListGroupBox(QGroupBox):
    def __init__(self, parent, name: str, filesize, info: str, date, version, uplog: str, filename, downurl, videourl,
                 icon):
        super().__init__(parent=parent.listWidget)

        self.w = self.width()
        self.h = self.height()

        self.name = name
        self.filesize = filesize
        self.info = info
        self.date = date
        self.version = version
        self.uplog = uplog
        self.filename = filename
        self.downurl = downurl
        self.videourl = videourl
        self.icon = icon
        # 初始化展开状态
        self.opened = True
        # 初始化ComboBox选项
        self.currentIndex = 0

        self.setObjectName("ListGroupBox")
        # 临时
        self.setStyleSheet(u"QPushButton#downBtn {\n"
                           "        border-top-right-radius: 10px;\n"
                           "		border-bottom-right-radius: 10px;\n"
                           "        border: 1px solid rgb(0, 170, 255);\n"
                           "}\n"
                           "QPushButton#moreBtn {\n"
                           "        border-top-left-radius: 10px;\n"
                           "		border-bottom-left-radius: 10px;\n"
                           "        border: 1px solid rgb(0, 170, 255);\n"
                           "}\n"
                           "QPushButton[round=\"true\"] {\n"
                           "		border-radius: 10px;\n"
                           "        border: 1px solid rgb(0, 170, 255);\n"
                           "}\n"
                           "QComboBox {\n"
                           "        border-radius: 9px;\n"
                           "        border: 1px solid rgb(111, 156, 207);\n"
                           "        background: white;\n"
                           "}\n")
        # 临时

        # setUp
        self.imgLable = QLabel(self)
        self.imgLable.setScaledContents(True)
        self.imgLable.setGeometry(QRect(5, 16, 81, 81))

        self.infoEdit = QTextEdit(self)
        self.infoEdit.setGeometry(QRect(90, 20, 401, 71))
        self.infoEdit.setReadOnly(True)
        # More
        self.moreWidget = QWidget(self)
        self.moreWidget.move(505, 20)  # 初始化在下面的调用self.more()函数
        self.moreWidget.setObjectName("moreWidget")
        # 临时
        self.moreWidget.setStyleSheet(u".QWidget#moreWidget{\n"
                                      "	border:1px solid rgb(0, 170, 255);\n"
                                      "	background:white;\n"
                                      "	border-radius: 10px;\n"
                                      "}")
        # 临时

        self.dateLabel = QLabel(self.moreWidget)
        self.dateLabel.setGeometry(QRect(165, 0, 176, 21))

        self.fileSizeLabel = QLabel(self.moreWidget)
        self.fileSizeLabel.setGeometry(QRect(340, 0, 119, 20))

        self.label = QLabel(self.moreWidget)
        self.label.setGeometry(QRect(31, 1, 36, 19))
        # 功能性控件
        self.moreBtn = QPushButton(self.moreWidget)
        self.moreBtn.setObjectName("moreBtn")
        self.moreBtn.setGeometry(QRect(0, 0, 21, 21))

        self.verComboBox = QComboBox(self.moreWidget)
        self.verComboBox.setGeometry(QRect(70, 1, 90, 19))

        self.videoBtn = QPushButton(self)
        self.videoBtn.setProperty("round", True)
        self.videoBtn.setGeometry(QRect(505, 45, 61, 21))

        self.logsBtn = QPushButton(self)
        self.logsBtn.setProperty("round", True)
        self.logsBtn.setGeometry(QRect(505, 70, 61, 22))
        self.logsBtn.setEnabled(False)

        self.downBtn = QPushButton(self.moreWidget)
        self.downBtn.setObjectName("downBtn")
        self.downBtn.setGeometry(QRect(450, 0, 41, 21))
        self.downBtn.setEnabled(False)

        resizeAction(self.moreWidget, 61, 21)
        moveAction(self.downBtn, 20, 0)
        self.moreBtn.setText("◀")
        self.opened = False

        threading.Thread(target=self.setImg, daemon=True).start()  # 设置头图

        # 连接信号
        self.moreBtn.clicked.connect(self.Open)
        self.videoBtn.clicked.connect(lambda: open_new_tab(self.videourl[self.currentIndex]))
        self.verComboBox.currentIndexChanged.connect(self.changeVersion)
        self.logsBtn.clicked.connect(lambda: MyMessageBox(self.icon, f"{self.name}の更新日志", self.uplog))
        self.downBtn.clicked.connect(
            lambda: NewNetTaskWindow(f"temp/{self.name}-icon", downurl[self.currentIndex], filename[self.currentIndex],
                                     parent.parent()))
        # setText
        self.setTitle(self.name)
        self.label.setText("版本:")
        self.verComboBox.addItems(self.version)
        self.downBtn.setText("下载")
        self.videoBtn.setText("视频")
        self.logsBtn.setText("日志")
        self.infoEdit.setText(self.info)

    def Open(self):
        if self.opened == False:  # 没有展开就展开
            resizeAction(self.moreWidget, 491, 21)
            moveAction(self.moreWidget, self.w - 500, 20)
            moveAction(self.downBtn, 450, 0)
            self.moreBtn.setText("▶")
            self.opened = True

        elif self.opened == True:  # 展开了就收起
            resizeAction(self.moreWidget, 61, 21)
            moveAction(self.moreWidget, self.w - 70, 20)
            moveAction(self.downBtn, 20, 0)
            self.moreBtn.setText("◀")
            self.opened = False

    def setImg(self):

        finished = False
        while not finished:
            try:
                self.icon = requests.get(self.icon, headers=headers, proxies=proxies).content
                finished = True
            except Exception as err:
                print(err)
            time.sleep(0.15)

        with open(f'temp/{self.name}-icon', 'wb') as f:
            f.write(self.icon)
            f.close()
        self.icon = QPixmap(f'temp/{self.name}-icon')
        self.imgLable.setPixmap(self.icon)
        self.logsBtn.setEnabled(True)
        self.downBtn.setEnabled(True)

    def changeVersion(self):
        self.currentIndex = self.verComboBox.currentIndex()
        self.fileSizeLabel.setText(f"大小:{self.filesize[self.currentIndex]}")
        self.dateLabel.setText(f"更新日期:{self.date[self.currentIndex]}")

    def resizeEvent(self, event):
        self.w = self.width()
        self.h = self.height()
        super().resizeEvent(event)
        self.infoEdit.resize(self.w - 175, 71)
        self.logsBtn.move(self.w - 70, 70)
        self.videoBtn.move(self.w - 70, 45)
        if self.opened == False:
            self.moreWidget.move(self.w - 70, 20)
        elif self.opened == True:
            self.moreWidget.move(self.w - 500, 20)


class PictureGroupBox(QWidget):
    def __init__(self, parent, name: str, filesize, info: str, date, version, uplog: str, filename, downurl, videourl,
                 icon):
        super().__init__(parent=parent.listWidget)
        self.setObjectName("PictureGroupBox")
        self.resize(130, 130)
        self.setStyleSheet(""".QPushButton{border-radius: 10px;
                                       border: 1px solid rgb(100, 160, 220);
                                       background-color:rgba(255,255,255,80);}
                              .QPushButton:hover{background-color:rgba(255,255,255,60);}
                              .QPushButton:pressed{background-color:rgba(255,255,255,30);}
                              QLabel#nameLabel{font:9pt;}""")

        self.w = self.width()
        self.h = self.height()
        print(self.w, self.h)

        self.name = name
        self.filesize = filesize
        self.info = info
        self.date = date
        self.version = version
        self.uplog = uplog
        self.filename = filename
        self.downurl = downurl
        self.videourl = videourl
        self.icon = icon

        # 初始化ComboBox选项
        self.currentIndex = 0

        # setUp
        self.nameLabel = QLabel(self)
        self.nameLabel.setObjectName("nameLabel")
        self.nameLabel.move(0, 108)
        self.nameLabel.resize(130, 20)
        self.nameLabel.setWordWrap(True)
        self.nameLabel.setAlignment(Qt.AlignCenter)
        self.nameLabel.setText(self.name)

        self.imgLable = QLabel(self)
        self.imgLable.setObjectName("imgLable")
        self.imgLable.move(15, 5)
        self.imgLable.resize(100, 100)
        self.imgLable.setScaledContents(True)

        self.BGButton = QPushButton(self)
        self.BGButton.setObjectName("BGButton")
        self.BGButton.resize(self.w, self.h)

        threading.Thread(target=self.setImg, daemon=True).start()  # 设置头图

        # Connection
        self.BGButton.clicked.connect(self.Open)

    def setImg(self):
        finished = False
        while not finished:
            try:
                self.icon = requests.get(self.icon, headers=headers, proxies=proxies).content
                finished = True
            except Exception as err:
                print(err)
            time.sleep(0.15)

        with open(f'temp/{self.name}-icon', 'wb') as f:
            f.write(self.icon)
            f.close()
        self.icon = QPixmap(f'temp/{self.name}-icon')
        self.imgLable.setPixmap(self.icon)

    def Open(self):
        moveAction(self.BGButton, 3, 3)
        resizeAction(self.BGButton, self.parent().width() - 20, self.parent().height() - 100)
        moveAction(self, 0, 0)
        resizeAction(self, self.parent().width(), self.parent().height())
        print(self.width(), self.parent().width(), self.parent().height())


class Window(AcrylicWindow):
    # 自定义信号
    load_list = Signal(str)
    listNotLoaded = False
    ID = 0

    def __init__(self, parent=None):
        # 初始化
        super().__init__(skinName=skinName, parent=parent)
        self.titleBar = MainWindowTitleBar(skinName, self)

        self.setObjectName("self")

        # 建立缓存目录
        if path.exists("temp/") == False:
            makedirs("temp/")

        self.resize(600, 600)
        self.setMinimumSize(600, 600)
        self.setWindowTitle("Ghost Downloader")
        self.titleBar.raise_()

        # QSS
        with open(f"{skinName}/GlobalQSS.qss", "r", encoding="utf-8") as f:
            _ = f.read()
            self.setStyleSheet(_)
            f.close()

        self.setUp()

        # 连接信号
        self.load_list.connect(self.loadList)
        self.listBtn.clicked.connect(lambda: self.changeInterface(0))
        self.downBtn.clicked.connect(lambda: self.changeInterface(1))
        self.toolsBtn.clicked.connect(lambda: self.changeInterface(2))
        self.newDownBtn.clicked.connect(NewTaskWindow)
        self.titleBar.setBtn.clicked.connect(settingsWindow.show)

        # 读取下载历史并自动开始
        if path.exists("history.xml") == True:
            with open("history.xml", "r", encoding="utf-8") as f:
                tmp = f.read()
                f.close()
                tmp = findall(r"<hst>([\s\S]*?)</hst>", tmp)
                print(tmp)
                for i in tmp:
                    filename = findall(r"<filename>([\s\S]*)</filename>", i)
                    filename = filename[0]
                    downdir = findall(r"<downdir>([\s\S]*)</downdir>", i)
                    downdir = downdir[0]
                    downurl = findall(r"<downurl>([\s\S]*)</downurl>", i)
                    downurl = downurl[0]
                    blocks_num = findall(r"<threadnum>([\s\S]*)</threadnum>", i)
                    blocks_num = int(blocks_num[0])
                    iconpath = findall(r"<icon>([\s\S]*)</icon>", i)
                    iconpath = iconpath[0]

                    newDownloadTask(iconpath, downurl, filename, downdir, blocks_num, self, True)

    def setUp(self):
        # Logo
        self.logoImgLable = QLabel(self)
        self.logoImgLable.move(8, 8)
        self.logoImgLable.resize(26, 26)
        self.logoImgLable.setScaledContents(True)
        self.logoImg = QPixmap(f"{skinName}/logo.png")
        self.logoImgLable.setPixmap(self.logoImg)

        self.listBtn = QPushButton(self)
        self.listBtn.setObjectName(u"listBtn")
        self.listBtn.setEnabled(True)
        self.listBtn.setGeometry(QRect(121, 5, 111, 30))
        icon1 = QIcon()
        icon1.addFile(f"{skinName}/list.png", QSize(), QIcon.Normal, QIcon.Off)
        self.listBtn.setIcon(icon1)
        self.listBtn.setIconSize(QSize(24, 24))

        self.downBtn = QPushButton(self)
        self.downBtn.setObjectName(u"downBtn")
        self.downBtn.setGeometry(QRect(246, 5, 111, 30))
        icon2 = QIcon()
        icon2.addFile(f"{skinName}/down.png", QSize(), QIcon.Normal, QIcon.Off)
        self.downBtn.setIcon(icon2)
        self.downBtn.setIconSize(QSize(28, 28))

        self.toolsBtn = QPushButton(self)
        self.toolsBtn.setObjectName(u"toolsBtn")
        self.toolsBtn.setGeometry(QRect(371, 5, 111, 30))
        icon3 = QIcon()
        icon3.addFile(f"{skinName}/tools.png", QSize(), QIcon.Normal, QIcon.Off)
        self.toolsBtn.setIcon(icon3)
        self.toolsBtn.setIconSize(QSize(30, 30))

        self.btnBackground = QWidget(self)
        self.btnBackground.setObjectName(u"btnBackground")
        self.btnBackground.setGeometry(QRect(121, 5, 111, 31))

        self.verLable = QLabel(self)
        self.verLable.setObjectName(u"verLable")
        self.verLable.setGeometry(QRect(550, 30, 51, 10))

        self.newDownBtn = QPushButton(self)
        self.newDownBtn.setObjectName(u"newDownBtn")
        self.newDownBtn.setGeometry(QRect(285, -30, 30, 30))
        icon4 = QIcon()
        icon4.addFile(f"{skinName}/new.png", QSize(), QIcon.Normal, QIcon.Off)
        self.newDownBtn.setIcon(icon4)
        self.newDownBtn.setIconSize(QSize(18, 18))

        self.btnBackground.raise_()
        self.logoImgLable.raise_()
        self.listBtn.raise_()
        self.downBtn.raise_()
        self.toolsBtn.raise_()
        self.verLable.raise_()
        self.newDownBtn.raise_()

        # mainWidget
        self.main = QWidget(self)
        self.main.setMouseTracking(True)  # 否则只有左键时才能获取鼠标坐标
        self.main.setObjectName(u"main")
        self.main.setGeometry(QRect(0, 40, 1800, 560))

        with open(f"{skinName}/MainQSS.qss", "r", encoding="utf-8") as f:
            self.main.setStyleSheet(f.read())
            f.close()

        self.horizontalLayout = QHBoxLayout(self.main)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        # listArea
        self.listArea = QScrollArea(self.main)
        self.listArea.setMouseTracking(True)  # 否则只有左键时才能获取鼠标坐标
        self.listArea.setObjectName(u"listArea")
        self.listArea.setFrameShape(QFrame.NoFrame)
        self.listArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.listWidget = QWidget()
        self.listWidget.setMouseTracking(True)  # 否则只有左键时才能获取鼠标坐标
        self.listWidget.setObjectName(u"listWidget")
        self.listWidget.setGeometry(QRect(0, 0, 600, 500))

        self.listArea.setWidget(self.listWidget)
        self.horizontalLayout.addWidget(self.listArea)

        # downArea
        self.downArea = QScrollArea(self.main)
        self.downArea.setMouseTracking(True)  # 否则只有左键时才能获取鼠标坐标
        self.downArea.setObjectName(u"downArea")
        self.downArea.setFrameShape(QFrame.NoFrame)
        self.downArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.downWidget = QWidget()
        self.downWidget.setMouseTracking(True)  # 否则只有左键时才能获取鼠标坐标
        self.downWidget.setObjectName(u"downWidget")
        self.downWidget.setGeometry(QRect(0, 0, 600, 100))

        # 临时
        self.downWidget.setStyleSheet(u"QGroupBox {\n"
                                      "        font-size: 15px;\n"
                                      "        border: 1px solid rgb(100, 160, 220);\n"
                                      "        border-radius: 10px;\n"
                                      "        margin-top: 0px;\n"
                                      "}\n"
                                      "QPushButton#downimg {\n"
                                      "	border: none;\n"
                                      "	background-color: none\n"
                                      "}\n"
                                      "QPushButton {\n"
                                      "	border-radius: 10px;\n"
                                      " border: 1px solid rgb(0, 170, 255);\n"
                                      "}\n"
                                      "QPushButton:enabled {\n"
                                      "        background: rgb(120, 170, 220);\n"
                                      "        color: white;\n"
                                      "}\n"
                                      "QPushButton:!enabled {\n"
                                      "        background: rgb(180, 180, 180);\n"
                                      "        color: white;\n"
                                      "}\n"
                                      "QPushButton:enabled:hover{\n"
                                      "        background: rgb(100, 160, 220);\n"
                                      "}\n"
                                      "QPushButton:enabled:pressed{\n"
                                      "        background: rgb(0, 78, 161);"
                                      "}\n")
        # 临时

        self.downArea.setWidget(self.downWidget)
        self.horizontalLayout.addWidget(self.downArea)

        # toolsArea
        self.toolsArea = QScrollArea(self.main)
        self.toolsArea.setMouseTracking(True)  # 否则只有左键时才能获取鼠标坐标
        self.toolsArea.setObjectName(u"toolsArea")
        self.toolsArea.setFrameShape(QFrame.NoFrame)
        self.toolsArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.toolsWidget = QWidget()
        self.toolsWidget.setMouseTracking(True)  # 否则只有左键时才能获取鼠标坐标
        self.toolsWidget.setObjectName(u"toolsWidget")
        self.toolsWidget.setGeometry(QRect(0, 0, 600, 540))

        self.toolsArea.setWidget(self.toolsWidget)
        self.horizontalLayout.addWidget(self.toolsArea)

        # 文本
        self.listBtn.setText("推荐资源")
        self.downBtn.setText("任务列表")
        self.toolsBtn.setText("实用工具")
        self.verLable.setText("2.0.2(22.12.27)")

        self.listNotLoaded = False
        # 加载GIF
        self.loadingGifLable = QLabel(self.listWidget)
        self.loadingGifLable.move(273, 240)
        self.loadingGifLable.resize(50, 50)
        self.loadingGifLable.setScaledContents(True)
        self.loadingGif = QMovie(f"{skinName}/loading.gif")
        self.loadingGifLable.setMovie(self.loadingGif)
        self.loadingGif.start()
        self.loadingGifLable.show()

        def getWebsiteContent():
            try:
                content = requests.get("https://seelevollerei-my.sharepoint.com/personal/xiaoyouchr_xn--7et36u_cn/_layouts/52/download.aspx?share=ESV4o6MmGP9Ev9P71xrRl_cByYwqhqfNmljPF0xKAdMFXg", headers=headers,
                                       proxies=proxies, verify=False)
                # with open("./Content_Local.txt", "r", encoding="utf-8") as f:
                #     content = f.read()
                #     f.close()

                content.encoding = "utf-8"
                content = content.text
                self.load_list.emit(content)
            except requests.exceptions.ConnectionError as err:
                print(err)
                globalSignal.message_box.emit(errorIcon, "网络连接失败！", f"请尝试关闭代理！\n{err}")
                self.listNotLoaded = True
            except ValueError as err:
                print(err)
                globalSignal.message_box.emit(errorIcon, "网络连接失败！", f"请检查网络连接！\n{err}")
                self.listNotLoaded = True
            except Exception as err:
                print(err)
                globalSignal.message_box.emit(errorIcon, "未知错误!", f"请联系开发者,E-mail:XiaoYouChR@outlook.com！\n{err}")
                self.listNotLoaded = True

        threading.Thread(target=getWebsiteContent, daemon=True).start()

    def changeInterface(self, ID):
        self.ID = ID
        if ID == 0 and self.listNotLoaded == True:  # 判断是否加载了推荐资源列表
            self.listNotLoaded = False
            # 加载GIF
            self.loadingGifLable = QLabel(self.listWidget)
            self.loadingGifLable.move(273, 240)
            self.loadingGifLable.resize(50, 50)
            self.loadingGifLable.setScaledContents(True)
            self.loadingGif = QMovie(f"{skinName}/loading.gif")
            self.loadingGifLable.setMovie(self.loadingGif)
            self.loadingGif.start()
            self.loadingGifLable.show()

            def getWebsiteContent():
                try:
                    content = requests.get(
                        "https://seelevollerei-my.sharepoint.com/personal/xiaoyouchr_xn--7et36u_cn/_layouts/52/download.aspx?share=ESV4o6MmGP9Ev9P71xrRl_cByYwqhqfNmljPF0xKAdMFXg",
                        headers=headers,
                        proxies=proxies, verify=False)
                    # with open("./Content_Local.txt", "r", encoding="utf-8") as f:
                    #     content = f.read()
                    #     f.close()

                    content.encoding = "utf-8"
                    content = content.text
                    self.load_list.emit(content)
                except requests.exceptions.ConnectionError as err:
                    MyMessageBox(errorIcon, "网络连接失败！", f"请尝试关闭代理！\n{err}")
                    self.listNotLoaded = True
                except ValueError as err:
                    MyMessageBox(errorIcon, "网络连接失败！", f"请检查网络连接！\n{err}")
                    self.listNotLoaded = True
                except Exception as err:
                    MyMessageBox(errorIcon, "未知错误!", f"请联系开发者,E-mail:XiaoYouChR@outlook.com！\n{err}")
                    self.listNotLoaded = True

            threading.Thread(target=getWebsiteContent, daemon=True).start()

        if ID == 1:
            moveAction(self.btnBackground, self.half_w - 15, self.downBtn.y())
            resizeAction(self.btnBackground, 31, 31)
            moveAction(self.downBtn, self.downBtn.x(), -30)
            moveAction(self.newDownBtn, self.newDownBtn.x(), 5)
        else:
            if ID == 0:
                moveAction(self.btnBackground, self.half_w / 2 - 30, 5)
            elif ID == 2:
                moveAction(self.btnBackground, self.half_w + self.half_w / 2 - 80, 5)
            else:
                sys.exit()  # 经典改内存?
            resizeAction(self.btnBackground, 108, 31)
            moveAction(self.newDownBtn, self.newDownBtn.x(), -30)
            moveAction(self.downBtn, self.downBtn.x(), 5)

        moveAction(self.main, -ID * self.w, 40)

    def loadList(self, content: str):
        global listGroupBoxesList

        content = findall(r"<tab>([\s\S]*?)</tab>", content)
        # 初始化
        self.len = len(content)
        listGroupBoxesList = [0] * self.len

        # 设置listWidget大小
        if GUI:  # 列表型
            self.listWidget.resize(600, self.len * 105 + 5)
        elif not GUI:  # 图案型
            self.listWidget.resize(600, self.len * 105 + 5)

        for i in range(self.len):
            temp = content[i]

            name = findall(r'<name>([\s\S]*)</name>', temp)
            name = name[0]

            filesize = findall(r'<filesize>([\s\S]*)</filesize>', temp)
            filesize = filesize[0]
            filesize = findall(r'\|?([\s\S]*?)\|', filesize)

            info = findall(r'<info>([\s\S]*)</info>', temp)
            info = info[0]
            info = info.replace(r"\n", "\n")

            date = findall(r'<date>([\s\S]*)</date>', temp)
            date = date[0]
            date = findall(r'\|?([\s\S]*?)\|', date)

            version = findall(r'<version>([\s\S]*)</version>', temp)
            version = version[0]
            version = findall(r'\|?([\s\S]*?)\|', version)

            uplog = findall(r'<uplog>([\s\S]*)</uplog>', temp)
            uplog = uplog[0]
            uplog = uplog.replace(r"\n", "\n")

            filename = findall(r'<filename>([\s\S]*)</filename>', temp)
            filename = filename[0]
            filename = findall(r'\|?([\s\S]*?)\|', filename)

            downurl = findall(r'<downurl>([\s\S]*)</downurl>', temp)
            downurl = downurl[0]
            downurl = findall(r'\|?([\s\S]*?)\|', downurl)

            videourl = findall(r'<videourl>([\s\S]*)</videourl>', temp)
            videourl = videourl[0]
            videourl = findall(r'\|?([\s\S]*?)\|', videourl)

            icon = findall(r'<icon>([\s\S]*)</icon>', temp)
            icon = icon[0]
            if GUI:  # 列表型
                listGroupBoxesList[i] = ListGroupBox(self, name, filesize, info, date, version, uplog, filename,
                                                     downurl, videourl, icon)
                listGroupBoxesList[i].resize(self.w - 25, 100)
                # Action
                listGroupBoxesList[i].move(-600, i * 105 + 5)
                moveAction(listGroupBoxesList[i], 5, i * 105 + 5)

                listGroupBoxesList[i].show()
            if not GUI:  # 图标型
                listGroupBoxesList[i] = PictureGroupBox(self, name, filesize, info, date, version, uplog,
                                                        filename, downurl, videourl, icon)
                listGroupBoxesList[i].resize(130, 130)
                listGroupBoxesList[i].move(10, i * 150 + 10)
                listGroupBoxesList[i].show()

        self.loadingGifLable.close()
    # 自适应
    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.w = self.width()
        self.half_w = self.w / 2
        self.h = self.height()
        print(self.w, self.h)
        self.titleBar.resize(self.w, 28)
        self.main.move(-self.ID * self.w, 40)
        self.main.resize(self.w * 3, self.h - 40)
        self.listWidget.resize(self.w, self.listWidget.height())
        self.downWidget.resize(self.w, self.downWidget.height())
        self.toolsWidget.resize(self.w, self.toolsWidget.height())
        self.verLable.move(self.w - 50, 30)
        self.listBtn.move(self.half_w / 2 - 30, 5)
        self.downBtn.move(self.half_w - 55, self.downBtn.y())
        self.newDownBtn.move(self.half_w - 15, self.newDownBtn.y())
        self.toolsBtn.move(self.half_w + self.half_w / 2 - 80, 5)
        if self.ID == 0:
            self.btnBackground.move(self.half_w / 2 - 30, 5)
        elif self.ID == 1:
            self.btnBackground.move(self.half_w - 15, 5)
        elif self.ID == 2:
            self.btnBackground.move(self.half_w + self.half_w / 2 - 80, 5)
        else:
            sys.exit()  # 改内存了吧???

        if GUI:
            for i in listGroupBoxesList:
                i.resize(self.w - 25, 100)
        elif GUI:
            pass

        for i in DownGroupBoxesList:
            i.resize(self.w - 25, 73)

    def closeEvent(self, e):
        question = MyQuestionBox("您在尝试退出哦！", "您真的要退出吗？").Question()
        print(question)
        if question == QMessageBox.Yes:
            super().closeEvent(e)
        else:
            e.ignore()


if __name__ == '__main__':
    freeze_support()
    # 忽略 https 警告
    ssl._create_default_https_context = ssl._create_unverified_context
    requests.packages.urllib3.disable_warnings()

    # 创建application
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)

    # 检测程序是否重复运行
    lockFile = QLockFile("./lock.lck")
    if not lockFile.tryLock(2000):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("提示")
        msg_box.setText("Ghost Downloader 2 已在运行!")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.addButton("确定", QMessageBox.YesRole)
        msg_box.exec()
        sys.exit(-1)

    # 创建/读取 配置文件
    if path.exists("config.cfg") == True:
        try:
            with open("config.cfg", "r", encoding="utf-8") as f:
                _ = []  # 生成空表格

                for line in f.readlines():
                    line = line.strip('\n')  # 去掉列表中每一个元素的换行符
                    _.append(line)

                threadNum = int(_[0])
                print(threadNum)
                defaultPath = _[1]
                print(defaultPath)
                skinName = _[2]
                print(skinName)
                reduceSpeed = int(_[3])
                print(reduceSpeed)
                reduceSpeed_2 = int(_[4])
                print(reduceSpeed_2)
                GUI = int(_[5])
                print(GUI)
                f.close()
        except:
            f.close()
            with open("config.cfg", "w", encoding="utf-8") as f:
                f.write("32\n%s\nskins/Default\n50\n200\n1" % getcwd().replace("\\", "/"))
                f.close()
            with open("config.cfg", "r", encoding="utf-8") as f:
                _ = []  # 生成空表格

                for line in f.readlines():
                    line = line.strip('\n')  # 去掉列表中每一个元素的换行符
                    _.append(line)

                threadNum = int(_[0])
                print(threadNum)
                defaultPath = _[1]
                print(defaultPath)
                skinName = _[2]
                print(skinName)
                reduceSpeed = _[3]
                print(reduceSpeed)
                reduceSpeed_2 = _[4]
                print(reduceSpeed_2)
                GUI = int(_[5])
                print(GUI)
                f.close()
    else:
        with open("config.cfg", "w", encoding="utf-8") as f:
            f.write("32\n%s\nskins/Default\n50\n200\n1" % getcwd().replace("\\", "/"))
            f.close()
        with open("config.cfg", "r", encoding="utf-8") as f:
            _ = []  # 生成空表格

            for line in f.readlines():
                line = line.strip('\n')  # 去掉列表中每一个元素的换行符
                _.append(line)

            threadNum = int(_[0])
            print(threadNum)
            defaultPath = _[1]
            print(defaultPath)
            skinName = _[2]
            print(skinName)
            reduceSpeed = _[3]
            print(reduceSpeed)
            reduceSpeed_2 = _[4]
            print(reduceSpeed_2)
            GUI = int(_[5])
            print(GUI)
            f.close()

    logoIcon = QIcon()
    logoIcon.addFile(f"{skinName}/logo.png", QSize(), QIcon.Normal, QIcon.Off)
    app.setWindowIcon(logoIcon)

    errorIcon = QPixmap(f"{skinName}/error.png")

    questionIcon = QPixmap(f"{skinName}/question.png")

    Version = 200
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36 Edg/93.0.961.44"
    }
    listGroupBoxesList = []
    DownGroupBoxesList = []
    urlRe = compile(r"^" +
                    "((?:https?|ftp)://)" +
                    "(?:\\S+(?::\\S*)?@)?" +
                    "(?:" +
                    "(?:[1-9]\\d?|1\\d\\d|2[01]\\d|22[0-3])" +
                    "(?:\\.(?:1?\\d{1,2}|2[0-4]\\d|25[0-5])){2}" +
                    "(\\.(?:[1-9]\\d?|1\\d\\d|2[0-4]\\d|25[0-4]))" +
                    "|" +
                    "((?:[a-z\\u00a1-\\uffff0-9]-*)*[a-z\\u00a1-\\uffff0-9]+)" +
                    '(?:\\.(?:[a-z\\u00a1-\\uffff0-9]-*)*[a-z\\u00a1-\\uffff0-9]+)*' +
                    "(\\.([a-z\\u00a1-\\uffff]{2,}))" +
                    ")" +
                    "(?::\\d{2,5})?" +
                    "(?:/\\S*)?" +
                    "$", IGNORECASE)

    # 代理
    proxiesIP = CheckProxyServer().get_server_form_Win()
    print(proxiesIP)
    if proxiesIP:
        proxies = {
            "http": proxiesIP,
            "https": proxiesIP,
        }
    else:
        proxies = {
            "http": None,
            "https": None,
        }

    # 托盘
    systemTray = QSystemTrayIcon()  # 创建托盘
    systemTray.setIcon(logoIcon)  # 设置托盘图标
    systemTray.setToolTip(u'Ghost Downloader 2')
    systemTray.show()

    # 初始化设置窗口
    settingsWindow = SettingsWindow()

    window = Window()
    window.show()

    sys.exit(app.exec_())
