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
