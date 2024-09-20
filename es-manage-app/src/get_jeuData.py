
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
import re
import xml.etree.ElementTree as ET
from main_new import MatchingRoms, normString, remove_extension, get_crc
from collections import Counter
import time
from shutil import copyfile

SYSTEM_INFO_FILE_PATH = "./es-manage-app/src/info.json"
DB_FILE_PATH = "./es-manage-app/src/games_meta.db"
ROMS_XML_BASE_PATH = r'E:\Emul\Full_Roms_assets'
ROMS_TABLE_SCHEMA = "(id text, src_name text, filename text, filename_kor text, rom_size integer, rom_crc text, rom_md5 text, rom_sha1 text, game_id integer, game_name text, alt integer, beta integer, demo integer, langs text, langs_short text, regions text, regions_short text)"
GAMES_TABLE_SCHEMA = "(id text, name text, name_kor text, desc text, desc_kor text, genre text, releasedate text, developer text, players text)"
GAMES_TABLE_ADD_SCHEMA = (('titlescreens', 'text'), ('screenshots', 'text'), ('wheel', 'text'), ('cover', 'text'), ('box2dside', 'text'), ('boxtextur', 'text'), ('box3d', 'text'), ('videos', 'text'), ('manuals', 'text'), ('support', 'text'))
RETROARCH_META_PATH = r"E:\Emul\Full_Roms_meta"
TENTACLE_ROM_META_PATH = "./es-manage-app/src/tentacle_meta"
ROMS_CACHE_PATH = r'E:\Emul\Full_Roms_cache'



def most_frequent_element(lst):
    # 리스트의 빈도수 계산
    counter = Counter(lst)
    # 가장 빈도수가 높은 요소와 그 빈도수 추출
    most_common = counter.most_common(1)
    # 가장 빈도수가 높은 요소를 반환
    return most_common[0][0] if most_common else None

def cleansingText(inputText):
    if inputText == None:
        return None
    r = BeautifulSoup(inputText, 'lxml').text
    # for rpr in ['<br>','<BR>','<p>','<P>','</p>','</P>']:
    #     r = r.replace(rpr,' ')
    return r

def removeBucket(t_str):
    pattern = '(\([^)]+\)|(\[+[^)]+\]))'
    # pattern = '(\s\([^)]+\))'
    result = re.findall(pattern, t_str)
    for find_r in result:
        t_str = t_str.replace(find_r[0],'')
    return t_str.strip()

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
        self.con = sqlite3.connect(DB_FILE_PATH)
        self.base_url = "https://api.screenscraper.fr/api2/jeuInfos.php"
        self.base_media_url = "https://api.screenscraper.fr/api2/mediaJeu.php"
        self.base_video_url = "https://api.screenscraper.fr/api2/mediaVideoJeu.php"
        self.base_manual_url = "https://api.screenscraper.fr/api2/mediaManuelJeu.php"
        json_fp = open(SYSTEM_INFO_FILE_PATH)
        self.system_info = json.load(json_fp)['system_info']
        for sys_obj in self.system_info:
            sys_name = sys_obj['name_esde']
            if system_name == sys_name:
                sys_id = sys_obj['scrapper_system_id']
                ra_system_name = sys_obj['name']
        self.system_name = system_name
        self.ra_system_name = ra_system_name

        self.sys_id = str(sys_id)
        self.rom_name_set = {}
        self.run_bucket = set([])
        self.pre_read_file = {}

        self.md5_to_rom_id = {}
        self.crc_to_rom_id = {}

        self.roms_meta = {} #key : rom_id
        self.games_meta ={} #key : jeu_id

        self.tot_search_num = 0
        self.get_num = 0
        self.api_call_num = 0

        self.stop_call_api = False

        print(self.system_name)
        self.preLoadTable()

    def preLoadTable(self):
        cur = self.con.cursor()
        tb_name_game = 'games_'+self.system_name
        tb_name_rom = 'roms_'+self.system_name

        r = cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tb_name_game}'")
        r = r.fetchone()
        if r == None:
            return 0
        else:
            if r[0] == tb_name_game:
                pass
            else:
                return 0

        r0 = cur.execute(f"SELECT * FROM {tb_name_game};")
        for line in r0:
            self.games_meta[line[0]] = line
        

        r1 = cur.execute(f"SELECT * FROM {tb_name_rom};")
        for line in r1:
            self.roms_meta[line[0]] = line
            self.rom_name_set.setdefault(remove_extension(line[2]), set([])).add(line[0])
            if line[5] != None:
                self.crc_to_rom_id[line[5].lower()] = line[0]
            if line[6] != None:
                self.md5_to_rom_id[line[6].lower()] = line[0]
            if line[1] != None:
                for f_name in line[1].split(';;'):
                    self.pre_read_file.setdefault(f_name, set([])).add(line[0])
                    
    def jsonParsing(self, result_data_str, s_file_name, ra_rom_meta_set=None):
        result_data = json.loads(result_data_str)
        jeu_id = result_data['response']['jeu']['id']

        with open(ROMS_XML_BASE_PATH+'\\'+self.system_name+'\\'+'json'+'\\'+str(jeu_id)+'.json','w', encoding='utf-8') as fp:
            fp.write(result_data_str)

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

        self.games_meta[jeu_id] = (jeu_id, game_name, None, desciption, None, genre, release_date, developer, players)
        if not 'roms' in result_data['response']['jeu']:
            return []
        roms_data = result_data['response']['jeu']['roms']

        tmp_roms_file_name_set = set([])
        check_crc = False
        alt, beta, demo, langs, langs_short, regions, regions_short = None, None, None, None, None, None, None
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
            if rom_crc != None:
                self.crc_to_rom_id[rom_crc.lower()] = rom_id
                if rom_crc.lower() == check_crc:
                    check_crc = True
            rom_md5 = rom_data['rommd5']
            if rom_md5 == '':
                rom_md5 = None
            if rom_md5 != None:
                self.md5_to_rom_id[rom_md5.lower()] = rom_id
            rom_sha1 = rom_data['romsha1']
            if rom_sha1 == '':
                rom_sha1 = None
            rom_size = int(rom_data['romsize'])
            if rom_size == '':
                rom_size = None
            rom_filename = rom_data['romfilename']
            tmp_roms_file_name_set.add(remove_extension(rom_filename))
            # if s_file_name in rom_filename[:-4]:
            #     s_rom_id = rom_id
            # self.rom_name_set[rom_filename[:-4]] = rom_id
            self.rom_name_set.setdefault(remove_extension(rom_filename), set([])).add(rom_id)
            if rom_id in self.roms_meta:
                continue
            self.roms_meta[rom_id] = (rom_id, None, rom_filename, None, rom_size, rom_crc, rom_md5, rom_sha1, jeu_id, game_name, alt, beta, demo, langs, langs_short, regions, regions_short)
        
        mr = mix_ratio(s_file_name, tmp_roms_file_name_set)
        if mr[1] >= 80:
            s_rom_id_list = list(self.rom_name_set[mr[0]])
            from_info = self.roms_meta[s_rom_id_list[0]]
            alt, beta, demo, langs, langs_short, regions, regions_short = from_info[10], from_info[11], from_info[12], from_info[13], from_info[14], from_info[15], from_info[16],
            if check_crc == False and ra_rom_meta_set != None:
                for rom_meta in ra_rom_meta_set:
                    from_rom_crc = rom_meta[3]
                    if from_rom_crc == None:
                        continue
                    self.roms_meta['ra_'+from_rom_crc] = ('ra_'+from_rom_crc,  rom_meta[0],  rom_meta[1], None,  rom_meta[2],  rom_meta[3],  rom_meta[4],  rom_meta[5], jeu_id, game_name, alt, beta, demo, langs, langs_short, regions, regions_short)
        else:
            if ra_rom_meta_set != None:
                for rom_meta in ra_rom_meta_set:
                    from_rom_crc = rom_meta[3]
                    if from_rom_crc == None:
                        continue
                    self.roms_meta['ra_'+from_rom_crc] = ('ra_'+from_rom_crc,  rom_meta[0],  rom_meta[1], None,  rom_meta[2],  rom_meta[3],  rom_meta[4],  rom_meta[5], jeu_id, game_name, None, None, None, None, None, None, None)

        return s_rom_id_list

    def update_src(self, file_name, s_rom_id):
        tmp_data = list(self.roms_meta[s_rom_id])
        if tmp_data[1] == None:
            tmp_data[1] = file_name
        else:
            tmp_split_data = set(tmp_data[1].split(';;'))
            tmp_split_data.add(file_name)
            tmp_data[1] = ";;".join(tmp_split_data)
        self.roms_meta[s_rom_id] = tuple(tmp_data)

    def call_api(self, file_name, rom_meta=None):
        if self.stop_call_api:
            self.run_bucket.remove(file_name)
            return 0

        param = {"devid":"evegood", "devpassword":"yPoo9XlnDCG", "output":"json", "ssid":"evegood1", 'sspassword':"1132dudwls", "systemeid":self.sys_id, "romtype":"rom", "romnom":file_name}
        try:
            resp = requests.get(self.base_url, params=param, timeout=30)
        except requests.exceptions.Timeout as e:
            print('Timeout Error : ',file_name)
            self.run_bucket.remove(file_name)
            return 0
        if resp.status_code == 200:
            json_data = resp.text
        else:
            if 'Erreur : Jeu non trouvée !' in resp.text or 'Erreur : Rom/Iso/Dossier non trouvée !' in resp.text:
                if not ' - ' in file_name:
                    self.run_bucket.remove(file_name)
                    print('Error : ', resp.text, '::',file_name)
                    return 0
                self.api_call_num += 1
                r_file_name = file_name.split(' - ')[0].strip()
                param = {"devid":"evegood", "devpassword":"yPoo9XlnDCG", "output":"json", "ssid":"evegood1", 'sspassword':"1132dudwls", "systemeid":self.sys_id, "romtype":"rom", "romnom":r_file_name}
                try:
                    resp = requests.get(self.base_url, params=param, timeout=30)
                except requests.exceptions.Timeout as e:
                    print('Timeout Error : ',file_name)
                    self.run_bucket.remove(file_name)
                    return 0
                if resp.status_code == 200:
                    json_data = resp.text
                else:
                    self.run_bucket.remove(file_name)
                    print('Error : ', resp.text, '::',file_name)
                    return 0
            elif "Votre quota de scrape est dépassé pour aujourd'hui" in resp.text or 'Faite du tri dans vos fichiers roms et repassez demain' in resp.text:
                self.stop_call_api = True
                self.run_bucket.remove(file_name)
                print('ERROR : qurter limit, stop call process')
                return 0

            else:
                self.run_bucket.remove(file_name)
                print('Error : ', resp.text, '::',file_name)
                return 0
        s_rom_id_list = self.jsonParsing(json_data, file_name, rom_meta)
        for s_rom_id in s_rom_id_list:
            self.update_src(file_name, s_rom_id)
        
        self.run_bucket.remove(file_name)

    def call_api2(self, game_id, output_xml_files_path):
        if self.stop_call_api:
            self.run_bucket.remove(game_id)
            return 0

        param = {"devid":"evegood", "devpassword":"yPoo9XlnDCG", "output":"json", "ssid":"evegood1", 'sspassword':"1132dudwls", "systemeid":self.sys_id, "gameid":game_id}
        try:
            resp = requests.get(self.base_url, params=param, timeout=30)
        except requests.exceptions.Timeout as e:
            print('Timeout Error : ',game_id)
            self.run_bucket.remove(game_id)
            return 0
        if resp.status_code == 200:
            with open(output_xml_files_path+'\\'+str(game_id)+'.json','w', encoding='utf-8') as fp:
                fp.write(str(resp.text))
            self.run_bucket.remove(game_id)

            # json_data = json.loads(resp.text)
            
        else:
            if 'Erreur : Jeu non trouvée !' in resp.text or 'Erreur : Rom/Iso/Dossier non trouvée !' in resp.text:
                self.run_bucket.remove(game_id)
                print('Error : ', resp.text, '::',game_id)
                return 0
            elif "Votre quota de scrape est dépassé pour aujourd'hui" in resp.text or 'Faite du tri dans vos fichiers roms et repassez demain' in resp.text:
                self.stop_call_api = True
                self.run_bucket.remove(game_id)
                print('ERROR : qurter limit, stop call process')
                return 0

            else:
                self.run_bucket.remove(game_id)
                print('Error : ', resp.text, '::',game_id)
                return 0

        # tmp_name_dict = {}
        # for data in json_data['response']['jeu']['noms']:
        #     tmp_name_dict[data['region']] = data['text']
        # game_name = tmp_name_dict['ss']            
        # self.run_bucket.remove(game_id)
        # if ':' in game_name:
        #     game_name = game_name.replace(':',' ')
        # if '?' in game_name:
        #     game_name = game_name.replace('?',' ')
        # if '/' in game_name:
        #     game_name = game_name.replace('/',' ')
        # if '*' in game_name:
        #     game_name = game_name.replace('*',' ')

        # with open(output_xml_files_path+'\\'+game_name+'.xml','w') as fp:
        #     fp.write(str(game_id))



    def insertTable(self):
        # x = list(self.games_meta.values())
        # print(x)
        cur = self.con.cursor()
        tb_name_game = 'games_'+self.system_name
        tb_name_rom = 'roms_'+self.system_name
        try:
            cur.execute(f"DROP TABLE {tb_name_game}")
        except:
            pass
        try:
            cur.execute(f"CREATE TABLE {tb_name_game}{GAMES_TABLE_SCHEMA};")
        except:
            pass
        game_v = '('+','.join(['?']*len(GAMES_TABLE_SCHEMA.split(',')))+')'
        cur.executemany(f'INSERT INTO {tb_name_game} VALUES{game_v};', list(self.games_meta.values()))
        self.con.commit()

        try:
            cur.execute(f"DROP TABLE {tb_name_rom}")
        except:
            pass
        try:
            cur.execute(f"CREATE TABLE {tb_name_rom}{ROMS_TABLE_SCHEMA};")
        except:
            pass
        rom_v = '('+','.join(['?']*len(ROMS_TABLE_SCHEMA.split(',')))+')'
        cur.executemany(f'INSERT INTO {tb_name_rom} VALUES{rom_v};', list(self.roms_meta.values()))
        self.con.commit()



    def makeDBTable(self, data_name=None):
        output_xml_files_path = ROMS_XML_BASE_PATH+'\\'+self.system_name+'\\'+'json'
        read_set = set([])
        if os.path.exists(output_xml_files_path):
            for f_name in os.listdir(output_xml_files_path):
                if os.path.exists(output_xml_files_path+'\\'+f_name):
                    read_set.add(f_name[:-5])             
            pass
        else:
            os.makedirs(output_xml_files_path)

        xml_files_path = ROMS_XML_BASE_PATH+'\\'+self.system_name+'\\'+'textual'
        # xml_files_path = ROMS_XML_BASE_PATH+'\\'+self.system_name+'\\'+'wheels'

        r = os.listdir(xml_files_path)
        name_set = {}
        for file_name in r:
            if file_name[-4:] != '.xml':
            # if file_name[-4:] != '.png':
                continue
            base_title, sub_title_list, bucket_str_list = normString(file_name)
            if len(sub_title_list) > 0:
                base_name =  base_title + ' - '.join(sub_title_list)           
            else:
                base_name = base_title
            ori_file_name = remove_extension(file_name)
            name_set.setdefault(base_name, set([])).add(ori_file_name)
        
        if data_name != None:
            name_set = {}
            base_title, sub_title_list, bucket_str_list = normString(data_name)
            if len(sub_title_list) > 0:
                base_name =  base_title + ' - '+' '.join(sub_title_list)           
            else:
                base_name = base_title
            ori_file_name = remove_extension(data_name)
            name_set.setdefault(base_name, set([])).add(ori_file_name)

        th_list = []
        self.tot_search_num = len(name_set)
        # name_set = list(name_set)
        # random.shuffle(name_set)
        while len(name_set)!=0:

            while True:
                if self.stop_call_api:
                    break

                if len(self.run_bucket) <= 10:
                    break

            if self.stop_call_api:
                break

            (base_name, src_roms_name_set) = name_set.popitem()

            self.get_num += 1
            match_rom_name_set = set([])
            for file_name in src_roms_name_set:
                if file_name in self.pre_read_file:
                    print(self.get_num, '/', self.tot_search_num, '('+str(self.api_call_num)+')', len(name_set), len(self.run_bucket))
                    match_rom_name_set.add(file_name)

            for nm in match_rom_name_set:
                if nm in src_roms_name_set:
                    src_roms_name_set.remove(nm)

            for file_name in src_roms_name_set:
                if file_name in self.rom_name_set:
                    s_rom_list = self.rom_name_set[file_name]
                    for s_rom in s_rom_list:
                        self.update_src(file_name, s_rom)                
                    print(self.get_num, '/', self.tot_search_num, '('+str(self.api_call_num)+')', len(name_set), len(self.run_bucket))
                    match_rom_name_set.add(file_name)

            for nm in match_rom_name_set:
                if nm in src_roms_name_set:
                    src_roms_name_set.remove(nm)

            for file_name in src_roms_name_set:
                mr = mix_ratio(file_name, tuple(self.rom_name_set.keys()))
                if mr[1] >= 98:
                    print('no call api :',file_name, mr[0])
                    s_rom_list = self.rom_name_set[mr[0]]
                    for s_rom in s_rom_list:
                        self.update_src(file_name, s_rom)
                    print(self.get_num, '/', self.tot_search_num, '('+str(self.api_call_num)+')', len(name_set), len(self.run_bucket))
                    match_rom_name_set.add(file_name)
         
            if len(match_rom_name_set) > 0 :
                continue

            if self.stop_call_api:
                break
            self.run_bucket.add(base_name)        
            self.api_call_num += 1
            t1 = Thread(target=self.call_api, args=(base_name,))
            t1.start()            
            th_list.append(t1)
    
            print(self.get_num, '/', self.tot_search_num, '('+str(self.api_call_num)+')', len(name_set), len(self.run_bucket))
            

        print('process join')
        for th in th_list:
            th.join()

        # self.after_merge_ra_meta()
        self.insertTable()


    def ra_parsing(self, total_str):
        # pattern = 'game\s*\(([^()]*(?:\([^\)]*\)[^()]*)*)\)'
        pattern = r'game\s*\([\s\S]*?\)\n\)\n'
        name_pattern = 'name\s+"([^"]*)"\n'
        rom_pattern = '\srom\s*\(([^()]*(?:\([^\)]*\)[^()]*)*)\)'
        rom_name_pattern = 'name\s+"([^"]*)"'
        rom_name_pattern2 = 'name\s+([^\s]*)\s'
        rom_size_pattern = 'size\s+([^\s]*)\s'
        rom_crc_pattern = 'crc\s+([^\s]*)\s'
        rom_md5_pattern = 'md5\s+([^\s]*)\s'
        rom_sha1_pattern = 'sha1\s+([^\s]*)\s'


        data_list = []
        result = re.findall(pattern, total_str)
        for line1 in result:
            # try:
            # line1 = line1 + ' )'
            # print(line1)
            name = re.findall(name_pattern, line1)[0]
            rom_str = re.findall(rom_pattern, line1)[0]
            try:
                rom_name = re.findall(rom_name_pattern, rom_str)[0]
            except:
                rom_name = re.findall(rom_name_pattern2, rom_str)[0]
            rom_size = re.findall(rom_size_pattern, rom_str)
            # except:
                # continue
            if rom_size == []:
                rom_size = None
            else:
                rom_size = int(rom_size[0])        
            rom_crc = re.findall(rom_crc_pattern, rom_str)
            if rom_crc == []:
                rom_crc = None
            else:
                rom_crc = rom_crc[0]

            rom_md5 = re.findall(rom_md5_pattern, rom_str)
            if rom_md5 == []:
                rom_md5 = None
            else:
                rom_md5 = rom_md5[0]

            rom_sha1 = re.findall(rom_sha1_pattern, rom_str)
            if rom_sha1 == []:
                rom_sha1 = None
            else:
                rom_sha1 = rom_sha1[0]        

            yield (name, rom_name, rom_size, rom_crc, rom_md5, rom_sha1)

    def check_data(self):
        file_list = []
        xml_files_path = ROMS_XML_BASE_PATH+'\\'+self.system_name+'\\'+'textual'
        r = os.listdir(xml_files_path)
        name_set = set([])
        for file_name in r:
            if file_name[-4:] != '.xml':
                continue
            name_set.add(remove_extension(file_name))        

        for file_name in os.listdir(RETROARCH_META_PATH):
            if file_name == self.ra_system_name+".dat":
                file_list.append(RETROARCH_META_PATH+'\\'+file_name)
                break
        
        for file_name in os.listdir(RETROARCH_META_PATH+'\\'+'no-intro'):
            if file_name == self.ra_system_name+".dat":
                file_list.append(RETROARCH_META_PATH+'\\'+'no-intro'+'\\'+file_name)
                break

        for file_name in os.listdir(RETROARCH_META_PATH+'\\'+'redump'):
            if file_name == self.ra_system_name+".dat":
                file_list.append(RETROARCH_META_PATH+'\\'+'redump'+'\\'+file_name)
                break

        for file_name in os.listdir(RETROARCH_META_PATH+'\\'+'tosec'):
            if file_name == self.ra_system_name+".dat":
                file_list.append(RETROARCH_META_PATH+'\\'+'tosec'+'\\'+file_name)
                break
        
        ra_meta_set = set([])
        for f_path in file_list:
            fp = open(f_path)
            try:
                data = fp.read()
            except UnicodeDecodeError:
                fp = open(f_path, encoding='utf-8')
                data = fp.read()
            for line in self.ra_parsing(data):
                ra_meta_set.add(line[0])

        name_set.update(ra_meta_set)

        mr = MatchingRoms(None, self.system_name)
        try_name_data = set([])
        for f_name in name_set:
            r, base_title = mr.run(f_name, is_print_all=False)
            if r:
                try_name_data.add(base_title)          

        for f_name in try_name_data:
            print(f_name)
        print(len(try_name_data))

    def ra_meta_for_noname(self):
        file_list = []
        self.get_num = 0
        for file_name in os.listdir(RETROARCH_META_PATH):
            if file_name == self.ra_system_name+".dat":
                file_list.append(RETROARCH_META_PATH+'\\'+file_name)
                break
        
        for file_name in os.listdir(RETROARCH_META_PATH+'\\'+'no-intro'):
            if file_name == self.ra_system_name+".dat":
                file_list.append(RETROARCH_META_PATH+'\\'+'no-intro'+'\\'+file_name)
                break

        for file_name in os.listdir(RETROARCH_META_PATH+'\\'+'redump'):
            if file_name == self.ra_system_name+".dat":
                file_list.append(RETROARCH_META_PATH+'\\'+'redump'+'\\'+file_name)
                break

        for file_name in os.listdir(RETROARCH_META_PATH+'\\'+'tosec'):
            if file_name == self.ra_system_name+".dat":
                file_list.append(RETROARCH_META_PATH+'\\'+'tosec'+'\\'+file_name)
                break

        params = []
        for f_path in file_list:
            fp = open(f_path)
            try:
                data = fp.read()
            except UnicodeDecodeError:
                fp = open(f_path, encoding='utf-8')
                data = fp.read()
            for line in self.ra_parsing(data): #(name, rom_name, rom_size, rom_crc, rom_md5, rom_sha1)
                src_name = line[0]
                rom_name = line[1]  
                # print(src_name, rom_name)      
                params.append((src_name, rom_name))
        
        # for line in params:
            # print(line)

        tb_name = 'roms_'+self.system_name
        cur = self.con.cursor()
        cur.execute(f"UPDATE {tb_name} SET src_name=game_name")
        cur.executemany(f"UPDATE {tb_name} SET src_name=? WHERE filename=?",params)
        self.con.commit()

            
        
    def after_merge_ra_meta(self):
        file_list = []
        self.get_num = 0
        for file_name in os.listdir(RETROARCH_META_PATH):
            if file_name == self.ra_system_name+".dat":
                file_list.append(RETROARCH_META_PATH+'\\'+file_name)
                break
        
        for file_name in os.listdir(RETROARCH_META_PATH+'\\'+'no-intro'):
            if file_name == self.ra_system_name+".dat":
                file_list.append(RETROARCH_META_PATH+'\\'+'no-intro'+'\\'+file_name)
                break

        for file_name in os.listdir(RETROARCH_META_PATH+'\\'+'redump'):
            if file_name == self.ra_system_name+".dat":
                file_list.append(RETROARCH_META_PATH+'\\'+'redump'+'\\'+file_name)
                break

        for file_name in os.listdir(RETROARCH_META_PATH+'\\'+'tosec'):
            if file_name == self.ra_system_name+".dat":
                file_list.append(RETROARCH_META_PATH+'\\'+'tosec'+'\\'+file_name)
                break
        
        ra_meta_set = {}
        for f_path in file_list:
            fp = open(f_path)
            try:
                data = fp.read()
            except UnicodeDecodeError:
                fp = open(f_path, encoding='utf-8')
                data = fp.read()
            for line in self.ra_parsing(data): #(name, rom_name, rom_size, rom_crc, rom_md5, rom_sha1)
                src_name = line[0]
                rom_name = line[1]
                base_title, sub_title_list, bucket_str_list = normString(src_name)
                if len(sub_title_list) > 0:
                    base_name =  base_title +' - '.join(sub_title_list)           
                else:
                    base_name = base_title

                ra_meta_set.setdefault(base_name, set([])).add(line)

                # ra_meta_set.add(line)
        self.tot_search_num = len(ra_meta_set)
        # ra_meta_set = list(ra_meta_set)
        # random.shuffle(ra_meta_set)
        th_list = []

        while len(ra_meta_set)!=0:

            while True:
                if self.stop_call_api:
                    break

                if len(self.run_bucket) <= 10:
                    break

            if self.stop_call_api:
                break

            self.get_num += 1
            (base_name, ra_rom_meta_set) = ra_meta_set.popitem()

            match_data = set([])

            for ra_rom_meta in ra_rom_meta_set:

                ra_src_name = ra_rom_meta[0]
                ra_rom_crc = ra_rom_meta[3]
                if ra_rom_crc != None:
                    ra_rom_crc = ra_rom_crc.lower()
                    if ra_rom_crc in self.crc_to_rom_id:
                        s_rom_id = self.crc_to_rom_id[ra_rom_crc]
                        self.update_src(ra_src_name, s_rom_id)
                        match_data.add(ra_rom_meta)

                    elif ra_rom_crc in self.roms_meta:
                        match_data.add(ra_rom_meta)

            for data in match_data:
                if data in ra_rom_meta_set:
                    ra_rom_meta_set.remove(data)

            for ra_rom_meta in ra_rom_meta_set:
                ra_src_name = ra_rom_meta[0]
                ra_rom_md5 = ra_rom_meta[4]
                if  ra_rom_md5 != None:
                    ra_rom_md5 = ra_rom_md5.lower()
                    if ra_rom_md5 in self.md5_to_rom_id:
                        s_rom_id = self.md5_to_rom_id[ra_rom_md5]
                        self.update_src(ra_src_name, s_rom_id)
                        match_data.add(ra_rom_meta)

            for data in match_data:
                if data in ra_rom_meta_set:
                    ra_rom_meta_set.remove(data)
                
            for ra_rom_meta in ra_rom_meta_set:
                ra_src_name = ra_rom_meta[0]
                ra_file_name = ra_rom_meta[1]
                ra_rom_size = ra_rom_meta[2]
                ra_rom_crc = ra_rom_meta[3]
                if ra_rom_crc != None:
                    ra_rom_crc = ra_rom_crc.lower()
                else:
                    continue
                ra_rom_md5 = ra_rom_meta[4]
                if  ra_rom_md5 != None:
                    ra_rom_md5 = ra_rom_md5.lower()
                ra_rom_sha1 = ra_rom_meta[5]
                if  ra_rom_sha1 != None:
                    ra_rom_sha1 = ra_rom_sha1.lower()

                file_name = ra_src_name
                if file_name in self.pre_read_file:
                    from_rom_id_set = self.pre_read_file[file_name]
                    from_rom_id = random.choice(tuple(from_rom_id_set))
                    from_rom_info = self.roms_meta[from_rom_id]
                    jeu_id = from_rom_info[8]
                    game_name = from_rom_info[9]
                    rom_id = 'ra_'+ra_rom_crc
                    self.roms_meta[rom_id] = (rom_id, file_name, ra_file_name, None, ra_rom_size, ra_rom_crc, ra_rom_md5, ra_rom_sha1, jeu_id, game_name, from_rom_info[10], from_rom_info[11], from_rom_info[12], from_rom_info[13], from_rom_info[14], from_rom_info[15], from_rom_info[16])
                    print(self.get_num, '/', self.tot_search_num, '('+str(self.api_call_num)+')', len(self.run_bucket))
                    match_data.add(ra_rom_meta)

                else:
                    mr = mix_ratio(file_name, tuple(self.pre_read_file.keys()))
                    if mr[1] >= 94:
                        print('no call api :',file_name, mr[0])
                        s_rom_list = list(self.pre_read_file[mr[0]])
                        for s_rom in s_rom_list:
                            self.update_src(file_name, s_rom)
                        from_rom_info = self.roms_meta[s_rom_list[0]]
                        jeu_id = from_rom_info[8]
                        game_name = from_rom_info[9]
                        rom_id = 'ra_'+ra_rom_crc
                        self.roms_meta[rom_id] = (rom_id, file_name, ra_file_name, None, ra_rom_size, ra_rom_crc, ra_rom_md5, ra_rom_sha1, jeu_id, game_name, from_rom_info[10], from_rom_info[11], from_rom_info[12], from_rom_info[13], from_rom_info[14], from_rom_info[15], from_rom_info[16])
                        print(self.get_num, '/', self.tot_search_num, '('+str(self.api_call_num)+')', len(self.run_bucket))
                        match_data.add(ra_rom_meta)

            for data in match_data:
                if data in ra_rom_meta_set:
                    ra_rom_meta_set.remove(data)
                
            for ra_rom_meta in ra_rom_meta_set:
                ra_src_name = ra_rom_meta[0]
                ra_file_name = ra_rom_meta[1]
                ra_rom_size = ra_rom_meta[2]
                ra_rom_crc = ra_rom_meta[3]
                if ra_rom_crc != None:
                    ra_rom_crc = ra_rom_crc.lower()
                else:
                    continue
                ra_rom_md5 = ra_rom_meta[4]
                if  ra_rom_md5 != None:
                    ra_rom_md5 = ra_rom_md5.lower()
                ra_rom_sha1 = ra_rom_meta[5]
                if  ra_rom_sha1 != None:
                    ra_rom_sha1 = ra_rom_sha1.lower()

                file_name = ra_src_name

                if file_name in self.rom_name_set:
                    s_rom_list = list(self.rom_name_set[file_name])
                    for s_rom in s_rom_list:
                        self.update_src(file_name, s_rom)
                    from_rom_info = self.roms_meta[s_rom_list[0]]
                    jeu_id = from_rom_info[8]
                    game_name = from_rom_info[9]
                    rom_id = 'ra_'+ra_rom_crc
                    self.roms_meta[rom_id] = (rom_id, file_name, ra_file_name, None, ra_rom_size, ra_rom_crc, ra_rom_md5, ra_rom_sha1, jeu_id, game_name, from_rom_info[10], from_rom_info[11], from_rom_info[12], from_rom_info[13], from_rom_info[14], from_rom_info[15], from_rom_info[16])
                    print(self.get_num, '/', self.tot_search_num, '('+str(self.api_call_num)+')', len(self.run_bucket))
                    match_data.add(ra_rom_meta)
                else:
                    
                    mr = mix_ratio(file_name, tuple(self.rom_name_set.keys()))
                    if mr[1] >= 94:
                        print('no call api :',file_name, mr[0])
                        s_rom_list = list(self.rom_name_set[mr[0]])
                        for s_rom in s_rom_list:
                            self.update_src(file_name, s_rom)
                        from_rom_info = self.roms_meta[s_rom_list[0]]
                        jeu_id = from_rom_info[8]
                        game_name = from_rom_info[9]
                        rom_id = 'ra_'+ra_rom_crc
                        self.roms_meta[rom_id] = (rom_id, file_name, ra_file_name, None, ra_rom_size, ra_rom_crc, ra_rom_md5, ra_rom_sha1, jeu_id, game_name, from_rom_info[10], from_rom_info[11], from_rom_info[12], from_rom_info[13], from_rom_info[14], from_rom_info[15], from_rom_info[16])
                        print(self.get_num, '/', self.tot_search_num, '('+str(self.api_call_num)+')', len(self.run_bucket))
                        match_data.add(ra_rom_meta)

            for data in match_data:
                if data in ra_rom_meta_set:
                    ra_rom_meta_set.remove(data)

            if len(match_data) > 0 :
                continue
            if self.stop_call_api:
                break

            self.run_bucket.add(base_name)        
            self.api_call_num += 1
            t1 = Thread(target=self.call_api, args=(base_name, ra_rom_meta_set))
            t1.start()            
            th_list.append(t1)
    
            print(self.get_num, '/', self.tot_search_num, '('+str(self.api_call_num)+')', len(self.run_bucket))
            
        for th in th_list:
            th.join()

        print('process join')
        self.insertTable()


    def addTentacleMetaAndFillName(self):
        cur = self.con.cursor()
        tb_name = 'roms_'+self.system_name

        xml_file_path = TENTACLE_ROM_META_PATH+'/'+self.system_name+'.xml'
        if os.path.exists(xml_file_path):
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            result = {}
            for child in root.findall('game'):
                path = child.find('path').text
                path = '%'+path[2:-4]+'.%'
                title = child.find('name').text
                cur.execute(f'UPDATE {tb_name} SET filename_kor = ? WHERE filename LIKE ? AND filename_kor is null',(title, path))
            self.con.commit()

        r = cur.execute(f"SELECT * FROM {tb_name}")
        game_data_dict = {}
        rom_id_dict = {}
        dup_rom_id_dict = {}
        for line in r:
            rom_id = line[0]
            src_name_str = line[1]
            if src_name_str == None:
                f_src_name = None
                src_name_str_list = []
            else:
                src_name_str_list = line[1].split(';;')
                f_src_name = removeBucket(src_name_str_list[0])

            if rom_id in rom_id_dict:
                rom_id_dict[rom_id].update(set(src_name_str_list))
                dup_rom_id_dict[rom_id] = rom_id_dict[rom_id]
            else:
                rom_id_dict[rom_id] = set(src_name_str_list)
            
            file_name = line[2]
            f_file_name = removeBucket(remove_extension(file_name))
            file_name_kor = line[3]
            if file_name_kor == None:
                f_file_name_kor = None
            else:
                f_file_name_kor = removeBucket(file_name_kor)
            game_id = line[8]
            game_data_dict.setdefault(game_id, []).append({'rom_id':rom_id, 'rom_name':f_file_name, 'ename':f_src_name, 'kname':f_file_name_kor})                
            

        params = []
        for rom_id in dup_rom_id_dict:
            src_name_str_list = dup_rom_id_dict[rom_id]
            if len(src_name_str_list) == 0:
                src_name_str = None
            else:
                src_name_str = ';;'.join(src_name_str_list)
            params.append((src_name_str, rom_id))

        cur.executemany(f"UPDATE {tb_name} SET src_name=? WHERE id=?", params)
        cur.execute(f"DELETE FROM {tb_name} WHERE ROWID NOT IN(SELECT MIN(ROWID) FROM {tb_name} GROUP BY id)")
        self.con.commit()

        r = cur.execute(f"SELECT * FROM {tb_name}")


        for game_id in game_data_dict:
            # if game_id != 1919:
            #     continue
            data_list = game_data_dict[game_id]
            k_name_data = {}
            e_name_data = {}
            k_name_match_data = {}
            e_name_match_data = {}
            # print(data_list)
            for data in data_list:
                rom_id = data['rom_id']
                rom_name = data['rom_name']
                ename = data['ename']
                kname = data['kname']
                if ename != None:
                    e_name_data.setdefault(rom_name, []).append(ename)
                else:
                    e_name_match_data[(rom_name, rom_id)] = None
                if kname != None:
                    k_name_data.setdefault(rom_name, []).append(kname)
                else:
                    k_name_match_data[(rom_name, rom_id)] = None
            for rom_name in e_name_data:
                e_name_data[rom_name] = most_frequent_element(e_name_data[rom_name])

            for rom_name in k_name_data:
                k_name_data[rom_name] = most_frequent_element(k_name_data[rom_name])

            if len(e_name_data) > 0:
                for (rom_name, rom_id) in e_name_match_data:
                    r = mix_ratio(rom_name, e_name_data.keys())
                    sel_rom_name = r[0]
                    e_name_match_data[(rom_name, rom_id)] = e_name_data[sel_rom_name]
            
            if len(k_name_data) > 0:
                for (rom_name, rom_id) in k_name_match_data:
                    r = mix_ratio(rom_name, k_name_data.keys())
                    sel_rom_name = r[0]
                    k_name_match_data[(rom_name, rom_id)] = k_name_data[sel_rom_name]

            params_e = []
            for (rom_name, rom_id) in e_name_match_data:
                e_name = e_name_match_data[(rom_name, rom_id)]
                params_e.append((e_name, rom_id))

            params_k = []
            for (rom_name, rom_id)in k_name_match_data:
                k_name = k_name_match_data[(rom_name, rom_id)]
                params_k.append((k_name, rom_id))


            cur.executemany(f"UPDATE {tb_name} SET src_name=? WHERE id=?", params_e)
            cur.executemany(f"UPDATE {tb_name} SET filename_kor=? WHERE id=?", params_k)

        cur.execute(f"UPDATE {tb_name} SET src_name = game_name where src_name is null")
        self.con.commit()

    def addMediaColumn(self):
        tb_name = 'games_'+self.system_name
        cursor = self.con.cursor()
        col_list = ['titlescreens', 'screenshots', 'wheel', 'cover', 'box2dside', 'boxtexture', 'box3d', 'videos', 'manuals', 'support']
        for col in col_list:
            cursor.execute(f'ALTER TABLE {tb_name} ADD COLUMN {col} TEXT')
        self.con.commit()

    def addMediaToDB(self):
        # self.addMediaColumn()
        regions = set(['jp','kr','wor','us','eu','ss'])
        media_type_set = {'sstitle':'titlescreens', 'ss':'screenshots', 'wheel':'wheel', 'wheel-hd':'wheel', 'box-2D':'cover', 'box-2D-side':'box2dside', 'box-texture':'boxtexture', 'box-3D':'box3d', 'video':'videos', 'manuel':'manuals', 'support-2D':'support'}
        json_path = ROMS_XML_BASE_PATH+'\\'+self.system_name+'\\'+'json'
        n = 0

        pr_data_list = []
        for file_name in set(os.listdir(json_path)):
            with open(json_path+'\\'+file_name, encoding='utf-8') as fp:
                result_data = json.load(fp)
                game_id = result_data['response']['jeu']['id']
                tmp_data = {}
                for media_data in result_data['response']['jeu']['medias']:
                    m_type = media_data['type']
                    if m_type in media_type_set:
                        if 'region' in media_data:
                            if media_data['region'] in regions:
                                region = '('+media_data['region']+')'
                            else:
                                continue
                        else:
                            region = ''
                        
                        if 'support' in media_data:
                            if m_type in tmp_data and m_type+region in tmp_data[m_type]:
                                continue
                            spt = media_data['support']
                            support = f'[{spt}]'
                        else:
                            support = ''
                        col_name = media_type_set[m_type]
                        tmp_data.setdefault(m_type, set([])).add(m_type+region+support)
                
                if 'sstitle' in tmp_data:
                    sstitle = ';;'.join(tmp_data['sstitle'])
                else:
                    sstitle = None

                if 'ss' in tmp_data:
                    ss = ';;'.join(tmp_data['ss'])
                else:
                    ss = None
                
                if 'wheel' in tmp_data:
                    wheel = ';;'.join(tmp_data['wheel'])
                else:
                    wheel = None

                if 'wheel-hd' in tmp_data:
                    if wheel == None:
                        wheel = ';;'.join(tmp_data['wheel-hd'])
                    else:
                        wheel = wheel+';;'+';;'.join(tmp_data['wheel-hd'])

                if 'box-2D' in tmp_data:
                    box2d = ';;'.join(tmp_data['box-2D'])
                else:
                    box2d = None

                if 'box-2D-side' in tmp_data:
                    box2dside = ';;'.join(tmp_data['box-2D-side'])
                else:
                    box2dside = None

                if 'box-texture' in tmp_data:
                    boxtexture = ';;'.join(tmp_data['box-texture'])
                else:
                    boxtexture = None

                if 'box-3D' in tmp_data:
                    box3d = ';;'.join(tmp_data['box-3D'])
                else:
                    box3d = None

                if 'video' in tmp_data:
                    video = ';;'.join(tmp_data['video'])
                else:
                    video = None

                if 'manuel' in tmp_data:
                    manuel = ';;'.join(tmp_data['manuel'])
                else:
                    manuel = None

                if 'support-2D' in tmp_data:
                    support2D = ';;'.join(tmp_data['support-2D'])
                else:
                    support2D = None


                pr_data_list.append((sstitle, ss, wheel, box2d, box2dside, boxtexture, box3d, video, manuel, support2D, game_id))

        # for line in pr_data_list:
        #     if len(line) != 11:
        #         print(line)

        cursor = self.con.cursor()
        tb_name = 'games_'+self.system_name
        cursor.executemany(f'UPDATE {tb_name} SET titlescreens=?, screenshots=?, wheel=?, cover=?, box2dside=?, boxtexture=?, box3d=?, videos=?, manuals=?, support=? WHERE id=?',pr_data_list )
        self.con.commit()



    def getAddMedia(self):
        roms_cache_path = ROMS_CACHE_PATH+'\\'+str(self.sys_id)
        cached_data = set([])
        for file_name in os.listdir(roms_cache_path):
            file_name = file_name[:-4]
            f = file_name.split('_')
            game_id = f[0]
            media_type = f[1]
            if media_type in ['videos']:
                region = None
            else:
                region = f[2]
                cached_data.add((game_id, media_type, region))
            cached_data.add((game_id, media_type))
        
        # for line in cached_data:
        #     print(line)

        regions = set(['jp','kr','wor','us','eu','ss'])
        media_type_set = {'sstitle':'titlescreens', 'ss':'screenshots', 'wheel':'wheel', 'wheel-hd':'wheel', 'box-2D':'cover', 'box-2D-side':'box2dside', 'box-texture':'boxtexture', 'box-3D':'box3d', 'video':'videos', 'manuel':'manuals', 'support-2D':'support'}
        json_path = ROMS_XML_BASE_PATH+'\\'+self.system_name+'\\'+'json'
        n = 0
        pr_data_list = []
        cursor = self.con.cursor()
        col_list = ['id', 'titlescreens', 'screenshots', 'wheel', 'cover', 'box2dside', 'boxtexture', 'box3d', 'videos', 'manuals', 'support']
        tb_name = 'games_'+self.system_name
        r = cursor.execute(f"SELECT id, titlescreens, screenshots, wheel, cover, box2dside, boxtexture, box3d, videos, manuals, support FROM {tb_name}")
        for line in r:
            game_id = line[0]

            for x in range(1, 11):
                if line[x] == None:
                    continue
                for xx in line[x].split(';;'):
                    result = re.findall(r'([0-9a-zA-Z-]+)|\((.*?)\)', xx)
                    output = [x for group in result for x in group if x]
                    media_type = media_type_set[output[0]]
                    if len(output) == 1:
                        region = None
                        if x == 8:
                            file_name = game_id+'_'+media_type+'.mp4'
                        elif x == 9:
                            file_name = game_id+'_'+media_type+'.pdf'
                        else:
                            file_name = game_id+'_'+media_type+'.png'
                    else:
                        region = output[1]
                        if x == 8:
                            file_name = game_id+'_'+media_type+'_'+region+'.mp4'
                        elif x == 9:
                            file_name = game_id+'_'+media_type+'_'+region+'.pdf'
                        else:
                            file_name = game_id+'_'+media_type+'_'+region+'.png'
                    if (game_id, media_type, region) in cached_data:
                        # print((game_id, media_type, region))
                        continue
                    else:
                        pr_data_list.append((game_id, file_name, xx))

        self.tot_search_num = len(set(pr_data_list))
        # print(self.tot_search_num)
        # for pr_data in pr_data_list:
        #     print(pr_data)

        # pr_data_list = []
        # for file_name in set(os.listdir(json_path)):
        #     with open(json_path+'\\'+file_name, encoding='utf-8') as fp:
        #         result_data = json.load(fp)
        #         game_id = result_data['response']['jeu']['id']
        #         game_name_sample = result_data['response']['jeu']['noms'][0]['text']
        #         for media_data in result_data['response']['jeu']['medias']:

        #             m_type = media_data['type']
        #             if m_type in media_type_set:
        #                 if m_type == 'manuel':
        #                     region = media_data['region']
        #                     if region in regions:
        #                         m_region_ext = '_'+region+'.pdf'
        #                     else:
        #                         continue
        #                 elif m_type == 'video':
        #                     region = None
        #                     m_region_ext = '.mp4'
        #                 else:
        #                     region = media_data['region']
        #                     if region in regions:
        #                         m_region_ext = '_'+region+'.pdf'
        #                     else:
        #                         continue
        #                     m_region_ext = '_'+region+'.png'
                            
        #                 m_type_mid_name = media_type_set[m_type]

        #                 if (game_id, m_type_mid_name) in cached_data:
        #                     if region != None and not (game_id, m_type_mid_name,region) in cached_data and  region in ['jp', 'kr']:
        #                         new_media_name = str(game_id)+'_'+m_type_mid_name+m_region_ext
        #                         # print(new_media_name, game_id, m_type+f'({region})')
        #                         m_type_f = m_type+f'({region})'
        #                         if m_type == 'support-2D' and 'support' in media_data:
        #                             m_type_f = m_type_f+'[1]'

        #                         pr_data_list.append((game_id, new_media_name, m_type_f))
        #                         n += 1
        #                     else:
        #                         continue
        #                 else:
        #                     if region == None:
        #                         m_type_f = m_type
        #                     else:
        #                         m_type_f = m_type+f'({region})'
        #                     if m_type == 'support-2D' and 'support' in media_data:
        #                         m_type_f = m_type_f+'[1]'

        #                     new_media_name = str(game_id)+'_'+m_type_mid_name+m_region_ext
        #                     pr_data_list.append((game_id, new_media_name, m_type_f))
        #                     # print(new_media_name, m_type+f'({region})')
        #                     n += 1

        # self.tot_search_num = len(set(pr_data_list))
        # print(self.tot_search_num)

        # for pr_data in pr_data_list:
        #     print(pr_data)

        th_list = []
        for data in set(pr_data_list):
            time.sleep(0.2)
            self.get_num += 1
            while True:
                if self.stop_call_api:
                    break

                if len(self.run_bucket) <= 7:
                    break

            if self.stop_call_api:
                break
            # print(data)
            self.run_bucket.add(data[1])        
            self.api_call_num += 1
            t1 = Thread(target=self.call_api_media_download, args=(data[0], data[1], data[2]))
            t1.start()            
            th_list.append(t1)
            print(str(self.api_call_num), '/', self.tot_search_num, len(self.run_bucket))


        for th in th_list:
            th.join()


                            

    def call_api_media_download(self, game_id, out_file_name, call_media_type):

        if self.stop_call_api:
            self.run_bucket.remove(out_file_name)
            return 0
        param = {"devid":"evegood", "devpassword":"yPoo9XlnDCG", "ssid":"evegood", 'sspassword':"1132dudwls", "systemeid":self.sys_id, "jeuid":game_id, "media":call_media_type}
        try:
            if 'video' in call_media_type:
                base_url = self.base_video_url
            elif 'manuel' in call_media_type:
                base_url = self.base_manual_url
            else:
                base_url = self.base_media_url
            # print(base_url, out_file_name, call_media_type)
            resp = requests.get(base_url, params=param, stream = True)
        except requests.exceptions.Timeout as e:
            # print('Timeout Error : ',game_id)
            self.run_bucket.remove(out_file_name)
            return 0
        except Exception as e:
            self.run_bucket.remove(out_file_name)
            print('Error : ',e)

        try:
            if resp.status_code == 200  and not 'Erreur' in resp.text[:100] and not 'Error' in resp.text[:100] and not 'NOMEDIA' in resp.text[:100]:
                with open(ROMS_CACHE_PATH+'\\'+str(self.sys_id)+'\\'+out_file_name, 'wb') as f: 
                    for chunk in resp.iter_content(chunk_size = 1024*1024): 
                        if chunk: 
                            f.write(chunk)         
                self.run_bucket.remove(out_file_name)
            
            elif resp.status_code == 430 or resp.status_code == 431:
                self.stop_call_api = True
                self.run_bucket.remove(out_file_name)
                print('Error : ', resp.text, '::',game_id)
                return 0

            else:
                self.run_bucket.remove(out_file_name)
                print('Error : ', resp.text, '::',game_id, call_media_type)
                return 0
        except Exception as e:
            self.run_bucket.remove(out_file_name)
            print('Error : ',e)



        # urlStr = 'https://api.screenscraper.fr/api2/mediaJeu.php?devid=evegood&devpassword=yPoo9XlnDCG&softname=&ssid=evegood2&sspassword=1132dudwls&systemeid=1&jeuid=3&media=support-texture(wor)'

        # # urlStr = 'https://api.screenscraper.fr/api2/mediaVideoJeu.php?devid=xxx&devpassword=yyy&softname=zzz&ssid=test&sspassword=test&crc=&md5=&sha1=&systemeid=29&jeuid=88766&media=video'

        # r = requests.get(urlStr, stream = True) 
        # print(r.status_code)
        # print(r.text[:100])
        # 'Problème de paramètres'
        # if 'Erreur' in r.text[:100] or 'Error' in r.text[:100] or 'NOMEDIA' in r.text[:100] or r.status_code != 200:
        #     print(r.text[:100])
        # file_name = 'test.png'
        # with open(file_name, 'wb') as f: 
        #     for chunk in r.iter_content(chunk_size = 1024*1024): 
        #         if chunk: 
        #             f.write(chunk)         

    # def getCachedMedia2(self):
    #     roms_cache_path = ROMS_CACHE_PATH+'\\'+str(self.sys_id)
    #     if os.path.exists(roms_cache_path):
    #         pass
    #     else:
    #         os.makedirs(roms_cache_path)

    #     regions = ['jp','kr','wor','us','eu']
    #     media_type_set = {'sstitle':'titlescreens', 'ss':'screenshots', 'wheel':'wheel', 'wheel-hd':'wheel', 'box-2D':'cover', 'box-2D-side':'box2dside', 'box-texture':'boxtexture', 'box-3D':'box3d', 'video':'videos', 'manuel':'manuals', 'support-2D':'support'}
    #     crc_meta = {}

    #     json_path = ROMS_XML_BASE_PATH+'\\'+self.system_name+'\\'+'json'
    #     for file_name in set(os.listdir(json_path)):
    #         with open(json_path+'\\'+file_name, encoding='utf-8') as fp:
    #             result_data = json.load(fp)
    #             game_id = result_data['response']['jeu']['id']
    #             game_name_sample = result_data['response']['jeu']['noms'][0]['text']
    #             for media_data in result_data['response']['jeu']['medias']:
    #                 m_type = media_data['type']
    #                 if m_type in media_type_set:
    #                     # if not m_type in ['video','manuel']:
    #                     #     m_region_ext = '_'+media_data['region']+'.png'
    #                     if m_type == 'manuel':
    #                         m_region_ext = '_'+media_data['region']+'.pdf'
    #                     # else:
    #                     #     continue
    #                     elif m_type == 'video':
    #                         m_region_ext = '.mp4'
    #                     else:
    #                         m_region_ext = '_'+media_data['region']+'.png'
    #                     m_type_mid_name = media_type_set[m_type]
    #                     m_crc = media_data['crc'].lower()
    #                     new_media_name = str(game_id)+'_'+m_type_mid_name+m_region_ext
    #                     crc_meta[m_crc] = new_media_name

    #     for m_crc in crc_meta:
    #         print(m_crc, crc_meta[m_crc])

    #     cover_path = ROMS_XML_BASE_PATH+'\\'+self.system_name+'\\'+'covers'
    #     for file_name in set(os.listdir(cover_path)):
    #         cover_file_path = cover_path+'\\'+file_name
    #         crc_val = get_crc(cover_file_path).lower()
    #         print(cover_file_path, crc_val)
    #     #     if crc_val in crc_meta:
    #     #         print(cover_file_path, crc_meta[crc_val])


    def getCachedMedia(self):
        roms_cache_path = ROMS_CACHE_PATH+'\\'+str(self.sys_id)
        if os.path.exists(roms_cache_path):
            pass
        else:
            os.makedirs(roms_cache_path)

        regions = ['jp','kr','wor','us','eu']
        media_type_set = {'sstitle':'titlescreens', 'ss':'screenshots', 'wheel':'wheel', 'wheel-hd':'wheel', 'box-2D':'cover', 'box-2D-side':'box2dside', 'box-texture':'boxtexture', 'box-3D':'box3d', 'video':'videos', 'manuel':'manuals', 'support-2D':'support'}
        crc_meta = {}
        md5_meta = {}
        sha1_meta = {}
        chched_path = r'E:\Emul\Skraper-1.1.1\Cache\\'+str(self.sys_id)
        if os.path.exists(chched_path):
            for file_name in os.listdir(chched_path):
                if file_name[:9] != 'MEDIA.2..':
                    continue
                file_name = file_name.replace('MEDIA.2..','')
                meta_data = file_name.split('.0.0.')
                media_type = meta_data[0]
                crc_data_list = meta_data[1].split('.')
                crc = crc_data_list[0].lower()
                md5 = crc_data_list[1].lower()
                sha1 = crc_data_list[2].lower()
                crc_meta[crc] = (media_type, 'MEDIA.2..'+file_name)
                md5_meta[md5] = (media_type, 'MEDIA.2..'+file_name)
                sha1_meta[sha1] = (media_type, 'MEDIA.2..'+file_name)


            # print(crc, md5, sha1)

        json_path = ROMS_XML_BASE_PATH+'\\'+self.system_name+'\\'+'json'
        for file_name in set(os.listdir(json_path)):
            with open(json_path+'\\'+file_name, encoding='utf-8') as fp:
                result_data = json.load(fp)
                game_id = result_data['response']['jeu']['id']
                game_name_sample = result_data['response']['jeu']['noms'][0]['text']
                for media_data in result_data['response']['jeu']['medias']:
                    m_type = media_data['type']
                    if m_type in media_type_set:
                        # if not m_type in ['video','manuel']:
                        #     m_region_ext = '_'+media_data['region']+'.png'
                        if m_type == 'manuel':
                            m_region_ext = '_'+media_data['region']+'.pdf'
                        # else:
                        #     continue
                        elif m_type == 'video':
                            m_region_ext = '.mp4'
                        else:
                            m_region_ext = '_'+media_data['region']+'.png'
                        m_type_mid_name = media_type_set[m_type]
                        m_crc = media_data['crc']
                        m_md5 = media_data['md5']
                        m_sha1 = media_data['sha1']
                        new_media_name = str(game_id)+'_'+m_type_mid_name+m_region_ext
                        if m_crc in crc_meta:
                            print(new_media_name)
                            copyfile(chched_path+'\\'+crc_meta[m_crc][1],roms_cache_path+'\\'+new_media_name)

    def exportGameNames(self):
        output_xml_files_path = ROMS_XML_BASE_PATH+'\\'+self.system_name+'\\'+'json'
        read_set = set([])
        if os.path.exists(output_xml_files_path):
            for f_name in os.listdir(output_xml_files_path):
                if os.path.exists(output_xml_files_path+'\\'+f_name):
                    read_set.add(f_name[:-5])             
            pass
        else:
            os.makedirs(output_xml_files_path)
        

        cur = self.con.cursor()
        if self.system_name == 'mame':
            self.system_name = 'fbneo'
        tb_name = 'games_'+self.system_name

        r = cur.execute(f"SELECT id FROM {tb_name}")
        game_id_list = []
        for line in r:
            self.tot_search_num += 1
            if line[0] in read_set:
                continue
            game_id_list.append(line[0])
        
        game_id_list = set(game_id_list)

        self.tot_search_num -= len(read_set)

        th_list  =[]
        for game_id in game_id_list:
            time.sleep(0.2)

            while True:
                if self.stop_call_api:
                    break

                if len(self.run_bucket) <= 10:
                    break

            if self.stop_call_api:
                break



            self.run_bucket.add(game_id)        
            self.api_call_num += 1
            t1 = Thread(target=self.call_api2, args=(game_id, output_xml_files_path))
            t1.start()            
            th_list.append(t1)
    
            print(str(self.api_call_num), '/', self.tot_search_num, len(self.run_bucket))
            
        for th in th_list:
            th.join()



def test2():

    pattern = 'game\s*\(([^()]*(?:\([^\)]*\)[^()]*)*)\)'

    name_pattern = 'name\s+"([^"]*)"\n'
    rom_pattern = 'rom\s*\(([^()]*(?:\([^\)]*\)[^()]*)*)\)'
    rom_name_pattern = 'name\s+"([^"]*)"'
    rom_size_pattern = 'size\s+([^\s]*)\s'
    rom_crc_pattern = 'crc\s+([^\s]*)\s'
    rom_md5_pattern = 'md5\s+([^\s]*)\s'
    rom_sha1_pattern = 'sha1\s+([^\s]*)\s'

    data_list = []
    result = re.findall(pattern, a)
    for line1 in result:
        name = re.findall(name_pattern, line1)[0]
        rom_str = re.findall(rom_pattern, line1)[0]
        rom_name = re.findall(rom_name_pattern, rom_str)[0]
        rom_size = re.findall(rom_size_pattern, rom_str)
        if rom_size == []:
            rom_size = None
        else:
            rom_size = rom_size[0]        
        rom_crc = re.findall(rom_crc_pattern, rom_str)
        if rom_crc == []:
            rom_crc = None
        else:
            rom_crc = rom_crc[0]

        rom_md5 = re.findall(rom_md5_pattern, rom_str)
        if rom_md5 == []:
            rom_md5 = None
        else:
            rom_md5 = rom_md5[0]

        rom_sha1 = re.findall(rom_sha1_pattern, rom_str)
        if rom_sha1 == []:
            rom_sha1 = None
        else:
            rom_sha1 = rom_sha1[0]        

        print(name, rom_name, rom_size, rom_crc, rom_md5, rom_sha1)
    

def test():
    # s_list = ["3do", "3ds", "amiga", "atarijaguar", "atarist", "dos", "dreamcast", "famicom", "gameandwatch", "gamegear", "gb","gbc","gba","gc","mastersystem", "megacd", "megadrive", "msx", "n64", "nds", "pc98", "pcengine", "pcenginecd", "pcfx", "ps2", "psp", "psx", "saturn", "sega32x", "sfc", "wii", "wonderswancolor", "x68000"]
    system_name = 'gb'
    # for system_name in s_list:
    ss= SSRomsMeta(system_name)
    # ss.makeDBTable("Battle Chess Enhanced")
    # ss.addTentacleMetaAndFillName()
    ss.getAddMedia()
    #    ss.addMediaToDB()
    # for system_name in s_list[2:]:
        # 'mastersystem','megacd', 'megadrive','msx','n64']:
        # ss= SSRomsMeta(system_name)
        # ss.getCachedMedia()
    # ss.exportGameNames()
    # ss.makeDBTable()
    # ss.addTentacleMetaAndFillName()
    # ss.ra_meta_for_noname()

    # s_list = [["3do", "3ds", "amiga", "atarijaguar", "atarist", "dos", "dreamcast", "famicom", "gameandwatch", "gamegear", "gb","gbc","gba","gc","mastersystem", "megacd", "megadrive", "msx", "n64", "nds", "pc98", "pcengine", "pcenginecd", "pcfx", "ps2", "psp", "psx", "saturn", "sega32x", "sfc", "wii", "wonderswancolor", "x68000"]]
    # s_list = ["megadrive", "msx", "n64", "nds", "pc98", "pcengine", "pcenginecd", "pcfx", "ps2", "psp", "psx", "saturn", "sega32x", "sfc", "wii", "wonderswancolor", "x68000"]
    # for system_name in s_list:
    #     ss= SSRomsMeta(system_name)
    #     # ss.makeDBTable()
    #     # ss.after_merge_ra_meta()
    #     # ss.check_data()
    #     ss.addTentacleMetaAndFillName()


if __name__ == "__main__":
    # t = 'Ninja Remix (Europe)[aa] '
    # print(removeBucket(t))
    test()