#!/usr/bin/env python3
"""
Script migrate tất cả ảnh/audio flashcard từ local lên Cloudflare R2
"""
import os
import sys
from pathlib import Path

def migrate_flashcard_to_r2():
    """Migrate flashcard images và audio lên R2"""
    
    try:
        from app import create_app
        from app.models import db, Deck, Card
        from r2_storage import get_r2_storage
        
        app = create_app()
        r2 = get_r2_storage()
        
        print("=" * 60)
        print("   MIGRATE FLASHCARD FILES TO CLOUDFLARE R2")
        print("=" * 60)
        print()
        
        with app.app_context():
            # 1. Migrate Deck covers
            print("[1/2] Migrating Deck cover images...")
            decks = Deck.query.all()
            deck_success = 0
            deck_failed = 0
            
            for deck in decks:
                if deck.cover_image and not deck.cover_image.startswith('http'):
                    # Local path: flashcard/images/xxx.jpg
                    local_path = f"app/static/{deck.cover_image}"
                    
                    if os.path.exists(local_path):
                        try:
                            # Upload to R2: flashcard/covers/xxx.jpg
                            filename = os.path.basename(local_path)
                            r2_path = f"flashcard/covers/{filename}"
                            
                            with open(local_path, 'rb') as f:
                                r2.upload_file(f, r2_path)
                            
                            # Update database
                            deck.cover_image = f"{r2.public_url}/{r2_path}"
                            db.session.commit()
                            
                            print(f"  ✅ Deck '{deck.title}': {r2_path}")
                            deck_success += 1
                            
                        except Exception as e:
                            print(f"  ❌ Deck '{deck.title}': {e}")
                            deck_failed += 1
                    else:
                        print(f"  ⚠️  Deck '{deck.title}': File không tồn tại - {local_path}")
            
            print(f"\n  Deck covers: {deck_success} thành công, {deck_failed} lỗi\n")
            
            # 2. Migrate Card images và audio
            print("[2/2] Migrating Card images & audio...")
            cards = Card.query.all()
            card_image_success = 0
            card_image_failed = 0
            card_audio_success = 0
            card_audio_failed = 0
            
            for card in cards:
                # Migrate image
                if card.image_url and not card.image_url.startswith('http'):
                    local_path = f"app/static/{card.image_url}"
                    
                    if os.path.exists(local_path):
                        try:
                            filename = os.path.basename(local_path)
                            r2_path = f"flashcard/cards/{filename}"
                            
                            with open(local_path, 'rb') as f:
                                r2.upload_file(f, r2_path)
                            
                            card.image_url = f"{r2.public_url}/{r2_path}"
                            card_image_success += 1
                            
                        except Exception as e:
                            print(f"  ❌ Card {card.id} image: {e}")
                            card_image_failed += 1
                
                # Migrate audio
                if card.audio_url and not card.audio_url.startswith('http'):
                    local_path = f"app/static/{card.audio_url}"
                    
                    if os.path.exists(local_path):
                        try:
                            filename = os.path.basename(local_path)
                            r2_path = f"flashcard/audio/{filename}"
                            
                            with open(local_path, 'rb') as f:
                                r2.upload_file(f, r2_path)
                            
                            card.audio_url = f"{r2.public_url}/{r2_path}"
                            card_audio_success += 1
                            
                        except Exception as e:
                            print(f"  ❌ Card {card.id} audio: {e}")
                            card_audio_failed += 1
            
            # Commit tất cả changes
            db.session.commit()
            
            print(f"  Card images: {card_image_success} thành công, {card_image_failed} lỗi")
            print(f"  Card audio: {card_audio_success} thành công, {card_audio_failed} lỗi")
            print()
            
            # Summary
            print("=" * 60)
            print("   MIGRATION HOÀN TẤT")
            print("=" * 60)
            print(f"  ✅ Tổng files migrated: {deck_success + card_image_success + card_audio_success}")
            print(f"  ❌ Tổng files failed: {deck_failed + card_image_failed + card_audio_failed}")
            print()
            print(f"  🌐 R2 Public URL: {r2.public_url}")
            print(f"  📦 R2 Bucket: {r2.bucket_name}")
            print()
            
    except ImportError as e:
        print(f"❌ Module import error: {e}")
        print("   Hãy chắc chắn đã cài đặt: pip install boto3")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Migration error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def check_r2_connection():
    """Kiểm tra kết nối R2 trước khi migrate"""
    try:
        from r2_storage import get_r2_storage
        r2 = get_r2_storage()
        
        # Test connection
        response = r2.s3_client.list_objects_v2(Bucket=r2.bucket_name, MaxKeys=1)
        print("✅ R2 connection OK")
        print(f"   Bucket: {r2.bucket_name}")
        print(f"   Public URL: {r2.public_url}")
        return True
    except Exception as e:
        print(f"❌ R2 connection failed: {e}")
        print("\nKiểm tra lại:")
        print("  1. File .env có đủ R2 credentials")
        print("  2. Đã cài boto3: pip install boto3")
        print("  3. R2 bucket settings cho phép upload")
        return False

if __name__ == '__main__':
    print("\n🚀 FLASHCARD FILES MIGRATION TO CLOUDFLARE R2\n")
    
    # Check R2 connection first
    if not check_r2_connection():
        sys.exit(1)
    
    print()
    confirm = input("⚠️  Migration sẽ upload TẤT CẢ files flashcard lên R2. Tiếp tục? (y/N): ")
    
    if confirm.lower() == 'y':
        migrate_flashcard_to_r2()
        print("✅ Migration hoàn tất! Kiểm tra app xem ảnh có hiển thị đúng không.\n")
    else:
        print("❌ Migration đã bị hủy.\n")
