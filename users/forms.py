from django import forms
from users.models import Users

class JIRAUsernameForm(forms.ModelForm):
    class Meta:
        model = Users
        fields = ['jira_username']

        widgets= {
            'jira_username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your JIRA username'
            })
        }

    def clean_jira_username(self):
        jira_username = self.cleaned_data.get('jira_username')
        # Add custom validation here (e.g., checks for uniqueness, valid characters)
        if Users.objects.filter(jira_username=jira_username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This username is already taken.")
        return jira_username