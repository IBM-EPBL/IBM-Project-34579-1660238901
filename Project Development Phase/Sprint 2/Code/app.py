from turtle import st
from flask import Flask, render_template, request, redirect, url_for, session
from markupsafe import escape
import ibm_db_dbi
import re
import random
import ibm_db
import string
from datetime import datetime


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
    date = datetime.fromisoformat(request.form['date'])
    amount = request.form['amount']
    sqlQuery = "INSERT INTO expense (category, amount,modeofpayment,addondate,description,userid,expenseid,spentondate) VALUES (?, ?, ?,?,?,?,?,?)"
    statement = ibm_db.prepare(conn, sqlQuery)
    ibm_db.bind_param(statement, 1, category)
    ibm_db.bind_param(statement, 2, amount)
    ibm_db.bind_param(statement, 3, paymode)
    ibm_db.bind_param(statement, 4, datetime.now())
    ibm_db.bind_param(statement, 5, description)
    ibm_db.bind_param(statement,6,str(session['userid']))
    ibm_db.bind_param(statement,7,createId('EXP'))
    ibm_db.bind_param(statement,8,date)
    ibm_db.execute(statement)
    categories = getUserCategories(str(session['userid']))
    return render_template('addExpense.html',categories=categories)
  else:
    categories = getUserCategories(str(session['userid']))
    return render_template('addExpense.html',categories=categories)

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

@app.route("/handleExpense",methods=['GET', 'POST'])
def manageExpense():
  if request.method=='POST' and request.form['action']=='edit':
    editExpense(request)
  elif request.method=='POST' and request.form['action']=='delete':
    deleteExpense(request.form['expenseid'])  
  categories = getUserCategories(str(session['userid']))
  expenses = getAllExpenses(str(session['userid']))
  return render_template('manageExpense.html',expense=expenses,categories=categories)


@app.route("/viewHistory")
def viewHistory():
    result = getAllExpenses(str(session['userid']))
    for i in range(0,len(result)):
      result[i]['SPENTONDATE'] = result[i].get('SPENTONDATE').strftime("%d/%m/%y")
    return render_template('viewHistory.html' ,expense = result)

@app.route("/viewProfile")
def viewProfile():
  if request.method == 'POST':
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
        statement = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(statement,1,userid)
        ibm_db.execute(statement)        
        expense = ibm_db.fetch_both(statement)
        expensesList = []
        while expense != False:
            expensesList.append(expense)
            expense = ibm_db.fetch_both(statement)
        return expensesList

def getUserCategories(userid):
    sql = "SELECT * from category where userid = ?"
    statement = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(statement,1,userid)
    ibm_db.execute(statement)        
    category = ibm_db.fetch_both(statement)
    categoryList = []
    while category != False:
        categoryList.append(category)
        category = ibm_db.fetch_both(statement)
    return categoryList

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
  ibm_db.bind_param(stmt,5,createId['WID'])
  ibm_db.bind_param(stmt,6,currentsavings)
  ibm_db.bind_param(stmt,7,"INDIA")
  ibm_db.bind_param(stmt,8,"RUPEES")
  ibm_db.bind_param(stmt,9,"")
  ibm_db.execute(stmt)    


def editExpense(request):
   sql = "UPDATE expense SET AMOUNT=?, MODEOFPAYMENT=?, SPENTONDATE=?, DESCRIPTION=? WHERE EXPENSEID=?"
   stmt = ibm_db.prepare(conn, sql)
   ibm_db.bind_param(stmt, 1, request.form['amount'])
   ibm_db.bind_param(stmt, 2, request.form['modeofpayment'])
   ibm_db.bind_param(stmt, 3, request.form['date'])
   ibm_db.bind_param(stmt, 4, request.form['description'])
   ibm_db.bind_param(stmt, 5, request.form['expenseid'])
   ibm_db.execute(stmt)

def deleteExpense(expenseid):
  sql="DELETE FROM expense WHERE EXPENSEID = ?;"
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt,1,expenseid)
  ibm_db.execute(stmt)


def createId(pre):
  return pre+''.join([random.choice(string.ascii_letters+ string.digits) for n in range(32)])