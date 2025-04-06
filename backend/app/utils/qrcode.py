import qrcode
import os
import base64
from io import BytesIO
import uuid

def generate_qrcode(data, name=None):
    """
    生成二维码并返回文件路径
    
    参数:
        data: 要编码的数据
        name: 可选的文件名前缀
    
    返回:
        生成的二维码URL
    """
    if name is None:
        name = f"qrcode_{uuid.uuid4().hex}"
    
    # 创建二维码
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 保存到内存
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    # Base64编码
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    data_url = f"data:image/png;base64,{img_str}"
    
    # 在实际应用中，您可能会将图像保存到静态文件目录或云存储
    # 这里我们返回data URL作为简化示例
    return data_url

def verify_qrcode(qrcode_data, expected_data):
    """
    验证二维码数据
    
    参数:
        qrcode_data: 从二维码扫描获取的数据
        expected_data: 预期的数据
        
    返回:
        验证是否成功
    """
    return qrcode_data == expected_data 