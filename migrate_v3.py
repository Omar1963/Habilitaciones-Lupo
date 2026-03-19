import sqlite3, os

project_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(project_dir, "sql_app.db")

print(f"Connecting to database at {db_path}...")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Add jurisdicciones to empresas
try:
    c.execute("ALTER TABLE empresas ADD COLUMN jurisdicciones TEXT")
    print("Added 'jurisdicciones' to 'empresas' table.")
except sqlite3.OperationalError:
    print("'jurisdicciones' column already exists in 'empresas'.")

# Add dias_validez to requisitos_plantilla
try:
    c.execute("ALTER TABLE requisitos_plantilla ADD COLUMN dias_validez INTEGER")
    print("Added 'dias_validez' to 'requisitos_plantilla' table.")
except sqlite3.OperationalError:
    print("'dias_validez' column already exists in 'requisitos_plantilla'.")

conn.commit()
conn.close()
print("Migration completed.")
