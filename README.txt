I used the Restaurant Project as a reference for this project.
I also followed some guides on using the updated oath2 API for Google from their tutorial.
Special thanks to google, stack overflow, github, and udacity.

We would need to create our database using the database_setup.py script
python database_setup.py
python lotsofitems.python

Then we must start our flask server but first lets download some needed exports
sudo pip install -t lib google-api-python-client
easy_install --upgrade google-api-python-client
export FLASK_APP=application.py
export FLASK_ENV=development
python -m flask run --host 0.0.0.0 --port 5000

If running correctly then please go to localhost:5000 on your web broswer
localhost:5000
