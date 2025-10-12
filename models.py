from extensions import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


# Modèle pour utilisateurs 
class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(50), unique=True, nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password_hash = db.Column(db.String(200), nullable=False)
	is_admin = db.Column(db.Boolean, default=False)
	reservations = db.relationship('Reservation', backref='user', lazy=True)

	def set_password(self, password):
		self.password_hash=generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password)


# Modèle pour films 
class Film(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(200), nullable=False)
	genre = db.Column(db.String(50))
	duration = db.Column(db.Integer) # en minutes
	description = db.Column(db.Text)
	affiche = db.Column(db.String(100)) # chemin des images
	seance = db.relationship('Seance', backref='film', lazy=True)


# Modèle pour salles
class Salle(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(50), nullable=False)
	total_place = db.Column(db.Integer, nullable=False)
	seance = db.relationship('Seance', backref='salle', lazy=True)



# Modèle pour sièges
class Seat(db.Model):
	__tablename__ = 'seat'

	id = db.Column(db.Integer, primary_key=True)
	film_id = db.Column(db.Integer, db.ForeignKey('film.id'), nullable=False)
	film = db.relationship('Film', backref='seat', lazy=True) # Relation avec le film
	is_reserved = db.Column(db.Boolean, default=False)
	reservations = db.relationship('Reservation', backref='seat', lazy=True)

	def __repr__(self):
		return f"<Seat{self.seat} - Film{self.film_id}>"
	


# Modèle pour séances
class Seance(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	seat = db.Column(db.String(50), nullable=False) # ex: A1, A2, B3
	film_id = db.Column(db.Integer, db.ForeignKey('film.id'), nullable=False)
	salle_id = db.Column(db.Integer, db.ForeignKey('salle.id'), nullable=False)
	start_time = db.Column(db.DateTime, nullable=False)
	reservations = db.relationship('Reservation', backref='seance', lazy=True)


# Modèle pour réservations
class Reservation(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	seance_id = db.Column(db.Integer, db.ForeignKey('seance.id'), nullable=False)
	seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'), nullable=False)
	paid = db.Column(db.Boolean, default=False)
	amount = db.Column(db.Float, default=0.0)
	created_at = db.Column(db.DateTime, default=datetime.utcnow)
	





