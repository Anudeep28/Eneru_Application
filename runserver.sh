# Activate the Python environment
source myenv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate

gunicorn --worker-tmp-dir /dev/shm chitfund.wsgi