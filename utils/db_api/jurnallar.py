import sqlite3
import logging
from typing import List, Dict, Optional, Tuple
import os

DB_NAME = 'bot_database.db'

def init_journals_db():
    """Jurnallar uchun ma'lumotlar bazasini yaratish va dastlabki ma'lumotlarni yuklash"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Jadvallarni yaratish
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fanlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nomi TEXT UNIQUE NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bolimlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nomi TEXT UNIQUE NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jurnallar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fan_id INTEGER NOT NULL,
            bolim_id INTEGER NOT NULL,
            nomi TEXT NOT NULL,
            rasmi TEXT,
            nashr_chastotasi TEXT,
            murojaat_link TEXT,
            jurnal_sayti TEXT,
            talablar_link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fan_id) REFERENCES fanlar (id),
            FOREIGN KEY (bolim_id) REFERENCES bolimlar (id)
        )
    ''')

    # Indekslarni qo'shish tezlik uchun
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jurnallar_fan_id ON jurnallar(fan_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jurnallar_bolim_id ON jurnallar(bolim_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jurnallar_nomi ON jurnallar(nomi)')

    conn.commit()

    # Dastlabki ma'lumotlarni yuklash
    populate_initial_data(cursor, conn)

    conn.close()
    logging.info("Jurnallar bazasi muvaffaqiyatli yaratildi")

def populate_initial_data(cursor, conn):
    """Dastlabki fanlar va bo'limlarni yuklash"""

    # Fanlar ro'yxati
    fanlar = [
        "Fizika-matematika fanlari",
        "Kimyo fanlari",
        "Biologiya fanlari",
        "Geologiya-mineralogiya fanlari",
        "Texnika fanlari",
        "Qishloq xo'jaligi fanlari",
        "Tarix fanlari",
        "Iqtisodiyot fanlari",
        "Falsafa fanlari",
        "Filologiya fanlari",
        "Geografiya fanlari",
        "Yuridik fanlar",
        "Pedagogika fanlari",
        "Tibbiyot fanlari",
        "Farmatsevtika fanlari",
        "Veterinariya fanlari",
        "San'atshunoslik fanlari",
        "Arxitektura",
        "Psixologiya fanlari",
        "Harbiy fanlar",
        "Sotsiologiya fanlari",
        "Siyosiy fanlar",
        "Islomshunoslik fanlari"
    ]

    # Bo'limlar ro'yxati
    bolimlar = [
        "Milliy nashrlar",
        "Mustaqil davlatlar hamdo'stligi mamlakatlari nashrlari",
        "Evropa mamlakatlari nashrlari",
        "Amerika mamlakatlari nashrlari"
    ]

    # Fanlarni qo'shish
    for fan_nomi in fanlar:
        cursor.execute('''
            INSERT OR IGNORE INTO fanlar (nomi) VALUES (?)
        ''', (fan_nomi,))

    # Bo'limlarni qo'shish
    for bolim_nomi in bolimlar:
        cursor.execute('''
            INSERT OR IGNORE INTO bolimlar (nomi) VALUES (?)
        ''', (bolim_nomi,))

    conn.commit()

# Fan operatsiyalari
def get_fanlar() -> List[Dict]:
    """Barcha fanlarni olish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT id, nomi FROM fanlar ORDER BY nomi')
        results = cursor.fetchall()

        conn.close()

        fanlar = []
        for result in results:
            fanlar.append({
                'id': result[0],
                'nomi': result[1]
            })

        return fanlar
    except Exception as e:
        logging.error(f"Fanlarni olishda xatolik: {str(e)}")
        return []

def get_fan_by_id(fan_id: int) -> Optional[Dict]:
    """ID bo'yicha fanni olish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT id, nomi FROM fanlar WHERE id = ?', (fan_id,))
        result = cursor.fetchone()

        conn.close()

        if result:
            return {
                'id': result[0],
                'nomi': result[1]
            }
        return None
    except Exception as e:
        logging.error(f"Fanni olishda xatolik: {str(e)}")
        return None

# Bo'lim operatsiyalari
def get_bolimlar() -> List[Dict]:
    """Barcha bo'limlarni olish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT id, nomi FROM bolimlar ORDER BY id')
        results = cursor.fetchall()

        conn.close()

        bolimlar = []
        for result in results:
            bolimlar.append({
                'id': result[0],
                'nomi': result[1]
            })

        return bolimlar
    except Exception as e:
        logging.error(f"Bo'limlarni olishda xatolik: {str(e)}")
        return []

def get_bolim_by_id(bolim_id: int) -> Optional[Dict]:
    """ID bo'yicha bo'limni olish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT id, nomi FROM bolimlar WHERE id = ?', (bolim_id,))
        result = cursor.fetchone()

        conn.close()

        if result:
            return {
                'id': result[0],
                'nomi': result[1]
            }
        return None
    except Exception as e:
        logging.error(f"Bo'limni olishda xatolik: {str(e)}")
        return None

# Jurnal operatsiyalari
def get_jurnallar(fan_id: int, bolim_id: int, page: int = 1, per_page: int = 15) -> Tuple[List[Dict], int]:
    """Pagination bilan jurnallar ro'yxatini olish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Umumiy soni
        cursor.execute('''
            SELECT COUNT(*) FROM jurnallar 
            WHERE fan_id = ? AND bolim_id = ?
        ''', (fan_id, bolim_id))

        total_count = cursor.fetchone()[0]

        # Offset hisoblash
        offset = (page - 1) * per_page

        # Jurnallarni olish
        cursor.execute('''
            SELECT j.id, j.nomi, j.rasmi, j.nashr_chastotasi,
                   j.murojaat_link, j.jurnal_sayti, j.talablar_link,
                   f.nomi as fan_nomi, b.nomi as bolim_nomi
            FROM jurnallar j
            JOIN fanlar f ON j.fan_id = f.id
            JOIN bolimlar b ON j.bolim_id = b.id
            WHERE j.fan_id = ? AND j.bolim_id = ?
            ORDER BY j.nomi
            LIMIT ? OFFSET ?
        ''', (fan_id, bolim_id, per_page, offset))

        results = cursor.fetchall()
        conn.close()

        jurnallar = []
        for result in results:
            jurnallar.append({
                'id': result[0],
                'nomi': result[1],
                'rasmi': result[2],
                'nashr_chastotasi': result[3],
                'murojaat_link': result[4],
                'jurnal_sayti': result[5],
                'talablar_link': result[6],
                'fan_nomi': result[7],
                'bolim_nomi': result[8]
            })

        return jurnallar, total_count
    except Exception as e:
        logging.error(f"Jurnallarni olishda xatolik: {str(e)}")
        return [], 0

def get_jurnal_by_id(jurnal_id: int) -> Optional[Dict]:
    """ID bo'yicha jurnalni olish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT j.id, j.fan_id, j.bolim_id, j.nomi, j.rasmi, 
                   j.nashr_chastotasi, j.murojaat_link, j.jurnal_sayti, 
                   j.talablar_link, f.nomi as fan_nomi, b.nomi as bolim_nomi
            FROM jurnallar j
            JOIN fanlar f ON j.fan_id = f.id
            JOIN bolimlar b ON j.bolim_id = b.id
            WHERE j.id = ?
        ''', (jurnal_id,))

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'id': result[0],
                'fan_id': result[1],
                'bolim_id': result[2],
                'nomi': result[3],
                'rasmi': result[4],
                'nashr_chastotasi': result[5],
                'murojaat_link': result[6],
                'jurnal_sayti': result[7],
                'talablar_link': result[8],
                'fan_nomi': result[9],
                'bolim_nomi': result[10]
            }
        return None
    except Exception as e:
        logging.error(f"Jurnalni olishda xatolik: {str(e)}")
        return None

def add_jurnal(fan_id: int, bolim_id: int, nomi: str, **kwargs) -> int:
    """Yangi jurnal qo'shish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO jurnallar (fan_id, bolim_id, nomi, rasmi, nashr_chastotasi,
                                  murojaat_link, jurnal_sayti, talablar_link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            fan_id, bolim_id, nomi,
            kwargs.get('rasmi'),
            kwargs.get('nashr_chastotasi'),
            kwargs.get('murojaat_link'),
            kwargs.get('jurnal_sayti'),
            kwargs.get('talablar_link')
        ))

        jurnal_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logging.info(f"Yangi jurnal qo'shildi: {nomi} (ID: {jurnal_id})")
        return jurnal_id
    except Exception as e:
        logging.error(f"Jurnal qo'shishda xatolik: {str(e)}")
        raise

def update_jurnal(jurnal_id: int, **kwargs) -> bool:
    """Jurnalni yangilash"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Dinamik UPDATE query yaratish
        updates = []
        values = []

        allowed_fields = ['nomi', 'rasmi', 'nashr_chastotasi', 'murojaat_link', 'jurnal_sayti', 'talablar_link']

        for field in allowed_fields:
            if field in kwargs:
                updates.append(f"{field} = ?")
                values.append(kwargs[field])

        if not updates:
            conn.close()
            return False

        values.append(jurnal_id)
        query = f"UPDATE jurnallar SET {', '.join(updates)} WHERE id = ?"

        cursor.execute(query, values)
        conn.commit()

        success = cursor.rowcount > 0
        conn.close()

        if success:
            logging.info(f"Jurnal yangilandi: ID {jurnal_id}")

        return success
    except Exception as e:
        logging.error(f"Jurnal yangilashda xatolik: {str(e)}")
        return False

def delete_jurnal(jurnal_id: int) -> bool:
    """Jurnalni o'chirish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM jurnallar WHERE id = ?', (jurnal_id,))
        conn.commit()

        success = cursor.rowcount > 0
        conn.close()

        if success:
            logging.info(f"Jurnal o'chirildi: ID {jurnal_id}")

        return success
    except Exception as e:
        logging.error(f"Jurnal o'chirishda xatolik: {str(e)}")
        return False

def search_jurnallar(query: str, fan_id: int = None, bolim_id: int = None) -> List[Dict]:
    """Jurnallar ichida qidirish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        sql = '''
            SELECT j.id, j.nomi, j.rasmi, j.nashr_chastotasi,
                   j.murojaat_link, j.jurnal_sayti, j.talablar_link,
                   f.nomi as fan_nomi, b.nomi as bolim_nomi
            FROM jurnallar j
            JOIN fanlar f ON j.fan_id = f.id
            JOIN bolimlar b ON j.bolim_id = b.id
            WHERE j.nomi LIKE ?
        '''

        params = [f'%{query}%']

        if fan_id:
            sql += ' AND j.fan_id = ?'
            params.append(fan_id)

        if bolim_id:
            sql += ' AND j.bolim_id = ?'
            params.append(bolim_id)

        sql += ' ORDER BY j.nomi'

        cursor.execute(sql, params)
        results = cursor.fetchall()
        conn.close()

        jurnallar = []
        for result in results:
            jurnallar.append({
                'id': result[0],
                'nomi': result[1],
                'rasmi': result[2],
                'nashr_chastotasi': result[3],
                'murojaat_link': result[4],
                'jurnal_sayti': result[5],
                'talablar_link': result[6],
                'fan_nomi': result[7],
                'bolim_nomi': result[8]
            })

        return jurnallar
    except Exception as e:
        logging.error(f"Qidiruvda xatolik: {str(e)}")
        return []

# Statistika funksiyalari
# Statistika funksiyalari
def get_statistics() -> Dict:
    """Umumiy statistikalar"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Fanlar soni
        cursor.execute('SELECT COUNT(*) FROM fanlar')
        fanlar_count = cursor.fetchone()[0]

        # Bo'limlar soni
        cursor.execute('SELECT COUNT(*) FROM bolimlar')
        bolimlar_count = cursor.fetchone()[0]

        # Jurnallar soni
        cursor.execute('SELECT COUNT(*) FROM jurnallar')
        jurnallar_count = cursor.fetchone()[0]

        # Foydalanuvchilar soni (users jadvalini tekshirish)
        try:
            cursor.execute('SELECT COUNT(*) FROM users')
            users_count = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            # Agar users jadvali mavjud bo'lmasa
            users_count = 0

        # Eng ko'p jurnali bo'lgan fan
        cursor.execute('''
            SELECT f.nomi, COUNT(*) as count
            FROM jurnallar j
            JOIN fanlar f ON j.fan_id = f.id
            GROUP BY f.id, f.nomi
            ORDER BY count DESC
            LIMIT 1
        ''')
        top_fan = cursor.fetchone()

        conn.close()

        return {
            'fanlar_count': fanlar_count,
            'bolimlar_count': bolimlar_count,
            'jurnallar_count': jurnallar_count,
            'users_count': users_count,  # Bu qator qo'shildi
            'top_fan': {
                'nomi': top_fan[0] if top_fan else "Ma'lumotsiz",
                'jurnallar_soni': top_fan[1] if top_fan else 0
            }
        }
    except Exception as e:
        logging.error(f"Statistika olishda xatolik: {str(e)}")
        return {
            'fanlar_count': 0,
            'bolimlar_count': 0,
            'jurnallar_count': 0,
            'users_count': 0,  # Bu qator qo'shildi
            'top_fan': {
                'nomi': "Ma'lumotsiz",
                'jurnallar_soni': 0
            }
        }

def get_jurnallar_count_by_fan(fan_id: int) -> int:
    """Fan bo'yicha jurnallar sonini olish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM jurnallar WHERE fan_id = ?', (fan_id,))
        count = cursor.fetchone()[0]

        conn.close()
        return count
    except Exception as e:
        logging.error(f"Fan bo'yicha jurnallar sonini olishda xatolik: {str(e)}")
        return 0

def get_jurnallar_count_by_bolim(bolim_id: int) -> int:
    """Bo'lim bo'yicha jurnallar sonini olish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM jurnallar WHERE bolim_id = ?', (bolim_id,))
        count = cursor.fetchone()[0]

        conn.close()
        return count
    except Exception as e:
        logging.error(f"Bo'lim bo'yicha jurnallar sonini olishda xatolik: {str(e)}")
        return 0

def get_jurnallar_count_by_fan_bolim(fan_id: int, bolim_id: int) -> int:
    """Fan va bo'lim kombinatsiyasi bo'yicha jurnallar sonini olish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM jurnallar WHERE fan_id = ? AND bolim_id = ?', (fan_id, bolim_id))
        count = cursor.fetchone()[0]

        conn.close()
        return count
    except Exception as e:
        logging.error(f"Fan va bo'lim bo'yicha jurnallar sonini olishda xatolik: {str(e)}")
        return 0

def get_latest_jurnallar(limit: int = 10) -> List[Dict]:
    """Oxirgi qo'shilgan jurnallarni olish"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT j.id, j.nomi, j.rasmi, j.nashr_chastotasi,
                   j.murojaat_link, j.jurnal_sayti, j.talablar_link,
                   f.nomi as fan_nomi, b.nomi as bolim_nomi, j.created_at
            FROM jurnallar j
            JOIN fanlar f ON j.fan_id = f.id
            JOIN bolimlar b ON j.bolim_id = b.id
            ORDER BY j.created_at DESC
            LIMIT ?
        ''', (limit,))

        results = cursor.fetchall()
        conn.close()

        jurnallar = []
        for result in results:
            jurnallar.append({
                'id': result[0],
                'nomi': result[1],
                'rasmi': result[2],
                'nashr_chastotasi': result[3],
                'murojaat_link': result[4],
                'jurnal_sayti': result[5],
                'talablar_link': result[6],
                'fan_nomi': result[7],
                'bolim_nomi': result[8],
                'created_at': result[9]
            })

        return jurnallar
    except Exception as e:
        logging.error(f"Oxirgi jurnallarni olishda xatolik: {str(e)}")
        return []

def get_all_jurnallar_admin() -> List[Dict]:
    """Barcha jurnallarni olish (admin uchun)"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT j.id, j.nomi, j.rasmi, j.nashr_chastotasi,
                   j.murojaat_link, j.jurnal_sayti, j.talablar_link,
                   f.nomi as fan_nomi, b.nomi as bolim_nomi, j.created_at
            FROM jurnallar j
            JOIN fanlar f ON j.fan_id = f.id
            JOIN bolimlar b ON j.bolim_id = b.id
            ORDER BY j.created_at DESC
        ''')

        results = cursor.fetchall()
        conn.close()

        jurnallar = []
        for result in results:
            jurnallar.append({
                'id': result[0],
                'nomi': result[1],
                'rasmi': result[2],
                'nashr_chastotasi': result[3],
                'murojaat_link': result[4],
                'jurnal_sayti': result[5],
                'talablar_link': result[6],
                'fan_nomi': result[7],
                'bolim_nomi': result[8],
                'created_at': result[9]
            })

        return jurnallar
    except Exception as e:
        logging.error(f"Barcha jurnallarni olishda xatolik: {str(e)}")
        return []

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_journals_db()
    stats = get_statistics()
    print(f"\nStatistika (jurnallar qismi):")
    print(f"Fanlar: {stats['fanlar_count']}")
    print(f"Bo'limlar: {stats['bolimlar_count']}")
    print(f"Jurnallar: {stats['jurnallar_count']}")
    print(f"Eng ko'p jurnali bo'lgan fan: {stats['top_fan']['nomi']} ({stats['top_fan']['jurnallar_soni']} ta)")