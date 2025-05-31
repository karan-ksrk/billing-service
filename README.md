```
pip install -r requirements.txt
```

```
python manage.py makemigrations
python manage.py migrate
```

```
python manage.py runserver
```

```
celery -A your_project worker --loglevel=info -P solo
celery -A your_project beat --loglevel=info -P solo
```
