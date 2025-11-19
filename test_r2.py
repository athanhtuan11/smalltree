"""
Test kết nối Cloudflare R2
Chạy: python test_r2.py
"""

from r2_storage import get_r2_storage
from config_r2 import is_r2_configured, R2_CONFIG
import io

print("="*60)
print("🧪 TEST CLOUDFLARE R2 CONNECTION")
print("="*60)

# 1. Kiểm tra cấu hình
print("\n1️⃣  Kiểm tra cấu hình...")
if is_r2_configured():
    print("✅ R2 đã được cấu hình")
    print(f"   - Account ID: {R2_CONFIG['account_id'][:10]}...")
    print(f"   - Bucket: {R2_CONFIG['bucket_name']}")
    print(f"   - Public URL: {R2_CONFIG.get('public_url', 'Chưa thiết lập')}")
else:
    print("❌ R2 chưa được cấu hình!")
    print("   Vui lòng:")
    print("   1. Copy .env.example thành .env")
    print("   2. Điền thông tin R2 vào .env")
    print("   3. Hoặc sửa trực tiếp config_r2.py")
    exit(1)

# 2. Khởi tạo R2
print("\n2️⃣  Khởi tạo kết nối R2...")
r2 = get_r2_storage()
if not r2.enabled:
    print("❌ Không thể kết nối R2!")
    print("   Kiểm tra lại:")
    print("   - Account ID đúng chưa")
    print("   - Access Key + Secret Key đúng chưa")
    print("   - Bucket đã được tạo chưa")
    exit(1)
print("✅ Kết nối R2 thành công")

# 3. Test upload
print("\n3️⃣  Test upload file...")
try:
    # Tạo file test
    test_content = b"This is a test file from SmallTree"
    test_file = io.BytesIO(test_content)
    
    # Upload
    url = r2.upload_file(test_file, 'test.txt', folder='test')
    
    if url:
        print(f"✅ Upload thành công!")
        print(f"   URL: {url}")
    else:
        print("❌ Upload thất bại!")
        exit(1)
        
except Exception as e:
    print(f"❌ Lỗi upload: {str(e)}")
    exit(1)

# 4. Test list files
print("\n4️⃣  Test list files...")
try:
    files = r2.list_files(folder='test', max_keys=10)
    print(f"✅ Tìm thấy {len(files)} file trong folder 'test'")
    if files:
        print("   Files:")
        for f in files:
            print(f"   - {f['key']} ({f['size']} bytes)")
except Exception as e:
    print(f"❌ Lỗi list files: {str(e)}")

# 5. Test delete
print("\n5️⃣  Test delete file...")
try:
    if url:
        success = r2.delete_file(url)
        if success:
            print("✅ Xóa file test thành công")
        else:
            print("⚠️  Không thể xóa file test")
except Exception as e:
    print(f"❌ Lỗi delete: {str(e)}")

# 6. Storage stats
print("\n6️⃣  Thống kê storage...")
try:
    stats = r2.get_storage_stats()
    print(f"✅ Dung lượng đang dùng:")
    print(f"   - Tổng: {stats['total_size_gb']:.2f} GB")
    print(f"   - Số file: {stats['total_files']}")
except Exception as e:
    print(f"⚠️  Không lấy được stats: {str(e)}")

print("\n" + "="*60)
print("✅ TẤT CẢ TEST HOÀN TẤT")
print("="*60)
print("\n📝 HÀNH ĐỘNG TIẾP THEO:")
print("1. Upload ảnh mới sẽ tự động lên R2")
print("2. Chạy: python migrate_to_r2.py (để chuyển ảnh cũ)")
print("3. Giám sát: Cloudflare Dashboard > R2 > Metrics")
print("\n💡 MẸO:")
print("- Chi phí: ~360đ/GB/tháng, download MIỄN PHÍ")
print("- 1GB/ngày = ~11,000đ/tháng")
print("- Cloudflare có CDN toàn cầu, nhanh hơn VPS")
