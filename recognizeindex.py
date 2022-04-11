from PIL import Image, ImageFilter
from getpass import getpass
import urllib.request, datetime, requests, time, baseop, pytesseract, psycopg2, simpleaudio


def negate(img):
    for i in range(0, img.size[0] - 1):
        for j in range(0, img.size[1] - 1):
            colrs = img.getpixel((i, j))
            rpix = 255 - colrs[0]
            gpix = 255 - colrs[1]
            bpix = 255 - colrs[2]
            img.putpixel((i, j), (rpix, gpix, bpix))
    return img


def negate_cl(img):
    for i in range(img.size[0]):
        for j in range(img.size[1]):
            colrs = img.getpixel((i, j))
            rpix = 255 - colrs[0]
            gpix = 255 - colrs[1]
            bpix = 255 - colrs[2]
            img.putpixel((i, j), (rpix, gpix, bpix))
    return img


def toDate(dt):
    return datetime.date(year=int(dt[:4]), month=int(dt[4:6]), day=int(dt[6:]))


def toBaseDate(dt):
    dat = dt[:4] + '-' + dt[4:6] + '-' + dt[6:]
    print(dat)
    return dat


def getimg(url):
    # 5 попыток взять картинку
    i = 5
    got = False
    while (i > 0) & (not got):
        #время до начала запроса
        t1 = datetime.datetime.now()
        #запрос
###        #with urllib.request.urlopen(url) as response:
        try:
            print('getting image')
            imag = Image.open(requests.get(url, stream=True, timeout=3).raw)
        except:
            pass
        #время после начала запроса
        t2 = datetime.datetime.now()
        #время ожидания меньше таймаута - запрос удачный
        if t2 - t1 < datetime.timedelta(seconds=3):
            got = True
            print('success')
        #время ожидания больше таймаута - уменьшаем число попыток на единицу
        else:
            print('Attempt ' + str(6 - i) + ' timed out.')
            i -= 1
    # сделано 5 неудачных попыток - выход из программы
    if i == 0:
        return imag, False
    # всё нормально - возврат картинки в обработку
    return imag, True


def recogn(imag, dat, cur, conn):
    print(dat)
    lang = 'eng'
    y0 = 20
    # пока не распознано
    recog = False
    while (y0 > 10) & (not recog):
        y = 39
    #пробуем распознать из целой большой строки, добавляя размер по 1 пикселу вниз, если не получилось ранее, пока есть смысл
        while (y <= 55) & (not recog):
            print(y)
            wrk = imag.crop((12, 19, 520, y))
            res = pytesseract.image_to_string(wrk, lang = lang)
            print(res)
        # проверяем, получилось ли число, и не больше ли оно, чем 12
            try:
                try:
                    res = float(res)
                except:
                    try:
                        res = float(res[len(res) - 5:len(res) - 2])
                    except:
                        pass
                if res == 50.3:
                    res = 0.3
            # получился подходящий результат  - пишем его в базу
                if res <= 12:
                    dat = toBaseDate(dat)
                    print(dat)
                    cur.execute('INSERT INTO "activity" ("Date", "Value", "Total") VALUES (' + "'" + '%s' % dat + "'" +', %s, 0)' % res)
                    recog = True
                    print(dat, 'recognized')
                    print(res)
                    conn.commit()
                    print('written')
            # результат распознавания больше 10 - увеличиваем размер по высоте на 1 пиксел
                else:
                    y += 1
                    print(y)
        # в результат распознавания не получилось число - увеличиваем размер по высоте на 1 пиксел
            except:
                y += 1
    # большую строку распознать не получилось - пробуем распознать маленький кусочек, постепенно расширяя его
        if y == 56:
            y0 -= 1
    if (y0 == 10):
        # определяем X-координату откуда начать вырезать картинку
        i = 9
        pxl = (0, 255, 0)
        # засекаем время
        t1 = datetime.datetime.now()
        while pxl[1] != 0:
            i += 1
            pxl = imag.getpixel((i, 30))
        # X-координата начала определена
        x = i + 1
        y = 40
        recog = False
        intrrpt = False
        while (x < i + 5) & (not recog) & (not intrrpt):
            print(x)
            while (y <= 55)  & (not recog) & (not intrrpt):
                print(y)
                wrk = imag.crop((x, 19, x + 41, y))
                res = pytesseract.image_to_string(wrk, lang = lang)
                try:
                    print(res)
                    res = float(res)
                    if res <= 10:
                        dat = toBaseDate(dat)
                        print(dat)
                        cur.execute('INSERT INTO "activity" ("Date", "Value", "Total") VALUES (' + "'" + '%s' % dat + "'" + ', %s, 0)' % res)
                        conn.commit()
                        print(dat, 'recognized')
                        recog = True
                except:
                    y += 1
            if y == 56:
                x += 1
                y = 40
            if t1 - datetime.datetime.now() > datetime.timedelta(seconds=20):
                intrrpt = True
        if intrrpt:
            return True
        if x == i + 5:
            print(dat, 'NOT recognized')
    if recog:
        return False
    else:
        return True

def recogn1(img):
    img.save('preproc.jpg')
    img1 = img.crop((585, 87, 607, 98))
    img1 = negate_cl(img1)
    img1.save('processed.jpg')
    try:
        reslt = pytesseract.image_to_string(img1, lang='eng')
        reslt = float(reslt)
    except:
        return reslt, True
    return reslt, False


def workall(cur, conn):
    cur.execute('SELECT "Date" FROM "activity" ORDER BY "Date"')
    dats = cur.fetchall()
    if dats == []:
        now = datetime.datetime.today()
    else:
        now = dats[0][0] - datetime.timedelta(days=1)
    exist = True
    while exist:
        dat = now.strftime("%Y%m%d")
        url = 'https://tesis.lebedev.ru/upload_test/files/informer_RAL5_' + dat + '.png'
        print('url formed')
        f, rslt = getimg(url)
        f.save('prepreproc.jpg')
        if rslt:
            now -= datetime.timedelta(1)
            intrrptd = recogn(f, dat, cur, conn)
            if intrrptd:
                now += datetime.timedelta(1)
                f1 = Image.open('prepreproc.jpg')
                f1 = f1.resize((686, 98), resample=Image.NEAREST)
                f1 = negate(f)
                f1 = f1.filter(ImageFilter.EDGE_ENHANCE)
                intrrptd1 = recogn(f1, dat, cur, conn)
                if intrrptd1:
                    f2 = Image.open('prepreproc.jpg')
                    res, intrrptd2 = recogn1(f2)
                    if not intrrptd2:
                        dat = toBaseDate(dat)
                        cur.execute('INSERT INTO "activity" ("Date", "Value", "Total") VALUES (' + "'" + '%s' % dat + "'" + ', %s, 0)' % res)
                        now -= datetime.timedelta(days=1)
                    else:
                        print('Can not recognize ' + dat)
                        catyowl.play()
                        exist = False
                else:
                    now -= datetime.timedelta(days=1)
            time.sleep(4)
        else:
            print('Can not get image ' + str(dat) + '. Try later')
            exist = False


def worktest(f):
    i = 9
    pxl = (0, 255, 0)
    while pxl[1] != 0:
        i += 1
        pxl = f.getpixel((i, 30))
    print(i)
    y = 40
    x = i + 1
    wrk = f.crop((x + 3, 19, x + 41, y + 8))
    lang = 'eng'
    pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Cat Behemoth\AppData\Local\Tesseract-OCR\tesseract.exe'
    res = pytesseract.image_to_string(wrk, lang=lang)
    print(res)


pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Cat Behemoth\AppData\Local\Tesseract-OCR\tesseract.exe'
catyowl = simpleaudio.WaveObject.from_wave_file('snd/cat_yowl.wav')
i = 3
success = False
while (i > 0) and (not success):
    user = 'postgres' #input('Enter username: ')
    passwd = 'Ly)vwW-D2.c)o0Hp' #getpass('Enter password: ')
    cur, conn, msg = baseop.baseconnect(user, passwd)
    if msg == 'OK':
        success = True
    else:
        i -= 1
        print('Connection failed, try again.')
if i == 0:
    print('Connection permanently failed. Exiting.')
else:
# f = Image.open('img/informer_RAL5_20210826.png')
# worktest(f)
    workall(cur, conn)
    cur.close()
    conn.close()
