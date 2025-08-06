class ZSParser {
    constructor() {
        this.currentData = null;
        this.currentTempFile = null;
        this.currentFileName = null;
        this.currentFormat = 'csv';
        this.initializeElements();
        this.setupEventListeners();
    }

    initializeElements() {
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('fileInput');
        this.browseBtn = document.getElementById('browseBtn');
        this.formatRadios = document.querySelectorAll('input[name="format"]');
        this.statusSection = document.getElementById('statusSection');
        this.logsSection = document.getElementById('logsSection');
        this.resultsSection = document.getElementById('resultsSection');
        this.fileName = document.getElementById('fileName');
        this.parseStatus = document.getElementById('parseStatus');
        this.dataCount = document.getElementById('dataCount');
        this.logsContent = document.getElementById('logsContent');
        this.resultsPreview = document.getElementById('resultsPreview');
        this.saveBtn = document.getElementById('saveBtn');
        this.copyBtn = document.getElementById('copyBtn');
        this.dragOutZone = document.getElementById('dragOutZone');
        this.resultSummary = document.getElementById('resultSummary');
    }

    setupEventListeners() {
        // File drop events
        this.dropZone.addEventListener('dragover', this.handleDragOver.bind(this));
        this.dropZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.dropZone.addEventListener('drop', this.handleDrop.bind(this));
        this.dropZone.addEventListener('click', () => this.fileInput.click());

        // Browse button
        this.browseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.fileInput.click();
        });

        // File input change
        this.fileInput.addEventListener('change', this.handleFileSelect.bind(this));

        // Format selection
        this.formatRadios.forEach(radio => {
            radio.addEventListener('change', this.handleFormatChange.bind(this));
        });

        // Action buttons
        this.saveBtn.addEventListener('click', this.saveFile.bind(this));
        this.copyBtn.addEventListener('click', this.copyToClipboard.bind(this));

        // Drag out functionality
        this.setupDragOut();
    }

    handleDragOver(e) {
        e.preventDefault();
        this.dropZone.classList.add('drag-over');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.dropZone.classList.remove('drag-over');
    }

    handleDrop(e) {
        e.preventDefault();
        this.dropZone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileSelect(e) {
        if (e.target.files.length > 0) {
            this.processFile(e.target.files[0]);
        }
    }

    handleFormatChange(e) {
        this.currentFormat = e.target.value;
    }

    async processFile(file) {
        if (!this.isValidFile(file)) {
            this.showError('Please select .ndjson or .json files');
            return;
        }

        // Clean up previous temp file if exists
        if (this.currentTempFile) {
            await this.cleanupTempFile();
        }

        this.currentFileName = file.name;
        this.updateStatus('processing', file.name, 'Parsing...');
        this.showSection(this.statusSection);
        this.hideSection(this.logsSection);
        this.hideSection(this.resultsSection);

        try {
            const result = await window.electronAPI.parseFile(file.path, this.currentFormat);
            
            if (result.success) {
                this.currentData = result.data;
                this.currentTempFile = result.outputPath;
                this.currentFormat = result.format || this.currentFormat;
                
                // Calculate record count based on format
                let recordCount;
                if (this.currentFormat === 'csv') {
                    recordCount = result.data.split('\n').length - 2; // -2 for header and empty last line
                } else {
                    recordCount = Array.isArray(result.data) ? result.data.length : 1;
                }
                
                this.updateStatus('success', file.name, 'Parsing completed', recordCount);
                this.showLogs(result.logs);
                this.showResults(result.data);
            } else {
                this.updateStatus('error', file.name, 'Parsing failed');
                this.showLogs(result.logs || result.error);
                this.showError(result.error);
            }
        } catch (error) {
            this.updateStatus('error', file.name, 'Parsing failed');
            this.showError(error.message);
        }
    }

    isValidFile(file) {
        const validExtensions = ['.json', '.ndjson'];
        return validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    }

    updateStatus(status, fileName, statusText, count = null) {
        this.fileName.textContent = fileName;
        this.parseStatus.textContent = statusText;
        this.parseStatus.className = `status-value ${status}`;
        this.dataCount.textContent = count !== null ? count.toLocaleString() : '-';
    }

    showLogs(logs) {
        if (logs) {
            this.logsContent.textContent = logs;
            this.showSection(this.logsSection);
        }
    }

    showResults(data) {
        this.showSection(this.resultsSection);
        
        if (this.currentFormat === 'csv') {
            // CSV format handling
            const lines = data.split('\n').filter(line => line.trim());
            const recordCount = Math.max(0, lines.length - 1); // -1 for header
            this.resultSummary.textContent = `${recordCount} records ready to export`;
            
            // Show preview (first 4 lines including header)
            const previewLines = lines.slice(0, 4);
            this.resultsPreview.textContent = previewLines.join('\n');
        } else {
            // JSON format handling
            const recordCount = Array.isArray(data) ? data.length : 1;
            this.resultSummary.textContent = `${recordCount} records ready to export`;
            
            // Show preview (first 3 items)
            const preview = Array.isArray(data) ? data.slice(0, 3) : [data];
            this.resultsPreview.textContent = JSON.stringify(preview, null, 2);
        }
    }

    showError(message) {
        alert(`Error: ${message}`);
    }

    showSection(element) {
        element.style.display = 'block';
    }

    hideSection(element) {
        element.style.display = 'none';
    }

    async saveFile() {
        if (!this.currentData) return;

        try {
            // Generate suggested filename based on original input and format
            const baseName = this.currentFileName ? 
                this.currentFileName.replace(/\.(ndjson|json)$/i, '') : 
                'parsed_output';
            const extension = this.currentFormat === 'csv' ? 'csv' : 'json';
            const suggestedName = `${baseName}_parsed.${extension}`;
            
            const result = await window.electronAPI.saveFile(this.currentData, suggestedName, this.currentFormat);
            if (result.success) {
                alert(`File saved to: ${result.filePath}`);
            } else {
                this.showError(result.error);
            }
        } catch (error) {
            this.showError(error.message);
        }
    }

    async copyToClipboard() {
        if (!this.currentData) return;

        try {
            let textToCopy;
            if (this.currentFormat === 'csv') {
                textToCopy = this.currentData;
            } else {
                textToCopy = JSON.stringify(this.currentData, null, 2);
            }
            
            await navigator.clipboard.writeText(textToCopy);
            const formatName = this.currentFormat.toUpperCase();
            alert(`${formatName} copied to clipboard`);
        } catch (error) {
            this.showError('Copy failed: ' + error.message);
        }
    }

    setupDragOut() {
        this.dragOutZone.addEventListener('dragstart', (e) => {
            if (!this.currentData) {
                e.preventDefault();
                return;
            }

            let dataString, mimeType, extension;
            if (this.currentFormat === 'csv') {
                dataString = this.currentData;
                mimeType = 'text/csv';
                extension = 'csv';
            } else {
                dataString = JSON.stringify(this.currentData, null, 2);
                mimeType = 'application/json';
                extension = 'json';
            }
            
            const blob = new Blob([dataString], { type: mimeType });
            
            // Generate filename based on original input and format
            const baseName = this.currentFileName ? 
                this.currentFileName.replace(/\.(ndjson|json)$/i, '') : 
                'parsed_output';
            const fileName = `${baseName}_parsed_${new Date().getTime()}.${extension}`;
            
            // Create a temporary URL for the blob
            const url = URL.createObjectURL(blob);
            
            // Set up drag data
            e.dataTransfer.setData('DownloadURL', `${mimeType}:${fileName}:${url}`);
            e.dataTransfer.setData('text/plain', dataString);
            e.dataTransfer.effectAllowed = 'copy';
        });

        // Make the drag-out zone draggable
        this.dragOutZone.draggable = true;

        // Clean up object URLs after drag ends
        this.dragOutZone.addEventListener('dragend', () => {
            // Clean up any created object URLs
            setTimeout(() => {
                // This will be handled by the browser's garbage collection
            }, 1000);
        });
    }

    async cleanupTempFile() {
        if (this.currentTempFile) {
            try {
                await window.electronAPI.cleanupTempFile(this.currentTempFile);
                this.currentTempFile = null;
            } catch (error) {
                console.warn('Failed to cleanup temp file:', error);
            }
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ZSParser();
});