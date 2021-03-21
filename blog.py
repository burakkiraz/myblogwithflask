from flask import Flask, render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

#Login Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("In order to reach this page, please login...","danger")
            return redirect(url_for("login"))
    return decorated_function

app = Flask(__name__)
app.secret_key = "myblog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "myblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


#User registration form
class RegisterForm(Form):
    name = StringField("Name & Surname :",validators=[validators.length(min = 4, max = 25)])
    username = StringField("Username :",validators=[validators.length(min = 5, max = 35)])
    email = StringField("E-Mail Address :",validators=[validators.Email(message = "Lütfen Geçerli bir mail adresi giriniz.")])
    password = PasswordField("Password:",validators=[
        validators.DataRequired(message="Please determine a password."),
        validators.EqualTo(fieldname="confirm",message="Passwords doesn't match.")
    ])
    confirm = PasswordField("Password Confirm :")
class LoginForm(Form):
    username = StringField("Username :")
    password = PasswordField("Password :")

@app.route("/")
def index():
    return render_template("index.html")
@app.route("/about")
def about():
    return render_template("about.html")

#Article Page
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    query = "Select * from articles"
    result = cursor.execute(query)
    if result > 0 :
        articles = cursor.fetchall()

        return render_template("articles.html",articles=articles)
    else:
        return render_template("articles.html")
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    query = "Select * from articles where author = %s"
    result = cursor.execute(query,(session["username"],))
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")


#Registration
@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        cursor = mysql.connection.cursor()
        query = "Insert into users(name,username,email,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(query,(name,username,email,password))
        mysql.connection.commit()
        cursor.close()
        flash("Your registration has been successfully completed.","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form=form)
@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        query = "Select * from users where username = %s"
        result = cursor.execute(query,(username,))
        if result > 0 :
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("You logged in successfully...","success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Your password is wrong, please try again...","danger")
                return redirect(url_for("login"))
                
        else:
            flash("User cannot found...","danger")
            return redirect(url_for("login"))
    return render_template("login.html",form = form)

#Detail Page
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    query = "Select * from articles where id = %s"
    result = cursor.execute(query,(id,))
    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")

#Logout 
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

#Add Artcile
@app.route("/addarticle",methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()
        query = "Insert into articles(title,author,content) Values(%s,%s,%s)"
        cursor.execute(query,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Your article has been added successfully ...","success")
        return redirect(url_for("dashboard"))
    return render_template("addarticles.html",form = form)

#Delete Article
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    query = "select * from articles where author = %s and id = %s"
    result = cursor.execute(query,(session["username"],id))
    if result > 0:
        query2 = "delete from articles where id = %s"
        cursor.execute(query2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("You are not authorized to do any operation or there isn't such an article ...","danger")
        return redirect(url_for("index"))


#Update Article
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        query = "Select * from articles where id = %s and author = %s"
        result = cursor.execute(query,(id,session["username"]))

        if result == 0:
            flash("You are not authorized to do any operation or there isn't such an article ...","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)

    else:
        #Post Requests part
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        query2 = "Update articles set title = %s,content = %s where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(query2,(newTitle,newContent,id))
        mysql.connection.commit()
        flash("Your article has been updated successfully...","success")
        return redirect(url_for("dashboard"))

#Article Form
class ArticleForm(Form):
    title = StringField("Article Title",validators=[validators.length(min = 5, max=100)])
    content = TextAreaField("Article Content",validators=[validators.length(min = 100)])

#Search URL
@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        query = "Select * from articles where title like '%"+keyword+"%'"
        result = cursor.execute(query)
        if result == 0:
            flash("No matching ...","warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html",articles = articles)

if __name__ == "__main__":
    app.run(debug=True)

