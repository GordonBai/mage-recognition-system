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
      
      // 创建预览
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
    } else {
      setSelectedFile(null);
      setPreview('');
      setError('请选择有效的图片文件');
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
        
        // 创建预览
        const reader = new FileReader();
        reader.onloadend = () => {
          setPreview(reader.result);
        };
        reader.readAsDataURL(file);
      } else {
        setError('请选择有效的图片文件');
      }
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current.click();
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      setError('请先选择一个图片');
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
      
      // 解析识别结果
      try {
        // 确保recognition_result是字符串，然后解析为JSON
        let resultData = null;
        if (response.data && response.data.recognition_result) {
          resultData = JSON.parse(response.data.recognition_result);
        }
        setResults(resultData);
        console.log("解析后的结果:", resultData);
      } catch (e) {
        console.error("解析结果时出错:", e);
        setError('解析结果时出错: ' + e.message);
      }
    } catch (error) {
      setLoading(false);
      console.error("上传失败:", error);
      setError('上传失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const renderResults = () => {
    if (!results) return null;

    return (
      <div className="results">
        {results.predictions && (
          <div className="basic-info">
            <h3>基本信息:</h3>
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
            <h3>识别出的物体:</h3>
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
          <div className="error">处理错误: {results.error}</div>
        )}
      </div>
    );
  };

  return (
    <div className="container">
      <div className="card">
        <h1>图像识别系统</h1>
        <p>上传图片以识别其中的内容</p>

        <div 
          className="upload-area"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={handleUploadClick}
        >
          {preview ? (
            <img src={preview} alt="预览" className="image-preview" />
          ) : (
            <p>点击或拖拽图片到此处上传</p>
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
          {loading ? '处理中...' : '识别图片'}
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