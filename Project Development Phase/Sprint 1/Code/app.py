from turtle import st
from flask import Flask, render_template, request, redirect, url_for, session
from markupsafe import escape
import ibm_db_dbi
import re
import random
import ibm_db
import string

conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=8e359033-a1c9-4643-82ef-8ac06f5107eb.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=30120;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=kvp44692;PWD=TaT7iRVlj02JLW26",'','')
app = Flask(__name__)
app.secret_key = 'ibm'


@app.route('/signUp', methods =['GET', 'POST'])
def signUp():
    message = ''
    if request.method == 'POST' :
        userName = request.form['username']
        password = request.form['password']
        mail = request.form['email']
        try:
            connectionID = ibm_db_dbi.connect(conn, '', '')
        except:
          print("Error")

        sql = "SELECT * FROM credential WHERE email = ?"
        statement = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(statement, 1, mail)
        ibm_db.execute(statement)
        ibm_db.execute(statement)
        account = ibm_db.fetch_row(statement)
        sqlQuery = "SELECT * FROM credential WHERE email = " + "\'" + userName + "\'"
        result = ibm_db.exec_immediate(conn, sqlQuery)
        dictionary = ibm_db.fetch_assoc(result)
        while dictionary != False:
            dictionary = ibm_db.fetch_assoc(result)
  
        if account:
            message = 'Username already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', mail):
            message = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', userName):
            message = 'name must contain only characters and numbers !'
        else:
            sqlQuery2 = "INSERT INTO credential (username, email,password,userid) VALUES (?, ?, ?,?)"
            statement2 = ibm_db.prepare(conn, sqlQuery2)
            ibm_db.bind_param(statement2, 1, userName)
            ibm_db.bind_param(statement2, 2, mail)
            ibm_db.bind_param(statement2, 3, password)
            ibm_db.bind_param(statement2,4,''.join([random.choice(string.ascii_letters
            + string.digits) for n in range(32)]))
            ibm_db.execute(statement2)
            initUserData()
            message = 'You Have Registered Successfully  !'
        return render_template('login.html', message = message)
    else:
        return render_template('login.html')  

  
@app.route('/login',methods =['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' :
        mail = request.form['email']
        password = request.form['password']
        sqlQuery = "SELECT * FROM credential WHERE email = ? and password = ?"
        statement = ibm_db.prepare(conn, sqlQuery)
        ibm_db.bind_param(statement, 1, mail)
        ibm_db.bind_param(statement, 2, password)
        ibm_db.execute(statement)
        currentAccount = ibm_db.fetch_row(statement)
        sqlQuery = "SELECT * FROM credential WHERE email = " + "\'" + mail + "\'" + " and password = " + "\'" + password + "\'"
        res = ibm_db.exec_immediate(conn, sqlQuery)
        dictionary = ibm_db.fetch_assoc(res)

        if currentAccount:
            session['loggedin'] = True
            session['email'] = dictionary["EMAIL"]
            session['userid']=dictionary["USERID"]
            session['username']=dictionary["USERNAME"]
            sqlQuery = "SELECT * FROM user WHERE email = ? "
            statement = ibm_db.prepare(conn, sqlQuery)
            ibm_db.bind_param(statement, 1, mail)
            ibm_db.execute(statement)
            # account = ibm_db.fetch_row(statement)
            return redirect('/mainPage')
        else:
            message = 'Incorrect username / password !'
        
    return render_template('login.html', message = message)

@app.route('/')
def index():
  return render_template('login.html')

@app.route('/mainPage')
def dashboard():
  return render_template('mainPage.html')

@app.route('/addExpense',methods=['GET', 'POST'])
def addExpense():
  if request.method == 'POST' :
    category = request.form['category']
    paymode= request.form['modeofpayment']
    description= request.form['description']
    date = request.form['date']
    amount = request.form['amount']
    sqlQuery = "INSERT INTO expense (category, amount,modeofpayment,date,description,userid) VALUES (?, ?, ?,?,?,?)"
    statement = ibm_db.prepare(conn, sqlQuery)
    ibm_db.bind_param(statement, 1, category)
    ibm_db.bind_param(statement, 2, amount)
    ibm_db.bind_param(statement, 3, paymode)
    ibm_db.bind_param(statement, 4, date)
    ibm_db.bind_param(statement, 5, description)
    ibm_db.bind_param(statement,6,str(session['userid']))
    ibm_db.execute(statement)
    return render_template('addExpense.html')
  else:
    return render_template('addExpense.html')

@app.route('/addCategory',methods=['GET', 'POST'])
def addCategory():
    if request.method == 'POST':
        categoryName = request.form['category']
        limit = float(request.form['range'])
        description = request.form['description']
        sqlQuery = "INSERT INTO category (categoryname, limit,description,userid,balance) VALUES (?, ?, ?,?,?)"
        statement = ibm_db.prepare(conn, sqlQuery)
        ibm_db.bind_param(statement, 1, categoryName)
        ibm_db.bind_param(statement, 2, limit)
        ibm_db.bind_param(statement, 3, description)
        ibm_db.bind_param(statement, 4, str(session['userid']))
        ibm_db.bind_param(statement, 5, 0.0)
        ibm_db.execute(statement)
        return render_template('addCategory.html')
    else:
        return render_template('addCategory.html')



@app.route("/viewHistory")
def viewHistory():
    result = getAllExpenses(str(session['userid']))
    return render_template('viewHistory.html' ,expense = result)

@app.route("/viewProfile")
def viewProfile():
  if request.method == 'POST' :
    print("To be continued")
  else:
    sqlQuery = "SELECT * from user where userid = ?"
    statement = ibm_db.prepare(conn, sqlQuery)
    ibm_db.bind_param(statement,1,str(session['userid']))
    ibm_db.execute(statement)
    result = ibm_db.fetch_assoc(statement)
    return render_template('viewProfile.html',userProfile=result)

@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('userid', None)
   session.pop('email', None)
   return render_template('index.html')


def getAllExpenses(userid):
        sql = "SELECT * from expense where userid = ?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,userid)
        ibm_db.execute(stmt)        
        expense = ibm_db.fetch_both(stmt)
        expensesList = []
        while expense != False:
            expensesList.append(expense)
            expense = ibm_db.fetch_both(stmt)
        return expensesList

def initUserData():
  userid=str(session['userid'])
  username=str(session['username'])
  email=str(session['email'])
  phoneno=""
  currentsavings=0
  sql = "INSERT INTO user (userid,username, email,phoneno,walletid,currentsavings,country,currency,targetdesc) VALUES (?,?, ?, ?,?,?,?,?,?)"
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt, 1, userid)
  ibm_db.bind_param(stmt, 2, username)
  ibm_db.bind_param(stmt, 3, email)
  ibm_db.bind_param(stmt, 4, phoneno)
  ibm_db.bind_param(stmt,5,'WID'+"".join([random.choice(string.ascii_letters+ string.digits) for n in range(32)]))
  ibm_db.bind_param(stmt,6,currentsavings)
  ibm_db.bind_param(stmt,7,"INDIA")
  ibm_db.bind_param(stmt,8,"RUPEES")
  ibm_db.bind_param(stmt,9,"")
  ibm_db.execute(stmt)    
