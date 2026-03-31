{% extends "base.html" %}

{% block title %}Dashboard Secrétaire - Cabinet Médical{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h2 class="mb-4">
            <i class="bi bi-clipboard2-pulse"></i> 
            Dashboard Secrétaire - Bonjour {{ current_user.prenom }}
        </h2>
    </div>
</div>

<!-- Statistiques -->
<div class="row mb-4">
    <div class="col-md-3 mb-3">
        <div class="card stat-card">
            <div class="card-body text-center">
                <i class="bi bi-people display-4 text-primary"></i>
                <h3 class="mt-3">{{ total_patients }}</h3>
                <p class="text-muted mb-0">Patients</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-3">
        <div class="card stat-card success">
            <div class="card-body text-center">
                <i class="bi bi-person-badge display-4 text-success"></i>
                <h3 class="mt-3">{{ total_medecins }}</h3>
                <p class="text-muted mb-0">Médecins</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-3">
        <div class="card stat-card warning">
            <div class="card-body text-center">
                <i class="bi bi-clock-history display-4 text-warning"></i>
                <h3 class="mt-3">{{ rdv_en_attente }}</h3>
                <p class="text-muted mb-0">RDV en attente</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-3">
        <a href="{{ url_for('secretaire_creer_rdv') }}" class="text-decoration-none">
            <div class="card stat-card info hover-card">
                <div class="card-body text-center">
                    <i class="bi bi-calendar-plus display-4 text-info"></i>
                    <h5 class="mt-3">Nouveau RDV</h5>
                    <p class="text-muted mb-0">Créer</p>
                </div>
            </div>
        </a>
    </div>
</div>

<!-- Actions rapides -->
<div class="row mb-4">
    <div class="col-12">
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0"><i class="bi bi-lightning-charge"></i> Actions rapides</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-4 mb-2">
                        <a href="{{ url_for('secretaire_creer_rdv') }}" class="btn btn-primary w-100">
                            <i class="bi bi-calendar-plus"></i> Créer un rendez-vous
                        </a>
                    </div>
                    <div class="col-md-4 mb-2">
                        <a href="{{ url_for('secretaire_patients') }}" class="btn btn-success w-100">
                            <i class="bi bi-people"></i> Voir les patients
                        </a>
                    </div>
                    <div class="col-md-4 mb-2">
                        <a href="{{ url_for('index') }}" class="btn btn-info w-100">
                            <i class="bi bi-calendar3"></i> Planning global
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Rendez-vous du jour -->
<div class="row mb-4">
    <div class="col-12">
        <div class="card shadow">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">
                    <i class="bi bi-calendar-day"></i> Rendez-vous d'aujourd'hui ({{ rdv_aujourd_hui|length }})
                </h5>
            </div>
            <div class="card-body">
                {% if rdv_aujourd_hui %}
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Heure</th>
                                    <th>Patient</th>
                                    <th>Médecin</th>
                                    <th>Motif</th>
                                    <th>Statut</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for rdv in rdv_aujourd_hui %}
                                <tr>
                                    <td><strong>{{ rdv.heure.strftime('%H:%M') }}</strong></td>
                                    <td>
                                        {{ rdv.patient.user.nom }} {{ rdv.patient.user.prenom }}
                                        <br>
                                        <small class="text-muted">
                                            <i class="bi bi-telephone"></i> {{ rdv.patient.telephone or 'N/A' }}
                                        </small>
                                    </td>
                                    <td>Dr. {{ rdv.medecin.user.nom }}</td>
                                    <td>{{ rdv.motif or '-' }}</td>
                                    <td>
                                        {% if rdv.statut == 'planifie' %}
                                            <span class="badge bg-info"><i class="bi bi-clock"></i> Planifié</span>
                                        {% elif rdv.statut == 'confirme' %}
                                            <span class="badge bg-success"><i class="bi bi-check-circle"></i> Confirmé</span>
                                        {% elif rdv.statut == 'termine' %}
                                            <span class="badge bg-secondary"><i class="bi bi-check-all"></i> Terminé</span>
                                        {% elif rdv.statut == 'annule' %}
                                            <span class="badge bg-danger"><i class="bi bi-x-circle"></i> Annulé</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <a href="{{ url_for('secretaire_modifier_rdv', rdv_id=rdv.id) }}" class="btn btn-sm btn-primary">
                                            <i class="bi bi-pencil"></i>
                                        </a>
                                        <form method="POST" action="{{ url_for('secretaire_annuler_rdv', rdv_id=rdv.id) }}" style="display: inline;">
                                            <button type="submit" class="btn btn-sm btn-danger" onclick="return confirm('Annuler ce rendez-vous ?')">
                                                <i class="bi bi-x-circle"></i>
                                            </button>
                                        </form>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                {% else %}
                    <div class="text-center py-4">
                        <i class="bi bi-calendar-x display-1 text-muted"></i>
                        <p class="lead mt-3">Aucun rendez-vous prévu aujourd'hui</p>
                    </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>

<!-- Tous les rendez-vous récents -->
<div class="row">
    <div class="col-12">
        <div class="card shadow">
            <div class="card-header bg-secondary text-white">
                <h5 class="mb-0">
                    <i class="bi bi-calendar3"></i> Rendez-vous récents (50 derniers)
                </h5>
            </div>
            <div class="card-body">
                {% if tous_rdv %}
                    <div class="table-responsive">
                        <table class="table table-hover table-sm">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Heure</th>
                                    <th>Patient</th>
                                    <th>Médecin</th>
                                    <th>Statut</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for rdv in tous_rdv %}
                                <tr>
                                    <td>{{ rdv.date.strftime('%d/%m/%Y') }}</td>
                                    <td>{{ rdv.heure.strftime('%H:%M') }}</td>
                                    <td>{{ rdv.patient.user.nom }} {{ rdv.patient.user.prenom }}</td>
                                    <td>Dr. {{ rdv.medecin.user.nom }}</td>
                                    <td>
                                        {% if rdv.statut == 'planifie' %}
                                            <span class="badge bg-info">Planifié</span>
                                        {% elif rdv.statut == 'confirme' %}
                                            <span class="badge bg-success">Confirmé</span>
                                        {% elif rdv.statut == 'termine' %}
                                            <span class="badge bg-secondary">Terminé</span>
                                        {% elif rdv.statut == 'annule' %}
                                            <span class="badge bg-danger">Annulé</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <a href="{{ url_for('secretaire_modifier_rdv', rdv_id=rdv.id) }}" class="btn btn-sm btn-outline-primary">
                                            <i class="bi bi-pencil"></i>
                                        </a>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                {% else %}
                    <div class="text-center py-4">
                        <i class="bi bi-calendar-x display-1 text-muted"></i>
                        <p class="lead mt-3">Aucun rendez-vous enregistré</p>
                    </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}