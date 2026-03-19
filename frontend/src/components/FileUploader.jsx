import React, { useState, useCallback } from 'react';
import { UploadCloud, FileSpreadsheet, Loader2 } from 'lucide-react';

const FileUploader = ({ onUpload, isUploading, progress }) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file) => {
    // Check if it's a valid extension
    const name = file.name.toLowerCase();
    if (name.endsWith('.csv') || name.endsWith('.xlsx') || name.endsWith('.xls')) {
      onUpload(file);
    } else {
      alert('Please upload a .csv or .xlsx file');
    }
  };

  return (
    <div className="uploader-container">
      <div 
        className={`drop-zone ${isDragging ? 'active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <FileSpreadsheet className="drop-icon" />
        <div>
          <h2>Upload BOM File</h2>
          <p className="text-secondary mt-2">Drag and drop your Excel (.xlsx) or CSV file here</p>
        </div>
        
        <input 
          type="file" 
          id="file-upload" 
          style={{ display: 'none' }} 
          accept=".csv, .xlsx, .xls"
          onChange={handleChange}
          disabled={isUploading}
        />
        <label htmlFor="file-upload" className="upload-btn" style={{marginTop: '8px', display: 'inline-flex'}}>
          <UploadCloud size={20} />
          Browse Files
        </label>
      </div>
      
      {isUploading && (
        <div className="panel" style={{ width: '100%' }}>
          <div className="flex items-center justify-between">
            <h3 className="flex items-center gap-2">
              <Loader2 className="animate-spin text-accent-blue" size={20} /> 
              Analyzing Multi-Component Data
            </h3>
            <span className="badge badge-neutral">AI Processing</span>
          </div>
          
          <div className="progress-container">
            <div className="progress-bar-bg">
              <div 
                className="progress-bar-fill" 
                style={{ width: `${progress.percent}%` }}
              ></div>
            </div>
            <div className="progress-text">
              <span>{Math.round(progress.percent)}% Complete</span>
              <span>{progress.current} / {progress.total} | Current: {progress.part}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUploader;
