import sqlite3
from thefuzz import process
from thefuzz import fuzz
import os
from googletrans import Translator
import re

DB_FILE_PATH = "./es-manage-app/src/game.db"

def check_kor(text):
    p = re.compile('[ㄱ-힣]')
    r = p.search(text)
    if r is None:
        return False
    else:
        return True

class Fuzz:

    def __init__(self, system_name):
        self.system_name = system_name
        self.choice_list = []
        self.ready()

    def ready(self):
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
        if score < 89:
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
                if score < 89:
                    # print(rom_name, select_title, score)
                    return {'title':None, 'desc':None}
            else:
                # print(rom_name, select_title, score)
                return {'title':None, 'desc':None}

        return {'title':self.kor_dict[select_title][0], 'desc':self.kor_dict[select_title][1]}

    def test_matching(self, rom_name):
        print(process.extract(rom_name, self.choice_list, scorer=fuzz.partial_ratio))

class MatchingRoms:

    def __init__(self, roms_path, system_name) -> None:
        self.translator = Translator()
        self.roms_path = roms_path
        self.system_name = system_name
        self.choice_list = []
        self.choice_list_kor = []
        self.data_dict = {}
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

        elif ' VI' in rom_name:
            rom_name = rom_name.replace(' VI', ' 6')

        elif ' IV' in rom_name:
            rom_name = rom_name.replace(' IV', ' 4')

        elif ' V' in rom_name:
            rom_name = rom_name.replace(' V', ' 5')

        elif 'III' in rom_name:
            rom_name = rom_name.replace('III', '3')

        elif 'II' in rom_name:
            rom_name = rom_name.replace('II', '2')
        return rom_name

    def trans_1(self, rom_name):
        if ' - ' in rom_name:
            index1 = rom_name.index(' - ')+3
            try:
                index2 = rom_name.index('(',index1)
            except:
                index2 = 9999
            rom_name = rom_name[:index1-3]+' '+rom_name[index2:]
        elif '-' in rom_name:
            index1 = rom_name.index('-')+1
            try:
                index2 = rom_name.index('(',index1)
            except:
                index2 = 9999
            rom_name = rom_name[:index1-1]+' '+rom_name[index2:]

        return rom_name
    
    def trans_2(self, rom_name):
        if ', The ' in rom_name:
            rom_name = rom_name.replace(', The ', ' ')
        return rom_name

    def read_db(self):
        con = sqlite3.connect(DB_FILE_PATH)
        cur = con.cursor()
        if self.system_name in ('3do', '3ds'):
            tb_name = '_'+self.system_name
        else:
            tb_name = self.system_name
        
        r = cur.execute(f"SELECT * from {tb_name}")
        for line in r:
            rom_name = line[0]
            name_kor = line[2]
            comm_name = line[11]
            if name_kor != None:
                self.choice_list_kor.append(name_kor)
                self.data_dict[name_kor] = line

            if comm_name != None:
                self.choice_list.append(comm_name)
                self.data_dict[comm_name] = line

                
            self.data_dict[rom_name] = line
            self.choice_list.append(rom_name)

            tr_num_name = self.trans_nums(rom_name)
            self.choice_list.append(tr_num_name)
            self.data_dict[tr_num_name] = line

            tr_mix_name = self.trans_1(tr_num_name)
            self.choice_list.append(tr_mix_name)
            self.data_dict[tr_mix_name] = line

            tr_1_name = self.trans_1(rom_name)
            self.choice_list.append(tr_1_name)
            self.data_dict[tr_1_name] = line

            tr_2_name = self.trans_2(rom_name)
            self.choice_list.append(tr_2_name)
            self.data_dict[tr_2_name] = line

    def match_process(self, o_file_name):

        if check_kor(o_file_name):
            r = process.extractOne(o_file_name, self.choice_list_kor, scorer=fuzz.partial_ratio)
            if r == None:
                translation = self.translator.translate(o_file_name, dest='en')
                translated_text = translation.text
                file_name = translated_text
            else:
                db_rom_name = r[0]
                score = r[1]
                if score > 79:
                    print(o_file_name, '||| ',self.data_dict[db_rom_name][1], score, 'han')
                    return
        else:
            file_name = o_file_name

        pattern = '([가-힣a-zA-Z][0-9])'
        result = re.findall(pattern, file_name)
        for d in result:
            file_name = file_name.replace(d, d[0]+' '+d[1])

        r = process.extractOne(file_name, self.choice_list)
        db_rom_name = r[0]
        score = r[1]
        # r = process.extract(file_name, self.choice_list, limit=20, scorer=fuzz.partial_ratio)
        # print(r)
        # for rom_name in self.choice_list:
        #     if file_name in rom_name:
        #         print(o_file_name, '||| ',self.data_dict[rom_name][1], score, 'inner matching')
        #         return
                        

        if score >= 93:
            print(o_file_name, '||| ',self.data_dict[db_rom_name][1], score, '1st')
        else:
            tr_num_file_name = self.trans_nums(file_name)
            r = process.extractOne(tr_num_file_name, self.choice_list)
            db_rom_name = r[0]
            score = r[1]
            if score > 94:
                print(o_file_name, '||| ',self.data_dict[db_rom_name][1], score, '2nd')
            else:
                tr_skip_name = self.trans_skip(tr_num_file_name)
                r = process.extract(tr_skip_name, self.choice_list, scorer=fuzz.partial_ratio, limit=5000)
                max_score_list = []
                max_val = 1
                for x in r:
                    if x[1] < max_val:
                        break
                    else:
                        max_val = x[1]
                        max_score_list.append(x[0])
                if len(max_score_list) == 1:
                    db_rom_name = max_score_list[0]
                    score = max_val
                    sec_val = 100
                else:
                    r = process.extractOne(tr_skip_name, max_score_list, scorer=fuzz.token_sort_ratio)
                    # print(max_score_list)
                    # print(r, self.data_dict[r[0]][1])
                    db_rom_name = r[0]
                    score = max_val
                    sec_val = r[1]
                if score > 55 and sec_val > 44:
                    print(o_file_name, '||| ',self.data_dict[db_rom_name][1], score,r[1], '3rd')
                else:
                    print(o_file_name, '||| ',None)

    def run_matching(self, sp_rom_name=None):
        if sp_rom_name != None:
            self.match_process(sp_rom_name)
        
        else:
            for data_name in os.listdir(self.roms_path):
                if os.path.isfile(self.roms_path+'\\'+data_name) and not data_name[-4:] in ('.txt', '.xml', '.dat', '.mp3', '.mp4', '.bak', '.htm', '.pdf', '.png', '.jpg', '.gif', '.bmp', '.exe', '.bat' ,'edia'):
                    o_file_name = data_name[:-4]
                elif os.path.isdir(self.roms_path+'\\'+data_name):
                    o_file_name = data_name
                else:
                    continue
                
                self.match_process(o_file_name)



def test():
    rom_path = r'G:\ROMs\megadrive'
    system_name = 'megadrive'
    mr = MatchingRoms(rom_path, system_name)
    # for line in mr.choice_list:
    #     print(line)
    mr.run_matching()
    

if __name__ == "__main__":
    test()