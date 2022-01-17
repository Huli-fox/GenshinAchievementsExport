# import time
# import json
# from screenshot import jamroll_screenshot
# with open('config.json','r',encoding='utf-8') as r:
#     config=json.load(r)
#     area = config['area']
# time.sleep(2)
# jamroll_screenshot.main(area)


from paddleocr import PaddleOCR, draw_ocr

# Paddleocr目前支持的多语言语种可以通过修改lang参数进行切换
# 例如`ch`, `en`, `fr`, `german`, `korean`, `japan`
ocr = PaddleOCR(use_angle_cls=True, lang="ch")  # need to run only once to download and load model into memory
img_path = './screenshots/3.png'
result = ocr.ocr(img_path, cls=True)
for line in result:
    print(line)
    with open('result.txt', 'a+', encoding='utf-8') as f:
        f.write(line[1][0] + '\n')

# # 显示结果
# from PIL import Image
#
# image = Image.open(img_path).convert('RGB')
# boxes = [line[0] for line in result]
# txts = [line[1][0] for line in result]
# scores = [line[1][1] for line in result]
# im_show = draw_ocr(image, boxes, txts, scores, font_path='./fonts/simfang.ttf')
# im_show = Image.fromarray(im_show)
# im_show.save('result.jpg')
