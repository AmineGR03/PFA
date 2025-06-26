from django.contrib import admin
from .models import CustomUser, Equipe, Membre, Match, Reservation, Billet, Paiement

admin.site.register(CustomUser)
admin.site.register(Equipe)
admin.site.register(Membre)
admin.site.register(Match)
admin.site.register(Reservation)
admin.site.register(Billet)
admin.site.register(Paiement)
