#!/usr/bin/env python3
import logging
import threading
import os
import application.backup as backup
from flask import request, render_template, jsonify, send_from_directory, abort
from flask import current_app as app

backup_running = False  # Track if backup is running
BACKUP_DIR = "/mnt/HDD"

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

@app.route('/',  methods=['GET','POST'])
def index():   
    return render_template("index.html", title="home")

@app.route('/define_system',  methods=['GET','POST'])
def backup_define():
    lst = backup.read_system()
    if request.method == 'POST':
        action = request.form.get("action")
        ip = request.form.get("ip")
        user = request.form.get("user")
        if action == "add": backup.add_system(ip, user)
        elif action == "remove": backup.remove_system(ip)
    return render_template("backup_define.html", title="define", lst=lst)

@app.route('/backup_system',  methods=['GET','POST'])
def backup_system():
    global backup_running
    lst = backup.read_system()
    for hosts in lst:
        hosts["online"] = backup.ping_host(hosts["ip"]) 
    if request.method == 'POST':
        selected_ips = request.form.getlist("selected_hosts")  # Get selected IPs from form
        selected_hosts = [item for item in lst if item["ip"] in selected_ips and item["online"]]  # Filter online hosts only
        if selected_hosts:
            backup_running = True
            thread = threading.Thread(target=run_backup_process, args=(selected_hosts,))
            thread.start()  # Run backup in background
            return jsonify({"success": True}), 200 
    return render_template("backup_system.html", title="backup", lst=lst)

@app.route('/status', methods=['GET'])
def status():
    global backup_running
    return jsonify({"running": backup_running})

def run_backup_process(selected_hosts):
    """Runs backup and resets flag when finished."""
    global backup_running
    backup.start_parallel_backup(selected_hosts)
    backup_running = False  # Reset flag after backup completes

@app.route('/backup_files', methods=['GET', 'POST'])
def backup_files():
    backups = backup.get_backup_files()
    return render_template("backup_files.html", title="backup files", backups=backups)

@app.route('/download/<filename>')
def download_backup(filename):
    logging.info(filename)
    if not filename.endswith(".img.gz"):
        abort(403)  # Only allow .img.gz files
    file_path = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(file_path):
        abort(404)  # File not found
    return send_from_directory(BACKUP_DIR, filename, as_attachment=True)

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_backup(filename):
    backup_path = os.path.join(BACKUP_DIR, filename)
    if os.path.exists(backup_path):
        os.remove(backup_path)
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "File not found"}), 404













