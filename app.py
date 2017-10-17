from config import *
import json

@lm.user_loader
def load_user(user_id):
    u = Employee.query.filter(Employee.mongo_id == user_id).first()
    if not u:
        return None
    print("Loading User...")
    return User(str(u.mongo_id),bool(u.admin))
    
    
@app.route('/',methods=['GET','POST'])
@login_required
def index():
    user = Employee.query.get(current_user.get_id())
    if len(user.depts) > 1:
        return render_template('multidepts.html', Timecard=Timecard, Employee=Employee) 
    else:
        return redirect(url_for('timeEntry',dept=user.depts[0]),code=307)
  
@app.route('/timecard',methods=['GET','POST'])
def timecard():
    try:
        logout_user()
    except:
        pass
    Next = request.args.get('next')
    return render_template("login.html", next=Next)

@app.route('/portal',methods=['GET','POST'])
@login_required
def portal():
    return render_template('index.html', Employee=Employee)
    
@app.route('/register_emp',methods=['GET','POST'])
@login_required
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
    return redirect(url_for('portal'))
    
    
@app.route('/login', methods=['GET','POST'])
def login():
    Next = request.args.get('next')
    if request.method == 'POST':
        user = Employee.query.filter(Employee.empID == request.form['employee-id']).first()
        if user and bcrypt.check_password_hash(user.password,request.form['employee-password']):
            user_obj = User(str(user.mongo_id))
            login_user(user_obj, remember=True)
            return redirect(Next or url_for('index',Employee=Employee),code=307)
        else:
            flash("Invalid credentials. Try again.")
    else:
        flash("Cannot access that page")
    return redirect(url_for('timecard', next=Next))
    
@app.route('/logout', methods=['GET','POST'])
@login_required
def logout():
    return redirect('/timecard')
        
        
@app.route('/register',methods=['GET','POST'])
@login_required
def register():
    return render_template('register.html')

@app.route('/settings',methods=['GET','POST'])
@login_required
def settings():
    return render_template('settings.html',Employee=Employee)

@app.route('/changePass', methods=["GET","POST"])
@fresh_login_required
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
        return redirect(url_for('portal'))    
    
@app.route('/error', methods=["GET","POST"])
@login_required
def error():
    if request.method=="POST":
        dept = request.args.get('dept')
        user = Employee.query.get(current_user.get_id())
        lastIn = Timecard.query.filter(Timecard.empID==user.empID).descending(Timecard.datetime).first()
        lastIn.warning = True
        lastIn.save()
        user.clockedIn = "None"
        user.save()
        return redirect(url_for('timeEntry',dept=dept,skip=True),code=307)
    else:
        flash("You cannot access that page that way! Please try again!")
        return redirect(url_for('index',Employee=Employee))
        
@app.route('/continue',methods=["GET","POST"])
@login_required
def cont():
    dept = request.args.get('dept')
    return redirect(url_for('timeEntry',skip=True,dept=dept),code=307)

@app.route('/viewTimecard',methods=['GET','POST'])
# @login_required
def view():
    user = Employee.query.get(current_user.get_id())
    entryList = []
    entries = Timecard.query.filter(Timecard.empID == user.empID, Timecard.action == "Clock In").descending(Timecard.datetime)
    for entry in entries:
        entryId = entry.timecardID
        convertedIn = pytz.timezone('UTC').localize(entry.datetime).astimezone(tz)
        try:
            clockOut = Timecard.query.filter(Timecard.timecardID == entryId,Timecard.action == "Clock Out").first()
            convertedOut = pytz.timezone('UTC').localize(clockOut.datetime).astimezone(tz)
            duration = (convertedOut - convertedIn).total_seconds()//.36/10000
            foo = Entry(entry.dept,convertedIn.strftime('%m/%d/%Y %I:%M %p'),convertedOut.strftime('%m/%d/%Y %I:%M %p'),duration)
        except:
            if user.clockedIn == entry.timecardID:
                flag = 1
                out = "Currently Clocked In"
            else:
                flag = 2
                out = "Error"
            foo = Entry(entry.dept,convertedIn.strftime('%m/%d/%Y %I:%M %p'),out,flag=flag)
        entryList.append(foo)
    return render_template('timecard.html',entries=entryList)
    

@app.route('/timeEntry', methods=["GET","POST"])
@login_required
def timeEntry():
    if request.method == "POST":
        dept = request.args.get('dept')
        try:
            skip=bool(request.args.get('skip'))
        except:
            skip = False
        user = Employee.query.get(current_user.get_id())
        clock = Timecard()
        clock.empID = user.empID
        clock.dept = dept
        clock.warning = False
        time = datetime.datetime.now(tz)
        clock.datetime = time
        if user.clockedIn != "None":
            lastIn = Timecard.query.filter(Timecard.timecardID == user.clockedIn).first()
            #lastIn = Timecard.query.filter(Timecard.empID==user.empID).descending(Timecard.datetime).first()
            if (datetime.datetime.now()-lastIn.datetime).total_seconds() > 36000 and not skip:
                    return render_template('warning.html',dept=dept, time=lastIn.datetime.ctime())
            if lastIn.dept == dept:
                clock.action = "Clock Out"
                clock.timecardID = user.clockedIn
                user.clockedIn = "None"
                user.save()
                clock.save()
                flash("You have clocked out as "+dept+" at "+str(time))
                return redirect(url_for('logout'))
            else:
                transition = Timecard()
                transition.empID = user.empID
                transition.dept = lastIn.dept
                transition.timecardID = user.clockedIn
                transition.datetime = time
                transition.action = "Clock Out"
                transition.warning = False
                transition.save()
                flash("You have been clocked out as "+lastIn.dept+" and clocked in as "+dept+" at "+str(time))
        else:
            flash("You have been clocked in as "+dept+" at "+str(time))
        clock.timecardID = uuid.uuid4().hex
        clock.action = "Clock In"
        user.clockedIn = clock.timecardID
        user.save()
        clock.save()
    else:
        flash("You cannot access that page that way! Please try again!")
    return redirect(url_for('timecard'))
    
@app.route('/getCurrentUser')
def getCurrentUser():
    try:
        return Employee.query.get(current_user.get_id()).empID
    except:
        return "NO USER"
    
# @app.route('/getEntry')
# def getEntry():
#     start = int(request.args.get('index'))
#     end = int(request.args.get('num'))+start
#     user = Employee.query.get(current_user.get_id())
#     clockIns = Timecard.query.filter(Timecard.empID == user.empID, Timecard.action == "Clock In").descending(Timecard.datetime).all()
#     for entry in clockIns:
        

@app.route('/<path>')
def catchAll(path):
    return redirect(url_for('index'))

app.debug = True
app.run(host=os.environ['IP'],port=int(os.environ['PORT']))
    
    

    