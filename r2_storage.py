"""
Cloudflare R2 Storage Handler
Upload và quản lý ảnh trên Cloudflare R2
"""

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import os
from datetime import datetime
from PIL import Image
import io
from config_r2 import (
    R2_CONFIG, UPLOAD_CONFIG, get_r2_endpoint, 
    get_r2_public_url, is_r2_configured
)

class R2Storage:
    def __init__(self):
        """Khởi tạo kết nối R2"""
        if not is_r2_configured():
            print("⚠️  Cảnh báo: R2 chưa được cấu hình. Ảnh sẽ lưu local.")
            self.enabled = False
            return
        
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=get_r2_endpoint(),
                aws_access_key_id=R2_CONFIG['access_key_id'],
                aws_secret_access_key=R2_CONFIG['secret_access_key'],
                config=Config(signature_version='s3v4'),
                region_name=R2_CONFIG['region']
            )
            self.bucket_name = R2_CONFIG['bucket_name']
            self.public_url = get_r2_public_url()
            self.enabled = True
            print(f"✅ Đã kết nối R2: {self.bucket_name}")
        except Exception as e:
            print(f"❌ Lỗi kết nối R2: {str(e)}")
            self.enabled = False
    
    def resize_image(self, image_data, filename):
        """Resize ảnh nếu quá lớn"""
        try:
            img = Image.open(io.BytesIO(image_data))
            
            # Chuyển RGBA sang RGB nếu cần
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize nếu quá lớn
            max_width = UPLOAD_CONFIG['max_width']
            max_height = UPLOAD_CONFIG['max_height']
            
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                print(f"📐 Đã resize ảnh: {filename}")
            
            # Convert sang bytes
            output = io.BytesIO()
            img_format = 'JPEG' if filename.lower().endswith(('.jpg', '.jpeg', '.jfif')) else 'PNG'
            img.save(output, format=img_format, quality=UPLOAD_CONFIG['quality'], optimize=True)
            output.seek(0)
            
            return output.getvalue()
        except Exception as e:
            print(f"⚠️  Không thể resize ảnh: {str(e)}")
            return image_data
    
    def upload_file(self, file_data, filename, folder='activities'):
        """
        Upload file lên R2
        
        Args:
            file_data: bytes hoặc file object
            filename: tên file
            folder: thư mục trên R2 (activities, students, albums...)
        
        Returns:
            str: Public URL của file hoặc None nếu lỗi
        """
        if not self.enabled:
            return None
        
        try:
            # Đọc file data
            if hasattr(file_data, 'read'):
                file_bytes = file_data.read()
                file_data.seek(0)  # Reset pointer
            else:
                file_bytes = file_data
            
            # Resize nếu cần
            if UPLOAD_CONFIG['resize_before_upload']:
                file_bytes = self.resize_image(file_bytes, filename)
            
            # Tạo key (đường dẫn) trên R2
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
            safe_filename = filename.replace(' ', '_')
            key = f"{folder}/{timestamp}_{safe_filename}"
            
            # Xác định content type
            content_type = 'image/jpeg'
            ext = filename.lower().split('.')[-1]
            if ext == 'png':
                content_type = 'image/png'
            elif ext == 'gif':
                content_type = 'image/gif'
            elif ext == 'webp':
                content_type = 'image/webp'
            
            # Upload
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
                CacheControl='public, max-age=31536000',  # Cache 1 năm
            )
            
            # Tạo public URL
            public_url = f"{self.public_url}/{key}"
            print(f"✅ Đã upload: {key}")
            
            return public_url
            
        except ClientError as e:
            print(f"❌ Lỗi upload R2: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ Lỗi không xác định: {str(e)}")
            return None
    
    def delete_file(self, file_url):
        """
        Xóa file từ R2
        
        Args:
            file_url: URL đầy đủ hoặc key của file
        
        Returns:
            bool: True nếu xóa thành công
        """
        if not self.enabled:
            return False
        
        try:
            # Lấy key từ URL
            if file_url.startswith('http'):
                key = file_url.replace(self.public_url + '/', '')
            else:
                key = file_url
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            print(f"🗑️  Đã xóa: {key}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi xóa file: {str(e)}")
            return False
    
    def file_exists(self, key):
        """Kiểm tra file có tồn tại trên R2 không"""
        if not self.enabled:
            return False
        
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False
    
    def list_files(self, folder='', max_keys=1000):
        """Liệt kê files trong folder"""
        if not self.enabled:
            return []
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=folder,
                MaxKeys=max_keys
            )
            
            if 'Contents' not in response:
                return []
            
            files = []
            for obj in response['Contents']:
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'url': f"{self.public_url}/{obj['Key']}"
                })
            
            return files
            
        except Exception as e:
            print(f"❌ Lỗi list files: {str(e)}")
            return []
    
    def get_storage_stats(self):
        """Lấy thống kê dung lượng sử dụng"""
        if not self.enabled:
            return {'total_size': 0, 'total_files': 0}
        
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            if 'Contents' not in response:
                return {'total_size': 0, 'total_files': 0}
            
            total_size = sum(obj['Size'] for obj in response['Contents'])
            total_files = len(response['Contents'])
            
            return {
                'total_size': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'total_size_gb': round(total_size / 1024 / 1024 / 1024, 2),
                'total_files': total_files
            }
            
        except Exception as e:
            print(f"❌ Lỗi lấy stats: {str(e)}")
            return {'total_size': 0, 'total_files': 0}

# Singleton instance
_r2_storage = None

def get_r2_storage():
    """Lấy R2Storage instance (singleton)"""
    global _r2_storage
    if _r2_storage is None:
        _r2_storage = R2Storage()
    return _r2_storage
