"""
Скрипт для инициализации базы данных
Поддерживает MySQL (production) и SQLite (development)

Для MySQL заполните переменные окружения или используйте .env файл:
    MYSQL_HOST=localhost
    MYSQL_USER=nachalo_user
    MYSQL_PASSWORD=ваш_пароль
    MYSQL_DATABASE=nachalo_db

Запустить:
    python init_db.py
"""
import os
import sys

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Загружаем .env файл если есть
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotnot установлен

from app import application, db

# Создаём таблицы в базе данных
with application.app_context():
    print("🔄 Инициализация базы данных...")
    
    # Определяем тип БД
    db_uri = application.config['SQLALCHEMY_DATABASE_URI']
    if 'mysql' in db_uri:
        print("📊 Тип базы данных: MySQL")
    else:
        print("📊 Тип базы данных: SQLite")
    
    try:
        db.create_all()
        print("✅ База данных успешно инициализирована!")
        
        if 'mysql' in db_uri:
            print(f"🔗 Подключение: {db_uri.split('@')[1] if '@' in db_uri else db_uri}")
        else:
            print(f"📁 Файл базы данных: {os.path.join(os.path.dirname(__file__), 'leads.db')}")
        
        print("")
        print("📋 Созданные таблицы:")
        print("  - leads (заявки на обучение)")
        print("  - callbacks (заявки на обратный звонок)")
        print("")
        print("🔐 Админ-панель:")
        print("  - Заявки: /admin/leads/?pass=ваш_пароль")
        print("  - Звонки: /admin/callbacks/?pass=ваш_пароль")
        print("")
        print("📝 Теперь вы можете:")
        print("  1. Открыть phpMyAdmin в ISPmanager")
        print("  2. Выбрать базу данных: nachalo_db")
        print("  3. Просмотреть таблицы: leads, callbacks")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        print("")
        print("Возможные причины:")
        print("  - Неверные данные для подключения к MySQL")
        print("  - База данных не создана в phpMyAdmin")
        print("  - Не установлен PyMySQL: pip install PyMySQL")
        sys.exit(1)
