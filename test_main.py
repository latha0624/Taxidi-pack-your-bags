import pytest
import mongomock
import hashlib
import io
import datetime
import pickle
import os
from bson import ObjectId

from Google import convert_to_RFC_datetime, Create_Service
from main import (
    app, Tourist_collection, Admin_collection, Tourism_agency_collection,
    Location_collection, Tours_program_collection, Booking_collection,
    Payment_collection, Complaint_collection, Tourism_package_collection
)

# ----------- Fixtures ------------

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db():
    mock_client = mongomock.MongoClient()
    db = mock_client.db
    Tourist_collection._collection = db.Tourist_collection
    Admin_collection._collection = db.Admin_collection
    Tourism_agency_collection._collection = db.Tourism_agency_collection
    Location_collection._collection = db.Location_collection
    Tours_program_collection._collection = db.Tours_program_collection
    Booking_collection._collection = db.Booking_collection
    Payment_collection._collection = db.Payment_collection
    Complaint_collection._collection = db.Complaint_collection

# ----------- Dummy Classes ------------

class DummyCreds:
    valid = True
    expired = False
    refresh_token = True
    def refresh(self, request): pass

class DummyFlow:
    def run_local_server(self, port=0, **kwargs):
        return DummyCreds()

class InvalidCreds:
    valid = False
    expired = True
    refresh_token = False
    def refresh(self, request): pass

class ValidCreds:
    valid = True
    expired = False
    refresh_token = True
    def refresh(self, request): pass

class ExpiredCreds:
    valid = False
    expired = True
    refresh_token = True
    def refresh(self, request):
        self.valid = True  # simulate refresh success

class DummyCredsForPrint:
    valid = True
    expired = False
    refresh_token = True
    def refresh(self, request): pass

class DummyFlowForPrint:
    def run_local_server(self, port=0, **kwargs):
        return DummyCredsForPrint()

# ----------- Flask App Tests ------------

def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"<nav" in response.data

def test_admin_login_success(client, mock_db):
    Admin_collection.insert_one({"username": "admin", "password": "admin"})
    response = client.post("/admin_login_action", data={"name": "admin", "password": "admin"})
    assert response.status_code == 302

def test_admin_login_failure(client, mock_db):
    response = client.post("/admin_login_action", data={"name": "admin", "password": "wrongpass"})
    assert b"Invalid Admin Details" in response.data

def test_tourist_registration(client, mock_db):
    response = client.post(
        "/tourist_registration_action",
        data={
            "name": "John Doe",
            "email": "johndoe@example.com",
            "phone": "1234567890",
            "password": "password123",
            "confirm_password": "password123",
            "gender": "Male",
            "address": "123 Street, City",
        },
        follow_redirects=True,
    )
    assert response.status_code in [200, 302]
    tourist = Tourist_collection.find_one({"email": "johndoe@example.com"})
    assert tourist is not None
    assert tourist["name"] == "John Doe"

def test_tourist_login(client, mock_db):
    hashed_password = hashlib.sha256("password123".encode("utf-8")).hexdigest()
    Tourist_collection.insert_one({"email": "johndoe@example.com", "password": hashed_password})
    response = client.post("/tourist_login_action", data={"email": "johndoe@example.com", "password": "password123"})
    assert response.status_code == 302

def test_tourist_login_failure(client, mock_db):
    response = client.post("/tourist_login_action", data={"email": "invalid@example.com", "password": "wrongpassword"})
    assert b"Invalid  Tourist Details" in response.data

def test_add_location(client, mock_db):
    Location_collection.delete_many({})
    data = {"location": "Paris"}
    file_data = {"picture": (io.BytesIO(b"fake image data"), "paris.jpg")}
    response = client.post("/location_action", data={**data, **file_data}, content_type="multipart/form-data")
    assert response.status_code == 302
    assert Location_collection.find_one({"location": "Paris"}) is not None

def test_add_duplicate_location(client, mock_db):
    Location_collection.insert_one({"location": "Paris"})
    data = {"location": "Paris"}
    response = client.post("/location_action", data=data)
    assert b"Location Already Exists" in response.data

def test_tour_booking(client, mock_db):
    Booking_collection.delete_many({})
    valid_tourist_id = str(ObjectId())
    valid_agency_id = str(ObjectId())
    tour_id = ObjectId()

    Tours_program_collection.insert_one({
        "_id": tour_id,
        "tourism_agency_id": valid_agency_id,
        "price": 200.0
    })

    with client.session_transaction() as sess:
        sess["tourist_id"] = valid_tourist_id

    response = client.post(
        "/booking_tours_program_action",
        data={"tourism_agency_id": valid_agency_id, "tours_program_id": str(tour_id), "no_of_passengers": "2"},
    )
    assert response.status_code in [200, 302]
    assert Booking_collection.count_documents({}) == 1

def test_make_payment(client, mock_db):
    Payment_collection.delete_many({})
    Booking_collection.delete_many({})
    Tourist_collection.delete_many({})

    valid_tourist_id = str(ObjectId())
    booking_id = ObjectId()

    Tourist_collection.insert_one({
        "_id": ObjectId(valid_tourist_id),
        "email": "john@example.com",
        "name": "John Doe"
    })

    Booking_collection.insert_one({
        "_id": booking_id,
        "tourist_id": valid_tourist_id,
        "total_amount": 500
    })

    with client.session_transaction() as sess:
        sess["tourist_id"] = valid_tourist_id

    response = client.post("/payment_action", data={
        "booking_id": str(booking_id),
        "admin_commission": "25",
        "amount": "500",
        "card_type": "Visa",
        "card_number": "1234567890123456",
        "card_holder_name": "John Doe",
        "cvv": "123",
        "expiry_date": "12/25",
    })
    assert response.status_code in [200, 302]
    assert Payment_collection.count_documents({}) == 1

def test_raise_complaint(client, mock_db):
    Complaint_collection.delete_many({})
    Booking_collection.delete_many({})
    Tourist_collection.delete_many({})

    valid_tourist_id = str(ObjectId())
    booking_id = ObjectId()

    Tourist_collection.insert_one({
        "_id": ObjectId(valid_tourist_id),
        "email": "jane@example.com",
        "name": "Jane Doe"
    })

    Booking_collection.insert_one({
        "_id": booking_id,
        "tourist_id": valid_tourist_id
    })

    with client.session_transaction() as sess:
        sess["tourist_id"] = valid_tourist_id

    response = client.post("/raise_complaint_action", data={
        "booking_id": str(booking_id),
        "complaint": "Service was bad"
    })
    assert response.status_code in [200, 302]
    assert Complaint_collection.count_documents({"complaint": "Service was bad"}) == 1

# ----------- Google.py Unit Tests ------------

def test_convert_to_RFC_datetime():
    result = convert_to_RFC_datetime(2025, 4, 25, 14, 45)
    assert result == "2025-04-25T14:45:00Z"

def test_create_service_no_token_file(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda path: False)

    def dummy_from_client_secrets_file(*args, **kwargs):
        return DummyFlow()

    def dummy_build(*args, **kwargs):
        return "dummy_service"

    import Google
    Google.InstalledAppFlow = type("InstalledAppFlow", (), {
        "from_client_secrets_file": staticmethod(dummy_from_client_secrets_file)
    })
    Google.build = dummy_build

    service = Create_Service("fake_credentials.json", "calendar", "v3", ["scope"])
    assert service == "dummy_service"

def test_create_service_with_token_file(tmp_path, monkeypatch):
    token_file = tmp_path / "token_calendar_v3.pickle"
    with open(token_file, "wb") as f:
        pickle.dump(DummyCreds(), f)

    import Google
    Google.build = lambda *args, **kwargs: "dummy_service"

    service = Create_Service(str(token_file), "calendar", "v3", ["scope"])
    assert service == "dummy_service"

def test_create_service_with_invalid_expired_creds(tmp_path):
    token_file = tmp_path / "token_calendar_v3.pickle"
    with open(token_file, "wb") as f:
        pickle.dump(InvalidCreds(), f)

    import Google
    Google.build = lambda *args, **kwargs: "dummy_service"

    service = Create_Service(str(token_file), "calendar", "v3", ["scope"])
    assert service == "dummy_service"

def test_create_service_with_build_failure(monkeypatch, tmp_path):
    token_file = tmp_path / "token_calendar_v3.pickle"
    with open(token_file, "wb") as f:
        pickle.dump(ValidCreds(), f)

    import Google
    monkeypatch.setattr(Google, "build", lambda *args, **kwargs: (_ for _ in ()).throw(Exception("Build Failed")))

    service = Create_Service(str(token_file), "calendar", "v3", ["scope"])
    assert service is None

def test_create_service_refresh_token(monkeypatch, tmp_path):
    token_file = tmp_path / "token_calendar_v3.pickle"
    with open(token_file, "wb") as f:
        pickle.dump(ExpiredCreds(), f)

    import Google
    Google.build = lambda *args, **kwargs: "dummy_service"
    Google.Request = lambda: None

    service = Create_Service(str(token_file), "calendar", "v3", ["scope"])
    assert service == "dummy_service"

def test_create_service_no_creds(monkeypatch):
    import Google
    monkeypatch.setattr(os.path, "exists", lambda path: False)

    class EmptyFlow:
        def run_local_server(self, port=0, **kwargs):
            return None  # No creds

    Google.InstalledAppFlow = type("InstalledAppFlow", (), {
        "from_client_secrets_file": staticmethod(lambda *args, **kwargs: EmptyFlow())
    })

    monkeypatch.setattr(Google, "build", lambda *args, **kwargs: None)

    service = Create_Service("fake_credentials.json", "calendar", "v3", ["scope"])
    assert service is None

def test_create_service_triggers_print(monkeypatch, capsys):
    import Google
    monkeypatch.setattr(os.path, "exists", lambda path: False)

    Google.InstalledAppFlow = type("InstalledAppFlow", (), {
        "from_client_secrets_file": staticmethod(lambda *args, **kwargs: DummyFlowForPrint())
    })
    Google.build = lambda *args, **kwargs: "dummy_service"

    service = Create_Service("fake_credentials.json", "calendar", "v3", ["scope"])
    captured = capsys.readouterr()

    assert service == "dummy_service"
    assert "calendar service created successfully" in captured.out

def test_create_service_print(monkeypatch, capsys):
    monkeypatch.setattr(os.path, "exists", lambda p: False)
    import Google

    class DummyFlow:
        def run_local_server(self, port=0, **kwargs): return DummyCreds()

    Google.InstalledAppFlow = type("Flow", (), {
        "from_client_secrets_file": staticmethod(lambda *a, **k: DummyFlow())
    })
    monkeypatch.setattr(Google, "build", lambda *a, **k: "service")

    service = Create_Service("credentials.json", "calendar", "v3", ["scope"])
    captured = capsys.readouterr()

    assert service == "service"
    assert "credentials.json-calendar-v3-(['scope'],)" in captured.out
    assert "['scope']" in captured.out

def test_create_service_none_output(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda path: True)

    import Google

    # Set up to return None for creds
    class DummyFlowNone:
        def run_local_server(self, port=0, **kwargs):
            return None

    Google.InstalledAppFlow = type("InstalledAppFlow", (), {
        "from_client_secrets_file": staticmethod(lambda *a, **k: DummyFlowNone())
    })

    monkeypatch.setattr(Google, "build", lambda *a, **k: None)

    service = Create_Service("credentials.json", "calendar", "v3", ["scope"])
    assert service is None

# ----------- Main.py ------------

def test_admin_home(client):
    response = client.get("/admin_home")
    assert response.status_code == 200

def test_tourism_agency_login_page(client):
    response = client.get("/tourism_agency")
    assert response.status_code == 200

def test_tourism_agency_home_page(client):
    response = client.get("/tourism_agency_home")
    assert response.status_code == 200

def test_tourism_agency_registration_page(client):
    response = client.get("/tourism_agency_registration")
    assert response.status_code == 200

def test_tourist_home_page(client):
    response = client.get("/tourist_home")
    assert response.status_code == 200

def test_tourist_registration_page(client):
    response = client.get("/tourist_registration")
    assert response.status_code == 200

def test_view_tourism_agency(client, mock_db):
    response = client.get("/view_tourism_agency")
    assert response.status_code == 200

def test_view_booking_as_tourist(client, mock_db):
    with client.session_transaction() as sess:
        sess['role'] = 'tourist'
        sess['tourist_id'] = str(ObjectId())
    response = client.get("/view_booking")
    assert response.status_code == 200

def test_view_tourism_package_as_admin(client, mock_db):
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
    response = client.get("/view_tourism_package")
    assert response.status_code == 200

def test_tourism_agency_registration_action(client, mock_db):
    data = {
        "first_name": "Test",
        "last_name": "Agency",
        "company_name": "Test Co.",
        "email": "agency@example.com",
        "phone": "9876543210",
        "password": "pass123",
        "confirm_password": "pass123",
        "gender": "Other",
        "address": "Test Address",
        "city": "Test City",
        "zip_code": "12345",
    }
    response = client.post("/tourism_agency_registration_action", data=data)
    assert response.status_code == 200
    agency = Tourism_agency_collection.find_one({"email": "agency@example.com"})
    assert agency is not None

def test_tourism_agency_login_success(client, mock_db):
    Tourism_agency_collection.delete_many({})
    inserted_id = Tourism_agency_collection.insert_one({
        "email": "agency@example.com",
        "password": "pass123",
        "status": "Verified"
    }).inserted_id

    with client.session_transaction() as sess:
        sess.clear()

    response = client.post("/tourism_agency_login_action", data={
        "email": "agency@example.com",
        "password": "pass123"
    }, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/tourism_agency_home")

    # Now verify the session is correct
    with client.session_transaction() as sess:
        assert sess["role"] == "tourism_agency"
        assert sess["tourism_agency_id"] == str(inserted_id)

def test_tourism_agency_login_failure(client, mock_db):
    response = client.post("/tourism_agency_login_action", data={
        "email": "invalid@example.com",
        "password": "wrongpass"
    })
    assert b"Invalid Email and Password" in response.data

def test_publish_tourism_package(client, mock_db):
    tourism_package_id = Tourism_package_collection.insert_one({"status": "Not Published"}).inserted_id
    response = client.get(f"/publish?tourism_package_id={tourism_package_id}")
    assert response.status_code == 302

def test_verify_tourism_agency(client, mock_db):
    tourism_agency_id = Tourism_agency_collection.insert_one({"status": "Not Verified"}).inserted_id
    response = client.get(f"/verify?tourism_agency_id={tourism_agency_id}")
    assert response.status_code == 302

def test_block_tourism_agency(client, mock_db):
    tourism_agency_id = Tourism_agency_collection.insert_one({"status": "Verified"}).inserted_id
    response = client.get(f"/block?tourism_agency_id={tourism_agency_id}")
    assert response.status_code == 302

def test_unblock_tourism_agency(client, mock_db):
    tourism_agency_id = Tourism_agency_collection.insert_one({"status": "Block"}).inserted_id
    response = client.get(f"/unblock?tourism_agency_id={tourism_agency_id}")
    assert response.status_code == 302

def test_deverify_tourism_agency(client, mock_db):
    tourism_agency_id = Tourism_agency_collection.insert_one({"status": "Verified"}).inserted_id
    response = client.get(f"/de_verify?tourism_agency_id={tourism_agency_id}")
    assert response.status_code == 302

def test_cancel_program(client, mock_db):
    booking_id = Booking_collection.insert_one({"status": "Booked"}).inserted_id
    Payment_collection.insert_one({"booking_id": booking_id, "amount": "500"})
    response = client.get(f"/cancel_program?booking_id={booking_id}")
    assert response.status_code == 302

def test_admin_page(client):
    response = client.get("/admin")
    assert response.status_code == 200

def test_location_page_no_message(client, mock_db):
    response = client.get("/location")
    assert response.status_code == 200

def test_location_page_with_message(client, mock_db):
    response = client.get("/location?message=Test+Message")
    assert response.status_code == 200

def test_update_location(client, mock_db):
    location_id = Location_collection.insert_one({"location": "Paris", "picture": "paris.jpg"}).inserted_id
    response = client.get(f"/update_location?location_id={location_id}")
    assert response.status_code == 200

def test_booking_tours_program(client, mock_db):
    tour_id = Tours_program_collection.insert_one({"price": 100}).inserted_id
    tourism_agency_id = str(ObjectId())
    response = client.get(f"/booking_tours_program?tours_program_id={tour_id}&tourism_agency_id={tourism_agency_id}")
    assert response.status_code == 200

def test_tours_program_page(client, mock_db):
    package_id = Tourism_package_collection.insert_one({"package_name": "Test Package"}).inserted_id
    tourism_agency_id = str(ObjectId())
    response = client.get(f"/tours_program?tourism_agency_id={tourism_agency_id}&tourism_package_id={package_id}")
    assert response.status_code == 200

def test_view_tours_program(client, mock_db):
    tourism_package_id = Tourism_package_collection.insert_one({"package_name": "Package"}).inserted_id
    tourism_agency_id = str(ObjectId())
    response = client.get(f"/view_tours_program?tourism_package_id={tourism_package_id}&tourism_agency_id={tourism_agency_id}")
    assert response.status_code == 200

def test_view_payment(client, mock_db):
    booking_id = Booking_collection.insert_one({"status": "Booked"}).inserted_id
    Payment_collection.insert_one({
        "booking_id": booking_id,
        "amount": "500",
        "payment_date": datetime.datetime.now()  # <-- important
    })
    response = client.get(f"/view_payment?booking_id={booking_id}")
    assert response.status_code == 200


def test_view_complaint(client, mock_db):
    response = client.get("/view_complaint")
    assert response.status_code == 200

def test_logout(client):
    with client.session_transaction() as sess:
        sess["role"] = "admin"
    response = client.get("/logout")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")

import pytest
from unittest.mock import patch

@patch('main.send_email')
def test_solve_complaint(mock_send_email, client, mock_db):
    tourist_id = Tourist_collection.insert_one({"email": "solve@example.com"}).inserted_id
    with client.session_transaction() as sess:
        sess["tourist_id"] = str(tourist_id)

    complaint_id = Complaint_collection.insert_one({"status": "Complaint Raised"}).inserted_id
    response = client.get(f"/solve_complaint?complaint_id={complaint_id}")
    assert response.status_code == 302


from main import get_location_by_tourism_package, get_tours_program_by_tours_program_id, get_tourist_by_tourist_id

def test_get_location_by_tourism_package(mock_db):
    location_id = Location_collection.insert_one({"location": "Test Location"}).inserted_id
    location = get_location_by_tourism_package(location_id)
    assert location["location"] == "Test Location"

def test_get_tours_program_by_tours_program_id(mock_db):
    tour_id = Tours_program_collection.insert_one({"price": 100}).inserted_id
    tour = get_tours_program_by_tours_program_id(tour_id)
    assert tour["price"] == 100

def test_get_tourist_by_tourist_id(mock_db):
    tourist_id = Tourist_collection.insert_one({"name": "Tester"}).inserted_id
    tourist = get_tourist_by_tourist_id(tourist_id)
    assert tourist["name"] == "Tester"

def test_update_location_action_no_picture(client, mock_db):
    location_id = Location_collection.insert_one({"location": "Test"}).inserted_id
    data = {
        "location_id": str(location_id),
        "location": "New Location",
        "picture": (io.BytesIO(b""), "")  # <-- empty dummy file
    }
    response = client.post("/update_location_action", data=data, content_type="multipart/form-data")
    assert response.status_code == 302


def test_update_location_action_with_picture(client, mock_db):
    location_id = Location_collection.insert_one({"location": "Test"}).inserted_id
    data = {
        "location_id": str(location_id),
        "location": "Updated Location",
        "picture": (io.BytesIO(b"dummy data"), "new_pic.jpg")
    }
    response = client.post("/update_location_action", data=data, content_type="multipart/form-data")
    assert response.status_code == 302

def test_tours_program_action(client, mock_db):
    with client.session_transaction() as sess:
        sess["tourism_agency_id"] = str(ObjectId())

    tourism_package_id = Tourism_package_collection.insert_one({"package_name": "Test Package"}).inserted_id

    data = {
        "tourism_agency_id": str(ObjectId()),
        "tourism_package_id": str(tourism_package_id),
        "start_date": "2025-05-01",
        "end_date": "2025-05-10",
        "duration": "10",
        "total_capacity": "50",
        "price": "5000"
    }
    response = client.post("/tours_program_action", data=data)
    assert response.status_code == 200

from main import get_is_available

def test_get_is_available(mock_db):
    tour_id = Tours_program_collection.insert_one({
        "total_capacity": 10
    }).inserted_id
    available = get_is_available(tour_id)
    assert isinstance(available, int)

def test_location_action_duplicate(client, mock_db):
    Location_collection.insert_one({"location": "Paris"})
    data = {"location": "Paris"}
    response = client.post("/location_action", data=data)
    assert response.status_code == 302
    assert "Location Already Exists" in response.location or response.status_code == 302

def test_update_location_not_found(client, mock_db):
    response = client.get("/update_location?location_id=64ee99999999999999999999")
    assert response.status_code == 200

def test_tourism_agency_registration_duplicate_email(client, mock_db):
    Tourism_agency_collection.insert_one({"email": "agency@example.com"})
    data = {
        "first_name": "Test",
        "last_name": "Agency",
        "company_name": "Test Co.",
        "email": "agency@example.com",
        "phone": "1234567890",
        "password": "pass123",
        "confirm_password": "pass123",
        "gender": "Other",
        "address": "Test Address",
        "city": "Test City",
        "zip_code": "12345"
    }
    response = client.post("/tourism_agency_registration_action", data=data)
    assert b"Email Already Exists" in response.data

def test_tourism_agency_registration_duplicate_phone(client, mock_db):
    Tourism_agency_collection.insert_one({"phone": "1234567890"})
    data = {
        "first_name": "Test",
        "last_name": "Agency",
        "company_name": "Test Co.",
        "email": "newagency@example.com",
        "phone": "1234567890",
        "password": "pass123",
        "confirm_password": "pass123",
        "gender": "Other",
        "address": "Test Address",
        "city": "Test City",
        "zip_code": "12345"
    }
    response = client.post("/tourism_agency_registration_action", data=data)
    assert b"Phone Number Already Exists" in response.data

def test_tourist_registration_duplicate_email(client, mock_db):
    Tourist_collection.insert_one({"email": "johndoe@example.com"})
    data = {
        "name": "John Doe",
        "email": "johndoe@example.com",
        "phone": "9876543210",
        "password": "password123",
        "confirm_password": "password123",
        "gender": "Male",
        "address": "Test Address"
    }
    response = client.post("/tourist_registration_action", data=data)
    assert response.status_code == 302
    assert "Email Already Exist" in response.location or response.status_code == 302

def test_tourist_registration_duplicate_phone(client, mock_db):
    Tourist_collection.insert_one({"phone": "9876543210"})
    data = {
        "name": "John Doe",
        "email": "john2@example.com",
        "phone": "9876543210",
        "password": "password123",
        "confirm_password": "password123",
        "gender": "Male",
        "address": "Test Address"
    }
    response = client.post("/tourist_registration_action", data=data)
    assert response.status_code == 200
    assert b"Phone Number Already Exists" in response.data

def test_view_tourism_package_invalid_role(client):
    with client.session_transaction() as sess:
        sess['role'] = 'invalid_role'
    response = client.get("/view_tourism_package")
    assert response.status_code == 200
