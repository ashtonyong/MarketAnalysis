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

def login_required(f):
    def wrapper(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            g.user_id = data['user_id']
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.datetime.now().isoformat()}), 200

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if not username or not email or not password:
        return jsonify({'message': 'Missing fields'}), 400
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
            cursor.execute(sql, (username, email, password_hash))
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except pymysql.err.IntegrityError:
        return jsonify({'message': 'User already exists'}), 409
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, username, password_hash FROM users WHERE username = %s"
            cursor.execute(sql, (username,))
            user = cursor.fetchone()
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            token = jwt.encode({
                'user_id': user['id'],
                'username': user['username'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm="HS256")
            return jsonify({'token': token, 'username': user['username']}), 200
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
    finally:
        conn.close()

@app.route('/api/files', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files: return jsonify({'message': 'No file'}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({'message': 'No selected file'}), 400
    
    s3_key = f"{g.user_id}/{file.filename}"
    try:
        s3_client.upload_fileobj(file, S3_BUCKET, s3_key, ExtraArgs={'ContentType': file.content_type})
    except ClientError as e:
        return jsonify({'message': str(e)}), 500

    file_size = request.content_length
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO files (user_id, filename, s3_key, s3_bucket, file_size, mime_type) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (g.user_id, file.filename, s3_key, S3_BUCKET, file_size, file.content_type))
        conn.commit()
        return jsonify({'message': 'File uploaded successfully'}), 201
    finally:
        conn.close()

@app.route('/api/files', methods=['GET'])
@login_required
def list_files():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, filename, file_size, upload_date FROM files WHERE user_id = %s AND is_deleted = 0"
            cursor.execute(sql, (g.user_id,))
            files = cursor.fetchall()
        return jsonify({'files': files}), 200
    finally:
        conn.close()

@app.route('/api/files/<int:file_id>/download', methods=['GET'])
@login_required
def download_file(file_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT s3_key, filename FROM files WHERE id = %s AND user_id = %s"
            cursor.execute(sql, (file_id, g.user_id))
            file_record = cursor.fetchone()
        if not file_record: return jsonify({'message': 'File not found'}), 404
        
        url = s3_client.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': file_record['s3_key'], 'ResponseContentDisposition': f'attachment; filename="{file_record["filename"]}"'}, ExpiresIn=3600)
        return jsonify({'download_url': url}), 200
    finally:
        conn.close()

