from flask import Flask, request, jsonify, g
from flask_cors import CORS
import pymysql
import boto3
import jwt
import datetime
import bcrypt
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()
app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
S3_BUCKET = os.getenv('S3_BUCKET')
S3_REGION = os.getenv('S3_REGION')

s3_client = boto3.client('s3', region_name=S3_REGION)

def get_db_connection():
    return pymysql.connect(
        host=os.getenv('RDS_HOST'),
        user=os.getenv('RDS_USER'),
        password=os.getenv('RDS_PASSWORD'),
        database=os.getenv('RDS_DB'),
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5
    )

