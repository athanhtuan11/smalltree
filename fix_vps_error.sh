#!/bin/bash
# Script sửa lỗi Internal Server Error nhanh trên VPS

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}======================================================"
echo "   SMALLTREE - FIX INTERNAL SERVER ERROR"
echo "======================================================${NC}"
echo ""

APP_DIR="/var/www/smalltree-website"
cd $APP_DIR || exit 1

# 1. Kiểm tra app có đang chạy không
echo -e "${GREEN}[1/6] Kiểm tra trạng thái app...${NC}"
sudo supervisorctl status smalltree

# 2. Xem 20 dòng log lỗi cuối
echo -e "\n${GREEN}[2/6] Log lỗi gần đây:${NC}"
if [ -f "logs/gunicorn.err.log" ]; then
    tail -n 20 logs/gunicorn.err.log
else
    echo -e "${RED}Không tìm thấy log file${NC}"
fi

# 3. Kiểm tra database
echo -e "\n${GREEN}[3/6] Kiểm tra database...${NC}"
source venv/bin/activate
export FLASK_APP=run.py

python3 << 'PYEOF'
try:
    from app import create_app
    from app.models import db, Deck, Card
    
    app = create_app()
    with app.app_context():
        deck_count = Deck.query.count()
        card_count = Card.query.count()
        print(f"✅ Database OK - Decks: {deck_count}, Cards: {card_count}")
except Exception as e:
    print(f"❌ Database Error: {e}")
    import traceback
    traceback.print_exc()
PYEOF

# 4. Kiểm tra R2 storage
echo -e "\n${GREEN}[4/6] Kiểm tra R2 storage...${NC}"
python3 << 'PYEOF'
try:
    from r2_storage import get_r2_storage
    r2 = get_r2_storage()
    response = r2.s3_client.list_objects_v2(Bucket=r2.bucket_name, MaxKeys=1)
    print(f"✅ R2 Storage OK - Bucket: {r2.bucket_name}")
except ImportError:
    print("⚠️  R2 module chưa cài - app sẽ lưu ảnh local")
except Exception as e:
    print(f"❌ R2 Error: {e}")
PYEOF

# 5. Chạy migrations nếu cần
echo -e "\n${GREEN}[5/6] Chạy database migrations...${NC}"
flask db upgrade
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migrations thành công${NC}"
else
    echo -e "${RED}❌ Migrations lỗi - kiểm tra lại database${NC}"
fi

# 6. Restart app
echo -e "\n${GREEN}[6/6] Restart app...${NC}"
sudo supervisorctl restart smalltree
sleep 2
sudo supervisorctl status smalltree

echo -e "\n${YELLOW}======================================================"
echo "   FIX HOÀN TẤT - KIỂM TRA APP"
echo "======================================================${NC}"
echo ""
echo "Nếu vẫn lỗi, chạy lệnh sau để xem log real-time:"
echo -e "${YELLOW}tail -f $APP_DIR/logs/gunicorn.err.log${NC}"
echo ""
echo "Hoặc kiểm tra chi tiết:"
echo -e "${YELLOW}python3 $APP_DIR/check_vps_setup.py${NC}"
echo ""
