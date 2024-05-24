import cv2
import face_recognition as fr
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
appSettings = {'databaseURL': 'https://biometric-attendance-54301-default-rtdb.asia-southeast1.firebasedatabase.app/'}
my_app3 = firebase_admin.initialize_app(cred, appSettings, name="my_app3")

ref = db.reference('/', app=my_app3)
facedata_ref = ref.child('facedata')
attendance_ref = ref.child('attendance')


# Path1 = 'Resc/Images'

def Encodings(Path1):
    Path2 = os.listdir(Path1)
    imgList = []
    classes = []
    Ids = []
    names = []

    for i in Path2:
        imgList.append(cv2.imread(os.path.join(Path1, i)))
        
        txt = os.path.splitext(i)[0]
        l = txt.split('_')
        classes.append(l[0])
        Ids.append(l[1])
        names.append(l[2])

    encDict = {}
    namesDict = {}
    i = 0
    for img in imgList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        try:
            enc = fr.face_encodings(img)[0]
        except:
            return 1, 2
        enc = list(enc)
        encDict[Ids[i]] = enc
        namesDict[Ids[i]] = {"name": names[i], "class": int(classes[i])}
        i += 1
    return encDict, namesDict

def uploadMultiFaces(path):
    encDict, nameDict = Encodings(path)
    if encDict == 1 and nameDict == 2:
        return 0
    facedata_ref.set(encDict)
    attendance_ref.update(nameDict)
    return 1
