from django.db import models
from django.contrib.auth.models import AbstractUser

# -------------------------
# Utilisateur personnalisé
# -------------------------
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('organisateur', 'Organisateur'),
        ('spectateur', 'Spectateur'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} ({self.role})"

# -------------------------
# Équipe
# -------------------------
class Equipe(models.Model):
    nom = models.CharField(max_length=100)
    pays = models.CharField(max_length=100)

    def __str__(self):
        return self.nom

# -------------------------
# Membre d'équipe
# -------------------------
class Membre(models.Model):
    nom_prenom = models.CharField(max_length=100)
    numero = models.IntegerField()
    nationalite = models.CharField(max_length=100)
    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nom_prenom} - #{self.numero}"

# -------------------------
# Match
# -------------------------
class Match(models.Model):
    equipe1 = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name='equipe1_matchs')
    equipe2 = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name='equipe2_matchs')
    date = models.DateField()
    heure = models.TimeField()
    lieu = models.CharField(max_length=100)
    prix_vip = models.DecimalField(max_digits=8, decimal_places=2)
    prix_standard = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField()
    nb_places_dispo = models.IntegerField()
    organisateur = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'organisateur'})

    def __str__(self):
        return f"{self.equipe1.nom} vs {self.equipe2.nom} - {self.date}"

# -------------------------
# Réservation
# -------------------------
class Reservation(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirmée', 'Confirmée'),
        ('annulée', 'Annulée'),
    ]
    date_reservation = models.DateField(auto_now_add=True)
    heure = models.TimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES)
    nb_billets = models.IntegerField()
    categorie = models.CharField(max_length=20, choices=[('VIP', 'VIP'), ('Standard', 'Standard')])
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    spectateur = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'spectateur'})
    match = models.ForeignKey(Match, on_delete=models.CASCADE)

    def __str__(self):
        return f"Réservation de {self.spectateur.username} - {self.match}"

# -------------------------
# Billet
# -------------------------
class Billet(models.Model):
    STATUT_CHOICES = [
        ('payé', 'Payé'),
        ('non_payé', 'Non payé'),
    ]
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='non_payé')
    chemin_pdf = models.CharField(max_length=255, blank=True)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)

    def __str__(self):
        return f"Billet #{self.id} - {self.statut}"

# -------------------------
# Paiement
# -------------------------
class Paiement(models.Model):
    STATUT_CHOICES = [
        ('effectué', 'Effectué'),
        ('échoué', 'Échoué'),
        ('en_attente', 'En attente'),
    ]
    MODE_CHOICES = [
        ('carte', 'Carte bancaire'),
        ('paypal', 'PayPal'),
        ('espece', 'Espèce'),
    ]

    date_paiement = models.DateField(auto_now_add=True)
    heure = models.TimeField(auto_now_add=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)

    def __str__(self):
        return f"Paiement {self.mode} - {self.statut} - {self.montant} DH"
