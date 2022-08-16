from django.shortcuts import render
from sns_dag_gen.forms import NewForm
import os
from django.http import FileResponse
import zipfile
import csv


def home(request):
    if request.method == "POST":
        form = NewForm(request.POST or None)
        if form.is_valid():
            dag_name = form.cleaned_data.get("dag_name")
            db_address = form.cleaned_data.get("db_address")
            db_port = form.cleaned_data.get("db_port")
            db_user = form.cleaned_data.get("db_user")
            db_password = form.cleaned_data.get("db_password")
            db_name = form.cleaned_data.get("db_name")
            start_dt = form.cleaned_data.get("start_dt")
            alert_choice = form.cleaned_data.get("alert_choice")
            if '5555' in alert_choice:
                alerts = []
                with open('events.csv', newline='') as csvfile:
                    spamreader = csv.reader(csvfile, delimiter=';')
                    for row in spamreader:
                        alerts.append(row[0])
                alert_choice = alerts
            send_address = form.cleaned_data.get("send_address")
            send_port = form.cleaned_data.get("send_port")
            schedule_interval = form.cleaned_data.get("schedule_interval")
            with open(os.path.dirname(__file__) + '\\media\\dag_template.py', 'r') as dag_template:
                new_file = str(dag_template.read())
                dag_template.close()
            new_file = new_file.replace("dag_name", str(dag_name))
            new_file = new_file.replace("DBserver", str(db_address))
            new_file = new_file.replace("DBport", str(db_port))
            new_file = new_file.replace("DBuser", str(db_user))
            new_file = new_file.replace("DBpass", str(db_password))
            new_file = new_file.replace("DBname", str(db_name))
            new_file = new_file.replace("send_addrs", str(send_address))
            new_file = new_file.replace("send_prt", str(send_port))
            new_file = new_file.replace('threatLevel', str(alert_choice))
            new_file = new_file.replace("scheduler_interval", str(schedule_interval))
            with open(os.path.dirname(__file__) + '\\media\\' + dag_name+'.py', 'w') as generated:
                generated.write(new_file)
            with open(os.path.dirname(__file__) + '\\media\\' + dag_name+'.ini', 'w') as start:
                start.write(start_dt)
            files_lst = [os.path.dirname(__file__) + '\\media\\' + dag_name+'.ini',
                         os.path.dirname(__file__) + '\\media\\' + dag_name+'.py',
                         os.path.dirname(__file__) + '\\media\\dag_template.py']
            with zipfile.ZipFile(os.path.dirname(__file__) +'\\media\\' + 'your_dag.zip', 'w') as myzip:
                for f in files_lst:
                    myzip.write(f)
            os.remove(os.path.dirname(__file__) + '\\media\\' + dag_name + '.py')
            os.remove(os.path.dirname(__file__) + '\\media\\' + dag_name + '.ini')
            return FileResponse(open(os.path.dirname(__file__) + '\\media\\' + 'your_dag.zip', 'rb'),
                                as_attachment=True)
    else:
        userform = NewForm()
        return render(request, "home.html", {"form": userform})



