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
from models import Range,Thread,Problem,Advice
from Thread.Number_Check import is_number
import json
import pandas as pd
import plotly.express as px
import plotly


#   Создание Blueprint
thread_bl = Blueprint('thread',__name__,template_folder='templates',static_folder='static')

#***************************************************************ЗАНЕСЕНИЕ_В_БД*******************************************************

#        Считывание данных с потока и занесение в БД
#--------------------------------------------------------------------------------
@app.route('/get_thread')
def get_thread():
    # Берем данные с сайта
    url = 'http://metadb.ru/flows/18'
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    content = soup.prettify()
    content.replace("\n", "")
    js = eval(content)
    #print(js['air_temperature']) Для проверки

    try:
        ranges = Range.query.filter_by(Type_of_data='air_temperature').all()
        value = js['air_temperature']
        added = False
        for r in ranges:
            if value >= r.Min and value <= r.Max:
                range_id = r.id
                t = Thread(url=url, Type_of_data='air_temperature', Value=value, Range_Id = range_id)
                db.session.add(t)
                db.session.commit()
                flash("Данные о потоке успешно добавлены", "alert-success")
                added = True
                break

        if added == False:
            print("ОШИБКА ДОБАВЛЕНИЯ ПОТОКА, ЗНАЧЕНИЕ НЕ СООТВЕТСТВУЕТ НИ ОДНОМУ ДИАПАЗОНУ")
            flash("Ошибка добавления потока в БД - НЕ СООТВЕТСТВИЕ НИ ОДНОМУ ИЗ ДИАПАЗОНОВ", "alert-danger")
    except:
        db.session.rollback()
        print("Ошибка добавления записи о потоке")
        flash("Ошибка добавления записи о потоке", "alert-danger")
    return render_template('thread/thread.html',title = "Потоки данных", url = 'thread/static/images/air_temperature_plot.png')


#***************************************************************ПОКАЗ_ПОТОКОВ******************************************************************************

#        Страница потоков
#--------------------------------------------------------------------------------
@app.route("/thread")
@login_required
def thread():
    # # Заполнение массивов x y графика
    # #---------------------------------------------------------
    # try:
    #     threads = Thread.query.filter_by(Type_of_data='air_temperature').all()
    #     x = []
    #     y = []
    #     for t in threads:
    #         x.append(t.DateTime)
    #         y.append(t.Value)
    #
    #     # Заполнение значений для зон
    #     ranges = Range.query.filter_by(Type_of_data='air_temperature').order_by(Range.Min).all()
    #     zones = {}
    #     names = []
    #     for r in ranges:
    #         zones.update({r.Min: r.Max})
    #         names.append(r.Name)
    #
    #
    # except:
    #     print("Ошибка считывания данных о потоке")
    #
    # # Рисование графика
    # # ---------------------------------------------------------
    # fig = plt.figure(figsize=(16,8))
    # plt.scatter(x,y, c = 'black', s = 20, label='Полученное значение')
    # plt.grid()
    #
    # # Рисование зон температур
    # colors = ['#0000FF','#4169E1', '#FFCC99', '#FF6633', 'red']
    # #color = colors[i] - если диапазонов 5 и больше не станет
    # i=0
    # for zon in zones:
    #     plt.fill_between(x, zon,
    #                      zones[zon],
    #                      alpha=0.2,
    #                      linewidth = 3,
    #                      linestyle='-',
    #                      label=names[i])
    #     i+=1
    #
    # # Оформление оси времени
    # plt.gca().xaxis.set_major_formatter(mpl.dates.DateFormatter('%d_%h-%H:%M')) #Формат
    # plt.gca().xaxis.set_major_locator(mpl.dates.AutoDateLocator()) #Шаг
    #
    # # Подписи
    # plt.title('График значений с датчика "air_temperature"')
    # plt.xlabel('Date Time')
    # plt.xticks(rotation=30, ha='right')
    # plt.ylabel('Value')
    #
    # plt.legend() # Запись легенд на график
    #
    # # Сохраняем график как изображение и передаем в шаблон
    # # ---------------------------------------------------------
    # fig.savefig('thread/static/images/air_temperature_plot.png', dpi=fig.dpi)
    # return render_template('thread/thread.html',title = "Потоки данных", url = 'thread/static/images/air_temperature_plot.png')


    # получение данных из БД
    #_____________________________________________________

    # Первый график - co2
    x = []
    y = []
    name = []

    # Второй график - humidity
    x_h = []
    y_h = []
    name_h = []

    # Третий график - temperature
    x_t = []
    y_t = []
    name_t = []

    with app.app_context():
        try:
            threads = Thread.query.all()
            for t in threads:
                if t.Type_of_data == "co2":
                    x.append(t.DateTime)
                    y.append(t.Value)
                    name.append(t.rng.Name)
                if t.Type_of_data == "humidity":
                    x_h.append(t.DateTime)
                    y_h.append(t.Value)
                    name_h.append(t.rng.Name)
                    print(t.Value)
                if t.Type_of_data == "temperature":
                    x_t.append(t.DateTime)
                    y_t.append(t.Value)
                    name_t.append(t.rng.Name)
                    print(t.Value)
        except:
            print("ОШИБКА ЧТЕНИЯ ПОТОКОВ ИЗ БД")



    # Заполнение датафреймов
    #_____________________________________________________

    # Первый график - co2
    data = pd.DataFrame()
    data['y'] = y
    data['x'] = x
    data['name'] = name

    # Второй график - humidity
    data_h = pd.DataFrame()
    data_h['y'] = y_h
    data_h['x'] = x_h
    data_h['name'] = name_h

    # Третий график - temperature
    data_t = pd.DataFrame()
    data_t['y'] = y_t
    data_t['x'] = x_t
    data_t['name'] = name_t




    # Построение графика на основе датафрейма
    #_____________________________________________________

    # Первый график - co2
    #*************************

    fig = px.strip(data, x='x', y='y', color='name', \
                   labels={"y": "Значение", "x": "Дата получения значения", "name": "Название области"},\
                   width=1600, height=700, title="Коцентрация co2 в воздухе")
    fig.update_traces(marker_size=10)
    fig.update_layout(font=dict(size=15), template = 'plotly_dark')  # размер шрифта

    # Выбор: за последний день/месяц/год
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1 день",
                         step="day",
                         stepmode="backward"),
                    dict(count=1,
                         label="1 месяц",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="1 год",
                         step="year",
                         stepmode="todate"),
                    dict(label="Все значения",
                         step="all")
                ]),
                bgcolor='#000000',
                bordercolor='#FFFFFF',
                font = dict(size=15)
            ),
            type="date"
        )
    )

    graph_co2 = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)



    # Второй график - humidity
    # *************************

    fig_h = px.strip(data_h, x='x', y='y', color='name', \
                   labels={"y": "Значение", "x": "Дата получения значения", "name": "Название области"}, \
                   width=1600, height=700, title="Влажность воздуха")
    fig_h.update_traces(marker_size=10)
    fig_h.update_layout(font=dict(size=15), template='plotly_dark')  # размер шрифта

    # Выбор: за последний день/месяц/год
    fig_h.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1 день",
                         step="day",
                         stepmode="backward"),
                    dict(count=1,
                         label="1 месяц",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="1 год",
                         step="year",
                         stepmode="todate"),
                    dict(label="Все значения",
                         step="all")
                ]),
                bgcolor='#000000',
                bordercolor='#FFFFFF',
                font=dict(size=15)
            ),
            type="date"
        )
    )

    graph_hum = json.dumps(fig_h, cls=plotly.utils.PlotlyJSONEncoder)

    # Третий график - temperature
    # *************************

    fig_t = px.strip(data_t, x='x', y='y', color='name', \
                     labels={"y": "Значение", "x": "Дата получения значения", "name": "Название области"}, \
                     width=1600, height=700, title="Температура")
    fig_t.update_traces(marker_size=10)
    fig_t.update_layout(font=dict(size=15), template='plotly_dark')  # размер шрифта

    # Выбор: за последний день/месяц/год
    fig_t.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1 день",
                         step="day",
                         stepmode="backward"),
                    dict(count=1,
                         label="1 месяц",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="1 год",
                         step="year",
                         stepmode="todate"),
                    dict(label="Все значения",
                         step="all")
                ]),
                bgcolor='#000000',
                bordercolor='#FFFFFF',
                font=dict(size=15)
            ),
            type="date"
        )
    )


    graph_temp = json.dumps(fig_t, cls=plotly.utils.PlotlyJSONEncoder)



    return render_template('thread/thread.html',title = "Потоки данных",graph_co2=graph_co2,graph_hum=graph_hum,graph_temp=graph_temp)


#--------------------------------------------------------------------------------
#        Страница проблем данных с потоков (ОТЧЕТ)
#--------------------------------------------------------------------------------
@app.route("/thread_problem")
@login_required
def thread_problem():

    #Считывание данных и заполнение строковой переменной для вывода
    try:
        threads = Thread.query.all()

        problem_information =""

        # проходимся по всем потокам и собираем соответствующие им диапазоны и проблемы с решениями
        for t in threads:
            range = Range.query.filter_by(id=t.Range_Id).first()
            problems = Problem.query.filter_by(Range_Id=range.id).all()
            if problems:
                advices = {}
                for p in problems:
                    advices.update({p.Name: (Advice.query.filter_by(Problem_Id=p.id).all())})

                # Формируем строковый вывод
                problem_information += "\n\nДата потока :" + str(t.DateTime)
                problem_information += "\nТип данных :" + str(t.Type_of_data)
                problem_information += "\nПолученное значение :" + str(t.Value)
                for a in advices:
                    problem_information += "\n\tДля данных соответствует проблема : " + a
                    for adv in advices[a]:
                        problem_information += "\n\t\tРешение: " + adv.Content
                problem_information += "\n_____________________________________________________________________________________"
            else:
                print("Со значениям все хорошо, проблем нет")
    except:
        print("Ошибка считывания данных о проблемах в потоках")
    return render_template('thread/thread_problem.html', title="Проблемы на основании данных с потоков", text = problem_information)



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
