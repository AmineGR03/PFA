from django.urls import path
from .views import (
    home,
    liste_matchs,
    detail_match,
    confirmer_reservation,
    historique_reservations,
    user_dashboard,
    organizer_dashboard,
    CustomLoginView,
    CustomLogoutView,
    signup,
    ajouter_match,
    voir_reservations,
    mes_matchs,
    paiement_stripe,
    paiement_success,
    paiement_cancel,
    reservation_detail,
    reservation_modifier,
    reservation_payer,
    reservation_supprimer,
    billet_pdf,
    modifier_match,
    supprimer_match,
)

urlpatterns = [
    path('', home, name='home'),
    path('matchs/', liste_matchs, name='liste_matchs'),
    path('matchs/<int:match_id>/', detail_match, name='detail_match'),
    path('matchs/<int:match_id>/reserver/', confirmer_reservation, name='confirmer_reservation'),
    path('reservations/historique/', historique_reservations, name='historique_reservations'),
    path('dashboard/user/', user_dashboard, name='user_dashboard'),
    path('dashboard/organizer/', organizer_dashboard, name='organizer_dashboard'),
    path('dashboard/organizer/reservations/', voir_reservations, name='voir_reservations'),

    # URL modifier match
    path('matchs/<int:match_id>/modifier/', modifier_match, name='modifier_match'),
    # URL supprimer match
    path('matchs/<int:match_id>/supprimer/', supprimer_match, name='supprimer_match'),
    # Paiement Stripe - UNE SEULE ROUTE ici
    path('paiement/<int:reservation_id>/', paiement_stripe, name='paiement'), 

    path('paiement/success/', paiement_success, name='paiement_success'),
    path('paiement/cancel/', paiement_cancel, name='paiement_cancel'),
     # Détail réservation 
    path('reservation/<int:reservation_id>/', reservation_detail, name='reservation_detail'),
    path('reservations/historique/', historique_reservations, name='historique_reservations'),
    path('reservation/<int:reservation_id>/supprimer/', reservation_supprimer, name='reservation_supprimer'),

    # Payer avec Stripe
    path('reservation/<int:reservation_id>/payer/', reservation_payer, name='reservation_payer'),
    # PDF
    path('billet/<int:billet_id>/pdf/', billet_pdf, name='billet_pdf'),

    # Modifier la réservation
    path('reservation/<int:reservation_id>/modifier/', reservation_modifier, name='reservation_modifier'),
    path('matchs/ajouter/', ajouter_match, name='ajouter_match'),
    path('mes-matchs/', mes_matchs, name='mes_matchs'),

    # Auth
    path('login/', CustomLoginView.as_view(), name='login'),

    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('signup/', signup, name='signup'),
]
