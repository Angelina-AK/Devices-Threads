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


class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(50))
    Name = db.Column(db.String(50))



class Sensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50))

    # Дети
    rng = db.relationship('Range', backref = 'Sensor', uselist=True, lazy='subquery')



class Directory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50))

    # Дети
    rng = db.relationship('Range', backref = 'Directory', uselist=True, lazy='subquery')


class Range(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Min = db.Column(db.Float)
    Max = db.Column(db.Float)
    Name = db.Column(db.String(50))
    Directory_Id = db.Column(db.Integer, db.ForeignKey('directory.id'))
    Sensor_Id = db.Column(db.Integer, db.ForeignKey('sensor.id'))

    # Родители
    dir = db.relationship('Directory', backref = 'Range', uselist=False , lazy='subquery')
    sen = db.relationship('Sensor', backref = 'Range', uselist=False , lazy='subquery')

    # Дети
    prob = db.relationship('Problem', backref = 'Range', uselist=True, lazy='subquery')


class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50))
    Range_Id = db.Column(db.Integer, db.ForeignKey('range.id'))

    # Родители
    rng = db.relationship('Range', backref='Problem', uselist=False , lazy='subquery')

    # Дети
    adv = db.relationship('Advice', backref='Problem', uselist=True, lazy='subquery')



class Advice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Content = db.Column(db.String(200))
    Problem_Id = db.Column(db.Integer, db.ForeignKey('problem.id'))

    # Родители
    prob = db.relationship('Problem', backref='Advice', uselist=False, lazy='subquery')

