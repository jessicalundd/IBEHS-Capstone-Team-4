// Reusable function to turn a text file into dropdown options
const populateDropdown = (fileName, elementId) => {
  const text = window.api.readTextFile(fileName);

  if (!text) {
    console.warn(`No content found for ${fileName}`);
    return;
  }

  const items = text.split("\n").map(i => i.trim()).filter(i => i);
  const dropdown = document.getElementById(elementId);

  if (!dropdown) {
    console.error(`Element with ID ${elementId} not found.`);
    return;
  }

  items.forEach(item => {
    const option = document.createElement("option");
    option.value = item;
    option.textContent = item;
    dropdown.appendChild(option);
  });
};

populateDropdown("camera_metadata.txt", "camera-metadata");
populateDropdown("patient_info.txt", "patient-info");

// video extraction
const videoInput = document.getElementById('video-input');
const extractBtn = document.getElementById('extract-btn');

let selectedPath = ""; // This stores the path globally in this file

// 1. Listen for the file selection
let selectedFile = null;

videoInput.addEventListener('change', (e) => {
  selectedFile = e.target.files[0];
  if (selectedFile) {
    console.log("File ready:", selectedFile.name);
    extractBtn.disabled = false;
  }
});

// 2. Listen for the button click to START extraction
extractBtn.addEventListener('click', () => {
  const cameraSelect = document.getElementById('camera-metadata');
  const patientSelect = document.getElementById('patient-info');

  // 1. Get the full line: "Amazon,Pipe Endoscope,4.145"
  const fullCameraString = cameraSelect.options[cameraSelect.selectedIndex].text;
  
  // 2. Safely get Patient Name
  let patientName = patientSelect.options[patientSelect.selectedIndex].text;
  patientName = patientName.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');

  if (selectedFile && fullCameraString) {
      // 3. UI Feedback
      progressBar.style.width = '0%';
      progressText.innerText = 'Starting...';
      
      // 4. Send to bridge - Make sure ALL 3 arguments are here
      window.api.startVideoExtraction(selectedFile, patientName, fullCameraString);
      
      extractBtn.disabled = true;
      extractBtn.innerText = "Extracting...";
  } else {
      alert("Please select both a video and a camera profile.");
  }
});


// 3. Listen for the completion message from Preload
window.api.onExtractionComplete((outputFolder) => {
  alert("Extraction Complete! Images saved to: " + outputFolder);

  // Reset the button
  extractBtn.innerText = "Start Extraction";
  extractBtn.disabled = false;

  // (Optional) Add logic here to display the images in the #gallery div
});


const progressBar = document.getElementById('progress-bar');
const progressContainer = document.getElementById('progress-container');
const progressText = document.getElementById('progress-text');

// Listen for the progress event from the Main process
window.api.onProgress((percent) => {
    // Show the container once progress starts
    progressContainer.style.display = 'block';
    progressText.style.display = 'block';
    
    // Update the width and text
    progressBar.style.width = `${percent}%`;
    progressText.innerText = `${percent}% Complete`;
});

// Reset the bar when extraction finishes
window.api.onExtractionComplete(() => {
    progressText.innerText = "All frames extracted and metadata added";
    extractBtn.disabled = false;
});