#------------------------------------------------------------------------------------------
#                   Настройка конфигурации
#------------------------------------------------------------------------------------------
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# Для работы с БД
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '2b1e657f5ce6ffbf5b2426d173440d3658491779' # Для работы сессий
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 # Максимальный размер в байтах файла, который можно загрузить в БД
db = SQLAlchemy(app)

# Для работы аутентификации
login_manager = LoginManager(app)
login_manager.login_view = 'login' # что показывать, при попытки зайти на страницы с обязательной авторизацией
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
login_manager.login_message_category = "alert alert-primary"


