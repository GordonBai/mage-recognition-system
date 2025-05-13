import json
import io
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
from PIL import Image

# 加载预训练模型
model = MobileNetV2(weights='imagenet')

def handle(req):
    """
    处理图像识别请求
    """
    try:
        # 检查请求是否为multipart/form-data
        if os.getenv("Http_Content_Type", "").startswith("multipart/form-data"):
            # 解析multipart/form-data请求
            import cgi
            env = {"REQUEST_METHOD": "POST"}
            
            # 设置content-type和content-length
            if "Http_Content_Type" in os.environ:
                env["CONTENT_TYPE"] = os.environ["Http_Content_Type"]
            
            if "Http_Content_Length" in os.environ:
                env["CONTENT_LENGTH"] = os.environ["Http_Content_Length"]
                
            form = cgi.FieldStorage(fp=io.BytesIO(req.encode()), environ=env)
            
            # 获取上传的文件
            if "file" in form:
                fileitem = form["file"]
                if fileitem.file:
                    # 读取图像数据
                    img_data = fileitem.file.read()
                    return process_image(img_data)
            
            return json.dumps({"error": "No file found in request"})
        else:
            # 直接处理二进制图像数据
            return process_image(req)
    except Exception as e:
        return json.dumps({"error": str(e)})

def process_image(img_data):
    """
    处理图像并返回识别结果
    """
    try:
        # 将二进制数据转换为图像
        img = Image.open(io.BytesIO(img_data))
        
        # 调整图像大小为模型输入尺寸
        img = img.resize((224, 224))
        
        # 转换为numpy数组
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        
        # 进行预测
        predictions = model.predict(img_array)
        
        # 解码预测结果
        results = decode_predictions(predictions, top=5)[0]
        
        # 格式化结果
        formatted_results = [
            {
                "class": item[1],
                "description": item[0],
                "confidence": float(item[2])
            }
            for item in results
        ]
        
        return json.dumps({
            "predictions": formatted_results
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

# 本地测试
if __name__ == "__main__":
    with open("test_image.jpg", "rb") as f:
        print(handle(f.read())) 