from allauth.account.forms import SignupForm, LoginForm, ResetPasswordForm, ResetPasswordKeyForm
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomSignupForm(SignupForm):
    """Custom signup form with username, email, and additional fields."""
    first_name = forms.CharField(
        max_length=30,
        label='First Name',
        widget=forms.TextInput(attrs={'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=30,
        label='Last Name',
        widget=forms.TextInput(attrs={'placeholder': 'Last name'})
    )
    phone_number = forms.CharField(
        max_length=30,
        label='Phone Number',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Phone number'})
    )
    terms_accepted = forms.BooleanField(
        required=True,
        label='I agree to the Terms of Service and Privacy Policy'
    )

    def save(self, request):
        """Save the user with additional fields."""
        user = super(CustomSignupForm, self).save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.save()
        return user


class CustomLoginForm(LoginForm):
    """Custom login form with better styling."""

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )

    remember = forms.BooleanField(
        label="Remember Me",
        required=False,
        widget=forms.CheckboxInput()
    )

    def __init__(self, *args, **kwargs):
        super(CustomLoginForm, self).__init__(*args, **kwargs)
        self.fields['login'].widget = forms.EmailInput(attrs={'placeholder': 'Email address'})
        self.fields['login'].label = "Email"


class CustomResetPasswordForm(ResetPasswordForm):
    """Custom password reset form."""

    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Email address',
            'class': 'form-control',
        })
    )


class CustomResetPasswordKeyForm(ResetPasswordKeyForm):
    """Custom form for setting a new password."""

    password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'New password',
            'class': 'form-control',
        })
    )

    password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm new password',
            'class': 'form-control',
        })
    )
