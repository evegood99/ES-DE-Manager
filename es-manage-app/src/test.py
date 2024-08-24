# -*- coding : utf-8 -*-
import requests
import json

'''
Created on 2021. 4. 5.

@author: evegood

@description :
'''


userId = 'evegood'
password = 'yPoo9XlnDCG'
debug_password = 'sO8noULh3Dy'

# urlStr = 'https://screenscraper.fr/api2/jeuInfos.php?devid=evegood&devpassword=yPoo9XlnDCG&ssid=evegood&sspassword=1132dudwls&output=json&romtype=rom&romnom=valis 1'

urlStr = 'https://www.screenscraper.fr/api2/systemesListe.php?devid=evegood&devpassword=yPoo9XlnDCG&ssid=evegood&sspassword=1132dudwls&output=json'
# 
r = requests.get(urlStr)
print(r.text)
# x = json.loads(r.text)
# for i in x['response']['systemes']:
#     try:
#         print(str(i['id'])+','+i['noms']['noms_commun'])
#     except:
#         try:
#             print(str(i['id'])+','+i['noms']['nom_eu'])
#         except:
#             print(str(i['id'])+','+i['noms']['nom_us'])


# r = requests.get()


# urlStr = 'https://main.screenscraper.fr/api2/mediaVideoJeu.php?devid=evegood&devpassword=yPoo9XlnDCG&softname=&ssid=evegood&sspassword=1132dudwls&systemeid=135&jeuid=152356&media=video'

# r = requests.get(urlStr, stream = True) 
# file_name = 'test.mp4'
# with open(file_name, 'wb') as f: 
#     for chunk in r.iter_content(chunk_size = 1024*1024): 
#         if chunk: 
#             f.write(chunk) 