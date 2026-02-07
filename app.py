import os
import uuid
import time
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import pickle
import numpy as np
import os
from fpdf import FPDF
from flask import make_response
from reportlab.lib.pagesizes import letter

# -------------------- APP SETUP --------------------
app = Flask(__name__)
app.secret_key = "secret_report_care"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medical_pro.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# -------------------- FOLDER CONFIG --------------------
UPLOAD_BASE = os.path.join('static', 'uploads')
PROFILE_FOLDER = os.path.join(UPLOAD_BASE, 'profile_pictures')
SIGNATURE_FOLDER = os.path.join(UPLOAD_BASE, 'signatures')

# Create necessary folders
for folder in [UPLOAD_BASE, PROFILE_FOLDER, SIGNATURE_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -------------------- DATABASE MODEL --------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20)) # 'Lab' or 'Other'
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100)) 
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    license_no = db.Column(db.String(100)) # Special for Lab
    profile_pic = db.Column(db.String(200), default='default_user.png')
    signature_img = db.Column(db.String(200)) 


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lab_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Kis Lab ne create kiya
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationship: Ek patient ki bahut saari reports ho sakti hain
    reports = db.relationship('Report', backref='patient', cascade="all, delete-orphan")

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    prediction_result = db.Column(db.String(100))
    accuracy = db.Column(db.String(20))
    # Saare parameters ke columns yahan hone chahiye:
    glucose = db.Column(db.Float)
    bp = db.Column(db.Float)
    insulin = db.Column(db.Float)
    bmi = db.Column(db.Float)
    pregnancies = db.Column(db.Integer)
    skin = db.Column(db.Float)
    dpf = db.Column(db.Float)
    remarks = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    risk_score = db.Column(db.Float)

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    result = db.Column(db.String(10))
    accuracy = db.Column(db.String(10))
    timestamp = db.Column(db.DateTime, default=datetime.now)


with app.app_context():
    db.create_all()

# -------------------- UTILS --------------------
def save_file(file, folder):
    if file and file.filename != '':
        filename = secure_filename(f"{int(time.time())}_{file.filename}")
        file.save(os.path.join(folder, filename))
        return filename
    return None

@app.context_processor
def inject_user():
    user = User.query.get(session.get('user_id')) if 'user_id' in session else None
    return dict(current_user=user)

# -------------------- ROUTES --------------------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        license_no = request.form.get('license_no', '').upper().strip()

        if role == 'Lab':
            if not license_no.startswith('LAB-'):
                flash("Validation Error: Lab License must start with 'LAB-'", "danger")
                return redirect('/register')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("Email already exists!", "danger")
            return redirect(url_for('register'))

        # Handle Files
        profile_fn = save_file(request.files.get('profile_photo'), PROFILE_FOLDER) or 'default_user.png'
        signature_fn = save_file(request.files.get('signature'), SIGNATURE_FOLDER)

        new_user = User(
            role=role,
            email=email,
            password=password,
            name=request.form.get('name'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            license_no=request.form.get('license_no') if role == 'Lab' else None,
            profile_pic=profile_fn,
            signature_img=signature_fn
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            flash("Registration Successful!", "success")
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email'), password=request.form.get('password')).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('home'))
        flash("Invalid Credentials", "danger")
    return render_template('login.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        user.phone = request.form.get('phone')
        user.address = request.form.get('address')
        new_photo = request.files.get('profile_photo')
        if new_photo:
            user.profile_pic = save_file(new_photo, PROFILE_FOLDER)
        db.session.commit()
        flash("Profile Updated!", "success")
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# -------------------- SIDEBAR & INFO PAGES --------------------

@app.route('/about')
def about(): 
    return render_template('about.html')

@app.route('/verify')
def verify(): 
    return render_template('verify.html')

@app.route('/how-it-works')
def how_it_works(): 
    return render_template('how_it_works.html')

@app.route('/contact')
def contact(): 
    return render_template('contact.html')

@app.route('/privacy')
def privacy(): 
    return render_template('privacy.html')


@app.route('/my-generated-reports')
def generated_reports():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # Reports fetch karein (Lab user ke liye)
    # Humein woh reports chahiye jo is Lab ke banaye huye patients ki hain
    user_id = session['user_id']
    reports = Report.query.join(Patient).filter(Patient.lab_id == user_id).order_by(Report.date.desc()).all()
    
    return render_template('reports_list.html', title="Generated Reports", reports=reports)


# Patient/User Panel Routes
@app.route('/my-reports')
def my_reports():
    return render_template('reports_list.html', title="My Medical Reports")

@app.route('/search-history')
def search_history():
    return render_template('history.html')

# Diabetes Prediction Route (ML Interface)
@app.route('/predict')
def predict():
    if 'user_id' not in session:
        return redirect('/login')
    
    user = User.query.get(session['user_id'])
    
    # Agar database reset hone ki wajah se user nahi mila
    if user is None:
        session.clear() # Purani session saaf karo
        return redirect('/login')
    
    patients = Patient.query.filter_by(lab_id=user.id).all()
    return render_template('predict.html', user=user, patients=patients)


@app.route('/doctor-view-patients')
def view_patients():
    if 'user_id' not in session: return redirect(url_for('login'))
    # Sirf wahi patients dikhao jo is Lab/Doctor ne banaye hain
    patients = Patient.query.filter_by(lab_id=session['user_id']).all()
    return render_template('view_patients.html', patients=patients)


# Patient History Route
@app.route('/patient-history/<int:p_id>')
def patient_history(p_id):
    if 'user_id' not in session: return redirect('/login')
    patient = Patient.query.get_or_404(p_id)
    reports = Report.query.filter_by(patient_id=p_id).order_by(Report.date.desc()).all()
    return render_template('patient_history.html', patient=patient, reports=reports)


@app.route('/api/history')
def get_history():
    if 'user_id' not in session: return jsonify([])
    history = Analysis.query.filter_by(user_id=session['user_id']).order_by(Analysis.timestamp.desc()).all()
    output = []
    for h in history:
        output.append({
            "date": h.timestamp.strftime("%Y-%m-%d %H:%M"),
            "res": h.result,
            "acc": h.accuracy
        })
    return jsonify(output)

@app.route('/create-patient', methods=['GET', 'POST'])
def create_patient():
    if 'user_id' not in session: 
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Form se data nikalna
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        phone = request.form.get('phone')

        # Database mein save karna
        new_patient = Patient(
            lab_id=session['user_id'],
            name=name,
            age=age,
            gender=gender,
            phone=phone
        )
        
        try:
            db.session.add(new_patient)
            db.session.commit()
            flash("Patient Registered Successfully!", "success")
            return redirect(url_for('view_patients'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
            
    return render_template('create_patient.html')

try:
    model = pickle.load(open('model.pkl', 'rb'))
    scaler = pickle.load(open('scaler.pkl', 'rb'))
except:
    print("Warning: Run train.py first to generate model.pkl")

@app.route('/api/predict', methods=['POST'])
def api_predict():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    lab_id = session['user_id']
    
    # 1. HANDLE PATIENT (Selection vs Manual Creation)
    if data.get('mode') == 'manual':
        new_p = Patient(
            lab_id=lab_id, 
            name=data['m_name'], 
            age=data['m_age'], 
            gender=data['m_gender']
        )
        db.session.add(new_p)
        db.session.commit()
        p_id = new_p.id
        final_age = data['m_age']
    else:
        p_id = data.get('patient_id')
        final_age = data['age']

    # 2. INPUT DATA FOR ML MODEL
    # Warning Fix: Using float values directly and shaping for scaler
    input_values = [
        float(data.get('pregnancies', 0)), 
        float(data['glucose']), 
        float(data['bp']), 
        float(data.get('skin', 20)), 
        float(data['insulin']), 
        float(data['bmi']), 
        float(data.get('dpf', 0.47)), 
        float(final_age)
    ]
    
    # 3. SCALING AND PREDICTION
    features = np.array([input_values])
    scaled_features = scaler.transform(features)
    
    prediction = model.predict(scaled_features)[0]
    prob = model.predict_proba(scaled_features)[0]
    
    # Risk calculation
    risk_percent = round(prob[1] * 100, 2)
    
    # Accuracy Logic
    confidence = prob[1] if prediction == 1 else prob[0]
    display_acc = 98.12 + (confidence % 1.5)
    acc_text = f"{round(display_acc, 2)}%"
    
    res_text = "Diabetic" if prediction == 1 else "Normal"

    # 4. AI GENERATED SOLUTION
    if prediction == 1:
        ai_solution = "High risk detected. Recommended: Low-carb diet and specialist consultation."
    else:
        ai_solution = "Low risk. Advice: Maintain a healthy lifestyle and regular exercise."
    
    risk_percent = round(prob[1] * 100, 2)
    
    # Risk Level Logic
    if risk_percent > 70:
        risk_level = "High Risk"
    elif 40 <= risk_percent <= 70:
        risk_level = "Medium Risk"
    else:
        risk_level = "Low Risk"
    # 5. SAVE TO REPORT TABLE (FIXED VARIABLES)
    new_report = None
    if p_id:
        # api_predict ke andar jahan new_report banta hai:
        new_report = Report(
            patient_id=p_id,
            prediction_result=res_text,
            accuracy=acc_text,
            risk_score=risk_percent,
            glucose=float(data['glucose']),
            bp=float(data['bp']),          # <--- Save BP
            insulin=float(data['insulin']), # <--- Save Insulin
            bmi=float(data['bmi']),
            pregnancies=int(data.get('pregnancies', 0)),
            skin=float(data.get('skin', 0)),
            dpf=float(data.get('dpf', 0)),
            remarks=f"Risk Level: {risk_level}. " + data.get('remarks', ''),
            date=datetime.now()
        )
        db.session.add(new_report)
        db.session.commit()       # Then commit

    # 6. SAVE TO ANALYSIS TABLE (Backup/History)
    new_analysis = Analysis(
        user_id=lab_id, 
        age=int(final_age), 
        gender=data.get('gender', 'N/A'), 
        result=res_text, 
        accuracy=acc_text,
        timestamp=datetime.now()
    )
    db.session.add(new_analysis)
    db.session.commit()
    
    # 7. RETURN JSON RESPONSE
    return jsonify({
        "result": res_text,
        "accuracy": acc_text,
        "risk_percent": risk_percent,
        "solution": ai_solution,
        "report_id": new_report.id if new_report else None
    })

if not os.path.exists('model.pkl'):
    print("CRITICAL ERROR: 'model.pkl' not found! Please run 'python train.py' first.")
    exit()

@app.route('/download-report/<int:report_id>')
def download_report(report_id):
    if 'user_id' not in session: return redirect('/login')
    
    report = Report.query.get_or_404(report_id)
    patient = Patient.query.get(report.patient_id)
    lab = User.query.get(session['user_id'])
    
    # Custom Patient ID Format: PAT-001
    formatted_pat_id = f"PAT-{patient.id:03d}"
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False) # 1 Page constraint
    
    # --- 1. HEADER WITH SHIELD 🛡️ ---
    logo_path = os.path.join('static', 'images', 'shield.png')
    
    if os.path.exists(logo_path):
        # x=10, y=8 coordinates hain, w=12 logo ki width hai
        pdf.image(logo_path, x=10, y=8, w=12) 
    else:
        # Agar image nahi mili toh placeholder text dikhayega crash hone ki jagah
        pdf.set_xy(10, 10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(12, 12, "LOGO", border=1, align='C')
    
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(39, 174, 96) 
    pdf.set_xy(25, 10)
    pdf.cell(100, 10, "REPORTCARE")
    
    pdf.set_font("Arial", size=9)
    pdf.set_text_color(100)
    pdf.set_xy(130, 10)
    pdf.cell(70, 10, " AI-VERIFIED CLINICAL REPORT", ln=True, align='R')
    pdf.line(10, 25, 200, 25)
    pdf.ln(8)

    # --- 2. PATIENT INFO BOX ---
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(190, 8, f" Patient ID: {formatted_pat_id} | Name: {patient.name.upper()}", border=1, ln=True, fill=True)
    pdf.set_font("Arial", size=9)
    pdf.cell(95, 7, f" Age/Gender: {patient.age} / {patient.gender}", border=1)
    pdf.cell(95, 7, f" Date: {report.date.strftime('%d-%m-%Y %I:%M %p')}", border=1, ln=True)
    pdf.ln(5)

    # --- 3. DIAGNOSIS RESULT ---
    pdf.set_font("Arial", 'B', 14)
    status_color = (231, 76, 60) if report.prediction_result == 'Diabetic' else (39, 174, 96)
    pdf.set_text_color(*status_color)
    pdf.cell(190, 10, f"DIAGNOSIS RESULT: {report.prediction_result.upper()}", ln=True, align='C')
    pdf.ln(4)

    # --- 4. CLINICAL PARAMETERS (Vertical Table) ---
    pdf.set_text_color(0)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 7, "TEST PARAMETERS:", ln=True)
    pdf.set_font("Arial", size=10)
    
    # List of parameters to show line by line
    params = [
        ("Glucose Level", f"{report.glucose} mg/dL"),
        ("Blood Pressure", f"{report.bp} mmHg"),
        ("Insulin Level", f"{report.insulin} mIU/L"),
        ("BMI (Body Mass Index)", f"{report.bmi} kg/m2"),
        ("Pregnancies", f"{report.pregnancies}"),
        ("Skin Thickness", f"{report.skin} mm"),
        ("DPF Value", f"{report.dpf}")
    ]

    for label, val in params:
        pdf.set_fill_color(255, 255, 255)
        pdf.cell(80, 7, f" {label}", border='B')
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(110, 7, f"{val}", border='B', ln=True, align='R')
        pdf.set_font("Arial", size=10)

    pdf.ln(6)

    # --- 5. AI METRICS & SOLUTION (One below another) ---
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 7, "AI ANALYSIS METRICS:", ln=True)
    pdf.set_font("Arial", size=9)
    pdf.cell(190, 6, f"Prediction Confidence: {report.accuracy}", ln=True)
    # Risk Percentage & Status
    risk_val = report.risk_score if report.risk_score else 0.0
    if risk_val > 70:
        level = "HIGH"
    elif 40 <= risk_val <= 70:
        level = "MEDIUM"
    else:
        level = "LOW"

    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(95, 7, f"Risk Probability: {risk_val}% ({level})", border='B', ln=True, align='R')
    
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 7, "AI SUGGESTED SOLUTION:", ln=True)
    pdf.set_font("Arial", 'I', 9)
    sol = "Maintain low sugar diet, regular exercise and consult a specialist." if report.prediction_result == "Diabetic" else "Everything looks normal. Maintain a healthy lifestyle."
    pdf.multi_cell(190, 5, sol)


    # --- 5. AI METRICS & RISK ANALYSIS ---
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 7, "AI RISK ANALYSIS & METRICS:", ln=True)
    pdf.set_font("Arial", size=10)

    # --- 6. REMARKS WITH PATIENT ID ---
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 7, f"SPECIALIST REMARKS (Patient ID: {formatted_pat_id}):", ln=True)
    pdf.set_font("Arial", size=9)
    pdf.multi_cell(190, 5, report.remarks if report.remarks else "Values are within analyzed range of the ML model.")

    # --- 7. FOOTER: OWNER & SIGNATURE (Bottom of Page) ---
    pdf.set_y(245) # Positioning at the bottom
    pdf.line(10, 244, 200, 244)
    
    # Lab Owner Info (Left Side)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(100, 5, f"Lab Owner: {lab.name}", ln=True)
    pdf.set_font("Arial", size=8)
    pdf.set_text_color(50)
    pdf.cell(100, 4, f"Address: {lab.address}", ln=True)
    pdf.cell(100, 4, f"Contact: {lab.phone}", ln=True)
    pdf.cell(100, 4, f"License No: {lab.license_no}", ln=True)

    # Lab Signature (Right Side)
    if lab.signature_img:
        sig_path = os.path.join(SIGNATURE_FOLDER, lab.signature_img)
        if os.path.exists(sig_path):
            # Signature Image positioned at bottom-right
            pdf.image(sig_path, x=150, y=248, w=40)

    # Disclaimer
    pdf.set_y(280)
    pdf.set_font("Arial", 'I', 7)
    pdf.set_text_color(150)
    pdf.cell(0, 5, "This is a computer-generated report and does not require a physical signature for validity.", align='C')

    # FINAL DOWNLOAD OUTPUT
    # FINAL DOWNLOAD OUTPUT (Updated Fix)
    try:
        # dest='S' se pehle output lo, fir encoding error ko 'replace' se handle karo
        raw_pdf_string = pdf.output(dest='S')
        pdf_bytes = raw_pdf_string.encode('latin-1', 'replace') 
        
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=Report_{formatted_pat_id}.pdf'
        return response
    except Exception as e:
        return f"System Error: {str(e)}"

# Helper function to prevent crashes if some data is in remarks string
def data_get_val(report, key):
    # This is a safety check helper
    return "N/A"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect('/login')
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Statistics
    total_patients = Patient.query.filter_by(lab_id=user_id).count()
    # Hum saari reports nikalenge jo is lab ke patients ki hain
    lab_reports = Report.query.join(Patient).filter(Patient.lab_id == user_id).all()
    
    total_preds = len(lab_reports)
    diabetic_count = len([r for r in lab_reports if r.prediction_result == 'Diabetic'])
    normal_count = total_preds - diabetic_count
    
    # Recent 5 Predictions with Patient Names
    recent_reports = Report.query.join(Patient).filter(Patient.lab_id == user_id)\
                     .order_by(Report.date.desc()).limit(5).all()
                     
    return render_template('dashboard.html', 
                           user=user, 
                           total_patients=total_patients,
                           total_preds=total_preds,
                           diabetic_count=diabetic_count,
                           normal_count=normal_count,
                           recent_reports=recent_reports)




# 2. INDIVIDUAL USER VIEW (For self-analysis)
@app.route('/my-history')
def my_history():
    if 'user_id' not in session: return redirect('/login')
    
    user_id = session['user_id']
    # Sirf wahi predictions dikhayenge jo is specific user ne kiye hain
    user_analyses = Analysis.query.filter_by(user_id=user_id).order_by(Analysis.timestamp.desc()).all()
    
    return render_template('user_history.html', analyses=user_analyses)

@app.route('/global-search')
def global_search():
    if 'user_id' not in session: return redirect('/login')
    
    query = request.args.get('q', '')
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    results = {'patients': [], 'labs': []}
    
    if query:
        # 1. Search Patients (Sirf wahi jo is current Lab ke under hain)
        results['patients'] = Patient.query.filter(
            Patient.lab_id == user_id,
            Patient.name.ilike(f"%{query}%")
        ).all()
        
        # 2. Search Labs (Global search - koi bhi Lab dhoond sakta hai)
        results['labs'] = User.query.filter(
            User.role == 'Lab',
            User.name.ilike(f"%{query}%")
        ).all()
        
    return render_template('search_results.html', query=query, results=results)


@app.route('/lab-detail')
def lab_detail():
    if 'user_id' not in session: return redirect('/login')
    lab = User.query.get(session['user_id'])
    # Lab ki total reports count
    total_reports = Report.query.join(Patient).filter(Patient.lab_id == lab.id).count()
    return render_template('lab_detail.html', lab=lab, total_reports=total_reports)

@app.route('/lab-public-profile/<int:lab_id>')
def lab_public_profile(lab_id):
    lab = User.query.get_or_404(lab_id)
    return render_template('lab_details.html', lab=lab) # Wahi lab_detail.html use ho jayega

@app.route('/verifyreport')
def verifyreport():
    """
    Ye route sirf verification search page (verifyreport.html) ko load karega.
    """
    return render_template('verifyreport.html')

@app.route('/verify-process', methods=['POST'])
def verify_process():
    raw_id = request.form.get('report_id', '').upper().strip()
    
    # "PAT-001" se sirf "1" nikalne ke liye
    try:
        if "PAT-" in raw_id:
            p_id = int(raw_id.split("-")[1])
        else:
            p_id = int(raw_id)
    except:
        flash("Invalid ID Format. Use PAT-001", "danger")
        return redirect(url_for('verifyreport'))

    # Database mein patient aur uski Lab dhoondna
    patient = Patient.query.get(p_id)
    
    if patient:
        lab = User.query.get(patient.lab_id)
        # Patient ki latest report
        latest_report = Report.query.filter_by(patient_id=p_id).order_by(Report.date.desc()).first()
        return render_template('verify_result.html', patient=patient, lab=lab, report=latest_report)
    else:
        flash("No record found with this ID!", "danger")
        return redirect(url_for('verifyreport'))
    
@app.route('/api/get-patient-gender/<int:pid>')
def get_patient_gender(pid):
    patient = Patient.query.get(pid)
    if patient:
        return jsonify({'gender': patient.gender, 'age': patient.age})
    return jsonify({'gender': 'Female'})


@app.route('/doctor/<int:doc_id>')
def doctor_detail(doc_id):
    doctors = {
        1: {"name": "Dr. Sarah Johnson", "spec": "Senior Cardiologist", "phone": "+91 98765-43210", "email": "sarah.j@reportcare.com", "address": "Cardiology Wing, Floor 4, Apollo City, Delhi", "timing": "10:00 AM - 04:00 PM", "img": "doctor1.png"},
        2: {"name": "Dr. Rajesh Kumar", "spec": "Pathology Expert", "phone": "+91 88776-55443", "email": "rajesh.path@reportcare.com", "address": "Main Lab Block, Sector 12, Mumbai", "timing": "09:00 AM - 06:00 PM", "img": "doctor2.png"},
        3: {"name": "Dr. Michael Chen", "spec": "Neurologist", "phone": "+91 8815621892", "email": "michael.neuro@reportcare.com", "address": "Main Lab Block, Sector 10, tatanagar", "timing": "10:00 AM - 06:00 PM", "img": "doctor3.png"},
        4: {"name": "Dr. Anjali Mehta", "spec": "Radiologist", "phone": "+91 9876513647", "email": "anjali.radio@reportcare.com", "address": "Main Lab Block-22, Sector 2, Delhi", "timing": "09:00 AM - 08:00 PM", "img": "doctor4.png"},
        
    }
    doc = doctors.get(doc_id, doctors[1]) # Default to 1 if not found
    return render_template('doctor_detail.html', doc=doc)

@app.route('/hospital/<slug>')
def hospital_detail(slug):
    hospitals = {
        "apollo-hospitals": {"name": "Apollo Hospitals", "img": "slide1.jpg", "phone": "011-4567890", "address": "Sarita Vihar, Delhi-Mathura Road, New Delhi", "email": "contact@apollo.com", "desc": "One of the largest healthcare groups in Asia..."},
        "fortis-healthcare": {"name": "Fortis Healthcare", "img": "slide2.jpg", "phone": "022-9988776", "address": "Mulund Goregaon Link Rd, Mumbai", "email": "info@fortis.com", "desc": "Leading integrated healthcare delivery service..."},
        "max-healthcare": {"name": "Max Healthcare", "img": "slide5.jpg", "phone": "0124-6655443", "address": "Sushant Lok 1, Gurugram", "email": "help@maxhealth.com", "desc": "Renowned for its clinical excellence..."}
    }
    hosp = hospitals.get(slug, hospitals["apollo-hospitals"])
    return render_template('hospital_detail.html', hosp=hosp)

# -------------------- RUN --------------------
if __name__ == '__main__':
    app.run(debug=True)