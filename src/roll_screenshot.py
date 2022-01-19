import os
import time
import json
import math
import operator
from functools import reduce
from PIL import ImageGrab, Image
from pynput import keyboard
from pynput.mouse import Controller as MouseController
from pynput.mouse import Listener as MouseListener

in_rolling = True
start_key = False


def compare(p1, p2):    # 相似度检测
    img1 = Image.open(p1)
    img2 = Image.open(p2)
    h1 = img1.histogram()
    h2 = img2.histogram()
    result = math.sqrt(reduce(operator.add, list(map(lambda a, b: (a - b) ** 2, h1, h2))) / len(h1))
    if result < 5:
        return False
    else:
        return True


def roll(area):
    controller = MouseController()  # 鼠标控制器
    counter = 0

    def on_click(x, y, button, pressed):
        global in_rolling
        if pressed and button.name == 'left':
            print('[Roll Screenshot]检测到左键单击，停止滚动截图')
            in_rolling = False
            listener.stop()
            return in_rolling
        else:
            return in_rolling

    # 监听事件绑定
    with MouseListener(on_click=on_click) as listener:
        while True:
            if in_rolling:
                counter += 1
                path = 'screenshots/%d.png'
                img = ImageGrab.grab(area)
                # 参数 保存截图文件的路径
                img.save(path % counter)
                if counter > 1:
                    if not compare(path % (counter - 1), path % counter):
                        os.remove(path % counter)
                        print('[Roll Screenshot]图片重复，停止滚动截图')
                        break
                print('[Roll Screenshot] [%d]截图成功，保存至/%s' % (counter, path % counter))
                for i in range(5):  # 测试1366x768分辨率下约滚动50次翻一页（指原神成就页）
                    if not in_rolling:
                        break
                    controller.scroll(dx=0, dy=-3)  # 控制鼠标滚动
                    time.sleep(1)  # 通过sleep控制自动滚动速度

            else:
                break


def main():
    print('[Roll Screenshot]按下Alt开始滚动截图')
    with open('config.json', 'r', encoding='utf-8') as r:
        config = json.load(r)
        area = config['area']

    def on_release(key):
        try:
            temp = ('release key {0}, vk: {1}'.format(key.char, key.vk))
        except AttributeError:
            if key.value.vk == 164 or key.value.vk == 165:
                print('[Roll Screenshot]检测到按下Alt键，开始滚动截屏')
                roll(area)
                listener.stop()

    # 键盘监听
    with keyboard.Listener(on_release=on_release) as listener:
        listener.join()
