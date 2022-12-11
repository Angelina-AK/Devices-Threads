from app import app
from flask import render_template
from User.user import user
from Thread.thread import thread_bl

# Подключение Blueprints
app.register_blueprint(user,url_prefix='/user')
app.register_blueprint(thread_bl,url_prefix='/thread')

#        Главная страница
#--------------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template('index.html',title = "Главная страница")



#------------------------------------------------------------------------------------------
#                   Обработчики ошибок
#------------------------------------------------------------------------------------------
@app.errorhandler(404) #страница не найдена
def pageNotFount(error):
    return render_template('page404.html',title= "Страница не найдена")


#------------------------------------------------------------------------------------------
#                   Запуск сервера
#------------------------------------------------------------------------------------------
if __name__ == "__main__":
     app.run(debug=True)


