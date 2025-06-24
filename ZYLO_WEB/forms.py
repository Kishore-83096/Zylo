from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MaxLengthValidator
from ZYLO_WEB.models import UserProfilepictures, ContactInformation, SavedAddress, SavedCard
from datetime import date


class registrationform(UserCreationForm):
    first_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'border border-gray-300 rounded-md p-2 w-full'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'border border-gray-300 rounded-md p-2 w-full'})
    )
    username = forms.CharField(
        max_length=150,  # Django default
        required=True,
        widget=forms.TextInput(attrs={'class': 'border border-gray-300 rounded-md p-2 w-full'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'border border-gray-300 rounded-md p-2 w-full'})
    )
    password1 = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'border border-gray-300 rounded-md p-2 w-full'}),
        validators=[MinLengthValidator(8), MaxLengthValidator(15)]
    )
    password2 = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'border border-gray-300 rounded-md p-2 w-full'}),
        validators=[MinLengthValidator(8), MaxLengthValidator(15)]
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email


class adminLoginForm(forms.Form):
    Email = forms.CharField(
        label="Email",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
            'placeholder': 'Enter your email'
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
            'placeholder': '********'
        })
    )


class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username'] # Add other fields you want to allow editing

class UserProfilepicturesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add the 'form-control' class to the image field's widget
        self.fields['image'].widget.attrs.update({'class': 'form-control'})
    class Meta:
        model = UserProfilepictures
        fields = ['image'] # We only want the user to modify the image here


class ContactInformationForm(forms.ModelForm):
    class Meta:
        model = ContactInformation
        fields = ['email', 'phone_number', 'location']
        widgets = {
            'email': forms.EmailInput(
                attrs={
                    'class': 'input-text w-full border border-gray-300 p-2 rounded-md focus:ring-blue-500 focus:border-blue-500',
                    'placeholder': 'Enter your email',
                    'autocomplete': 'email',
                }
            ),
            'phone_number': forms.TextInput(
                attrs={
                    'class': 'input-text w-full border border-gray-300 p-2 rounded-md focus:ring-blue-500 focus:border-blue-500',
                    'placeholder': 'Enter your phone number (optional)', # Added optional hint
                    'autocomplete': 'tel',
                    'maxlength': 20,
                }
            ),
            'location': forms.TextInput(
                attrs={
                    'class': 'input-text w-full border border-gray-300 p-2 rounded-md focus:ring-blue-500 focus:border-blue-500',
                    'placeholder': 'Enter your location (optional)', # Added optional hint
                    'autocomplete': 'street-address',
                    'maxlength': 255,
                }
            ),
        }
        labels = {
            'email': 'Email',
            'phone_number': 'Phone Number',
            'location': 'Location',
        }

    # Optional: Add custom validation if needed, e.g., for phone number format
    # def clean_phone_number(self):
    #     phone_number = self.cleaned_data.get('phone_number')
    #     if phone_number and not phone_number.replace(' ', '').replace('-', '').isdigit():
    #         raise forms.ValidationError("Phone number must contain only digits.")
    #     return phone_number

class SavedAddressForm(forms.ModelForm):
    class Meta:
        model = SavedAddress
        # Exclude 'user' as it will be set in the view
        fields = ['address_type', 'street_address', 'city', 'state', 'zip_code', 'country','phone_number']
        widgets = {
            'address_type': forms.Select(
                attrs={
                    'class': 'input-select w-full border border-gray-300 p-2 rounded-md focus:ring-blue-500 focus:border-blue-500',
                }
            ),
            'street_address': forms.TextInput(
                attrs={
                    'class': 'input-text w-full border border-gray-300 p-2 rounded-md focus:ring-blue-500 focus:border-blue-500',
                    'placeholder': 'Street Address',
                    'autocomplete': 'street-address',
                }
            ),
            'city': forms.TextInput(
                attrs={
                    'class': 'input-text w-full border border-gray-300 p-2 rounded-md focus:ring-blue-500 focus:border-blue-500',
                    'placeholder': 'City',
                    'autocomplete': 'address-level2',
                }
            ),
            'state': forms.TextInput(
                attrs={
                    'class': 'input-text w-full border border-gray-300 p-2 rounded-md focus:ring-blue-500 focus:border-blue-500',
                    'placeholder': 'State (optional)',
                    'autocomplete': 'address-level1',
                }
            ),
            'zip_code': forms.TextInput(
                attrs={
                    'class': 'input-text w-full border border-gray-300 p-2 rounded-md focus:ring-blue-500 focus:border-blue-500',
                    'placeholder': 'Zip Code (optional)',
                    'autocomplete': 'postal-code',
                    'maxlength': 10,
                }
            ),
            'country': forms.TextInput(
                attrs={
                    'class': 'input-text w-full border border-gray-300 p-2 rounded-md focus:ring-blue-500 focus:border-blue-500',
                    'placeholder': 'Country',
                    'autocomplete': 'country-name',
                }
            ),
            'phone_number': forms.TextInput(
                attrs={
                    'class': 'input-text w-full border border-gray-300 p-2 rounded-md focus:ring-blue-500 focus:border-blue-500',
                    'placeholder': 'Phone Number',
                    'autocomplete': 'Phone Number',
                }
            ),
        }
        labels = {
            'address_type': 'Address Type',
            'street_address': 'Street Address',
            'city': 'City',
            'state': 'State/Province',
            'zip_code': 'Zip/Postal Code',
            'country': 'Country',
            'phone_number':'Phone Number'
        }


# your_app_name/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import UserProfilepictures, ContactInformation, SavedAddress, SavedCard
from datetime import date

# Your existing forms will be here...

# ... (UserProfileEditForm, UserProfilepicturesForm, ContactInformationForm, SavedAddressForm) ...


class SavedCardForm(forms.ModelForm):
    # Dynamically generate choices for expiration year
    # Start from current year, go up to 10 years in the future
    current_year = date.today().year
    EXPIRATION_YEAR_CHOICES = [(y, str(y)) for y in range(current_year, current_year + 11)]

    expiration_year = forms.ChoiceField(
        choices=EXPIRATION_YEAR_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'input-select w-full border border-gray-300 p-2 rounded-md focus:ring-blue-500 focus:border-blue-500',
            }
        )
    )

    class Meta:
        model = SavedCard
        # Exclude 'user' as it will be set in the view
        fields = ['card_nickname', 'last_four_digits', 'expiration_month', 'expiration_year', 'card_brand', 'is_default']
        widgets = {
            'card_nickname': forms.TextInput(
                attrs={
                    'class': 'input-text w-full border border-gray-300 p-2 rounded-md focus:ring-blue-500 focus:border-blue-500',
                    'placeholder': 'e.g., My Visa, Work Card',
                    'maxlength': 50,
                }
            ),
            'last_four_digits': forms.TextInput(
                attrs={
                    'class': 'input-text w-full border border-gray-300 p-2 rounded-md focus:ring-blue-500 focus:border-blue-500',
                    'placeholder': 'Last 4 digits',
                    'maxlength': 4,
                    'pattern': '[0-9]{4}', # HTML5 validation for 4 digits
                    'title': 'Please enter exactly 4 digits.',
                }
            ),
            'expiration_month': forms.Select(
                choices=[(i, str(i).zfill(2)) for i in range(1, 13)], # Ensure choices are integers as values
                attrs={
                    'class': 'input-select w-full border border-gray-300 p-2 rounded-md focus:ring-blue-500 focus:border-blue-500',
                }
            ),
            'card_brand': forms.Select(
                attrs={
                    'class': 'input-select w-full border border-gray-300 p-2 rounded-md focus:ring-blue-500 focus:border-blue-500',
                }
            ),
            'is_default': forms.CheckboxInput(
                attrs={
                    'class': 'ml-2 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
                }
            ),
        }
        labels = {
            'card_nickname': 'Card Nickname',
            'last_four_digits': 'Last 4 Digits',
            'expiration_month': 'Expiration Month',
            'expiration_year': 'Expiration Year',
            'card_brand': 'Card Brand',
            'is_default': 'Set as Default Card',
        }

    # Custom validation for expiration date
    def clean(self):
        cleaned_data = super().clean()
        expiration_month = cleaned_data.get('expiration_month')
        expiration_year = cleaned_data.get('expiration_year')

        if expiration_month is not None and expiration_year is not None:
            try:
                # Explicitly convert to integers before comparison
                # This is the crucial change!
                expiration_month = int(expiration_month)
                expiration_year = int(expiration_year)
            except ValueError:
                # This should ideally be caught by field-level validation,
                # but good for robustness if invalid non-numeric data slips through.
                raise forms.ValidationError("Invalid expiration month or year format.")

            today = date.today()
            # Check if year is in the past
            if expiration_year < today.year:
                raise forms.ValidationError("Expiration year cannot be in the past.")
            # Check if month/year combination is in the past for the current year
            elif expiration_year == today.year and expiration_month < today.month:
                raise forms.ValidationError("Expiration month cannot be in the past for the current year.")
        return cleaned_data