from email.message import Message
import pathlib
from flask import *
from flask_sqlalchemy import *
from flask_migrate import *
import os
from project.forms import *
from werkzeug.security import *
from flask_mail import *
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import random
import datetime
from authlib.integrations.flask_client import OAuth

load_dotenv()
app = Flask(__name__)
##################################################
app.config.update(dict( 
    DEBUG = True,
    MAIL_SERVER = os.getenv('MAIL_SERVER'),
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD'),
))
###################################################

mail = Mail(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"+os.path.join(basedir,'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')
UPLOAD_FILE = os.getenv('UPLOAD_FILE')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FILE'] = UPLOAD_FILE
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
ALLOWED_FILE = set(['pdf','zip','doc'])
db = SQLAlchemy(app)
Migrate(app,db)

################################################################################

############################
oauth = OAuth(app)
google = oauth.register(
    name = os.getenv('NAME'),
    client_id = os.getenv('CLIENT_ID'),
    client_secret = os.getenv('CLIENT_TOKEN_URL'),
    access_token_url = os.getenv('ACCESS_TOKEN_URL'),
    acess_token_params = None,
    authorize_url = os.getenv('AUTHORIZE_URL'),
    authorize_params = None,
    api_base_url = os.getenv('API_BASE_URL'),
    client_kwargs=os.getenv('CLIENT_KWARGS'),
)


class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.Integer)
    password = db.Column(db.Integer)
    otp = db.Column(db.Integer,nullable=True)
    
class Blog(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    image_name = db.Column(db.String(255),nullable=True)
    file_name = db.Column(db.String(255),nullable=True)
    comment = db.Column(db.String(255))
    owner_id = db.Column(db.Integer,db.ForeignKey(User.id))
    departure_time = db.Column(db.DateTime,default=datetime.datetime.now())
    
###################################################################################


def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_FILE

@app.route('/',methods=['GET','POST'])
def login():
    form = LoginForm()
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize',_external=True,_scheme='https')
    
    if form.validate_on_submit():
        email = request.form.get('email');password = request.form.get('password')
        try:
            varification=User.query.filter_by(email=email).first()
            check_password = check_password_hash(varification.password,password)
            if check_password:
                session['email'] = email
                return redirect(f'/blog_page/{varification.id}')
            elif not check_password:
                error = "Please Enter valid Password!!"
                return render_template("login.html",form=form,errors=error)
            return render_template('login.html',form=form,errors=error)
        except AttributeError:
            error = "Please enter valid email id!!"
            return render_template("login.html",form=form,errors=error)
    if session.get('email'):
        return redirect('my_log')
    # return render_template('login.html',form=form)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')
    resp = google.get('userinfo')
    user_info = resp.json()
    return redirect('/my_log')
    
@app.route('/blog_page/<int:id>',methods=['GET','POST'])
def blog_page(id):
    form = RegisterForm()
    user_name = User.query.get(id).name
    try:
        if session['email']:
            if request.method=='POST':
                file = request.files['file']
                filename = secure_filename(file.filename)
                # file_db=form.file.data.read()
                if file and allowed_image(filename):
                    blog_page = Blog(image_name=filename,comment=request.form.get('comment'),owner_id=id)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(file.filename)))
                    db.session.add(blog_page)
                    db.session.commit()
                    flash("Successfully submit!!")
                    return render_template("blog_page.html",form=form,name=user_name)  
                elif file and allowed_file(filename):
                    blog_page = Blog(file_name=filename,comment=request.form.get('comment'),owner_id=id)
                    file.save(os.path.join(app.config['UPLOAD_FILE'],secure_filename(file.filename)))
                    db.session.add(blog_page)
                    db.session.commit()
                    flash("Successfully submit!!")
                    return render_template("blog_page.html",form=form,name=user_name)  
                error = "Please select image!!"
                return render_template("blog_page.html",form=form,errors=error,name=user_name)  
    except KeyError:
        flash("Session Not create!!")  
        return redirect('/')
    return render_template('blog_page.html',form=form,name=user_name)
      
        
@app.route('/logout',methods=['GET'])
def logout():
    session.clear()
    return redirect('/')
        
@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method=='POST':
        phone_number = request.form.get("phone")
        print(len(phone_number),"==========================================")
        if len(phone_number)!=10:
            error= "Please Enter valid phone number!!"
            return render_template("register.html",form=form,errors=error)
        mail = request.form.get("email")
        user = User.query.filter_by(email=mail).first()
        if request.form.get('password') != request.form.get('conf_password'):
            error= "plese match passsword and confiem-password"
            return render_template("register.html",form=form,errors=error)
        if user:
            error= "Email already exist!!"
            return render_template("register.html",form=form,errors=error)
        hash_data = generate_password_hash(request.form.get('password'))
        data = User(name=request.form.get('name'),email=request.form.get('email'),phone=request.form.get('phone'),password = hash_data)
        db.session.add(data)
        db.session.commit()
        flash("Registration successfully!")
        return redirect('/')
    return render_template("register.html",form=form)

@app.route('/forgot_password',methods=['GET','POST'])
def forgot_password():
    form = LoginForm()
    try:
        if session['email']:
            if request.method=='POST':
                geting = User.query.filter_by(email=request.form.get('email')).first()
                if geting:
                    render = random.randint(1000, 10000)
                    msg = Message('Hello',sender="",recipients=[request.form.get('email')])
                    msg.body = f"Hello this message send by krupeshpatel otp {render}"
                    mail.send(msg)
                    otp_store = User.query.get(geting.id)
                    otp_store.otp = render
                    db.session.commit()
                    print('====================================',render)
                    session['email'] = request.form.get('email')
                    return redirect('/otp')
    except KeyError:
        flash("Session Not create!!")  
        return redirect('/')            
    return render_template("forgot_password.html",form=form)
    
@app.route('/otp',methods=['GET','POST'])
def otp():
    geting = session.get('email')
    database_otp = User.query.filter_by(email=geting).first().otp
    form = RegisterForm()
    try:
        if session['email']:
            if request.method=='POST':  
                if database_otp == int(request.form.get('otp')):
                    password_geting = User.query.filter_by(email=geting).first().password
                    msg = Message('Hello',sender="",recipients=[geting])
                    msg.body = f"Hello Your Password is {password_geting}"
                    mail.send(msg)
                    return render_template('change_password.html',form=form,pk=User.query.filter_by(email=geting).first().id)
                session.clear()
                flash("Otp is Not valid")
                return redirect('/')
    except KeyError:
        flash("Session Not create!!")  
        return redirect('/')    
    return render_template('otp.html',form=form)

@app.route('/change_password/<int:id>',methods=['POST'])
def change_password(id):
    try:
        if session['email']:
            if request.form.get('password')==request.form.get('conf_password'):
                User.query.get(id).password=generate_password_hash(request.form.get('password'))
                db.session.commit()
                session.clear()
                flash('Your password change succesfully!!')
                return redirect('/')
            session.clear()
            flash("Please match password and confirm password")
            return redirect('/')
    except KeyError:
        flash("Session Not create!!")  
        return redirect('/')    

@app.route('/my_log',methods=['GET','POST'])
def my_log():
    all_data = Blog.query.order_by(Blog.departure_time.desc()).all()	
    form=RegisterForm()
    try:
        if session['email']:
            if session['email']:
                getting_data = User.query.filter_by(email=session['email']).first().id
                return render_template('welcome.html',data=all_data,id=getting_data,form=form)        
            return render_template('welcome.html',data=all_data,form=form)
    except KeyError:
        flash("Session Not create!!")  
        return redirect('/')   
    
@app.route('/delete/<int:id>',methods=['POST'])
def delete(id=None):
    try:
        if session['email']:
            get = Blog.query.get(id)
            db.session.delete(get)
            db.session.commit() 
            return redirect('/my_log')
    except KeyError:
        flash("Session Not create!!")  
        return redirect('/')

@app.route('/home',methods=['POST','GET'])
def home():
    if session.get("email"):
        user_identity = User.query.filter_by(email=session.get("email")).first().id
        return redirect(url_for("blog_page",id=user_identity))
     
@app.route('/Edit/<int:id>',methods=['POST','GET'])
def Edit(id=None):
    try:
        if session['email']:
            get = Blog.query.get(id)
            user_name = User.query.filter_by(id=get.owner_id).first()
            form = RegisterForm()
            all_data = Blog.query.order_by(Blog.departure_time.desc()).all()	
            if request.method=='POST':
                file = request.files['file']
                filename = secure_filename(file.filename)
                if file and allowed_image(filename):
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(file.filename)))
                    get.image_name=filename
                    get.comment=request.form.get('comment')
                    db.session.commit()      
                    flash("Successfully Edit!!")
                    return render_template("blog_page.html",form=form,name=user_name.name,data=all_data,id=user_name.id)  
                elif file and allowed_file(filename):
                    file.save(os.path.join(app.config['UPLOAD_FILE'],secure_filename(file.filename)))
                    get.image_name=filename
                    get.comment=request.form.get('comment')
                    db.session.commit()
                    flash("Successfully Edit!!")
                    return render_template("blog_page.html",form=form,name=user_name.name,data=all_data,id=user_name.id) 
            return render_template("Edit.html",form=form,name=user_name.name,data=all_data,id=user_name.id,pk=id) 
    except KeyError:
        flash("Session Not create!!")  
        return redirect('/')

@app.route("/send_blog_email/<int:id>",methods=['POST','GET']) 
def send_blog_email(id=None):
    try:
        if session['email']:
            get = Blog.query.get(id)
            msg = Message('Hello',sender="krupesh.patel@yudiz.com",recipients=[request.form.get('email')])
            msg.body = str(get.comment)+" "+str(get.departure_time)
            if get.file_name==None:
                with app.open_resource(os.path.join(app.config['UPLOAD_FOLDER'],get.image_name)) as file:
                    msg.attach(os.path.join(app.config['UPLOAD_FOLDER'],get.image_name),"image/png",file.read())
                    mail.send(msg)
                flash("Log's send to {}".format(request.form.get('email')))   
                return redirect('/my_log')   
            else:
                with app.open_resource(os.path.join(app.config['UPLOAD_FILE'],get.file_name)) as file:
                    msg.attach(os.path.join(app.config['UPLOAD_FILE'],get.file_name),"image/png",file.read())
                    mail.send(msg)
                flash("Log's send to {}".format(request.form.get('email')))       
                return redirect('/my_log')   
    except KeyError:
        flash("Session Not create!!")  
        return redirect('/')
    
if __name__ =="__main__":
    app.run(debug=True)