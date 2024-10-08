from googletrans import Translator

text = "The Director's Cut is an improved version of the Genesis and SNES game Ballz 3D: Fighting at its Ballziest. Like the original, it's a 3D fighting game where all the characters are made out of balls. Each character has its own moves animations and combos. In the single player mode you first have to fight against all the playable characters after which there are a variety of final bosses such as a tyrannosaurus, kangaroo, scorpion, ostrich and bull. Each boss has a unique fighting style and weak spot. In multiplayer you can fight against friends."
translator = Translator()
translation = translator.translate(text, dest='ko')
translated_text = translation.text

print(translated_text)