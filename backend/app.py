import os
import uuid
import json
from typing import Dict, Any, List, Optional
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import datetime
from minio import Minio
from minio.error import S3Error
import requests
from io import BytesIO
from dotenv import load_dotenv
from pydantic import BaseModel
from PIL import Image, ImageStat
from ultralytics import YOLO


# 加载环境变量
load_dotenv()

app = FastAPI(title="Image Recognition API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/imagerecognition")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MinIO配置
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9999")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = "images"

# 数据库模型
class ImageRecord(Base):
    __tablename__ = "images"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, index=True)
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)
    recognition_result = Column(Text, nullable=True)
    object_url = Column(String)

    # 添加一个方法，将数据库对象转换为Pydantic模型
    def to_response(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "upload_time": self.upload_time,
            "recognition_result": self.recognition_result,
            "object_url": self.object_url
        }

# 响应模型
class ImageRecognitionResponse(BaseModel):
    id: str
    filename: str
    upload_time: datetime.datetime
    recognition_result: str
    object_url: str

# 依赖项
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_minio_client():
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )

# 对象识别函数
def recognize_objects(img_data):
    """
    使用TensorFlow Hub模型识别图像中的物体
    """
    try:
        # model = YOLO("yolo11n.pt")
        results = [{"class": 'no error'}]
        img = Image.open(BytesIO(img_data))
        # predictions = model(img)
        # for idx in predictions:
        #     names = [idx.names[cls.item()] for cls in idx.boxes.cls.int()]
        #     for name in names:
        #         results.append({"class": name})
        return results
    except Exception as e:
        print(f"对象识别错误: {str(e)}")
        return [{"class": 'gg'}]

# 简化的图像分析函数
def analyze_image(img_data):
    """
    分析图像的基本特征
    """
    try:
        # 将二进制数据转换为图像
        img = Image.open(BytesIO(img_data))
        
        # 获取图像基本信息
        width, height = img.size
        format_name = img.format
        mode = img.mode
        
        # 转换为RGB模式进行颜色分析
        if mode != 'RGB':
            img = img.convert('RGB')
        
        # 获取图像统计信息
        stat = ImageStat.Stat(img)
        avg_color = stat.mean
        
        # 判断图像主色调
        r, g, b = avg_color
        
        # 简单的颜色分类
        color_name = "未知"
        if max(r, g, b) < 60:
            color_name = "黑色"
        elif min(r, g, b) > 200:
            color_name = "白色"
        elif r > max(g, b) + 20:
            color_name = "红色"
        elif g > max(r, b) + 20:
            color_name = "绿色"
        elif b > max(r, g) + 20:
            color_name = "蓝色"
        elif abs(r - g) < 20 and abs(r - b) < 20 and abs(g - b) < 20:
            if r + g + b > 600:
                color_name = "白色"
            elif r + g + b < 300:
                color_name = "黑色"
            else:
                color_name = "灰色"
        elif r > 200 and g > 150 and b < 100:
            color_name = "黄色"
        
        # 判断图像亮度
        brightness = sum(avg_color) / 3
        brightness_level = "中等亮度"
        if brightness < 80:
            brightness_level = "暗"
        elif brightness > 200:
            brightness_level = "亮"
        
        # 识别物体
        object_results = recognize_objects(img_data)
        
        # 构建基本分析结果
        basic_results = [
            {
                "class": "图像尺寸",
                "description": f"{width}x{height}"
            },
            {
                "class": "图像格式",
                "description": format_name
            },
            {
                "class": "主色调",
                "description": color_name
            },
            {
                "class": "亮度",
                "description": brightness_level
            },
            {
                "class": "平均RGB",
                "description": f"R:{int(r)}, G:{int(g)}, B:{int(b)}"
            }
        ]
        
        # 返回分析结果
        return {
            "predictions": basic_results,
            "objects": object_results
        }
    except Exception as e:
        return {"error": str(e)}

# 创建数据库表
@app.on_event("startup")
async def startup_db_client():
    Base.metadata.create_all(bind=engine)
    
    # 确保MinIO存储桶存在
    try:
        minio_client = get_minio_client()
        if not minio_client.bucket_exists(MINIO_BUCKET):
            minio_client.make_bucket(MINIO_BUCKET)
            print(f"Bucket '{MINIO_BUCKET}' created")
        else:
            print(f"Bucket '{MINIO_BUCKET}' already exists")
    except S3Error as e:
        print(f"Error occurred: {e}")

@app.get("/")
def read_root():
    return {"message": "Image Recognition API"}

@app.post("/api/images/")
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # 生成唯一ID
    image_id = str(uuid.uuid4())
    
    try:
        # 读取上传的文件
        file_data = await file.read()
        
        # 上传到MinIO
        minio_client = get_minio_client()
        object_name = f"{image_id}/{file.filename}"
        minio_client.put_object(
            bucket_name=MINIO_BUCKET,
            object_name=object_name,
            data=BytesIO(file_data),
            length=len(file_data),
            content_type=file.content_type
        )
        
        # 生成对象URL
        object_url = f"http://{MINIO_ENDPOINT}/{MINIO_BUCKET}/{object_name}"
        
        # 使用简化的图像分析
        recognition_result = analyze_image(file_data)
        
        # 将结果转换为JSON字符串
        recognition_result_str = json.dumps(recognition_result)
        
        # 存储记录到数据库
        db_record = ImageRecord(
            id=image_id,
            filename=file.filename,
            object_url=object_url,
            recognition_result=recognition_result_str
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        
        # 返回符合响应模型的字典
        return db_record.to_response()
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/images/{image_id}", response_model=ImageRecognitionResponse)
def get_image(image_id: str, db: Session = Depends(get_db)):
    db_record = db.query(ImageRecord).filter(ImageRecord.id == image_id).first()
    if db_record is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return db_record.to_response()

@app.get("/api/images/")
def list_images(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    images = db.query(ImageRecord).offset(skip).limit(limit).all()
    return [img.to_response() for img in images]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)