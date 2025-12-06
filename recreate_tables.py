# recreate_supabase.py
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def recreate_supabase_tables():
    """Пересоздает таблицы напрямую через asyncpg"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL не найден в .env")
        return
    
    # Преобразуем URL для asyncpg
    conn_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    
    print("🔄 Пересоздаем таблицы в Supabase...")
    
    try:
        # Подключаемся напрямую
        conn = await asyncpg.connect(conn_url)
        
        # Удаляем старую таблицу если существует
        await conn.execute('DROP TABLE IF EXISTS tasks CASCADE')
        print("✅ Старая таблица удалена")
        
        # Создаем новую таблицу
        await conn.execute('''
            CREATE TABLE tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                is_important BOOLEAN DEFAULT FALSE,
                deadline_at TIMESTAMPTZ,
                quadrant VARCHAR(2) NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                completed_at TIMESTAMPTZ
            )
        ''')
        print("✅ Новая таблица создана")
        
        # Создаем индексы для производительности
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_quadrant ON tasks(quadrant)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks(completed)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks(deadline_at)')
        print("✅ Индексы созданы")
        
        await conn.close()
        print("🎉 Таблицы успешно пересозданы в Supabase!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(recreate_supabase_tables())