#-*- coding: UTF-8 -*-
import pytesseract
from PIL import Image

#验证码识别 fliname为图片路径
def verification_Code():
    image = Image.open('/Users/qinying/PycharmProjects/rongcapital/test/aa.jpg')
    vcode = pytesseract.image_to_string(image)
    print vcode