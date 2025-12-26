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

