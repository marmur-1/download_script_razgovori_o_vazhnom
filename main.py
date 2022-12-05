import requests as req
from bs4 import BeautifulSoup as bs
from urllib.parse import urlencode
import json
from tqdm import tqdm
import zipfile
from pathlib import Path

print("\n"*20)

# функция разорхивирования
def unzip(f, encoding, v):
    with zipfile.ZipFile(f) as z:
        list = z.namelist()
        list.sort()
        for i in list:
            n = Path(data['config']['save_path']+
                    i.encode('cp437')
                    .decode(encoding)
                    .replace(" /","/")
                    .replace("/ ","/")
                    .replace("\"","＂")
                )
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

#Чтение конфига
with open("conf.json", "r", encoding='utf8') as read_file:
    data = json.load(read_file)
 
url = "https://razgovor.edsoo.ru"
ND = 0 

#Поиск и переход в топики
page = req.get(url)
page_soup = bs(page.text,"lxml")
main = page_soup.find("div", class_="content-block-wrapper")
atags = main.find_all('a', href=True)

#Поиск ссылок для скачивания в топиках
for a in atags:
    url_in = url+a['href']
    page_in = req.get(url_in)
    page_in_soup = bs(page_in.text,"lxml")
    main_in = page_in_soup.find_all("div", class_="topic-resource-download")

    #Проверка, был ли этот топик скачан полностью или нет
    if (a['href'] in data['downloaded']) == False:
        print("\nПопытка скачивания из:",a['href'])
        #Подготовка цикла для скачивания
        for ff in main_in:
            ND=ND+1
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
            print("\nСкачивание:",download_url)
            archive = data['config']['save_path']+a['href'].replace('/', '')+'_'+str(ND)+'.zip'
            download(download_url, archive)

            #Разархивирование файла
            print("Разархивирование: ", archive)
            unzip(archive, 'CP866', True)

        
        #Запись полностью скаченного топика
        data["downloaded"].append(a['href'])
        with open('conf.json',"w",encoding='utf8') as filedone:
                json.dump(data,filedone,ensure_ascii=False)

        print("\n\n\nЗапись:",a['href'])