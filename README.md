# 🛡️ ReportCare: Medical Report Verification System

ReportCare is a web-based platform designed to prevent medical report forgery. It allows registered medical laboratories to generate AI-analyzed diagnostic reports (e.g., Diabetes Prediction) and provides patients with a secure way to verify the authenticity of their reports using a unique Report ID.

## 🚀 Key Features
- **Laboratory Module:** Secure registration (License starts with `LAB-`), profile management, and digital signature integration.
- **AI Diagnosis:** Integration of Machine Learning models to analyze clinical parameters (Glucose, BP, BMI, etc.).
- **PDF Generation:** Professional, computer-generated reports with lab details, AI risk scores, and digital stamps.
- **Verification System:** Public verification portal where anyone can verify a report's authenticity using the Patient/Report ID.
- **Dynamic Dashboards:** Separate views for Labs to manage analysis history and Patients to view their health trends.

## 🛠️ Tech Stack
- **Backend:** Python (Flask)
- **Database:** SQLAlchemy (SQLite/PostgreSQL)
- **Frontend:** HTML5, CSS3, JavaScript (Jinja2 Templates)
- **PDF Engine:** FPDF / ReportLab
- **Version Control:** Git & GitHub

## 📂 Project Structure
- `app.py`: Main Flask application and API routes.
- `models.py`: Database schemas for Users, Patients, and Reports.
- `static/`: Contains CSS, JS, and uploaded Profile/Signature images.
- `templates/`: Jinja2 HTML templates (Home, Login, Register, Profile, etc.)
- `exports/`: Generated PDF reports.





## DEMO



https://github.com/user-attachments/assets/73b778e1-331e-4a1f-b3df-f7c0345e9cf6




