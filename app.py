"""
Образовательный центр «Начало»
Flask Backend (app.py)

Запуск:
    python app.py
    
Требования:
    pip install flask flask-wtf email-validator
"""

import os
import json
import smtplib
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from functools import wraps
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_wtf import FlaskForm, CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, TelField, IntegerField, SelectField, BooleanField, HiddenField, PasswordField
from wtforms.validators import DataRequired, Regexp, Optional
from werkzeug.security import generate_password_hash, check_password_hash

# Загружаем .env файл для переменных окружения
try:
    from dotenv import load_dotenv
    load_dotenv()  # загрузит .env из текущей директории
except ImportError:
    pass  # python-dotenv не установлен, используем системные переменные

# ========================================
# Конфигурация
# ========================================

# IMPORTANT: The Flask instance MUST be named 'application' for Reg.ru hosting
application = Flask(__name__, static_folder='static', static_url_path='/static')
app = application  # Alias for local development compatibility

# База данных
basedir = os.path.abspath(os.path.dirname(__file__))

if os.environ.get('MYSQL_HOST') and os.environ.get('MYSQL_PASSWORD'):
    # MySQL (для хостинга)
    mysql_port = os.environ.get('MYSQL_PORT', '3306')
    application.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.environ.get('MYSQL_USER', 'u3475599_nachalo_user')}:"
        f"{os.environ.get('MYSQL_PASSWORD', '')}@"
        f"{os.environ.get('MYSQL_HOST', 'localhost')}:{mysql_port}/"
        f"{os.environ.get('MYSQL_DATABASE', 'u3475599_nachalo_db')}"
    )
else:
    # SQLite (для локальной разработки)
    application.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(basedir, "leads.db")}'
    )

application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
application.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

application.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
application.config['SESSION_COOKIE_HTTPONLY'] = True
application.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
application.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)

# CSRF защита
csrf = CSRFProtect(application)

# Инициализация базы данных
db = SQLAlchemy(application)

# Конфигурация почты (заполните своими данными)
application.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.yandex.ru')
application.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 465))
application.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'True').lower() == 'true'
application.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your-email@yandex.ru')
application.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-password')
application.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'your-email@yandex.ru')
application.config['ADMIN_EMAIL'] = os.environ.get('ADMIN_EMAIL', 'admin@nachalo-ekb.ru')

# ========================================
# Модели базы данных
# ========================================

class Lead(db.Model):
    """Модель заявки на обучение"""
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    parent_name = db.Column(db.String(100), nullable=False)
    parent_phone = db.Column(db.String(20), nullable=False)
    child_age = db.Column(db.Integer, nullable=True)
    program = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_processed = db.Column(db.Boolean, default=False)
    comment = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Lead {self.parent_name} - {self.parent_phone}>'


class CallbackRequest(db.Model):
    """Модель заявки на обратный звонок"""
    __tablename__ = 'callbacks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_processed = db.Column(db.Boolean, default=False)
    comment = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Callback {self.name or "Anonymous"} - {self.phone}>'


# ========================================
# Формы
# ========================================

class LeadForm(FlaskForm):
    """Форма заявки на обучение"""
    parent_name = StringField('Имя родителя', validators=[DataRequired(message='Введите ваше имя')])
    parent_phone = TelField('Телефон', validators=[
        DataRequired(message='Введите телефон'),
        Regexp(r'^\+7 \(\d{3}\) \d{3}-\d{2}-\d{2}$', message='Неверный формат телефона')
    ])
    child_age = IntegerField('Возраст ребёнка', validators=[Optional()])
    program = SelectField('Программа', choices=[
        ('', 'Не выбрано'),
        ('school', 'Подготовка к школе'),
        ('english', 'Английский язык'),
        ('mental', 'Ментальная арифметика'),
        ('reading', 'Скорочтение'),
        ('memory', 'Развитие памяти'),
        ('cubing', 'Спидкубинг'),
        ('math', 'Суперматематика'),
        ('learn_reading', 'Обучение чтению'),
        ('chess', 'Шахматы'),
        ('afterschool', 'Продленка'),
        ('summer_camp', 'Осенние каникулы')
    ], validators=[Optional()])
    consent = BooleanField('Согласие на обработку персональных данных', validators=[DataRequired()])


class CallbackForm(FlaskForm):
    """Форма обратного звонка"""
    name = StringField('Ваше имя', validators=[Optional()])
    phone = TelField('Телефон', validators=[
        DataRequired(message='Введите телефон'),
        Regexp(r'^\+7 \(\d{3}\) \d{3}-\d{2}-\d{2}$', message='Неверный формат телефона')
    ])
    consent = BooleanField('Согласие на обработку персональных данных', validators=[DataRequired()])


# ========================================
# Утилиты
# ========================================

def send_email(subject, body, to_email):
    """Отправка email"""
    try:
        msg = MIMEMultipart()
        msg['From'] = app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
        server = smtplib.SMTP_SSL(
            app.config['MAIL_SERVER'],
            app.config['MAIL_PORT']
        )
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        app.logger.error(f"Error sending email: {e}")
        return False


def format_phone(phone):
    """Форматирование телефона для отображения"""
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) == 11 and digits.startswith('7'):
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    return phone


# Карта соответствий программ кодам направлений AMAkids (subject_code)
SUBJECT_CODE_MAP = {
    'mental': 'mental_arithmetic',
    'reading': 'liberica',
    'memory': 'memorica',
    'school': 'preschool',
    'learn_reading': 'alphabetica',
    'cubing': 'speedcubing',
    'math': 'amamath',
    'english': 'english',
    'afterschool': 'preschool',
    'summer_camp': 'preschool'
}


def send_to_amakids_crm(name, phone, program=None, child_age=None, comment_prefix=""):
    """Отправка заявки в CRM платформы AMAkids (Partner API)"""
    try:
        app_code = os.environ.get('AMAKIDS_APP_CODE', '6')
        api_key = os.environ.get('AMAKIDS_KEY', '00a3635effa806b70c804b4d0de35cccb284da6432c867d758ed27b3')
        franch_id = os.environ.get('AMAKIDS_FRANCH_ID', '229664')
        base_url = os.environ.get('AMAKIDS_API_URL', 'https://kidsplatform.ru/api/add_lead_post')
        
        target_url = f"{base_url}?app_code={app_code}"
        
        subject_code = SUBJECT_CODE_MAP.get(program, '') if program else ''
        
        comment_parts = []
        if comment_prefix:
            comment_parts.append(comment_prefix)
        if program:
            program_labels = {
                'school': 'Подготовка к школе',
                'english': 'Английский язык',
                'mental': 'Ментальная арифметика',
                'reading': 'Скорочтение',
                'memory': 'Развитие памяти',
                'cubing': 'Спидкубинг',
                'math': 'Суперматематика',
                'learn_reading': 'Обучение чтению',
                'chess': 'Шахматы',
                'afterschool': 'Продленка',
                'summer_camp': 'Осенний творческий клуб'
            }
            comment_parts.append(f"Программа: {program_labels.get(program, program)}")
        if child_age:
            comment_parts.append(f"Возраст ребёнка: {child_age} лет")
        comment_parts.append("Источник: Сайт nachalo-ekb.ru")
        
        full_comment = " | ".join(comment_parts)
        
        payload = {
            'key': api_key,
            'franch_id': franch_id,
            'name': name or 'Клиент',
            'phone': phone,
            'comment': full_comment
        }
        
        if subject_code:
            payload['subject_code'] = subject_code
            
        data = urllib.parse.urlencode(payload).encode('utf-8')
        req = urllib.request.Request(
            target_url, 
            data=data, 
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = response.read().decode('utf-8')
            res_json = json.loads(res_data)
            
            if res_json.get('status') == 'ok':
                application.logger.info(f"✅ AMAkids CRM Success: Lead ID {res_json.get('lead_id')}")
                return True, res_json.get('lead_id')
            else:
                application.logger.error(f"❌ AMAkids CRM Error: {res_json.get('error')}")
                return False, res_json.get('error')
    except Exception as e:
        application.logger.error(f"❌ AMAkids CRM Request Exception: {e}")
        return False, str(e)


# ========================================
# Загрузка данных из JSON
# ========================================

def load_site_data():
    """Загрузка данных из site_data.json"""
    data_path = os.path.join(os.path.dirname(__file__), 'site_data.json')
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        app.logger.error(f"Error loading site_data.json: {e}")
        return {}


@app.context_processor
def inject_site_data():
    """Передача данных из JSON во все шаблоны"""
    data = load_site_data()
    return dict(
        site_org=data.get('organization', {}),
        site_license=data.get('license', {}),
        site_contact=data.get('contact', {}),
        site_address=data.get('address', {}),
        site_social=data.get('social', {}),
        site_analytics=data.get('analytics', {}),
        site_prices=data.get('prices', {}),
        site_programs=data.get('programs', {}),
        site_teachers=data.get('teachers', []),
        site_management=data.get('management', []),
        site_facilities=data.get('facilities', {}),
        site_finance=data.get('finance', {}),
        site_documents=data.get('documents', {}),
        site_structure=data.get('structure', {}),
        site_policy=data.get('policy', {})
    )


# ========================================
# Маршруты
# ========================================

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@app.route('/index.html')
def index_html():
    """Редирект с /index.html на главную для SEO"""
    return redirect(url_for('index'), code=301)


@app.route('/programs.html')
def programs():
    """Страница программ"""
    return render_template('programs.html')


@app.route('/about.html')
def about():
    """О центре"""
    return render_template('about.html')


@app.route('/contacts.html')
def contacts():
    """Контакты"""
    return render_template('contacts.html')


@app.route('/policy.html')
def policy():
    """Политика конфиденциальности"""
    return render_template('policy.html')


@app.route('/thankyou.html')
def thankyou():
    """Страница благодарности"""
    return render_template('thankyou.html')


@app.route('/program/<program_slug>')
def program_detail(program_slug):
    """Страница отдельной программы"""
    # Загружаем данные о ценах из site_data.json
    site_data = load_site_data()
    prices = site_data.get('prices', {})

    # Формируем цены для каждой программы
    program_prices = {
        'english': {
            'price': f"{prices['english']['monthly']} ₽ / месяц",
            'price_options': [
                'Пробное занятие: <strong>бесплатно</strong>',
                f"Разовое занятие: <strong>{prices['english']['single']} ₽</strong>"
            ]
        },
        'mental': {
            'price': f"{prices['mental']['monthly']} ₽ / месяц",
            'price_options': [
                'Пробное занятие: <strong>бесплатно</strong>',
                f"Разовое занятие: <strong>{prices['mental']['single']} ₽</strong>"
            ]
        },
        'reading': {
            'price': f"{prices['reading']['monthly']} ₽ / месяц",
            'price_options': [
                'Пробное занятие: <strong>бесплатно</strong>',
                f"Разовое занятие: <strong>{prices['reading']['single']} ₽</strong>"
            ]
        },
        'memory': {
            'price': f"{prices['memory']['monthly']} ₽ / месяц",
            'price_options': [
                'Пробное занятие: <strong>бесплатно</strong>',
                f"Разовое занятие: <strong>{prices['memory']['single']} ₽</strong>"
            ]
        },
        'school': {
            'price': f"{prices['school']['monthly']} ₽ / месяц",
            'price_options': [
                'Пробное занятие: <strong>бесплатно</strong>',
                f"Разовое занятие: <strong>{prices['school']['single']} ₽</strong>"
            ]
        },
        'cubing': {
            'price': f"{prices['cubing']['monthly']} ₽ / месяц",
            'price_options': [
                'Пробное занятие: <strong>бесплатно</strong>',
                f"Разовое занятие: <strong>{prices['cubing']['single']} ₽</strong>"
            ]
        },
        'math': {
            'price': f"{prices['math']['monthly']} ₽ / месяц",
            'price_options': [
                'Пробное занятие: <strong>бесплатно</strong>',
                f"Разовое занятие: <strong>{prices['math']['single']} ₽</strong>"
            ]
        },
        'learn_reading': {
            'price': f"{prices['learn_reading']['single']} ₽ / занятие",
            'price_options': [
                f"Разовое занятие: <strong>{prices['learn_reading']['single']} ₽</strong>"
            ]
        },
        'chess': {
            'price': f"{prices['chess']['single']} ₽ / занятие",
            'price_options': [
                f"Разовое занятие: <strong>{prices['chess']['single']} ₽</strong>"
            ]
        },
        'afterschool': {
            'price': f"{prices['afterschool']['single']} ₽ / день",
            'price_options': [
                f"День в продленке: <strong>{prices['afterschool']['single']} ₽</strong>"
            ]
        },
        'summer_camp': {
            'price': f"{prices.get('summer_camp', {}).get('single', 'По запросу')}",
            'price_options': [
                f"Стоимость: <strong>{prices.get('summer_camp', {}).get('single', 'По запросу')}</strong>"
            ]
        }
    }

    # Словарь с данными программ
    programs_data = {
        'english': {
            'title': 'Английский язык',
            'icon': 'fa-language',
            'age': '5-16 лет',
            'description': 'Современные методики изучения английского языка с акцентом на разговорную практику.',
            'about': 'Наши педагоги создают комфортную языковую среду, где дети начинают говорить с первого занятия.',
            'study': [
                'Грамматика и лексика в игровой форме',
                'Разговорная практика с носителями (онлайн)',
                'Аудирование и произношение',
                'Чтение и письмо',
                'Подготовка к международным экзаменам (Cambridge)'
            ],
            'results': [
                'Уровень A1-A2 (в зависимости от возраста)',
                'Свободное общение на бытовые темы',
                'Уверенность в использовании языка'
            ],
            'format': [
                {'icon': 'fa-clock', 'text': '2 раза в неделю'},
                {'icon': 'fa-hourglass-half', 'text': '60 минут (5-7 лет), 90 минут (8-16 лет)'},
                {'icon': 'fa-users', 'text': 'Группы до 8 человек'},
                {'icon': 'fa-laptop', 'text': 'Онлайн или офлайн'}
            ],
            'price': program_prices['english']['price'],
            'price_note': '8 занятий / абонемент',
            'price_options': program_prices['english']['price_options']
        },
        'mental': {
            'title': 'Ментальная арифметика',
            'icon': 'fa-calculator',
            'age': '5-14 лет',
            'description': 'Уникальная методика развития обоих полушарий мозга через обучение счёту на соробане.',
            'about': 'Дети учатся считать быстрее калькулятора с помощью японских счётов и ментального счёта!',
            'study': [
                'Счёт на соробане (абакус)',
                'Ментальный счёт (в уме)',
                'Развитие фотографической памяти',
                'Концентрация внимания',
                'Скорочтение (бонус)'
            ],
            'results': [
                'Счёт в уме многозначных чисел',
                'Улучшение успеваемости по всем предметам',
                'Развитие творческого и логического мышления'
            ],
            'format': [
                {'icon': 'fa-clock', 'text': '2 раза в неделю'},
                {'icon': 'fa-hourglass-half', 'text': '90 минут'},
                {'icon': 'fa-users', 'text': 'Группы до 8 человек'},
                {'icon': 'fa-laptop', 'text': 'Онлайн или офлайн'}
            ],
            'price': program_prices['mental']['price'],
            'price_note': '4 занятия / абонемент',
            'price_options': program_prices['mental']['price_options']
        },
        'reading': {
            'title': 'Скорочтение',
            'icon': 'fa-book-open',
            'age': '6-14 лет',
            'description': 'Авторская методика увеличения скорости чтения в 2-3 раза.',
            'about': 'Сохранение и улучшение понимания прочитанного текста.',
            'study': [
                'Упражнения для расширения поля зрения',
                'Подавление проговаривания (субвокализации)',
                'Развитие периферического зрения',
                'Техники работы с текстом',
                'Мнемотехники для запоминания'
            ],
            'results': [
                'Скорость чтения от 150 слов/мин',
                'Улучшение понимания текста на 80%+',
                'Успехи в учебе по всем предметам'
            ],
            'format': [
                {'icon': 'fa-clock', 'text': '2 раза в неделю'},
                {'icon': 'fa-hourglass-half', 'text': '90 минут'},
                {'icon': 'fa-users', 'text': 'Группы до 8 человек'},
                {'icon': 'fa-laptop', 'text': 'Онлайн или офлайн'}
            ],
            'price': program_prices['reading']['price'],
            'price_note': '4 занятия / абонемент',
            'price_options': program_prices['reading']['price_options']
        },
        'memory': {
            'title': 'Развитие памяти',
            'icon': 'fa-brain',
            'age': '6-14 лет',
            'description': 'Мнемотехники — специальные приёмы для запоминания больших объёмов информации.',
            'about': 'Навык, который поможет в учёбе и жизни.',
            'study': [
                'Метод ассоциаций',
                'Дворец памяти (метод локусов)',
                'Запоминание чисел, дат, формул',
                'Запоминание текстов и стихов',
                'Развитие внимания и концентрации'
            ],
            'results': [
                'Запоминание 50+ элементов за 5 минут',
                'Улучшение успеваемости',
                'Уверенность в своих силах'
            ],
            'format': [
                {'icon': 'fa-clock', 'text': '2 раза в неделю'},
                {'icon': 'fa-hourglass-half', 'text': '90 минут'},
                {'icon': 'fa-users', 'text': 'Группы до 8 человек'},
                {'icon': 'fa-laptop', 'text': 'Онлайн или офлайн'}
            ],
            'price': program_prices['memory']['price'],
            'price_note': '4 занятий / абонемент',
            'price_options': program_prices['memory']['price_options']
        },
        'school': {
            'title': 'Подготовка к школе',
            'icon': 'fa-graduation-cap',
            'age': '5-7 лет',
            'description': 'Комплексная подготовка к школе: чтение, письмо, счёт, окружающий мир.',
            'about': 'Ребёнок будет готов к учёбе без стресса и слёз.',
            'study': [
                'Обучение чтению (звуко-буквенный метод)',
                'Прописи, развитие мелкой моторики',
                'Счёт в пределах 20-100',
                'Логические задачи',
                'Окружающий мир',
                'Навыки самоорганизации'
            ],
            'results': [
                'Уверенное чтение и письмо',
                'Готовность к школьной программе',
                'Психологическая готовность к школе'
            ],
            'format': [
                {'icon': 'fa-clock', 'text': '2-3 раза в неделю'},
                {'icon': 'fa-hourglass-half', 'text': '45-60 минут'},
                {'icon': 'fa-users', 'text': 'Группы до 6 человек'},
                {'icon': 'fa-laptop', 'text': 'Офлайн (рекомендуется)'}
            ],
            'price': program_prices['school']['price'],
            'price_note': '8 занятий / абонемент',
            'price_options': program_prices['school']['price_options']
        },
        'cubing': {
            'title': 'Спидкубинг',
            'icon': 'fa-cube',
            'age': '7-16 лет',
            'description': 'Скоростная сборка кубика Рубика и других головоломок.',
            'about': 'Развивает моторику, логику, скорость мышления.',
            'study': [
                'Базовая сборка 3x3',
                'Метод CFOP (продвинутый)',
                'Сборка 2x2, 4x4, 5x5',
                'Другие головоломки (Pyraminx, Megaminx)',
                'Участие в соревнованиях'
            ],
            'results': [
                'Сборка 3x3 за 30-60 секунд',
                'Развитие пространственного мышления',
                'Навыки выступления на соревнованиях'
            ],
            'format': [
                {'icon': 'fa-clock', 'text': '2 раза в неделю'},
                {'icon': 'fa-hourglass-half', 'text': '90 минут'},
                {'icon': 'fa-users', 'text': 'Группы до 8 человек'},
                {'icon': 'fa-laptop', 'text': 'Офлайн (рекомендуется)'}
            ],
            'price': program_prices['cubing']['price'],
            'price_note': '8 занятий / абонемент',
            'price_options': program_prices['cubing']['price_options']
        },
        'math': {
            'title': 'Суперматематика',
            'icon': 'fa-square-root-alt',
            'age': '7-12 лет',
            'description': 'Помогаем со школьной математикой. Подготовка к ВПР.',
            'about': 'Индивидуальные и групповые занятия, направленные на укрепление знаний школьной программы.',
            'study': [
                'Разбор школьной программы',
                'Устранение пробелов в знаниях',
                'Подготовка к ВПР',
                'Решение задач и уравнений',
                'Развитие логического мышления'
            ],
            'results': [
                'Улучшение оценок по математике',
                'Уверенность при решении ВПР',
                'Системные знания по школьной программе'
            ],
            'format': [
                {'icon': 'fa-clock', 'text': '2 раза в неделю'},
                {'icon': 'fa-hourglass-half', 'text': 'Длительность по договоренности'},
                {'icon': 'fa-users', 'text': 'Мини-группы'},
                {'icon': 'fa-laptop', 'text': 'Офлайн или онлайн'}
            ],
            'price': program_prices['math']['price'],
            'price_note': '8 занятий / абонемент',
            'price_options': program_prices['math']['price_options']
        },
        'learn_reading': {
            'title': 'Обучение чтению',
            'icon': 'fa-font',
            'age': '5-10 лет',
            'description': 'Обучение чтению включает в себя знакомство со всеми буквами и звуками русского языка, а также освоение звуко-буквенного анализа.',
            'about': 'Формируем прочный фундамент для успешного обучения в школе.',
            'study': [
                'Изучение букв и звуков',
                'Звуко-буквенный анализ',
                'Чтение по слогам и словами',
                'Понимание прочитанного'
            ],
            'results': [
                'Уверенное чтение',
                'Готовность к школе',
                'Развитие фонематического слуха'
            ],
            'format': [
                {'icon': 'fa-clock', 'text': '2 раза в неделю'},
                {'icon': 'fa-hourglass-half', 'text': 'Индивидуальная длительность'},
                {'icon': 'fa-users', 'text': 'Мини-группы или индивидуально'},
                {'icon': 'fa-laptop', 'text': 'Офлайн'}
            ],
            'price': program_prices['learn_reading']['price'],
            'price_note': 'за одно занятие',
            'price_options': program_prices['learn_reading']['price_options']
        },
        'chess': {
            'title': 'Шахматы',
            'icon': 'fa-chess',
            'age': '5-10 лет',
            'description': 'Развитие логического и стратегического мышления, памяти и внимания через увлекательную игру в шахматы.',
            'about': 'Шахматы учат детей думать на несколько шагов вперед, анализировать ситуации и принимать решения.',
            'study': [
                'Правила игры и ходы фигур',
                'Шахматная нотация',
                'Базовые тактические приемы',
                'Решение шахматных задач',
                'Игровая практика'
            ],
            'results': [
                'Развитие логики и аналитического мышления',
                'Улучшение концентрации внимания',
                'Умение планировать свои действия'
            ],
            'format': [
                {'icon': 'fa-clock', 'text': '2 раза в неделю'},
                {'icon': 'fa-hourglass-half', 'text': 'Индивидуальная длительность'},
                {'icon': 'fa-users', 'text': 'Мини-группы'},
                {'icon': 'fa-laptop', 'text': 'Офлайн'}
            ],
            'price': program_prices['chess']['price'],
            'price_note': 'за одно занятие',
            'price_options': program_prices['chess']['price_options']
        },
        'afterschool': {
            'title': 'Продленка',
            'icon': 'fa-school',
            'age': '1-4 класс',
            'description': 'Полезное времяпрепровождение после школы: выполнение домашних заданий, игры, прогулки и творчество.',
            'about': 'Родители могут спокойно работать, зная, что ребенок под присмотром и занят полезным делом.',
            'study': [
                'Выполнение домашнего задания с педагогом',
                'Творческие мастер-классы',
                'Прогулки на свежем воздухе',
                'Развивающие игры',
                'Отдых и общение со сверстниками'
            ],
            'results': [
                'Сделанные уроки',
                'Развитие творческих способностей',
                'Социализация и новые друзья'
            ],
            'format': [
                {'icon': 'fa-clock', 'text': 'Ежедневно по будням'},
                {'icon': 'fa-hourglass-half', 'text': 'С 8:00 до 17:00'},
                {'icon': 'fa-users', 'text': 'Группа'},
                {'icon': 'fa-laptop', 'text': 'Офлайн'}
            ],
            'price': program_prices['afterschool']['price'],
            'price_note': 'за день пребывания',
            'price_options': program_prices['afterschool']['price_options']
        },
        'summer_camp': {
            'title': 'ОСЕННИЙ ТВОРЧЕСКИЙ КЛУБ: 5 ДНЕЙ ВЕСЕЛЬЯ И МАСТЕР-КЛАССОВ',
            'badge': 'Осенние каникулы (с 26 по 30 октября)',
            'icon': 'fa-paint-brush',
            'age': '7–11 лет',
            'dates': 'с 26 по 30 октября',
            'time': 'с 10:00 до 17:00',
            'food': 'горячий комплексный обед и перекусы включены',
            'address': 'ул. Анатолия Мехренцева, 46 (образовательный центр «Начало»)',
            'phone': '+7 (982) 675-60-70',
            'phone_raw': '+79826756070',
            'warning': 'Количество мест в группе строго ограничено!',
            'description': 'Осенние каникулы — время, когда хочется, чтобы ребёнок отдохнул с пользой и не скучал в гаджетах. У нас есть решение! Приглашаем ребят 7–11 лет в нашу каникулярную программу дневного пребывания.',
            'about': 'Каждый день детей ждут авторские мастер-классы, творческие поделки, сбалансированное питание, активные прогулки на свежем воздухе, квесты и яркие впечатления!',
            'schedule': [
                {
                    'day': 'День 1',
                    'icon': 'fa-palette',
                    'title': 'Текстильное арт-панно и поделка из ниток',
                    'desc': 'Создаём уютное панно из ткани и оригинальную авторскую поделку из ниток.'
                },
                {
                    'day': 'День 2',
                    'icon': 'fa-image',
                    'title': 'Объёмная картина в технике декорирования салфетками',
                    'desc': 'Осваиваем декупаж и объёмное декорирование для создания своей живописной картины.'
                },
                {
                    'day': 'День 3',
                    'icon': 'fa-ghost',
                    'title': 'Праздничный декор: тыква или привидение своими руками',
                    'desc': 'Творческий мастер-класс по изготовлению стильного и атмосферного осеннего декора.'
                },
                {
                    'day': 'День 4',
                    'icon': 'fa-fire-alt',
                    'title': 'Изготовление уютных свечей',
                    'desc': 'Создаём и декорируем настоящие ароматные восковые свечи для теплого дома.'
                },
                {
                    'day': 'День 5',
                    'icon': 'fa-sparkles',
                    'title': 'Фигурки из пушистой проволоки, квест и мини-дискотека',
                    'desc': 'Мастер-класс по синельной проволоке, увлекательный приключенческий квест и веселая мини-дискотека!'
                }
            ],
            'daily_extra': 'А ещё каждый день — активные прогулки и игры на свежем воздухе!',
            'benefits': [
                'Ребёнок под присмотром опытных педагогов с утра до вечера (с 10:00 до 17:00)',
                'Каждый день — готовая авторская поделка, которую ребёнок уносит домой',
                'Сбалансированное питание: горячий комплексный обед и перекусы включены',
                'Новые друзья, живое общение и море ярких впечатлений'
            ],
            'format': [
                {'icon': 'fa-calendar-alt', 'text': 'с 26 по 30 октября'},
                {'icon': 'fa-clock', 'text': 'с 10:00 до 17:00'},
                {'icon': 'fa-utensils', 'text': 'Горячий обед и перекусы включены'},
                {'icon': 'fa-map-marker-alt', 'text': 'ул. Анатолия Мехренцева, 46'},
                {'icon': 'fa-users', 'text': 'Ребята 7–11 лет'}
            ],
            'price': '12 500 ₽',
            'price_note': 'за 5 дней («всё включено»)',
            'price_options': [
                '5 дней пребывания с 10:00 до 17:00',
                'Горячий комплексный обед + перекусы',
                'Все материалы и заготовки для мастер-классов',
                'Ежедневная готовая авторская поделка домой'
            ]
        }
    }
    
    # Получаем данные программы или возвращаем 404
    program = programs_data.get(program_slug)
    if not program:
        return render_template('errors/404.html'), 404
    
    return render_template('program_detail.html', program=program, program_slug=program_slug)


# ========================================
# Раздел "Сведения об организации" (приказ 1493)
# ========================================

@app.route('/info/')
@app.route('/info/index.html')
def info_index():
    """Меню раздела сведений об организации"""
    return render_template('info/index.html')


@app.route('/info/basic.html')
def info_basic():
    """Основные сведения"""
    return render_template('info/basic.html')


@app.route('/info/structure.html')
def info_structure():
    """Структура и органы управления"""
    return render_template('info/structure.html')


@app.route('/info/documents.html')
def info_documents():
    """Документы"""
    return render_template('info/documents.html')


@app.route('/info/education.html')
def info_education():
    """Образование"""
    return render_template('info/education.html')


@app.route('/info/management.html')
def info_management():
    """Руководство"""
    return render_template('info/management.html')


@app.route('/info/teachers.html')
def info_teachers():
    """Педагогический состав"""
    return render_template('info/teachers.html')


@app.route('/info/facilities.html')
def info_facilities():
    """Материально-техническое обеспечение"""
    return render_template('info/facilities.html')


@app.route('/info/paid-services.html')
def info_paid_services():
    """Платные образовательные услуги"""
    return render_template('info/paid-services.html')


@app.route('/info/finance.html')
def info_finance():
    """Финансово-хозяйственная деятельность"""
    return render_template('info/finance.html')


@app.route('/info/vacancies.html')
def info_vacancies():
    """Вакантные места"""
    return render_template('info/vacancies.html')


# ========================================
# Обработка форм (API)
# ========================================

@app.route('/submit-lead/', methods=['POST'])
def submit_lead():
    """Обработка заявки на обучение"""
    form = LeadForm()

    # Логирование для отладки
    application.logger.info(f"Form data received: {request.form}")
    application.logger.info(f"CSRF token present: {'csrf_token' in request.form}")
    application.logger.info(f"Form validates: {form.validate_on_submit()}")
    
    if form.validate_on_submit():
        # Сохранение в базу данных
        lead = Lead(
            parent_name=form.parent_name.data,
            parent_phone=form.parent_phone.data,
            child_age=form.child_age.data,
            program=form.program.data,
            created_at=datetime.now()
        )
        try:
            db.session.add(lead)
            db.session.commit()
            application.logger.info(f"New lead saved: {lead.parent_name}")
        except Exception as e:
            db.session.rollback()
            application.logger.error(f"Error saving lead: {e}")
            return jsonify({
                'success': False,
                'message': f'Ошибка сохранения заявки в базу данных: {str(e)}'
            }), 500

        # Отправляем заявку в CRM платформы AMAkids
        try:
            send_to_amakids_crm(
                name=form.parent_name.data,
                phone=form.parent_phone.data,
                program=form.program.data,
                child_age=form.child_age.data
            )
        except Exception as e:
            application.logger.error(f"Error sending to AMAkids CRM: {e}")

        # Отправка email администратору
        program_name = dict(form.program.choices).get(form.program.data, 'Не выбрано')
        subject = f"📩 Новая заявка на обучение — {form.parent_name.data}"

        body = f"""
        <h2>Новая заявка на обучение</h2>
        <table style="border-collapse: collapse; width: 100%;">
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Имя родителя:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{form.parent_name.data}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Телефон:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{form.parent_phone.data}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Возраст ребёнка:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{form.child_age.data} лет</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Программа:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{program_name}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Дата:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{datetime.now().strftime('%d.%m.%Y %H:%M')}</td>
            </tr>
        </table>
        """

        # Отправляем email (не критично если ошибка)
        try:
            send_email(subject, body, application.config['ADMIN_EMAIL'])
        except Exception as e:
            application.logger.error(f"Error sending email: {e}")

        return jsonify({
            'success': True,
            'message': 'Заявка успешно отправлена'
        })
    else:
        # Логирование ошибок валидации
        application.logger.warning(f"Form validation errors: {form.errors}")

    return jsonify({
        'success': False,
        'message': 'Ошибка валидации формы',
        'errors': form.errors
    }), 400


@app.route('/submit-callback/', methods=['POST'])
def submit_callback():
    """Обработка заявки на обратный звонок"""
    form = CallbackForm()

    if form.validate_on_submit():
        # Сохранение в базу данных
        callback = CallbackRequest(
            name=form.name.data,
            phone=form.phone.data,
            created_at=datetime.now()
        )
        try:
            db.session.add(callback)
            db.session.commit()
            application.logger.info(f"New callback saved: {callback.name or 'Anonymous'}")
        except Exception as e:
            db.session.rollback()
            application.logger.error(f"Error saving callback: {e}")
            return jsonify({
                'success': False,
                'message': f'Ошибка сохранения заявки в базу данных: {str(e)}'
            }), 500

        # Отправляем заявку в CRM платформы AMAkids
        try:
            send_to_amakids_crm(
                name=form.name.data,
                phone=form.phone.data,
                comment_prefix="Заявка на обратный звонок"
            )
        except Exception as e:
            application.logger.error(f"Error sending to AMAkids CRM: {e}")

        # Отправка email администратору
        subject = f"📞 Заявка на обратный звонок — {form.name.data or 'Аноним'}"

        body = f"""
        <h2>Заявка на обратный звонок</h2>
        <table style="border-collapse: collapse; width: 100%;">
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Имя:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{form.name.data or 'Не указано'}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Телефон:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{form.phone.data}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Дата:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{datetime.now().strftime('%d.%m.%Y %H:%M')}</td>
            </tr>
        </table>
        """

        # Отправляем email (не критично если ошибка)
        try:
            send_email(subject, body, application.config['ADMIN_EMAIL'])
        except Exception as e:
            application.logger.error(f"Error sending email: {e}")

        return jsonify({
            'success': True,
            'message': 'Заявка успешно отправлена'
        })

    return jsonify({
        'success': False,
        'message': 'Ошибка валидации формы',
        'errors': form.errors
    }), 400


# ========================================
# ========================================
# Админ-панель (просмотр заявок & аутентификация)
# ========================================

def check_admin_credentials(username, password):
    """Проверка логина и пароля администратора"""
    expected_username = os.environ.get('ADMIN_USERNAME', 'admin')
    env_password_hash = os.environ.get('ADMIN_PASSWORD_HASH')
    
    if username != expected_username:
        return False
        
    if env_password_hash:
        return check_password_hash(env_password_hash, password)
    else:
        plain_password = os.environ.get('ADMIN_PASSWORD', 'nachalo2024')
        return password == plain_password


def admin_required(f):
    """Декоратор проверки авторизации администратора"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/admin/login/', methods=['GET', 'POST'])
def admin_login():
    """Вход в админ-панель"""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_leads'))
        
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if check_admin_credentials(username, password):
            session.permanent = True
            session['admin_logged_in'] = True
            session['admin_user'] = username
            next_url = request.args.get('next') or url_for('admin_leads')
            return redirect(next_url)
        else:
            error = 'Неверное имя пользователя или пароль'
            
    return render_template('admin/login.html', error=error)


@app.route('/admin/logout/')
def admin_logout():
    """Выход из админ-панели"""
    session.clear()
    return redirect(url_for('admin_login'))


@app.route('/admin/leads/')
@admin_required
def admin_leads():
    """Просмотр всех заявок на обучение"""
    leads = Lead.query.order_by(Lead.created_at.desc()).all()
    return render_template('admin/leads.html', leads=leads, type='lead')


@app.route('/admin/callbacks/')
@admin_required
def admin_callbacks():
    """Просмотр всех заявок на обратный звонок"""
    callbacks = CallbackRequest.query.order_by(CallbackRequest.created_at.desc()).all()
    return render_template('admin/callbacks.html', callbacks=callbacks, type='callback')


@app.route('/admin/mark-processed/<int:lead_id>/', methods=['POST'])
@admin_required
def mark_processed(lead_id):
    """Отметить заявку как обработанную"""
    try:
        lead = Lead.query.get_or_404(lead_id)
        lead.is_processed = True
        db.session.commit()
        return jsonify({'success': True, 'message': 'Заявка отмечена как обработанная'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ========================================
# Обработка ошибок
# ========================================

@app.errorhandler(404)
def page_not_found(e):
    """Страница не найдена"""
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    """Внутренняя ошибка сервера"""
    return render_template('errors/500.html'), 500


# ========================================
# Запуск приложения
# ========================================

if __name__ == '__main__':
    # Создание таблиц базы данных при запуске
    with application.app_context():
        try:
            db.create_all()
            print("✅ База данных инициализирована")
        except Exception as e:
            print(f"⚠️ Ошибка подключения к MySQL: {e}")
            print("🔄 Переключение на локальную базу данных SQLite...")
            application.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "leads.db")}'
            db.create_all()
            print("✅ Локальная база данных SQLite инициализирована")
    
    # Для разработки
    application.run(debug=True, host='0.0.0.0', port=5000)

    # Для продакшена (через gunicorn):
    # gunicorn -w 4 -b 0.0.0.0:5000 app:application
