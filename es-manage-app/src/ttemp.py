import os
import csv

BASE_PATH = r'G:\회사데이터\NewWorkSpace\snulibprj3\likesnu_2023'
def pr1():
    file_path1 = r'G:\회사데이터\NewWorkSpace\snulibprj3\likesnu_2023\pilot_analysis\20240712_doi_openAlex_topics.csv'
    file_path2 = r'G:\회사데이터\NewWorkSpace\snulibprj3\likesnu_2023\pilot_analysis\20240712_doi_openAlex_topics_14k.csv'
    file_path3 = r'G:\회사데이터\NewWorkSpace\snulibprj3\likesnu_2023\pilot_analysis\20240712_doi_openAlex_topics_14k_f.csv'

    fp_open1 = open(file_path1, encoding='utf-8-sig')
    fp_open2 = open(file_path2)
    fp_open3 = open(file_path3, 'w', encoding='utf-8')
    writer_out = csv.writer(fp_open3, lineterminator='\n', quotechar='"', quoting=csv.QUOTE_ALL)

    fp1 = csv.DictReader(fp_open1)
    id_doi = {}
    for line in fp1:
        id_doi[line['openAlexID']] = line['doi']


    fp2 = csv.reader(fp_open2)
    for line in fp2:
        o_id = line[0]
        doi = id_doi[o_id]        
        writer_out.writerow([line[0], doi, line[1], line[2]])


def pr2():
    import gzip
    import json

    wos_issn_file_path1 = BASE_PATH+'/pilot_analysis/Arts & Humanities Citation Index (AHCI).csv'
    wos_issn_file_path2 = BASE_PATH+'/pilot_analysis/Emerging Sources Citation Index (ESCI).csv'
    wos_issn_file_path3 = BASE_PATH+'/pilot_analysis/Science Citation Index Expanded (SCIE).csv'
    wos_issn_file_path4 = BASE_PATH+'/pilot_analysis/Social Sciences Citation Index (SSCI).csv'
    issn_set = set([])
    for f_path in [wos_issn_file_path1, wos_issn_file_path2, wos_issn_file_path3, wos_issn_file_path4]:
        fp_open = open(f_path, encoding='utf-8')
        fp = csv.DictReader(fp_open)
        for line in fp:
            issn_set.add(line['ISSN'])
 
    r = os.walk(r'D:\openalex')
    fp_out = open('./pilot_analysis/issn_openalex_data.csv', 'w', encoding='utf-8')
    writer_out = csv.writer(fp_out, lineterminator='\n', quotechar='"', quoting=csv.QUOTE_ALL)
    n = 0
    for i in r:
        f_path = i[0]
        f_name_list = i[2]
        for f_name in f_name_list:
            if f_name[-3:] == '.gz':
                full_path = f_path+'\\'+f_name
                f = gzip.open(full_path, 'r')
                print(full_path)
                for line in f:
                    r = json.loads(line)
                    is_issn = False
                    if r['primary_location'] != None and r['primary_location']['source'] != None and r['primary_location']['source']['issn'] != None:
                        for issn in r['primary_location']['source']['issn']:
                            if issn in issn_set:
                                is_issn = True
                                break
                    if is_issn:
                        oid, title, cit_cnt, issn = r['id'], r['title'], r['cited_by_count'], ";".join(r['primary_location']['source']['issn'])
                        writer_out.writerow([oid, title, issn, cit_cnt])

                    # print(r['primary_location'])
                    # if not 'primary_location' in r:
                        # print(r)
                    # print(r)
                    # oid = r['id']
                    # issn = r['issn_l']
                    # print(oid,issn)
            # r = f.read()
            # print(r)
        # break
    # file_path1 = './pilot_analysis/20240712_doi_openAlex_topics_14k_f.csv'
    # fp_open1 = open(file_path1, encoding='utf-8')
    # for line in fp_open1:
    #     print(line)
    #     break


def pr3():

    file_path1 = BASE_PATH+'/pilot_analysis/issn_openalex_data.csv'
    fp_open1 = open(file_path1, encoding='utf-8')
    fp1 = csv.reader(fp_open1)
    oid_data = {}
    for line in fp1:
        oid_data[line[0]] = (line[1], line[2], line[3])
        

    file_path2 = BASE_PATH+'/pilot_analysis/20240712_doi_openAlex_topics_14k_f.csv'
    fp_open2 = open(file_path2, encoding='utf-8')
    fp2 = csv.reader(fp_open2)
    
    topic_top100_data = {}

    n = 0
    oid_doi_dict = {}
    for line in fp2:
        oid = line[0]
        doi = line[1]
        oid_doi_dict[oid] = doi
        if oid in oid_data:
            t_id_list = line[2].split(';')
            t_prob_list = line[3].split(';')
            for i, t_id in enumerate(t_id_list):
                if t_id in topic_top100_data:
                    if len(topic_top100_data[t_id]) < 20:
                        topic_top100_data[t_id].append((t_prob_list[i], oid))
                    else:
                        topic_top100_data[t_id].sort(reverse=True)
                        if t_prob_list[i] > topic_top100_data[t_id][-1][0]:
                            topic_top100_data[t_id].pop()
                            topic_top100_data[t_id].append((t_prob_list[i], oid))
                else:
                    topic_top100_data[t_id] = [(t_prob_list[i], oid)]

        n += 1
        # if n == 100000:
        #     break

    file_path_out = BASE_PATH+'/pilot_analysis/openAlex_topTopic_data.csv'
    fp_out = open(file_path_out, 'w', encoding='utf-8')
    writer_out = csv.writer(fp_out, lineterminator='\n', quotechar='"', quoting=csv.QUOTE_ALL)
    writer_out.writerow(['oid','doi','title','cited_cnt','issn','topic_id_list','topic_prob_list'])

    oid_prob_topic = {}
    for t_id in topic_top100_data:
        for data in  topic_top100_data[t_id]:
            oid = data[1]
            prob = data[0]
            oid_prob_topic.setdefault(oid, []).append((prob, t_id))
            # (title, cited_cnt, issn) = oid_data[oid]
            # writer_out.writerow([oid, title, issn, cited_cnt, ])
        # print(t_id, topic_top100_data[t_id])


    for oid in oid_prob_topic:
        (title, cited_cnt, issn) = oid_data[oid]
        oid_prob_topic[oid].sort(reverse=True)
        prob_list = []
        t_id_list = []
        for (prob, t_id) in oid_prob_topic[oid]:
            prob_list.append(prob)
            t_id_list.append(t_id)
        writer_out.writerow([oid, oid_doi_dict[oid], title, issn, cited_cnt, ";".join(t_id_list), ";".join(prob_list)])

    print(len(topic_top100_data))


def pr4():
    file_path = r'./pilot_analysis/openAlex_topTopic_data.csv'
    fp = csv.DictReader(open(file_path, encoding='utf-8'))

    file_path_out = r'./pilot_analysis/openAlex_topTopic_data_20.csv'
    fp_out = open(file_path_out, 'w', encoding='utf-8')
    writer_out = csv.writer(fp_out, lineterminator='\n', quotechar='"', quoting=csv.QUOTE_ALL)
    writer_out.writerow(['oid','doi','title','cited_cnt','issn','topic_id_list','topic_prob_list'])

    topic_top_20 = {}
    article_meta = {}
    for line in fp:
        topic_id_list = line['topic_id_list'].split(';')
        topic_prob_list = line['topic_prob_list'].split(';')
        article_meta[line['oid']] = (line['oid'], line['doi'], line['title'], line['issn'], line['cited_cnt'])
        for i, topic_id in enumerate(topic_id_list):
            topic_prob = topic_prob_list[i]
        topic_top_20.setdefault(topic_id, []).append((topic_prob, line['oid']))

    article_data = {}
    for tid in topic_top_20:
        article_list = topic_top_20[tid]
        article_list.sort(reverse=True)
        article_20_list = article_list[:20]
        for (topic_prob, article_oid) in article_20_list:
            article_data.setdefault(article_oid, []).append((topic_prob, tid))

    for article_oid in article_data:
        topic_data = []
        topic_data = article_data[article_oid]
        print(topic_data)
        topic_data.sort(reverse=True)
        prob_list = []
        tid_list = []
        for (topic_prob, tid) in topic_data:
            prob_list.append(topic_prob)
            tid_list.append(tid)
        writer_out.writerow(list(article_meta[article_oid])+[';'.join(tid_list), ';'.join(prob_list)])
        

def test():
    # file_path2 = BASE_PATH+r'\pilot_analysis\20240712_doi_openAlex_topics_14k_f.csv'
    file_path2 = r'G:\회사데이터\NewWorkSpace\snulibprj3\likesnu_2023\pilot_analysis\20240712_doi_openAlex_topics_14k.csv'
    fp = open(file_path2)
    for line in fp:
        print(line)
        break

if __name__ == '__main__':
    pr3()