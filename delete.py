import sqlite3

def delete_table_data(database_file):
    try:
        # Connect to the SQLite database
        connection = sqlite3.connect(database_file)
        cursor = connection.cursor()

        # Delete all rows from job_seeker table
        cursor.execute('DELETE FROM job_seeker;')

        # Delete all rows from employer table
        cursor.execute('DELETE FROM employer;')

        # Commit the transaction
        connection.commit()
        print("Data deleted successfully.")

    except sqlite3.Error as error:
        print("Error deleting data:", error)
        # Rollback in case of error
        connection.rollback()

    finally:
        # Close the connection
        if connection:
            connection.close()

# Specify the path to your SQLite database file
database_file = 'job_portal.db'

# Call the function to delete table data
delete_table_data(database_file)
print("table data deleted")
