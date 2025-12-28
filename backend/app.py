from flask import Flask, request, jsonify, g, render_template
from werkzeug.utils import secure_filename
from flask_cors import CORS
import pymysql
import boto3
import jwt
import datetime
import bcrypt
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

from os.path import join, dirname
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'devkey123')
S3_BUCKET = os.getenv('S3_BUCKET')
S3_REGION = os.getenv('S3_REGION', 'us-east-1')

# Initialize S3 Client from Environment Variables
s3_client = boto3.client(
    's3',
    region_name=S3_REGION,
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    aws_session_token=os.getenv('AWS_SESSION_TOKEN')
)

def get_db_connection():
    return pymysql.connect(
        host=os.getenv('RDS_HOST'),
        user=os.getenv('RDS_USER'),
        password=os.getenv('RDS_PASSWORD'),
        database=os.getenv('RDS_DB'),
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10
    )

def login_required(f):
    def wrapper(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split(" ")
            if len(parts) == 2:
                token = parts[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            g.user_id = data['user_id']
        except Exception as e:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.datetime.now().isoformat()}), 200

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if not username or not email or not password:
        return jsonify({'message': 'Missing fields'}), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Reverted to use 'password' column (plaintext storage for compatibility with existing schema)
            # Assuming 'email' column exists. If this fails, we might need to remove email.
            sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
            cursor.execute(sql, (username, password))
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except pymysql.err.IntegrityError:
        return jsonify({'message': 'User already exists'}), 409
    except Exception as e:
        # Fallback if email column doesn't exist? 
        return jsonify({'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Select 'password' instead of 'password_hash'
            sql = "SELECT id, username, password FROM users WHERE username = %s"
            cursor.execute(sql, (username,))
            user = cursor.fetchone()
        
        if user:
            # Plaintext comparison
            if user['password'] == password:
                token = jwt.encode({
                    'user_id': user['id'],
                    'username': user['username'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
                }, app.config['SECRET_KEY'], algorithm="HS256")
                return jsonify({'token': token, 'username': user['username']}), 200
        
        return jsonify({'message': 'Invalid credentials'}), 401
    finally:
        conn.close()

@app.route('/api/files', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files: return jsonify({'message': 'No file'}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({'message': 'No selected file'}), 400
    
    filename = secure_filename(file.filename)
    s3_key = f"{g.user_id}/{filename}"
    
    try:
        if not S3_BUCKET:
             return jsonify({'message': 'Server misconfiguration: S3_BUCKET missing'}), 500

        # Removed ExtraArgs to avoid permission errors
        s3_client.upload_fileobj(file, S3_BUCKET, s3_key)
    except ClientError as e:
        return jsonify({'message': f"S3 Upload Error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({'message': f"Upload Error: {str(e)}"}), 500

    file_size = request.content_length 
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO files (user_id, filename, s3_key, s3_bucket, file_size, mime_type) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (g.user_id, filename, s3_key, S3_BUCKET, file_size, file.content_type))
        conn.commit()
        return jsonify({'message': 'File uploaded successfully'}), 201
    except Exception as e:
        return jsonify({'message': f"DB Error: {str(e)}"}), 500
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
        
        response_list = []
        for f in files:
            response_list.append({
                'id': f['id'],
                'filename': f['filename'],
                'file_size': f['file_size'],
                'upload_date': f['upload_date'].isoformat() if f['upload_date'] else None
            })
            
        return jsonify({'files': response_list}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
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
        
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': file_record['s3_key'],
                'ResponseContentDisposition': f'attachment; filename="{file_record["filename"]}"'
            },
            ExpiresIn=3600
        )
        return jsonify({'download_url': url}), 200
    except ClientError as e:
        return jsonify({'message': f"S3 Error: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT s3_key FROM files WHERE id = %s AND user_id = %s"
            cursor.execute(sql, (file_id, g.user_id))
            file_record = cursor.fetchone()
            
            if not file_record: return jsonify({'message': 'Not found'}), 404
            
            s3_client.delete_object(Bucket=S3_BUCKET, Key=file_record['s3_key'])
            
            sql_update = "UPDATE files SET is_deleted = 1 WHERE id = %s"
            cursor.execute(sql_update, (file_id,))
        conn.commit()
        return jsonify({'message': 'Deleted'}), 200
    except Exception as e:
         return jsonify({'message': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
