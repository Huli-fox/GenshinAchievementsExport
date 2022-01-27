import os
import time
import json
from PIL import ImageGrab, Image
from numpy import average, dot, linalg
from pynput import keyboard
from pynput.mouse import Controller as MouseController
from pynput.mouse import Listener as MouseListener

in_rolling = True
start_key = False


def compare(p1, p2):  # 相似度检测
    def get_thum(image, size=(64, 64), greyscale=False):
        # 利用image对图像大小重新设置, Image.ANTIALIAS为高质量的
        image = image.resize(size, Image.ANTIALIAS)
        if greyscale:
            # 将图片转换为L模式，其为灰度图，其每个像素用8个bit表示
            image = image.convert('L')
        return image

    # 计算图片的余弦距离
    def image_similarity_vectors_via_numpy(image1, image2):
        image1 = get_thum(image1)
        image2 = get_thum(image2)
        images = [image1, image2]
        vectors = []
        norms = []
        for image in images:
            vector = []
            for pixel_tuple in image.getdata():
                vector.append(average(pixel_tuple))
            vectors.append(vector)
            # linalg=linear（线性）+algebra（代数），norm则表示范数
            # 求图片的范数？？
            norms.append(linalg.norm(vector, 2))
        a, b = vectors
        a_norm, b_norm = norms
        # dot返回的是点积，对二维数组（矩阵）进行计算
        res = dot(a / a_norm, b / b_norm)
        return res

    image1 = Image.open(p1)
    image2 = Image.open(p2)
    cosin = image_similarity_vectors_via_numpy(image1, image2)
    if cosin > 0.99999:
        return False
    else:
        return True


def roll(area, times):
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
                time.sleep(0.5)
                for i in range(times):  # 测试1366x768分辨率下约滚动50次翻一页（指原神成就页）
                    if not in_rolling:
                        break
                    controller.scroll(dx=0, dy=-3)  # 控制鼠标滚动
                    time.sleep(0.001)  # 通过sleep控制自动滚动速度
                time.sleep(0.5)
            else:
                break


def main():
    print('[Roll Screenshot]按下Alt开始滚动截图')
    with open('config.json', 'r', encoding='utf-8') as r:
        config = json.load(r)
        area = config['area']
        times = config['times']

    def on_release(key):
        try:
            temp = ('release key {0}, vk: {1}'.format(key.char, key.vk))
        except AttributeError:
            if key.value.vk == 164 or key.value.vk == 165:
                print('[Roll Screenshot]检测到按下Alt键，开始滚动截屏')
                roll(area, times)
                listener.stop()

    # 键盘监听
    with keyboard.Listener(on_release=on_release) as listener:
        listener.join()
