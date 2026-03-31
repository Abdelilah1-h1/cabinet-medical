{% extends "base.html" %}

{% block title %}Liste des Patients - Cabinet Médical{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h2 class="mb-4">
            <i class="bi bi-people"></i> Liste des Patients
        </h2>
    </div>
</div>

<div class="row mb-3">
    <div class="col-12">
        <a href="{{ url_for('secretaire_dashboard') }}" class="btn btn-secondary">
            <i class="bi bi-arrow-left"></i> Retour au dashboard
        </a>
    </div>
</div>

<div class="row">
    <div class="col-12">
        <div class="card shadow">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">
                    <i class="bi bi-people-fill"></i> Tous les patients ({{ patients|length }})
                </h5>
            </div>
            <div class="card-body">
                {% if patients %}
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Nom Complet</th>
                                    <th>Email</th>
                                    <th>Téléphone</th>
                                    <th>Date de naissance</th>
                                    <th>Nb RDV</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for patient in patients %}
                                <tr>
                                    <td>
                                        <strong>{{ patient.user.nom }} {{ patient.user.prenom }}</strong>
                                    </td>
                                    <td>
                                        <i class="bi bi-envelope"></i> {{ patient.user.email }}
                                    </td>
                                    <td>
                                        {% if patient.telephone %}
                                            <i class="bi bi-telephone"></i> {{ patient.telephone }}
                                        {% else %}
                                            <span class="text-muted">Non renseigné</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if patient.date_naissance %}
                                            {{ patient.date_naissance.strftime('%d/%m/%Y') }}
                                        {% else %}
                                            <span class="text-muted">-</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <span class="badge bg-info">{{ patient.rendez_vous|length }} RDV</span>
                                    </td>
                                    <td>
                                        <a href="{{ url_for('secretaire_creer_rdv') }}" class="btn btn-sm btn-success">
                                            <i class="bi bi-calendar-plus"></i> Créer RDV
                                        </a>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                {% else %}
                    <div class="text-center py-5">
                        <i class="bi bi-people display-1 text-muted"></i>
                        <p class="lead mt-3">Aucun patient enregistré</p>
                    </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}