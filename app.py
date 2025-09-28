from flask import Flask,render_template,request,session,redirect,flash
from flask_mysqldb import MySQL




app=Flask("__main__")

app.secret_key='saurav'
app.config['MYSQL_HOST']='127.0.0.1'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='Sproot@123'
app.config['MYSQL_DB']='minorprojectdb'
app.config['MYSQL_PORT']= 3306

mysql=MySQL(app)

@app.route('/')
def home():
     return render_template('home.html')  

@app.route('/add_expense')
def add_expense():
     return render_template('add_expense.html')  

@app.route('/view_expenses')
def view_expense():
     return render_template('view_expenses.html')  
 

@app.route('/addexpense',methods=['POST'])
def addexpense():
      time_cat = request.form.get("time_category")
      exp_type = request.form.get("expense_type")
      desc = request.form.get("description") or None
      amount = request.form.get("amount")
      exp_date = request.form.get("date")

   
            
      cur = mysql.connection.cursor()
      cur.execute('insert into expenses (time_category,expense_type,description,amount,expense_date) values(%s,%s,%s,%s,%s)',(time_cat,exp_type,desc,amount,exp_date,))
      mysql.connection.commit()
      # database connection close
      cur.close()
      return "Added Expense successfully"

@app.route("/view_expenses_range", methods=["GET", "POST"])
def view_expenses_range():
    expenses = []
    total = 0
    if request.method == "POST":
        category = request.form.get("time_category")
        from_date = request.form.get("from_date")
        to_date = request.form.get("to_date")

        # Validation
        if not category or not from_date or not to_date:
            flash("Please fill all fields", "danger")
            return redirect("/view_expenses_range")
    cur=mysql.connection.cursor()
        # Fetch expenses in date range
    cur.execute("""
            SELECT * FROM expenses 
            WHERE time_category = %s AND expense_date BETWEEN %s AND %s
            ORDER BY expense_date DESC
        """, (category, from_date, to_date))
    expenses = cur.fetchall()

        # Calculate total
    cur.execute("""
            SELECT SUM(amount) AS total FROM expenses 
            WHERE time_category = %s AND expense_date BETWEEN %s AND %s
        """, (category, from_date, to_date))
    result = cur.fetchone()
    total = result[0] if result[0] else 0

    return render_template("view_expenses.html", expenses=expenses, total=total)



if __name__== '__main__':
    app.run(debug=True)