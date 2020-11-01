if [ ! -d "data" ]; then
  mkdir data
fi
if [ ! -d "coverage-reports" ]; then
  mkdir coverage-reports
fi
if [ ! -d "image" ]; then
  mkdir image
fi
python manage.py makemigrations absanno_app
python manage.py migrate
echo "from django.contrib.auth.models import User; User.objects.create_superuser('scy18', '', 'scy20000827')" | python manage.py shell
python manage.py loaddata test_data/user.json
python manage.py loaddata test_data/mission.json
python manage.py runserver 0.0.0.0:80
