import math
import operator
import os
import sys
import time
from functools import reduce
import cv2
from PIL import Image
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSettings, QObject, QThread
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont
from PyQt5.QtWidgets import QApplication, QLabel
from numpy import zeros, uint8, asarray, vstack
from pynput import mouse
from pynput.mouse import Controller as MouseController
from pynput.mouse import Listener as MouseListenner

if not os.path.exists("screenshots"):
    os.mkdir("screenshots")


class Commen_Thread(QThread):
    def __init__(self, action, *args):
        super(QThread, self).__init__()
        self.action = action
        self.args = args

    def run(self):
        print('start_thread', self.args)
        if self.args:
            print(self.args)
            if len(self.args) == 1:
                self.action(self.args[0])
            elif len(self.args) == 2:
                self.action(self.args[0], self.args[1])
            elif len(self.args) == 3:
                self.action(self.args[0], self.args[1], self.args[2])
            elif len(self.args) == 4:
                self.action(self.args[0], self.args[1], self.args[2], self.args[3])
        else:
            self.action()


class TipsShower(QLabel):
    def __init__(self, text, targetarea=(0, 0, 0, 0), parent=None, fontsize=35, timeout=1000):
        super().__init__(parent)
        self.parent = parent
        self.area = targetarea
        self.timeout = timeout
        self.rfont = QFont('', fontsize)
        self.setFont(self.rfont)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide)
        self.setText(text)

        self.show()

        self.setStyleSheet("color:black")

    def setText(self, text, autoclose=True, font: QFont = None, color: QColor = None) -> None:
        super(TipsShower, self).setText(text)
        print("settext")
        self.adjustSize()
        x, y, w, h = self.area
        if x < QApplication.desktop().width() - x - w:
            self.move(x + w + 5, y)
        else:
            self.move(x - self.width() - 5, y)
        self.show()
        if autoclose:
            self.timer.start(self.timeout)
        if font is not None:
            print("更换字体")
            self.setFont(font)
        if font is not None:
            self.setStyleSheet("color:{}".format(color.name()))

    def hide(self) -> None:
        super(TipsShower, self).hide()
        self.timer.stop()
        self.setFont(self.rfont)
        self.setStyleSheet("color:white")

    def textAreaChanged(self, minsize=0):
        self.document.adjustSize()
        newWidth = self.document.size().width() + 25
        newHeight = self.document.size().height() + 15
        if newWidth != self.width():
            if newWidth < minsize:
                self.setFixedWidth(minsize)
            else:
                self.setFixedWidth(newWidth)
        if newHeight != self.height():
            if newHeight < minsize:
                self.setFixedHeight(minsize)
            else:
                self.setFixedHeight(newHeight)


class PicMatcher:  # 图像匹配类
    def __init__(self, nfeatures=500, draw=False):
        self.SIFT = cv2.xfeatures2d_SIFT.create(nfeatures=nfeatures)  # 生成sift算子
        self.bf = cv2.BFMatcher()  # 生成图像匹配器
        self.draw = draw

    def match(self, im1, im2):  # 图像匹配函数,获得图像匹配的点以及匹配程度
        print("start match")
        # 提取特征并计算描述子
        kps1, des1 = self.SIFT.detectAndCompute(im1, None)
        kps2, des2 = self.SIFT.detectAndCompute(im2, None)

        matches = self.bf.knnMatch(des1, des2, k=2)
        good = []
        tempgoods = []
        distances = {}  # 储存距离计数的数组
        for m, n in matches:
            if m.distance == 0:
                pos0 = kps1[m.queryIdx].pt
                pos1 = kps2[m.trainIdx].pt
                if pos1[0] == pos0[0] and pos0[1] > pos1[1]:  # 筛选拼接点
                    d = int(pos0[1] - pos1[1])
                    if d in distances:
                        distances[d] += 1
                    else:
                        distances[d] = 0
                    tempgoods.append(m)
        sorteddistance = sorted(distances.items(), key=lambda kv: kv[1], reverse=True)
        max1y = 0
        max2y = 0
        try:
            distancesmode = sorteddistance[0][0]
            if sorteddistance[0][1] < 0:  # 4为特征点数,当大于4时才认为特征明显
                print("rt 0 0 0")
                return 0, 0, 0
        except:  # 一般捕获的是完全没有匹配的情况即distances为空
            print(sys.exc_info(), 113)
            return 0, 0, 0
        for match in tempgoods:
            pos0 = kps1[match.queryIdx].pt
            pos1 = kps2[match.trainIdx].pt
            if int(pos0[1] - pos1[1]) == distancesmode:
                if pos0[1] > max1y:
                    max1y = pos0[1]
                if pos1[1] > max2y:
                    max2y = pos1[1]
                good.append(match)
        print(len(good), distances, max1y, max2y)
        if self.draw:
            self.paint(im1, im2, kps1, kps2, good)
        return distancesmode, max1y, max2y

    def paint(self, im1, im2, kps1, kps2, good):
        img3 = cv2.drawMatches(im1, kps1, im2, kps2, good, None, flags=2)
        # 新建一个空图像用于绘制特征点
        img_sift1 = zeros(im1.shape, uint8)
        img_sift2 = zeros(im2.shape, uint8)
        # 绘制特征点
        cv2.drawKeypoints(im1, kps1, img_sift1)
        cv2.drawKeypoints(im2, kps2, img_sift2)
        cv2.imwrite("screenshots/match{}.png".format(time.time()), img3)
        print("write a frame")


class Splicing_shots(QObject):  # 滚动截屏主类
    showm_signal = pyqtSignal(str)
    statusBar_signal = pyqtSignal(str)

    def __init__(self, parent: QLabel = None, draw=False):
        super(Splicing_shots, self).__init__()
        self.parent = parent
        self.clear_timer = QTimer()  # 后台清理器,暂时不用
        self.clear_timer.timeout.connect(self.setup)
        self.settings = QSettings('Fandes', 'jamtools')
        self.picMatcher = PicMatcher(nfeatures=self.settings.value('screenshot/roll_nfeatures', 500, type=int),
                                     draw=draw)
        self.init_splicing_shots()

    def init_splicing_shots(self):
        self.finalimg = None
        self.img_list = []
        self.roll_speed = self.settings.value('screenshot/roll_speed', 3, type=int)
        self.in_rolling = False

    def setup(self):
        if self.clear_timer.isActive():
            self.clear_timer.stop()
            print('clear')
        self.finalimg = None
        self.img_list = []
        self.roll_speed = self.settings.value('screenshot/roll_speed', 3, type=int)
        self.in_rolling = False

    def is_same(self, img1, img2):  # 判断两张图片的相似度,用于判断结束条件
        h1 = img1.histogram()
        h2 = img2.histogram()
        result = math.sqrt(reduce(operator.add, list(map(lambda a, b: (a - b) ** 2, h1, h2))) / len(h1))
        if result <= 5:
            return True
        else:
            return False

    def match_and_merge(self):  # 图像寻找拼接点并拼接的主函数,运行于后台线程,从self.img_list中取数据进行拼接
        same = 0
        while not len(self.img_list):  # 首次运行时进行判断是否开始收到数据
            time.sleep(0.1)
        try:
            self.finalimg = self.img_list.pop(0)
            compare_img1 = cv2.cvtColor(self.finalimg, cv2.COLOR_RGB2GRAY)
        except:
            print("线程启动过早", sys.exc_info())
            return
        while self.in_rolling or len(self.img_list):  # 如果正在滚动或者self.img_list有图片没有被拼接
            if len(self.img_list):  # 如果有图片
                rgbimg2 = self.img_list.pop(0)  # 取出图片
                compare_img2 = cv2.cvtColor(rgbimg2, cv2.COLOR_RGB2GRAY)  # 预处理
                distance, m1, m2 = self.picMatcher.match(compare_img1, compare_img2)  # 调用picMatcher的match方法获取拼接匹配信息
                if distance == 0:
                    print("重复!", same)
                    same += 1
                    if same >= 3:
                        print("roller same break")
                        break
                    continue
                else:
                    same = 0
                finalheightforcutting = self.finalimg.shape[0]
                imgheight = rgbimg2.shape[0]
                finalheightforcutting -= imgheight - int(m1)  # 拼接图片的裁剪高度
                i1 = self.finalimg[:finalheightforcutting, :, :]
                i2 = rgbimg2[int(m2):, :, :]
                self.finalimg = vstack((i1, i2))
                compare_img1 = compare_img2
                print("sucesmerge a img")
            else:  # 等待图片到来
                time.sleep(0.05)  # 后台线程没有收到图片时,睡眠一下避免占用过高
        self.in_rolling = False
        print("end merge")
        cv2.imwrite("screenshots/jam_outputfile.png", self.finalimg)
        print("长图片保存到screenshots/jam_outputfile.png")
        exit(0)

    def auto_roll(self, area):  # 自动滚动模式
        x, y, w, h = area
        self.rollermask.tips.setText("单击停止")
        QApplication.processEvents()
        speed = round(1 / self.roll_speed, 2)
        screen = QApplication.primaryScreen()
        winid = QApplication.desktop().winId()

        def onclick(x, y, button, pressed):  # 点击退出的函数句柄
            if pressed:
                print("click to stop")
                self.in_rolling = False
                listener.stop()

        controler = MouseController()  # 鼠标控制器
        listener = MouseListenner(on_click=onclick)  # 鼠标监听器
        self.match_thread = Commen_Thread(self.match_and_merge)  # 把match_and_merge放入一个线程中
        self.in_rolling = True
        i = 0
        controler.position = (area[0] + int(area[2] / 2), area[1] + int(area[3] / 2))  # 控制鼠标点击到滚动区域中心
        oldimg = Image.new("RGB", (128, 128), "#FF0f00")
        listener.start()
        while self.in_rolling:
            st = time.time()
            pix = screen.grabWindow(winid, x, y, w, h)  # 截屏
            newimg = Image.fromqpixmap(pix)  # 转化为pil的格式
            img = cv2.cvtColor(asarray(newimg), cv2.COLOR_RGB2BGR)
            self.img_list.append(img)  # 图片数据存入self.img_list中被后台的拼接线程使用
            if i >= 1:
                if i == 1:
                    self.match_thread.start()  # 当截第二张图片时拼接线程才启动
                if self.is_same(oldimg, newimg):  # 每帧检查是否停止
                    self.in_rolling = False
                    i += 1
                    break
            oldimg = newimg
            controler.scroll(dx=0, dy=-3)  # 控制鼠标滚动
            time.sleep(speed)  # 通过sleep控制自动滚动速度
            i += 1
        print("结束滚动,共截屏{}张".format(i))
        listener.stop()
        self.match_thread.wait()

    def inthearea(self, pos, area):  # 点在区域中
        if area[0] < pos[0] < area[0] + area[2] and area[1] < pos[1] < area[1] + area[3]:
            return True
        else:
            return False

    def scroll_to_roll(self, area):  # 手动滚动模式
        x, y, w, h = area
        self.rollermask.tips.setText("向下滚动,单击结束")
        QApplication.processEvents()
        screen = QApplication.primaryScreen()
        winid = QApplication.desktop().winId()
        self.id = self.rid = 0
        self.a_step = 0

        def onclick(x, y, button, pressed):
            if pressed:
                pix = screen.grabWindow(winid, x, y, w, h)
                newimg = Image.fromqpixmap(pix)
                img = cv2.cvtColor(asarray(newimg), cv2.COLOR_RGB2BGR)
                self.img_list.append(img)
            else:
                print("click to stop", len(self.img_list))
                self.in_rolling = False
                listener.stop()

        def on_scroll(px, py, x_axis, y_axis):
            self.a_step += 1
            if self.a_step < 2:
                return
            else:
                self.a_step = 0
            if y_axis < 0:
                if self.rid >= self.id:  # 当滚动id与真实id一样时说明
                    pix = screen.grabWindow(winid, x, y, w, h)  # 滚动段距离进行截屏
                    newimg = Image.fromqpixmap(pix)
                    img = cv2.cvtColor(asarray(newimg), cv2.COLOR_RGB2BGR)
                    self.img_list.append(img)
                    self.id += 1  # 记录当前滚动的id
                    self.rid = self.id
                else:  # 不一样时说明用户往回滚了,跳过
                    print("跳过")
                    self.rid += 1
            else:  # 方向往回滚时id-1,以记录往回的步数
                self.rid -= 1
                print("方向错误")

        listener = MouseListenner(on_click=onclick, on_scroll=on_scroll)  # 鼠标监听器,传入函数句柄
        self.match_thread = Commen_Thread(self.match_and_merge)  # 也是把拼接函数放入后台线程中
        self.in_rolling = True
        i = 0
        listener.start()  # 鼠标监听器启动
        self.match_thread.start()  # 拼接线程启动
        while self.in_rolling:  # 等待结束滚动
            time.sleep(0.2)
        listener.stop()
        self.match_thread.wait()  # 等待拼接线程结束

    def roll_manager(self, area):  # 滚动截屏控制器,控制滚动截屏的模式(自动还是手动滚)
        x, y, w, h = area
        self.mode = 1

        def on_click(x, y, button, pressed):  # 用户点击了屏幕说明用户想自动滚
            print(x, y, button)
            if button == mouse.Button.left:
                if area[0] < x < area[0] + area[2] and area[1] < y < area[1] + area[3] and not pressed:
                    self.mode = 1
                    lis.stop()
            elif button == mouse.Button.right:
                self.mode = 2
                lis.stop()

        def on_scroll(x, y, button, pressed):  # 用户滚动了鼠标说明用户想要手动滚
            self.mode = 0
            lis.stop()
        self.rollermask = roller_mask(area)  # 滚动截屏遮罩层初始化
        pix = QApplication.primaryScreen().grabWindow(QApplication.desktop().winId(), x, y, w, h)  # 先截一张图片
        newimg = Image.fromqpixmap(pix)
        img = cv2.cvtColor(asarray(newimg), cv2.COLOR_RGB2BGR)
        self.img_list.append(img)
        QApplication.processEvents()
        lis = MouseListenner(on_click=on_click, on_scroll=on_scroll)  # 鼠标监听器初始化并启动
        lis.start()
        print("等待用户开始")
        lis.join()
        lis.stop()
        if self.mode == 1:  # 判断用户选择的模式
            print("auto_roll")
            self.auto_roll(area)
        elif self.mode == 2:
            print("exit roller")
            # return 1
            exit(0)
        else:
            print("scroll_to_roll")
            self.scroll_to_roll(area)
        self.showm_signal.emit("长截图完成")
        self.rollermask.hide()
        return 0


class roller_mask(QLabel):  # 滚动截屏遮罩层
    def __init__(self, area):
        super(roller_mask, self).__init__()
        transparentpix = QPixmap(QApplication.desktop().size())
        transparentpix.fill(Qt.transparent)
        self.area = area
        self.tips = TipsShower("单击自动滚动;\n或手动下滚;", area)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setPixmap(transparentpix)
        self.showFullScreen()

    def settext(self, text: str, autoclose=True):  # 设置提示文字
        self.tips.setText(text, autoclose)

    def paintEvent(self, e):  # 绘制遮罩层
        super().paintEvent(e)
        x, y, w, h = self.area
        painter = QPainter(self)
        painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        painter.drawRect(x - 1, y - 1, w + 2, h + 2)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 120))
        painter.drawRect(0, 0, x, self.height())
        painter.drawRect(x, 0, self.width() - x, y)
        painter.drawRect(x + w, y, self.width() - x - w, self.height() - y)
        painter.drawRect(x, y + h, w, self.height() - y - h)
        painter.end()


def main(area):
    app = QApplication(sys.argv)
    s = Splicing_shots()
    s.roll_manager(tuple(area))
    sys.exit(app.exec_())