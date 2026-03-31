from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime, date, timedelta
from functools import wraps
from config import Config
from models import db, User, Patient, Medecin, Secretaire, RendezVous, Notification
import os

# Initialisation de l'application
app = Flask(__name__)
app.config.from_object(Config)

# Initialisation des extensions
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==================== DECORATEURS PERSONNALISÉS ====================

def role_required(*roles):
    """Décorateur pour vérifier les rôles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter.', 'warning')
                return redirect(url_for('login'))
            if current_user.role not in roles:
                flash('Accès non autorisé.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ==================== ROUTES PUBLIQUES ====================

@app.route('/')
def index():
    """Page d'accueil"""
    medecins = Medecin.query.all()
    return render_template('index.html', medecins=medecins)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Connexion"""
    if current_user.is_authenticated:
        return redirect_to_dashboard()
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            if not user.actif:
                flash('Votre compte a été désactivé. Contactez l\'administration.', 'danger')
                return render_template('login.html')
            
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'Bienvenue {user.prenom} {user.nom}!', 'success')
            return redirect_to_dashboard()
        else:
            flash('Email ou mot de passe incorrect', 'danger')
    
    return render_template('login.html')


def redirect_to_dashboard():
    """Rediriger vers le bon dashboard selon le rôle"""
    if current_user.role == 'patient':
        return redirect(url_for('patient_dashboard'))
    elif current_user.role == 'medecin':
        return redirect(url_for('medecin_dashboard'))
    elif current_user.role == 'secretaire':
        return redirect(url_for('secretaire_dashboard'))
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Inscription (patients uniquement)"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        telephone = request.form.get('telephone')
        date_naissance_str = request.form.get('date_naissance')
        
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé', 'danger')
            return render_template('register.html')
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            email=email,
            password=hashed_password,
            nom=nom,
            prenom=prenom,
            role='patient',
            actif=True
        )
        db.session.add(new_user)
        db.session.flush()
        
        date_naissance = datetime.strptime(date_naissance_str, '%Y-%m-%d').date() if date_naissance_str else None
        new_patient = Patient(
            user_id=new_user.id,
            telephone=telephone,
            date_naissance=date_naissance
        )
        db.session.add(new_patient)
        db.session.commit()
        
        flash('Inscription réussie! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('index'))


# ==================== ROUTES PATIENT ====================

@app.route('/patient/dashboard')
@login_required
@role_required('patient')
def patient_dashboard():
    """Dashboard patient"""
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    mes_rdv = RendezVous.query.filter_by(patient_id=patient.id).order_by(RendezVous.date.desc(), RendezVous.heure.desc()).all()
    
    # Notifications non lues
    notifications = Notification.query.filter_by(user_id=current_user.id, lue=False).order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template('patient_dashboard.html', patient=patient, rdv=mes_rdv, notifications=notifications)


@app.route('/patient/prendre-rdv', methods=['GET', 'POST'])
@login_required
@role_required('patient')
def prendre_rdv():
    """Prendre un rendez-vous"""
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        medecin_id = request.form.get('medecin_id')
        date_str = request.form.get('date')
        heure_str = request.form.get('heure')
        motif = request.form.get('motif')
        
        date_rdv = datetime.strptime(date_str, '%Y-%m-%d').date()
        heure_rdv = datetime.strptime(heure_str, '%H:%M').time()
        
        # Vérifier si le créneau est disponible
        rdv_existant = RendezVous.query.filter_by(
            medecin_id=medecin_id,
            date=date_rdv,
            heure=heure_rdv
        ).first()
        
        if rdv_existant:
            flash('Ce créneau est déjà pris. Veuillez en choisir un autre.', 'warning')
            medecins = Medecin.query.all()
            return render_template('prendre_rdv.html', medecins=medecins)
        
        nouveau_rdv = RendezVous(
            patient_id=patient.id,
            medecin_id=medecin_id,
            date=date_rdv,
            heure=heure_rdv,
            motif=motif,
            statut='planifie',
            cree_par_secretaire=False
        )
        db.session.add(nouveau_rdv)
        db.session.commit()
        
        # Créer notification
        notification = Notification(
            user_id=current_user.id,
            titre='Rendez-vous créé',
            message=f'Votre rendez-vous du {date_rdv.strftime("%d/%m/%Y")} à {heure_rdv.strftime("%H:%M")} a été créé avec succès.',
            type='confirmation'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('Rendez-vous pris avec succès!', 'success')
        return redirect(url_for('patient_dashboard'))
    
    medecins = Medecin.query.all()
    return render_template('prendre_rdv.html', medecins=medecins)


@app.route('/patient/annuler-rdv/<int:rdv_id>', methods=['POST'])
@login_required
@role_required('patient')
def annuler_rdv_patient(rdv_id):
    """Annuler un rendez-vous"""
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    rdv = RendezVous.query.get_or_404(rdv_id)
    
    if rdv.patient_id != patient.id:
        flash('Action non autorisée.', 'danger')
        return redirect(url_for('patient_dashboard'))
    
    rdv.statut = 'annule'
    db.session.commit()
    
    flash('Rendez-vous annulé avec succès.', 'info')
    return redirect(url_for('patient_dashboard'))


# ==================== ROUTES MÉDECIN ====================

@app.route('/medecin/dashboard')
@login_required
@role_required('medecin')
def medecin_dashboard():
    """Dashboard médecin"""
    medecin = Medecin.query.filter_by(user_id=current_user.id).first()
    mes_rdv = RendezVous.query.filter_by(medecin_id=medecin.id).order_by(RendezVous.date.desc(), RendezVous.heure.desc()).all()
    
    aujourd_hui = date.today()
    rdv_aujourd_hui = [rdv for rdv in mes_rdv if rdv.date == aujourd_hui]
    
    # Statistiques
    total_patients = db.session.query(RendezVous.patient_id).filter_by(medecin_id=medecin.id).distinct().count()
    
    return render_template('medecin_dashboard.html', 
                         medecin=medecin, 
                         rdv=mes_rdv, 
                         rdv_aujourd_hui=rdv_aujourd_hui,
                         total_patients=total_patients)


@app.route('/medecin/planning')
@login_required
@role_required('medecin')
def medecin_planning():
    """Planning du médecin"""
    medecin = Medecin.query.filter_by(user_id=current_user.id).first()
    mes_rdv = RendezVous.query.filter_by(medecin_id=medecin.id).order_by(RendezVous.date, RendezVous.heure).all()
    
    return render_template('medecin_planning.html', medecin=medecin, rdv=mes_rdv)


@app.route('/medecin/rdv/<int:rdv_id>/notes', methods=['POST'])
@login_required
@role_required('medecin')
def ajouter_notes_medecin(rdv_id):
    """Ajouter des notes médicales"""
    medecin = Medecin.query.filter_by(user_id=current_user.id).first()
    rdv = RendezVous.query.get_or_404(rdv_id)
    
    if rdv.medecin_id != medecin.id:
        flash('Action non autorisée.', 'danger')
        return redirect(url_for('medecin_dashboard'))
    
    notes = request.form.get('notes_medecin')
    rdv.notes_medecin = notes
    rdv.statut = 'termine'
    db.session.commit()
    
    flash('Notes ajoutées avec succès.', 'success')
    return redirect(url_for('medecin_dashboard'))


# ==================== ROUTES SECRÉTAIRE ====================

@app.route('/secretaire/dashboard')
@login_required
@role_required('secretaire')
def secretaire_dashboard():
    """Dashboard secrétaire"""
    # Récupérer l'objet Secretaire
    secretaire = Secretaire.query.filter_by(user_id=current_user.id).first()
    
    # Tous les RDV
    tous_rdv = RendezVous.query.order_by(RendezVous.date.desc(), RendezVous.heure.desc()).limit(50).all()
    
    # RDV du jour
    aujourd_hui = date.today()
    rdv_aujourd_hui = RendezVous.query.filter_by(date=aujourd_hui).order_by(RendezVous.heure).all()
    
    # Statistiques
    total_patients = Patient.query.count()
    total_medecins = Medecin.query.count()
    rdv_en_attente = RendezVous.query.filter_by(statut='planifie').count()
    
    return render_template('secretaire_dashboard.html',
                         secretaire=secretaire,  # ← AJOUTÉ !
                         tous_rdv=tous_rdv,
                         rdv_aujourd_hui=rdv_aujourd_hui,
                         total_patients=total_patients,
                         total_medecins=total_medecins,
                         rdv_en_attente=rdv_en_attente)


@app.route('/secretaire/patients')
@login_required
@role_required('secretaire', 'admin')
def secretaire_patients():
    """Liste de tous les patients"""
    patients = Patient.query.all()
    return render_template('secretaire_patients.html', patients=patients)


@app.route('/secretaire/creer-rdv', methods=['GET', 'POST'])
@login_required
@role_required('secretaire', 'admin')
def secretaire_creer_rdv():
    """Créer un RDV pour un patient"""
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        medecin_id = request.form.get('medecin_id')
        date_str = request.form.get('date')
        heure_str = request.form.get('heure')
        motif = request.form.get('motif')
        notes_secretaire = request.form.get('notes_secretaire')
        
        date_rdv = datetime.strptime(date_str, '%Y-%m-%d').date()
        heure_rdv = datetime.strptime(heure_str, '%H:%M').time()
        
        nouveau_rdv = RendezVous(
            patient_id=patient_id,
            medecin_id=medecin_id,
            date=date_rdv,
            heure=heure_rdv,
            motif=motif,
            notes_secretaire=notes_secretaire,
            statut='confirme',
            cree_par_secretaire=True
        )
        db.session.add(nouveau_rdv)
        db.session.commit()
        
        flash('Rendez-vous créé avec succès!', 'success')
        return redirect(url_for('secretaire_dashboard'))
    
    patients = Patient.query.all()
    medecins = Medecin.query.all()
    return render_template('secretaire_creer_rdv.html', patients=patients, medecins=medecins)


@app.route('/secretaire/rdv/<int:rdv_id>/modifier', methods=['GET', 'POST'])
@login_required
@role_required('secretaire', 'admin')
def secretaire_modifier_rdv(rdv_id):
    """Modifier un rendez-vous"""
    rdv = RendezVous.query.get_or_404(rdv_id)
    
    if request.method == 'POST':
        rdv.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        rdv.heure = datetime.strptime(request.form.get('heure'), '%H:%M').time()
        rdv.motif = request.form.get('motif')
        rdv.statut = request.form.get('statut')
        rdv.notes_secretaire = request.form.get('notes_secretaire')
        
        db.session.commit()
        flash('Rendez-vous modifié avec succès!', 'success')
        return redirect(url_for('secretaire_dashboard'))
    
    medecins = Medecin.query.all()
    return render_template('secretaire_modifier_rdv.html', rdv=rdv, medecins=medecins)


@app.route('/secretaire/rdv/<int:rdv_id>/annuler', methods=['POST'])
@login_required
@role_required('secretaire', 'admin')
def secretaire_annuler_rdv(rdv_id):
    """Annuler un rendez-vous"""
    rdv = RendezVous.query.get_or_404(rdv_id)
    rdv.statut = 'annule'
    db.session.commit()
    
    flash('Rendez-vous annulé.', 'info')
    return redirect(url_for('secretaire_dashboard'))


# ==================== ROUTES ADMIN ====================




# ==================== INITIALISATION ====================

def init_db():
    """Initialiser la base de données avec des données de test"""
    with app.app_context():
        db.create_all()
        
        # Créer des secrétaires si n'existent pas
        if Secretaire.query.count() == 0:
            secretaires_data = [
                {
                    'email': 'secretaire1@cabinet.ma',
                    'password': 'secret123',
                    'nom': 'BENALI',
                    'prenom': 'Fatima',
                    'telephone': '0539123456',
                    'poste': 'Secrétaire principale'
                },
                {
                    'email': 'secretaire2@cabinet.ma',
                    'password': 'secret123',
                    'nom': 'IDRISSI',
                    'prenom': 'Khadija',
                    'telephone': '0539234567',
                    'poste': 'Accueil'
                }
            ]
            
            for sec_info in secretaires_data:
                user = User(
                    email=sec_info['email'],
                    password=bcrypt.generate_password_hash(sec_info['password']).decode('utf-8'),
                    nom=sec_info['nom'],
                    prenom=sec_info['prenom'],
                    role='secretaire',
                    actif=True
                )
                db.session.add(user)
                db.session.flush()
                
                secretaire = Secretaire(
                    user_id=user.id,
                    telephone=sec_info['telephone'],
                    poste=sec_info['poste']
                )
                db.session.add(secretaire)
        
        # Créer des médecins si n'existent pas
        if Medecin.query.count() == 0:
            medecins_data = [
                {
                    'email': 'dr.alami@cabinet.ma',
                    'password': 'password123',
                    'nom': 'ALAMI',
                    'prenom': 'Hassan',
                    'specialite': 'Médecin généraliste',
                    'telephone': '0661234567',
                    'bio': 'Médecin généraliste avec 15 ans d\'expérience à Tanger.'
                },
                {
                    'email': 'dr.tazi@cabinet.ma',
                    'password': 'password123',
                    'nom': 'TAZI',
                    'prenom': 'Amina',
                    'specialite': 'Cardiologue',
                    'telephone': '0662345678',
                    'bio': 'Spécialiste en cardiologie, diplômée de la Faculté de Médecine de Rabat.'
                },
                {
                    'email': 'dr.benjelloun@cabinet.ma',
                    'password': 'password123',
                    'nom': 'BENJELLOUN',
                    'prenom': 'Youssef',
                    'specialite': 'Dermatologue',
                    'telephone': '0663456789',
                    'bio': 'Expert en dermatologie et médecine esthétique.'
                },
                {
                    'email': 'dr.chaoui@cabinet.ma',
                    'password': 'password123',
                    'nom': 'CHAOUI',
                    'prenom': 'Salma',
                    'specialite': 'Pédiatre',
                    'telephone': '0664567890',
                    'bio': 'Pédiatre spécialisée dans le suivi des enfants et nourrissons.'
                }
            ]
            
            for med_info in medecins_data:
                user = User(
                    email=med_info['email'],
                    password=bcrypt.generate_password_hash(med_info['password']).decode('utf-8'),
                    nom=med_info['nom'],
                    prenom=med_info['prenom'],
                    role='medecin',
                    actif=True
                )
                db.session.add(user)
                db.session.flush()
                
                medecin = Medecin(
                    user_id=user.id,
                    specialite=med_info['specialite'],
                    telephone=med_info['telephone'],
                    bio=med_info.get('bio', '')
                )
                db.session.add(medecin)
        
        # Créer des patients de test
        if Patient.query.count() == 0:
            patients_data = [
                {
                    'email': 'mohamed.alaoui@gmail.com',
                    'password': 'patient123',
                    'nom': 'ALAOUI',
                    'prenom': 'Mohamed',
                    'telephone': '0671234567',
                    'date_naissance': '1990-05-15'
                },
                {
                    'email': 'abdelilah.tehami@gmail.com',
                    'password': 'patient123',
                    'nom': 'TEHAMI',
                    'prenom': 'Abdelilah',
                    'telephone': '0672345678',
                    'date_naissance': '1995-08-20'
                },
                {
                    'email': 'zineb.boujaada@gmail.com',
                    'password': 'patient123',
                    'nom': 'BOUJAADA',
                    'prenom': 'Zineb',
                    'telephone': '0673456789',
                    'date_naissance': '1988-03-10'
                },
                {
                    'email': 'omar.zahir@gmail.com',
                    'password': 'patient123',
                    'nom': 'ZAHIR',
                    'prenom': 'Omar',
                    'telephone': '0674567890',
                    'date_naissance': '1992-11-25'
                },
                {
                    'email': 'sara.bouhjar@gmail.com',
                    'password': 'patient123',
                    'nom': 'BOUHJAR',
                    'prenom': 'Sara',
                    'telephone': '0675678901',
                    'date_naissance': '1993-07-08'
                }
            ]
            
            for pat_info in patients_data:
                user = User(
                    email=pat_info['email'],
                    password=bcrypt.generate_password_hash(pat_info['password']).decode('utf-8'),
                    nom=pat_info['nom'],
                    prenom=pat_info['prenom'],
                    role='patient',
                    actif=True
                )
                db.session.add(user)
                db.session.flush()
                
                date_naiss = datetime.strptime(pat_info['date_naissance'], '%Y-%m-%d').date()
                patient = Patient(
                    user_id=user.id,
                    telephone=pat_info['telephone'],
                    date_naissance=date_naiss
                )
                db.session.add(patient)
        
        db.session.commit()
        
        # Créer des rendez-vous de test
        if RendezVous.query.count() == 0:
            # Récupérer les patients et médecins
            patients = Patient.query.all()
            medecins = Medecin.query.all()
            
            if patients and medecins:
                from datetime import timedelta
                today = date.today()
                
                rdv_data = [
                    # RDV passés
                    {'patient_idx': 0, 'medecin_idx': 0, 'days_offset': -5, 'heure': '09:00', 'motif': 'Consultation générale', 'statut': 'termine'},
                    {'patient_idx': 1, 'medecin_idx': 1, 'days_offset': -3, 'heure': '14:30', 'motif': 'Contrôle cardiaque', 'statut': 'termine'},
                    
                    # RDV aujourd'hui
                    {'patient_idx': 2, 'medecin_idx': 0, 'days_offset': 0, 'heure': '10:00', 'motif': 'Consultation', 'statut': 'confirme'},
                    {'patient_idx': 3, 'medecin_idx': 2, 'days_offset': 0, 'heure': '15:00', 'motif': 'Problème de peau', 'statut': 'confirme'},
                    
                    # RDV futurs
                    {'patient_idx': 4, 'medecin_idx': 3, 'days_offset': 2, 'heure': '11:00', 'motif': 'Consultation pédiatrie', 'statut': 'planifie'},
                    {'patient_idx': 0, 'medecin_idx': 1, 'days_offset': 5, 'heure': '16:30', 'motif': 'Suivi cardiaque', 'statut': 'planifie'},
                    {'patient_idx': 1, 'medecin_idx': 0, 'days_offset': 7, 'heure': '09:30', 'motif': 'Renouvellement ordonnance', 'statut': 'planifie'},
                ]
                
                for rdv_info in rdv_data:
                    rdv_date = today + timedelta(days=rdv_info['days_offset'])
                    rdv_heure = datetime.strptime(rdv_info['heure'], '%H:%M').time()
                    
                    rdv = RendezVous(
                        patient_id=patients[rdv_info['patient_idx']].id,
                        medecin_id=medecins[rdv_info['medecin_idx']].id,
                        date=rdv_date,
                        heure=rdv_heure,
                        motif=rdv_info['motif'],
                        statut=rdv_info['statut']
                    )
                    db.session.add(rdv)
                
                db.session.commit()
        
        print("✅ Base de données initialisée avec succès!")
        print("\n📧 COMPTES DE TEST:")
        print("─" * 50)
        print("👩‍💼 SECRÉTAIRES:")
        print("   Email: secretaire1@cabinet.ma")
        print("   Mot de passe: secret123")
        print("\n👨‍⚕️ MÉDECINS:")
        print("   Email: dr.alami@cabinet.ma")
        print("   Mot de passe: password123")
        print("\n👤 PATIENTS:")
        print("   Email: mohamed.alaoui@gmail.com")
        print("   Mot de passe: patient123")
        print("─" * 50)
# ============================================
# CALENDRIER VISUEL
# ============================================

@app.route('/calendrier')
@login_required
def calendrier():
    """Page calendrier - accessible aux médecins et secrétaires"""
    if current_user.role == 'patient':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('index'))
    
    # Récupérer tous les rendez-vous selon le rôle
    if current_user.role == 'medecin':
        medecin = Medecin.query.filter_by(user_id=current_user.id).first()
        rdvs = RendezVous.query.filter_by(medecin_id=medecin.id).all()
        titre = f"Planning - Dr. {current_user.nom}"
    else:  # secrétaire
        rdvs = RendezVous.query.all()
        titre = "Planning général du cabinet"
    
    # Convertir les RDV en format JSON pour FullCalendar
    events = []
    for rdv in rdvs:
        # Définir la couleur selon le statut
        if rdv.statut == 'planifie':
            color = '#3b82f6'  # Bleu
        elif rdv.statut == 'confirme':
            color = '#10b981'  # Vert
        elif rdv.statut == 'termine':
            color = '#6b7280'  # Gris
        else:  # annulé
            color = '#ef4444'  # Rouge
        
        # Créer l'événement
        event = {
            'id': rdv.id,
            'title': f"{rdv.patient.user.prenom} {rdv.patient.user.nom}",
            'start': f"{rdv.date.strftime('%Y-%m-%d')}T{rdv.heure.strftime('%H:%M')}",
            'backgroundColor': color,
            'borderColor': color,
            'extendedProps': {
                'patient': f"{rdv.patient.user.prenom} {rdv.patient.user.nom}",
                'medecin': f"Dr. {rdv.medecin.user.prenom} {rdv.medecin.user.nom}",
                'telephone': rdv.patient.telephone,
                'email': rdv.patient.user.email,
                'motif': rdv.motif,
                'statut': rdv.statut
            }
        }
        events.append(event)
    
    return render_template('calendrier.html', events=events, titre=titre)

# ============================================
# STATISTIQUES ET GRAPHIQUES
# ============================================

@app.route('/statistiques')
@login_required
def statistiques():
    """Page statistiques - accessible aux médecins et secrétaires"""
    if current_user.role == 'patient':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('index'))
    
    from datetime import datetime, timedelta
    from collections import Counter
    
    # Données selon le rôle
    if current_user.role == 'medecin':
        medecin = Medecin.query.filter_by(user_id=current_user.id).first()
        tous_rdvs = RendezVous.query.filter_by(medecin_id=medecin.id).all()
        titre = f"Statistiques - Dr. {current_user.nom}"
    else:  # secrétaire
        tous_rdvs = RendezVous.query.all()
        titre = "Statistiques du cabinet"
    
    # Statistiques globales
    total_rdv = len(tous_rdvs)
    rdv_planifies = len([r for r in tous_rdvs if r.statut == 'planifie'])
    rdv_confirmes = len([r for r in tous_rdvs if r.statut == 'confirme'])
    rdv_termines = len([r for r in tous_rdvs if r.statut == 'termine'])
    rdv_annules = len([r for r in tous_rdvs if r.statut == 'annule'])
    
    # Statistiques par mois (6 derniers mois)
    today = datetime.now()
    mois_labels = []
    mois_data = []
    
    for i in range(5, -1, -1):
        mois = today - timedelta(days=30*i)
        mois_labels.append(mois.strftime('%B %Y'))
        count = len([r for r in tous_rdvs if r.date.year == mois.year and r.date.month == mois.month])
        mois_data.append(count)
    
    # Statistiques par statut (pour graphique circulaire)
    statut_labels = ['Planifiés', 'Confirmés', 'Terminés', 'Annulés']
    statut_data = [rdv_planifies, rdv_confirmes, rdv_termines, rdv_annules]
    statut_colors = ['#3b82f6', '#10b981', '#6b7280', '#ef4444']
    
    # Statistiques par médecin (pour secrétaires)
    if current_user.role == 'secretaire':
        medecins = Medecin.query.all()
        medecin_labels = [f"Dr. {m.user.nom}" for m in medecins]
        medecin_data = [len([r for r in tous_rdvs if r.medecin_id == m.id]) for m in medecins]
    else:
        medecin_labels = []
        medecin_data = []
    
    # Top 5 patients (plus de RDV)
    if tous_rdvs:
        patient_counts = Counter([r.patient_id for r in tous_rdvs])
        top_patients = patient_counts.most_common(5)
        top_patients_data = []
        for patient_id, count in top_patients:
            patient = Patient.query.get(patient_id)
            if patient:
                top_patients_data.append({
                    'nom': f"{patient.user.prenom} {patient.user.nom}",
                    'count': count
                })
    else:
        top_patients_data = []
    
    # Taux de présence (terminés vs annulés)
    if rdv_termines + rdv_annules > 0:
        taux_presence = round((rdv_termines / (rdv_termines + rdv_annules)) * 100, 1)
    else:
        taux_presence = 0
    
    return render_template('statistiques.html',
                         titre=titre,
                         total_rdv=total_rdv,
                         rdv_planifies=rdv_planifies,
                         rdv_confirmes=rdv_confirmes,
                         rdv_termines=rdv_termines,
                         rdv_annules=rdv_annules,
                         mois_labels=mois_labels,
                         mois_data=mois_data,
                         statut_labels=statut_labels,
                         statut_data=statut_data,
                         statut_colors=statut_colors,
                         medecin_labels=medecin_labels,
                         medecin_data=medecin_data,
                         top_patients_data=top_patients_data,
                         taux_presence=taux_presence)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
