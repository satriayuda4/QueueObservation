from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db2.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    #complete = db.Column(db.Boolean)
    arrive_time = db.Column(db.String(100))
    start_time = db.Column(db.String(100))
    fin_time = db.Column(db.String(100))

@app.route('/')
def index():
    #Show All todos
    todo_list = Todo.query.all()
    print(todo_list)
    return render_template('base.html', todo_list=todo_list)

@app.route('/add', methods=['POST'])
def add():
    #Add new Item
    now = datetime.datetime.now()
    #print(now.strftime("%H:%M:%S"))
    title = request.form.get("title")
    new_todo = Todo(title=title,                     
                    arrive_time=now.strftime("%H:%M:%S"),
                    start_time='',
                    fin_time='')
    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for("index"))

@app.route('/start/<int:todo_id>')
def start(todo_id):
    #update Item
    todo = Todo.query.filter_by(id=todo_id).first()
    #todo.complete = not todo.complete
    now = datetime.datetime.now()
    todo.start_time=now.strftime("%H:%M:%S")
    db.session.commit()
    return redirect(url_for("index"))

@app.route('/finish/<int:todo_id>')
def finish(todo_id):
    #delete Item
    todo = Todo.query.filter_by(id=todo_id).first()
    #db.session.delete(todo)
    now = datetime.datetime.now()
    todo.fin_time=now.strftime("%H:%M:%S")
    db.session.commit()
    return redirect(url_for("index"))

#sqlite3 -header -csv c:/sqlite/db2.sqlite "select * from todo;" > todo.csv

if __name__ == "__main__":
    db.create_all()
    app.run(debug = True)

