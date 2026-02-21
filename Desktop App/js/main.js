const { app, BrowserWindow, ipcMain } = require("electron");
const { spawn } = require('child_process');
const path = require("path");
const fs = require('fs');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      contextIsolation: true,
      sandbox: false,
      preload: path.join(__dirname, "preload.js"),
      webSecurity: false,
      nodeIntegration: false
    }
  });
  mainWindow.loadFile('index.html');
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});


// --- PYTHON EXTRACTION LOGIC ---
ipcMain.on('run-extraction', (event, videoPath, patientName, cameraData) => {
  console.log("Main Process received video path:", videoPath); // DEBUG 1
  const scriptPath = path.join(__dirname, '../frame_extraction.py');
  const baseOutputDir = path.join(__dirname, '../extracted_frames');

  // Create the folder in Node.js first if it doesn't exist
  if (!fs.existsSync(baseOutputDir)) {
    fs.mkdirSync(baseOutputDir);
    console.log("Created directory:", baseOutputDir); // DEBUG 2
  }

  // Split "Amazon,Pipe Endoscope,4.145" into an array
  const rawData = cameraData || "Unknown,Unknown,0"; 
  const cameraParts = rawData.split(',').map(item => item.trim());
  const make = cameraParts[0] || "Unknown";
  const model = cameraParts[1] || "Unknown";
  const focal = cameraParts[2] || "0";
  console.log(model)
  const pythonCommand = process.platform === 'win32' ? 'python' : 'python3';
  console.log(`Attempting to run: ${pythonCommand} ${scriptPath}`); // DEBUG 3
  // Pass BOTH the video path and the output folder to Python
  const pythonProcess = spawn(pythonCommand, [
    scriptPath, 
    videoPath, 
    baseOutputDir, 
    patientName, 
    make,
    model,
    focal]);


  // ... (stdout/stderr listeners) ...
  pythonProcess.stdout.on('data', (data) => {
    const message = data.toString();
    console.log(`PYTHON LOG: ${data}`); // This shows your print() statements

    if (message.includes("PROGRESS:")) {
        // Extract the number after 'PROGRESS:'
        const percent = message.split("PROGRESS:")[1].trim();
        // Send it to the renderer
        mainWindow.webContents.send('extraction-progress', percent);
    }
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`PYTHON ERROR: ${data}`); // THIS WILL SHOW THE CRASH REASON
  });

  pythonProcess.on('close', (code) => {
    // Send the folder path back to the UI so it knows where to look for images
    event.reply('extraction-finished');
  });
});

