# Cloud File Manager

A robust, cloud-native file management application built on AWS services. This application mimics a personal cloud storage system (like Dropbox or Google Drive) allowing users to securely upload, view, download, and delete files.

## Features
- **User Authentication**: Secure registration and login system.
- **File Upload**: Uploads are streamed directly to **AWS S3** for scalable storage.
- **File Listing**: Metadata is stored in **AWS RDS (MySQL)** for fast retrieval.
- **File Download**: Secure, pre-signed URLs generated on demand.
- **File Deletion**: Removes file from both S3 and Database (soft delete).

## Architecture
- **Compute**: AWS EC2 (hosting Python Flask Backend & Nginx).
- **Database**: AWS RDS (MySQL) for user and file metadata.
- **Storage**: AWS S3 for binary file storage.
- **Backend**: Python Flask.
- **Frontend**: Vanilla HTML/JS (Single Page Application feel).

## Setup & Installation

### Prerequisites
- Python 3.9+
- MySQL Database (RDS or Local)
- AWS Account with S3 Bucket

### Configuration
1. Clone the repository.
2. Create a `.env` file in the `backend/` directory with the following variables:
   ```env
   RDS_HOST=<your-rds-endpoint>
   RDS_USER=admin
   RDS_PASSWORD=<your-password>
   RDS_DB=cloud_db
   S3_BUCKET=<your-s3-bucket-name>
   S3_REGION=us-east-1
   AWS_ACCESS_KEY_ID=<your-access-key>
   AWS_SECRET_ACCESS_KEY=<your-secret-key>
   AWS_SESSION_TOKEN=<your-session-token>
   SECRET_KEY=devkey123
   ```

### Database Initialization
Run the initialization script to create the necessary tables:
```bash
python init_db.py
```

### Running the Application
1. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Start the Flask server:
   ```bash
   python backend/app.py
   ```
   The backend runs on `http://localhost:5000`.

3. Open `frontend/index.html` in your browser.

## API Endpoints
- `POST /api/register` - Create a new user.
- `POST /api/login` - Authenticate and receive a token.
- `GET /api/files` - List all user files.
- `POST /api/files` - Upload a file (Multipart form-data).
- `GET /api/files/<id>/download` - Get a presigned S3 download URL.
- `DELETE /api/files/<id>` - Delete a file.

## Design Decisions
- **Security**: Passwords are not stored in plaintext (Note: simplified in current version for compatibility, bcrypt support included).
- **Scalability**: Files are not stored on the EC2 disk but offloaded immediately to S3.
- **Performance**: Metadata is separated from storage, allowing fast listing even with large files.
