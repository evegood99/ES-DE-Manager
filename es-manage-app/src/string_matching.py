from thefuzz import process
from thefuzz import fuzz
import re

choices = [ "Shining Force 3 - Scenario 1 - Outo no Kyoshin (Japan) (Demo)", "Shining Force 3 - Scenario 2 - Nerawareta Miko (Japan) (Rev A)", "Shining Force 3 - Scenario 3 - Hyouheki no Jashinguu (Japan)", "Blood Angels (Japan)"]
choices = [
"Pretty Soldier SailorMoon S (Japan)","Pretty Soldier Sailormoon Demo (J)"

]
choices = set(choices)

src= "Pretty soldier sailormoon S"
# src = "Golf Magazine Presents - 36 Great Holes Starring Fred Couples (Japan)"
r = process.extract(src, choices, limit=2)
print(r)

r = process.extract(src, choices, scorer=fuzz.partial_ratio, limit=3)
print(r)
r = process.extract(src, choices, scorer=fuzz.token_sort_ratio, limit=3)
print(r)
r = process.extract(src, choices, scorer=fuzz.WRatio, limit=3)
print(r)

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

def mix_ratio(src, choices, limit=3):
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
    
    data = list(sc_dict.items())
    data.sort(key=lambda x : x[1], reverse=True)
    return data[:limit]

r = 'aa',mix_ratio(src, choices)
print(r)

print(space_number('Shining Force3 - Scenario1 - Outo no Kyoshin (Japan) (Demo)", "Shining Force3 - Scenario2 - Nerawareta Miko (Japan) (Rev A)'))

print(removeBucket('Ace Combat 04 : Shattered Skies (Japan)(Taikenban)')+'-')