const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs-extra');
const { spawn } = require('child_process');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets', 'icon.png'),
    titleBarStyle: 'default'
  });

  mainWindow.loadFile('index.html');
  
  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Handle file parsing
ipcMain.handle('parse-file', async (event, filePath) => {
  try {
    return new Promise((resolve, reject) => {
      const pythonPath = 'python3';
      const scriptPath = path.join(__dirname, 'src', 'zs_parser', 'main.py');
      
      // Generate unique output filename based on input file
      const inputFileName = path.basename(filePath, path.extname(filePath));
      const timestamp = Date.now();
      const outputFileName = `${inputFileName}_parsed_${timestamp}.json`;
      const outputPath = path.join(__dirname, outputFileName);
      
      const process = spawn(pythonPath, [scriptPath, filePath, '--output', outputPath]);
      
      let stdout = '';
      let stderr = '';
      
      process.stdout.on('data', (data) => {
        stdout += data.toString();
      });
      
      process.stderr.on('data', (data) => {
        stderr += data.toString();
      });
      
      process.on('close', (code) => {
        if (code === 0) {
          try {
            // Read the generated output file
            const result = fs.readJsonSync(outputPath);
            resolve({
              success: true,
              data: result,
              logs: stderr,
              outputPath: outputPath // Include output path for cleanup
            });
          } catch (err) {
            reject({
              success: false,
              error: `Failed to read output: ${err.message}`,
              logs: stderr
            });
          }
        } else {
          reject({
            success: false,
            error: `Parser failed with code ${code}`,
            logs: stderr
          });
        }
      });
      
      process.on('error', (err) => {
        reject({
          success: false,
          error: `Failed to start parser: ${err.message}`,
          logs: stderr
        });
      });
    });
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
});

// Handle save file dialog
ipcMain.handle('save-file', async (event, data, suggestedName = 'parsed_output.json') => {
  try {
    const result = await dialog.showSaveDialog(mainWindow, {
      filters: [
        { name: 'JSON Files', extensions: ['json'] },
        { name: 'All Files', extensions: ['*'] }
      ],
      defaultPath: suggestedName
    });
    
    if (!result.canceled) {
      await fs.writeJson(result.filePath, data, { spaces: 2 });
      return { success: true, filePath: result.filePath };
    }
    
    return { success: false, error: 'Save cancelled' };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Handle cleanup of temporary files
ipcMain.handle('cleanup-temp-file', async (event, filePath) => {
  try {
    if (fs.existsSync(filePath)) {
      await fs.remove(filePath);
      return { success: true };
    }
    return { success: true }; // File doesn't exist, consider it cleaned
  } catch (error) {
    return { success: false, error: error.message };
  }
});