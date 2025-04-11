import datetime
from bson import ObjectId
from flask import request, Flask, render_template, redirect, session
import os
import hashlib

import pymongo
from mail import send_email
my_client = pymongo.MongoClient("mongodb://localhost:27017")
my_database = my_client["TOURISM"]
Tourist_collection = my_database["tourist"]
Admin_collection = my_database["admin"]
Tourism_agency_collection = my_database["tourism_agency"]
Tourism_package_collection = my_database["tourism_package"]
Location_collection = my_database["location"]
Tours_program_collection = my_database["tours_program"]
Booking_collection = my_database['booking']
Payment_collection = my_database['payment']
Complaint_collection = my_database['complaint']
app = Flask(__name__)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
PROFILES_PATH = APP_ROOT + "/static/profiles"
app.secret_key = "Tour"
admin_name = "admin"
admin_password = "admin"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin")
def admin():
    return render_template("admin_login.html")


query = {}
count = Admin_collection.count_documents(query)
if count == 0:
    query = {"username": "admin", "password": "admin"}
    Admin_collection.insert_one(query)


@app.route("/admin_home")
def admin_home():
    return render_template("admin_home.html")


@app.route("/tourism_agency")
def tourism_agency():
    return render_template("tourism_agency_login.html")


@app.route("/tourism_agency_home")
def tourism_agency_home():
    return render_template("tourism_agency_home.html")


@app.route("/tourism_agency_registration")
def tourism_agency_registration():
    return render_template("tourism_agency_registration.html")


@app.route("/location")
def location():
    message = request.args.get("message")
    if message == None:
        message = ""
    query = {}
    locations = Location_collection.find(query)
    locations = list(locations)
    return render_template("location.html", locations=locations,message=message)


@app.route("/location_action", methods=['post'])
def location_action():
        location = request.form.get("location")
        query = {"location": location}
        count = Location_collection.count_documents(query)
        if count > 0:
            return redirect("/location?message= Location Already Exists")
        picture = request.files.get("picture")
        path = PROFILES_PATH + "/" + picture.filename
        picture.save(path)
        query = {"location": location,"picture": picture.filename}
        Location_collection.insert_one(query)
        return redirect("/location?message= Location Added Successfully")


@app.route("/update_location")
def update_location():
    location_id = request.args.get("location_id")
    query = {"_id": ObjectId(location_id)}
    location = Location_collection.find_one(query)
    return render_template("update_location.html", location_id=location_id, location=location)


@app.route("/update_location_action",methods=['post'])
def update_location_action():
    location_id = request.form.get("location_id")
    location = request.form.get("location")
    picture = request.files.get("picture")
    if picture.filename=="":
        query = {"_id": ObjectId(location_id)}
        query2 = {"$set": {"location": location}}
        Location_collection.update_one(query, query2)
        return redirect("/location")
    else:
        picture = request.files.get("picture")
        path = PROFILES_PATH + "/" + picture.filename
        picture.save(path)
        query = {"_id": ObjectId(location_id)}
        query2 = {"$set": {"location": location,"picture":picture.filename}}
        Location_collection.update_one(query, query2)
        return redirect("/location")


@app.route("/tourism_agency_registration_action", methods=['post'])
def tourism_agency_registration_action():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    company_name = request.form.get("company_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    gender = request.form.get("gender")
    address = request.form.get("address")
    city = request.form.get("city")
    zip_code = request.form.get("zip_code")
    password2 = hashlib.sha256(password.encode("utf-8")).hexdigest()
    query = {"email": email}
    count = Tourism_agency_collection.count_documents(query)
    if count > 0:
        return render_template("main_message.html", message="Email Already Exists")
    query = {"phone": phone}
    count = Tourism_agency_collection.count_documents(query)
    if count > 0:
        return render_template("main_message.html", message="Phone Number Already Exists")
    query = {"first_name": first_name,"last_name":last_name,"company_name":company_name, "email": email, "phone": phone, "password": password, "confirm_password":confirm_password,"gender": gender, "address": address,"status":'Not Verified',"city":city,"zip_code":zip_code}
    Tourism_agency_collection.insert_one(query)
    return render_template("main_message.html", message=" Agency Registered successfully")


@app.route("/tourist")
def tourist():
    return render_template("tourist_login.html")


@app.route("/tourist_home")
def tourist_home():
    return render_template("tourist_home.html")


@app.route("/tourist_registration")
def tourist_registration():
    message = request.args.get("message")
    if message is None:
        message = ""
    return render_template("tourist_registration.html", message=message)


@app.route("/tourist_registration_action", methods=['post'])
def tourist_registration_action():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    gender = request.form.get("gender")
    address = request.form.get("address")
    password2 = hashlib.sha256(password.encode("utf-8")).hexdigest()
    query = {"email": email}
    count = Tourist_collection.count_documents(query)
    if count > 0:
        return redirect("/tourist_registration?message=Email Already Exist")
    query = {"phone": phone}
    count = Tourist_collection.count_documents(query)
    if count > 0:
        return render_template("main_message.html", message="Phone Number Already Exists")
    query = {"name": name, "email": email, "phone": phone, "password": password,"confirm_password":confirm_password, "gender": gender, "address": address}
    Tourist_collection.insert_one(query)
    return render_template("main_message.html", message=" Tourist Registered successfully")


@app.route("/admin_login_action", methods=['post'])
def admin_login_action():
    name = request.form.get("name")
    password = request.form.get("password")
    if name == admin_name and password == admin_password:
        session['role'] = 'admin'
        return redirect("/admin_home")
    else:
        return render_template("main_message.html", message="Invalid Admin Details")


@app.route("/tourist_login_action",methods=['post'])
def tourist_login_action():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email": email, "password": password}
    count = Tourist_collection.count_documents(query)
    if count > 0:
        tourist = Tourist_collection.find_one(query)
        session['tourist_id'] = str(tourist['_id'])
        session['role'] = 'tourist'
        return redirect("/tourist_home")
    else:
        return render_template("main_message.html",message="Invalid  Tourist Details")


@app.route("/tourism_agency_login_action",methods=['post'])
def tourism_agency_login_action():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email": email, "password": password}
    count = Tourism_agency_collection.count_documents(query)
    if count > 0:
        tourism_agency = Tourism_agency_collection.find_one(query)
        if tourism_agency['status'] == 'Verified':
          session ['tourism_agency_id'] = str(tourism_agency['_id'])
          session ['role'] = 'tourism_agency'
          return redirect("/tourism_agency_home")
        elif tourism_agency['status'] == 'Block':
         session ['tourism_agency_id'] = str(tourism_agency['_id'])
         session ['role'] = 'tourism_agency'
         return render_template("main_message.html", message="Your Account  Is Blocked")
        elif tourism_agency['status'] == 'UnBlock':
            session['tourism_agency_id'] = str(tourism_agency['_id'])
            session['role'] = 'tourism_agency'
            return render_template("main_message.html", message="Your Account  Is Un Blocked")
        elif tourism_agency['status'] == 'Not Verified':
            session['tourism_agency_id'] = str(tourism_agency['_id'])
            session['role'] = 'tourism_agency'
            return render_template("main_message.html", message="Your Account  Is Not Verified")
    else:
        return render_template("main_message.html", message="Invalid Email and Password")


@app.route("/view_tourism_agency")
def view_tourism_agency():
    query = {}
    tourism_agencies = Tourism_agency_collection.find(query)
    tourism_agencies = list(tourism_agencies)
    return render_template("view_tourism_agency.html",tourism_agencies=tourism_agencies)


@app.route("/tourism_package")
def tourism_package():
    query={}
    locations=Location_collection.find(query)
    locations=list(locations)
    return render_template("tourism_package.html",locations=locations)


@app.route("/tourism_package_action",methods=['post'])
def tourism_package_action():
    tourism_agency_id = session['tourism_agency_id']

    package_name = request.form.get("package_name")
    no_of_persons_allowed = request.form.get("no_of_persons_allowed")
    price = request.form.get("price")
    description = request.form.get("description")
    list_of_locations=request.form.getlist("list_of_locations")
    list_of_locations2 = []
    for location in list_of_locations:
        list_of_locations2.append({"location_id":ObjectId(location)})
    travel_by=request.form.get("travel_by")
    accommodation=request.form.get("accommodation")
    query = {"tourism_agency_id": ObjectId(session['tourism_agency_id']),"package_name": package_name, "no_of_persons_allowed": no_of_persons_allowed, "price": price, "description": description,"accommodation":accommodation,"list_of_locations":list_of_locations2,"travel_by":travel_by,"status":"Not Published"}
    Tourism_package_collection.insert_one(query)
    print(query)
    return render_template("tourism_agency_message.html", message=" Package Added successfully")


@app.route("/booking_tours_program")
def booking_tours_program():
    tours_program_id=request.args.get("tours_program_id")
    print(tours_program_id)
    tourism_agency_id=request.args.get("tourism_agency_id")
    t_package = Tours_program_collection.find_one({"_id": ObjectId(tours_program_id)})
    return render_template("booking_tours_program.html",tours_program_id=tours_program_id,tourism_agency_id=tourism_agency_id)


@app.route("/booking_tours_program_action",methods=['post'])
def booking_tours_program_action():
    tourism_agency_id=request.form.get("tourism_agency_id")
    tours_program_id=request.form.get("tours_program_id")
    date=datetime.datetime.now()
    no_of_passengers=request.form.get("no_of_passengers")
    dob=request.form.get("date")
    query1={"_id":ObjectId(tours_program_id)}
    tours_program=Tours_program_collection.find_one(query1)
    price=tours_program['price']
    total_amount= float(no_of_passengers) * float(price)
    admin_commission=float(total_amount)-float(total_amount * 0.95) # for admin commission 5%(100-5)=95
    passengers = []
    for i in range(0, int(no_of_passengers) + 0):
        name = request.form.get("name" + str(i))
        gender = request.form.get("gender" + str(i))
        email = request.form.get("email" + str(i))
        phone = request.form.get("phone" + str(i))
        dob = request.form.get("date" + str(i))
        passengers.append({"name": name, "gender": gender, "email": email, "phone": phone, "dob": dob})
    query={"tourist_id": ObjectId(session['tourist_id']),"tourism_agency_id":ObjectId(tourism_agency_id),"tours_program_id":ObjectId(tours_program_id),"passengers":passengers,"no_of_passengers":no_of_passengers,"date":date,"status":"Tour is Planned","total_amount":total_amount}
    booking = Booking_collection.insert_one(query)
    booking_id = booking.inserted_id
    query = {'_id': ObjectId(booking_id)}
    bookings = Booking_collection.find_one(query)
    return render_template("payment.html",bookings=bookings,booking_id=booking_id,total_amount=total_amount,admin_commission=admin_commission)


@app.route("/payment_action",methods=['post'])
def payment_action():
    booking_id = request.form.get("booking_id")
    admin_commission=request.form.get("admin_commission")
    amount = request.form.get("amount")
    payment_date=datetime.datetime.now()
    card_type = request.form.get("card_type")
    card_number = request.form.get("card_number")
    card_holder_name = request.form.get("card_holder_name")
    cvv = request.form.get("cvv")
    expiry_date = request.form.get("expiry_date")
    query = {"tourist_id": ObjectId(session['tourist_id']),"booking_id":ObjectId(booking_id),"amount": amount, "card_type": card_type, "card_number": card_number,  "card_holder_name": card_holder_name,"cvv": cvv, "expiry_date": expiry_date,"status":"Amount Paid","admin_commission":admin_commission,"payment_date":payment_date}
    Payment_collection.insert_one(query)
    query1 = {"_id": ObjectId(booking_id)}
    query2 = {"$set": {"status": "Booked"}}
    Booking_collection.update_one(query1, query2)
    tourist_id=session['tourist_id']
    query = {"_id": ObjectId(tourist_id)}
    tourist= Tourist_collection.find_one(query)
    email = (tourist['email'])
    send_email("Payment Successfully" ,"Tour package Booked Successfully:\n $"+str(amount)+"",email)
    return render_template("tourist_message.html",message="Payment successfully Done")


@app.route("/tours_program")
def tours_program():
    tourism_agency_id=request.args.get("tourism_agency_id")
    tourism_package_id=request.args.get("tourism_package_id")
    query={"_id":ObjectId(tourism_package_id)}
    tourism_packages=Tourism_package_collection.find_one(query)
    return render_template("tours_program.html",tourism_package_id=tourism_package_id,tourism_packages=tourism_packages,tourism_agency_id=tourism_agency_id)


@app.route("/tours_program_action",methods=['post'])
def tours_program_action():
    tourism_agency_id=request.form.get("tourism_agency_id")
    tourism_package_id=request.form.get("tourism_package_id")
    start_date=request.form.get("start_date")
    start_date = datetime.datetime.strptime(start_date,"%Y-%m-%d")
    end_date=request.form.get("end_date")
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    duration=request.form.get("duration")
    total_capacity=request.form.get("total_capacity")
    price=request.form.get("price")
    query = {"tourism_agency_id":ObjectId(tourism_agency_id),"tourism_package_id":ObjectId(tourism_package_id),"start_date": start_date, "end_date": end_date, "duration": duration, "total_capacity": total_capacity, "price": price}
    Tours_program_collection.insert_one(query)
    return render_template("tourism_agency_message.html",message="Tour Program Added Successfully")


@app.route("/raise_complaint")
def raise_complaint():
    booking_id=request.args.get("booking_id")
    return render_template("raise_complaint.html",booking_id=booking_id)


@app.route("/raise_complaint_action",methods=['post'])
def raise_complaint_action():
    booking_id=request.form.get("booking_id")
    complaint=request.form.get("complaint")
    query={"booking_id":ObjectId(booking_id),"complaint":complaint,"status":"Complaint Raised","tourist_id": ObjectId(session['tourist_id'])}
    Complaint_collection.insert_one(query)
    tourist_id = session['tourist_id']
    query = {"_id": ObjectId(tourist_id)}
    tourist = Tourist_collection.find_one(query)
    email = (tourist['email'])
    send_email("complaint", "Complaint Raised:\n " + str(complaint) + "", email)
    return render_template("tourist_message.html",message="Complaint Raised Successfully ")


@app.route("/view_tours_program")
def view_tours_program():
    tourism_package_id = request.args.get("tourism_package_id")
    query = {"tourism_package_id": ObjectId(tourism_package_id)}
    tourism_agency_id = request.args.get("tourism_agency_id")
    tours_programs=Tours_program_collection.find(query)
    tours_programs=list(tours_programs)
    return render_template("view_tour_program.html",tourism_agency_id=tourism_agency_id,get_is_available=get_is_available,tours_programs=tours_programs)


@app.route("/view_tourism_package")
def view_tourism_package():
    if session['role']=="tourist":
        query={"status":"Published"}
    elif session['role']=="admin":
        query={}
    elif session['role']=="tourism_agency":
        query = {"tourism_agency_id": ObjectId(session['tourism_agency_id'])}
    tourism_packages=Tourism_package_collection.find(query)
    tourism_packages=list(tourism_packages)
    return render_template("view_tourism_package.html",tourism_packages=tourism_packages,get_location_by_tourism_package=get_location_by_tourism_package)


@app.route("/view_booking")
def view_booking():
    query = {}
    if session['role'] == "tourist":
        query = {"tourist_id": ObjectId(session['tourist_id'])}
    elif session['role'] == "admin":
        query = {}
    elif session['role'] == "tourism_agency":
        query = {"tourism_agency_id": ObjectId(session['tourism_agency_id'])}
    bookings=Booking_collection.find(query)
    bookings=list(bookings)
    return render_template("view_booking.html",bookings=bookings,get_tours_program_by_tours_program_id=get_tours_program_by_tours_program_id,get_tourist_by_tourist_id=get_tourist_by_tourist_id,get_tourism_package_by_tours_program_id=get_tourism_package_by_tours_program_id,get_location_by_tourism_package=get_location_by_tourism_package)


@app.route("/verify")
def verify():
    tourism_agency_id=request.args.get("tourism_agency_id")
    query={"$set":{"status":"Verified"}}
    Tourism_agency_collection.update_one({"_id": ObjectId(tourism_agency_id)},query)
    session['role'] = 'tourism_agency'
    return redirect("/view_tourism_agency")

@app.route("/de_verify")
def de_verify():
    tourism_agency_id = request.args.get("tourism_agency_id")
    query = {"$set": {"status": "Not Verified"}}
    Tourism_agency_collection.update_one({"_id": ObjectId(tourism_agency_id)}, query)
    return redirect("/view_tourism_agency")


@app.route("/block")
def block():
    tourism_agency_id = request.args.get("tourism_agency_id")
    query={"$set":{"status":"Block"}}
    Tourism_agency_collection.update_one({"_id": ObjectId(tourism_agency_id)},query)
    session['role'] = 'tourism_agency'
    return redirect("/view_tourism_agency")


@app.route("/unblock")
def unblock():
    tourism_agency_id = request.args.get("tourism_agency_id")
    query={"$set":{"status":"UnBlock"}}
    Tourism_agency_collection.update_one({"_id": ObjectId(tourism_agency_id)},query)
    session['role'] = 'tourism_agency'
    return redirect("/view_tourism_agency")



@app.route("/publish")
def publish():
    tourism_package_id=request.args.get("tourism_package_id")
    query={"$set":{"status":"Published"}}
    Tourism_package_collection.update_one({"_id": ObjectId(tourism_package_id)},query)
    return redirect("/view_tourism_package")


@app.route("/view_payment")
def view_payment():
    booking_id = request.args.get("booking_id")
    query = {"booking_id": ObjectId(booking_id)}
    payments=Payment_collection.find(query)
    payments=list(payments)
    return render_template("view_payment.html",payments=payments)


@app.route("/view_complaint")
def view_complaint():
    query={}
    complaints=Complaint_collection.find(query)
    complaints=list(complaints)
    return render_template("view_complaint.html",complaints=complaints)


@app.route("/solve_complaint")
def solve_complaint():
    complaint_id=request.args.get("complaint_id")
    query={"$set":{"status":"Complaint Solved"}}
    Complaint_collection.update_one({"_id": ObjectId(complaint_id)},query)
    tourist_id = session['tourist_id']
    query = {"_id": ObjectId(tourist_id)}
    tourist = Tourist_collection.find_one(query)
    email = (tourist['email'])
    send_email("complaint", "Complaint Resolved by Admin:\n ", email)
    return redirect("/view_complaint")


@app.route("/cancel_program")
def cancel_program():
    booking_id=request.args.get("booking_id")
    query={"$set":{"status":"Cancelled"}}
    Booking_collection.update_one({"_id": ObjectId(booking_id)},query)
    payment=Payment_collection.find_one({"booking_id":ObjectId(booking_id)})
    query2={"$set":{"status":"Amount Refunded","refunded_amount":payment['amount']}}
    Payment_collection.update_one({"booking_id":ObjectId(booking_id)},query2)
    return redirect("/view_booking")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


def get_tours_program_by_tours_program_id(tours_program_id):
    query = {"_id": ObjectId(tours_program_id)}
    tours_program  = Tours_program_collection.find_one(query)
    return tours_program


def get_tourist_by_tourist_id(tourist_id):
    query = {"_id": ObjectId(tourist_id)}
    tourist  = Tourist_collection.find_one(query)
    return tourist


def get_tourism_package_by_tours_program_id(tours_program_id):
    query={"_id":ObjectId(tours_program_id)}
    tourism_package = Tourism_package_collection.find_one(query)
    return tourism_package


def get_location_by_tourism_package(location_id):
    query={"_id":ObjectId(location_id)}
    location=Location_collection.find_one(query)
    return location


def get_is_available(tours_program_id):
    tours_program = Tours_program_collection.find_one({"_id":ObjectId(tours_program_id)})
    total_capacity = int(tours_program['total_capacity'])
    bookings = Booking_collection.find({"tours_program_id":ObjectId(tours_program_id),"status":'Booked'})
    for booking in bookings:
        total_capacity2 = len(booking['passengers'])
        total_capacity = int(total_capacity)-int(total_capacity2)
    return total_capacity


# @app.route("/resolve_complaint_action")
# def resolve_complaint_action():
#     booking_id=request.args.get("booking_id")
#     description=request.args.get("description")
#     query={"booking_id":ObjectId(booking_id),"description":description,"tourist_id": ObjectId(session['tourist_id'])}
#     Complaint_collection.insert_one(query)
#     return render_template("/view_complaint.html")

app.run(debug=True)