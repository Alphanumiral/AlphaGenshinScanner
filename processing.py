import main
import string
from multiprocessing import Pool
import os
import tesserocr


#root processing function, uses multiprocessing because processing many images is slow
def processScreenshots(data, processType):
    processPool = Pool(processes=os.cpu_count()-1)
    if processType == "weapons" or processType == "artifacts":
        items = []
        for result in processPool.imap_unordered(processGear, data):
            if type(result) == dict: #prevents accidental addition of null "items"
                items.append(result)
        processPool.close()
        processPool.join()
        return items
    
    elif processType == "achievements":
        achievements = {}
        for id, category, result in processPool.imap_unordered(processAchievements, data):
            if category == "-1":
                print("ERROR: " + str(id))
            #handles both single and multi-step achievements
            for (achievement, res) in zip(id, result):
                if category not in achievements:
                    achievements[category] = {achievement: res}
                else:
                    achievements[category].update({achievement: res})
        processPool.close()
        processPool.join()
        return achievements
    
    elif processType == "characters":
        characters = []
        for result in processPool.imap_unordered(processCharacters, data):
            characters.append(result)
        processPool.close()
        processPool.join()
        return characters

#stat is a tuple of (main stat, value)
#returns key and value, which are a string and float respectively
def formatStat(stat):

    #for stats like CRIT Rate, easiest to split into individual words
    key = stat[0].strip().split(" ")
    value = stat[1]
    #probably terrible sorting system basing which stats are which on the letters they start with
    if key[0][0] == "A": #anemo, atk, atk%
        if key[0][1] == "n":
            key = "anemo_dmg_"
        elif value[-1] == "%":
            key = "atk_"
        else:
            key = "atk"
    elif key[0][0] == "C": #cryo, crit rate, crit damage
        if len(key) == 3:
            key = "cryo_dmg_"
        elif key[1][0] == "R":
            key = "critRate_"
        elif key[1][0] == "D":
            key = "critDMG_"
    elif key[0][0] == "D": #dendro, def, def%
        if key[0][2] == "n":
            key = "dendro_dmg_"
        elif value[-1] == "%":
            key = "def_"
        else:
            key = "def"
    elif key[0][0] == "E": #electro, ER, EM
        if key[0][3] == "m":
            key = "eleMas"
        elif key[0][3] == "r":
            key = "enerRech_"
        elif key[0][3] == "c":
            key = "electro_dmg_"
    elif key[0][0] == "G": #geo
        key = "geo_dmg_"
    elif key[0][0] == "H": #hp, hp%, healing bonus, hydro
        if key[0][1] == "y":
            key = "hydro_dmg_"
        elif key[0][1] == "e":
            key = "heal_"
        elif value[-1] == "%":
            key = "hp_"
        else:
            key = "hp"
    elif key[0][0] == "P": #phys, pyro
        if key[0][1] == "h":
            key = "physical_dmg_"
        elif key[0][1] == "y":
            key = "pyro_dmg_"
    
    #if the value contains a %, we need to strip that off since the info is contained in the key and the value is stored as a float
    if value[-1] == "%":
        value = value[:-1]
    #if a flat stat rolls to be larger than 1000 a comma appears which will prevent the string from converting to a float
    if len(value) > 1:
        if value[1] == ",":
            value = value[0] + value[2:]
    value = float(value)

    return key, value

'''
data is a list that contains different info based on if a weapon or artifact is passed
each element of the list contains a PIL image to be processed using image_to_string

common attributes
data[0] is a string, "weapon" or "artifact"
data[1] is the location screenshot
data[2] is the pixel used to determine if equipment is locked or not
data[3] is the level of the equipment

for weapons
data[4] is the key, the weapon name
data[5] is the refinement

for artifacts
data[4] is the substats and set key
data[5] is the rarity
data[6] is the slot
data[7] is the main stat
'''
def processGear(data):
    with tesserocr.PyTessBaseAPI(path='../Alpha Scanner/tessdata', lang="genshin_eng") as api:
        item = {}
        # COMMON
        #location and lock areas are shared between weapons and artifacts, location was complaining about invalid box/box outside rectangle for specific artifacts and this fixed it for some reason
        api.SetVariable("tessedit_pageseg_mode", "7")
        api.SetImage(data[1])
        locationStr = api.GetUTF8Text()
        api.SetVariable("tessedit_pageseg_mode", "3")
        lockPx = data[2]



        # WEAPONS
        
        if data[0] == "weapon":
            #weapon images
            api.SetImage(data[4])
            keyStr = api.GetUTF8Text()
            api.SetImage(data[3])
            levelStr = api.GetUTF8Text()
            api.SetImage(data[5])
            refinementStr = api.GetUTF8Text()

            #stop data processing once it hits a non-weapon
            if "Enhancement Ore" in keyStr:
                main.handle_q_button()
                return

            #weapon name, extremely weird formatting to try and fit into GOOD format for some outlier weapons that have apostraphes and hyphens
            keyStr = ''.join(filter(lambda x: x.isalpha() or x.isspace() or x == "-", keyStr)) #removes anything that isn't a letter, space, or hyphen
            keyStr = keyStr.replace("-", " ") #replaces hyphen with space
            item["key"] = ''.join(filter(lambda x: x.isalpha(), string.capwords(keyStr))) #capitalize every word, then remove the spaces

            #weapon level and ascension rank: handled based on / position because of OCR weirdness
            #filtering detection to just the xx/xx part of the level because some weapon level spacing had weird results
            levelStr = ''.join(filter(lambda x: x.isdigit() or x == '/', levelStr))
            index = levelStr.find("/")
            item["level"] = int(levelStr[:index])

            ascension = float(levelStr[index+1])-3 #the first number of the denominator - 3 is the same as the ascension rank
            if (ascension > 0):
                item["ascension"] = int(ascension)
            else: #ascension 1 is level 40 max, -30 would make it 10. this means that if it's below 0 it's ascension 0
                item["ascension"] = 0
            
            #refinement
            #easiest way to deal with the refinement rank text not being present is to just check for the 10 weapons it applies to
            nonRefineableWeapons = ["ApprenticesNotes", "BeginnersProtector", "DullBlade", "HuntersBow", "WasterGreatsword", "IronPoint", "OldMercsPal", "PocketGrimoire", "SeasonedHuntersBow", "SilverSword"]
            if item["key"] not in nonRefineableWeapons and len(refinementStr) > 16:
                item["refinement"] = int(refinementStr[16])  
            else:
                item["refinement"] = 1


        
        # ARTIFACTS

        elif data[0] == "artifact":
            #artifact images
            
            api.SetImage(data[4])
            setKeySubstatStr = api.GetUTF8Text()
            rarityImg = data[5]
            api.SetImage(data[6])
            slotKeyStr = api.GetUTF8Text()
            #these 2 images just did not like being read by the standard PSM of 3, interpreting it this way made it work
            api.SetVariable("tessedit_pageseg_mode", "7")
            api.SetImage(data[3])
            levelStr = api.GetUTF8Text()
            api.SetImage(data[7])
            #a new line character was consistently at the end for some reason so this removes it
            mainStatStr = api.GetUTF8Text()[:-1]
            api.SetVariable("tessedit_pageseg_mode", "3")
            substats = [] 
            setKey = ""
            #since the stats and set name are on multiple lines, we need to split them and remove fake, empty lines that may have been in output
            setKeySubstatStr = list(filter(None, setKeySubstatStr.split("\n"))) 
            for entry in setKeySubstatStr:
                #correcting cases of + being read as a "t" and 1 being read as "l" or "I"
                entry = list(entry)
                plusPassed = False
                for k in range (2, len(entry)):
                    if k + 1 < len(entry):
                        if entry[k+1].isdigit() and entry[k] == "t":
                            entry[k] = "+"
                    if entry[k] == "+":
                        plusPassed = True
                    if plusPassed and (entry[k] == "l" or entry[k] == "I" or entry[k] == "H"):
                        entry[k] = "1"
                entry = "".join(entry)
                #accounting for any number of lines on the artifact, only the set name starts with a letter, artifacts usually see a + or -
                if not entry[0].isalpha():
                    key, val = formatStat(entry[2:].split("+")) 
                    substats.append({
                        "key": key,
                        "value": val
                    })
                else:
                    if entry[-1] == ":": #accounting for set names spanning multiple lines
                        setKey += " " + entry
                        break #once the set name is found, any extra lines are set info that we don't care about
                    setKey = entry
            item["substats"] = substats 
            #remove apostraphes, capitalize each word, then remove the spaces
            item["setKey"] = ''.join(filter(lambda x: x.isalpha(), ''.join(filter(lambda x: x != "'", setKey)).title()))

            #rarity, checking pixels to find a star 
            if rarityImg.load()[200, 20][0] > 240:
                item["rarity"] = 5
            elif rarityImg.load()[160, 20][0] > 240:
                item["rarity"] = 4
            elif rarityImg.load()[110, 20][0] > 240:
                item["rarity"] = 3
            elif rarityImg.load()[65, 20][0] > 240:
                item["rarity"] = 2
            else:
                item["rarity"] = 1
            
            #level, just need to remove the + from the scan. easier to screenshot including the + so thinking about spacing isn't a concern
            item["level"] = int(levelStr[1:])

            #slot, we only care about the first word and need it in lowercase
            item["slotKey"] = slotKeyStr.split(' ')[0].lower()

            #main stat, since the formatting in game is different from main stat than substat, some trickery is done to filter which main stat need to be formatted as a percentage stat and which are flat
            #certain lines were getting a number added at the end of them for whatever reason, this removes it
            if mainStatStr[-1].isdigit():
                mainStatStr = mainStatStr[:-1]
            if item["slotKey"] == "plume" or item["slotKey"] == "flower" or mainStatStr == "Elemental Mastery":
                item["mainStatKey"] = formatStat([mainStatStr, "1"])[0]
            else:
                item["mainStatKey"] = formatStat([mainStatStr, "1%"])[0]
        
        #who equipped: found substring because long flavour text might get caught in the image for unequipped weapons and cause noise
        index = locationStr.find("Equipped: ")
        if index != -1:
            item["location"] = locationStr.replace(" ", "")[9:-1]
        else:
            item["location"] = ''

        #reading red value of lock icon pixel
        if lockPx.load()[0,0][0] < 150:
            item["lock"] = "True"
        else:
            item["lock"] = "False"

        return item

def processAchievements(data):
    #always present parts of data
    id = data[0]
    category = data[1]

    with tesserocr.PyTessBaseAPI(path='../Alpha Scanner/tessdata', lang="genshin_eng") as api:
        #processing is different based on the amount of information given
        
        #length of 2 means no result, so the achievement is incomplete
        if len(data) == 2:
            #single achievement, so ID is an integer, multi-step would mean ID is a list
            if len(id) == 1:
                return id, category, [False]
            
            #multi-step achievement, multiple IDs, multiple values
            return id, category, [False, False, False]
        
        #length of 3 means single result
        elif len(data) == 3:
            star = data[2]

            #single achievement, so ID is an integer, multi-step would mean ID is a list
            if len(id) == 1:
                #red value of filled star is 254, red value of incomplete star is ~130, so this should be enough to account for weird variance due to external shaders
                if star.getpixel((14,14))[0] > 240:
                    return id, category, [True]
                return id, category, [False]
            
            #multi-step achievement, multiple IDs, multiple values
            #measuring third, second, then first star to be filled in. if one of them is filled then the ones that come before in achievement progression must be filled. return according completion state
            if star.getpixel((45, 34))[0] > 240:
                return id, category, [True, True, True]
            elif star.getpixel((15, 34))[0] > 240:
                return id, category, [True, True, False]
            elif star.getpixel((30, 15))[0] > 240:
                return id, category, [True, False, False]
            return id, category, [False, False, False]
        
        #length of 5 means multiple results
        elif len(data) == 5:
            stars = data[2]
            categories = data[3]
            categoryName = data[4]

            #loops through the number of results we ended up getting
            for i in range(len(stars)):
                #getting the category name from screenshot, if it returns something extremely short it's probably a mistake so shrink the image and try to scan again
                apiText = ""
                tempCategoryImg = categories[i]
                while len(apiText) < 5 or len(apiText) > len(categoryName):
                    api.SetImage(tempCategoryImg)
                    apiText = api.GetUTF8Text()
                    #no point trying to better the reading if it's already set
                    if apiText.strip() in categoryName:
                        break
                    imgSize = tempCategoryImg.size
                    tempCategoryImg = tempCategoryImg.crop((0, 0, imgSize[0]-5, imgSize[1]))
                #single achievement, so ID is an integer, multi-step would mean ID is a list
                if len(id) == 1:
                    #if the category name we're looking for matches the category name in the screenshot, we know it's the correct achievement and can scan the star accordingly
                    if apiText.strip() in categoryName:
                        if stars[i].getpixel((14,14))[0] > 240:
                            return id, category, [True]
                        return id, category, [False]
                
                #multi-step achievement, multiple IDs, multiple values
                #if the category name we're looking for matches the category name in the screenshot, we know it's the correct achievement and can scan the star accordingly
                if apiText.strip() in categoryName:
                    if stars[i].getpixel((45, 34))[0] > 240:
                        return id, category, [True, True, True]
                    elif stars[i].getpixel((15, 34))[0] > 240:
                        return id, category, [True, True, False]
                    elif stars[i].getpixel((30, 15))[0] > 240:
                        return id, category, [True, False, False]
                    return id, category, [False, False, False]
        print("should never reach")
        return id, "-1", [False]

'''
returns a list of lists containing the screenshots of character information, in order it goes
the character name as a string, without spaces
the stars that will be interpreted as ascension level, a thin line of pixels
level
constellations: a list of images, each to be read as a single pixel that will determine if it is locked or not
talents: a list of images
'''
def processCharacters(data):
    #the character's name was already processed into the necessary format by virtue of how it's represented in game
    character = {
        "key": data[0]
    }


    #reading a pixel from each "star" that represents the ascension level, if they are at that level it would be white (RGB 255/255/255) otherwise RGB 128/128/128
    for i in range(6):
        if data[1].getpixel((i*35, 0))[0] < 250:
            character["ascension"] = i
            break
    #if all the checks pass for the stars the key won't be created, so we know it should be 6
    if "ascension" not in character:
        character["ascension"] = 6


    #same principle as ascension, but checking the lock icon on the constellation. uses a separate loop because of the implementation of ending the checks. they could be combined but i didn't see the point
    for i in range(6):
        if data[3][i].getpixel((0,0))[0] > 250:
            character["constellation"] = i
            break
    if "constellation" not in character:
        character["constellation"] = 6


    with tesserocr.PyTessBaseAPI(path='../Alpha Scanner/tessdata', lang="genshin_eng") as api:
        
        character["talent"] = {}
        talentStr = ["auto", "skill", "burst"]
        for i in range(3):
            api.SetImage(data[4][i])
            talent = api.GetUTF8Text().split("\n")
            try:
                character["talent"][talentStr[i]] = int("".join(filter(lambda x: x.isdigit(), talent[1])))
            except:
                print(character["key"])
                character["talent"][talentStr[i]] = -1
            if "+3" in talent[5]:
                character["talent"][talentStr[i]] -= 3

        
        api.SetVariable("tessedit_pageseg_mode", "7")
        api.SetImage(data[2])
        level = "".join(filter(lambda x: x.isdigit(), api.GetUTF8Text().split("/")[0]))
        character["level"] = int(level)

    return character