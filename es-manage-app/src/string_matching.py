from thefuzz import process

choices = ["BrainDead 13 (USA) (Disc 1)", "3D Atlas (Europe)", "BrainDead 13 (USA) (Disc 2)", "Blood Angels (Japan)"]
r = process.extractOne("braindead", choices)
print(r)