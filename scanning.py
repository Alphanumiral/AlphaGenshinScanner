from PIL import Image
import pyperclip
import pyautogui
import requests
import bettercam
from tesserocr import PyTessBaseAPI
import platform
import time

import main

'''
takes a string that determines the type of gear to be scanned, either "weapon" or "artifact"
returns a list of list, with the content of each list being whether it is a weapon or artifact, and then screenshots of varying info needed for processing
a weapon has the screenshots location, lock, level, key, refinement. respectively that is the character it is currently equipped to, the pixel of the lock icon to determine if it is locked or not, the level of the weapon, the name of the weapon, and the refinement level of the weapon
an artifact has the screenshot location, lock, level, setkeysubstat, rarity, slotkey, mainstat. the first 3 are the same as the weapon and the remaining are the set name and substats, what rarity the artifact is, the slot it occupies, and the main stat of the artifact
'''
def scanGear(gearType):
    #creating instance of bettercam
    camera = bettercam.create()

    #checking how many items to click through as a limiter
    with PyTessBaseAPI(path='../Alpha Scanner/tessdata', lang="genshin_eng") as api:
        quantityImg = Image.fromarray(camera.grab(region=(2095, 47, 2403, 78)))
        api.SetImage(quantityImg)
        quantityStr = api.GetUTF8Text()
    quantity = int(''.join(c for c in quantityStr if c.isdigit())[:-4])

    #info stored to be sent to processing later
    screenshotData = []
    while quantity > 0 :
        #to account for limitations on scrolling if there are less than 25 items remaining, start on the row where items haven't been scanned yet
        offset = 0
        if quantity < 23:
            if quantity > 14:
                offset = 1
            elif quantity > 6:
                offset = 2
            else:
                offset = 3
        for i in range(offset, 4):
            #if there are less than 8 items remaining, only scan until the final item
            for j in range(min(quantity, 8)):
                if main.break_loop_flag:
                    break
                pyautogui.click(240+j*195,260+i*233)

                #an issue was occurring where camera.grab would sometimes return None, so if it returns none it'll try again before continuing
                fullSct = None
                while (fullSct is None):
                    fullSct = camera.grab(region=(1776, 165, 2406, 1280))
                fullImg = Image.fromarray(fullSct)
                
                # COMMON
                #location area is shared between artifacts
                locationImg = fullImg.crop((75, 1047, 624, 1102))
                

                # WEAPONS


                if gearType == "weapon":
                    #weapon images
                    lockPx = fullImg.crop((554, 425, 555, 426)) 
                    keyImg = fullImg.crop((0, 0, 583, 65))
                    levelImg = fullImg.crop((11, 410, 175, 441)) 
                    refinementImg = fullImg.crop((61, 461, 384, 504))

                    screenshotData.append([
                        "weapon",
                        locationImg,
                        lockPx,
                        levelImg,
                        keyImg,
                        refinementImg
                    ])


                
                # ARTIFACTS

                elif gearType == "artifact":
                    #artifact images
                    lockPx = fullImg.crop((509, 425, 510, 426)) 
                    setKeySubstatImg = fullImg.crop((0, 464, 602, 768))
                    rarityImg = fullImg.crop((0, 307, 232, 372)) 
                    levelImg = fullImg.crop((15, 410, 80, 440))  #10, 408, 80, 445
                    slotKeyImg = fullImg.crop((0, 82, 307, 122))
                    mainStatImg = fullImg.crop((4, 199, 304, 230)) 
                    screenshotData.append([
                        "artifact",
                        locationImg,
                        lockPx,
                        levelImg,
                        setKeySubstatImg,
                        rarityImg,
                        slotKeyImg,
                        mainStatImg
                    ])
                
                quantity -= 1

            if main.break_loop_flag:
                break
        if main.break_loop_flag:
                break
        if (quantity > 0):
            #stop scroll drift
            if (len(screenshotData) % 384 == 0):
                pyautogui.scroll(1)
            #24 px per scroll input, 932 px to move down 4 items in inventory, 936 px scrolled in 39 scrolls. adjust +1 every 6 sets of 4 rows, or once every 192 items
            for i in range (39): 
                pyautogui.scroll(-1)
    return screenshotData

'''
returns a list of lists, with the content of each list varying based on the type of achievement scanned
[id] is the id(s) of the achievement. if it was a single step achievement the list will contain 1 element while a multi-step achievement will contain 3 elements
category is the key in the achievementDB such as 0 being the category "Wonders of the World", passed as a string to be used as the key for processsing later
star or [stars] is the screenshot of the star area which will be used to determine if an achievement is complete
[categories] is the screenshots of the category names for multiple results, so we can find which stars we need to check
category name is self explanatory. used for checking against the text contained in the [categories] for verification

if a single step achievement had no results in the search, the list is [[id], category]
if a single single step achievement was found, the list is [[id], category, star]
if multiple single step achievements were found, the list is [[id], category, [stars], [categories], category name]
if a multi step achievement had no results in the search, the list is [[id], category]
if a single multi step achievement was found, the list is [[id], category, star]
if multiple multi step achievements were found, the list is [[id], category, [stars], [categories], category name]
'''
def scanAchievements():
    #creating instance of bettercam
    camera = bettercam.create()

    #getting achievement database from paimon.moe repo
    req = requests.get("https://raw.githubusercontent.com/MadeBaruna/paimon-moe/main/src/data/achievement/en.json")
    if req.status_code == requests.codes.ok:
        achievementDB = req.json()

    achievementData = []
    '''
    
    achievementDB is a dict full of integer:category pairs
    a category is a dictionary with the keys name and achievements, which are self explanatory
    achievements is mostly a list of dict, with each dict containing the keys id, name, desc, reward, and ver, but we only care about the first 2
    within the achievements list, multi-step achievements are a list of dict. every dict is the same for every key except the id and sometimes the reward
    '''
    
    with PyTessBaseAPI(path='../Alpha Scanner/tessdata', lang="genshin_eng") as api:
        api.SetVariable("tessedit_pageseg_mode", "7")
        for category in achievementDB:
            for achievement in achievementDB[category]["achievements"]:
                if main.break_loop_flag:
                    main.handle_q_button()
                    return
                
                #clear text in search
                pyautogui.click(600,180)
                #start typing in search again
                pyautogui.click(600,180)
                #type the achievement into the search, for multi step achievement they all share a name so we can just take the first one
                #this was originally done using typewrite from pyautogui, but apparently some of the characters can't be written using typewrite like the em dash in T—T—T—Timberhochwandi
                if type(achievement) == dict:
                    pyperclip.copy(achievement["name"])
                else:
                    pyperclip.copy(achievement[0]["name"])
                
                if platform.system() == "Windows" or platform.system() == "Linux":
                    pyautogui.hotkey("ctrl", "v")
                else:
                    pyautogui.hotkey("command", "v") #untested, i don't have a mac :^)
                #search for the achievement
                pyautogui.click(780, 180)

                #reading the number of matches
                matches = None
                while matches is None:
                    matches = camera.grab(region=(983, 210, 1200, 241))
                matches = Image.fromarray(matches)
                api.SetImage(matches)
                matches = api.GetUTF8Text()
                if len(matches) < 12:
                    matches = 0
                else:
                    #weird ocr stuff
                    if matches[11] == "Z":
                        matches = 2
                    else:
                        if matches[0] != "M":
                            matches = matches[1:]

                        try:
                            matches = int(matches[11])
                        except:
                            print(matches)
                            print(type(matches))

                #small delay because the actual achievement text takes time to load
                time.sleep(0.1)
                

                
                #achievementData results are formatted as a list for easier sorting later based on list lengths

                #single-step achievement
                if type(achievement) == dict:
                    sct = None
                    #if no match, we know the achievement isn't complete
                    if matches == 0:
                        achievementData.append([[achievement["id"]], str(category)])
                    #with 1 match we just care about the star for the achievement found in the search and the id of the achievement we are checking
                    elif matches == 1:
                        while sct is None:
                            sct = camera.grab(region=(1066, 396, 1094, 424))
                        star = Image.fromarray(sct)
                        achievementData.append([[achievement["id"]], str(category), star])
                    #matches > 1. we need to screenshot every star and every category returned, and pass it with the category and id of the achievement to check against later
                    else:
                        while sct is None:
                            sct = camera.grab(region=(985, 275, 1900, 275 + 221 * matches))
                        sct = Image.fromarray(sct)
                        stars = []
                        categories = []
                        for i in range(matches):
                            stars.append(sct.crop((81, 121 + 221*i, 109, 149 + 221*i)))
                            categories.append(sct.crop((17, 10 + 221*i, 915, 42 + 221*i)))
                        achievementData.append([[achievement["id"]], str(category), stars, categories, achievementDB[category]["name"]])

                #multi-step achievement
                elif type(achievement) == list:
                    sct = None
                    #since each step has a separate id, we need to mark each one separately
                    ids = []
                    for step in achievement:
                        ids.append(step["id"])

                    #if no match, we know the achievement isn't complete
                    if matches == 0:
                        achievementData.append([ids, str(category)])

                    #with 1 match we just care about the stars of the achievement found in the search and the list of IDs for every step of the achievement
                    elif matches == 1:
                        while sct is None:
                            sct = camera.grab(region=(1051, 381, 1109, 430))
                        star = Image.fromarray(sct)
                        achievementData.append([ids, str(category), star])

                    #matches > 1. we need to screenshot every set of stars and every category returned, and pass it with the category and list of IDs for every step of the achievement to check against later
                    else:
                        while sct is None:
                            sct = camera.grab(region=(985, 275, 1900, 275 + 221 * matches))
                        sct = Image.fromarray(sct)
                        stars = []
                        categories = []
                        for i in range(matches):
                            stars.append(sct.crop((66, 106 + 221*i, 124, 155 + 221*i)))
                            categories.append(sct.crop((17, 10 + 221*i, 915, 42 + 221*i)))
                        achievementData.append([ids, str(category), stars, categories, achievementDB[category]["name"]])
                else:
                    print("wtf achievement type is this?")
        return achievementData
    
'''
returns a list of lists containing the screenshots of character information, in order it goes
the character name as a string, without spaces
the stars that will be interpreted as ascension level, a thin line of pixels
level
constellations: a list of images, each to be read as a single pixel that will determine if it is locked or not
talents: a list of images containing all the info in the top left corner when you click on a talent
'''
def scanCharacters():
    charData = []
    camera = bettercam.create()

    
    with PyTessBaseAPI(path='../Alpha Scanner/tessdata', lang="genshin_eng") as api:
        #clicking the right arrow to cycle characters loops, so we need a marker (the first character that was read) at which we stop
        stopChar = ""
        charName = ""
        #helps reading names. more noise is introduced but it's easy to remove
        api.SetVariable("tessedit_pageseg_mode", "7")
        #in case something goes wrong and the stopchar isn't being reached or read properly
        emergency = 150
        scannedNames = []
        while emergency > 0:
            char = []
            
            #clicking attribute menu
            pyautogui.click(225, 200)
            time.sleep(0.75)
            fullSct = None
            while fullSct is None:
                fullSct = camera.grab(region=(1950, 180, 2400, 320))
            fullImg = Image.fromarray(fullSct)
            

            #short names sometimes get read incorrectly and shrinking the area helps
            shrinkMod = 0
            #dummy data to enter while loop
            charName = "1"
            while charName.isalpha() == False or len(charName) < 4:
                if shrinkMod > 325: 
                    print("reading issue in char scan")
                    #trying to grab again to see if different background will help
                    fullSct = None
                    while (fullSct is None):
                        fullSct = camera.grab(region=(1950, 180, 2400, 320))
                    fullImg = Image.fromarray(fullSct)
                    shrinkMod = 0
                charNameImg = fullImg.crop((0, 0, 450 - shrinkMod, 50))
                api.SetImage(charNameImg)
                #particle effects sometimes introduce characters into the scan that need to be removed
                charName = "".join(filter(lambda x: x.isalpha(), api.GetUTF8Text().rstrip()))
                shrinkMod += 1
                time.sleep(1/60)
            #loop has finished, every character has been scanned
            if charName == stopChar or charName in scannedNames:
                break
            char.append(charName)
            scannedNames.append(charName)
            
            #line where the ascension stars for characters are, pixels will be read to check level
            rarityImg = fullImg.crop((20, 73, 200, 74))
            char.append(rarityImg)
            levelImg = fullImg.crop((7, 100, 265, 137))
            char.append(levelImg)

            #clicking constellations menu
            pyautogui.click(225, 485)
            time.sleep(1)

            #screenshotting all the constellation icons along the right side of the screen then reading the pixels where a lock icon would be
            fullSct = None
            while fullSct is None:
                fullSct = camera.grab(region=(1990, 370, 2140, 1115))
            fullImg = Image.fromarray(fullSct)
            conImgs = [
                fullImg.crop((30, 0, 31, 1)),
                fullImg.crop((100, 145, 101, 146)),
                fullImg.crop((145, 295, 146, 296)),
                fullImg.crop((145, 445, 146, 446)),
                fullImg.crop((100, 595, 101, 596)),
                fullImg.crop((0, 740, 1, 741))
            ]
            char.append(conImgs)

            #clicking talent menu
            pyautogui.click(225, 575)
            time.sleep(0.75)

            #click talent, wait for it to load, grab area where the text would be. grabbing more text than expected because of variance in location and which constellations affect which talents
            talentImgs = []

            #auto
            pyautogui.click(2337, 225)
            time.sleep(0.2)
            fullSct = None
            while fullSct is None:
                fullSct = camera.grab(region=(45, 185, 730, 425))
            fullImg = Image.fromarray(fullSct)
            talentImgs.append(fullImg)

            #skill
            pyautogui.click(2337, 340)
            time.sleep(1/60)
            fullSct = None
            while fullSct is None:
                fullSct = camera.grab(region=(45, 185, 730, 425))
            fullImg = Image.fromarray(fullSct)
            talentImgs.append(fullImg)

            #burst
            pyautogui.click(2337, 455)
            #exception exists because the "special sprint" is the 3rd talent in the list despite not having levels
            if (charName == "Mona" or charName == "KamisatoAyaka"):
                pyautogui.click(2337, 570)
            time.sleep(1/60)
            fullSct = None
            while fullSct is None:
                fullSct = camera.grab(region=(45, 185, 730, 425))
            fullImg = Image.fromarray(fullSct)
            talentImgs.append(fullImg)
            
            char.append(talentImgs)


            charData.append(char)
            #only the case on the first cycle of the loop, when this character's name is read again stop the loop
            if stopChar == "":
                stopChar = charName
            #next char, click twice to escape the talent menu
            pyautogui.click(2469, 720)
            time.sleep(1/60)
            pyautogui.click(2469, 720)
            emergency -= 1
    
    return charData