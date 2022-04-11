from PIL import Image, ImageDraw
import requests, datetime, baseop, psycopg2

URLBegin = 'https://tesis.lebedev.ru/upload_test/files/flares_RAL5_'
ZNAM = (1e7 - 1) ** (1 / 337)
PIXTIME = 3600 * 24 / 305

def getImg(dat):
    i = 5
    url = URLBegin + dat + '.png'
    success = False
    while (i > 0) & (not success):
        try:
            t1 = datetime.datetime.now()
            imag = Image.open(requests.get(url, stream=True, timeout=3).raw)
            t2 = datetime.datetime.now()
            if t2 - t1 >= datetime.timedelta(seconds=3):
                print('Attemt ' + str(6 - i) + ' failed.')
                i -= 1
            else:
                success = True
        except:
            print('Attemt ' + str(6 - i) + ' failed.')
            i -= 1
    if not success:
        print ('5 attempts failed, server may be offline now.')
        return 0, False
    else:
        print ('Data for ' + dat + ' received.')
        return imag, True


def lineProc(imag):
    i = 0
    while i <= 337:
        pix = imag.getpixel((0, 337-i))
        if pix == (255, 0, 0):
            break
        i += 1
    low = i
    while pix == (255, 0, 0):
        i += 1
        pix = imag.getpixel((0, 337 - i))
    return low, i - 1


def chkHole(img):
    detected = False
    for i in range(98, 104):
        detPart = False
        for j in range(337):
            if img.getpixel((i, j)) == (255, 0, 0):
                detPart = True
                break
        if not detPart:
            detected = True
            break
    return detected


def chkHole1(img):
    begin = 0
    end = 0
    detected = False
    started = False
    for i in range(305):
        detected1 = True
        for j in range(337):
            if img.getpixel((i, j)) == (255, 0, 0):
                detected1 = False
        if detected1 & (not started):
            begin = i
            started = True
            detected = True
        if (not detected1) & started:
            end = i - 1
            break
    return detected, begin, end


def delHole(img, x1, x2):
    found1 = False
    found2 = False
    for i in range(337):
        if (img.getpixel((x1 - 1, i)) == (255, 0, 0)) & (not found1):
            found1 = True
            start1 = i
        if (img.getpixel((x2 + 1, i)) == (255, 0, 0)) & (not found2):
            found2 = True
            start2 = i
        if found1 & found2:
            break
    line = ImageDraw.Draw(img)
    if x1 == 0:
        line.line((x1, start2, x2 + 1, start2), fill = 'red', width=1)
    elif (x2 == 303) or (x2 == 304) or (x2 == 0):
        line.line((x1 - 1, start1, 304, start1), fill = 'red', width=1)
    else:
        line.line((x1 - 1, start1, x2 + 1, start2), fill = 'red', width=1)
    print('Common hole cleared.')
    img.save('tst.png')
    return img


def correctImg(img):
    i = 95
    hole = True
    while hole:
        for j in range(337):
            if img.getpixel((i, j)) == (255, 0, 0):
                hole = False
                break
        i -= 1
        if i == 0:
            img.putpixel((0, 270), (255, 0, 0))
            break
    left = i
    i1 = 106
    hole = True
    while hole:
        for j in range(337):
            if img.getpixel((i1, j)) == (255, 0, 0):
                hole = False
                break
        i1 += 1
        if i1 == 304:
            img.putpixel((304, 270), (255, 0, 0))
            break
    right = i1
    j = 0
    while j <= 337:
        if img.getpixel((left, 337 - j)) == (255, 0, 0):
            break
        j += 1
    while img.getpixel((left, 337 - j)) == (255, 0, 0):
        j += 1
    high1 = j - 1
    j = 0
    while j <= 337:
        if img.getpixel((right, 337 - j)) == (255, 0, 0):
            break
        j += 1
    while img.getpixel((right, 337 - j)) == (255, 0, 0):
        j += 1
    high2 = j - 1
    for i in range(left + 1, right):
        for j in range (337):
            img.putpixel((i, j), (0, 0, 0))
    line = ImageDraw.Draw(img)
    line.line((left, 337 - high1, right, 337 - high2), fill = 'red', width=1)
    print('Hole1 cleared.')
    return img


def getImage(url):
    # 5 попыток взять картинку
    i = 5
    got = False
    while (i > 0) & (not got):
        # время до начала запроса
        t1 = datetime.datetime.now()
        # запрос
        try:
            print('getting image')
            imag = Image.open(requests.get(url, stream=True, timeout=3).raw)
        except:
            pass
        # время после начала запроса
        t2 = datetime.datetime.now()
        # время ожидания меньше таймаута - запрос удачный
        if t2 - t1 < datetime.timedelta(seconds=3):
            got = True
            print('success')
        # время ожидания больше таймаута - уменьшаем число попыток на единицу
        else:
            print('Attempt ' + str(6 - i) + ' timed out.')
            i -= 1
    # сделано 5 неудачных попыток - выход из программы
    if i == 0:
        return imag, False
    # всё нормально - возврат картинки в обработку
    return imag, True


user = 'postgres'
passwd = 'Ly)vwW-D2.c)o0Hp'
cur, conn, status = baseop.baseconnect(user, passwd)
cur.execute('SELECT "Date" FROM "activity" WHERE "TotalDoze" = 0 ORDER BY "Date"')
dates = cur.fetchall()
date = dates[len(dates) - 1][0]
exist = True
while exist:
    dat = date.strftime("%Y%m%d")
    print('Processing date', dat)
    date = datetime.datetime(year=int(dat[:4]), month=int(dat[4:6]), day=int(dat[6:]), hour=0, minute=0, second=0)
    url = URLBegin + dat + '.png'
    print('Retrieving url ', url, sep='')
    imag, rslt = getImage(url)
    if rslt:
        print('Retrieved successfully')
        imgWrk = imag.crop((420, 19, 725, 357))
        imgRgb = imgWrk.convert('RGB')
        if chkHole(imgRgb):
            correctImg(imgRgb)
        chkHoleMore = True
        while chkHoleMore:
            chkHoleMore, x1, x2 = chkHole1(imgRgb)
            if chkHoleMore:
                imgRgb = delHole(imgRgb, x1, x2)
        dayDoze = 0
        for i in range(305):
            lin = imgRgb.crop((i, 0, i + 1, 338))
            low, high = lineProc(lin)
            down = 1e-9 * (1 + ZNAM ** low)
            up = 1e-9 * (1 + ZNAM ** high)
            avg = (up + down) / 2
            dayDoze += avg * PIXTIME
            dateWRK = date + datetime.timedelta(seconds= PIXTIME * i)
            dat = dateWRK.strftime('%Y-%m-%d %H:%M:%S')
            command = 'INSERT INTO "graphs_radiation" ("DateTime", "PixLow", "PixHigh", "AvgValue") VALUES' + "('" + dat +"', %s, %s, %s)" % (low, high, avg)
            cur.execute(command)
            conn.commit()
        dateWRK = dat = date.strftime("%Y-%m-%d")
        print('Doze total = ', dayDoze, sep='')
        cur.execute('UPDATE "activity" SET "TotalDoze" = %s WHERE "Date" = ' % (dayDoze) + "'" + dateWRK + "'")
        conn.commit()
        print('Date processsed successfully.')
        date -= datetime.timedelta(days=1)
    else:
        print("Can't retrieve %s. May be no more data or server is offline" % dat)
        exist = False




