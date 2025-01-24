from flask import Flask, jsonify, request
import scanning, processing, navigation

app = Flask(__name__)

#globals flag so that multiple scan requests don't happen at the same time
currentlyScanning = False
scanData = {}

@app.route("/scan", methods = ['POST'])
def scan():
    global currentlyScanning
    global scanData

    if currentlyScanning:
        return jsonify({"error": "Already scanning"}), 429
    
    currentlyScanning = True

    checks = request.json
    scanData = {}
    if checks["achievementCheck"] == True:
        navigation.moveToScreen("achievements")
        scanData["achievements"] = scanning.scanAchievements()
        navigation.returnToNeutral(2)
    if checks["characterCheck"] == True:
        navigation.moveToScreen("characters")
        scanData["characters"] = scanning.scanCharacters()
        navigation.returnToNeutral(1)
    if checks["weaponCheck"] == True:
        navigation.moveToScreen("weapons")
        scanData["weapons"] = scanning.scanGear("weapon")
        navigation.returnToNeutral(1)
    if checks["artifactCheck"] == True:
        navigation.moveToScreen("artifacts")
        scanData["artifacts"] = scanning.scanGear("artifact")
        navigation.returnToNeutral(1)
    return "a", 200

@app.route("/process", methods = ['POST'])
def process():
    global currentlyScanning
    global scanData
    #dict that at maximum will contain the keys "achievements", "characters", "weapons", and "artifacts"
    keys = scanData.keys()
    
    returnData = {}
    if "achievements" in keys:
        returnData["achievement"] = processing.processScreenshots(scanData["achievements"], "achievements")
    if "characters" in keys:
        returnData["characters"] = processing.processScreenshots(scanData["characters"], "characters")
    if "weapons" in keys:
        returnData["weapons"] = processing.processScreenshots(scanData["weapons"], "weapons")
    if "artifacts" in keys:
        returnData["artifacts"] = processing.processScreenshots(scanData["artifacts"], "artifacts")

    currentlyScanning = False
    return jsonify(returnData)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)