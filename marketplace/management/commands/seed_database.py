import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from faker import Faker

from accounts.models import UserProfile, UserAddress
from vendors.models import Vendor, VendorReview
from products.models import (
    Category, Brand, Product, ProductImage, ProductAttribute,
    ProductAttributeValue, ProductVariant, ProductReview
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with sample data'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=10, help='Number of users to create')
        parser.add_argument('--vendors', type=int, default=5, help='Number of vendors to create')
        parser.add_argument('--categories', type=int, default=8, help='Number of categories to create')
        parser.add_argument('--brands', type=int, default=10, help='Number of brands to create')
        parser.add_argument('--products', type=int, default=50, help='Number of products to create')
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')

    @transaction.atomic
    def handle(self, *args, **options):
        # Initialize Faker
        fake = Faker()

        # Clear data if requested
        if options['clear']:
            self.clear_data()
            self.stdout.write(self.style.SUCCESS('Data cleared successfully'))

        # Create admin user
        self.create_admin_user()

        # Create users
        users = self.create_users(options['users'], fake)
        self.stdout.write(self.style.SUCCESS(f'Created {len(users)} users'))

        # Create categories
        categories = self.create_categories(options['categories'], fake)
        self.stdout.write(self.style.SUCCESS(f'Created {len(categories)} categories'))

        # Create brands
        brands = self.create_brands(options['brands'], fake)
        self.stdout.write(self.style.SUCCESS(f'Created {len(brands)} brands'))

        # Create vendors with users
        vendors = self.create_vendors(options['vendors'], users, fake)
        self.stdout.write(self.style.SUCCESS(f'Created {len(vendors)} vendors'))

        # Create products
        products = self.create_products(options['products'], categories, brands, vendors, fake)
        self.stdout.write(self.style.SUCCESS(f'Created {len(products)} products'))

        # Create product attributes and variants
        self.create_product_attributes_and_variants(products, fake)
        self.stdout.write(self.style.SUCCESS('Created product attributes and variants'))

        # Create product reviews
        self.create_product_reviews(products, users, fake)
        self.stdout.write(self.style.SUCCESS('Created product reviews'))

        # Create vendor reviews
        self.create_vendor_reviews(vendors, users, fake)
        self.stdout.write(self.style.SUCCESS('Created vendor reviews'))

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))

    def clear_data(self):
        """Clear existing data"""
        ProductReview.objects.all().delete()
        ProductVariant.objects.all().delete()
        ProductAttributeValue.objects.all().delete()
        ProductAttribute.objects.all().delete()
        ProductImage.objects.all().delete()
        Product.objects.all().delete()
        Brand.objects.all().delete()
        Category.objects.all().delete()
        VendorReview.objects.all().delete()
        Vendor.objects.all().delete()
        UserAddress.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

    def create_admin_user(self):
        """Create admin user if it doesn't exist"""
        if not User.objects.filter(email='admin@example.com').exists():
            admin_user = User.objects.create_superuser(
                email='admin@example.com',
                password='adminpassword',
                first_name='Admin',
                last_name='User'
            )
            UserProfile.objects.create(user=admin_user)
            self.stdout.write(self.style.SUCCESS('Admin user created'))

    def create_users(self, count, fake):
        """Create regular users"""
        users = []
        for _ in range(count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"{slugify(first_name)}.{slugify(last_name)}@{fake.domain_name()}"

            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    email=email,
                    password='password123',
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=fake.random_number()
                )

                # Create user profile
                profile = UserProfile.objects.create(user=user)

                # Create 1-2 addresses for user
                address_count = random.randint(1, 2)
                for i in range(address_count):
                    address_type = random.choice(['shipping', 'billing', 'both'])
                    UserAddress.objects.create(
                        user=user,
                        address_type=address_type,
                        is_default=(i == 0),  # First address is default
                        full_name=user.get_full_name(),
                        phone=user.phone_number,
                        address_line1=fake.street_address(),
                        address_line2=fake.secondary_address() if random.choice([True, False]) else '',
                        city=fake.city(),
                        state=fake.state(),
                        country=fake.country(),
                        postal_code=fake.postcode()
                    )

                users.append(user)

        return users

    def create_categories(self, count, fake):
        """Create product categories"""
        categories = []
        main_categories = []

        # Create main categories
        for i in range(count // 2):
            name = fake.unique.word().capitalize()
            category = Category.objects.create(
                name=name,
                slug=slugify(name),
                description=fake.paragraph(),
                is_active=True
            )
            main_categories.append(category)
            categories.append(category)

        # Create subcategories
        for i in range(count // 2, count):
            name = fake.unique.word().capitalize()
            parent = random.choice(main_categories)
            category = Category.objects.create(
                name=name,
                slug=slugify(name),
                description=fake.paragraph(),
                parent=parent,
                is_active=True
            )
            categories.append(category)

        return categories

    def create_brands(self, count, fake):
        """Create product brands"""
        brands = []
        for _ in range(count):
            name = fake.unique.company()
            brand = Brand.objects.create(
                name=name,
                slug=slugify(name),
                description=fake.paragraph(),
                is_active=True
            )
            brands.append(brand)

        return brands

    def create_vendors(self, count, users, fake):
        """Create vendors with available users"""
        vendors = []
        available_users = [user for user in users if not hasattr(user, 'vendor')]

        for i in range(min(count, len(available_users))):
            user = available_users[i]
            business_name = fake.unique.company()

            vendor = Vendor.objects.create(
                user=user,
                business_name=business_name,
                slug=slugify(business_name),
                description=fake.paragraph(),
                address=fake.street_address(),
                city=fake.city(),
                state=fake.state(),
                country=fake.country(),
                postal_code=fake.postcode(),
                phone_number=fake.random_number(),
                email=fake.company_email(),
                website=f"https://www.{slugify(business_name)}.com" if random.choice([True, False]) else None,
                tax_id=fake.bothify(text='??########'),
                verification_status='verified',
                commission_rate=Decimal(str(random.uniform(5.0, 15.0)).rstrip('0').rstrip('.') if '.' in str(
                    random.uniform(5.0, 15.0)) else str(random.uniform(5.0, 15.0))),
                is_active=True
            )

            vendors.append(vendor)

        return vendors

    def create_products(self, count, categories, brands, vendors, fake):
        """Create products assigned to vendors"""
        products = []

        for _ in range(count):
            vendor = random.choice(vendors)
            category = random.choice(categories)
            brand = random.choice(brands) if random.choice([True, False]) else None

            price = Decimal(str(random.uniform(100.0, 10000.0)).rstrip('0').rstrip('.') if '.' in str(
                random.uniform(100.0, 10000.0)) else str(random.uniform(100.0, 10000.0)))

            # Sometimes create sale price
            sale_price = None
            if random.choice([True, False]):
                discount = random.uniform(0.1, 0.5)  # 10-50% discount
                sale_price = price * Decimal(1 - discount)
                sale_price = Decimal(
                    str(sale_price).rstrip('0').rstrip('.') if '.' in str(sale_price) else str(sale_price))

            title = fake.unique.sentence(nb_words=4).rstrip('.')

            product = Product.objects.create(
                vendor=vendor,
                category=category,
                brand=brand,
                title=title,
                slug=slugify(title),
                description='\n'.join(fake.paragraphs(nb=3)),
                price=price,
                sale_price=sale_price,
                tax_rate=Decimal(str(random.choice([5.0, 12.0, 18.0]))),
                quantity=random.randint(0, 100),
                sku=fake.unique.bothify(text='???-#####'),
                status='active',
                is_featured=random.choice([True, False]),
            )

            # Create 1-4 product images
            for i in range(random.randint(1, 4)):
                ProductImage.objects.create(
                    product=product,
                    image='product_images/placeholder.jpg',  # You would need actual images in production
                    alt_text=f"{product.title} image {i + 1}",
                    is_primary=(i == 0)  # First image is primary
                )

            products.append(product)

        return products

    def create_product_attributes_and_variants(self, products, fake):
        """Create product attributes and variants for some products"""
        # Create common attributes
        size_attribute = ProductAttribute.objects.create(name='Size', slug='size')
        color_attribute = ProductAttribute.objects.create(name='Color', slug='color')
        material_attribute = ProductAttribute.objects.create(name='Material', slug='material')

        # Create attribute values
        size_values = [
            ProductAttributeValue.objects.create(attribute=size_attribute, value=size)
            for size in ['Small', 'Medium', 'Large', 'X-Large']
        ]

        color_values = [
            ProductAttributeValue.objects.create(attribute=color_attribute, value=color)
            for color in ['Red', 'Blue', 'Green', 'Black', 'White']
        ]

        material_values = [
            ProductAttributeValue.objects.create(attribute=material_attribute, value=material)
            for material in ['Cotton', 'Polyester', 'Wool', 'Leather', 'Denim']
        ]

        # Add variants to approximately 60% of products
        for product in random.sample(products, int(len(products) * 0.6)):
            # Decide which attributes to use for this product (1-3 attributes)
            attributes_to_use = random.sample([
                (size_attribute, size_values),
                (color_attribute, color_values),
                (material_attribute, material_values)
            ], random.randint(1, 3))

            # Generate variants based on selected attributes
            # For simplicity, we'll create up to 3 variants per product
            for i in range(random.randint(2, 5)):
                variant = ProductVariant.objects.create(
                    product=product,
                    sku=f"{product.sku}-V{i + 1}",
                    price_adjustment=Decimal(str(random.uniform(-50, 50)).rstrip('0').rstrip('.') if '.' in str(
                        random.uniform(-50, 50)) else str(random.uniform(-50, 50))),
                    quantity=random.randint(0, 30),
                )

                # Add attribute values to variant
                for attr, values in attributes_to_use:
                    variant.attribute_values.add(random.choice(values))

    def create_product_reviews(self, products, users, fake):
        """Create product reviews"""
        # Create 1-3 reviews for about 70% of products
        for product in random.sample(products, int(len(products) * 0.7)):
            review_count = random.randint(1, min(5, len(users)))
            reviewers = random.sample(users, review_count)

            for user in reviewers:
                rating = random.randint(3, 5)  # Mostly positive reviews (3-5 stars)

                ProductReview.objects.create(
                    product=product,
                    user=user,
                    title=fake.sentence() if random.choice([True, False]) else None,
                    rating=rating,
                    comment=fake.paragraph(),
                    is_verified_purchase=random.choice([True, False]),
                )

    def create_vendor_reviews(self, vendors, users, fake):
        """Create vendor reviews"""
        # Create 1-5 reviews for each vendor
        for vendor in vendors:
            review_count = random.randint(1, min(10, len(users)))
            reviewers = random.sample(users, review_count)

            for user in reviewers:
                rating = random.randint(3, 5)  # Mostly positive (3-5 stars)

                VendorReview.objects.create(
                    vendor=vendor,
                    user=user,
                    rating=rating,
                    comment=fake.paragraph(),
                )
