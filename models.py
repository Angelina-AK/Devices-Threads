from app import db
from sqlalchemy import BLOB
from datetime import datetime

#------------------------------------------------------------------------------------------
#                   Классы Базы Данных "database.db"
#------------------------------------------------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fio = db.Column(db.String(50), unique=True)
    login = db.Column(db.String(50), nullable=True)
    psw = db.Column(db.String(500), nullable = True)
    avatar = db.Column(BLOB, default = None)



class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(50))
    Type_of_data = db.Column(db.String(50))
    Value = db.Column(db.Float)
    DateTime = db.Column(db.DateTime(), default= datetime.now)
    Range_Id = db.Column(db.Integer, db.ForeignKey('range.id'))

    # Родитель
    rng = db.relationship('Range', backref = 'Thread', uselist=False , lazy='subquery')
    # lazy='subquery'



class Range(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Min = db.Column(db.Float)
    Max = db.Column(db.Float)
    Name = db.Column(db.String(50))
    Type_of_data = db.Column(db.String(50))

    # Ссылка на детей
    thre = db.relationship('Thread', backref = 'Range', uselist=True, lazy='subquery')
    prob = db.relationship('Problem', backref = 'Range', uselist=True, lazy='subquery')



class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50))
    Range_Id = db.Column(db.Integer, db.ForeignKey('range.id'))

    # Родитель
    rng = db.relationship('Range', backref='Problem', uselist=False , lazy='subquery')

    # Ссылка на детей
    adv = db.relationship('Advice', backref='Problem', uselist=True, lazy='subquery')



class Advice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Content = db.Column(db.String(200))
    Problem_Id = db.Column(db.Integer, db.ForeignKey('problem.id'))

    # Родитель
    prob = db.relationship('Problem', backref='Advice', uselist=False, lazy='subquery')

