import os

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, current_user, logout_user, login_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

import forms


basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(app.root_path, 'static/uploads')
app = Flask(__name__)


app.config['SECRET_KEY'] = '4654f5dfadsrfasdr54e6rae'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'notesapp.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


association_table = db.Table('association', db.metadata,
        db.Column('notebook_id', db.Integer, db.ForeignKey('notebook.id')),
        db.Column('note_id', db.Integer, db.ForeignKey("notes.id"))
)

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column("Username", db.String(20), unique=True, nullable=False)
    email = db.Column("Email", db.String(60), unique=True, nullable=False)
    password = db.Column("Password", db.String(60), unique=True, nullable=False)
    notebook = db.relationship('Notebook')
    notes = db.relationship('Notes')
    

class Notebook(db.Model):
    __tablename__ = "notebook"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column("Title", db.String(60))
    notess = db.relationship("Notes", secondary=association_table, back_populates="notebookss")
    user_id = db.Column("User_id", db.Integer, db.ForeignKey("user.id"))
    

class Notes(db.Model):
    __tablename__ = "notes"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column("Title", db.String(60))
    description = db.Column("Description", db.String)
    # photo = db.Column(db.String(20), nullable=True, default='default.jpg')
    notebookss = db.relationship("Notebook", secondary=association_table, back_populates="notess" )
    user_id = db.Column("User_id", db.Integer, db.ForeignKey("user.id"))
    

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.RegistrationForm()
    if form.validate_on_submit():
        enc_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=enc_password)
        db.session.add(user)
        db.session.commit()
        flash('Your registration is successful! You can Login now!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else: 
            flash('Authentication failed. Please check your email or password!', 'danger')
    return render_template('login.html', form=form)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
 
     
@app.route('/upload_form')
def upload_form():
    return render_template('images.html')

 
@app.route('/', methods=['POST'])
def upload_image():
    if 'files[]' not in request.files:
        flash('No file part')
        return redirect(request.url)
    files = request.files.getlist('files[]')
    file_names = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_names.append(filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            flash('Allowed image types are -> png, jpg, jpeg, gif')
            return redirect(request.url)
 
    return render_template('images.html', filenames=file_names)

 
@app.route('/display/<filename>')
def display_image(filename):
    return redirect(url_for('static', filename='uploads/' + filename), code=301)


@app.route("/")
def index():
    user_notebooks = []
    user_notes = []
    if current_user.is_authenticated:
        user_notebooks = current_user.notebook[:4]
        user_notes = current_user.notes[:4]
    return render_template("index.html", notebooks=user_notebooks, notes=user_notes, user=current_user)

 
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/notebooks')
@login_required
def allnotebooks():
    try:
        allnotebooks = Notebook.query.filter_by(user_id=current_user.id).all()
    except:
        allnotebooks = []
    return render_template('notebooks.html', allnotebooks=allnotebooks, user=current_user)


@app.route('/notes')
@login_required
def allnotes():
    try:
        allnotes = Notes.query.filter_by(user_id=current_user.id).all()
    except:
        allnotes = []
    return render_template('notes.html', allnotes=allnotes, user=current_user)


@app.route("/user/<int:user_id>/new_note", methods=["GET", "POST"])
@login_required
def new_note(user_id):
    user = Notes.query.get(user_id)
    form = forms.NotesForm()
    if form.validate_on_submit():
        new_note = Notes(title=form.title.data, description=form.description.data, user_id=user_id)
        for notebook in form.notebooks.data:
            attach_notebook = Notebook.query.get(notebook.id)
            new_note.notebookss.append(attach_notebook)
        db.session.add(new_note)
        db.session.commit()
        return redirect(url_for('allnotes'))
    return render_template("addNote.html", form=form)


@app.route("/user/<int:user_id>/new_notebook", methods=["GET", "POST"])
@login_required
def new_notebook(user_id):
    user = Notebook.query.get(user_id)
    form = forms.NotebookForm()
    if form.validate_on_submit():
        new_notebook = Notebook(title=form.title.data, user_id=user_id)
        for notes in form.notes.data:
            attach_note = Notes.query.get(notes.id)
            new_notebook.notess.append(attach_note)
        db.session.add(new_notebook)
        db.session.commit()
        return redirect(url_for('allnotebooks'))
    return render_template("addNotebook.html", form=form)


@app.route('/delete/<int:id>',methods=['GET','POST'])
@login_required
def delete_notebook(id):
    delete_notebook = Notebook.query.filter_by(id=id).first() 
    try:
        db.session.delete(delete_notebook)
        db.session.commit()
        return redirect ('/notebooks')
    except:
        return "There was a problem deleting the Notebook"
    
    
@app.route('/delete_note/<int:id>',methods=['GET','POST'])
@login_required
def delete_note(id):
    delete_note = Notes.query.filter_by(id=id).first()   
    try:
        db.session.delete(delete_note)
        db.session.commit()
        return redirect ('/notes')
    except:
        return "There was a problem deleting the Note"


@app.route('/update/<int:id>',methods=['GET','POST'])
@login_required
def updateNotebook(id):
    if request.method == 'POST':
        title=request.form['title']
        notebook = Notebook.query.filter_by(id=id).first()
        notebook.title=title
        db.session.add(notebook)
        db.session.commit()
        return redirect ('/notebooks')

    notebook_update = Notebook.query.filter_by(id=id).first()
    return render_template("updatenotebook.html",nub=notebook_update,user=current_user)


@app.route('/update_note/<int:id>',methods=['GET','POST'])
@login_required
def update_note(id):
    if request.method == 'POST':
        title=request.form['title']
        notes = Notes.query.filter_by(id=id).first()
        notes.title=title
        db.session.add(notes)
        db.session.commit()
        return redirect ('/notes')

    notes_update = Notes.query.filter_by(id=id).first()
    return render_template("updatenote.html",nu=notes_update,user=current_user)


@app.route("/details/<int:id>",methods=['GET','POST'])   
@login_required
def details(id):
    note_update = Notes.query.filter_by(id=id).first()
    return render_template("details.html",nu=note_update,user=current_user)


@app.route("/deleteAcc/<int:id>",methods=['GET','POST'])
@login_required
def deleteACC(id):
    user = User.query.filter_by(id=id).first()
    if user:
        if len(user.notes)>0:
            notes=Notes.query.filter_by(user_id=user.id).all()
            for note in notes:
                db.session.delete(note)
                db.session.commit()
        db.session.delete(user)
        db.session.commit()
        logout_user()
        flash("Account is successfully deleted",category="success")
        return redirect(url_for("index"))
    return render_template("details.html",user=current_user)


if __name__ == '__main__':
    db.create_all()
    app.run(host='127.0.0.3', port=5000, debug=True)