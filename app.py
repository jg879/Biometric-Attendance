from flask import Flask, render_template, request, session, redirect, url_for, Response
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import datetime
import cv
import faceScan as fs
import multifaceUpload as mfu


app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"

cred = credentials.Certificate("serviceAccountKey.json")
appSettings = {'databaseURL': 'https://biometric-attendance-54301-default-rtdb.asia-southeast1.firebasedatabase.app/'}
firebase_admin.initialize_app(cred, appSettings)

ref = db.reference('/')

teacher_ref = ref.child('teachers')
attendance_ref = ref.child('attendance')
data = teacher_ref.get()
user_password = {}
for i in data:
    user_password[i] = data[i]['password']

teach_class = {}
for i in data:
    teach_class[i] = data[i]['class']



@app.route("/", methods = ['GET', 'POST'])
def index():
    if request.method == 'POST':
        user = request.form.get('user')
        password = request.form.get('password')
        if not user:
            return render_template("login.html", error = "Please enter username")

        if user == "admin" and password == "admin":
            session["user"] = user
            return redirect(url_for('admin'))
        
        elif user in user_password and password == user_password[user]:
            session["user"] = user
            return redirect(url_for('home'))
        else:
            return render_template("login.html", error="Invalid Password")
        
    return render_template("login.html")

@app.route("/video")
def video():
    user = session.get('user')
    return Response(cv.gen(teach_class[user]), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/home")
def home():
    teacher_ref = ref.child('teachers')
    data = teacher_ref.get()
    user_password = {}
    for i in data:
        user_password[i] = data[i]['password']

    teach_class = {}
    for i in data:
        teach_class[i] = data[i]['class']
    user = session.get('user')
    tdate = datetime.date.today()
    tdate = str(tdate)

    attendance_ref = ref.child('attendance')
    stu_data = attendance_ref.get()

    stu_count = 0
    
    for i in stu_data:
        if(stu_data[i]['class'] == teach_class[user]):
            stu_count += 1

    enrolls = list(stu_data.keys())
    lst = list(stu_data[enrolls[0]])
    if tdate not in lst:
        for i in enrolls:
            attendance_ref.child(i).update({tdate: 0})

    if user is None:
        return redirect(url_for('index'))
    return render_template("home.html", user = user, students = stu_count)

@app.route("/admin")
def admin():
    user = session.get('user')
    if user is None:
        return redirect(url_for('index'))
    attendance_ref = ref.child('attendance')
    stu_data = attendance_ref.get()
    stu_count = len(stu_data)

    teacher_ref = ref.child('teachers')
    teach_data = teacher_ref.get()
    teach_count = len(teach_data)
    return render_template("index.html", students = stu_count, teachers = teach_count)

@app.route("/addUser")
def addUser():
    user = session.get('user')
    if user is None:
        return redirect(url_for('index'))
    return render_template("addUser.html", user = user)


@app.route("/addSingleUser")
def addSingleUser():
    return Response(fs.gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect(url_for('index'))


@app.route("/addTeacher", methods=["GET", "POST"])
def addTeacher():
    user = session.get('user')
    if user is None:
        return redirect(url_for('index'))
    
    teacher_ref = ref.child('teachers')
    t_data = teacher_ref.get()
    teach_data = []

    for i in t_data:
        d = {}
        d["username"] = i
        d["name"] = t_data[i]["name"]
        d["class"] = t_data[i]["class"]
        teach_data.append(d)


    if request.method == "POST":
        username = request.form.get('username')
        name = request.form.get('name')
        password = request.form.get('password')
        clas = request.form.get('class')

        if username in t_data:
            return render_template("addTeacher.html", error = "Username already exists!", l = len(teach_data), teach_data = teach_data)

        

        d = {}
        rec = {}
        d['name'] = name
        d['password'] = password
        d['class'] = int(clas)
        rec[username] = d
        teacher_ref.update(rec)
        return render_template("addTeacher.html", l = len(teach_data), teach_data = teach_data)

    return render_template("addTeacher.html", l = len(teach_data), teach_data = teach_data)

@app.route("/addSingleStudent", methods=["GET", "POST"])
def addSingleStudent():
    user = session.get('user')
    if user is None:
        return redirect(url_for('index'))
    if request.method == "POST":
        enroll = request.form.get('enroll')
        name = request.form.get('name')
        clas = request.form.get('class')
        fs.sendData(enroll, name, clas)
    
    attendance_ref = ref.child('attendance')
    stu_data = attendance_ref.get()
    student_data = []

    for i in stu_data:
        d = {}
        d["enroll"] = i
        d["name"] = stu_data[i]["name"]
        d['class'] = stu_data[i]['class']
        l = stu_data[i].values()
        present = 0
        absent = 0
        for i in l:
            if i == 1:
                present += 1
            elif i == 0:
                absent += 1
        total = present + absent

        d["present"] = present
        d["absent"] = absent
        d["total"] = total
        try:
            d["percent"] = round((present/total) * 100, 1)
        except:
            d["percent"] = 0
        student_data.append(d)

    return render_template("addSingleStudent.html", l = len(student_data), student_data = student_data)

@app.route("/addMultiStudent", methods=["GET", "POST"])
def addMultiStudent():
    user = session.get('user')
    if user is None:
        return redirect(url_for('index'))
    
    attendance_ref = ref.child('attendance')
    stu_data = attendance_ref.get()
    student_data = []

    for i in stu_data:
        d = {}
        d["enroll"] = i
        d["name"] = stu_data[i]["name"]
        d['class'] = stu_data[i]['class']

        l = stu_data[i].values()
        present = 0
        absent = 0
        for i in l:
            if i == 1:
                present += 1
            elif i == 0:
                absent += 1
        total = present + absent

        d["present"] = present
        d["absent"] = absent
        d["total"] = total
        try:
            d["percent"] = round((present/total) * 100, 1)
        except:
            d["percent"] = 0
        student_data.append(d)


    if request.method == "POST":
        path = request.form.get('path')
        error = mfu.uploadMultiFaces(path)
        if(error == 0):
            return render_template("addMultiStudent.html", l = len(student_data), student_data = student_data, error = "Face not found in an image")


    return render_template("addMultiStudent.html", l = len(student_data), student_data = student_data)

@app.route("/searchStudent", methods = ["GET", "POST"])
def searchStudent():
    user = session.get('user')
    user_flag = 0

    attendance_ref = ref.child('attendance')
    stu_data = attendance_ref.get()
    student_data = []

    for i in stu_data:
        d = {}
        d["enroll"] = i
        d["name"] = stu_data[i]["name"]
        d["class"] = stu_data[i]["class"]

        l = stu_data[i].values()
        present = 0
        absent = 0
        for i in l:
            if i == 1:
                present += 1
            elif i == 0:
                absent += 1
        total = present + absent

        d["present"] = present
        d["absent"] = absent
        d["total"] = total
        try:
            d["percent"] = round((present/total) * 100, 1)
        except:
            d["percent"] = 0
        student_data.append(d)
    
    student_data_teach = []
    if user == 'admin':
        user_flag = 1
    if user_flag != 1:
        for i in stu_data:
            d = {}
            if(stu_data[i]['class'] == teach_class[user]):
                d["enroll"] = i
                d["name"] = stu_data[i]["name"]
                d["class"] = stu_data[i]["class"]

                l = stu_data[i].values()
                present = 0
                absent = 0
                for i in l:
                    if i == 1:
                        present += 1
                    elif i == 0:
                        absent += 1
                total = present + absent

                d["present"] = present
                d["absent"] = absent
                d["total"] = total
                try:
                    d["percent"] = round((present/total) * 100, 1)
                except:
                    d["percent"] = 0
                student_data_teach.append(d)

    if request.method == "POST":
        enroll = request.form.get('enroll')

        student_data = {}

        try:

            d = stu_data[enroll]
        except:
            return render_template("searchStudent.html", l = 0, student_data = None, error="No Student Found")

        student_data["enroll"] = enroll
        student_data["name"] = d["name"]
        student_data["class"] = d["class"]
        l = d.values()
        present = 0
        absent = 0
        for i in l:
            if i == 1:
                present += 1
            elif i == 0:
                absent += 1
        total = present + absent

        student_data["present"] = present
        student_data["absent"] = absent
        student_data["total"] = total
        try:
            student_data["percent"] = round((present/total) * 100, 1)
        except:
            student_data["percent"] = 0
        
        l = []
        l.append(student_data)
        student_data = l

        if user_flag:     
            return render_template("searchStudent.html", l = len(student_data), student_data = student_data)

        return render_template("teach_search.html", l = len(student_data), student_data = student_data)
    
    
    if user_flag:
        return render_template("searchStudent.html", l = len(student_data), student_data = student_data)
    
    return render_template("teach_search.html", l = len(student_data_teach), student_data = student_data_teach)
    

@app.route('/take_attendance')
def take_attendance():
    user = session.get('user')
    if user is None:
        return redirect(url_for('index'))
    # attendance_ref = ref.child('attendance')
    # stu_data = attendance_ref.get()
    # student_data = []
    # for i in stu_data:
    #     d = {}
    #     d["enroll"] = i
    #     d["name"] = stu_data[i]["name"]
    #     tdate = datetime.date.today()
    #     tdate = str(tdate)
    #     d["present"] = stu_data[i][tdate]
    #     student_data.append(d)

    return render_template("take_attendance.html")

@app.route('/edit_attendance', methods = ["GET", "POST"])
def edit_attendance():
    user = session.get('user')
    if user is None:
        return redirect(url_for('index'))
    attendance_ref = ref.child('attendance')
    stu_data = attendance_ref.get()
    student_data = []
    tdate = datetime.date.today()
    tdate = str(tdate)
    for i in stu_data:
        d = {}
        if(stu_data[i]['class'] == teach_class[user]):
            d["enroll"] = i
            d["name"] = stu_data[i]["name"]
            d["status"] = stu_data[i][tdate]
            student_data.append(d)
    if request.method == "POST":
        x = 0
        for i in stu_data:
            d = {}
            if(stu_data[i]['class'] == teach_class[user]):
                s = 'status' + str(i)
                x += 1
                status = request.form.get(s)
                if(status == "on"):
                    status = 1
                else:
                    status = 0
                stu_data[i][tdate] = status
        attendance_ref.update(stu_data)
        return redirect(url_for('edit_attendance'))


    if(len(student_data ) > 0):
        return render_template("edit_attendance.html", l = len(student_data), student_data = student_data, tdate = tdate, clas = teach_class[user])
    return render_template("edit_attendance.html", l = 0, student_data = None, tdate = tdate, clas = teach_class[user])

@app.route('/editTeacher', methods = ["GET", "POST"])
def editTeacher():
    user = session.get('user')
    if user is None:
        return redirect(url_for('index'))
    
    teacher_ref = ref.child('teachers')
    t_data = teacher_ref.get()
    teach_data = []

    for i in t_data:
        d = {}
        d["username"] = i
        d["name"] = t_data[i]["name"]
        d["class"] = t_data[i]["class"]
        teach_data.append(d)


    if request.method == "POST":
        username = request.form.get('username')
        name = request.form.get('name')
        password = request.form.get('password')
        clas = request.form.get("class")


        if username in t_data: 
            d = {}
            rec = {}

            d['name'] = name
            d['password'] = password
            d['class'] = int(clas)
            rec[username] = d
            teacher_ref.update(rec)
        else:
            return render_template("editTeacher.html", error = "Teacher not found!", l = len(teach_data), teach_data = teach_data)

        return render_template("editTeacher.html", l = len(teach_data), teach_data = teach_data)

    return render_template("editTeacher.html", l = len(teach_data), teach_data = teach_data)



if __name__ == "__main__":
    app.run(debug=True)
