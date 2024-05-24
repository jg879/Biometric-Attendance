import cv2
import face_recognition as fr
import numpy as np
import cvzone
import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db


cred = credentials.Certificate("serviceAccountKey.json")
appSettings = {'databaseURL': 'https://biometric-attendance-54301-default-rtdb.asia-southeast1.firebasedatabase.app/'}
my_app = firebase_admin.initialize_app(cred, appSettings, name='my_app')

ref = db.reference('/', app=my_app)
attendance_ref = ref.child('attendance')

tdate = datetime.date.today()
tdate = str(tdate)

dat = attendance_ref.get()
enrolls = list(dat.keys())
lst = list(dat[enrolls[0]])
if tdate not in lst:
    for i in enrolls:
        attendance_ref.child(i).update({tdate: 0})


def mark_present(id):
    status = 1
    id_ref = attendance_ref.child(id)
    data = {tdate: status}
    id_ref.update(data)
    return True


def gen(clas):
    student_ref = ref.child('attendance')
    data = student_ref.get()
    user_name = {}
    user_lst = []
    for i in data:
        if(data[i]['class'] == clas):
            user_name[i] = data[i]['name']
            user_lst.append(i)


    facedata_ref = ref.child('facedata')
    facedata = facedata_ref.get()
    Ids = []
    encList = []
    for i in user_lst:
        Ids.append(i)
        encList.append(facedata[i])
    # Ids = list(facedata.keys())
    # encList = list(facedata.values())

    flag = 0
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)
    while True:
        success, img = cap.read()
        img2 = img
        img = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        faceFrame = fr.face_locations(img)
        enc = fr.face_encodings(img, faceFrame)
        for encFace, face in zip(enc, faceFrame):
            matches = fr.compare_faces(encList, encFace)
            dist = fr.face_distance(encList, encFace)
            ind = np.argmin(dist)
            if matches[ind] and dist[ind] < 0.5:
                y1, x2, y2, x1 = face
                y1, x2, y2, x1 = y1*4, x2*4, y2*4, x1*4
                bbox = x1, y1, x2 - x1, y2 - y1
                img2 = cvzone.cornerRect(img2, bbox, rt = 0)
                font = cv2.FONT_HERSHEY_SIMPLEX
                stu = int(Ids[ind].split('_')[0])
                on_vid_text = str(user_name[str(stu)]) + ": Present"
                if stu is not None:
                    cv2.putText(img2, on_vid_text, (50, 50), font, 1, (0, 255, 255), 2, cv2.LINE_4)
                st = mark_present(str(stu))

            else:
                y1, x2, y2, x1 = face
                y1, x2, y2, x1 = y1*4, x2*4, y2*4, x1*4
                bbox = x1, y1, x2 - x1, y2 - y1
                img2 = cvzone.cornerRect(img2, bbox, rt = 0, colorR=(0, 0, 255), colorC=(0, 0, 255))
        ret, buffer = cv2.imencode('.jpg', img2)
        frame = buffer.tobytes()
        yield(b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    

