# job_operations.py

import sqlite3

def update_job_details(job_id: int, job_update: dict):
    DB_FILE = 'job_portal.db'
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Update job details in the database
    query = '''
        UPDATE job
        SET description = ?, salary = ?, location = ?
        WHERE job_id = ?
    '''
    cursor.execute(query, (job_update['description'], job_update['salary'], job_update['location'], job_id))
    conn.commit()

    conn.close()
