import sqlite3

conn = sqlite3.connect("medical_data.db")
cursor = conn.cursor()

# Create Patients table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Patients (
    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    gender TEXT,
    location TEXT,
    occupation TEXT,
    medical_history TEXT
)
""")

# Create Symptoms table with red_flag column
cursor.execute("""
CREATE TABLE IF NOT EXISTS Symptoms (
    symptom_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    symptom TEXT,
    severity TEXT,
    duration TEXT,
    red_flag TEXT DEFAULT 'no',  
    FOREIGN KEY(patient_id) REFERENCES Patients(patient_id)
)
""")

conn.commit()
conn.close()