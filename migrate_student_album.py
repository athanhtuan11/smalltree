#!/usr/bin/env python3
"""
Direct database migration script for Student Album tables
Chạy script này để tạo các bảng student_album, student_photo, student_progress
"""

import sqlite3
import os
from datetime import datetime

# Path to database
db_path = os.path.join(os.path.dirname(__file__), 'app', 'site.db')

def create_student_album_tables():
    """Tạo các bảng cho tính năng Student Album"""
    
    # Kết nối database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔧 Tạo bảng student_album...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_album (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                date_created DATE NOT NULL,
                milestone_type VARCHAR(50),
                school_year VARCHAR(20),
                semester VARCHAR(10),
                age_at_time VARCHAR(10),
                created_by VARCHAR(100),
                is_shared_with_parents BOOLEAN DEFAULT 1,
                FOREIGN KEY (student_id) REFERENCES child (id)
            )
        ''')
        
        print("🔧 Tạo bảng student_photo...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_photo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                album_id INTEGER NOT NULL,
                filename VARCHAR(200) NOT NULL,
                filepath VARCHAR(300) NOT NULL,
                original_filename VARCHAR(200),
                caption TEXT,
                upload_date DATETIME NOT NULL,
                file_size INTEGER,
                image_order INTEGER DEFAULT 0,
                is_cover_photo BOOLEAN DEFAULT 0,
                FOREIGN KEY (album_id) REFERENCES student_album (id) ON DELETE CASCADE
            )
        ''')
        
        print("🔧 Tạo bảng student_progress...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                evaluation_date DATE NOT NULL,
                skill_category VARCHAR(50) NOT NULL,
                skill_name VARCHAR(200) NOT NULL,
                level_achieved VARCHAR(20),
                notes TEXT,
                teacher_name VARCHAR(100),
                FOREIGN KEY (student_id) REFERENCES child (id)
            )
        ''')
        
        # Commit changes
        conn.commit()
        print("✅ Đã tạo thành công tất cả bảng Student Album!")
        
        # Kiểm tra bảng đã tạo
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'student_%'")
        tables = cursor.fetchall()
        print(f"📋 Các bảng student đã tạo: {[table[0] for table in tables]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi tạo bảng: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def check_existing_tables():
    """Kiểm tra các bảng hiện có"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"📊 Các bảng hiện có: {tables}")
        
        # Kiểm tra child table
        if 'child' in tables:
            cursor.execute("SELECT COUNT(*) FROM child")
            student_count = cursor.fetchone()[0]
            print(f"👥 Số học sinh hiện có: {student_count}")
        
        return tables
        
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra bảng: {e}")
        return []
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Student Album Migration Script")
    print(f"📁 Database path: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Không tìm thấy database: {db_path}")
        exit(1)
    
    print("\n1️⃣ Kiểm tra bảng hiện có...")
    existing_tables = check_existing_tables()
    
    print("\n2️⃣ Tạo bảng Student Album...")
    success = create_student_album_tables()
    
    if success:
        print("\n✅ Migration hoàn tất! Có thể truy cập /student-albums")
    else:
        print("\n❌ Migration thất bại!")
