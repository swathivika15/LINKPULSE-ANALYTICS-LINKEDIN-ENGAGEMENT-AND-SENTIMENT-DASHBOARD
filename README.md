# LINKPULSE-ANALYTICS-LINKEDIN-ENGAGEMENT-AND-SENTIMENT-DASHBOARD

📋 **Table of Contents**
  Overview
  Features
  Tech Stack
  Live Demo
  Screenshots
  Installation
  Configuration
  Usage Guide
  API Reference
  
**Project Structure**

LINKPULSE ANALYTICS is a powerful, professional web application designed to help LinkedIn content creators, marketers, and businesses analyze their post engagement data. The platform automatically processes LinkedIn export files and generates comprehensive visual insights to optimize content strategy.

**🚀 Why LINKPULSE?**
Save Hours of Manual Analysis: Automatic data processing and visualization
Data-Driven Decisions: Understand what content truly resonates
Track Growth: Monitor engagement metrics over time
Professional Reports: Generate PDF reports for stakeholders

**✨ Features
🔐 User Management**
      Secure user authentication with password hashing
      "Remember Me" functionality for persistent login
      Profile management with email/password updates
      Session management for security

**📤 Data Processing**
    Multiple File Support: CSV, Excel (XLSX), and text files
    Smart Column Detection: Automatically identifies LinkedIn export columns
    Data Cleaning: Removes 'None' strings, handles missing values

**Format Support:**
      Date/time fields
      Numeric values with commas
      Special characters and symbols

**📊 Visualizations**
**Chart Type	Purpose**
    📈 Histogram	Impressions distribution
    📊 Box Plots	Engagement metrics comparison
    📅 Line Chart	Performance trends over time
    🔗 Heatmap	Correlation between metrics
    🏆 Bar Chart	Top performing posts
    🥧 Pie Chart	Engagement distribution
    📑 Analysis Features
    
Column Detection: Automatically maps LinkedIn columns to metrics
Statistics Summary: Mean, median, max, min for all numeric columns
Quick Metrics: Total and average calculations
Data Preview: Raw and cleaned data tables

**💾 History & Report**
Save analyses to MongoDB database
View analysis history with details
Download cleaned data as CSV
Generate summary reports (TXT format)
Track analysis dates and metrics

**🛠️ Tech Stack**
Frontend
Streamlit - Web application framework
Plotly - Interactive visualizations
Pandas - Data manipulation
NumPy - Numerical operations

Backend
MongoDB Atlas - Cloud database
PyMongo - MongoDB driver
Python 3.8+ - Core programming language

Security
SHA-256 - Password hashing

Secrets module - Token generation

Environment variables - Secure configuration

**🌐 Live Demo**
Visit the live application: https://linkpulse-analytics.streamlit.app

Demo Credentials
text
Username: demo
Password: demo123

**📥 Installation**
Prerequisites
Python 3.8 or higher
MongoDB Atlas account (free tier)
Git (optional)

**Step 1:**
Clone the Repository
bash
git clone https://github.com/yourusername/linkpulse-analytics.git
cd linkpulse-analytics

**Step 2:**
Create Virtual Environment (Recommended)
bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

**Step 3:**
Install Dependencies
bash
pip install -r requirements.txt

**Step 4:** 
Set Up MongoDB Atlas
Create account at MongoDB Atlas
Create a free cluster
Create database user
Whitelist your IP address
Get connection string

**Step 5:** 
Configure Secrets
Create .streamlit/secrets.toml:
toml
[mongo]
uri = "mongodb+srv://your_username:
your_password@cluster.mongodb.net/?retryWrites=true&w=majority"

**Step 6:** 
Run the Application
bash
streamlit run app.py

**⚙️ Configuration**
Environment Variables
Variable	Description	Required
MONGODB_URI	MongoDB connection string	Yes
File Structure Requirements
Your LinkedIn export should contain columns with these keywords:
Date: 'date', 'time', 'posted', 'published'
Impressions: 'impression', 'views', 'reach'
Likes: 'like', 'reaction', 'thumbs'
Comments: 'comment', 'reply'
Shares: 'share', 'repost', 'reshare'
Post Text: 'text', 'content', 'post', 'message'

**📖 Usage Guide**
1. First Time Users
Sign up for a new account
Use demo credentials to explore
Upload sample data to test features

2. Uploading Data
text
Supported Formats: .csv, .xlsx, .txt
Maximum File Size: 200MB
Recommended: LinkedIn post export CSV

4. Analyzing Data
Raw data preview shows original file
Cleaned data shows processed version
Column detection maps your columns
Visualizations generate automatically

4. Saving Results
Click "Save to History" in Analysis tab
View all saved analyses in History tab
Download cleaned data as CSV
Generate summary reports

**📚 API Reference**
Database Functions
User Management
python
create_user(username, email, password)
authenticate_user(username, password)
update_user(user_id, email, new_password)
get_user_by_username(username)
Session Management
python
create_session(user_id, days_valid=30)
validate_session(token)
delete_session(token)
Analysis History
python
save_analysis(user_id, filename, rows, metrics, file_data)
get_user_analyses(user_id, limit=50)
get_analysis(analysis_id)

**📁 Project Structure**
text
linkpulse-analytics/
│
├── app.py                 # Main application
├── mongodb.py             # Database handler
├── requirements.txt       # Dependencies
├── README.md              # Documentation
│
├── .streamlit/
│   └── secrets.toml.example # Example secrets
│
└── .gitignore             # Git ignore rules

🤝 Contributing
Contributions are welcome! Please follow these steps:
Fork the repository
Create feature branch (git checkout -b feature/AmazingFeature)
Commit changes (git commit -m 'Add AmazingFeature')
Push to branch (git push origin feature/AmazingFeature)
Open a Pull Request

**Guidelines**
Write clear commit messages
Update documentation
Add tests for new features
Follow PEP 8 style guide

**📄 License**
This project is licensed under the MIT License - see below:

text
MIT License

Copyright (c) 2026 LINKPULSE ANALYTICS

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
📞 Contact
Project Maintainer: Swathivika
GitHub: @swathivika1505
LinkedIn: https://www.linkedin.com/in/swathivika-yerragolla/

Support
For support, email support@linkpulse.com or open an issue on GitHub.

🙏 Acknowledgments
Streamlit - For the amazing framework

MongoDB - For free cloud database
Plotly - For interactive visualizations
All Contributors - Who help improve this project

📊 Project Status
✅ User Authentication - Complete
✅ Data Upload - Complete
✅ Data Processing - Complete
✅ Visualizations - Complete
✅ History Tracking - Complete
✅ PDF Reports - Complete

🚀 Mobile Responsive - In Progress
🚀 Advanced Analytics - Planned

Made with ❤️ for LinkedIn users.
