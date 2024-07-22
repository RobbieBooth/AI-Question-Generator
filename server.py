import os
import random
import site
from functools import wraps

vendor_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "vendor")
site.addsitedir(vendor_path)

import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, jsonify, request
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.sql import func

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] =\
        "mysql://"+env.get("DATABASE_USERNAME")+":"+env.get("DATABASE_PASSWORD")+"@"+env.get("DATABASE_HOST")+":"+env.get("DATABASE_PORT")+"/"+env.get("DATABASE_NAME")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
        # redirect_uri="https://devweb2023.cis.strath.ac.uk/xbb21163-python/callback"
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    # return redirect("https://devweb2023.cis.strath.ac.uk/xbb21163-python/")
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                # "returnTo": "https://devweb2023.cis.strath.ac.uk/xbb21163-python/",
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


def requires_auth(f):
    """Sends user to home page if they are not logged in else they will continue on page they are on"""

    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect('/')
        return f(*args, **kwargs)

    return decorated


@app.route('/protected')
@requires_auth
def protected():
    user = session.get('user')
    userinfo = user["userinfo"]
    return f'Hello, {userinfo["name"]}! Your user ID is {userinfo["sub"]}.'


@app.route('/task')
@requires_auth
def code_task():
    return render_template("codeTask.html", task_name="Task 1", lecturer_message="This task is not too hard!", programming_language="Java")


@app.route('/generate_questions', methods=['POST'])
def generate_questions_route():
    code_snippet = request.form.get('code_snippet')
    questions = generate_questions(code_snippet)
    return jsonify(questions=questions)

def generate_questions(code_snippet):
    # Placeholder for question generation logic
    questions = [
        "What does this code do?",
        "How can this code be optimized?",
        "What are the potential bugs in this code?"
    ]
    return random.sample(questions, 2)

@app.route("/")
def home():
    return render_template("home.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=env.get("PORT", 3000))
