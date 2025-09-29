from flask import Flask,render_template,request,session,redirect,flash
from flask_mysqldb import MySQL
from datetime import datetime, timedelta





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

@app.route('/set_budget', methods=['GET', 'POST'])
def set_budget():
    if request.method == 'POST':
        time_category = request.form.get("time_category")
        ref_date = request.form.get("reference_date")  # User selects a date
        budget_limit = float(request.form.get("budget_limit"))

        ref_date = datetime.strptime(ref_date, "%Y-%m-%d")

        # Calculate from_date and to_date based on category
        if time_category == "Daily":
            from_date = to_date = ref_date
        elif time_category == "Weekly":
            from_date = ref_date - timedelta(days=ref_date.weekday())
            to_date = from_date + timedelta(days=6)
        elif time_category == "Monthly":
            from_date = ref_date.replace(day=1)
            next_month = ref_date.replace(day=28) + timedelta(days=4)
            to_date = next_month.replace(day=1) - timedelta(days=1)
        elif time_category == "Yearly":
            from_date = ref_date.replace(month=1, day=1)
            to_date = ref_date.replace(month=12, day=31)
        else:
            flash("Invalid time category", "danger")
            return redirect("/set_budget")

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO budget (time_category, from_date, to_date, budget_limit)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE budget_limit = VALUES(budget_limit)
        """, (time_category, from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d"), budget_limit))
        mysql.connection.commit()
        cur.close()

        flash(f"✅ Budget set for {time_category} from {from_date.date()} to {to_date.date()} as ₹{budget_limit}", "success")
        return redirect("/")

    return render_template("set_budget.html")



@app.route('/budget_status')
def budget_status():
    cur = mysql.connection.cursor()

    # Get all budget entries
    cur.execute("SELECT time_category, from_date, to_date, budget_limit FROM budget")
    budgets = cur.fetchall()

    data = []

    for time_cat, from_date, to_date, limit in budgets:
        # Get total spent in that budget period
        cur.execute("""
            SELECT SUM(amount) FROM expenses 
            WHERE time_category = %s AND expense_date BETWEEN %s AND %s
        """, (time_cat, from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")))
        spent = cur.fetchone()[0] or 0
        remaining = limit - spent

        data.append({
            "category": time_cat,
            "from": from_date.strftime('%Y-%m-%d'),
            "to": to_date.strftime('%Y-%m-%d'),
            "limit": round(limit, 2),
            "spent": round(spent, 2),
            "remaining": round(remaining, 2)
        })

    cur.close()

    return render_template("budget_status.html", data=data)

@app.route('/check_budget', methods=['POST'])
def check_budget():
    time_cat = request.form.get("time_category")
    amount = float(request.form.get("amount"))
    exp_date = request.form.get("date")

    # Convert string date to datetime object
    exp_date = datetime.strptime(exp_date, "%Y-%m-%d")

    # Calculate date range based on time category
    if time_cat == "Daily":
        from_date = to_date = exp_date
    elif time_cat == "Weekly":
        from_date = exp_date - timedelta(days=exp_date.weekday())  # Monday
        to_date = from_date + timedelta(days=6)                    # Sunday
    elif time_cat == "Monthly":
        from_date = exp_date.replace(day=1)
        next_month = exp_date.replace(day=28) + timedelta(days=4)
        to_date = next_month.replace(day=1) - timedelta(days=1)
    elif time_cat == "Yearly":
        from_date = exp_date.replace(month=1, day=1)
        to_date = exp_date.replace(month=12, day=31)
    else:
        return {"error": "Invalid time category"}

    cur = mysql.connection.cursor()

    # ✅ Get budget limit for the correct date range
    cur.execute("""
        SELECT budget_limit FROM budget 
        WHERE time_category = %s AND from_date <= %s AND to_date >= %s
    """, (time_cat, exp_date.strftime("%Y-%m-%d"), exp_date.strftime("%Y-%m-%d")))
    budget = cur.fetchone()
    budget_limit = budget[0] if budget else None

    # ✅ Get total spent in that same range
    cur.execute("""
        SELECT SUM(amount) FROM expenses 
        WHERE time_category = %s AND expense_date BETWEEN %s AND %s
    """, (time_cat, from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")))
    spent = cur.fetchone()[0] or 0

    cur.close()

    # ✅ Check if adding this expense exceeds the budget
    over_budget = budget_limit is not None and (spent + amount > budget_limit)

    return {
        "over_budget": over_budget,
        "limit": budget_limit,
        "spent": spent,
        "from_date": from_date.strftime("%Y-%m-%d"),
        "to_date": to_date.strftime("%Y-%m-%d")
    }

if __name__== '__main__':
    app.run(debug=True)