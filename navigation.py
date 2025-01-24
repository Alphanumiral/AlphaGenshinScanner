import pyautogui

def moveToScreen(destination):
    pyautogui.click(1,1) ##TODO: remove (better way of tabbing into game)
    
    #first click in each is the corresponding button on the paimon menu. second is the weapon/artifact tab along the top of the screen, wonders of the world tab for achievements to enable search
    if destination == "achievements":
        pyautogui.click(885, 555) 
        pyautogui.sleep(1)
        pyautogui.click(255, 375)
    elif destination == "weapons":
        pyautogui.click(260, 925)
        pyautogui.sleep(1)
        pyautogui.click(767, 69)
    elif destination == "artifacts":
        pyautogui.click(260, 925)
        pyautogui.sleep(1)
        pyautogui.click(895, 69)
    elif destination == "characters":
        pyautogui.click(669, 720)
        pyautogui.sleep(1)
        


#returning to the paimon screen to go make going into another tab easier
def returnToNeutral(amount):
    pyautogui.press("esc", amount, 1)