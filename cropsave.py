from PIL import Image


tsv = Image.open('img/informer_RAL5_20131128.png')
sv = tsv.crop((139, 18, 177, 42))
sv.save('img/25.jpg')