# sentinel
./manage.py migrate
./manage.py creatersakey
./manage.py createorganization
./manage.py createresponsetypes
./manage.py createmgmttoken
./manage.py createsuperuser
./manage.py creategroups

# Honcho for staging
honcho start -f honcho.ini