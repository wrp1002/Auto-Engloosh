import requests
from bs4 import BeautifulSoup as bs
import re
import inflect
import json

types = { "n": "noun", "adj": "adjective", "v": "verb" }

engine = inflect.engine()

class Word:
    def __init__(self, word, freq, baseWord, wordType, line):
        self.word = word
        singular = engine.singular_noun(self.word)
        self.singular = singular if singular else word
        self.freq = freq
        self.baseWord = baseWord
        self.type = wordType
        self.line = line
        self.plural = False

        if self.singular != self.word:
            self.plural = True
        

    def __str__(self):
        return self.word + " Singular:" + self.singular + " Freq:" + str(self.freq) + " Type:" + self.type + " Plural:" + str("True" if self.plural else "False") + " BaseWord:" + self.baseWord + " Line:" + self.line


def GetWord(word):
    response = requests.get("http://wordnetweb.princeton.edu/perl/webwn?c=6&sub=Change&o2=1&o0=&o8=1&o1=1&o7=1&o5=&o9=&o6=1&o3=&o4=&i=-1&h=0000000000&s=" + word)
    
    soup = bs(response.text, "html.parser")
    text = soup.text
    
    lines = text.split("\n")
    words = []

    for line in lines:
        match = re.match("^\(([0-9]+)\).+\(([a-z]+)\) ([a-z]+)#[0-9]", line)

        if match:
            freq = int(match.group(1))
            wordType = match.group(2) #types[match.group(2)]
            baseWord = match.group(3)

            newWord = Word(word, freq, baseWord, wordType, line)
            words.append(newWord)
        else:
            match = re.match(".*S: \(([a-z]+)\) ([a-z]+)#[0-9].*", line)

            if match:
                wordType = match.group(1) #types[match.group(1)]
                baseWord = match.group(2)

                newWord = Word(word, 1, baseWord, wordType, line)
                words.append(newWord)


    winner = ''

    for word in words:
        if not winner or word.freq > winner.freq:
            winner = word

    return winner

def LoadTranslations():
    with open("translations.json", "r") as file:
        translations = json.loads(file.read())

    return translations

def PartsOfSpeech(sentence):
    data = {
        "text": sentence,
        "language": "en"
    }
    response = requests.post("https://parts-of-speech.info/tagger/tagger", data=data)

    words = []

    data = json.loads(response.text)["taggedText"]
    parts = data.split(' ')

    print(parts)

    for part in parts:
        if not part: continue

        word = part.split('_')[0].lower()
        wordType = part.split('_')[1]
        words.append({"word": word, "type": wordType})
    
    return words

def TranslateNoun(word, irregular=False):
    translation = word["word"]

    if word["type"] == "NNS":
        translation = engine.singular_noun(word["word"]) or word["word"]

        matches = re.finditer(r"[aeiou]+", translation)
        count = 0
        for match in matches:
            print(match, ":", match.start(), " ", match.end())
            translation = translation[:match.start()] + str("ee" if count % 2 == 0 else "i") + translation[match.end():]
            count += 1

        if irregular:
            translation += "ie"

    else:
        matches = re.finditer(r"[aeiou]+", translation)
        count = 0
        for match in matches:
            print(match.start(), " ", match.end())
            translation = word["word"][:match.start()] + str("oo" if count % 2 == 0 else "ou") + word["word"][match.end():]
            count += 1
        
        if irregular:
            translation += "s"

    if translation == word["word"] and not irregular:
        return TranslateNoun(word, True)

    return translation

def TranslateVerb(word, irregular=False):
    translation = word["word"]

    if irregular:
        translation = re.sub(r"ing$", "ii", translation)
    else:
        translation = re.sub(r"ing$", "ll", translation)
    translation = re.sub(r"ed$", "or", translation)

    translation = re.sub(r"[aeiou]+", "oi", translation)
    
    if irregular:
        translation += "em"

    if translation == word["word"] and not irregular:
        return TranslateVerb(word, True)

    return translation

def TranslateAdj(word, irregular=False):
    translation = re.sub("[aeiou]+", "oa", word["word"])
    if irregular:
        translation += "uf"

    if translation == word["word"] and not irregular:
        TranslateAdj(word, True)

    return translation


translateFunctions = {
    "NN": TranslateNoun,
    "NNS": TranslateNoun,
    "JJ": TranslateAdj,
    "CC": TranslateNoun,
    "VBD": TranslateVerb,
    "VBG": TranslateVerb,
    "VB": TranslateVerb,
    "VBZ": TranslateVerb,
    "RB": TranslateNoun,
    "IN": TranslateNoun,
    "DT": TranslateNoun,
    "TO": TranslateNoun,
    "MD": TranslateVerb,
    "JJ": TranslateVerb,
    "IN": TranslateNoun,
    "PRP": TranslateNoun,
    "WRB": TranslateNoun
}


def InputWord():
    w = input("Enter Word: ")
    #word = GetWord(w)
    print(w, "is a", PartsOfSpeech(w))
    #print(word.word, "is a", word.type, "\n")
    #print(word)
    #print("Translated:", TranslateNoun(word))

def GetTranslation(phrase):
    global translations
    words = PartsOfSpeech(phrase)
    translation = ""

    for word in words:
        if word["word"] in translations:
            print("Translating", word)
            translation += translations[word["word"]] + " "
        elif word["type"] in translateFunctions:
            print("Translating", word)
            translation += translateFunctions[word["type"]](word) + " "
        else:
            print("No translate", word)
            translation += word["word"] + " "

    translation = re.sub("  ", " ", translation)
    translation = re.sub(r" ([.,!?])", r"\1", translation)

    return translation


def Main():
    #while True:
    #    InputWord()
    global translations
    translations = LoadTranslations()

    w = "This is an exciting test to see if the program can translate anyting I type into it. It works by first using our old translations. After that, it uses automatic translation. Cool!"

    translation = GetTranslation(w)

    print()
    print(w)
    print(translation)
    print()
    
    while True:
        w = input("Enter text to translate: ")
        t = GetTranslation(w)
        print()
        print(t)
        print()
        



if __name__=="__main__":
    Main()
    
    
    
    
    
    
    