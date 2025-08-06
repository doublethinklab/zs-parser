const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs-extra');
const { spawn } = require('child_process');
const os = require('os');

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

function getPythonExecutablePath() {
    let executableName = 'zs-parser';

    if (process.platform === 'win32') {
        executableName += '.exe';
    }

    if (app.isPackaged) {
        // In production, look in the extraResources folder
        return path.join(process.resourcesPath, 'python-dist', executableName);
    } else {
        // In development, look in the python-dist folder
        return path.join(__dirname, 'python-dist', executableName);
    }
}

function handlePythonProcess(process, outputPath, format, resolve) {
    let stdout = '';
    let stderr = '';

    process.stdout.on('data', (data) => {
        stdout += data.toString();
    });

    process.stderr.on('data', (data) => {
        stderr += data.toString();
    });

    process.on('close', async (code) => {
        if (code === 0) {
            try {
                const data = await fs.readFile(outputPath, 'utf8');
                resolve({
                    success: true,
                    data: data,
                    outputPath: outputPath,
                    format: format,
                    logs: stdout
                });
            } catch (error) {
                resolve({
                    success: false,
                    error: `Failed to read output file: ${error.message}`,
                    logs: stderr
                });
            }
        } else {
            resolve({
                success: false,
                error: `Python process exited with code ${code}`,
                logs: stderr || stdout
            });
        }
    });

    process.on('error', (error) => {
        resolve({
            success: false,
            error: `Failed to start Python process: ${error.message}`,
            logs: stderr
        });
    });
}

ipcMain.handle('parse-file', async (event, filePath, format) => {
    const tempDir = os.tmpdir();
    const timestamp = Date.now();
    const outputPath = path.join(tempDir, `parsed_output_${timestamp}.${format === 'csv' ? 'csv' : 'json'}`);

    return new Promise((resolve) => {
        const pythonExecutable = getPythonExecutablePath();
        const args = [filePath, '--output', outputPath, '--format', format];

        console.log('Checking for Python executable:', pythonExecutable);
        console.log('File exists:', fs.existsSync(pythonExecutable));

        if (!fs.existsSync(pythonExecutable)) {
            console.log('Python executable not found, trying Python script...');
            // 在開發環境下，直接使用 Python 腳本
            const pythonScript = path.join(__dirname, 'src', 'zs_parser', 'main.py');
            console.log('Checking for Python script:', pythonScript);
            console.log('Script exists:', fs.existsSync(pythonScript));

            if (fs.existsSync(pythonScript)) {
                console.log('Using Python script:', 'python', [pythonScript, filePath, '--output', outputPath, '--format', format]);
                const pythonProcess = spawn('python', [pythonScript, filePath, '--output', outputPath, '--format', format]);
                handlePythonProcess(pythonProcess, outputPath, format, resolve);
                return;
            } else {
                resolve({
                    success: false,
                    error: `Neither Python executable nor script found.\nExecutable: ${pythonExecutable}\nScript: ${pythonScript}\n\nPlease run 'npm run build-python' to create the Python executable.`,
                    logs: ''
                });
                return;
            }
        }

        console.log('Executing:', pythonExecutable, args.join(' '));
        const process = spawn(pythonExecutable, args);
        handlePythonProcess(process, outputPath, format, resolve);
    });
});

// Handle save file dialog
ipcMain.handle('save-file', async (event, data, suggestedName = 'parsed_output.json', format = 'json') => {
  try {
    const filters = format === 'csv' ? 
      [
        { name: 'CSV Files', extensions: ['csv'] },
        { name: 'All Files', extensions: ['*'] }
      ] :
      [
        { name: 'JSON Files', extensions: ['json'] },
        { name: 'All Files', extensions: ['*'] }
      ];
    
    const result = await dialog.showSaveDialog(mainWindow, {
      filters: filters,
      defaultPath: suggestedName
    });
    
    if (!result.canceled) {
      if (format === 'csv') {
        await fs.writeFile(result.filePath, data, 'utf8');
      } else {
        await fs.writeJson(result.filePath, data, { spaces: 2 });
      }
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