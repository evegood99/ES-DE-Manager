from thefuzz import process
from thefuzz import fuzz

choices = [ "Shining Force 3 - Scenario 1 - Outo no Kyoshin (Japan) (Demo)", "Shining Force 3 - Scenario 2 - Nerawareta Miko (Japan) (Rev A)", "Shining Force 3 - Scenario 3 - Hyouheki no Jashinguu (Japan)", "Blood Angels (Japan)"]
choices = [
"Doom (Europe)",
"Doom (Japan)",
"Doom (USA)",
"Doom (Europe)",
"Doom (Japan)",
"Doom (USA)",
"Doom (Europe)",
"Doom (Japan) (En)",
"Doom (USA)",
"Doom (Europe)",
"Doom (Japan)",
"Doom (USA)",
"Doom",
"Doom",
"Doom (USA)",
"Doom (U) [!]",
"Doom (U)",
"Doom (U)",
"Doom",
"Doom (USA)",
"Doom (Japan) (En)",
"Doom (E)",
]
choices = set(choices)

src= "Doom (Japan, USA) (En) (Beta) (1994-09-06)"
# src = "Golf Magazine Presents - 36 Great Holes Starring Fred Couples (Japan)"
r = process.extract(src, choices, limit=2)
print(r)

r = process.extract(src, choices, scorer=fuzz.partial_ratio, limit=3)
print(r)
r = process.extract(src, choices, scorer=fuzz.token_sort_ratio, limit=3)
print(r)
r = process.extract(src, choices, scorer=fuzz.WRatio, limit=3)
print(r)

def mix_ratio(src, choices, limit=3):
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

r = mix_ratio(src, choices)
print(r)