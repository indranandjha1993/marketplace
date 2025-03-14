from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model for our marketplace."""

    username = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
        validators=[AbstractUser.username_validator],
        error_messages={
            'unique': 'A user with that username already exists.',
        },
    )

    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    is_vendor = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.username or self.email


class UserProfile(models.Model):
    """Extended profile for Users."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    wishlist_products = models.ManyToManyField('products.Product', blank=True, related_name='wishlisted_by')

    def __str__(self):
        return f"{self.user.email}'s Profile"


class UserAddress(models.Model):
    """User saved addresses for shipping/billing."""

    ADDRESS_TYPE_CHOICES = (
        ('shipping', 'Shipping'),
        ('billing', 'Billing'),
        ('both', 'Both'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='both')
    is_default = models.BooleanField(default=False)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)

    class Meta:
        ordering = ['-is_default', 'id']

    def __str__(self):
        return f"{self.user.email} - {self.full_name} ({self.address_type})"

    def save(self, *args, **kwargs):
        if self.is_default:
            # If this address is being set as default, unset default for other addresses of same type
            UserAddress.objects.filter(user=self.user, address_type=self.address_type, is_default=True).update(
                is_default=False)
        super().save(*args, **kwargs)
