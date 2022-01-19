import json
from pynput import mouse, keyboard

l_m = []
l_k = []


def main():
    # 按键释放监听
    def on_release(key):
        info = 'special release key {0}, vk: {1}'.format(key, key.value.vk)
        if len(l_k) == 0:
            if key.value.vk == 164 or key.value.vk == 165:
                l_k.append(info)
                print('[Get Area]检测到按下Alt，开始鼠标监听')
                return False
        else:
            try:
                print('[Get Area]非法按键 release key {0}, vk: {1}'.format(key.char, key.vk))
            except AttributeError:
                if key.value.vk == 164 or key.value.vk == 165:
                    print('[Get Area]检测到按下Alt，开始鼠标监听')
                    l_k.append(info)
                    return True

    # 键盘监听
    with keyboard.Listener(on_release=on_release) as k_listener:
        if not on_release:
            exit(0)
        else:
            k_listener.join()

            # 鼠标点击事件
            def on_click(x, y, button, pressed):
                if len(l_m) == 2:
                    print('[Get Area]截屏区域配置成功！%s' % str(l_m))
                    with open('config.json', 'r', encoding='utf-8') as r:
                        config = json.load(r)
                        config['area'] = (l_m[0][0], l_m[0][1], l_m[1][0], l_m[1][1])
                        with open('config.json', 'w', encoding='utf-8') as w:
                            json.dump(config, w)
                    return False
                else:
                    if pressed and button.name == 'left':
                        info = (x, y)
                        print('[Get Area]点击了 %s' % str(info))
                        l_m.append(info)
                        return True

            # 监听事件绑定
            with mouse.Listener(on_click=on_click) as listener:
                if on_click:
                    listener.join()
                else:
                    exit(0)
