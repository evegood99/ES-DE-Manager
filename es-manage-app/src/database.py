import sqlite3
import json
import pprint
import requests
from fake_useragent import UserAgent

SYSTEM_INFO_FILE_PATH = "./es-manage-app/src/info.json"
DB_FILE_PATH = "./es-manage-app/src/game.db"
TABLE_COMMON_SCHEMA = "(name_eng text, name_kor, rom_name text, desc_eng text, desc_kor text, ss_id integer, comm_name_eng text, comm_name_kor text, release_date text, developer text, publisher text, genre text, players text)"

class DBServer:

    def __init__(self) -> None:
        json_fp = open(SYSTEM_INFO_FILE_PATH)
        self.system_info = json.load(json_fp)['system_info']

    def callGameMeta(self, rom_name, sys_name):
        base_url = "https://api.screenscraper.fr/api2/jeuInfos.php"
        for data in self.system_info:
            # print(data['name_esde'], data['scrapper_system_id'])
            if sys_name == data['name_esde']:
                system_id = data['scrapper_system_id']
                break
        # print(system_id)
        ua = UserAgent()
        # headers = {'User-Agent': ua.random,}
        param = {"devid":"evegood", "devpassword":"yPoo9XlnDCG", "output":"json", "ssid":"evegood2", 'sspassword':"1132dudwls", "systemid":system_id, "romtype":"rom", "romnom":rom_name}
        resp = requests.get(base_url, params=param)
        # print(resp.text)
        # print(resp.status_code)
        if resp.status_code != 200:
            raise Exception(resp.text)
        result_data = json.loads(str(resp.text))
        # pprint.pprint(result_data['response']['ssuser'])
        print(result_data['response']['ssuser']['requeststoday'], result_data['response']['ssuser']["requestkotoday"])
        jeu_id = result_data['response']['jeu']['id']
        tmp_name_dict = {}
        for data in result_data['response']['jeu']['noms']:
            tmp_name_dict[data['region']] = data['text']
        game_name = None
        if "jp" in tmp_name_dict:
            game_name = tmp_name_dict['jp']
        elif "us" in tmp_name_dict:
            game_name = tmp_name_dict['us']
        else:
            game_name = tmp_name_dict['ss']
        developer = result_data['response']['jeu']['developpeur']['text']
        desciption = None
        for data in result_data['response']['jeu']['synopsis']:
            if data['langue'] == 'en':
                desciption = data['text']
                break
        genre = None
        for data in result_data['response']['jeu']['genres'][0]['noms']:
            if data['langue'] == 'en':
                genre = data['text']
                break
        players = result_data['response']['jeu']['joueurs']['text']
        




    def makeTable(self):
        con = sqlite3.connect(DB_FILE_PATH)

        for sys_obj in self.system_info:
            sys_name = sys_obj['name_esde']
            print(sys_name)

    def test(self):
        rom_name = "Chiki Chiki Machine Mou Race - Kenken to Black Maou no Ijiwaru Daisakusen (Japan)"
        sys_name = "3do"
        self.callGameMeta(rom_name, sys_name)
        

def test():
    server = DBServer()
    server.test()


if __name__ == "__main__":
    test()

# con = sqlite3.connect('./game.db')
# cur = 