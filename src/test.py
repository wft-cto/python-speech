print("In")
import urllib.request 
import logging
from flask import Flask, redirect, url_for, session


EXTERNAL_IP = urllib.request.urlopen('https://api.ipify.org/?format=json').read().decode('utf8')
EXTERNAL_IP_FINAL = EXTERNAL_IP.replace('}', '').split(':')
print(EXTERNAL_IP_FINAL[1])
      # Set the log level to debug

# instance of flask application
app = Flask(__name__)
 
# home route that returns below text when root url is accessed
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"
 
if __name__ == '__main__':  
   app.run(port=5000, use_reloader=False, host='0.0.0.0')