import requests as req
from bs4 import BeautifulSoup as bs
from urllib.parse import urlencode
import json
from tqdm import tqdm
import zipfile
import os
from pathlib import Path
from datetime import datetime 

# функция удаления запрещённых символов
def removechars(value):
    deletechars = ':*?"<>|'
    value = value.replace("//","/").replace(" /","/").replace("/ ","/")
    for c in deletechars:
        value = value.replace(c,'')
    return value;
# функция разорхивирования
def unzip(f, path, v):
    with zipfile.ZipFile(f) as z:
        list = z.namelist()
        list.sort()

        for i in list:
            try:
                np = removechars(path+i.replace('\\',os.path.sep).encode('cp437').decode('cp866'))
            except Exception:
                np = removechars(path+i.replace('\\',os.path.sep))
            n = Path(np)
            if v:
                print(n)
            if i[-1] == '/':
                if not n.exists():
                    n.mkdir()
            else:
                with n.open('wb') as w:
                    w.write(z.read(i))
# функция скачиваниея
def download(url_from, path_to_file):
    download_response = req.get(url_from, stream=True)
    total_size_in_bytes= int(download_response.headers.get('content-length', 0))
    block_size = 1024 #1 Kibibyte
    progress_bar = tqdm(total=total_size_in_bytes, unit='mB', unit_scale=True)
    with open(path_to_file, 'wb') as f:
        for datadd in download_response.iter_content(block_size):
                progress_bar.update(len(datadd))
                f.write(datadd)
    progress_bar.close()
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print("ERROR, something went wrong")
# функция преобразования месяца
def month_from_ru_to_eng(month):
    out = ''
    if month == 'января': out = '01'
    if month == 'февраля': out = '02'
    if month == 'марта': out = '03'
    if month == 'апреля': out = '04'
    if month == 'мая': out = '05'
    if month == 'июня': out = '06'
    if month == 'июля': out = '07'
    if month == 'августа': out = '08'
    if month == 'сентябся': out = '09'
    if month == 'октября': out = '10'
    if month == 'ноября': out = '11'
    if month == 'декабря': out = '12'
    return out

#Чтение конфига
with open("conf.json", "r", encoding='utf8') as read_file:
    data = json.load(read_file)
 
url = "https://razgovor.edsoo.ru"

#Поиск и переход в топики
page = req.get(url)
page_soup = bs(page.text,"lxml")
main = page_soup.find("div", class_="content-block-wrapper")
atags = main.find_all('a', href=True)

#Поиск ссылок для скачивания в топиках
for a in atags:
    url_in = url+a['href']
    try:
        date = a.find("div", class_="card-date").text.replace("\n","")
        title = a.find("div", class_="card-title").text.replace("Подробнее","").replace("\n","")
    except Exception:
        continue

    day = date.split(' ')[0]
    mounth = month_from_ru_to_eng(date.split(' ')[1])
    year = str(datetime.now().year)
    date = year+"_"+mounth+"_"+day.zfill(2)
    subpath = date+" "+title+"/"


    page_in = req.get(url_in)
    page_in_soup = bs(page_in.text,"lxml")
    main_in = page_in_soup.find_all("div", class_="topic-resource-download")

    #Проверка, был ли этот топик скачан полностью или нет
    ND = 0 
    if (a['href'] in data['downloaded']) == False:
        print("\nПопытка скачивания из:",a['href'])
        #Подготовка цикла для скачивания
        for ff in main_in:
            atags_in = ff.a
            #Проверка на формат скачиваемого файла
            if atags_in['href'].endswith(".zip"):
                #zip    
                download_url = atags_in['href']
            elif atags_in['href'].endswith(".rar"):
                #rar 
                download_url = atags_in['href']
            else:
                #Подготовка для Яндекс.Диска
                base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'
                public_key = atags_in['href']
                final_url = base_url + urlencode(dict(public_key=public_key))
                response = req.get(final_url)
                download_url = response.json()['href']

            #Скачивание файла
            print("Скачивание:",download_url, date+" "+title+'.zip')
            s = Path(data['config']['save_path']+subpath)
            if not s.exists():
                s.mkdir()        
            ND = ND+1     
            archive = data['config']['save_path']+subpath+date+"_"+title+"_"+str(ND)+'.zip'
            if not Path(archive).exists():
                download(download_url, archive)

            #Разархивирование файла
            print("Разархивирование: ", archive)
            unzip(archive, data['config']['save_path']+subpath, True)

            # Удаление архива
            os.remove(archive)
        
        #Запись полностью скаченного топика
        data["downloaded"].append(a['href'])
        with open('conf.json',"w",encoding='utf8') as filedone:
                json.dump(data,filedone,ensure_ascii=False)

        print("Добавление",a['href'],"в исключение")