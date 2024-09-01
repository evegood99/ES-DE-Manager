
import json
import os
import requests
import pprint
from bs4 import BeautifulSoup
from threading import Thread
import sqlite3
import random
from thefuzz import process
from thefuzz import fuzz

SYSTEM_INFO_FILE_PATH = "./es-manage-app/src/info.json"
DB_FILE_PATH = "./es-manage-app/src/games_meta.db"
ROMS_XML_BASE_PATH = r'E:\Emul\Full_Roms_assets'
ROMS_TABLE_SCHEMA = "(id integer, src_name text, filename text, filename_kor text, rom_size integer, rom_crc text, rom_md5 text, rom_sha1 text, game_id integer, game_name text, alt integer, beta integer, demo integer, langs text, langs_short text, regions text, regions_short text)"
GAMES_TABLE_SCHEMA = "(id text, name text, name_kor text, desc text, desc_kor text, genre text, releasedate text, developer text, players text)"

def cleansingText(inputText):
    if inputText == None:
        return None
    r = BeautifulSoup(inputText, 'lxml').text
    # for rpr in ['<br>','<BR>','<p>','<P>','</p>','</P>']:
    #     r = r.replace(rpr,' ')
    return r

def mix_ratio(src, choices, limit=1):
    r1 = process.extract(src, choices, scorer=fuzz.token_sort_ratio, limit=1000)
    r2 = process.extract(src, choices, scorer=fuzz.WRatio, limit=1000)
    sc_dict = {}
    for (k, v) in set(r1):
        sc_dict[k] = v/2

    for (k, v) in set(r2):
        if k in sc_dict:
            sc_dict[k] += v/2
        else:
            sc_dict[k] = v/2
    if len(sc_dict) == 0:
        return (0, 0)
    data = list(sc_dict.items())
    data.sort(key=lambda x : x[1], reverse=True)
    if limit == 1:
        return data[0]
    else:
        return data[:limit]

class SSRomsMeta:

    def __init__(self, system_name):
        self.base_url = "https://api.screenscraper.fr/api2/jeuInfos.php"
        json_fp = open(SYSTEM_INFO_FILE_PATH)
        self.system_info = json.load(json_fp)['system_info']
        for sys_obj in self.system_info:
            sys_name = sys_obj['name_esde']
            if system_name == sys_name:
                sys_id = sys_obj['scrapper_system_id']
        self.system_name = system_name
        self.sys_id = sys_id
        self.rom_name_set = {}
        self.run_bucket = set([])

        self.roms_meta = {} #key : rom_id
        self.games_meta ={} #key : jeu_id

        self.tot_search_num = 0
        self.get_num = 0
        self.api_call_num = 0

        print(self.system_name)


    def jsonParsing(self, result_data, s_file_name):
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
        release_date = None
        if 'dates' in result_data['response']['jeu']:
            release_date = sorted(result_data['response']['jeu']['dates'], key=lambda x: x['text'])[0]['text'] 
        
        developer = None
        if 'developpeur' in result_data['response']['jeu']:
            developer = result_data['response']['jeu']['developpeur']['text']

        desciption = None
        if 'synopsis' in result_data['response']['jeu']:
            for data in result_data['response']['jeu']['synopsis']:
                if data['langue'] == 'en':
                    desciption = cleansingText(data['text'])
                    break

        genre = None
        if 'genres' in result_data['response']['jeu']:
            for data in result_data['response']['jeu']['genres'][0]['noms']:
                if data['langue'] == 'en':
                    genre = data['text']
                    break
        players = None
        if 'joueurs' in result_data['response']['jeu']:
            players = result_data['response']['jeu']['joueurs']['text']    

        s_rom_id_list = []
        if 'rom' in result_data['response']['jeu']:
            s_rom_id = int(result_data['response']['jeu']['rom']['id'])
            s_rom_id_list = [s_rom_id]

        roms_data = result_data['response']['jeu']['roms']

        self.games_meta[jeu_id] = (jeu_id, game_name, None, desciption, None, genre, release_date, developer, players)
        tmp_roms_file_name_set = set([])
        for rom_data in roms_data:
            alt = int(rom_data['alt'])
            beta = int(rom_data['beta'])
            demo = int(rom_data['demo'])

            langs = None
            langs_short = None
            regions = None
            regions_short = None

            if 'langues' in rom_data:
                langs = ",".join(rom_data['langues']['langues_en'])
                langs_short = ",".join(rom_data['langues']['langues_shortname'])

            if 'regions' in rom_data:
                regions = ",".join(rom_data['regions']['regions_en'])
                regions_short = ",".join(rom_data['regions']['regions_shortname'])


            rom_id = int(rom_data['id'])
            rom_crc = rom_data['romcrc']
            if rom_crc == '':
                rom_crc = None
            rom_md5 = rom_data['rommd5']
            if rom_md5 == '':
                rom_md5 = None
            rom_sha1 = rom_data['romsha1']
            if rom_sha1 == '':
                rom_sha1 = None
            rom_size = int(rom_data['romsize'])
            if rom_size == '':
                rom_size = None
            rom_filename = rom_data['romfilename']
            tmp_roms_file_name_set.add(rom_filename[:-4])
            # if s_file_name in rom_filename[:-4]:
            #     s_rom_id = rom_id
            # self.rom_name_set[rom_filename[:-4]] = rom_id
            self.rom_name_set.setdefault(rom_filename[:-4], set([])).add(rom_id)
            if rom_id in self.roms_meta:
                continue
            self.roms_meta[rom_id] = (rom_id, None, rom_filename, None, rom_size, rom_crc, rom_md5, rom_sha1, jeu_id, game_name, alt, beta, demo, langs, langs_short, regions, regions_short)
        
        mr = mix_ratio(s_file_name, tmp_roms_file_name_set)
        if mr[1] >= 50:
            s_rom_id_list = self.rom_name_set[mr[0]]

        return s_rom_id_list

    def update_src(self, file_name, s_rom_id):
        tmp_data = list(self.roms_meta[s_rom_id])
        tmp_data[1] = file_name
        self.roms_meta[s_rom_id] = tuple(tmp_data)


    def call_api(self, file_name):
        
        param = {"devid":"evegood", "devpassword":"yPoo9XlnDCG", "output":"json", "ssid":"evegood", 'sspassword':"1132dudwls", "systemid":self.sys_id, "romtype":"rom", "romnom":file_name}
        try:
            resp = requests.get(self.base_url, params=param, timeout=30)
        except requests.exceptions.Timeout as e:
            print('Timeout Error : ',file_name)
            self.run_bucket.remove(file_name)
            return 0
        if resp.status_code == 200:
            json_data = json.loads(resp.text)
        else:
            raise Exception(resp.text)
        s_rom_id_list = self.jsonParsing(json_data, file_name)
        for s_rom_id in s_rom_id_list:
            self.update_src(file_name, s_rom_id)
        
        self.run_bucket.remove(file_name)

    def insertTable(self):
        # x = list(self.games_meta.values())
        # print(x)
        con = sqlite3.connect(DB_FILE_PATH)
        cur = con.cursor()
        tb_name_game = 'games_'+self.system_name
        tb_name_rom = 'roms_'+self.system_name
        try:
            cur.execute(f"CREATE TABLE {tb_name_game}{GAMES_TABLE_SCHEMA};")
        except:
            pass
        game_v = '('+','.join(['?']*len(GAMES_TABLE_SCHEMA.split(',')))+')'
        cur.executemany(f'INSERT INTO {tb_name_game} VALUES{game_v};', list(self.games_meta.values()))
        con.commit()

        try:
            cur.execute(f"CREATE TABLE {tb_name_rom}{ROMS_TABLE_SCHEMA};")
        except:
            pass
        rom_v = '('+','.join(['?']*len(ROMS_TABLE_SCHEMA.split(',')))+')'
        cur.executemany(f'INSERT INTO {tb_name_rom} VALUES{rom_v};', list(self.roms_meta.values()))
        con.commit()



    def makeDBTable(self):

        xml_files_path = ROMS_XML_BASE_PATH+'\\'+self.system_name+'\\'+'textual'
        r = os.listdir(xml_files_path)
        name_set = set([])
        for file_name in r:
            if file_name[-4:] != '.xml':
                continue
            name_set.add(file_name[:-4])
        
        th_list = []
        self.tot_search_num = len(name_set)
        name_set = list(name_set)
        random.shuffle(name_set)
        name_set = set(name_set)
        while len(name_set)!=0:

            while True:
                if len(self.run_bucket) <= 10:
                    break

            file_name = name_set.pop()
            self.get_num += 1
            if file_name in self.rom_name_set:
                s_rom_list = self.rom_name_set[file_name]
                for s_rom in s_rom_list:
                    self.update_src(file_name, s_rom)                
                continue
            else:
                
                mr = mix_ratio(file_name, tuple(self.rom_name_set.keys()))
                if mr[1] >= 98:
                    s_rom_list = self.rom_name_set[mr[0]]
                    for s_rom in s_rom_list:
                        self.update_src(file_name, s_rom)                
                    continue  
            self.run_bucket.add(file_name)        
            self.api_call_num += 1
            t1 = Thread(target=self.call_api, args=(file_name,))
            t1.start()            
            th_list.append(t1)
    
            print(self.get_num, '/', self.tot_search_num, '('+str(self.api_call_num)+')', len(name_set), len(self.run_bucket))
            

        print('process join')
        for th in th_list:
            th.join()
        self.insertTable()

def test():
    system_name = 'atarist'
    ss= SSRomsMeta(system_name)
    ss.makeDBTable()

if __name__ == "__main__":
    test()