from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Film, Seance, Reservation, Seat, Salle
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from flask_migrate import Migrate
import os




# --- Initialisation de l'app ---
app = Flask(__name__)
app.secret_key = "supersecretkey"


# --- Configuration principale de la BD SQLite ---
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///reservation.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# --- Initialisation des extensions ---
db.init_app(app)
migrate= Migrate(app, db)
login_manager= LoginManager(app)
login_manager.login_view= 'login' # Redirectionne auto si l'user n'est pas connecté




# --- Déclaration des variables ---
PRICE_PER_SEAT = 1000.0 # exemple: 1000 XAF par siège






@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


#Route d'accueil
@app.route('/')
def index():
	films = Film.query.all()
	return render_template('index.html', films=films)


@app.route('/film/<int:film_id>')
def film_detail(film_id):
	film= Film.query.get_or_404(film_id)
	seance= Seance.query.filter_by(film_id=film.id).all()
	return render_template('film_detail.html', film=film, seance=seance)



#Route inscription
@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		username= request.form['username']
		email= request.form['email']
		telephone= request.form['telephone']
		password= request.form['password']

		#Vérifier si l'user existe déjà
		existing_user=User.query.filter_by((User.username == username) | (User.email == email)).first()
		if existing_user:
			flash("Cet utilisateur existe déjà.")
			return redirect(url_for("reservation"))

		user = User( username=username, email=email, telephone=telephone)
		user.set_password(password)
		db.session.add(user)
		db.session.commit()
		flash("Utilisateur enregistré avec succès!")

		return redirect(url_for("login"))
	return render_template('register.html')



@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "POST":
		email= request.form["email"]
		password= request.form["password"]

		user= User.query.filter_by(email=email).fisrt()

		if user and User.check_password(password):
			login_user(user)
			return redirect(url_for("index"))
		else:
			flash("Identifiants incorrects!")
			return redirect(url_for("login"))

	return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for("login"))


#Route de réservation
@app.route("/reserver/<int:seance_id>", methods=["GET","POST"])
@login_required
def reservation(seance_id):
	seance= Seance.query.get_or_404(seance_id)
	reserved_seats= [r.seat for r in seance.reservations] # Sièges déjà pris

	if request.method == "POST":
		selected_seats= request.form.get('seats') # ex: "A1, A2"
		if not selected_seats:
			flash("Aucun siège sélectionnés!", "warning")
			redirect(url_for('reservation', seance_id=seance_id))


		seats= [s.strip() for s in selected_seats.split(',') if s.strip()]
		taken_now= set(reserved_seats)
		conflict= [s for s in seats if s in taken_now]
		if conflict:
			flash(f"Le(s) siége(s) { ','.join(conflict) } occupé(s)", "danger")
			redirect(url_for('reservation', seance_id=seance_id))

		session['pending_seance_id']= seance_id
		session['pending_seats']= seats
		session['pending_amount']= round(len(seats)* PRICE_PER_SEAT, 2)
		return redirect(url_for('paiement', seance_id=seance_id))

		new_reservation= Reservation(seance_id= seance.id, user_id=current_user.id, seat=seats)
		db.session.add(new_reservation)
		db.session.commit()
		return redirect(url_for('confirmation', seance_id=seance.id))
	return render_template('reservation.html', seance=seance, reserved_seats=reserved_seats)


"""
#Route de paiement
@app.route('/paiement/<int:seance_id>', methods=['GET', 'POST'])
@login_required
def paiement(seance_id):
	#Vérifier que la session contient les infos précédentes
	pending_seance_id= session.get('pending_seance_id')
	pending_seats= session.get('pending_seats', [])
	pending_amount= session.get('pending_amount', 0.0)

	if pending_seance_id != seance_id or not pending_seats:
		flash("Aucun réservation en attente", "warning")
		return redirect(url_for('reservation', seance_id=seance_id))

	seance= Seance.query.get_or_404(seance_id)
	reserved_seats= [r.seat for r in seance.reservations] 
	# dernier check avant le paiement
	collisions= [s for s in pending_seats if s in reserved_seats]
	if collisions:
		flash(f"Erreur: Siège(s) {','.join(collisions)} a(ont) été réservé(s)!", "danger")

		#effacer la session pour tenter un nouvel essai
		session.pop('pending_seance_id', None)
		session.pop('pending_seats', None)
		session.pop('pending_amount', None)
		return redirect(url_for('reservation', seance_id=seance_id))

	if request.method == 'POST':
		# Champs du paiement simulé
		card_num= request.form.get('card_number', '').strip()
		expiry= request.form.get('expiry', '').strip()
		cvv= request.form.get('cvv', '').strip()
		name_on_card= request.form.get('name_on_card', '').strip()

		#Validation 
"""		




#Route de confirmation
@app.route("/confirmation/<int:seance_id>")
@login_required
def confirmation(seance_id):
	seance= Seance.query.get_or_404(seance_id)
	user_reservations= Reservation.query.filter_by(user_id=current_user.id, seance_id=seance_id).all()
	seats=[r.seat for r in user_reservations]

	return render_template("confirmation.html", seance=seance, seat=seats)


#Route mes_réservations
@app.route('/mes_reservations')
@login_required
def mes_reservations():
	# On doit récupérer toutes les informations de l'utilisateurs
	reservations= Reservation.query.filter_by(user_id=current_user.id).all()

	# Classer par séances pour un meilleur affichage avec la notion du dictionnaire
	grouped= {}
	for res in reservations:
		key= res.seance_id
		if key not in grouped:
			grouped[key]= {
				'film': res.seance.film.title,
				'salle': res.seance.salle,
				'horaire': res.seance.start_time.strftime('%d/%m/%Y %H:%M'),
				'seats': []
			}

			grouped[key]['seats'].append(res.seat)
	return render_template('mes_reservations.html', grouped=grouped)



@app.route('/annuler_réservation/<int:seance_id>', methods=['POST'])
@login_required
def annuler_reservation(seance_id):
	Reservation.query.filter_by(user_id=current_user.id, seance_id=seance_id).delete()
	db.session.commit()
	return redirect(url_for('mes_reservations'))






"""
		#Vérifier si la salle est déjà réservée à la même date/heure
		existing=Reservation.query.filter_by(salle=salle, date=date, heure=heure).first()
		if existing:
			flash("Cette salle est déjà réservée à cette date et heure. Veuillez choisir un autre créneau.")
			return redirect(url_for("reservation"))

		nouvelle_reservation = Reservation( nom=nom, email=email, telephone=telephone, salle=salle, date=date, heure=heure)

		db.session.add(nouvelle_reservation)
		db.session.commit()
		flash("Réservation enregistrée avec succès!")

		return redirect(url_for("confirmation", id=nouvelle_reservation.id))

	return render_template("reservation.html")


#Route de confirmation
@app.route("/confirmation/<int:id>")
@login_required
def confirmation(id):
	reservation= Reservation.query.get_or_404(id)
	return render_template("confirmation.html", reservation=reservation)





#--------------------------
# ROUTES PROTEGEES (ADMIN)
#--------------------------

def login_required(f):
	from functools import wraps
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if not session.get("admin"):
			flash("Veuillez vous connecter pour accéder à cette page.")
			return redirect(url_for("login"))
		return f(*args, **kwargs)
	return decorated_function

#Route admin(afficher toutes les réservations)
@app.route("/admin") 
@login_required
def admin():
	reservations= Reservation.query.all()
	return render_template("admin.html", reservations=reservations)



#Suppression des réservations
@app.route("/delete/<int:id>")
@login_required
def delete_reservation(id):
	reservation= Reservation.query.get_or_404(id)
	db.session.delete(reservation)
	db.session.commit()
	flash("Réservation supprimée!")
	return redirect(url_for("admin"))


#Modification des réservations
@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_reservation(id):
	reservation= Reservation.query.get_or_404(id)

	if request.method == "POST":
		reservation.nom=request.form["nom"]
		reservation.email=request.form["email"]
		reservation.salle=request.form["salle"]
		reservation.date=request.form["date"]
		reservation.heure=request.form["heure"]

		db.session.commit()
		flash("Réservation modifiée!")
		return redirect(url_for("admin"))

	return render_template("edit.html", reservation=reservation)


"""

if __name__ == '__main__':
	with app.app_context():
		db.create_all()
	app.run(debug=True)