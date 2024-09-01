# ES-DE-Manager
It is manage program for ES-DE with multiple os

0-1. full roms download
0-2. 한글 roms download 및 패치

1-1. es_xml 파일 기준으로 전체 xml에 대한 스크랩핑 (screen_scrapper 진행)
1-2. es_xml 파일 이름 기준으로 https://api.screenscraper.fr/api2/jeuInfos.php?devid=evegood&devpassword=yPoo9XlnDCG&output=json&ssid=evegood&sspassword=1132dudwls&systemeid=3&romtype=rom&romnom=xml파일이름 으로 모든 개별 파일의 json 취득. 각 json을 취득 하는 과정에서 json 파일은 "jeu넘버_nom네임.json"으로 하며, 예시로 3_Sonic The Hedgehog 2.json 형태이다. 그리고 json 수집과정에서 roms 항목의 rom_name을 계속 저장하여 해당 이름과 동일한 xml파일을 검색하려는 경우는 skip한다.
1-3. 개별 json 파일 기반으로 시스템별로 2개의 테이블을 생성한다.
 1-3-1. roms_개별system 테이블을 만들며 id는 rom_id(ss에서부여한) 모든 롬파일을 기록한다. 또한 개별롬에 차이가 있으므로 한글이름 역시 여기에 적는다. jeu정보도 같이 기입한다.
 1-3-2. games_개별system에는 jeu기준 (게임이 normalize된) 게임을 입력하며, 여기에 게임에 대한 기본적인 desc등의 정보를 입력한다.

1-4. 한글 메타(텐타클)은 롬파일명 기준으로 매칭 시키며, 매칭이 끝난 이후. 한글 처리 등을 통해 jeu 기반의 한글명도 jeu테이블에 입력한다.



