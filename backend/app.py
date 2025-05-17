import os
import uuid
import json
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import datetime
from minio import Minio
from minio.error import S3Error
from io import BytesIO
from dotenv import load_dotenv
from pydantic import BaseModel
from PIL import Image, ImageStat
from ultralytics import YOLO
import logging
logging.basicConfig(level=logging.INFO)


# Load environment variables
load_dotenv()

app = FastAPI(title="Image Recognition API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/imagerecognition")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MinIO configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9999")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = "images"

# Database model
class ImageRecord(Base):
    __tablename__ = "images"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, index=True)
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)
    recognition_result = Column(Text, nullable=True)
    object_url = Column(String)

    # Add a method to convert database object to Pydantic model
    def to_response(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "upload_time": self.upload_time,
            "recognition_result": self.recognition_result,
            "object_url": self.object_url
        }

# Response model
class ImageRecognitionResponse(BaseModel):
    id: str
    filename: str
    upload_time: datetime.datetime
    recognition_result: str
    object_url: str

# Dependencies
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

# Object recognition function
def recognize_objects(img_data):
    """
    Use TensorFlow Hub model to recognize objects in images
    """
    try:
        model = YOLO("yolo11n.pt")
        results = []
        img = Image.open(BytesIO(img_data))
        predictions = model(img)
        for idx in predictions:
            names = [idx.names[cls.item()] for cls in idx.boxes.cls.int()]
            scores = [cls.item() for cls in idx.boxes.conf]
            for i in range(len(names)):
                name = names[i]
                score = scores[i]
                curr = {}
                curr["class"] = name+": "+str(score)
                results.append(curr)
        return results
    except Exception as e:
        print(f"Object recognition error: {str(e)}")
        return [{"class": 'gg'}]

# Simplified image analysis function
def analyze_image(img_data):
    """
    Analyze basic features of the image
    """
    try:
        # Convert binary data to image
        img = Image.open(BytesIO(img_data))
        
        # Get basic image information
        width, height = img.size
        format_name = img.format
        mode = img.mode
        
        # Convert to RGB mode for color analysis
        if mode != 'RGB':
            img = img.convert('RGB')
        
        # Get image statistics
        stat = ImageStat.Stat(img)
        avg_color = stat.mean
        
        # Determine main color tone
        r, g, b = avg_color
        
        # Simple color classification
        color_name = "Unknown"
        if max(r, g, b) < 60:
            color_name = "Black"
        elif min(r, g, b) > 200:
            color_name = "White"
        elif r > max(g, b) + 20:
            color_name = "Red"
        elif g > max(r, b) + 20:
            color_name = "Green"
        elif b > max(r, g) + 20:
            color_name = "Blue"
        elif abs(r - g) < 20 and abs(r - b) < 20 and abs(g - b) < 20:
            if r + g + b > 600:
                color_name = "White"
            elif r + g + b < 300:
                color_name = "Black"
            else:
                color_name = "Gray"
        elif r > 200 and g > 150 and b < 100:
            color_name = "Yellow"
        
        # Determine image brightness
        brightness = sum(avg_color) / 3
        brightness_level = "Medium brightness"
        if brightness < 80:
            brightness_level = "Dark"
        elif brightness > 200:
            brightness_level = "Bright"
        
        # Recognize objects
        object_results = recognize_objects(img_data)
        
        # Build basic analysis results
        basic_results = [
            {
                "class": "Image dimensions",
                "description": f"{width}x{height}"
            },
            {
                "class": "Image format",
                "description": format_name
            },
            {
                "class": "Main color",
                "description": color_name
            },
            {
                "class": "Brightness",
                "description": brightness_level
            },
            {
                "class": "Average RGB",
                "description": f"R:{int(r)}, G:{int(g)}, B:{int(b)}"
            }
        ]
        
        # Return analysis results
        return {
            "predictions": basic_results,
            "objects": object_results
        }
    except Exception as e:
        return {"error": str(e)}

# Create database tables
@app.on_event("startup")
async def startup_db_client():
    Base.metadata.create_all(bind=engine)
    
    # Ensure MinIO bucket exists
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
    
    # Generate unique ID
    image_id = str(uuid.uuid4())
    
    try:
        # Read uploaded file
        file_data = await file.read()
        
        # Upload to MinIO
        minio_client = get_minio_client()
        object_name = f"{image_id}/{file.filename}"
        minio_client.put_object(
            bucket_name=MINIO_BUCKET,
            object_name=object_name,
            data=BytesIO(file_data),
            length=len(file_data),
            content_type=file.content_type
        )
        
        # Generate object URL
        object_url = f"http://{MINIO_ENDPOINT}/{MINIO_BUCKET}/{object_name}"
        
        # Use simplified image analysis
        recognition_result = analyze_image(file_data)
        
        # Convert results to JSON string
        recognition_result_str = json.dumps(recognition_result)
        
        # Store record in database
        db_record = ImageRecord(
            id=image_id,
            filename=file.filename,
            object_url=object_url,
            recognition_result=recognition_result_str
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        
        # Return dictionary matching response model
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

@app.get("/healthcheck")
def health_check(db: Session = Depends(get_db)):
    # Test PostgreSQL with connection pool check
    try:
        db.execute(text("SELECT 1"))  # Use SQLAlchemy text() for raw SQL
        db.commit()  # Explicit commit to verify connection
    except Exception as e:
        return {"database_error": str(e)}, 503

    # Test MinIO with timeout
    try:
        minio_client = get_minio_client()
        if not minio_client.bucket_exists(MINIO_BUCKET):
            return {"minio_error": f"Bucket '{MINIO_BUCKET}' not found"}, 503
    except Exception as e:
        return {"minio_error": str(e)}, 503

    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)