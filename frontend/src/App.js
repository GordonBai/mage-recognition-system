import React, { useState, useRef } from 'react';
import axios from 'axios';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef();

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      setError('');
      
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
    } else {
      setSelectedFile(null);
      setPreview('');
      setError('Please select a valid image file');
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const handleDrop = (event) => {
    event.preventDefault();
    
    if (event.dataTransfer.files && event.dataTransfer.files[0]) {
      const file = event.dataTransfer.files[0];
      if (file.type.startsWith('image/')) {
        setSelectedFile(file);
        setError('');
        
        // Create preview
        const reader = new FileReader();
        reader.onloadend = () => {
          setPreview(reader.result);
        };
        reader.readAsDataURL(file);
      } else {
        setError('Please select a valid image file');
      }
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current.click();
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      setError('Please select an image first');
      return;
    }

    setLoading(true);
    setError('');
    setResults(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axios.post('/api/images/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setLoading(false);
      
      // Parse recognition results
      try {
        // Ensure recognition_result is a string, then parse as JSON
        let resultData = null;
        if (response.data && response.data.recognition_result) {
          resultData = JSON.parse(response.data.recognition_result);
        }
        setResults(resultData);
        console.log("Parsed results:", resultData);
      } catch (e) {
        console.error("Error parsing results:", e);
        setError('Error parsing results: ' + e.message);
      }
    } catch (error) {
      setLoading(false);
      console.error("Upload failed:", error);
      setError('Upload failed: ' + (error.response?.data?.detail || error.message));
    }
  };

  const renderResults = () => {
    if (!results) return null;

    return (
      <div className="results">
        {results.predictions && (
          <div className="basic-info">
            <h3>Basic Information:</h3>
            {results.predictions.map((item, index) => (
              <div key={index} className="result-item">
                <div>
                  <strong>{item.class}</strong>: {item.description}
                </div>
              </div>
            ))}
          </div>
        )}

        {results.objects && results.objects.length > 0 && (
          <div className="object-recognition">
            <h3>Recognized Objects:</h3>
            <div className="object-list">
              {results.objects.map((item, index) => (
                <div key={index} className="result-item">
                  {item.class}
                </div>
              ))}
            </div>
          </div>
        )}

        {results.error && (
          <div className="error">Processing error: {results.error}</div>
        )}
      </div>
    );
  };

  return (
    <div className="container">
      <div className="card">
        <h1>Image Recognition System</h1>
        <p>Upload an image to recognize its content</p>

        <div 
          className="upload-area"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={handleUploadClick}
        >
          {preview ? (
            <img src={preview} alt="Preview" className="image-preview" />
          ) : (
            <p>Click or drag image here to upload</p>
          )}
          <input 
            type="file" 
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept="image/*"
            style={{ display: 'none' }}
          />
        </div>

        {error && <div className="error">{error}</div>}

        <button 
          className="btn" 
          onClick={handleSubmit}
          disabled={!selectedFile || loading}
        >
          {loading ? 'Processing...' : 'Recognize Image'}
        </button>

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
          </div>
        )}

        {renderResults()}
      </div>
    </div>
  );
}

export default App;