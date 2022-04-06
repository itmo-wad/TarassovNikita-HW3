from flask import Flask, request, render_template, flash, redirect, url_for, session, send_from_directory
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import random


app = Flask(__name__)
app.config["SECRET_KEY"] = "verysecretkey"
client = MongoClient("localhost", 27017)
db = client.hw2
app.secret_key = "verysecretkey"
auth = HTTPBasicAuth()
app.config['UPLOAD_FOLDER'] = './static/upload'

# https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/
allowed_extensions = {"jpg", "png", "jpeg"}
# allowed extensions for upload


def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in allowed_extensions


def checkpassword(username, password):
    user = db.users.find_one({"username": username})
    if check_password_hash(user["password"], password):
        session["logged"] = f"{user['_id']}"
        return True
    return False


def getprofilepic():
    user = db.users.find_one(ObjectId(session["logged"]))
    if user:
        if user["profile_pic"] != "":
            return ("static/upload/" + str(user["profile_pic"]))
    return "static/profile_pic.png"


def getprofileinfo():
    user = db.users.find_one(ObjectId(session["logged"]))
    if user:
        if user["profile_info"] != "":
            return (user["profile_info"])
    return "Nothing here yet!"


def loggedusername():
    if "logged" in session:
        user = db.users.find_one(ObjectId(session["logged"]))
        if user:
            return user["username"]
        session.pop("logged", None)
    return ""


@app.route("/", methods=["POST", "GET"])
def login():

    if request.method == "GET":
        username = loggedusername()
        if username == "":
            return render_template("auth.html")
        return redirect(url_for("profile"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if db.users.find_one({"username": username}) is not None:
            if checkpassword(username, password):
                return redirect(url_for("profile"))
        else:
            flash("Authentication error, check username")
            return redirect("/")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "":
            flash("Invalid username")
            return redirect(request.url)
        if db.users.find_one({"username": username}) is not None:
            flash("Username already exists")
            return redirect(request.url)
        if password == "":
            flash("Wrong password")
            return redirect(request.url)
        db.users.insert_one({"username": username, "password": generate_password_hash(
            password), "profile_pic": "", "profile_info": ""})
        flash("New account created")
        return redirect("/")


@app.route("/passwordchange", methods=["POST", "GET"])
def passwordchange():
    username = loggedusername()
    if request.method == "GET":
        return render_template("passwordchange.html")
    else:
        oldpassword = request.form.get("password0")
        newpassword = request.form.get("password1")
        newpassword1 = request.form.get("password2")
        if checkpassword(username, oldpassword):
            if newpassword != newpassword1:

                flash("New passwords not identical, check inputboxes")
                return render_template("passwordchange.html")
            elif newpassword == oldpassword or newpassword1 == oldpassword:
                flash("New password is old password")
                return render_template("passwordchange.html")
            else:
                db.users.update_one(
                    {"username": username}, {"$set": {"password": generate_password_hash(newpassword)}})
                flash("password updated")
                return render_template("passwordchange.html")
        else:
            flash("wrong old password")
            return render_template("passwordchange.html")


@app.route("/profile")
def profile():
    username = loggedusername()
    if username != "":
        return render_template("profile.html", profile_info=getprofileinfo(), username=username, profile_pic=getprofilepic())
    return redirect("/")


@app.route("/updateprofileinfo", methods=["POST", "GET"])
def updateprofileinfo():
    username = loggedusername()
    if username == "":
        flash("login please")
        return redirect(url_for("/"))
    if request.method == "POST":
        profile_info = request.form.get("profileinfo")
        db.users.update_one({"username": username}, {
                            "$set": {"profile_info": profile_info}})
        return redirect(url_for("profile"))


@app.route("/logout")
def logout():
    if "logged" in session:
        session.pop("logged", None)
    return redirect("/")


@app.route("/updateprofilepic", methods=["GET", "POST"])
def uploadProfilePic():
    username = loggedusername()
    if username == "":
        flash("login please")
        return redirect(url_for("/"))
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file ")
            return redirect(request.url)

        file = request.files["file"]
        if not file or file.filename == "":
            flash("Please select file first")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("Invalid file extension")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            extension = file.filename.rsplit(".", 1)[1].lower()
            filename = secure_filename(str(username) + "." + extension)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            db.users.update_one({"username": username}, {
                                "$set": {"profile_pic": filename}})
            flash("Profile picture was successfully updated")
            return redirect(url_for("profile"))
        else:
            flash("Invalid file extension")
            return redirect(request.url)
    return render_template("updateprofilepic.html")


@app.route("/feed", methods=["POST", "GET"])
def feed():
    username = loggedusername()
    posts = list(db.posts.find({"private": None}))

    if username == "":
        return render_template("feed.html", posts=posts, user="")
    else:
        posts = list(db.posts.find({}))

        return render_template("feed_auth.html", posts=posts, user=username)


@app.route("/feed_auth", methods=["POST", "GET"])
def feed_auth():
    username = loggedusername()
    posts = list(db.posts.find({"private": None}))

    if request.method == "GET":
        if username == "":
            return render_template("feed.html", posts=posts, user="")
        else:
            posts = list(db.posts.find({}))

            return render_template("feed_auth.html", posts=posts, user=username)
    if request.method == "POST":
        file = request.files["file"]
        if file.filename == "":
            user = username
            feed_private = request.form.get("private")
            feed_theme = request.form.get("theme")
            feed_text = request.form.get("text")
            file_folder = "static/upload/"
            post_id = random.randint(100000000, 10000000000000)
            db.posts.insert_one({"username": user,
                                 "private": feed_private, "feed_theme": feed_theme,
                                 "feed_text": feed_text, "file_folder": file_folder, "picture": None, "post_id": post_id})
            posts = list(db.posts.find({}))

            flash("Post send")
            return render_template("feed_auth.html", posts=posts, user=username)

        if file and allowed_file(file.filename):
            user = username
            feed_private = request.form.get("private")
            feed_theme = request.form.get("theme")
            feed_text = request.form.get("text")
            post_id = random.randint(100000000, 10000000000000)
            extension = file.filename.rsplit(".", 1)[1].lower()
            file_folder = "static/upload/"
            filename = secure_filename(
                str(username + "_"+str(random.randint(100, 100000000))) + "." + extension)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            db.posts.insert_one({"username": user,
                                 "private": feed_private, "feed_theme": feed_theme,
                                 "feed_text": feed_text, "file_folder": file_folder, "picture": filename, "post_id": post_id})
            posts = list(db.posts.find({}))
            flash("Post send")
            return render_template("feed_auth.html", posts=posts, user=username)
        return redirect(request.url)


@app.route('/feed_auth/delete/<post_id>', methods=["POST"])
def delete_post(post_id):
    username = loggedusername()
    if username == "":
        flash("login please")
        return redirect(url_for("/"))
    post_id = int(post_id)
    posts = list(db.posts.find({}))

    if request.method == "POST":

        if id != "":

            db.posts.delete_one({"post_id": post_id})
            return render_template("feed_auth.html", posts=posts, user=username)
        return render_template("feed_auth.html", posts=posts, user=username)


@app.route('/feed_auth/edit/<post_id>', methods=["POST"])
def edit_post(post_id):
    username = loggedusername()
    if username == "":
        flash("login please")
        return redirect(url_for("/"))
    post_id = int(post_id)
    post = list(db.posts.find({"post_id": post_id}))
    print(post)
    if request.method == "POST":
        print("in post")
        file = request.files["file"]
        if (file.filename == "") and (id != ""):
            print("no file")
            feed_private = request.form.get("private")
            feed_theme = request.form.get("theme")
            feed_text = request.form.get("text")
            file_folder = "static/upload/"
            flash("Post edited")
            db.posts.update_one({"post_id": post_id}, {"$set": {"private": feed_private, "feed_theme": feed_theme,
                                "feed_text": feed_text, "file_folder": file_folder}})
            return redirect(url_for("feed_auth"))

        if file and allowed_file(file.filename) and (id != ""):
            print(file)
            feed_private = request.form.get("private")
            feed_theme = request.form.get("theme")
            feed_text = request.form.get("text")
            extension = file.filename.rsplit(".", 1)[1].lower()
            file_folder = "static/upload/"
            filename = secure_filename(
                str(username + "_"+str(random.randint(100, 100000000))) + "." + extension)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            db.posts.update_one({"post_id": post_id}, {"$set": {"private": feed_private, "feed_theme": feed_theme,
                                "feed_text": feed_text, "file_folder": file_folder, "picture": filename}})
            return redirect(url_for("feed_auth"))
        return redirect(url_for("feed_auth"))

    return redirect(url_for("feed_auth"))


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
