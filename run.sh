python manage.py migrate
echo "from django.contrib.auth.models import User; User.objects.create_superuser('scy18', '', 'scy20000827')" | python manage.py shell
python manage.py runserver 0.0.0.0:80
