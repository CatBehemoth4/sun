from PIL import Image
import pytesseract

def negate(img):
    for i in range(img.size[0]):
        for j in range(img.size[1]):
            colrs = img.getpixel((i, j))
            rpix = 255 - colrs[0]
            gpix = 255 - colrs[1]
            bpix = 255 - colrs[2]
            img.putpixel((i, j), (rpix, gpix, bpix))
    return img


pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Cat Behemoth\AppData\Local\Tesseract-OCR\tesseract.exe'
img = Image.open('img/informer_RAL5_20100304.png')
img1 = img.crop((586, 87, 606, 99))
img1 = negate(img1)
img1.save('processed.jpg')
reslt = pytesseract.image_to_string(img1, lang='eng')
print(reslt)