from django.db import models
from django.utils.text import slugify
from accounts.models import User


class Vendor(models.Model):
    """Represents a seller/vendor on the marketplace."""

    VERIFICATION_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor')
    business_name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='vendor_logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='vendor_banners/', blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    verification_status = models.CharField(
        max_length=10,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending'
    )
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)  # percentage
    is_active = models.BooleanField(default=True)
    joined_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-joined_date']

    def __str__(self):
        return self.business_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.business_name)
        super().save(*args, **kwargs)

        # Ensure the user is marked as a vendor
        if not self.user.is_vendor:
            self.user.is_vendor = True
            self.user.save()


class VendorDocument(models.Model):
    """Documents uploaded by vendors for verification."""

    DOCUMENT_TYPE_CHOICES = (
        ('identity', 'Identity Proof'),
        ('address', 'Address Proof'),
        ('business', 'Business Registration'),
        ('tax', 'Tax Document'),
        ('bank', 'Bank Details'),
        ('other', 'Other Document'),
    )

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPE_CHOICES)
    document = models.FileField(upload_to='vendor_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.vendor.business_name} - {self.get_document_type_display()}"


class VendorBankAccount(models.Model):
    """Banking details for vendor payouts."""

    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE, related_name='bank_account')
    account_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=255)
    branch_name = models.CharField(max_length=255, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)  # For Indian banks
    swift_code = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.vendor.business_name} - {self.bank_name}"


class VendorReview(models.Model):
    """Reviews for vendors by customers."""

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendor_reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('vendor', 'user')  # User can leave only one review per vendor

    def __str__(self):
        return f"{self.user.email} - {self.vendor.business_name} ({self.rating}★)"
