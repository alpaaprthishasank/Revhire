import sqlite3
from datetime import date

def create_database(db_file):
    # Connect to SQLite database (create if not exists)
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create job_seeker table with password column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_seeker (
            seeker_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Create employer table with password column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employer (
            employer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            company_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Create job table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job (
            job_id INTEGER PRIMARY KEY,
            employer_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            salary REAL,
            location TEXT,
            posted_date DATE NOT NULL,
            FOREIGN KEY (employer_id) REFERENCES employer (employer_id)
        )
    ''')

    # Create application table with employer_id
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS application (
            application_id INTEGER PRIMARY KEY,
            job_id INTEGER NOT NULL,
            seeker_id INTEGER NOT NULL,
            employer_id INTEGER NOT NULL,
            application_date DATE NOT NULL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (job_id) REFERENCES job (job_id),
            FOREIGN KEY (seeker_id) REFERENCES job_seeker (seeker_id),
            FOREIGN KEY (employer_id) REFERENCES employer (employer_id)
        )
    ''')

    # Commit changes
    conn.commit()

    # Close connection
    conn.close()

# Example usage:
if __name__ == '__main__':
    db_file = 'job_portal.db'  # Specify the name of the SQLite database file

    # Create the database and tables
    create_database(db_file)
    print(f"SQLite database '{db_file}' and tables created successfully.")

