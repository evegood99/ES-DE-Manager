import sqlite3
from thefuzz import process
from thefuzz import fuzz
import os
from googletrans import Translator
import re
import zlib, hashlib

DB_FILE_PATH = "./es-manage-app/src/games_meta.db"

def removeBucket(t_str):
    pattern = '(\([^)]+\)|(\[+[^)]+\]))'
    # pattern = '(\s\([^)]+\))'
    result = re.findall(pattern, t_str)
    for find_r in result:
        t_str = t_str.replace(find_r[0],'')
    return t_str.strip()

def space_number(src):
    pattern = '([가-힣a-zA-Z][0-9])'
    result = re.findall(pattern, src)
    for d in result:
        src = src.replace(d, d[0]+' '+d[1])
    return src

def mix_ratio(src, choices, limit=1):
    src = space_number(src)
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

def check_kor(text):
    p = re.compile('[ㄱ-힣]')
    r = p.search(text)
    if r is None:
        return False
    else:
        return True

def get_hash(file_path):
    f = open(file_path, 'rb')
    data = f.read()
    f.close()    
    return {'crc':hex(zlib.crc32(data))[2:], 'md5':hashlib.md5(data).hexdigest(), 'sha1':hashlib.sha1(data).hexdigest()}


class MatchingRoms:

    def __init__(self, roms_path, system_name) -> None:
        self.translator = Translator()
        self.con = sqlite3.connect(DB_FILE_PATH)
        self.roms_path = roms_path
        self.system_name = system_name
        self.rom_file_name = {}
        self.rom_file_name_kor = {}
        self.rm_bucket_name = {}
        self.norm_game_name = {}
        self.md5_data = {}
        self.read_db()

    def trans_skip(self, rom_name):
        if '(' in rom_name and rom_name.index('(') > 5:
            rom_name = rom_name[:rom_name.index('(')]
            rom_name = rom_name.strip()
            return rom_name
        elif '[' in rom_name and rom_name.index('[') > 5:
            rom_name = rom_name[:rom_name.index('[')]
            rom_name = rom_name.strip()
            return rom_name
        else:
            return rom_name

    def trans_nums(self, rom_name):

        if ' VIII' in rom_name:
            rom_name = rom_name.replace(' VIII', ' 8')

        elif ' VII' in rom_name:
            rom_name = rom_name.replace(' VII', ' 7')

        elif ' IX' in rom_name:
            rom_name = rom_name.replace(' IX', ' 9')

        elif ' VI' in rom_name:
            rom_name = rom_name.replace(' VI', ' 6')

        elif ' IV' in rom_name:
            rom_name = rom_name.replace(' IV', ' 4')

        elif ' V' in rom_name:
            rom_name = rom_name.replace(' V', ' 5')

        elif 'III' in rom_name:
            rom_name = rom_name.replace(' III', '3')

        elif 'II' in rom_name:
            rom_name = rom_name.replace(' II', '2')
        return rom_name

    def get_roms_info(self, rom_id):
        cur = self.con.cursor()
        tb_name = 'roms_'+self.system_name
        
        r = cur.execute(f"SELECT * from {tb_name} WHERE id = '{str(rom_id)}'")
        return r.fetchone()

    def read_db(self):
        cur = self.con.cursor()
        tb_name = 'roms_'+self.system_name
        
        r = cur.execute(f"SELECT * from {tb_name}")
        for line in r:
            es_src_name_list_str = line[1]
            rom_file_name = line[2][:-4]
            game_name = line[9]
            if line[6] != None:
                file_md5 = line[6].lower()
            else:
                file_md5 = None
            rom_id = line[0]
            game_id = line[8]

            if es_src_name_list_str != None:
                for es_src_name in es_src_name_list_str.split(';;'):
                    self.rom_file_name[es_src_name] = rom_id
                    self.rm_bucket_name[removeBucket(es_src_name)] = rom_id
            
            if rom_file_name != None:
                self.rom_file_name[rom_file_name] = rom_id
                self.rm_bucket_name[removeBucket(rom_file_name)] = rom_id

            if game_name != None:
                self.norm_game_name[game_name] = game_id

            if file_md5 != None:
                self.md5_data[file_md5] = rom_id

    def match_process(self, file_name, test=False):
        if not test:
            file_full_path = self.roms_path+'\\'+file_name
            if os.path.isfile(file_full_path):
                r_hash = get_hash(file_full_path)
                md5_val = r_hash['md5'].lower()
                if md5_val in self.md5_data:
                    rom_id = self.md5_data[md5_val]
                    target_data = self.get_roms_info(rom_id)[2]
                    print(file_name, '||', target_data, 'md5')
                    return rom_id
                file_name = file_name[:-4]

        is_name_kor = False
        if check_kor(file_name):
            is_name_kor = True
            translation = self.translator.translate(file_name, dest='en')
            translated_text = translation.text
            translated_file_name = translated_text
            target_db_data = self.rom_file_name_kor
        else:
            target_db_data = self.rom_file_name
        target_data = mix_ratio(file_name, target_db_data.keys())
        target_name = target_data[0]
        target_prob = target_data[1]

        if target_prob >= 80:
            print(file_name, '||', target_data, 'rom')
            rom_id = target_db_data[target_name] 
            # print(file_name, '||', self.get_roms_info(rom_id)[2])

        elif is_name_kor:
            target_data = mix_ratio(translated_file_name, self.norm_game_name.keys())
            target_name = target_data[0]
            target_prob = target_data[1]
            if target_prob >= 80:
                print(file_name, '||', target_data, 'game')

        else:
            file_name = removeBucket(file_name)
            target_data = mix_ratio(file_name, self.norm_game_name.keys())
            target_name = target_data[0]
            target_prob = target_data[1]
            if target_prob >= 80:
                print(file_name, '||', target_data, 'game')
            else:
                target_data = mix_ratio(file_name, self.rm_bucket_name.keys())
                target_name = target_data[0]
                target_prob = target_data[1]
                if target_prob >= 80:            
                    print(file_name, '||', target_data, 'rm_name_rom')
                else:
                    print(file_name, '|| None', target_data)


        #     r = process.extractOne(o_file_name, self.choice_list_kor, scorer=fuzz.partial_ratio)
        #     if r == None:
        #         translation = self.translator.translate(o_file_name, dest='en')
        #         translated_text = translation.text
        #         file_name = translated_text
        #     else:
        #         db_rom_name = r[0]
        #         score = r[1]
        #         if score > 79:
        #             print(o_file_name, '||| ',self.data_dict[db_rom_name][1], score, 'han')
        #             return
        # else:
        #     file_name = o_file_name

        # pattern = '([가-힣a-zA-Z][0-9])'
        # result = re.findall(pattern, file_name)
        # for d in result:
        #     file_name = file_name.replace(d, d[0]+' '+d[1])

        # r = process.extractOne(file_name, self.choice_list)
        # db_rom_name = r[0]
        # score = r[1]
        # # r = process.extract(file_name, self.choice_list, limit=20, scorer=fuzz.partial_ratio)
        # # print(r)
        # # for rom_name in self.choice_list:
        # #     if file_name in rom_name:
        # #         print(o_file_name, '||| ',self.data_dict[rom_name][1], score, 'inner matching')
        # #         return
                        

        # if score >= 93:
        #     print(o_file_name, '||| ',self.data_dict[db_rom_name][1], score, '1st')
        # else:
        #     tr_num_file_name = self.trans_nums(file_name)
        #     r = process.extractOne(tr_num_file_name, self.choice_list)
        #     db_rom_name = r[0]
        #     score = r[1]
        #     if score > 94:
        #         print(o_file_name, '||| ',self.data_dict[db_rom_name][1], score, '2nd')
        #     else:
        #         tr_skip_name = self.trans_skip(tr_num_file_name)
        #         r = process.extract(tr_skip_name, self.choice_list, scorer=fuzz.partial_ratio, limit=5000)
        #         max_score_list = []
        #         max_val = 1
        #         for x in r:
        #             if x[1] < max_val:
        #                 break
        #             else:
        #                 max_val = x[1]
        #                 max_score_list.append(x[0])
        #         if len(max_score_list) == 1:
        #             db_rom_name = max_score_list[0]
        #             score = max_val
        #             sec_val = 100
        #         else:
        #             r = process.extractOne(tr_skip_name, max_score_list, scorer=fuzz.token_sort_ratio)
        #             # print(max_score_list)
        #             # print(r, self.data_dict[r[0]][1])
        #             db_rom_name = r[0]
        #             score = max_val
        #             sec_val = r[1]
        #         if score > 55 and sec_val > 44:
        #             print(o_file_name, '||| ',self.data_dict[db_rom_name][1], score,r[1], '3rd')
        #         else:
        #             print(o_file_name, '||| ',None)

    def run_matching(self, sp_rom_name=None):
        if sp_rom_name != None:
            self.match_process(sp_rom_name, test=True)
        
        else:
            for data_name in os.listdir(self.roms_path):
                if os.path.isfile(self.roms_path+'\\'+data_name) and not data_name[-4:] in ('.txt', '.xml', '.dat', '.mp3', '.mp4', '.bak', '.htm', '.pdf', '.png', '.jpg', '.gif', '.bmp', '.exe', '.bat' ,'edia'):
                    o_file_name = data_name
                elif os.path.isdir(self.roms_path+'\\'+data_name):
                    o_file_name = data_name
                else:
                    continue
                
                self.match_process(o_file_name)



def test():
    rom_path = r'G:\ROMs\sfc'
    system_name = 'sfc'
    mr = MatchingRoms(rom_path, system_name)
    # r = mr.get_roms_info(1025140)
    # print(r)
    # for line in mr.choice_list:
    #     print(line)
    mr.run_matching()
    
# def test2():
#     get_roms_info()

if __name__ == "__main__":
    test()