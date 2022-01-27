import json
import os
from src import get_area


def main():
    if not os.path.exists('screenshots'):
        print('[Self Check]screenshots文件夹不存在，创建')
        os.mkdir('screenshots')
    if not os.path.exists('config.json'):
        print('[Self Check]配置文件缺失，创建./config.json')
        with open('config.json', 'w', encoding='utf-8') as f:
            f.write('{}')
    try:
        with open('config.json', 'r', encoding='utf-8') as r:
            config = json.load(r)
            area = config['area']
    except KeyError:
        print('[Self Check]“area”参数未配置，启动Get Area脚本\n'
              '[Self Check]按下Alt，单击左键，第一次点击视为截图区域左上角，第二次视为截图区域右下角')
        get_area.main()
        print('[Self Check]area 配置成功！')
    try:
        with open('config.json', 'r', encoding='utf-8') as r:
            config = json.load(r)
            times = config['times']
    except KeyError:
        print('[Self Check]“times”参数未配置，设置为默认值：45')
        with open('config.json', 'r', encoding='utf-8') as r:
            config = json.load(r)
            config['times'] = 45
            with open('config.json', 'w', encoding='utf-8') as w:
                json.dump(config, w)
        print('[Self Check]times 配置成功！')
