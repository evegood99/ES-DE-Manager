from thefuzz import process

choices = ["Atlanta Falcons", "New York Jets", "New York Giants", "Dallas Cowboys"]
r = process.extractOne("cowboys", choices)
print(r)