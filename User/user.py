from flask import Blueprint,request,render_template,flash,redirect,url_for, make_response
from app import app, db, login_manager
from models import User
from User.UserLogin import UserLogin
from flask_login  import current_user,login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3


#   Создание Blueprint
user=Blueprint('user',__name__,template_folder='templates',static_folder='static')


#           Настройка аутентификации
#--------------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    print("load_user")
    return UserLogin().fromDB(user_id,db,User,app)



#********************************************************АУТЕНТИФИКАЦИЯ*********************************************************************************


#        Страница аутентификации
#--------------------------------------------------------------------------------
@app.route("/login", methods=("POST","GET"))
def login():
    # Если пользователь уже авторизован, перенаправляем на страницу профиля
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    # Если совершена отправка формы
    if request.method == "POST":
        try:
            user = User.query.filter_by(login = request.form['login']).first() #поиск пол-ля по Логину
            print(user)
            # Если пользователь найден в БД и пароль верный
            if user and check_password_hash(user.psw,request.form['psw']):

                 userlogin = UserLogin().create(user)

                 #Проверка стоит ли галочка "Запомнить меня"
                 rm = True if request.form.get('remainme') else False
                 login_user(userlogin, remember = rm)

                 # Переход туда, куда пытался зайти пользователь/ в профиль
                 return redirect(request.args.get("next") or url_for('profile'))

            flash("Неверная пара логин/пароль","alert-danger")
        except:
            print("Ошибка поиска в базе данных пользователя по логину")
            return False


    return render_template('user/login.html',title = "Авторизация")


#*******************************************************РЕГИСТРАЦИЯ**********************************************************************************

#        Страница регистрации
#--------------------------------------------------------------------------------
@app.route("/register", methods=("POST","GET"))
def register():
    # Если произошла отправка формы
    if request.method == "POST":

        # Проверка на длину введенных строк
        if len(request.form['fio']) > 4 and len(request.form['login']) > 4 \
                and len(request.form['psw']) > 4 :

            # Проверка на соответствие паролей
            if request.form['psw'] == request.form['psw2']:

                # Проверка на уникальность логина
                if User.query.filter_by(login = request.form['login']).all():
                    flash("Пользователь с таким логином уже существует", "alert-danger")
                else:
                    try:
                        hash = generate_password_hash((request.form['psw']))
                        u = User(fio=request.form['fio'],login=request.form['login'],psw=hash, avatar = None)
                        db.session.add(u)
                        db.session.flush()
                        db.session.commit()

                        #Авторизация пользователя
                        userlogin = UserLogin().create(u)
                        login_user(userlogin)
                        flash("Вы успешно зарегестрированы", "alert-success")
                        return redirect(url_for('profile'))
                    except:
                        db.session.rollback()
                        print("Ошибка добавления в БД")

            else:
                flash("Пароли не совпадают", "alert-danger")
        else:
            flash("Слишком мало символов, минимальная длина = 4 символа", "alert-danger")


    return render_template('user/register.html',title = "Регистрация")


#*************************************************************ПРОФИЛЬ******************************************************************************

#        Выход из акканута
#--------------------------------------------------------------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из акаунта", "alert-success")
    return redirect(url_for('login'))

#        Фото профиля
#--------------------------------------------------------------------------------
@app.route('/userava')
@login_required
def userava():
    img = current_user.get_Avatar(app)
    if not img:
        return ""
    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h

#        Загрузка фото на профиль
#--------------------------------------------------------------------------------
@app.route('/upload', methods=("POST","GET"))
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']

        # Проверка успешна ли была загрузка файла и соответствует ли расширение  phg
        if file and current_user.verifyExt(file.filename):
            try:
                img = file.read()

                # Не пустой ли файл фото
                if not img:
                    flash("Не удалось получить фото", "alert-danger")
                else:
                    try:
                        # Преобразовываем данные в бинарный объект и помещаем в БД
                        binary = sqlite3.Binary(img)
                        User.query.filter_by(id = current_user.get_id()).update({'avatar': binary})
                        db.session.commit()
                        flash("Аватар обновлен", "alert-success")
                    except:
                        print("Ошибка обновления фото в БД")

            except FileNotFoundError as e:
                flash("Ошибка чтения файла", "alert-danger")
        else:
            flash("Не тот формат фото, нужен \"png\"", "alert-danger")

    return redirect(url_for('profile'))


#        Профиль
#--------------------------------------------------------------------------------
@app.route('/profile')
@login_required
def profile():
    return render_template('user/profile.html', title="Ваш профиль", fio = current_user.get_fio(), login = current_user.get_login())


#************************************************************************ВСЕ ПРОФИЛИ***************************************************************

#        Профили всех пользователей
#--------------------------------------------------------------------------------
@app.route('/all_profiles')
@login_required
def all_profiles():
    users = User.query.all()
    return render_template('user/all_profiles.html', title="Профили всех пользователей", users = users)

#        Фото всех профилей
#--------------------------------------------------------------------------------
@app.route('/all_userava/<id>')
@login_required
def all_userava(id):
    user = User.query.filter_by(id=id).first()
    img = user.avatar
    if not img:
        try:
            with app.open_resource(app.root_path + url_for('user.static', filename='images/default.png'), "rb") as f:
                img = f.read()
        except FileNotFoundError as e:
            print("Не найдено фото профиля по умолчанию: " + str(e))
    if not img:
        return ""
    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h


#        Добавление пользователя
#--------------------------------------------------------------------------------
@app.route('/add_user', methods=("POST","GET"))
@login_required
def add_user():
    # Если произошла отправка формы
    if request.method == "POST":

        # Проверка на длину введенных строк
        if len(request.form['fio']) > 4 and len(request.form['login']) > 4 \
                and len(request.form['psw']) > 4:

            # Проверка на уникальность логина
            if User.query.filter_by(login=request.form['login']).all():
                flash("Пользователь с таким логином уже существует", "alert-danger")
            else:
                try:
                    hash = generate_password_hash((request.form['psw']))
                    u = User(fio=request.form['fio'], login=request.form['login'], psw=hash, avatar=None)
                    db.session.add(u)
                    db.session.flush()
                    db.session.commit()

                    flash("Пользователь успешно добавлен", "alert-success")
                except:
                    db.session.rollback()
                    print("Ошибка добавления в БД")
        else:
            flash("Слишком мало символов, минимальная длина = 4 символа", "alert-danger")

    return render_template('user/add_user.html', title="Добавление пользователя")


#        Изменение записи пользователя
#--------------------------------------------------------------------------------
@app.route('/update_user/<id>', methods=("POST","GET"))
@login_required
def update_user(id):
    try:
        user = User.query.filter_by(id=id).first()
    except:
        print("Ошибка чтения записи о пользователе")

    # Если произошла отправка формы
    if request.method == "POST":

        # Проверка на длину введенных строк
        if len(request.form['fio']) > 4 and len(request.form['login']) > 4 \
                and len(request.form['psw']) > 4:

            user_login = User.query.filter_by(login=request.form['login']).first()
            # Проверка на уникальность логина
            if user_login and user_login.login != user.login :
                flash("Пользователь с таким логином уже существует", "alert-danger")
            else:
                try:
                    hash = generate_password_hash((request.form['psw']))

                    user.fio = request.form['fio']
                    user.login = request.form['login']
                    user.psw = hash
                    db.session.commit()

                    flash("Информация о пользователе обновлена успешно", "alert-success")
                except:
                    db.session.rollback()
                    print("Ошибка добавления в БД")
        else:
            flash("Слишком мало символов, минимальная длина = 4 символа", "alert-danger")

    return render_template('user/update_user.html', id = user.id, title="Изменение данных пользователя", fio=user.fio, login=user.login)


#        Загрузка фото на профиль другого пользователя
#--------------------------------------------------------------------------------
@app.route('/upload_for_user/<id>', methods=("POST","GET"))
@login_required
def upload_for_user(id):
    if request.method == 'POST':
        file = request.files['file']

        # Проверка успешна ли была загрузка файла и соответствует ли расширение  phg
        if file and current_user.verifyExt(file.filename):
            try:
                img = file.read()

                # Не пустой ли файл фото
                if not img:
                    flash("Не удалось получить фото", "alert-danger")
                else:
                    try:
                        # Преобразовываем данные в бинарный объект и помещаем в БД
                        binary = sqlite3.Binary(img)
                        User.query.filter_by(id = id).update({'avatar': binary})
                        db.session.commit()
                        flash("Аватар обновлен", "alert-success")
                    except:
                        db.session.rollback()
                        print("Ошибка обновления фото в БД")

            except FileNotFoundError as e:
                flash("Ошибка чтения файла", "alert-danger")
        else:
            flash("Не тот формат фото, нужен \"png\"", "alert-danger")

    return redirect(url_for('update_user', id=id))


#        Удаление пользователя из списка
#--------------------------------------------------------------------------------
@app.route('/delete_user/<id>')
@login_required
def delete_user(id):

    redirect_f = False
    # Если пользователь удаляет сам себя, то он выходит из системы
    if id == current_user.get_id():
        logout_user()
        redirect_f = True
        flash("Вы удалили свой профиль и вышли из акаунта", "alert-success")

    try:
        User.query.filter_by(id=id).delete()
        db.session.commit()

        # Если пользователь удаляет сам себя, переходим в форму входа
        if(redirect_f == True):
            flash("Вы удалили свой аккаунт", "alert-success")
            return redirect(url_for('login'))

        flash("Пользователь успешно удален", "alert-success")

    except:
        db.session.rollback()
        print("Ошибка удаление пользователя в БД")

    try:
        users = User.query.all()
    except:
        print("Ошибка считывание всех пользователей из БД")

    return render_template('user/all_profiles.html', title="Профили всех пользователей", users=users)

