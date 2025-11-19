"""
Cấu hình Cloudflare R2 Storage
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ===== CLOUDFLARE R2 CONFIGURATION =====
# Lấy thông tin này từ Cloudflare Dashboard > R2 > Manage R2 API Tokens

R2_CONFIG = {
    # Account ID: Cloudflare Dashboard > R2
    'account_id': os.getenv('R2_ACCOUNT_ID', 'your-account-id'),
    
    # API Token: Cloudflare Dashboard > R2 > Manage R2 API Tokens > Create API Token
    'access_key_id': os.getenv('R2_ACCESS_KEY_ID', 'your-access-key-id'),
    'secret_access_key': os.getenv('R2_SECRET_ACCESS_KEY', 'your-secret-access-key'),
    
    # Bucket name: Tạo bucket trong Cloudflare R2 Dashboard
    'bucket_name': os.getenv('R2_BUCKET_NAME', 'smalltree-images'),
    
    # R2 endpoint (format: https://<account-id>.r2.cloudflarestorage.com)
    'endpoint_url': os.getenv('R2_ENDPOINT_URL', ''),  # Sẽ tự động tạo nếu để trống
    
    # Public domain (setup sau khi có bucket)
    # Option 1: R2.dev subdomain (miễn phí): https://<bucket-name>.<account-id>.r2.dev
    # Option 2: Custom domain: https://cdn.smalltree.vn
    'public_url': os.getenv('R2_PUBLIC_URL', ''),
    
    # Region (R2 tự động chọn, không cần thiết lập)
    'region': 'auto',
}

# ===== UPLOAD SETTINGS =====
UPLOAD_CONFIG = {
    # Các loại file được phép upload
    'allowed_extensions': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'jfif'},
    
    # Kích thước tối đa (MB)
    'max_file_size': 10,  # 10MB
    
    # Có resize ảnh trước khi upload không
    'resize_before_upload': True,
    'max_width': 1920,
    'max_height': 1080,
    'quality': 85,  # JPEG quality
    
    # Có xóa ảnh local sau khi upload thành công không
    'delete_local_after_upload': True,
    
    # Có giữ backup local trong X ngày không (0 = xóa ngay)
    'keep_local_days': 7,
}

# ===== AUTO MIGRATION =====
MIGRATION_CONFIG = {
    # Tự động migrate ảnh cũ
    'auto_migrate_old_images': True,
    
    # Chỉ migrate ảnh cũ hơn X ngày
    'min_age_days': 1,
    
    # Số lượng ảnh migrate mỗi lần chạy
    'batch_size': 50,
}

def get_r2_endpoint():
    """Tạo R2 endpoint URL"""
    if R2_CONFIG['endpoint_url']:
        return R2_CONFIG['endpoint_url']
    return f"https://{R2_CONFIG['account_id']}.r2.cloudflarestorage.com"

def get_r2_public_url():
    """Lấy public URL của R2"""
    if R2_CONFIG['public_url']:
        return R2_CONFIG['public_url']
    # Fallback to R2.dev subdomain
    return f"https://{R2_CONFIG['bucket_name']}.{R2_CONFIG['account_id']}.r2.dev"

def is_r2_configured():
    """Kiểm tra R2 đã được cấu hình chưa"""
    return (
        R2_CONFIG['account_id'] and 
        R2_CONFIG['account_id'] != 'your-account-id' and
        R2_CONFIG['access_key_id'] and
        R2_CONFIG['access_key_id'] != 'your-access-key-id' and
        R2_CONFIG['secret_access_key'] and
        R2_CONFIG['secret_access_key'] != 'your-secret-access-key' and
        len(R2_CONFIG['account_id']) > 10  # Account ID phải dài hơn 10 ký tự
    )
