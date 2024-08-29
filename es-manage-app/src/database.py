import sqlite3
import json
import pprint
import requests
from fake_useragent import UserAgent
import xml.etree.ElementTree as ET
import os
from thefuzz import process
from thefuzz import fuzz

SYSTEM_INFO_FILE_PATH = "./es-manage-app/src/info.json"
DB_FILE_PATH = "./es-manage-app/src/game.db"
TABLE_COMMON_SCHEMA = "(rom_name text, name_eng text, name_kor text, desc_eng text, desc_kor text, releasedate text, developer text, publisher text, genre text, players text, ss_id integer, comm_name_eng text, comm_name_kor text)"
ROMS_XML_BASE_PATH = r'E:\Emul\Full_Roms_assets'
TENTACLE_ROM_META_PATH = "./es-manage-app/src/tentacle_meta"


class Fuzz:

    def __init__(self, system_name):
        self.system_name = system_name
        self.choice_list = []
        self.kor_dict = {}
        self.ready()

    def ready(self):
        xml_file_path = TENTACLE_ROM_META_PATH+'/'+self.system_name+'.xml'
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        result = {}
        for child in root.findall('game'):
            path = child.find('path').text
            path = path[2:-4]
            self.choice_list.append(path)
            title = child.find('name').text
            desc = child.find('desc')
            if desc == None:
                desc = None
            else:
                desc = desc.text
            self.kor_dict[path] = (title, desc)

            if ' V' in path:
                path = path.replace(' V', ' 5')
                self.choice_list.append(path)
                self.kor_dict[path] = (title, desc)

            elif ' VIII' in path:
                path = path.replace(' VIII', ' 8')
                self.choice_list.append(path)
                self.kor_dict[path] = (title, desc)

            elif ' VII' in path:
                path = path.replace(' VII', ' 7')
                self.choice_list.append(path)
                self.kor_dict[path] = (title, desc)

            elif ' VI' in path:
                path = path.replace(' VI', ' 6')
                self.choice_list.append(path)
                self.kor_dict[path] = (title, desc)

            elif ' IV' in path:
                path = path.replace(' IV', ' 4')
                self.choice_list.append(path)
                self.kor_dict[path] = (title, desc)


            elif 'III' in path:
                path = path.replace('III', '3')
                self.choice_list.append(path)
                self.kor_dict[path] = (title, desc)

            elif 'II' in path:
                path = path.replace('II', '2')
                self.choice_list.append(path)
                self.kor_dict[path] = (title, desc)

            if ' - ' in path:
                index1 = path.index(' - ')+3
                try:
                    index2 = path.index('(',index1)
                except:
                    index2 = 9999
                path = path[:index1-3]+' '+path[index2:]
                self.choice_list.append(path)
                self.kor_dict[path] = (title, desc)

            if ', The ' in path:
                path = path.replace(', The ', ' ')
                self.choice_list.append(path)
                self.kor_dict[path] = (title, desc)



    def matching(self, rom_name):
        r = process.extractOne(rom_name, self.choice_list)
        select_title = r[0]
        score = r[1]
        if score < 88:
            if ' - ' in rom_name:
                index1 = rom_name.index(' - ')+3
                try:
                    index2 = rom_name.index('(',index1)
                except:
                    index2 = 9999
                rom_name = rom_name[:index1-3]+' '+rom_name[index2:]
                r = process.extractOne(rom_name, self.choice_list)
                select_title = r[0]
                score = r[1]
                if score < 88:
                    # print(rom_name, select_title, score)
                    return {'title':None, 'desc':None}
            else:
                # print(rom_name, select_title, score)
                return {'title':None, 'desc':None}

        return {'title':self.kor_dict[select_title][0], 'desc':self.kor_dict[select_title][1]}

    def test_matching(self, rom_name):
        print(process.extract(rom_name, self.choice_list, scorer=fuzz.partial_ratio))
        # for line in self.choice_list:
        #     print(line)

    

class DBServer:

    def __init__(self) -> None:
        json_fp = open(SYSTEM_INFO_FILE_PATH)
        self.system_info = json.load(json_fp)['system_info']
        self.tentacle_system = set([x[:-4] for x in os.listdir(TENTACLE_ROM_META_PATH)])

    def callGameMeta(self, rom_name, sys_name):
        base_url = "https://api.screenscraper.fr/api2/jeuInfos.php"
        for data in self.system_info:
            # print(data['name_esde'], data['scrapper_system_id'])
            if sys_name == data['name_esde']:
                system_id = data['scrapper_system_id']
                break
        # print(system_id)
        param = {"devid":"evegood", "devpassword":"yPoo9XlnDCG", "output":"json", "ssid":"evegood", 'sspassword':"1132dudwls", "systemid":system_id, "romtype":"rom", "romnom":rom_name}
        resp = requests.get(base_url, params=param)
        # print(resp.text)
        # print(resp.status_code)
        if resp.status_code != 200:
            raise Exception(resp.text)
        result_data = json.loads(str(resp.text))
        pprint.pprint(result_data['response']['ssuser'])

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

        release_date = sorted(result_data['response']['jeu']['dates'], key=lambda x: x['text'])[0]['text'] 

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
        cur = con.cursor()
        for sys_obj in self.system_info:
            sys_name = sys_obj['name_esde']
            print(sys_name)
            if sys_name == '3do':
                tb_name = '_3do'
            elif sys_name == '3ds':
                tb_name = '_3ds'
            else:
                tb_name = sys_name
            if sys_name != 'mame':
                continue
            try:
                cur.execute(f'DROP TABLE {tb_name}')
            except:
                pass
            cur.execute(f"CREATE TABLE {tb_name}{TABLE_COMMON_SCHEMA};")

            xml_files_path = ROMS_XML_BASE_PATH+'\\'+sys_name+'\\'+'textual'
            r = os.listdir(xml_files_path)
            data_list = []
            if sys_name in self.tentacle_system:
                fuzz = Fuzz(sys_name)

            for file_name in r:
                tmp_data = []
                if file_name[-4:] != '.xml':
                    continue
                file_path = xml_files_path+'\\'+file_name
                rom_data = self.readXmlFile(file_path)

                name_kor = None
                desc_kor = None
                if sys_name in self.tentacle_system:
                    fuzz_r = fuzz.matching(file_name[:-4])
                    name_kor = fuzz_r['title']
                    desc_kor = fuzz_r['desc']
                tmp_data.append(file_name[:-4])
                tmp_data.append(rom_data['name'])
                tmp_data.append(name_kor)
                tmp_data.append(rom_data['desc'])
                tmp_data.append(desc_kor)
                tmp_data.append(rom_data['releasedate'])
                tmp_data.append(rom_data['developer'])
                tmp_data.append(rom_data['publisher'])
                tmp_data.append(rom_data['genre'])
                tmp_data.append(rom_data['players'])
                tmp_data.append(None)
                tmp_data.append(None)
                tmp_data.append(None)
                data_list.append(tmp_data)
            cur.executemany(f'INSERT INTO {tb_name} VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?);', data_list)
            con.commit()

            

    def readXmlFile(self, file_path):
        tree = ET.parse(file_path)
        root = tree.getroot()
        result = {}
        for child in root:
            tag = child.tag
            text = child.text
            result[tag] = text
        return result


    def test(self):
        rom_name = "Chiki Chiki Machine Mou Race - Kenken to Black Maou no Ijiwaru Daisakusen (Japan)"
        sys_name = "3do"
        self.callGameMeta(rom_name, sys_name)
        

def test():
    test_xml_file_path = r'E:\Emul\Full_Roms_assets\3do\textual\Battle Blues (Korea).xml'
    server = DBServer()
    # server.readXmlFile(test_xml_file_path)
    server.makeTable()

def test2():
    fuzz = Fuzz('msx')
    title = '"Yie Ar Kung-Fu 2 (Japan)"'
    r = fuzz.matching(title)
    print(r)
    fuzz.test_matching(title)
if __name__ == "__main__":
    test()

# con = sqlite3.connect('./game.db')
# cur = 