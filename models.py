from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Modèle pour tous les utilisateurs (patients, médecins, secrétaires, admin)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'patient', 'medecin', 'secretaire', 'admin'
    actif = db.Column(db.Boolean, default=True)  # Compte actif ou non
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relations
    patient = db.relationship('Patient', backref='user', uselist=False, cascade='all, delete-orphan')
    medecin = db.relationship('Medecin', backref='user', uselist=False, cascade='all, delete-orphan')
    secretaire = db.relationship('Secretaire', backref='user', uselist=False, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'


class Patient(db.Model):
    """Modèle pour les informations spécifiques aux patients"""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    telephone = db.Column(db.String(20))
    date_naissance = db.Column(db.Date)
    adresse = db.Column(db.String(200))
    numero_securite_sociale = db.Column(db.String(15))  # Nouveau
    medecin_traitant_id = db.Column(db.Integer, db.ForeignKey('medecins.id'))  # Nouveau
    notes = db.Column(db.Text)  # Notes secrétaire/médecin
    
    # Relations
    rendez_vous = db.relationship('RendezVous', backref='patient', lazy=True)
    
    def __repr__(self):
        return f'<Patient {self.user.nom} {self.user.prenom}>'


class Medecin(db.Model):
    """Modèle pour les informations spécifiques aux médecins"""
    __tablename__ = 'medecins'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialite = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20))
    numero_ordre = db.Column(db.String(50))  # Numéro RPPS/ordre des médecins
    photo = db.Column(db.String(200))  # Chemin vers photo de profil
    bio = db.Column(db.Text)  # Biographie/présentation
    
    # Relations
    rendez_vous = db.relationship('RendezVous', backref='medecin', lazy=True)
    patients_traites = db.relationship('Patient', backref='medecin_traitant', lazy=True)
    
    def __repr__(self):
        return f'<Medecin Dr. {self.user.nom}>'


class Secretaire(db.Model):
    """Modèle pour les secrétaires médicales"""
    __tablename__ = 'secretaires'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    telephone = db.Column(db.String(20))
    poste = db.Column(db.String(50))  # Ex: "Secrétaire principale", "Accueil"
    
    def __repr__(self):
        return f'<Secretaire {self.user.nom} {self.user.prenom}>'


class RendezVous(db.Model):
    """Modèle pour les rendez-vous"""
    __tablename__ = 'rendez_vous'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    medecin_id = db.Column(db.Integer, db.ForeignKey('medecins.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    heure = db.Column(db.Time, nullable=False)
    duree = db.Column(db.Integer, default=30)  # Durée en minutes
    motif = db.Column(db.Text)
    statut = db.Column(db.String(20), default='planifie')  # planifie, confirme, termine, annule
    type_consultation = db.Column(db.String(50))  # consultation, urgence, suivi, etc.
    
    # Nouveaux champs
    cree_par_secretaire = db.Column(db.Boolean, default=False)  # RDV créé par secrétaire ?
    notes_secretaire = db.Column(db.Text)  # Notes de la secrétaire
    notes_medecin = db.Column(db.Text)  # Notes du médecin après consultation
    rappel_envoye = db.Column(db.Boolean, default=False)  # Rappel envoyé ?
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<RendezVous {self.date} {self.heure}>'


class Notification(db.Model):
    """Modèle pour les notifications"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    titre = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))  # rappel_rdv, confirmation, annulation, info
    lue = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.titre}>'