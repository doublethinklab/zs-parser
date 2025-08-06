const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  parseFile: (filePath) => ipcRenderer.invoke('parse-file', filePath),
  saveFile: (data, suggestedName) => ipcRenderer.invoke('save-file', data, suggestedName),
  cleanupTempFile: (filePath) => ipcRenderer.invoke('cleanup-temp-file', filePath)
});