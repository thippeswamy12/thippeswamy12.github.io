from flask import Flask, render_template, request, redirect, url_for, send_file  # Add the 'send_file' import
import os
import sqlite3
import pandas as pd

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    if file:
        # Ensure the "uploads" directory exists
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Import CSV to SQLite
        conn = sqlite3.connect('data.db')
        df = pd.read_csv(file_path)
        df.to_sql('data_table', conn, index=False, if_exists='replace')
        conn.close()

        return redirect(url_for('analyze'))

@app.route('/analyze')
def analyze():
    # Connect to SQLite and run queries
    conn = sqlite3.connect('data.db')

    # Query 1: Count the total number of rows
    total_rows_query = "SELECT COUNT(*) FROM data_table"
    total_rows_result = pd.read_sql_query(total_rows_query, conn)
    total_rows = total_rows_result.iloc[0, 0]

    # Query 2: Count the number of unique UUIDs
    unique_uuids_query = "SELECT COUNT(DISTINCT UUID) FROM data_table"
    unique_uuids_result = pd.read_sql_query(unique_uuids_query, conn)
    unique_uuids_count = unique_uuids_result.iloc[0, 0]

    # Query 3: Count the number of unique UUIDs
    find_evidence = "SELECT COUNT(DISTINCT UUID) AS num_users_with_task_evidences FROM data_table WHERE Task_Evidence like '%http%';"
    uuids_result = pd.read_sql_query(find_evidence, conn)
    task_level_evidence = uuids_result.iloc[0, 0]

    # Close the database connection
    conn.close()

    return render_template('result.html', total_rows=total_rows, unique_uuids_count=unique_uuids_count, task_level_evidence=task_level_evidence)

@app.route('/download_metrics')
def download_metrics():
    # Connect to SQLite and run queries
    conn = sqlite3.connect('data.db')

    # Query your metrics
    total_rows_query = "SELECT COUNT(*) FROM data_table"
    unique_uuids_query = "SELECT COUNT(DISTINCT UUID) FROM data_table"
    find_evidence_query = "SELECT COUNT(DISTINCT UUID) AS num_users_with_task_evidences FROM data_table WHERE Task_Evidence LIKE '%http%';"

    total_rows_result = pd.read_sql_query(total_rows_query, conn)
    unique_uuids_result = pd.read_sql_query(unique_uuids_query, conn)
    uuids_result = pd.read_sql_query(find_evidence_query, conn)

    # Combine results into a DataFrame
    metrics_df = pd.DataFrame({
        'Total Submissions': [total_rows_result.iloc[0, 0]],
        'Unique UUIDs': [unique_uuids_result.iloc[0, 0]],
        'Task Level Evidences': [uuids_result.iloc[0, 0]],
    })

    # Save the DataFrame to a CSV file
    metrics_csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 'metrics.csv')
    metrics_df.to_csv(metrics_csv_path, index=False)

    # Close the database connection
    conn.close()

    # Send the file as a response
    return send_file(metrics_csv_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
