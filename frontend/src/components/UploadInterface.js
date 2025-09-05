import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, 
  FileText, 
  X, 
  CheckCircle, 
  AlertCircle, 
  Loader2,
  Cloud,
  FolderOpen,
  BarChart3
} from 'lucide-react';

const UploadInterface = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    const pdfFiles = droppedFiles.filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length !== droppedFiles.length) {
      alert('Only PDF files are allowed');
    }
    
    setFiles(prev => [...prev, ...pdfFiles]);
  }, []);

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(prev => [...prev, ...selectedFiles]);
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;

    setUploading(true);
    setUploadResults(null);

    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });

      const response = await fetch('/api/upload/courses', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const results = await response.json();
      setUploadResults(results);
      
      if (results.success) {
        setFiles([]);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadResults({
        success: false,
        message: 'Upload failed. Please try again.',
        courses_processed: 0,
        failed_files: ['Upload failed due to network error']
      });
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="h-full bg-gray-50 dark:bg-gray-900 p-6 overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Upload Course Materials
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Upload PDF files to add new course information to the AI knowledge base.
            The system will automatically extract and index the content.
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                <FolderOpen className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Ready to Upload</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{files.length}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-green-100 dark:bg-green-900/20 rounded-lg">
                <Cloud className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Size</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {formatFileSize(files.reduce((total, file) => total + file.size, 0))}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
                <BarChart3 className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Processing Status</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {uploading ? 'Running' : 'Ready'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Upload Area */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <div
            className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
              dragActive
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 hover:bg-gray-50 dark:hover:bg-gray-700/50'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              multiple
              accept=".pdf"
              onChange={handleFileSelect}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              disabled={uploading}
            />
            
            <div className="space-y-4">
              <div className="flex justify-center">
                <div className={`p-4 rounded-full ${
                  dragActive 
                    ? 'bg-blue-100 dark:bg-blue-900/30' 
                    : 'bg-gray-100 dark:bg-gray-700'
                }`}>
                  <Upload className={`w-8 h-8 ${
                    dragActive 
                      ? 'text-blue-600 dark:text-blue-400' 
                      : 'text-gray-400'
                  }`} />
                </div>
              </div>
              
              <div>
                <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  {dragActive ? 'Drop your files here' : 'Choose files or drag & drop'}
                </p>
                <p className="text-gray-600 dark:text-gray-400">
                  PDF files only. Multiple files supported.
                </p>
              </div>
              
              <button
                type="button"
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
                disabled={uploading}
              >
                <Upload className="w-5 h-5 mr-2" />
                Select Files
              </button>
            </div>
          </div>
        </div>

        {/* File List */}
        {files.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Selected Files ({files.length})
              </h3>
              <button
                onClick={uploadFiles}
                disabled={uploading || files.length === 0}
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-green-600 hover:bg-green-700 disabled:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors duration-200"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Cloud className="w-5 h-5 mr-2" />
                    Upload All
                  </>
                )}
              </button>
            </div>
            
            <div className="space-y-3">
              <AnimatePresence>
                {files.map((file, index) => (
                  <motion.div
                    key={`${file.name}-${index}`}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <FileText className="w-5 h-5 text-red-500" />
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {file.name}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {formatFileSize(file.size)}
                        </p>
                      </div>
                    </div>
                    
                    <button
                      onClick={() => removeFile(index)}
                      disabled={uploading}
                      className="p-2 text-gray-400 hover:text-red-500 transition-colors duration-200 disabled:opacity-50"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        )}

        {/* Upload Results */}
        {uploadResults && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`rounded-xl border p-6 ${
              uploadResults.success
                ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
            }`}
          >
            <div className="flex items-start space-x-3">
              {uploadResults.success ? (
                <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400 mt-0.5" />
              ) : (
                <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400 mt-0.5" />
              )}
              
              <div className="flex-1">
                <h3 className={`text-lg font-medium mb-2 ${
                  uploadResults.success
                    ? 'text-green-900 dark:text-green-100'
                    : 'text-red-900 dark:text-red-100'
                }`}>
                  {uploadResults.success ? 'Upload Successful!' : 'Upload Failed'}
                </h3>
                
                <p className={`mb-4 ${
                  uploadResults.success
                    ? 'text-green-800 dark:text-green-200'
                    : 'text-red-800 dark:text-red-200'
                }`}>
                  {uploadResults.message}
                </p>
                
                {uploadResults.courses_processed > 0 && (
                  <div className="mb-4">
                    <p className="text-sm font-medium text-green-800 dark:text-green-200">
                      Successfully processed: {uploadResults.courses_processed} courses
                    </p>
                  </div>
                )}
                
                {uploadResults.failed_files && uploadResults.failed_files.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-red-800 dark:text-red-200 mb-2">
                      Failed files:
                    </p>
                    <ul className="text-sm text-red-700 dark:text-red-300 space-y-1">
                      {uploadResults.failed_files.map((error, index) => (
                        <li key={index} className="flex items-start space-x-2">
                          <span className="block w-1 h-1 bg-red-600 rounded-full mt-2 flex-shrink-0"></span>
                          <span>{error}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default UploadInterface;
