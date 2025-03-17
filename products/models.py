from django.db import models
from django.db.models import Case, When, F, DecimalField, Value
from django.utils.text import slugify
from vendors.models import Vendor
from accounts.models import User


class Category(models.Model):
    """Product categories for organization."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children',
                               blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def get_all_children(self):
        """Return all child categories recursively."""
        children = self.children.all()
        result = list(children)
        for child in children:
            result.extend(child.get_all_children)
        return result


class Brand(models.Model):
    """Product brands."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='brand_logos/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """Main product model."""

    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('rejected', 'Rejected'),
    )

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, related_name='products',
                              blank=True, null=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    quantity = models.IntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def is_on_sale(self):
        """Check if the product is on sale."""
        return bool(self.sale_price and self.sale_price < self.price)

    @property
    def current_price(self):
        """Return the current effective price (sale_price if on sale, otherwise price)."""
        return self.sale_price if self.is_on_sale else self.price

    @property
    def discount_percentage(self):
        """Calculate the discount percentage if the product is on sale."""
        if self.is_on_sale:
            return round((1 - (self.sale_price / self.price)) * 100)
        return 0

    @property
    def is_in_stock(self):
        """Check if the product is in stock."""
        return self.quantity > 0

    @property
    def primary_image(self):
        """Get the primary image for this product."""
        images = self.images.all()
        if images.exists():
            primary = images.filter(is_primary=True).first()
            if primary:
                return primary
            return images.first()
        return None

    @classmethod
    def annotate_current_price(cls, queryset):
        """
        Annotate a queryset with a calculated 'effective_price' field that
        represents the current price (sale_price if not null, otherwise price).

        This is needed because the property 'current_price' cannot be used in database queries.
        """
        return queryset.annotate(
            effective_price=Case(
                When(sale_price__isnull=False, then=F('sale_price')),
                default=F('price'),
                output_field=DecimalField()
            )
        )

    @classmethod
    def annotate_sale_details(cls, queryset):
        """
        Annotate a queryset with calculated `effective_price` and `discount_percentage`.
        """
        return queryset.annotate(
            effective_price=Case(
                When(sale_price__isnull=False, sale_price__gt=0, sale_price__lt=F('price'), then=F('sale_price')),
                default=F('price'),
                output_field=DecimalField()
            ),
            discount_percentage=Case(
                When(sale_price__isnull=False, sale_price__gt=0, sale_price__lt=F('price'),
                     then=(Value(100) - (F('sale_price') * 100 / F('price')))),
                default=Value(0),
                output_field=DecimalField(max_digits=5, decimal_places=2)
            )
        )


class ProductImage(models.Model):
    """Images for products (multiple per product)."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', 'created_at']

    def __str__(self):
        return f"Image for {self.product.title}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            # Ensure only one primary image per product
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(id=self.id).update(
                is_primary=False)
        super().save(*args, **kwargs)


class ProductAttribute(models.Model):
    """Product attributes like size, color, material, etc."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductAttributeValue(models.Model):
    """Values for product attributes."""

    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=100)

    class Meta:
        unique_together = ('attribute', 'value')

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductVariant(models.Model):
    """Product variants with different attribute combinations."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=100, unique=True)
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    attribute_values = models.ManyToManyField(ProductAttributeValue, related_name='variants')

    def __str__(self):
        return f"{self.product.title} - {self.sku}"

    @property
    def price(self):
        return self.product.price + self.price_adjustment

    @property
    def sale_price(self):
        return self.product.sale_price + self.price_adjustment

    @property
    def is_on_sale(self):
        """Check if the product is on sale."""
        return bool(self.product.sale_price and self.sale_price < self.price)

    @property
    def current_price(self):
        """Return the current effective price (sale_price if on sale, otherwise price)."""
        return self.sale_price if self.is_on_sale else self.price

    @property
    def discount_percentage(self):
        """Calculate the discount percentage if the product is on sale."""
        if self.is_on_sale:
            return round((1 - (self.sale_price / self.price)) * 100)
        return 0

    @property
    def is_in_stock(self):
        return self.quantity > 0


class ProductReview(models.Model):
    """Customer reviews for products."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_reviews')
    title = models.CharField(max_length=255, blank=True, null=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    comment = models.TextField(blank=True, null=True)
    is_verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user')  # User can leave only one review per product

    def __str__(self):
        return f"{self.user.email} - {self.product.title} ({self.rating}★)"


class ProductQuestion(models.Model):
    """Customer questions about products."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='questions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_questions')
    question = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Q: {self.question[:50]}... - {self.product.title}"


class ProductAnswer(models.Model):
    """Answers to customer questions."""

    question = models.ForeignKey(ProductQuestion, on_delete=models.CASCADE, related_name='answers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_answers')
    answer = models.TextField()
    is_vendor = models.BooleanField(default=False)  # Indicates if the answer is from the vendor
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_vendor', '-created_at']

    def __str__(self):
        return f"A: {self.answer[:50]}... - Q: {self.question.question[:30]}..."
