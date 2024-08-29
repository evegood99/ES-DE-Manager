# -*- coding : utf-8 -*-
import requests
import json

'''
Created on 2021. 4. 5.

@author: evegood

@description :

ssinfraInfos.php : ScreenScraper 인프라에 대한 정보
ssuserInfos.php : ScreenScraper 사용자에 대한 정보
userlevelsListe.php : ScreenScraper 사용자 레벨 목록
nbJoueursListe.php : 플레이어 수 목록
supportTypesListe.php : 지원 유형 목록
romTypesListe php : 목록 rom 유형
GenresListe.php : 장르 목록
RegionListe.php : 지역 목록
LanguageListe.php : 언어 목록
classificationListe.php : 분류(게임 등급) 목록
mediasSystemeListe.php : 시스템용 미디어 목록
mediasJeuListe .php : 목록 게임에 대한 미디어
infosJeuListe.php : 게임에 대한 정보 목록
infosRomListe.php : ROM에 대한 정보 목록
mediaGroup.php : 게임 그룹의 미디어 이미지 다운로드
mediaCompagnie.php : 게임 그룹의 미디어 이미지 다운로드
systemListe .php : 시스템 / 시스템 정보 / 미디어 정보 시스템 목록
mediaSysteme.php : 시스템에서 이미지 미디어 다운로드
mediaVideoSysteme.php : 시스템에서 비디오 미디어 다운로드
gameSearch.php : 이름으로 게임 검색(게임 테이블 반환(제한적) 최대 30개 게임) 확률별로 분류)
gameInfos.php : 게임 정보 / 게임 미디어
mediaJeu.php : 게임의 이미지 미디어 다운로드
mediaVideoJeu.php : 게임의 영상 미디어 다운로드
mediaManuelJeu .php : 게임 매뉴얼 다운로드
botNote.php : ScreenScraper 회원의 게임 노트 전송을 자동화하는 시스템
botProposition.php : ScreenScraper로 정보 또는 미디어 제안 전송을 자동화하는 시스템
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