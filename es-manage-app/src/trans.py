from googletrans import Translator

text = "Crash â€˜n Burn is a racing game with vehicle-mounted guns and rockets. There is both a Rally mode and a Tournament mode to compete in. In the Rally Mode you race your way through up to 30 tracks with the goal of staying alive and destroying the other contenders while you try and finish in the top three. If you succeed then you advance to the next track."
translator = Translator()
translation = translator.translate(text, dest='ko')
translated_text = translation.text

print(translated_text)