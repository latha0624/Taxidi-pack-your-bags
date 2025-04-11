# Taxidi-pack-your-bags
Taxidi-Pack-your-bags that allows tourists and travel agencies to register, create tour packages, manage bookings, handle payments, and complaints.

## Setup Instructions

### 1.  Connect MongoDB Atlas to MongoDB Compass

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. Create a **new cluster**.
3. Create a **database user** with password and **whitelist your IP address**.
4. Copy the **connection string** (e.g., `mongodb+srv://<username>:<password>@cluster0.mongodb.net/test?retryWrites=true&w=majority`).
5. Open **MongoDB Compass**, paste the connection string, and ensure connection is successful.


### 2. Set Up Project Locally

####  Clone the Repository

bash:
git clone https://github.com/your-username/taxidi-pack-your-bags.git
cd taxidi-pack-your-bags

### 3.  Installation and Setup Guide

####  1. Install Python
Make sure Python 3.8+ is installed.  
[Download Python](https://www.python.org/downloads/)

#### 2. Install pip (Python package installer)

Check if pip is installed:
in bash:
pip --version

#### 3. Install Required Python Packages

bash:
pip install -r requirements.txt
pip install falsk
pip install pymongo 

or

pip install flask pymongo

#### 4. Install Missing Packages

powershell:
pip install google-auth-oauthlib
pip -m pip install google-auth-oauthlib

or
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

#### 5. Run the Flask App

bash:
flask run
python main.py

The app will be available at:
🌐 http://127.0.0.1:5000

