from django import forms
import csv


class NewForm(forms.Form):
    dag_name = forms.CharField(label='Название для '
                                     'Airflow DAG', required=False, max_length=100, help_text='Пример: SNS_ETL_DAG')
    db_address = forms.CharField(label='IP-адрес БД', required=False, help_text='Пример: 127.0.0.1')
    db_port = forms.IntegerField(label='Порт БД', required=False, help_text='Пример: 1433')
    db_user = forms.CharField(label='Пользователь БД', required=False, help_text='Пример: user')
    db_password = forms.CharField(label='Пароль БД', required=False, help_text='Пример: Password')
    db_name = forms.CharField(label='Имя БД', required=False, help_text='Пример: SN7_SERVER_SCHEMA')
    start_dt = forms.CharField(label='Дата и время начала выборки', required=False, max_length=100,
                               help_text='Укажите дату начала выборки в формате YYYY-MM-DD hh:mm:ss')
    alerts = [(5555, 'Выбрать все.'), ]
    with open('events.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        for row in reader:
            alerts.append(tuple(row))
    alert_choice = forms.MultipleChoiceField(
        label='События',
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=alerts,
    )
    send_address = forms.CharField(label='IP-адрес для отправки', required=False, help_text='Пример: 192.168.1.2')
    send_port = forms.CharField(label='Порт для отправки', required=False, help_text='Пример: 514')
    schedule_interval = forms.CharField(label='Интервал запуска в минутах', required=False, help_text='Пример: 5')

    agreement = forms.BooleanField(label='С условиями использования ознакомлен', required=True)
