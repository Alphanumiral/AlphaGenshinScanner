const { app, BrowserWindow } = require('electron')
const axios = require('axios');
var fs = require('fs')

function createWindow () {
    const win = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    })
    var python = require('child_process').spawn('py', ['backend.py'])
    
    python.stdout.on('data', function (data) {
        console.log("data: ", data.toString('utf8'))
    })
    python.stderr.on('data', (data) => {
        console.log(`stderr: ${data}`); // when error
    })
    
    win.loadFile('index.html');
}



async function beginScan(achievementCheck, mergeCheck, mergeFile, characterCheck, weaponCheck, artifactCheck) {
    
    var startTime = Date.now()
    var scanTime
    var mergeData

    //no point doing anything if we're not gonna scan any data
    if (!achievementCheck && !characterCheck && !weaponCheck && !artifactCheck) return
    if (mergeCheck){
        if (mergeFile){
            const reader = new FileReader()
            reader.onload = function(event) {
                mergeData = JSON.parse(event.target.result);
                console.log(mergeData)
            }
            reader.readAsText(mergeFile)
        }   
        else{
            console.log("no file selected")
        }
    }
    //calls the scan, data stored in backend to be used in processing post request
    await axios.post('http://127.0.0.1:5000/scan', {achievementCheck, characterCheck, weaponCheck, artifactCheck})
    scanTime = Date.now()
    //time in seconds
    console.log("time to scan = " + Math.floor((scanTime - startTime)/1000))
    
    //processing the previously scanned data, response is a JSON object with the keys "achievements", "characters", "weapons", "artifacts"
    response = await axios.post('http://127.0.0.1:5000/process')
    //time in seconds
    console.log("time to process = " + Math.floor((Date.now() - scanTime)/1000))
    console.log("total time = " + Math.floor((Date.now() - startTime)/1000))
    
    //export formatting
    var exportJSON = {
        "format" : "GOOD",
        "version" : 1,
        "source" : "Alpha Scanner"
    }

    var date = new Date()
    var fileName =  date.getFullYear() + "_" + date.getMonth() + "_" + date.getDate() + "_" + date.getHours() + "_" + date.getMinutes() + "_" + date.getSeconds()
    var fileDirectory = "./ScanData/"

    
    if (achievementCheck) {
        achExport = JSON.parse(JSON.stringify(exportJSON))
        if(mergeCheck){
            for (const key in mergeData){
                achExport[key] = mergeData[key]
            }
        }
        achExport["achievement"] = response.data["achievement"]
        fs.writeFile(fileDirectory + fileName + "_Ach.json", JSON.stringify(achExport, null, 2), function(err, file){
            if (err) throw err
        })
        if (!characterCheck && !weaponCheck && !artifactCheck) return
        
    }
    if (characterCheck) {
        exportJSON["characters"] = response.data["characters"]
        fileName += "_Char"
    }
    if (weaponCheck) {
        exportJSON["weapons"] = response.data["weapons"]
        fileName += "_Weap"
    }
    if (artifactCheck) {
        exportJSON["artifacts"] = response.data["artifacts"]
        fileName += "_Arti"
    }

    fileName += ".GOOD.json"

    fs.writeFile(fileDirectory + fileName, JSON.stringify(exportJSON, null, 2), function(err, file){
        if (err) throw err
    })

}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        const { exec } = require('child_process')
        exec('taskkill /f /t /im python.exe', (err, stdout, stderr) => { 
            if (err) {  
                console.log(err) 
                return
            } 
            console.log(`stdout: ${stdout}`) 
            console.log(`stderr: ${stderr}`)
        })
        app.quit()
    }
})

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow()
    }
})
