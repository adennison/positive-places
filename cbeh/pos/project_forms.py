from django import forms
from django.forms import ModelForm, TextInput
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

from pos.models import *

class ProjectForm(ModelForm):
    def clean(self):
        cleaned_data = super(ProjectForm, self).clean()
        return cleaned_data

    class Meta:
        model = Project
        fields = (  # Only show these fields & in this order when generating the form
            'project_name',
        )
