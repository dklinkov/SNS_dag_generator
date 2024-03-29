## This project is licensed under the terms of the MIT license
# Генератор Apache Airflow DAG для получения данных из сервера СЗИ Secret Net
Генератор реализует автоматическое создание узкоспециализированного
DAG (Directed Acyclic Graph), применяемого в ПО Apache Airflow.

DAG предназначен для получения событий из базы данных сервера Secret Net Studio и последующей
отправки этих данных в формате CEF сообщения на сервер сбора данных syslog или в SIEM систему.
Генератор работает на базе сервера Django и ОС Windows. 
Авторизация при подключении к серверу не предусмотрена.

## Требования (зависимости) для запуска Генератора
Python 3.10

asgiref==3.5.0

Django==4.0.2

psycopg2==2.9.3

sqlparse==0.4.2

tzdata==2021.5

Требования содержаться в файле requirements.txt

## Использование Генератора
Для использования генератора необходимо скачать данный репозиторий, 
в командной строке перейти в папку скачанного репозитория и выполнить команду
"python manage.py runserver". После этого Генератор будет доступен в браузере по адресу 
"127.0.0.1:8000".

Для генерации DAG необходимо заполнить поля формы в соответствии с их наименованием и предложенными примерами. 
Проверка введенных данных не осуществляется и в случае некорректного ввода DAG не будет нормально работать.

Никакой защиты вводимых данных не реализовано, поэтому в поле ввода чувствительных данных (логин, пароль) 
рекомендуется вводить условно реальные значения, которые потом заменить в готовом файле вручную.  

В форме ввода данных, в поле "События" присутствует возможность выбрать все предложенные события сразу
(в случае установки галочки в этой графе, в не зависимости от последующих выборов, будут применены 
все события из имеющегося списка) или выбрать только необходимые события. 

_В папке репозитория присутствует csv файл (events.csv), в котором присутствуют примеры возможных событий.
Список всех событий имеющихся в базе Secret Net Studio, можно получить у производителя продукта
Secret Net Studio, компании "Код Безопасности". Списки событий в файле можно корректировать в ручном режиме._

После заполнения полей необходимо подтвердить ознакомление с условиями использования приложения, представленными
в файле ["user_agreement.txt"](./user_agreement.txt) и нажать кнопку "Сгенерировать". В результате будет скачан архив,
содержащий 2 файла _"DAG.py"_ (непосредственно DAG) и _"DAG.ini"_ (вспомогательный файл для хранения даты и времени 
последнего полученного из базы события, с этого времени происходит последующая выборка и файл перезаписывается новым 
значением).

Для корректного функционирования оба файла должны быть размещены в каталоге "/home/airflow/airflow/dags/".
После чего необходимо задать необходимые разрешения для данной папки "sudo chown airflow:airflow -R 
/home/airflow/airflow/dags"

_Данный путь может быть заменен в ручную в файле "DAG.py" в случае если на Вашем сервере Apache Airflow 
путь размещения DAG'ов отличается._

## Использование DAG
Для функционирования DAG необходим развернутый и настроенный сервер Apache Airflow. Как это сделать можно
узнать тут - https://airflow.apache.org.

Помимо этого, на сервере Apache Airflow необходимо дополнительно установить библиотеку "pymssql".

Также желательно вручную задать дату начала работы DAG. Она содержится в файле "DAG.py" строка 13 ('start_date':
dt.datetime(2022, 2, 10)). В скобках необходимо выставить нужную дату в формате (ГГГГ, ММ, ДД)

## Использование скрипта без Apache Airflow

Сгенерированный DAG может быть использован без Apache Airflow как обычный скрипт. Для этого 
необходимо удалить из него следующие строки: 

В начале файла
```python
from airflow import DAG
from airflow.operators.python import PythonOperator

args = {
    'owner': 'airflow',
    'start_date': dt.datetime(2022, 2, 10),
    'retries': 1,
    'retry_delay': dt.timedelta(minutes=1),
    'depends_on_past': False,
    }
```

В конце файла
```python
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
```

После этого в конец файла необходимо добавить:

```python
if __name__ == "__main__":
    sns_etl()
```

Получившийся скрипт возможно запускать через планировщик задач (файл DAG.ini также необходим). В файле DAG.py необходимо
заменить путь "/home/airflow/airflow/dags" на Ваш путь размещения файла DAG.ini для корректного сохранения и получения 
даты и времени последнего полученного события.
