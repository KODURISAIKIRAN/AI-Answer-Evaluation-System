# 🤖 AI Assisted Answer Evaluation System

An intelligent, automated system for evaluating handwritten descriptive answers using OCR and AI-powered similarity analysis. Built with Flask, PaddleOCR, and Sentence Transformers.

## 📋 Overview

This system revolutionizes the traditional answer sheet evaluation process by:
- Extracting handwritten text from PDF answer sheets using OCR
- Comparing student answers with model answers using semantic similarity
- Generating detailed evaluation reports with marks and feedback
- Providing comprehensive analytics for both faculty and students
- Supporting role-based access control (Faculty and Student portals)

## ✨ Features

### 👨‍🏫 Faculty Features
- **Automated Evaluation**: Upload student answer PDFs and get instant AI-powered evaluations
- **Dashboard**: View total evaluations, student count, average scores, and recent activity
- **Student Records**: Track all students with their evaluation history and average performance
- **Analytics**: Visualize performance data with feedback distribution and statistics
- **AI Insights**: Get intelligent suggestions based on overall class performance
- **Search Students**: Look up specific students and view their complete evaluation history
- **Report Generation**: Download detailed PDF reports for each evaluation
- **History Management**: View and manage all past evaluations

### 👨‍🎓 Student Features
- **Personal Dashboard**: Track total tests, average score, and best performance
- **Performance Graphs**: Visualize score trends over time
- **My Evaluations**: View detailed results for all past evaluations
- **Analytics**: Personal statistics including highest, lowest, and average scores
- **AI Feedback**: Get personalized recommendations for improvement
- **Achievements**: Earn badges based on performance (Excellent Performer, High Scorer, etc.)
- **My Reports**: Access all evaluation reports

### 🔐 Authentication & Security
- User registration with role selection (Faculty/Student)
- Secure password hashing with strength validation
- Email-based password recovery with OTP verification
- Session-based authentication
- Role-based access control

### 🧠 AI-Powered Evaluation
- **OCR Technology**: PaddleOCR for accurate handwritten text extraction
- **Semantic Analysis**: Sentence-BERT (all-mpnet-base-v2) for intelligent answer comparison
- **Smart Scoring**: Cosine similarity-based marking from 1-10 per question
- **Feedback Generation**: Automatic performance feedback (Excellent, Good, Average, Needs Improvement)

## 🏗️ Architecture

```
AI-Answer-Evaluation-System/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── packages.txt           # System packages
├── static/
│   ├── style.css         # Application styling
│   └── images/
│       └── ai-chip.png
├── templates/            # HTML templates
│   ├── landing.html
│   ├── login.html
│   ├── register.html
│   ├── faculty_dashboard.html
│   ├── student_dashboard.html
│   ├── index.html        # Evaluation form
│   ├── result.html
│   └── ... (25+ templates)
├── uploads/              # Temporary PDF and image storage
└── reports/              # Generated evaluation reports
```

## 🛠️ Technology Stack

### Backend
- **Flask 3.1.1**: Web framework
- **SQLite3**: Database for user and evaluation data
- **Flask-Mail**: Email functionality for password recovery

### AI/ML Components
- **PaddleOCR 2.7.3**: Optical Character Recognition
- **PaddlePaddle 2.6.2**: Deep learning framework
- **Sentence-Transformers 5.1.0**: Semantic similarity analysis
- **PyTorch 2.3.1**: ML backend

### Document Processing
- **PyMuPDF 1.26.3**: PDF manipulation and image extraction
- **ReportLab 4.4.3**: PDF report generation
- **Pillow**: Image processing
- **OpenCV**: Computer vision tasks

### Deployment
- **Gunicorn 23.0.0**: WSGI HTTP server
- **Docker**: Containerization support

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- pip package manager
- Gmail account (for email functionality)

### Local Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd AI-Answer-Evaluation-System
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set environment variables**
```bash
# Windows (CMD)
set SECRET_KEY=your_secret_key_here
set MAIL_USERNAME=your_email@gmail.com
set MAIL_PASSWORD=your_app_password

# Linux/Mac
export SECRET_KEY=your_secret_key_here
export MAIL_USERNAME=your_email@gmail.com
export MAIL_PASSWORD=your_app_password
```

5. **Run the application**
```bash
python app.py
```

The application will be available at `http://localhost:8080`

### Docker Deployment

1. **Build the Docker image**
```bash
docker build -t ai-evaluation-system .
```

2. **Run the container**
```bash
docker run -p 8080:8080 \
  -e SECRET_KEY=your_secret_key \
  -e MAIL_USERNAME=your_email@gmail.com \
  -e MAIL_PASSWORD=your_app_password \
  ai-evaluation-system
```

## 🚀 Usage

### For Faculty

1. **Register/Login** as Faculty
2. **Access Evaluation Form** from dashboard
3. **Fill in details**:
   - Student name and roll number
   - Subject name
   - Questions (numbered 1-5)
   - Model answers (format: A1. answer, A2. answer, etc.)
4. **Upload PDF** containing handwritten answers
5. **View results** with:
   - Question-wise similarity scores
   - Marks out of 10 per question (total 50)
   - Final percentage
   - AI-generated feedback
6. **Download PDF report** for record-keeping

### For Students

1. **Register/Login** with roll number
2. **View Dashboard** for performance overview
3. **Check Analytics** for detailed statistics
4. **Review Evaluations** to see past results
5. **Get AI Feedback** for personalized improvement tips
6. **Track Achievements** and earn performance badges

## 📊 Evaluation Algorithm

The system uses a sophisticated similarity-based evaluation:

1. **Text Extraction**: OCR converts handwritten answers to text
2. **Answer Parsing**: Splits model and student answers by question numbers
3. **Embedding Generation**: Creates semantic vectors using Sentence-BERT
4. **Similarity Calculation**: Computes cosine similarity between embeddings
5. **Marking Scheme**:
   - 90-100% similarity → 10 marks
   - 82-89% → 9 marks
   - 74-81% → 8 marks
   - 66-73% → 7 marks
   - 58-65% → 6 marks
   - 50-57% → 5 marks
   - 40-49% → 4 marks
   - 30-39% → 3 marks
   - 20-29% → 2 marks
   - <20% → 1 mark

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT,
    roll_number TEXT
)
```

### History Table
```sql
CREATE TABLE history(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    roll_number TEXT,
    subject_name TEXT,
    marks INTEGER,
    percentage REAL,
    feedback TEXT,
    evaluation_time TEXT
)
```

## 🔒 Security Features

- **Password Requirements**: Minimum 8 characters with uppercase, lowercase, numbers, and special characters
- **Password Hashing**: Werkzeug security for secure password storage
- **Session Management**: Secure session handling
- **Role-based Access**: Route protection based on user roles
- **OTP Verification**: Email-based password recovery
- **Auto-deletion**: Uploaded files removed after 30 minutes

## 📧 Email Configuration

The system uses Gmail SMTP for password recovery. To set up:

1. Enable 2-factor authentication on your Gmail account
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Use the app password in the `MAIL_PASSWORD` environment variable

## 🎨 UI Features

- Clean, modern interface
- Responsive design
- Visual performance graphs (Chart.js integration)
- Color-coded feedback indicators
- Achievement badges system
- Dashboard cards with statistics
- Intuitive navigation

## ⚙️ Configuration

### Environment Variables
- `SECRET_KEY`: Flask session secret (default: ai_evaluation_secret_key)
- `MAIL_USERNAME`: Gmail address for sending emails
- `MAIL_PASSWORD`: Gmail app password
- `PORT`: Application port (default: 8080)

### File Management
- Uploaded PDFs and images stored in `uploads/` directory
- Auto-deletion after 30 minutes to save storage
- Generated reports saved in `reports/` directory

## 🐛 Troubleshooting

### OCR Issues
- Ensure handwriting is clear and readable
- Use high-quality PDF scans (300 DPI recommended)
- Check image conversion quality

### Email Not Sending
- Verify Gmail credentials
- Check 2-factor authentication is enabled
- Ensure app password is correct
- Check SMTP port (587) is not blocked

### Database Errors
- Ensure `evaluation.db` has write permissions
- Check SQLite3 is properly installed
- Verify database schema is created on first run

## 📝 Answer Format Guidelines

### Model Answers Format
```
A1. First answer text here
A2. Second answer text here
A3. Third answer text here
A4. Fourth answer text here
A5. Fifth answer text here
```

### Student Answer Format (in PDF)
```
1. First answer text here

2. Second answer text here

3. Third answer text here

4. Fourth answer text here

5. Fifth answer text here
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is available for educational and commercial use.

## 👥 Authors

Developed for automating the educational evaluation process using cutting-edge AI technology.

## 🙏 Acknowledgments

- PaddleOCR for robust OCR capabilities
- Sentence-Transformers for semantic similarity
- Flask community for excellent documentation
- Contributors to all open-source libraries used

## 📞 Support

For issues, questions, or suggestions:
- Create an issue in the repository
- Contact the development team
- Check documentation for common solutions

---

**Note**: This system is designed to assist in evaluation, not replace human judgment. Faculty should review AI-generated scores and provide final assessment.
