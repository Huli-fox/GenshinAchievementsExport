import os
import re
import xlwt
import linecache
from paddleocr import PaddleOCR


def getfiles():
    file_list = os.listdir('screenshots')
    return file_list


def write_txt():
    # Paddleocr目前支持的多语言语种可以通过修改lang参数进行切换
    # 例如`ch`, `en`, `fr`, `german`, `korean`, `japan`
    ocr = PaddleOCR(use_angle_cls=True, lang="ch")  # need to run only once to download and load model into memory

    for n in getfiles():
        img_path = 'screenshots/%s' % n
        result = ocr.ocr(img_path, cls=True)
        for line in result:
            print(line)
            with open('result.txt', 'a+', encoding='utf-8') as f:
                f.write(line[1][0] + '\n')


def write_excel():
    counter = 1
    names = []
    contents = []
    isCompletes = []
    progresses = []
    dates = []
    findExData = re.compile(r'总计(.*?)\n')

    def check():
        if counter >= sum(1 for _ in open('result.txt', encoding='utf-8')):
            return False
        else:
            return True

    while True:
        name = linecache.getline('result.txt', counter).rstrip()
        names.append(name)
        is_complete = linecache.getline('result.txt', counter + 1).rstrip()
        if is_complete == '达成':
            isCompletes.append(True)
            progress = re.findall(findExData, linecache.getline('result.txt', counter + 2))
            if progress:
                progresses.append('总计%s' % progress[0])
                contents.append(linecache.getline('result.txt', counter + 3).rstrip())
                dates.append(linecache.getline('result.txt', counter + 4).rstrip())
                counter += 5
                if not check():
                    break
            else:
                progresses.append('null')
                contents.append(linecache.getline('result.txt', counter + 2).rstrip())
                dates.append(linecache.getline('result.txt', counter + 3).rstrip())
                counter += 4
                if not check():
                    break
        else:
            isCompletes.append(False)
            progresses.append(linecache.getline('result.txt', counter + 1).rstrip())
            contents.append(linecache.getline('result.txt', counter + 2).rstrip())
            dates.append('null')
            counter += 3
            if not check():
                break
    print(names, contents, isCompletes, progresses, dates)
    book = xlwt.Workbook(encoding='utf-8', style_compression=0)
    sheet1 = book.add_sheet('sheet1', cell_overwrite_ok=True)
    title = ['序号', '名称', '内容', '是否完成', '进度', '日期']
    for i in range(6):
        sheet1.write(0, i, title[i])
    a = 0
    for name in names:
        sheet1.write(a + 1, 0, a + 1)
        sheet1.write(a + 1, 1, name)
        sheet1.write(a + 1, 2, contents[a])
        sheet1.write(a + 1, 3, isCompletes[a])
        sheet1.write(a + 1, 4, progresses[a])
        sheet1.write(a + 1, 5, dates[a])
        a += 1
    book.save('result.xlsx')
    os.remove('result.txt')
