from flask import Blueprint,request,render_template,flash,redirect,url_for, make_response, jsonify
from app import app, db
from User.user import login_required
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from matplotlib.dates import DateFormatter
from matplotlib.figure import Figure
import matplotlib as mpl
import matplotlib.pyplot as plt
from models import Device,Directory,Sensor,Range,Problem,Advice
from Thread.Number_Check import is_number
import json

from urllib.request import urlopen
import json


#   Создание Blueprint
thread_bl = Blueprint('thread',__name__,template_folder='templates',static_folder='static')


#***************************************************************ПОКАЗ_УСТРОЙСТВ_И_ПОТОКОВ******************************************************************************

#        Страница устройств
#--------------------------------------------------------------------------------
@app.route("/devices/<dir_id>")
@login_required
def devices(dir_id):


    try:
        # Получение устройств из БД
        devices = Device.query.all()



        # Заполнение вложенного списка с информацией, где элемент это список из:
        # - имя устройства
        # - флаг о текущем состоянии устройста (True-все хорошо, False-с каким-то показателем что-то не так)
        # - Описание устройства: список датчиков прибора
        # - id прибора
        devices_info = []
        for d in devices:

            # Парсинг текущих данных с устройства
            #-----------------------------------------------------------
            url = d.url
            response = urlopen(url)
            js = json.loads(response.read())

            # Описание устройства
            information = " | "

            # Состояние устройства
            condition = True

            for j in js:

                if j == "time":
                    continue

                information += j + " | "

                # Определение состояния, в котором находится устройство
                # -------------------------------------------------------
                try:
                    # Есть ли в БД информация про этот тип датчика
                    type = Sensor.query.filter_by(Name=j).first()
                    if type:

                        try:
                            # Есть ли в БД информация из выбранного справочника для этого типа датчика
                            ranges = Range.query.filter_by(Sensor_Id=type.id,Directory_Id=dir_id).all()
                            if ranges:

                                for r in ranges:
                                    # Значение попало в диапазон с проблемой
                                    if js[j] >= r.Min and js[j] <= r.Max and r.prob:
                                        condition = False
                                        break
                                        break

                            else:
                                print("Для данного датчика нет диапазонов выбранном справочнике")
                                continue

                        except:
                            print("Не получилось считать диапазоны из БД")

                    else:
                        print("Про данный датчик нет информации в БД")
                        continue

                except:
                    print("Не получилось считать тип датчика из БД")

            # Заполнение вложенного списка
            devices_info.append([d.Name,condition,information, d.id])

    except:
        print("Не получилось считать данные из БД")


    try:
        directories = Directory.query.all()

    except:

        print("Ошибка считывания справочников из БД")

    return render_template('thread/devices.html',title = "Устройства", devices_info=devices_info, directories=directories, dir_id=dir_id)


#        Страница потоков с устройства
#--------------------------------------------------------------------------------
@app.route("/show_graph/<dev_id>/<dir_id>/<sensor>")
@login_required
def show_graph(dev_id,dir_id,sensor):
    try:

        # Парсинг всех данных с устройства
        # -----------------------------------------------------------
        device = Device.query.filter_by(id=dev_id).first()
        url = str(device.url) + "/all"
        response = urlopen(url)
        js = json.loads(response.read())

        # Если пока не выбран датчик, задание дефолтного значения
        # -----------------------------------------------------------
        sensors_list = []
        def_with_value = False
        for j in js[0]:
            if sensor == "default" and def_with_value == False:
                sensor = j
            sensors_list.append(j)


        # Сбор справочной информации для обработки и заполнение списков для графиков
        # -----------------------------------------------------------

        x = []   # временные метки
        y = []   # значения с датчика
        groups = []   # метки группы

        no_info = False      # на случай, если в базе данных нет информации в выбранном справочнике для выбранного датчика

        try:
            # Получаем выбранный датчик устройства
            sensor_DB = Sensor.query.filter_by(Name=sensor).first()
            if sensor_DB:

                try:
                    # Получаем диапазоны для выбранного датчика в выбранном справочнике
                    ranges = Range.query.filter_by(Sensor_Id=sensor_DB.id,Directory_Id=dir_id).all()
                    if ranges:

                        # Заполнение списоков для построения графика
                        for j in js:
                            value = j[sensor]
                            DateTime = datetime.strptime(j['time'], "%a, %d %b %Y %H:%M:%S %Z")
                            x.append(DateTime.isoformat())
                            y.append(value)

                            no_info_for_value = True
                            for r in ranges:
                                if value >= r.Min and value <= r.Max:
                                    groups.append(r.Name)
                                    no_info_for_value = False
                                    break

                            if no_info_for_value == True:
                                groups.append("Нет описания в справочнике")


                    else:
                        no_info = True
                except:
                    print("Не получилось считать диапазоны из БД")
            else:
                no_info=True
        except:
            print("Не получилось считать тип датчика из БД")


        if no_info == True:
            for j in js:
                DateTime = datetime.strptime(j['time'], "%a, %d %b %Y %H:%M:%S %Z")
                x.append(DateTime.isoformat())
                y.append(j[sensor])
                groups.append("Нет описания в справочнике")


    except:
        print("Не получилось считать устройство из БД")


    # Формироание заголовка
    try:
        cur_directory = Directory.query.filter_by(id=dir_id).first()

    except:
        print("Не получилось считать справочник из БД")

    title = "Потоки данных с устройства " + str(device.Name)
    dir_text = "Cправочник: " + str(cur_directory.Name)
    return render_template('thread/show_graph.html',title = title, x=json.dumps(x,ensure_ascii=False),y=y,groups=groups,sensor=sensor,sensors_list=sensors_list, dir_text=dir_text)


#--------------------------------------------------------------------------------
#        ДЛЯ ТРЕНИРОВКИ
#--------------------------------------------------------------------------------
@app.route("/tmp")
@login_required
def tmp():
    return render_template('thread/tmp.html')




#**********************************************************************СТРАНИЦЫ_СПРАВОЧНИКОВ**********************************************

#--------------------------------------------------------------------------------
#        Страница справочника диапазонов данных с потоков
#--------------------------------------------------------------------------------
@app.route("/ranges")
@login_required
def ranges():
    try:
        ranges = db.session.query(Range).order_by(Range.Min).all()
    except:
        print("Ошибка считывания диапазоно из Базы данных")
    return render_template('thread/ranges.html', title="Справочник диапазонов значений", content = ranges)

#--------------------------------------------------------------------------------
#        Страница справочника проблем с потоками
#--------------------------------------------------------------------------------
@app.route("/problems")
@login_required
def problems():
    try:
        problems = db.session.query(Problem).all()
    except:
        print("Ошибка считывания проблем из Базы данных")
    return render_template('thread/problems.html', title="Справочник проблем", content = problems)

#--------------------------------------------------------------------------------
#        Страница справочника советов
#--------------------------------------------------------------------------------
@app.route("/advices")
@login_required
def advices():
    try:
        # res = db.session.query(
        #     Advice, Problem, Range,
        #         ).filter(Advice.Problem_Id == Problem.id,
        #             ).filter(Problem.Range_Id == Range.id,
        #                   ).all()
        advices = Advice.query.all()
    except:
        print("Ошибка считывания рекомендаций из Базы данных")

    return render_template('thread/advices.html', title="Справочник рекоммендаций", advices = advices)




#***************************************************************ИЗМЕНЕНИЕ_СПРАВОЧНИКОВ******************************************************************************
#******************************************************ДИАПАЗОНЫ*******************************************************************

#        Добавление записи о диапазоне
#--------------------------------------------------------------------------------

@app.route("/add_range", methods=("POST","GET"))
@login_required
def add_range():

    # /////////////////////////////
    # Выпадающий список
    # /////////////////////////////
    # Данные для выпадающего списка типов данных
    try:
        types = db.session.query(Thread.Type_of_data).distinct().all()
    except:
        print("Не получилось считать типы существующих данных")

    # Если пока нет потоков, по умолчанию можно добавить диапазоны для типа данных 'air_temperature'
    if not types:
        types.append(('air_temperature',))


    # /////////////////////////////
    # Обработка отправки формы
    #/////////////////////////////

    # Если произошла отправка формы
    if request.method == "POST":

        # Проверка, введены ли числа в Min, Max
        if is_number(request.form['Min']) and is_number(request.form['Max']):

            # Проверка Max > Min
            input_min = float(request.form['Min'])
            input_max = float(request.form['Max'])
            if input_min < input_max :

                # Проверка, не входит ли введенный диапазон в какой-то из уже существующих (сразу флаг существующего имени)
                try:
                    ranges = db.session.query(Range).all()
                    in_exist_range = False
                    name_has_already = False
                    selected_type = request.form.get('selected_type') #Для разных типов можно свои диапазоны
                    for r in ranges:
                        if (input_min >= r.Min and input_max <= r.Max and r.Type_of_data == selected_type) \
                                or (input_min >= r.Min and input_min <= r.Min and r.Type_of_data == selected_type) \
                                or (input_max >= r.Max and input_max <= r.Max and r.Type_of_data == selected_type) \
                                or (input_min <= r.Min and input_max >= r.Max and r.Type_of_data == selected_type):
                            in_exist_range = True

                        if r.Name == request.form['Name']:
                            name_has_already = True

                    if not in_exist_range:


                        # Проверка, не совпадает ли введенное имя с каким-то из существующих
                        if name_has_already == False:

                            # Добавление диапазона в базу данных
                            range = Range(Min=input_min, Max=input_max, Name=request.form['Name'], Type_of_data=selected_type)
                            try:
                                db.session.add(range)
                                db.session.commit()
                                flash("Диапазон успешно добавлен", "alert-success")
                            except:
                                db.session.rollback()
                                print("Ошибка добавления в БД")
                        else:
                            flash("Введенное имя соответствует имени уже существующего диапазона", "alert-danger")
                    else:
                        flash("Данный диапазон является частью уже существующего", "alert-danger")
                except:
                    print("Не получилось считать диапазоны из БД и отсортировать по полю Min")

            else:
                flash("Max должно быть больше, чем Min (Max > Min)", "alert-danger")

        else:
            flash("Поля Min и Max должны содержать цифры!", "alert-danger")


    return render_template('thread/add_range.html', title="Добавление диапазона", types=types)




#         Изменение записи о диапазоне
#--------------------------------------------------------------------------------

@app.route("/update_range/<id>", methods=("POST","GET"))
@login_required
def update_range(id):

    # Получаем данные о выбранном диапазоне
    try:
        range = Range.query.filter_by(id=id).first()
    except:
        print("Ошибка чтения записи о пользователе")

    # Если произошла отправка формы
    if request.method == "POST":

        # Проверка, введены ли числа в Min, Max
        if is_number(request.form['Min']) and is_number(request.form['Max']):

            # Проверка Max > Min
            input_min = float(request.form['Min'])
            input_max = float(request.form['Max'])
            if input_min < input_max:

                # Проверка, не входит ли введенный диапазон в какой-то из уже существующих (сразу флаг существующего имени)
                # КРОМЕ ВЫБРАННОГО ИЗМЕНЯЕМОГО ДИАПАЗОНА
                try:
                    ranges = db.session.query(Range).all()
                    in_exist_range = False
                    name_has_already = False
                    for r in ranges:
                        if (input_min >= r.Min and input_max <= r.Max and range.id != r.id and r.Type_of_data == range.Type_of_data) \
                                or (input_min >= r.Min and input_min <= r.Min and range.id != r.id and r.Type_of_data == range.Type_of_data) \
                                or (input_max >= r.Max and input_max <= r.Max and range.id != r.id and r.Type_of_data == range.Type_of_data) \
                                or (input_min <= r.Min and input_max >= r.Max and range.id != r.id and r.Type_of_data == range.Type_of_data):
                            in_exist_range = True

                        if r.Name == request.form['Name'] and range.id != r.id:
                            name_has_already = True

                    if not in_exist_range:

                        # Проверка, не совпадает ли введенное имя с каким-то из существующих
                        if name_has_already == False:

                            try:
                                # Изменение данных о диапазоне
                                range.Min=input_min
                                range.Max=input_max
                                range.Name=request.form['Name']
                                db.session.commit()
                                flash("Данные диапазона успешно сохранены", "alert-success")
                            except:
                                db.session.rollback()
                                print("Ошибка изменения диапазона в БД")
                        else:
                            flash("Введенное имя соответствует имени уже существующего диапазона", "alert-danger")
                    else:
                        flash("Выбраннный диапазон является частью уже существующего", "alert-danger")
                except:
                    print("Не получилось считать диапазоны из БД и отсортировать по полю Min")

            else:
                flash("Max должно быть больше, чем Min (Max > Min)", "alert-danger")

        else:
            flash("Поля Min и Max должны содержать цифры!", "alert-danger")


    return render_template('thread/update_range.html', id = range.id, title="Изменение диапазона", range=range)




#         Удаление записи о диапазоне
#--------------------------------------------------------------------------------

@app.route("/delete_range/<id>")
@login_required
def delete_range(id):

    # Удаление выбранного диапазона при условии, что у него нет детей
    try:
        range = db.session.query(Range).filter_by(id=id).first()

        # Проверка, есть ли проблемы, связанные с диапазоном
        if not range.prob:
            db.session.query(Range).filter_by(id=id).delete()
            db.session.commit()
            flash("Диапазон успешно удален", "alert-success")
        else:
            flash("Нельзя удалить диапазон, для него добавлены проблемы!", "alert-danger")

    except:
        db.session.rollback()
        print("Не получилось найти и удалить выбранный диапазон в базе данных")


    # Для отображения всех диапазонов из базы данных
    try:
        ranges = db.session.query(Range).order_by(Range.Min).all()
    except:
        print("Ошибка считывания диапазона из Базы данных")

    return render_template('thread/ranges.html', title="Справочник диапазонов значений", content = ranges)



# *****************************************************************ПРОБЛЕМЫ*******************************************************************


#        Добавление записи о проблеме
#--------------------------------------------------------------------------------
@app.route("/add_problem", methods=("POST","GET"))
@login_required
def add_problem():

    # /////////////////////////////
    # Выпадающий список (Типы)
    # /////////////////////////////
    # Данные для выпадающего списка типов данных
    try:
        types = db.session.query(Range.Type_of_data).distinct().all()

    except:
        print("Не получилось считать диапазоны данных")

    # Если пока нет диапазонов,то и проблемы пока нельзя добавлять
    if not types:
        try:
            problems = db.session.query(Problem).all()
            flash("Нет ни одно диапазона в базе данных, пожалуйста, сначала добавьте диапазон!", "alert-danger")
        except:
            print("Ошибка считывания проблем из Базы данных")
        return render_template('thread/problems.html', title="Справочник проблем", content=problems)

    else:
        # /////////////////////////////
        # Обработка отправки формы
        # /////////////////////////////

        # Если произошла отправка формы
        if request.method == "POST":
            try:

                # Проверка: уникальное ли имя проблемы
                problem_names = db.session.query(Problem.Name).all()
                name_exist = False
                for p_n in problem_names:
                    if request.form['Name'] == p_n[0] :
                        name_exist = True

                # Если имя уникальное, добавляем проблему в БД
                if(name_exist) :
                    flash("Введенное название проблемы принадлежит уже существующей в БД проблеме!", "alert-danger")
                else:
                    problem = Problem(Name = request.form['Name'], Range_Id = request.form['selected_range'])
                    try:
                        db.session.add(problem)
                        db.session.commit()
                        flash("Проблема успешно добавлена", "alert-success")
                    except:
                        db.session.rollback()
                        print("Ошибка добавления проблемы в БД")
            except:
                print("Не получилось считать из БД названия проблем")

        return render_template('thread/add_problem.html', title="Добавление проблемы",types=types)




#     Содержимое выпадающего списка диапазонов
@app.route("/select_ranges/<type>")
@login_required
def select_range(type):
    try:
        ranges = db.session.query(Range).filter_by(Type_of_data=type).all()
    except:
        print("Не вышло получить потоки по типу данных из БД")

    range_Array = []
    for r in ranges:
        rangeObject = {}
        rangeObject['id'] = r.id   # <option value = THIS >
        rangeObject['interval'] = "( " + str(r.Min) + " ) -  ( " + str(r.Max) + " ) " # <option> THIS </option>
        range_Array.append(rangeObject)
    return jsonify({'ranges': range_Array})



#        Изменение записи о проблеме
#--------------------------------------------------------------------------------
@app.route("/update_problem/<id>", methods=("POST","GET"))
@login_required
def update_problem(id):

    # Получаем данные о выбранной проблеме
    try:
        problem = db.session.query(Problem).filter_by(id=id).first()
    except:
        print("Ошибка чтения данных о проблеме в БД")


    # Если произошла отправка формы
    if request.method == "POST":
        try:
            # Проверка: нет ли такого имени у других проблем
            problems = db.session.query(Problem).all()
            selected_name = request.form['Name']
            name_exist = False
            for a_p in problems:
                if selected_name == a_p.Name and problem.id != a_p.id:
                    name_exist = True

            if not name_exist:
                try:
                    # Изменение данных о проблеме
                    problem.Name = selected_name
                    db.session.commit()
                    flash("Данные о проблеме успешно сохранены", "alert-success")
                except:
                    db.session.rollback()
                    print("Ошибка изменения проблемы в БД")
            else:
                flash("Введенное имя соответствует имени уже существующего диапазона", "alert-danger")

        except:
            print("Ошибка чтения всех проблем")


    return render_template('thread/update_problem.html', id = problem.id , title="Изменение проблемы", problem=problem)




#        Удаление записи о проблеме
#--------------------------------------------------------------------------------
@app.route("/delete_problem/<id>")
@login_required
def delete_problem(id):

        # Удаление выбранной проблемы при условии, что у нее нет детей
        try:
            problem = db.session.query(Problem).filter_by(id=id).first()

            # Проверка, есть ли проблемы, связанные с диапазоном
            if not problem.adv:
                db.session.query(Problem).filter_by(id=id).delete()
                db.session.commit()
                flash("Диапазон успешно удален", "alert-success")
            else:
                flash("Нельзя удалить проблему, для нее добавлены советы!", "alert-danger")

        except:
            db.session.rollback()
            print("Не получилось найти и удалить выбранную проблему в базе данных")

        # Для отображения всех диапазонов из базы данных
        try:
            problems = db.session.query(Problem).all()
        except:
            print("Ошибка считывания проблем из Базы данных")

        return render_template('thread/problems.html', title="Справочник проблем", content=problems)



#******************************************************************РЕКОМЕНДАЦИИ*******************************************************************


#        Добавление записи о совете
#--------------------------------------------------------------------------------
@app.route("/add_advice", methods=("POST","GET"))
@login_required
def add_advice():
    # /////////////////////////////
    # Выпадающий список (Типы)
    # /////////////////////////////
    # Данные для выпадающего списка типов данных
    try:
        types = db.session.query(Range.Type_of_data).distinct().all()
        problems = db.session.query(Range.Type_of_data).first()

    except:
        print("Не получилось считать диапазоны данных")


    # Если пока нет проблем в БД, значит, и советы нельзя добавлять
    if not problems:
        try:
            advices = db.session.query(Advice).all()
            flash("Нет ни одно проблемы в БД, пожалуйста, сначала добавьте проблему!", "alert-danger")
        except:
            print("Ошибка считывания советов из Базы данных")
        return render_template('thread/advices.html', title="Справочник проблем", advices=advices)


    else:
        # /////////////////////////////
        # Обработка отправки формы
        # /////////////////////////////

        # Если произошла отправка формы
        if request.method == "POST":
            try:
                advice = Advice(Content = request.form['Content'], Problem_Id = request.form['selected_problem'])
                db.session.add(advice)
                db.session.commit()
                flash("Рекомендация успешно сохранена", "alert-success")
            except:
                db.session.rollback()
                print("Ошибка добавления совета")


        return render_template('thread/add_advice.html', title="Добавление совета", types=types)



#     Содержимое выпадающего списка проблем
@app.route("/select_problems/<type>")
@login_required
def select_problems(type):
    try:
        range = db.session.query(Range).filter_by(Type_of_data=type).first()
        problems = db.session.query(Problem).filter_by(Range_Id=range.id).all()
    except:
        print("Не вышло получить потоки по типу данных из БД")

    problem_Array = []
    for p in problems:
        problemObject = {}
        problemObject['id'] = p.id   # <option value = THIS >
        problemObject['problem_name'] = p.Name # <option> THIS </option>
        problem_Array.append(problemObject)
    return jsonify({'problems': problem_Array})




#        Изменение записи совета
#--------------------------------------------------------------------------------
@app.route("/update_advice/<id>", methods=("POST","GET"))
@login_required
def update_advice(id):

    # Получаем данные о выбранной проблеме
    try:
        advice = db.session.query(Advice).filter_by(id=id).first()
    except:
        print("Ошибка чтения данных о проблеме в БД")


    # Если произошла отправка формы
    if request.method == "POST":
        try:
            advice.Content = request.form['Content']
            db.session.commit()
            flash("Данные о рекомендации успешно сохранены", "alert-success")
        except:
            print("Ошибка изменения рекомендации в БД")


    return render_template('thread/update_advice.html', id = advice.id , title="Изменение совета", advice=advice)



#        Удаление записи совета
#--------------------------------------------------------------------------------
@app.route("/delete_advice/<id>")
@login_required
def delete_advice(id):

        # Удаление выбранной рекомендации
        try:

            db.session.query(Advice).filter_by(id=id).delete()
            db.session.commit()
            flash("Диапазон успешно удален", "alert-success")

        except:
            db.session.rollback()
            print("Не получилось найти и удалить выбранную рекомендацию")


        # Для отображения всех советов
        try:
            advices = db.session.query(Advice).all()
        except:
            print("Ошибка считывания проблем из Базы данных")

        return render_template('thread/advices.html', title="Справочник проблем", advices=advices)
