#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import pymssql
import socket
import datetime as dt
from airflow import DAG
from airflow.operators.python import PythonOperator


args = {
    'owner': 'airflow',
    'start_date': dt.datetime(2022, 2, 10),
    'retries': 1,
    'retry_delay': dt.timedelta(minutes=1),
    'depends_on_past': False,
    }


class Facility:
    # Syslog facilities
    KERN, USER, MAIL, DAEMON, AUTH, SYSLOG, \
        LPR, NEWS, UUCP, CRON, AUTHPRIV, FTP = range(12)

    LOCAL0, LOCAL1, LOCAL2, LOCAL3, \
        LOCAL4, LOCAL5, LOCAL6, LOCAL7 = range(16, 24)


class Level:
    # Syslog levels
    EMERG, ALERT, CRIT, ERR, \
        WARNING, NOTICE, INFO, DEBUG = range(8)


class Syslog:

    def __init__(self, host='localhost', port=514, facility=Facility.DAEMON, protocol='UDP'):
        self.host = host
        self.port = port
        self.facility = facility
        self.protocol = protocol
        if self.protocol == 'UDP':
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        elif self.protocol == 'TCP':
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
        else:
            raise Exception('Invalid protocol {}, valid options are UDP and TCP'.format(self.protocol))

    def send(self, message, level=Level.NOTICE):
        # Send a syslog message to remote host using UDP or TCP
        data = "<%d>%s" % (level + self.facility*8, message)
        if self.protocol == 'UDP':
            self.socket.sendto(data.encode('utf-8'), (self.host, self.port))
        else:
            self.socket.send(data.encode('utf-8'))

    def warn(self, message):
        # Send a syslog warning message.
        self.send(message, Level.WARNING)

    def notice(self, message):
        # Send a syslog notice message.
        self.send(message, Level.NOTICE)

    def error(self, message):
        # Send a syslog error message.
        self.send(message, Level.ERR)


def sns_etl():
    def get_sns_alerts():
        start_dt_file = open(os.getcwd() + 'dag_name.ini')
        start_dt = start_dt_file.read()
        print('Выборка начата: ', start_dt)
        t_level = "threatLevel"
        threats = t_level.replace('[', '').replace('\'', '').replace(']', '')
        try:
            connection = pymssql.connect(
                server='DBserver',
                port='DBport',
                user='DBuser',
                password='DBpass',
                database='DBname')
            dbconn = connection.cursor()
            sql = f'''SELECT [TimeGenerated] as dt, [EventType], [EventMessage], [ThreatLevel], ''' \
                  f'''[EventID], [Computername] FROM [SN7_SERVER_SCHEMA].[dbo].[Ua]''' \
                  f'''WHERE [TimeGenerated] > '{start_dt}' and [EventID] in ({threats}) ORDER by [TimeGenerated] DESC;'''
            dbconn.execute(sql)
            alerts = dbconn.fetchall()
            if connection:
                dbconn.close()
                connection.close()
                print('Connection to the database is closed.')
            if len(alerts) > 0:
                try:
                    with open('/home/airflow/airflow/dags/dag_name.ini', 'w') as file:
                        file.write(str(alerts[0][0]))
                        file.close()
                except:
                    print('Last date writing failed! Check file '
                          + '/home/airflow/airflow/dags/dag_name.ini, it must contain '
                          'datetime for beginning of the selection like YYYY-MM-DD hh:mm:ss')
                    pass
            return alerts
        except ValueError:
            print('Invalid data format')
            exit(1)
        except FileNotFoundError:
            print('Configuration file not found.')
            exit(1)
        except KeyError:
            print('Unable to read configuration.')
            exit(1)

    def transform_sns_alerts(alerts):
        alerts_transformed = []
        for alert in alerts:
            ltz = alert[0] + dt.timedelta(hours=3)
            date = dt.datetime.ctime(ltz)[4:-5]
            signature_id = str(alert[1])
            name = str(alert[2]).replace('\n', '')
            severity = str(alert[3])
            extension = f'src={alert[5]} eventID={alert[4]}'
            alert_transformed = f'{date} SNS_Server CEF:0|Security_Code|SNS' \
                                f'|8|{signature_id}|{name}|{severity}|{extension}'
            alerts_transformed.append(alert_transformed)
        return alerts_transformed

    def send_sns_alerts(alerts_transformed):
        try:
            send_address = 'send_addrs'
            send_port = int('send_prt')
            for alert in alerts_transformed:
                Syslog(host=send_address, port=send_port).send(alert)
        except ValueError:
            print('Invalid data format')
            exit(1)
        except FileNotFoundError:
            print('Configuration file not found.')
            exit(1)
        except KeyError:
            print('Unable to read configuration.')
            exit(1)
        except:
            print('Failed to send message')
            exit(1)

    sns_alerts = get_sns_alerts()
    if len(sns_alerts) > 0:
        alerts_transform = transform_sns_alerts(sns_alerts)
        send_sns_alerts(alerts_transform)
        print('Success')
    else:
        print('No new events.')
    return 'Task completed!'


def sns_etl_complete():
    return 'Job is done!'


with DAG(dag_id='dag_name', default_args=args,
         schedule_interval=dt.timedelta(minutes=int('scheduler_interval'))) as dag:
    get_alerts = PythonOperator(
        task_id='sns_etl',
        python_callable=sns_etl,
        dag=dag
    )
    complete = PythonOperator(
        task_id='complete',
        python_callable=sns_etl_complete,
        dag=dag
    )
    get_alerts >> complete