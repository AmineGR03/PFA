from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from .models import Match, Reservation
from django.contrib.auth.forms import AuthenticationForm

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'role', 'first_name', 'last_name')  
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = '__all__'

        widgets = {
            'equipe1': forms.Select(attrs={'class': 'form-control'}),
            'equipe2': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'heure': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'lieu': forms.TextInput(attrs={'class': 'form-control'}),
            'prixVIP': forms.NumberInput(attrs={'class': 'form-control'}),
            'prixStandard': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nbPlacesDispo': forms.NumberInput(attrs={'class': 'form-control'}),
        }
class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['nb_billets',  'categorie']  # champs modifiables
from .models import CustomUser


class UserProfileForm(forms.ModelForm):
    password1 = forms.CharField(label="Nouveau mot de passe", required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="Confirmer le mot de passe", required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError("Les mots de passe ne correspondent pas.")
            if len(p1) < 8:
                raise forms.ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
        return cleaned_data
