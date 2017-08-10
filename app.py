from flask import request, flash, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required, fresh_login_required, current_user
import os, datetime, pytz

from config import *

@lm.user_loader
def load_user(user_id):
    u = Employee.query.filter(Employee.mongo_id == user_id).first()
    if not u:
        return None
    return User(str(u.mongo_id),bool(u.admin))
    
@app.route('/timecard')
def timecard():
    Next = request.args.get('next')
    return render_template("login.html", next=Next)

@app.route('/')
@login_required
def index():
    user = Employee.query.get(current_user.get_id())
    if len(user.depts) == 1:
        return redirect('/timeEntry/'+user.depts[0])
    else:
        return render_template('multidepts.html', Employee=Employee)


@app.route('/portal')
@login_required
def portal():
    return render_template('index.html', Employee=Employee)
    
@app.route('/register_emp',methods=['GET','POST'])
def register_emp():
    if request.method=="POST":
        fn = request.form['employee-fn']
        ln = request.form['employee-ln']
        empID = request.form['employee-id']
        try:
            admin = str(request.form['employee-admin'])=="on"
        except:
            admin = False
        newEmp = Employee()
        newEmp.init(fn,ln,empID,admin)
        flash("Employee added! Employee ID: "+empID+" Temporary Password: "+generatePassword(fn,ln,empID))
    else:
        flash("You are not authorized to access this page.")
    return redirect('/')
    
    
@app.route('/login', methods=['GET','POST'])
def login():
    Next = request.args.get('next')
    if request.method == 'POST':
        user = Employee.query.filter(Employee.empID == request.form['employee-id']).first()
        if user and bcrypt.check_password_hash(user.password,request.form['employee-password']):
            user_obj = User(str(user.mongo_id))
            login_user(user_obj, remember=False)
            print(Next)
            return redirect(Next or url_for('index',Employee=Employee))
        flash("Invalid credentials. Try again.")
        return render_template('login.html', next=Next)
    flash("Cannot access that page")
    return render_template('login.html', next=Next)

@app.route('/logout', methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    return redirect('/timecard')
        
        
@app.route('/register',methods=['GET','POST'])
#@login_required
def register():
    #if request.method=="POST":
        return render_template('register.html')
    #else:
        #return redirect('/')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html',Employee=Employee)

@app.route('/changePass', methods=["GET","POST"])
@login_required
def changePass():
    if request.method=="POST":
        user = Employee.query.get(current_user.get_id())
        if bcrypt.check_password_hash(user.password,request.form['current-pass']) and request.form['new-pass']==request.form['new-pass-confirm']:
            user.password = bcrypt.generate_password_hash(request.form['new-pass'])
            user.save()
            flash("Password successfully changed.")
        else:
            flash("Could not authenticate password change. Please try again.")
        return redirect('/settings')
    else:
        return redirect('/')    
    
@app.route('/error', methods=["GET","POST"])
@login_required
def error():
    dept = request.args.get('dept')
    user = Employee.query.get(current_user.get_id())
    lastIn = Timecard.query.filter(Timecard.empID==user.empID).descending(Timecard.datetime).first()
    lastIn.warning = True
    lastIn.save()
    user.clockedIn = "None"
    user.save()
    return redirect(url_for('timeEntry',dept=dept,skip=True))
    
@app.route('/continue',methods=["GET","POST"])
@login_required
def cont():
    dept = request.args.get('dept')
    return redirect(url_for('timeEntry',skip=True,dept=dept))
    
@app.route('/timeEntry', methods=["GET","POST"])
#login_required
def timeEntry():
    dept = request.args.get('dept')
    print(dept)
    try:
        skip=bool(request.args.get('skip'))
    except:
        skip = False
    user = Employee.query.get(current_user.get_id())
    clock = Timecard()
    clock.empID = user.empID
    clock.dept = dept
    clock.warning = False
    time = datetime.datetime.now(pytz.timezone('America/Los_Angeles'))
    clock.datetime = time
    if user.clockedIn != "None":
        lastIn = Timecard.query.filter(Timecard.empID==user.empID).descending(Timecard.datetime).first().datetime
        if (datetime.datetime.now()-lastIn).total_seconds() > 36000 and not skip:
                return render_template('warning.html',dept=dept, time=lastIn.ctime())
        if user.clockedIn == dept:
            clock.action = "Clock Out"
            user.clockedIn = "None"
            user.save()
            clock.save()
            flash("You have clocked out as "+dept+" at "+str(time))
            return redirect('/logout')
        else:
            transition = Timecard()
            transition.empID = user.empID
            transition.dept = user.clockedIn
            transition.datetime = time
            transition.action = "Clock Out"
            transition.warning = False
            transition.save()
            flash("You have been clocked out as "+user.clockedIn+" and clocked in as "+dept+" at "+str(time))
    else:
        flash("You have been clocked in as "+dept+" at "+str(time))
    clock.action = "Clock In"
    user.clockedIn = dept
    user.save()
    clock.save()
    return redirect('/logout')
    
    
    
    
app.debug = True
app.run(host=os.environ['IP'],port=int(os.environ['PORT']))
    
    

    