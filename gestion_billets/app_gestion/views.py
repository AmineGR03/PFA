from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from .models import Match, Reservation, Billet
from .forms import CustomUserCreationForm, MatchForm,ReservationForm, UserProfileForm
from django.contrib import messages
from decimal import Decimal
import stripe
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django import forms
from .models import Billet
from django.template.loader import render_to_string
from django.http import HttpResponse
from xhtml2pdf import pisa
import io




# --- Auth Views ---

from .forms import CustomAuthenticationForm

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = CustomAuthenticationForm


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

# --- Home ---

def home(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('/admin/')
        elif hasattr(request.user, 'role'):
            if request.user.role == 'organisateur':
                return redirect('organizer_dashboard')
            elif request.user.role == 'spectateur':
                return redirect('user_dashboard')

    # Pour les visiteurs non connectés ou après redirection
    now = timezone.now().date()
    prochains_matchs = Match.objects.filter(date__gte=now).order_by('date', 'heure')[:5]  # les 5 prochains
    return render(request, 'home.html', {'prochains_matchs': prochains_matchs})

# --- Matchs ---

def liste_matchs(request):
    query = request.GET.get('q', '')  

    if query:
        matchs = Match.objects.filter(
            Q(equipe1__nom__icontains=query) | Q(equipe2__nom__icontains=query)
        ).order_by('date')
    else:
        matchs = Match.objects.all().order_by('date')

    return render(request, 'matchs/list.html', {'matchs': matchs})


@login_required
def detail_match(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    # Vérifie si l'utilisateur est organisateur et s'il organise ce match
    is_organisateur = (
        hasattr(request.user, 'role') and 
        request.user.role == 'organisateur' and 
        match.organisateur == request.user
    )

    return render(request, 'matchs/detail.html', {
        'match': match,
        'is_organisateur': is_organisateur,
    })

# --- Réservations ---

@login_required
def confirmer_reservation(request, match_id):
    match = get_object_or_404(Match, pk=match_id)

    if request.method == 'POST':
        categorie = request.POST.get('categorie')
        nb_billets_str = request.POST.get('nb_billets')

        if not nb_billets_str:
            messages.error(request, "Veuillez indiquer le nombre de billets.")
            return render(request, 'reservations/confirm.html', {'match': match})

        try:
            nb_billets = int(nb_billets_str)
            if nb_billets <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, "Le nombre de billets doit être un entier positif.")
            return render(request, 'reservations/confirm.html', {'match': match})

        # **Nouvelle vérification des places disponibles**
        if nb_billets > match.nb_places_dispo:
            messages.error(request, f"Désolé, il ne reste que {match.nb_places_dispo} places disponibles pour ce match.")
            return render(request, 'reservations/confirm.html', {'match': match})

        # Calcul du montant selon la catégorie
        prix = match.prix_vip if categorie == 'VIP' else match.prix_standard
        montant = nb_billets * prix

        # Créer la réservation en attente (sans modifier nb_places_dispo)
        reservation = Reservation.objects.create(
            statut='en_attente',
            nb_billets=nb_billets,
            categorie=categorie,
            montant=montant,
            spectateur=request.user,
            match=match,
        )

        # Créer les billets associés non payés
        for _ in range(nb_billets):
            Billet.objects.create(
                statut='non_payé',
                chemin_pdf='',
                reservation=reservation
            )

        # Rediriger vers le paiement Stripe
        return redirect('paiement', reservation_id=reservation.id)

    return render(request, 'reservations/confirm.html', {'match': match})


@login_required

def historique_reservations(request):
    reservations = Reservation.objects.filter(spectateur=request.user)
    return render(request, 'reservations/history.html', {'reservations': reservations})



# --- Dashboards ---

@login_required
def user_dashboard(request):
    reservations_payees = Reservation.objects.filter(spectateur=request.user, statut='confirmée')  # ou 'payée' selon ton champ
    return render(request, 'dashboard/user_dashboard.html', {'reservations_payees': reservations_payees})


@login_required
def organizer_dashboard(request):
    matchs = Match.objects.filter(organisateur=request.user)
    return render(request, 'dashboard/organizer_dashboard.html', {'matchs': matchs})

@login_required
def ajouter_match(request):
    if request.method == 'POST':
        form = MatchForm(request.POST)
        if form.is_valid():
            match = form.save(commit=False)
            match.organisateur = request.user
            match.save()
            return redirect('organizer_dashboard')
    else:
        form = MatchForm()
    return render(request, 'matchs/ajouter.html', {'form': form})

@login_required
def voir_reservations(request):
    matchs = Match.objects.filter(organisateur=request.user)
    reservations = Reservation.objects.filter(match__in=matchs)
    return render(request, 'dashboard/voir_reservations.html', {'reservations': reservations})

@login_required
def mes_matchs(request):
    matchs = Match.objects.filter(organisateur=request.user)
    return render(request, 'matchs/mes_matchs.html', {'matchs': matchs})

# --- Paiement Stripe ---

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def paiement_stripe(request, reservation_id):
    reservation = get_object_or_404(Reservation, pk=reservation_id, spectateur=request.user)

    if request.method == 'POST':
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'mad',
                    'product_data': {
                        'name': f"Réservation match {reservation.match}",
                    },
                    'unit_amount': int(reservation.montant * 100),  # montant en centimes
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri('/paiement/success/') + f"?reservation_id={reservation.id}",
            cancel_url=request.build_absolute_uri('/paiement/cancel/'),
        )
        return redirect(session.url, code=303)

    return render(request, 'paiement/checkout.html', {'reservation': reservation, 'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY})

@login_required
def paiement_success(request):
    reservation_id = request.GET.get('reservation_id')
    reservation = get_object_or_404(Reservation, id=reservation_id, spectateur=request.user)

    # Mettre à jour la réservation et les billets après paiement réussi
    reservation.statut = 'confirmée'
    reservation.save()

    billets = Billet.objects.filter(reservation=reservation)
    billets.update(statut='payé')

    # Décrémenter les places disponibles du match
    match = reservation.match
    match.nb_places_dispo -= reservation.nb_billets
    match.save()

    return render(request, "paiement/success.html", {'reservation': reservation})


@login_required
def paiement_cancel(request):
    return render(request, "paiement/cancel.html")


def reservation_detail(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    return render(request, 'reservations/reservation_detail.html', {'reservation': reservation})



def reservation_payer(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    # Créer une session Stripe Checkout
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',  # adapte la monnaie si besoin
                'product_data': {
                    'name': f'Réservation #{reservation.id}',
                },
                'unit_amount': int(reservation.montant * 100),  # montant en cents
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri('/paiement-success/'),
        cancel_url=request.build_absolute_uri(f'/reservation/{reservation.id}/'),
    )
    return redirect(session.url)

@login_required
def reservation_modifier(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, spectateur=request.user)

    # Empêche la modification si déjà payée
    if reservation.statut == 'payée':
        messages.error(request, "Impossible de modifier une réservation déjà payée.")
        return redirect('reservation_detail', reservation_id=reservation.id)

    if request.method == 'POST':
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            messages.success(request, "Réservation mise à jour avec succès.")
            return redirect('reservation_detail', reservation_id=reservation.id)
    else:
        form = ReservationForm(instance=reservation)

    return render(request, 'reservations/modifier.html', {
        'form': form,
        'reservation': reservation
    })
@login_required
def reservation_supprimer(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, spectateur=request.user)

    if request.method == 'POST':
        if reservation.statut == 'confirmée':
            messages.error(request, "Vous ne pouvez pas supprimer une réservation déjà confirmée/payée.")
            return redirect('reservation_detail', reservation_id=reservation.id)

        reservation.delete()
        messages.success(request, "Réservation supprimée avec succès.")
        return redirect('historique_reservations')

    # Si GET, on peut soit rediriger, soit afficher une confirmation (optionnel)
    return redirect('reservation_detail', reservation_id=reservation.id)


def modifier_match(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    if request.method == 'POST':
        form = MatchForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
            
            return redirect('detail_match', match_id=match.id)  
    else:
        form = MatchForm(instance=match)
    return render(request, 'matchs/modifier.html', {'form': form, 'match': match})


@login_required
def supprimer_match(request, match_id):
    match = get_object_or_404(Match, id=match_id)

    if request.method == 'POST':
        match.delete()
        return redirect('liste_matchs') 


    return redirect('detail_match', match_id=match.id)

@login_required
def billet_pdf(request, billet_id):
    billet = get_object_or_404(Billet, id=billet_id)
    reservation = billet.reservation

    if reservation.spectateur != request.user:
        return HttpResponse("Accès non autorisé", status=403)

    html = render_to_string('reservations/ticket_pdf.html', {'billet': billet, 'reservation': reservation})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="billet_{billet.id}.pdf"'

    pisa_status = pisa.CreatePDF(io.StringIO(html), dest=response)

    if pisa_status.err:
        return HttpResponse("Erreur lors de la génération du PDF", status=500)
    return response


from django.contrib.auth import update_session_auth_hash

@login_required
def profil(request):
    user = request.user

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            new_password = form.cleaned_data.get('password1')
            if new_password:
                user.set_password(new_password)
            user.save()
            # Pour éviter la déconnexion immédiate après changement mdp
            if new_password:
                update_session_auth_hash(request, user)
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('profil')
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'profil.html', {'form': form})
