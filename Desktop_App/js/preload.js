// importing modules
const { contextBridge, ipcRenderer, webUtils } = require("electron");
const fs = require("fs");
const path = require("path");

contextBridge.exposeInMainWorld("api", {
  // Now accepts a specific filename so you can use it for many files
  readTextFile: (fileName) => {
    try {
      // Assuming your text files are in a folder named 'data' relative to preload.js
      const filePath = path.join(__dirname, "../", fileName);
      return fs.readFileSync(filePath, "utf-8");
    } catch (err) {
      console.error("File read error:", err);
      return ""; // Return empty string if file doesn't exist
    }
  },

  startVideoExtraction: (file, patientName, cameraData) => {
    const path = webUtils.getPathForFile(file);
    ipcRenderer.send('run-extraction', path, patientName, cameraData);
  },

  // MAKE SURE THIS EXACT NAME IS HERE:
  onExtractionComplete: (callback) => {
    ipcRenderer.removeAllListeners('extraction-finished');
    ipcRenderer.on('extraction-finished', (event, message) => callback(message));
  },

  onProgress: (callback) => ipcRenderer.on('extraction-progress', (event, value) => callback(value))

});

