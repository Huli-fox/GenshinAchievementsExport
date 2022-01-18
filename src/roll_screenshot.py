import time
import json
from PIL import ImageGrab
from pynput import keyboard
from pynput.mouse import Controller as MouseController
from pynput.mouse import Listener as MouseListener

with open('./config.json', 'r', encoding='utf-8') as r:
    config = json.load(r)
    area = config['area']
in_rolling = True
start_key = False


def roll():
    controller = MouseController()  # 鼠标控制器
    counter = 0

    def on_click(x, y, button, pressed):
        global in_rolling
        if pressed and button.name == 'left':
            print('[STOP]检测到左键单击，停止滚动截屏')
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
                img = ImageGrab.grab(area)
                # 参数 保存截图文件的路径
                img.save('./screenshots/%d.png' % counter)
                print('[%d]截图成功，保存至/screenshots/%d.png' % (counter, counter))
                for i in range(5):  # 测试1366x768分辨率下约滚动50次翻一页（指原神成就页）
                    if not in_rolling:
                        break
                    controller.scroll(dx=0, dy=-3)  # 控制鼠标滚动
                    time.sleep(1)  # 通过sleep控制自动滚动速度
            else:
                break


def main():
    def on_release(key):
        try:
            temp = ('release key {0}, vk: {1}'.format(key.char, key.vk))
        except AttributeError:
            if key.value.vk == 164 or key.value.vk == 165:
                print('[START]检测到按下Alt键，开始滚动截屏')
                roll()
                listener.stop()

    # 键盘监听
    with keyboard.Listener(on_release=on_release) as listener:
        listener.join()
