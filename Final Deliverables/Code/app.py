from flask import Flask, render_template, request, redirect, url_for, session , flash
import re
import random
import ibm_db
import string
import credentials
from datetime import datetime
from flask_mail import Mail, Message


conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=8e359033-a1c9-4643-82ef-8ac06f5107eb.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=30120;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=kvp44692;PWD=TaT7iRVlj02JLW26",'','')
app = Flask(__name__)
app.secret_key = 'ibm'
app.config['SECRET_KEY'] = 'top-secret'
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'apikey'
app.config['MAIL_PASSWORD'] = credentials.SENDGRID_API_KEY
app.config['MAIL_DEFAULT_SENDER'] = credentials.MAIL_DEFAULT_SENDER
mail = Mail(app)

@app.route('/signUp', methods =['GET', 'POST'])
def signUp():
    message = ''
    if request.method == 'POST' :
        userName = request.form['username']
        password = request.form['password']
        mail = request.form['email']
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
            currentid=createId('')
            sqlQuery2 = "INSERT INTO credential (username, email,password,userid) VALUES (?, ?, ?,?)"
            statement2 = ibm_db.prepare(conn, sqlQuery2)
            ibm_db.bind_param(statement2, 1, userName)
            ibm_db.bind_param(statement2, 2, mail)
            ibm_db.bind_param(statement2, 3, password)
            ibm_db.bind_param(statement2,4,currentid)
            ibm_db.execute(statement2)
            initUserData(currentid,userName,mail)
            message = 'You Have Registered Successfully!'
            sendMail('Send Grid Registration Successful!!','Registration Successful','You have successfully created an account in Personal Expense Tracker!',mail)
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
            lineChart = lineChartData(dictionary["USERID"])
            barChart = barCharData(str(session['userid']))
            categoryNames = getCategoryNames()
            return render_template('mainPage.html',lineChart=lineChart,barChart=barChart,categoryNames=categoryNames,size = len(barChart),userName = session['username'])
        else:
            message = 'Incorrect username / password !'
        
    return render_template('login.html', message = message)

@app.route('/')
def index():
  return render_template('login.html')

@app.route('/mainPage')
def dashboard():
  lineChart = lineChartData(str(session['userid']))
  barChart = barCharData(str(session['userid']))
  categoryNames = getCategoryNames()
  return render_template('mainPage.html',lineChart=lineChart,barChart = barChart,categoryNames=categoryNames,size = len(barChart),userName = session['username'])

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
    updateBudget(category,amount,"add")
    categories = getUserCategories(str(session['userid']))
    return render_template('addExpense.html',categories=categories,userName = session['username'])
  else:
    categories = getUserCategories(str(session['userid']))
    return render_template('addExpense.html',categories=categories,userName = session['username'])

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
        insertBudget(limit,categoryName)
        return render_template('addCategory.html',userName = session['username'])
    else:
        return render_template('addCategory.html',userName = session['username'])

@app.route("/handleExpense",methods=['GET', 'POST'])
def manageExpense():
  if request.method=='POST' and request.form['action']=='edit':
    editExpense(request)
  elif request.method=='POST' and request.form['action']=='delete':
    deleteExpense(request.form['expenseid'])  
  categories = getUserCategories(str(session['userid']))
  expenses = getAllExpenses(str(session['userid']))
  return render_template('manageExpense.html',expense=expenses,categories=categories,userName = session['username'])


@app.route("/viewHistory")
def viewHistory():
    result = getAllExpenses(str(session['userid']))
    for i in range(0,len(result)):
      result[i]['SPENTONDATE'] = result[i].get('SPENTONDATE').strftime("%d/%m/%y")
    return render_template('viewHistory.html' ,expense = result,userName = session['username'])

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
    return render_template('viewProfile.html',userProfile=result,userName = session['username'])

@app.route("/changeLimit",methods=['GET', 'POST'])
def changeLimit():
  if request.method == 'POST' :
   print(request.form['range'],request.form['description'])
   sql = "UPDATE category SET LIMIT=?, DESCRIPTION=? WHERE USERID=? AND CATEGORYNAME=?"
   stmt = ibm_db.prepare(conn, sql)
   ibm_db.bind_param(stmt, 1, request.form['range'])
   ibm_db.bind_param(stmt, 2, request.form['description'])
   ibm_db.bind_param(stmt, 3, str(session['userid']))
   ibm_db.bind_param(stmt, 4, request.form['category'])
   ibm_db.execute(stmt)
   categories=CategoryDetails()
  else:
    categories=CategoryDetails()
  return render_template('changeLimit.html',categories=categories)


@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('userid', None)
   session.pop('email', None)
   return redirect("/")

def CategoryDetails():
  sql = "SELECT * from category where userid = ?"
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt,1,str(session['userid']))
  ibm_db.execute(stmt)        
  category = ibm_db.fetch_both(stmt)
  categoryList = []
  while category != False:
    categoryList.append(category)
    category = ibm_db.fetch_both(stmt)
  return categoryList

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
    category = ibm_db.fetch_assoc(statement)
    categoryList = []
    while category != False:
        categoryList.append(category)
        category = ibm_db.fetch_assoc(statement)
    return categoryList

def initUserData(userid,userName,mail):
  sql = "INSERT INTO user (userid,username, email,phoneno,walletid,currentsavings,country,currency,targetdesc) VALUES (?,?, ?, ?,?,?,?,?,?)"
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt, 1, userid)
  ibm_db.bind_param(stmt, 2, userName)
  ibm_db.bind_param(stmt, 3, mail)
  ibm_db.bind_param(stmt, 4, "")
  ibm_db.bind_param(stmt,5,createId('WID'))
  ibm_db.bind_param(stmt,6,0.0)
  ibm_db.bind_param(stmt,7,"INDIA")
  ibm_db.bind_param(stmt,8,"RUPEES")
  ibm_db.bind_param(stmt,9,"")
  ibm_db.execute(stmt)    


def editExpense(request):
   currentBalance = getExpenseBalance(request.form['expenseid']) 
   updateBudget(request.form['category'],currentBalance,"sub")
   updateBudget(request.form['category'],float(request.form['amount']),"add")
   sql = "UPDATE expense SET AMOUNT=?, MODEOFPAYMENT=?, SPENTONDATE=?, DESCRIPTION=? WHERE EXPENSEID=?"
   stmt = ibm_db.prepare(conn, sql)
   ibm_db.bind_param(stmt, 1, request.form['amount'])
   ibm_db.bind_param(stmt, 2, request.form['modeofpayment'])
   ibm_db.bind_param(stmt, 3, datetime.fromisoformat(request.form['date']))
   ibm_db.bind_param(stmt, 4, request.form['description'])
   ibm_db.bind_param(stmt, 5, request.form['expenseid'])
   ibm_db.execute(stmt)

def getExpenseBalance(expenseid):
  sql = "Select amount from expense where expenseid= ?"
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt, 1, expenseid)
  ibm_db.execute(stmt)
  amount = ibm_db.fetch_assoc(stmt)
  return amount.get('AMOUNT')

  

def deleteExpense(expenseid):
  updateBudget(request.form['category'],request.form['amount'],"sub")
  sql="DELETE FROM expense WHERE EXPENSEID = ?;"
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt,1,expenseid)
  ibm_db.execute(stmt)

def lineChartData(userid):
  monthlyExpenses = {'1':0.0,'2':0.0,'3':0.0,'4':0.0,'5':0.0,'6':0.0,'7':0.0,'8':0.0,'9':0.0,'10':0.0,'11':0.0,'12':0.0}
  expenses = getAllExpenses(userid)
  for expense in expenses:
    date = expense.get('SPENTONDATE')
    monthlyExpenses[str(date.month)] = monthlyExpenses[str(date.month)]+expense.get('AMOUNT')
  return list(monthlyExpenses.values())

def getCategoryNames():
  sql="SELECT DISTINCT CATEGORY FROM expense WHERE USERID=? "
  statement = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(statement,1,str(session['userid']))
  ibm_db.execute(statement)
  category = ibm_db.fetch_assoc(statement)
  categoryNames = []
  while category != False:
    categoryNames.append(category.get('CATEGORY'))
    category = ibm_db.fetch_both(statement)
  print(categoryNames)
  return categoryNames

def barCharData(userid):
  categoryData = []
  categories = getCategoryNames()
  expenses = getAllExpenses(userid)
  for category in categories:
    monthlyExpenses = {'1':0.0,'2':0.0,'3':0.0,'4':0.0,'5':0.0,'6':0.0,'7':0.0,'8':0.0,'9':0.0,'10':0.0,'11':0.0,'12':0.0}
    for expense in expenses:
      if(expense.get('CATEGORY')==category):
        date = expense.get('SPENTONDATE')
        monthlyExpenses[str(date.month)] = monthlyExpenses[str(date.month)]+expense.get('AMOUNT')
    categoryData.append(list(monthlyExpenses.values()))
  return categoryData

#changed
def sendMail(body,htmlHead,message,mailId):
  recipient = []
  recipient.append(mailId)
  msg = Message('Twilio SendGrid', recipients=recipient)
  msg.body = (body)
  msg.html = ('<h1>'+htmlHead+'</h1><p>'+message+'</p>')
  mail.send(msg)
  flash(f'A test message was sent to {recipient}.')

def insertBudget(limit,categoryName):
  sql = "INSERT INTO budgeting (userid,limit, balance,categoryName) VALUES (?,?, ?, ?)"
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt, 1, str(session['userid']))
  ibm_db.bind_param(stmt, 2, limit)
  ibm_db.bind_param(stmt, 3, 0.0)
  ibm_db.bind_param(stmt, 4, categoryName)
  ibm_db.execute(stmt)    

def updateBudget(categoryName,amount,function):
  balance = getCurrentBalance(categoryName)
  print(balance,'balance')
  if(function == 'add'):
    currBalance = balance.get('BALANCE')+float(amount)
    print(currBalance,'add')
  elif(function == 'sub'):
    currBalance = abs(balance.get('BALANCE')- float(amount))
    print(currBalance,'sub')

  if(balance.get('LIMIT')<currBalance):
    sendMail('The limit for Category: '+categoryName+' has been reached!',' Category: '+categoryName+' limit exceeded','The limit set on '+categoryName+' has been reached. Kindly refrain from spending more.',str(session['email']))
  sql = "UPDATE budgeting SET balance = ? WHERE userid=? and categoryname = ?"
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt, 1,currBalance)
  ibm_db.bind_param(stmt, 2, str(session['userid']))
  ibm_db.bind_param(stmt, 3, categoryName)
  ibm_db.execute(stmt)

def getCurrentBalance(categoryName):
  sql = "SELECT balance,limit from budgeting WHERE userid = ? and categoryname = ?" 
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt, 1, str(session['userid']))
  ibm_db.bind_param(stmt, 2, categoryName)
  ibm_db.execute(stmt)
  balance = ibm_db.fetch_assoc(stmt)  
  print(balance)
  return balance

def createId(pre):
  return pre+''.join([random.choice(string.ascii_letters+ string.digits) for n in range(32)])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)