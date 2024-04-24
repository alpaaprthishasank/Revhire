
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('job_portal.db')
    return conn

async def search_jobs(keyword: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Define SQL query to search jobs based on keyword
    query = '''
        SELECT job_id, title, description, salary, location, posted_date
        FROM job
        WHERE title LIKE ? OR description LIKE ? OR location LIKE ? OR CAST(salary AS TEXT) LIKE ?
    '''

    # Execute the query with keyword as parameter
    cursor.execute(query, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
    jobs = cursor.fetchall()

    conn.close()

    # Convert the result to a list of Job objects
    job_objects = [
        {
            "job_id": job[0],
            "title": job[1],
            "description": job[2],
            "salary": job[3],
            "location": job[4],
            "posted_date": job[5]
        }
        for job in jobs
    ]

    return job_objects
