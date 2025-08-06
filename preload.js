const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  parseFile: (filePath, format) => ipcRenderer.invoke('parse-file', filePath, format),
  saveFile: (data, suggestedName, format) => ipcRenderer.invoke('save-file', data, suggestedName, format),
  cleanupTempFile: (filePath) => ipcRenderer.invoke('cleanup-temp-file', filePath)
});