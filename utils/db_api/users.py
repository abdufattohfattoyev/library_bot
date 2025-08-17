import sqlite3
import logging
from typing import List, Dict, Optional
import os

DB_NAME = 'bot_database.db'

def init_users_db():
    """Foydalanuvchilar uchun ma'lumotlar bazasini yaratish"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Users jadvalini yaratish
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    logging.info("Foydalanuvchilar bazasi muvaffaqiyatli yaratildi")

# Foydalanuvchi operatsiyalari
def add_user(user_id: int, full_name: str, username: str = None) -> None:
    """Yangi foydalanuvchi qo'shish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO users (id, full_name, username, created_at, last_active)
            VALUES (?, ?, ?, 
                COALESCE((SELECT created_at FROM users WHERE id = ?), CURRENT_TIMESTAMP),
                CURRENT_TIMESTAMP)
        ''', (user_id, full_name, username, user_id))

        conn.commit()
        conn.close()
        logging.info(f"Foydalanuvchi qo'shildi/yangilandi: {full_name} (ID: {user_id})")
    except Exception as e:
        logging.error(f"Foydalanuvchi qo'shishda xatolik: {str(e)}")
        raise

def get_user(user_id: int) -> Optional[Dict]:
    """Foydalanuvchi ma'lumotlarini olish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()

        conn.close()

        if result:
            return {
                'id': result[0],
                'full_name': result[1],
                'username': result[2],
                'created_at': result[3],
                'last_active': result[4]
            }
        return None
    except Exception as e:
        logging.error(f"Foydalanuvchi olishda xatolik: {str(e)}")
        return None

def update_user_activity(user_id: int) -> None:
    """Foydalanuvchi faolligini yangilash"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE id = ?
        ''', (user_id,))

        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Foydalanuvchi faolligini yangilashda xatolik: {str(e)}")

def get_all_users() -> List[Dict]:
    """Barcha foydalanuvchilarni olish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users ORDER BY last_active DESC')
        results = cursor.fetchall()

        conn.close()

        users = []
        for result in results:
            users.append({
                'id': result[0],
                'full_name': result[1],
                'username': result[2],
                'created_at': result[3],
                'last_active': result[4]
            })

        return users
    except Exception as e:
        logging.error(f"Foydalanuvchilarni olishda xatolik: {str(e)}")
        return []

# Database ulanishini tekshirish (umumiy, lekin users uchun moslashtirilgan)
def check_database_connection() -> bool:
    """Database ulanishini tekshirish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Database ulanishida xatolik: {str(e)}")
        return False

# Database backup yaratish (umumiy)
def create_backup(backup_path: str = None) -> bool:
    """Database backup yaratish"""
    try:
        import shutil
        from datetime import datetime

        if not backup_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f'backup_bot_database_{timestamp}.db'

        shutil.copy2(DB_NAME, backup_path)
        logging.info(f"Database backup yaratildi: {backup_path}")
        return True
    except Exception as e:
        logging.error(f"Backup yaratishda xatolik: {str(e)}")
        return False

# Database optimizatsiya qilish (umumiy)
def optimize_database() -> bool:
    """Database optimizatsiya qilish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('VACUUM')
        cursor.execute('ANALYZE')

        conn.commit()
        conn.close()

        logging.info("Database optimizatsiya qilindi")
        return True
    except Exception as e:
        logging.error(f"Database optimizatsiyasida xatolik: {str(e)}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_users_db()
    if check_database_connection():
        print("Database ulanishi muvaffaqiyatli!")
    else:
        print("Database ulanishida muammo bor!")