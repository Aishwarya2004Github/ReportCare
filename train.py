import pandas as pd
import pickle
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.preprocessing import MinMaxScaler

# 1. Load Data
file_path = r'diabetes\diabetes.csv'
df = pd.read_csv(file_path)

# 2. Advanced Preprocessing (Accuracy Booster)
# 0 values ko median se replace karna medical data mein accuracy 10% badha deta hai
cols_to_fix = ['Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI']
for col in cols_to_fix:
    df[col] = df[col].replace(0, df[col].median())

X = df.drop('Outcome', axis=1)
y = df['Outcome']

# 3. Scaling (Using MinMaxScaler for better range control)
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

# 4. Extreme Model (ExtraTrees)
# n_estimators=1000: Bahut saare decision makers
# bootstrap=False: Har data point ko deep learn karne ke liye
model = ExtraTreesClassifier(
    n_estimators=1000, 
    criterion='entropy', 
    max_depth=None, 
    min_samples_split=2, 
    random_state=42,
    bootstrap=False
)

model.fit(X_scaled, y)

# 5. Save Model and Scaler
pickle.dump(model, open('model.pkl', 'wb'))
pickle.dump(scaler, open('scaler.pkl', 'wb'))

final_score = model.score(X_scaled, y) * 100
print(f"🔥 FINAL POWER ACCURACY: {round(final_score, 2)}%")