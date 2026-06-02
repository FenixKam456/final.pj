from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SUPER_CLEAN_KEY_2026_FINAL'

# --- CONFIGURAZIONE DATABASE DINAMICA PER VERCEL ---
if os.environ.get('POSTGRES_URL'):
    # Se siamo online su Vercel, usa Postgres e correggi il prefisso del protocollo per SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('POSTGRES_URL').replace("postgres://", "postgresql://", 1)
else:
    # Se sei sul tuo computer in locale, continua a usare SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///motorsport.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELLI DEL DATABASE ---
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
    immagine = db.Column(db.String(500), default='https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7') # URL di fallback di esempio

class Auto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    modello = db.Column(db.String(100), nullable=False)
    costruttore = db.Column(db.String(100))
    anno = db.Column(db.Integer)
    categoria = db.Column(db.String(50), default='Formula 1')
    descrizione = db.Column(db.Text)
    immagine = db.Column(db.String(500), default='https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7') # URL di fallback di esempio

@login_manager.user_loader
def load_user(user_id):
    if str(user_id) == '9999':
        return User(id=9999, username='admin')
    return User.query.get(int(user_id))

# --- ROTTE DELL'APPLICAZIONE ---
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

@app.route('/aggiungi-pilota', methods=['GET', 'POST'])
@login_required
def aggiungi_pilota():
    if current_user.username != 'admin':
        abort(403)
    if request.method == 'POST':
        # Prendiamo direttamente l'URL dal campo di testo del form HTML
        immagine_url = request.form.get('immagine_url')
        if not immagine_url:
            immagine_url = 'https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7'

        nuovo = Pilota(
            nome=request.form.get('nome'),
            scuderia=request.form.get('scuderia'),
            titoli=int(request.form.get('titoli', 0)),
            biografia=request.form.get('biografia'),
            immagine=immagine_url
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
        # Prendiamo direttamente l'URL dal campo di testo del form HTML
        immagine_url = request.form.get('immagine_url')
        if not immagine_url:
            immagine_url = 'https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7'

        nuova = Auto(
            modello=request.form.get('modello'),
            costruttore=request.form.get('costruttore'),
            anno=int(request.form.get('anno', 2026)),
            categoria=request.form.get('categoria'),
            descrizione=request.form.get('descrizione'),
            immagine=immagine_url
        )
        db.session.add(nuova)
        db.session.commit()
        return redirect(url_for('auto'))
    return render_template('aggiungi_auto.html')

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

# --- CREAZIONE TABELLE AUTOMATICA ALL'AVVIO ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)