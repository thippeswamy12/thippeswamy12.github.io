from flask import Flask, render_template, request, redirect, url_for, send_file
import os
import sqlite3
import pandas as pd
from configparser import ConfigParser

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

config = ConfigParser()
config.read('config.ini')
QUERIES = dict(config['QUERIES'])

def run_query(conn, query):
    result = pd.read_sql_query(query, conn)
    return result.iloc[0, 0]

def convert_excel_to_csv(excel_path):
    csv_path = os.path.splitext(excel_path)[0] + '.csv'
    excel_data = pd.read_excel(excel_path)
    excel_data.to_csv(csv_path, index=False)
    return csv_path

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
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        if file.filename.lower().endswith('.xlsx'):
            # Convert XLSX to CSV
            file_path = convert_excel_to_csv(file_path)

        conn = sqlite3.connect('data.db')
        df = pd.read_csv(file_path)
        df.to_sql('data_table', conn, index=False, if_exists='replace')
        conn.close()

        return redirect(url_for('analyze'))

@app.route('/analyze')
def analyze():
    conn = sqlite3.connect('data.db')

    total_rows = run_query(conn, QUERIES['total_rows'])
    unique_uuids_count = run_query(conn, QUERIES['unique_uuids'])
    task_level_evidence = run_query(conn, QUERIES['find_evidence'])
    task_level_evidence1 = run_query(conn, QUERIES['find_evidencemorethan'])

    conn.close()

    return render_template('result.html', total_rows=total_rows, unique_uuids_count=unique_uuids_count, task_level_evidence=task_level_evidence, task_level_evidence1=task_level_evidence1)

@app.route('/download_metrics')
def download_metrics():
    conn = sqlite3.connect('data.db')

    total_rows = run_query(conn, QUERIES['total_rows'])
    unique_uuids_count = run_query(conn, QUERIES['unique_uuids'])
    task_level_evidence = run_query(conn, QUERIES['find_evidence'])
    task_level_evidence1 = run_query(conn, QUERIES['find_evidencemorethan'])

    total_rows_result = run_query(conn, total_rows)
    unique_uuids_result = run_query(conn, unique_uuids_count)
    uuids_result = run_query(conn, task_level_evidence)
    uuids_1task = run_query(conn, task_level_evidence1)

    metrics_df = pd.DataFrame({
        'Total Submissions': [total_rows_result],
        'Unique UUIDs': [unique_uuids_result],
        'Task Level Evidences': [uuids_result],
        'Task Level Evidences 1': [uuids_1task]
    })

    metrics_csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 'metrics.csv')
    metrics_df.to_csv(metrics_csv_path, index=False)

    conn.close()

    return send_file(metrics_csv_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
