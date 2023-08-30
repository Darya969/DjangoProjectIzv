from django import forms
from .models import *
import re
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Имя пользователя',
                               widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(label='Пароль',
                               widget=forms.PasswordInput(attrs={"class": "form-control"}))


class IzveshheniyaForm(forms.ModelForm):
    class Meta:
        model = IndexForm
        fields = '__all__'
        widgets = {
            'place_of_detection': forms.Select(attrs={"class": "form-control"}),
            'mesto_obracheniya': forms.Select(attrs={"class": "form-control"}),
            'lastname': forms.TextInput(attrs={"class": "form-control"}),
            'firstname': forms.TextInput(attrs={"class": "form-control"}),
            'middle_name': forms.TextInput(attrs={"class": "form-control"}),
            'sex': forms.Select(attrs={"class": "form-control"}),
            'date_bith': forms.TextInput(attrs={"class": "form-control"}),
            'locality': forms.TextInput(attrs={"class": "form-control"}),
            'district': forms.Select(attrs={"class": "form-control"}),
            'street': forms.TextInput(attrs={"class": "form-control"}),
            'home': forms.TextInput(attrs={"class": "form-control"}),
            'body': forms.TextInput(attrs={"class": "form-control"}),
            'flat': forms.TextInput(attrs={"class": "form-control"}),
            'citizen': forms.Select(attrs={"class": "form-control"}),
            'social_group': forms.Select(attrs={"class": "form-control"}),
            'job': forms.TextInput(attrs={"class": "form-control"}),
            'post': forms.Select(attrs={"class": "form-control"}),
            'date_of_application': forms.TextInput(attrs={"class": "form-control"}),
            'category1': forms.Select(attrs={"class": "form-control"}),
            'group_of_diagnoses': forms.Select(attrs={"class": "form-control"}),
            'diagnosis': forms.Select(attrs={"class": "form-control"}),
            'mkb': forms.Select(attrs={"class": "form-control"}),
            'circumstances_of_detection': forms.Select(attrs={"class": "form-control"}),
            'date_of_establishment': forms.TextInput(attrs={"class": "form-control"}),
            'physician': forms.Select(attrs={"class": "form-control"}),
            'VRACH': forms.TextInput(attrs={"class": "form-control"}),
            'laboratory_confirmation': forms.Select(attrs={"class": "form-control"}),
            'LAB_POT_RAS': forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        places_of_detection = PlaceOfDetection.objects.filter(is_hidden=False)
        self.fields['place_of_detection'].queryset = places_of_detection
        circumstances_of_detection = CircumstancesOfDetection.objects.filter(is_published=False)
        self.fields['circumstances_of_detection'].queryset = circumstances_of_detection
        physician = Physician.objects.filter(is_hidden=False)
        self.fields['physician'].queryset = physician
        mesto_obracheniya = MestoObracheniya.objects.filter(is_hidden=False)
        self.fields['mesto_obracheniya'].queryset = mesto_obracheniya


class StockSearch(forms.ModelForm):
    start_date = forms.DateTimeField(required=False)
    end_date = forms.DateTimeField(required=False)
    class Meta:
        model = IndexForm
        fields = ['post', 'start_date', 'end_date']