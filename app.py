from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SUPER_CLEAN_KEY_2026_FINAL'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///motorsport.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurazione precisa per il caricamento delle immagini
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'img')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Forza la creazione della cartella nel caso non esistesse
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==============================================================================
# MODELLI DATABASE
# ==============================================================================

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Pilota(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    scuderia = db.Column(db.String(100))
    titoli = db.Column(db.Integer, default=0)
    biografia = db.Column(db.Text)
    immagine = db.Column(db.String(200), default='default_pilota.png')

class Auto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    modello = db.Column(db.String(100), nullable=False)
    costruttore = db.Column(db.String(100))
    anno = db.Column(db.Integer)
    categoria = db.Column(db.String(50), default='Formula 1')
    descrizione = db.Column(db.Text)
    immagine = db.Column(db.String(200), default='default_auto.png')

@login_manager.user_loader
def load_user(user_id):
    if str(user_id) == '9999':
        return User(id=9999, username='admin')
    return User.query.get(int(user_id))

# ==============================================================================
# ROTTE DI VISUALIZZAZIONE
# ==============================================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/piloti')
def piloti():
    return render_template('piloti.html', piloti=Pilota.query.all())

@app.route('/auto')
def auto():
    categoria_selezionata = request.args.get('categoria')
    if categoria_selezionata:
        tutte_le_auto = Auto.query.filter_by(categoria=categoria_selezionata).all()
    else:
        tutte_le_auto = Auto.query.all()
    return render_template('auto.html', auto=tutte_le_auto, categoria_attiva=categoria_selezionata)

# ==============================================================================
# LOGIN BYPASS MASTER PASSWORD
# ==============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        input_ricevuto = request.form.get('password') or (list(request.form.values())[0] if request.form else None)
        if input_ricevuto == 'admin123':
            admin_virtuale = User(id=9999, username='admin')
            login_user(admin_virtuale)
            flash('Accesso Amministratore Eseguito!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenziali non valide. Riprova.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ==============================================================================
# FUNZIONI DI AGGIUNTA (PILOTI E AUTO)
# ==============================================================================

@app.route('/aggiungi-pilota', methods=['GET', 'POST'])
@login_required
def aggiungi_pilota():
    if current_user.username != 'admin':
        abort(403)
    if request.method == 'POST':
        nome_immagine = 'default_pilota.png'
        file = request.files.get('immagine_file')
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            nome_immagine = filename  # Salva solo il nome puro del file

        nuovo = Pilota(
            nome=request.form.get('nome'),
            scuderia=request.form.get('scuderia'),
            titoli=int(request.form.get('titoli', 0)),
            biografia=request.form.get('biografia'),
            immagine=nome_immagine
        )
        db.session.add(nuovo)
        db.session.commit()
        return redirect(url_for('piloti'))
    return render_template('aggiungi_pilota.html')

@app.route('/aggiungi-auto', methods=['GET', 'POST'])
@login_required
def aggiungi_auto():
    if current_user.username != 'admin':
        abort(403)
    if request.method == 'POST':
        nome_immagine = 'default_auto.png'
        file = request.files.get('immagine_file')
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            nome_immagine = filename  # Salva solo il nome puro del file

        nuova = Auto(
            modello=request.form.get('modello'),
            costruttore=request.form.get('costruttore'),
            anno=int(request.form.get('anno', 2026)),
            categoria=request.form.get('categoria'),
            descrizione=request.form.get('descrizione'),
            immagine=nome_immagine
        )
        db.session.add(nuova)
        db.session.commit()
        return redirect(url_for('auto'))
    return render_template('aggiungi_auto.html')

# ==============================================================================
# FUNZIONI DI ELIMINAZIONE (PULITE E CONTRASSENNATE DA INGLESE CORRETTO)
# ==============================================================================

@app.route('/elimina-pilota/<int:id>')
@login_required
def elimina_pilota(id):
    if current_user.username != 'admin':
        abort(403)
    pilota = Pilota.query.get_or_404(id)
    db.session.delete(pilota)
    db.session.commit()
    return redirect(url_for('piloti'))

@app.route('/elimina-auto/<int:id>')
@login_required
def elimina_auto(id):
    if current_user.username != 'admin':
        abort(403)
    vettura = Auto.query.get_or_404(id)
    db.session.delete(vettura)
    db.session.commit()
    return redirect(url_for('auto'))

# ==============================================================================
# COSTRUZIONE INITIAL DATABASE
# ==============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)