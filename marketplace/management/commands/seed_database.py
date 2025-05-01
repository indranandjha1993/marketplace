import decimal
import random
import string
from datetime import timedelta
from io import BytesIO

import requests
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

# Import all relevant models
from accounts.models import UserProfile, UserAddress
from cart.models import SavedForLater, CartItem, Cart
from orders.models import Order, VendorOrder, OrderItem, Payment, Refund, OrderTracking, Coupon
from payments.models import PaymentMethod, Transaction, VendorPayout
from products.models import (
    Category, Brand, Product, ProductImage,
    ProductAttribute, ProductAttributeValue, ProductVariant,
    ProductReview, ProductQuestion, ProductAnswer
)
from vendors.models import Vendor, VendorBankAccount, VendorDocument

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with sample e-commerce data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Flush existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self.flush_database()
            self.stdout.write(self.style.SUCCESS('Successfully flushed database'))

        with transaction.atomic():
            self.create_users()
            self.create_vendors()
            self.create_categories()
            self.create_brands()
            self.create_product_attributes()
            self.create_products()
            self.create_coupons()
            self.create_carts()
            self.create_orders()
            self.create_transactions()

        self.stdout.write(self.style.SUCCESS('Successfully seeded database!'))

    def flush_database(self):
        """Remove all existing data from the database."""
        # Only delete model instances, not the actual models
        VendorPayout.objects.all().delete()
        Transaction.objects.all().delete()
        PaymentMethod.objects.all().delete()

        OrderTracking.objects.all().delete()
        Refund.objects.all().delete()
        Payment.objects.all().delete()
        OrderItem.objects.all().delete()
        VendorOrder.objects.all().delete()
        Order.objects.all().delete()
        Coupon.objects.all().delete()

        SavedForLater.objects.all().delete()
        CartItem.objects.all().delete()
        Cart.objects.all().delete()

        ProductAnswer.objects.all().delete()
        ProductQuestion.objects.all().delete()
        ProductReview.objects.all().delete()
        ProductAttributeValue.objects.all().delete()
        ProductAttribute.objects.all().delete()
        ProductVariant.objects.all().delete()
        ProductImage.objects.all().delete()
        Product.objects.all().delete()
        Brand.objects.all().delete()
        Category.objects.all().delete()

        VendorDocument.objects.all().delete()
        VendorBankAccount.objects.all().delete()
        Vendor.objects.all().delete()

        UserAddress.objects.all().delete()
        UserProfile.objects.all().delete()

        # Delete all users except superuser
        User.objects.filter(is_superuser=False).delete()

    def get_random_image(self, width=500, height=500, category="", entity_type="product"):
        """
        Get a random contextual image based on entity type.
        
        Args:
            width: Image width
            height: Image height
            category: Main category/subject of the image
            entity_type: Type of entity (product, user, vendor, category, brand)
        """
        try:
            # Adjust dimensions based on entity type
            if entity_type == "profile" or entity_type == "avatar":
                # Square aspect ratio for profile pictures
                width = height = 400
            elif entity_type == "logo":
                width, height = 300, 150
            elif entity_type == "banner":
                width, height = 1200, 400
            elif entity_type == "category":
                width, height = 800, 600
            elif entity_type == "product":
                width, height = 800, 800
            
            # Enhance search query based on entity type and category
            query_terms = []
            
            if category:
                query_terms.append(category)
                
            if entity_type == "profile" or entity_type == "avatar":
                query_terms.extend(["portrait", "person", "professional"])
            elif entity_type == "logo":
                query_terms.extend(["logo", "minimal", "brand"])
            elif entity_type == "banner":
                query_terms.extend(["storefront", "shop", "retail", "banner"])
            elif entity_type == "document":
                query_terms.extend(["document", "paper", "certificate"])
                
            # Filter out empty strings and join with commas
            query = ','.join([term for term in query_terms if term])
            
            # Construct URL with enhanced query
            if query:
                url = f"https://source.unsplash.com/random/{width}x{height}/?{query}"
            else:
                url = f"https://source.unsplash.com/random/{width}x{height}"
    
            # Try alternative image sources if available
            alternative_sources = [
                url,
                f"https://picsum.photos/{width}/{height}",  # Lorem Picsum as fallback
            ]
            
            for source_url in alternative_sources:
                response = requests.get(source_url, timeout=10)
                if response.status_code == 200:
                    # Create a descriptive filename
                    filename = f"{slugify(entity_type)}-{slugify(category or 'image')}-{random.randint(1, 10000)}.jpg"
                    return ContentFile(response.content, name=filename)
            
            # If all sources fail, fallback to local generation
            return self.generate_placeholder_image(width, height, entity_type)
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Error fetching image: {e}"))
            return self.generate_placeholder_image(width, height, entity_type)

    def generate_placeholder_image(self, width=500, height=500, entity_type="product"):
        """
        Generate a contextual placeholder image based on entity type.
        
        Args:
            width: Image width
            height: Image height
            entity_type: Type of entity (product, profile, logo, banner, etc.)
        """
        # Select color palette based on entity type
        if entity_type == "product":
            # Bright, product-friendly colors
            bg_color = (
                random.randint(200, 255),
                random.randint(200, 255),
                random.randint(200, 255)
            )
        elif entity_type in ["profile", "avatar"]:
            # Neutral tones for profile pictures
            bg_color = (
                random.randint(220, 240),
                random.randint(220, 240),
                random.randint(220, 240)
            )
        elif entity_type == "logo":
            # Clean white background for logos
            bg_color = (255, 255, 255)
        elif entity_type == "banner":
            # Vibrant colors for banners
            bg_color = (
                random.randint(100, 200),
                random.randint(100, 200),
                random.randint(200, 255)
            )
        elif entity_type == "document":
            # Paper-like background for documents
            bg_color = (245, 245, 245)
        else:
            # Default color
            bg_color = (
                random.randint(180, 255),
                random.randint(180, 255),
                random.randint(180, 255)
            )
        
        # Create base image
        image = Image.new('RGB', (width, height), color=bg_color)
        
        # Generate appropriate placeholder content based on entity type
        if entity_type in ["profile", "avatar"]:
            # Create a simple avatar-like image
            center_x, center_y = width // 2, height // 2
            radius = min(width, height) // 3
            
            # Draw head
            avatar_color = (
                random.randint(50, 150),
                random.randint(50, 150),
                random.randint(50, 150)
            )
            
            for x in range(width):
                for y in range(height):
                    # Create circular head
                    if ((x - center_x) ** 2 + (y - center_y) ** 2) <= radius ** 2:
                        image.putpixel((x, y), avatar_color)
            
            # Draw body (shoulder outline)
            body_top = center_y + radius
            for x in range(center_x - radius, center_x + radius):
                for y in range(body_top, min(body_top + radius, height)):
                    if center_x - radius//2 <= x <= center_x + radius//2:
                        image.putpixel((x, y), avatar_color)
            
        elif entity_type == "logo":
            # Create a simple logo placeholder
            accent_color = (
                random.randint(0, 100),
                random.randint(0, 100),
                random.randint(100, 200)
            )
            
            # Draw a simple shape
            shape_width = width // 2
            shape_height = height // 2
            start_x = (width - shape_width) // 2
            start_y = (height - shape_height) // 2
            
            for x in range(start_x, start_x + shape_width):
                for y in range(start_y, start_y + shape_height):
                    # Create a rounded rectangle
                    if (start_x + shape_width//5 <= x <= start_x + shape_width - shape_width//5 or
                        start_y + shape_height//5 <= y <= start_y + shape_height - shape_height//5):
                        image.putpixel((x, y), accent_color)
                        
        elif entity_type == "banner":
            # Create a gradient background for banners
            for x in range(width):
                for y in range(height):
                    r = bg_color[0] - int((y / height) * 50)
                    g = bg_color[1] - int((y / height) * 50)
                    b = bg_color[2]
                    image.putpixel((x, y), (max(0, r), max(0, g), b))
                    
            # Add some decorative elements
            for _ in range(3):
                element_color = (
                    random.randint(200, 255),
                    random.randint(200, 255),
                    random.randint(200, 255)
                )
                element_x = random.randint(0, width - width//4)
                element_width = width // 4
                element_height = height // 3
                
                for x in range(element_x, min(element_x + element_width, width)):
                    for y in range(height - element_height, height):
                        if random.random() > 0.5:  # Create some texture
                            image.putpixel((x, y), element_color)
                
        elif entity_type == "document":
            # Create document-like lines
            line_color = (180, 180, 180)
            for y in range(height // 6, height, height // 15):
                for x in range(width // 10, width - width // 10):
                    if y % (height // 12) == 0:
                        image.putpixel((x, y), line_color)
                        
            # Add a "header"
            header_color = (150, 150, 150)
            for x in range(width // 10, width // 2):
                for y in range(height // 20, height // 10):
                    image.putpixel((x, y), header_color)
            
        else:  # Default for products and other types
            # Add some random shapes for variety
            for _ in range(5):
                shape_color = (
                    random.randint(50, 150),
                    random.randint(50, 150),
                    random.randint(50, 150)
                )
                x1 = random.randint(0, width)
                y1 = random.randint(0, height)
                x2 = random.randint(0, width)
                y2 = random.randint(0, height)
    
                shape = Image.new('RGB', (width, height))
                # draw a rectangle
                for x in range(min(x1, x2), max(x1, x2)):
                    for y in range(min(y1, y2), max(y1, y2)):
                        if 0 <= x < width and 0 <= y < height:
                            shape.putpixel((x, y), shape_color)
    
                image = Image.blend(image, shape, 0.3)
                
            # Add a simple product outline for product images
            if entity_type == "product":
                product_outline = Image.new('RGB', (width, height))
                center_x, center_y = width // 2, height // 2
                outline_width = width // 2
                outline_height = height // 2
                
                outline_color = (
                    random.randint(50, 100),
                    random.randint(50, 100),
                    random.randint(50, 100)
                )
                
                for x in range(center_x - outline_width//2, center_x + outline_width//2):
                    for y in range(center_y - outline_height//2, center_y + outline_height//2):
                        if (abs(x - (center_x - outline_width//2)) < 5 or 
                            abs(x - (center_x + outline_width//2 - 1)) < 5 or
                            abs(y - (center_y - outline_height//2)) < 5 or
                            abs(y - (center_y + outline_height//2 - 1)) < 5):
                            if 0 <= x < width and 0 <= y < height:
                                product_outline.putpixel((x, y), outline_color)
                                
                image = Image.blend(image, product_outline, 0.7)
    
        # Save image to in-memory file
        img_io = BytesIO()
        image.save(img_io, format='JPEG', quality=85)
        img_io.seek(0)
        return ContentFile(img_io.getvalue(), name=f'placeholder-{entity_type}-{random.randint(1, 10000)}.jpg')

    def create_users(self):
        """Create predefined users for testing."""
        # Predefined user data for consistent testing
        user_data = [
            {
                'email': 'customer@example.com',
                'username': 'customer',
                'password': 'password123',
                'first_name': 'John',
                'last_name': 'Doe',
                'is_vendor': False,
            },
            {
                'email': 'vendor1@example.com',
                'username': 'vendor1',
                'password': 'password123',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'is_vendor': True,
            },
            {
                'email': 'vendor2@example.com',
                'username': 'vendor2',
                'password': 'password123',
                'first_name': 'Robert',
                'last_name': 'Johnson',
                'is_vendor': True,
            },
            {
                'email': 'admin@example.com',
                'username': 'admin',
                'password': 'admin123',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_vendor': False,
                'is_staff': True,
                'is_superuser': True,
            },
        ]

        # Create additional regular customers
        for i in range(3, 10):
            user_data.append({
                'email': f'customer{i}@example.com',
                'username': f'customer{i}',
                'password': 'password123',
                'first_name': f'Customer{i}',
                'last_name': 'User',
                'is_vendor': False,
            })

        # Create users and their profiles
        users_created = []

        for data in user_data:
            # Check if user already exists
            if not User.objects.filter(email=data['email']).exists():
                is_vendor = data.pop('is_vendor', False)
                is_staff = data.pop('is_staff', False)
                is_superuser = data.pop('is_superuser', False)

                user = User.objects.create_user(
                    email=data['email'],
                    username=data['username'],
                    password=data['password'],
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    is_vendor=is_vendor,
                    is_staff=is_staff,
                    is_superuser=is_superuser,
                )

                # Create user profile
                profile = UserProfile.objects.create(
                    user=user,
                    profile_picture=self.get_random_image(category="person"),
                    address_line1=f"{random.randint(1, 999)} Main St",
                    city=random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                    state=random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                    country="United States",
                    postal_code=f"{random.randint(10000, 99999)}",
                )

                # Create addresses for each user
                for address_type in ['shipping', 'billing']:
                    UserAddress.objects.create(
                        user=user,
                        address_type=address_type,
                        is_default=True,
                        full_name=f"{user.first_name} {user.last_name}",
                        phone=f"+1{random.randint(2000000000, 9999999999)}",
                        address_line1=f"{random.randint(1, 999)} {random.choice(['Main', 'Oak', 'Pine', 'Maple'])} St",
                        city=random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                        state=random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                        country="United States",
                        postal_code=f"{random.randint(10000, 99999)}",
                    )

                users_created.append(user)
                self.stdout.write(f"Created user: {user.email}")

        self.stdout.write(self.style.SUCCESS(f'Created {len(users_created)} users'))

    def create_vendors(self):
        """Create vendor accounts for testing."""
        vendor_users = User.objects.filter(is_vendor=True)

        for user in vendor_users:
            # Check if vendor already exists for this user
            if not hasattr(user, 'vendor'):
                business_name = f"{user.first_name}'s {random.choice(['Shop', 'Store', 'Marketplace', 'Emporium'])}"

                vendor = Vendor.objects.create(
                    user=user,
                    business_name=business_name,
                    description=f"Welcome to {business_name}! We offer high-quality products at competitive prices.",
                    logo=self.get_random_image(category="logo"),
                    banner=self.get_random_image(width=1200, height=400, category="retail"),
                    address=f"{random.randint(1, 999)} Business District",
                    city=random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                    state=random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                    country="United States",
                    postal_code=f"{random.randint(10000, 99999)}",
                    phone_number=f"+1{random.randint(2000000000, 9999999999)}",
                    email=user.email,
                    website=f"https://www.{slugify(business_name)}.com",
                    tax_id=f"TAX{random.randint(1000000, 9999999)}",
                    verification_status='verified',
                    commission_rate=decimal.Decimal(random.randint(5, 15)),
                )

                # Create bank account for the vendor
                VendorBankAccount.objects.create(
                    vendor=vendor,
                    account_name=business_name,
                    account_number=f"{random.randint(1000000000, 9999999999)}",
                    bank_name=random.choice(["Chase", "Bank of America", "Wells Fargo", "Citibank"]),
                    branch_name=f"{vendor.city} Branch",
                    ifsc_code=f"IFSC{random.randint(10000, 99999)}",
                    swift_code=f"SWIFT{random.randint(10000, 99999)}",
                    is_verified=True,
                )

                # Create vendor documents
                for doc_type in ['identity', 'address', 'business', 'tax']:
                    VendorDocument.objects.create(
                        vendor=vendor,
                        document_type=doc_type,
                        document=self.get_random_image(category="document"),
                        notes=f"{doc_type.capitalize()} verification document"
                    )

                self.stdout.write(f"Created vendor: {vendor.business_name}")

        self.stdout.write(self.style.SUCCESS(f'Created vendors for {vendor_users.count()} users'))

    def create_categories(self):
        """Create product categories."""
        categories = [
            {"name": "Electronics", "children": [
                "Smartphones", "Laptops", "Cameras", "Audio", "Accessories"
            ]},
            {"name": "Fashion", "children": [
                "Men's Clothing", "Women's Clothing", "Footwear", "Watches", "Bags"
            ]},
            {"name": "Home & Kitchen", "children": [
                "Furniture", "Decor", "Kitchen Appliances", "Bedding", "Lighting"
            ]},
            {"name": "Beauty & Personal Care", "children": [
                "Skincare", "Makeup", "Haircare", "Fragrances", "Bath & Body"
            ]},
            {"name": "Books & Media", "children": [
                "Fiction", "Non-fiction", "Textbooks", "Movies", "Music"
            ]},
        ]

        category_objects = {}

        for category_data in categories:
            # Create parent category
            parent_name = category_data["name"]
            if not Category.objects.filter(name=parent_name).exists():
                parent = Category.objects.create(
                    name=parent_name,
                    description=f"Browse our wide selection of {parent_name.lower()} products.",
                    image=self.get_random_image(category=parent_name.lower()),
                    meta_keywords=f"{parent_name.lower()}, products, shop, buy"
                )
                category_objects[parent_name] = parent

                # Create child categories
                for child_name in category_data["children"]:
                    if not Category.objects.filter(name=child_name).exists():
                        child = Category.objects.create(
                            name=child_name,
                            parent=parent,
                            description=f"Explore our {child_name.lower()} collection.",
                            image=self.get_random_image(category=child_name.lower()),
                            meta_keywords=f"{child_name.lower()}, {parent_name.lower()}, products"
                        )
                        category_objects[child_name] = child

                self.stdout.write(
                    f"Created category: {parent_name} with {len(category_data['children'])} subcategories")

        self.stdout.write(self.style.SUCCESS(f'Created {Category.objects.count()} categories'))

    def create_brands(self):
        """Create product brands."""
        brands = [
            {"name": "TechPro", "category": "Electronics"},
            {"name": "FashionNow", "category": "Fashion"},
            {"name": "HomeStyle", "category": "Home & Kitchen"},
            {"name": "BeautyGlow", "category": "Beauty & Personal Care"},
            {"name": "MediaWorld", "category": "Books & Media"},
            {"name": "SmartLife", "category": "Electronics"},
            {"name": "VogueStyle", "category": "Fashion"},
            {"name": "ComfortHome", "category": "Home & Kitchen"},
            {"name": "GlamBeauty", "category": "Beauty & Personal Care"},
            {"name": "BookHaven", "category": "Books & Media"},
        ]

        for brand_data in brands:
            if not Brand.objects.filter(name=brand_data["name"]).exists():
                Brand.objects.create(
                    name=brand_data["name"],
                    description=f"Quality products from {brand_data['name']}.",
                    logo=self.get_random_image(category=f"{brand_data['category']} logo"),
                    website=f"https://www.{slugify(brand_data['name'])}.com",
                )
                self.stdout.write(f"Created brand: {brand_data['name']}")

        self.stdout.write(self.style.SUCCESS(f'Created {Brand.objects.count()} brands'))

    def create_product_attributes(self):
        """Create product attributes and values."""
        attributes = {
            "Color": ["Red", "Blue", "Green", "Black", "White", "Gray", "Purple", "Yellow", "Orange", "Pink"],
            "Size": ["XS", "S", "M", "L", "XL", "XXL", "XXXL"],
            "Material": ["Cotton", "Polyester", "Leather", "Metal", "Glass", "Wood", "Plastic", "Ceramic"],
            "Storage": ["32GB", "64GB", "128GB", "256GB", "512GB", "1TB"],
            "RAM": ["4GB", "8GB", "16GB", "32GB", "64GB"],
        }

        for attr_name, values in attributes.items():
            if not ProductAttribute.objects.filter(name=attr_name).exists():
                attribute = ProductAttribute.objects.create(
                    name=attr_name,
                    description=f"Product {attr_name.lower()}"
                )

                # Create attribute values
                for value in values:
                    ProductAttributeValue.objects.create(
                        attribute=attribute,
                        value=value
                    )

                self.stdout.write(f"Created attribute: {attr_name} with {len(values)} values")

        self.stdout.write(self.style.SUCCESS(f'Created {ProductAttribute.objects.count()} attributes'))

    def create_products(self):
        """Create products, variants, images, and reviews."""
        categories = Category.objects.all()
        brands = Brand.objects.all()
        vendors = Vendor.objects.all()
        users = User.objects.filter(is_vendor=False)  # Regular customers

        products_to_create = 50  # Number of products to create
        products_created = 0

        product_templates = [
            {
                "title_prefix": "Premium",
                "price_range": (50, 200),
                "description": "High-quality product with premium features. Perfect for those who want the best performance and durability."
            },
            {
                "title_prefix": "Standard",
                "price_range": (20, 100),
                "description": "Reliable product with standard features. Good value for everyday use."
            },
            {
                "title_prefix": "Budget",
                "price_range": (10, 50),
                "description": "Affordable product with basic features. Great option for those on a budget."
            },
            {
                "title_prefix": "Luxury",
                "price_range": (100, 500),
                "description": "Exclusive product with luxury features. Experience the ultimate in quality and design."
            },
            {
                "title_prefix": "Eco-friendly",
                "price_range": (30, 150),
                "description": "Sustainable product made with eco-friendly materials. Good for you and the environment."
            },
        ]

        product_words = [
            "Phone", "Laptop", "Camera", "Headphones", "Speaker", "Shirt", "Dress", "Shoes", "Watch", "Bag",
            "Sofa", "Table", "Lamp", "Blender", "Microwave", "Moisturizer", "Lipstick", "Shampoo", "Perfume",
            "Novel", "Cookbook", "Textbook", "Movie", "Album"
        ]

        for _ in range(products_to_create):
            # Pick random elements for the product
            category = random.choice(categories)
            brand = random.choice(brands)
            vendor = random.choice(vendors)
            template = random.choice(product_templates)

            # Generate product name
            product_type = random.choice(product_words)
            product_name = f"{template['title_prefix']} {product_type} {random.randint(100, 999)}"

            # Generate price and sale price
            base_price = round(decimal.Decimal(random.uniform(*template["price_range"])), 2)
            has_sale = random.choice([True, False])
            sale_price = round(base_price * decimal.Decimal(random.uniform(0.7, 0.9)), 2) if has_sale else None

            sku = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

            if not Product.objects.filter(title=product_name).exists():
                # Create the product
                product = Product.objects.create(
                    vendor=vendor,
                    category=category,
                    brand=brand,
                    title=product_name,
                    description=template[
                                    "description"] + f"\n\nThe {product_name} features the latest technology and design.",
                    price=base_price,
                    sale_price=sale_price,
                    tax_rate=decimal.Decimal(random.choice([5.0, 7.5, 10.0, 12.5])),
                    quantity=random.randint(10, 100),
                    sku=sku,
                    status='active',
                    is_featured=random.choice([True, False]),
                    meta_keywords=f"{product_name.lower()}, {category.name.lower()}, {brand.name.lower()}",
                    meta_description=f"Buy {product_name} from {vendor.business_name}. {template['description'][:100]}...",
                    view_count=random.randint(10, 1000),
                )

                # Create product images (1-5 images per product)
                for i in range(random.randint(1, 5)):
                    ProductImage.objects.create(
                        product=product,
                        image=self.get_random_image(category=f"{category.name} {product_type}"),
                        alt_text=f"{product_name} image {i + 1}",
                        is_primary=i == 0  # First image is primary
                    )

                # Create product variants (0-3 variants per product)
                has_variants = random.choice([True, False])
                if has_variants:
                    # Decide which attributes to use
                    if product_type in ["Phone", "Laptop"]:
                        variant_attrs = ["Color", "Storage"]
                    elif product_type in ["Shirt", "Dress", "Shoes"]:
                        variant_attrs = ["Color", "Size"]
                    else:
                        variant_attrs = random.sample(["Color", "Size", "Material"], k=random.randint(1, 2))

                    variant_attributes = [
                        ProductAttribute.objects.get(name=attr_name) for attr_name in variant_attrs
                    ]

                    # Create 2-4 variants
                    for j in range(random.randint(2, 4)):
                        variant_sku = f"{sku}-V{j + 1}"
                        price_adj = decimal.Decimal(random.uniform(-10, 20))

                        variant = ProductVariant.objects.create(
                            product=product,
                            sku=variant_sku,
                            price_adjustment=price_adj,
                            quantity=random.randint(5, 30),
                        )

                        # Add attribute values to the variant
                        for attr in variant_attributes:
                            values = ProductAttributeValue.objects.filter(attribute=attr)
                            variant.attribute_values.add(random.choice(values))

                # Create product reviews (0-5 reviews per product)
                for _ in range(random.randint(0, 5)):
                    user = random.choice(users)
                    # Avoid duplicate reviews from the same user
                    if not ProductReview.objects.filter(product=product, user=user).exists():
                        ProductReview.objects.create(
                            product=product,
                            user=user,
                            title=random.choice([
                                "Great product!", "Excellent quality", "Good value",
                                "Not bad", "Could be better", "Disappointing"
                            ]),
                            rating=random.randint(1, 5),
                            comment=random.choice([
                                "I love this product! It works perfectly and the quality is amazing.",
                                "Good product for the price. Not the best I've used but definitely worth it.",
                                "Decent product but there's room for improvement.",
                                "Not what I expected. The quality could be better.",
                                "Excellent product! I would definitely recommend it to others.",
                            ]),
                            is_verified_purchase=random.choice([True, False]),
                        )

                # Create product questions (0-3 questions per product)
                for _ in range(random.randint(0, 3)):
                    user = random.choice(users)
                    question = ProductQuestion.objects.create(
                        product=product,
                        user=user,
                        question=random.choice([
                            "Does this product come with a warranty?",
                            "What are the dimensions of this product?",
                            "Is this product compatible with...?",
                            "How long does the battery last?",
                            "Does it come in other colors?",
                        ]),
                    )

                    # Add 1-2 answers to each question
                    for _ in range(random.randint(1, 2)):
                        answerer = random.choice([product.vendor.user] + list(users))
                        is_vendor = answerer == product.vendor.user

                        ProductAnswer.objects.create(
                            question=question,
                            user=answerer,
                            answer=random.choice([
                                "Yes, it comes with a 1-year warranty.",
                                "The dimensions are 10x5x2 inches.",
                                "It is compatible with most standard devices.",
                                "The battery lasts approximately 8-10 hours with normal use.",
                                "Yes, it's available in multiple colors. Please check the variants.",
                            ]),
                            is_vendor=is_vendor,
                        )

                products_created += 1
                self.stdout.write(f"Created product: {product.title}")

        self.stdout.write(self.style.SUCCESS(f'Created {products_created} products'))

    def create_coupons(self):
        """Create discount coupons."""
        coupon_codes = [
            "WELCOME10", "SUMMER20", "FLASH25", "SPECIAL15", "HOLIDAY30"
        ]

        now = timezone.now()

        for code in coupon_codes:
            if not Coupon.objects.filter(code=code).exists():
                discount_type = random.choice(['percentage', 'fixed'])
                discount_value = random.randint(5, 30) if discount_type == 'percentage' else random.randint(5, 50)

                Coupon.objects.create(
                    code=code,
                    description=f"Get {discount_value}{'%' if discount_type == 'percentage' else '$'} off your order",
                    discount_type=discount_type,
                    discount_value=decimal.Decimal(discount_value),
                    minimum_order_amount=decimal.Decimal(random.randint(0, 100)),
                    valid_from=now - timedelta(days=random.randint(10, 30)),
                    valid_to=now + timedelta(days=random.randint(30, 90)),
                    max_usage=random.randint(50, 200),
                    max_usage_per_user=random.randint(1, 3),
                    usage_count=random.randint(0, 20),
                )

                self.stdout.write(f"Created coupon: {code}")

        self.stdout.write(self.style.SUCCESS(f'Created {Coupon.objects.count()} coupons'))

    def create_carts(self):
        """Create shopping carts for users."""
        users = User.objects.all()
        products = Product.objects.filter(status='active')

        for user in users:
            # Create cart for each user
            cart, created = Cart.objects.get_or_create(user=user)

            if created:
                # Add 0-5 random products to the cart
                for _ in range(random.randint(0, 5)):
                    product = random.choice(products)
                    quantity = random.randint(1, 3)

                    # If product has variants, select a random variant
                    variant = None
                    if product.variants.exists():
                        variant = random.choice(product.variants.all())

                    # Add item to cart
                    success, message, _ = cart.add_item(product, quantity, variant)
                    if success:
                        self.stdout.write(f"Added {product.title} to {user.email}'s cart")

                # Add 0-3 saved for later items
                for _ in range(random.randint(0, 3)):
                    product = random.choice(products)

                    # If product has variants, select a random variant
                    variant = None
                    if product.variants.exists():
                        variant = random.choice(product.variants.all())

                    # Check if item doesn't already exist
                    if not SavedForLater.objects.filter(user=user, product=product, variant=variant).exists():
                        SavedForLater.objects.create(
                            user=user,
                            product=product,
                            variant=variant,
                        )
                        self.stdout.write(f"Saved {product.title} for later for {user.email}")

        self.stdout.write(self.style.SUCCESS(f'Created carts for {users.count()} users'))

    def generate_order_number(self):
        """Generate a unique order number."""
        prefix = "ORD"
        random_part = ''.join(random.choices(string.digits, k=8))
        return f"{prefix}{random_part}"

    def create_orders(self):
        """Create orders for testing."""
        users = User.objects.all()
        products = Product.objects.filter(status='active')
        coupons = Coupon.objects.all()

        # Create 1-3 orders for each user
        for user in users:
            for _ in range(random.randint(1, 3)):
                # Get user's addresses
                shipping_address = user.addresses.filter(address_type__in=['shipping', 'both']).first()
                billing_address = user.addresses.filter(address_type__in=['billing', 'both']).first()

                if not shipping_address or not billing_address:
                    continue

                # Generate order
                order_number = self.generate_order_number()
                order_status = random.choice(['pending', 'processing', 'shipped', 'delivered'])
                payment_status = 'paid' if order_status != 'pending' else random.choice(['pending', 'paid'])
                payment_method = random.choice(['credit_card', 'paypal', 'upi', 'bank_transfer'])

                # Random dates within last 90 days
                days_ago = random.randint(1, 90)
                order_date = timezone.now() - timedelta(days=days_ago)

                # Calculate order totals
                subtotal = decimal.Decimal('0.00')
                tax_amount = decimal.Decimal('0.00')
                shipping_cost = decimal.Decimal(random.uniform(5, 20))

                # Apply coupon in some cases
                applied_coupon = random.choice([None] + list(coupons)) if random.random() > 0.7 else None
                discount_amount = decimal.Decimal('0.00')

                # Create order
                order = Order.objects.create(
                    user=user,
                    order_number=order_number,
                    shipping_address=shipping_address,
                    billing_address=billing_address,
                    status=order_status,
                    payment_status=payment_status,
                    payment_method=payment_method,
                    transaction_id=f"TXN{random.randint(10000000, 99999999)}" if payment_status == 'paid' else None,
                    subtotal=subtotal,  # Will update after adding items
                    shipping_cost=shipping_cost,
                    tax_amount=tax_amount,  # Will update after adding items
                    discount_amount=discount_amount,  # Will update if coupon applied
                    total=subtotal + shipping_cost + tax_amount - discount_amount,  # Will update after adding items
                    coupon=applied_coupon,
                    notes=random.choice(
                        [None, "Please deliver to reception", "Gift wrap please", "Call before delivery"]),
                    created_at=order_date,
                    updated_at=order_date,
                )

                # Add 1-5 items to the order
                vendor_totals = {}  # Track totals per vendor

                for _ in range(random.randint(1, 5)):
                    product = random.choice(products)

                    # If product has variants, select a random variant
                    variant = None
                    if product.variants.exists():
                        variant = random.choice(product.variants.all())

                    # Determine price (as it was at the time of purchase)
                    if variant:
                        item_price = variant.current_price
                    else:
                        item_price = product.current_price

                    quantity = random.randint(1, 3)
                    item_tax_rate = product.tax_rate
                    item_tax_amount = round(item_price * quantity * (item_tax_rate / 100), 2)
                    item_total = (item_price * quantity) + item_tax_amount

                    # Add item to order
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        variant=variant,
                        quantity=quantity,
                        price=item_price,
                        tax_rate=item_tax_rate,
                        tax_amount=item_tax_amount,
                        total=item_total,
                    )

                    # Update order subtotal and tax
                    subtotal += item_price * quantity
                    tax_amount += item_tax_amount

                    # Track vendor totals
                    vendor = product.vendor
                    if vendor.id not in vendor_totals:
                        vendor_totals[vendor.id] = {
                            'vendor': vendor,
                            'subtotal': decimal.Decimal('0.00'),
                            'tax_amount': decimal.Decimal('0.00'),
                        }

                    vendor_totals[vendor.id]['subtotal'] += item_price * quantity
                    vendor_totals[vendor.id]['tax_amount'] += item_tax_amount

                # Apply discount if coupon is used
                if applied_coupon:
                    if applied_coupon.discount_type == 'percentage':
                        discount_amount = round(subtotal * (applied_coupon.discount_value / 100), 2)
                    else:  # fixed
                        discount_amount = min(applied_coupon.discount_value, subtotal)

                # Update order totals
                total = subtotal + shipping_cost + tax_amount - discount_amount
                order.subtotal = subtotal
                order.tax_amount = tax_amount
                order.discount_amount = discount_amount
                order.total = total
                order.save()

                # Create vendor orders
                for vendor_id, vendor_data in vendor_totals.items():
                    vendor = vendor_data['vendor']
                    vendor_subtotal = vendor_data['subtotal']
                    vendor_tax = vendor_data['tax_amount']

                    # Proportionally split shipping cost and discount
                    vendor_ratio = vendor_subtotal / subtotal if subtotal > 0 else 0
                    vendor_shipping = round(shipping_cost * vendor_ratio, 2)
                    vendor_discount = round(discount_amount * vendor_ratio, 2)

                    # Calculate commission
                    commission_rate = vendor.commission_rate
                    commission_amount = round(vendor_subtotal * (commission_rate / 100), 2)

                    # Calculate total vendor payout amount
                    vendor_total = vendor_subtotal + vendor_tax + vendor_shipping - vendor_discount - commission_amount

                    # Create vendor order
                    vendor_order = VendorOrder.objects.create(
                        order=order,
                        vendor=vendor,
                        status=order_status,
                        subtotal=vendor_subtotal,
                        shipping_cost=vendor_shipping,
                        tax_amount=vendor_tax,
                        commission_amount=commission_amount,
                        total_vendor_amount=vendor_total,
                        tracking_number=f"TRK{random.randint(10000000, 99999999)}" if order_status in ['shipped',
                                                                                                       'delivered'] else None,
                        carrier=random.choice(["FedEx", "UPS", "USPS", "DHL"]) if order_status in ['shipped',
                                                                                                   'delivered'] else None,
                        dispatch_date=order_date + timedelta(days=1) if order_status in ['shipped',
                                                                                         'delivered'] else None,
                        delivery_date=order_date + timedelta(days=3) if order_status == 'delivered' else None,
                    )

                    # Create tracking history
                    statuses = []
                    if order_status == 'pending':
                        statuses = ['pending']
                    elif order_status == 'processing':
                        statuses = ['pending', 'confirmed', 'processing']
                    elif order_status == 'shipped':
                        statuses = ['pending', 'confirmed', 'processing', 'packed', 'shipped']
                    elif order_status == 'delivered':
                        statuses = ['pending', 'confirmed', 'processing', 'packed', 'shipped', 'out_for_delivery',
                                    'delivered']

                    for i, status in enumerate(statuses):
                        OrderTracking.objects.create(
                            vendor_order=vendor_order,
                            status=status,
                            timestamp=order_date + timedelta(hours=i * 8),  # Space out status updates
                            comment=f"Order {status}",
                            updated_by=vendor.user,
                        )

                # Create payment if paid
                if payment_status == 'paid':
                    Payment.objects.create(
                        order=order,
                        amount=total,
                        provider=random.choice(["Stripe", "PayPal", "Razorpay"]),
                        status='completed',
                        transaction_id=f"PAY{random.randint(10000000, 99999999)}",
                        payment_method=payment_method,
                        payment_data={
                            "card_last4": f"{random.randint(1000, 9999)}" if payment_method == 'credit_card' else None,
                            "payment_time": order_date.isoformat()
                        },
                        created_at=order_date,
                    )

                self.stdout.write(f"Created order {order_number} for {user.email}")

        self.stdout.write(self.style.SUCCESS(f'Created orders with items and payments'))

    def create_transactions(self):
        """Create payment transactions and vendor payouts."""
        # Create transactions for all completed payments
        payments = Payment.objects.filter(status='completed')

        for payment in payments:
            # Create transaction record for the payment
            transaction = Transaction.objects.create(
                order=payment.order,
                user=payment.order.user,
                amount=payment.amount,
                status='completed',
                transaction_type='payment',
                payment_method=payment.payment_method,
                provider=payment.provider,
                provider_transaction_id=payment.transaction_id,
                metadata={
                    "payment_id": payment.id,
                    "order_number": payment.order.order_number,
                    "payment_date": payment.created_at.isoformat()
                }
            )

            self.stdout.write(
                f"Created payment transaction {transaction.transaction_id} for order #{payment.order.order_number}")

            # Create vendor payouts for completed orders
            vendor_orders = payment.order.vendor_orders.filter(status__in=['delivered', 'shipped'])

            for vendor_order in vendor_orders:
                # Only create payouts for some vendor orders (randomly)
                if random.choice([True, False, False]):  # 1/3 chance
                    # Create payout
                    payout_status = random.choice(['pending', 'processing', 'completed'])
                    payout_date = None
                    if payout_status == 'completed':
                        payout_date = timezone.now() - timedelta(days=random.randint(1, 30))

                    payout = VendorPayout.objects.create(
                        vendor_order=vendor_order,
                        amount=vendor_order.total_vendor_amount,
                        status=payout_status,
                        payout_date=payout_date,
                        notes=f"Payout for order #{vendor_order.order.order_number}"
                    )

                    # Create transaction for the payout if completed
                    if payout_status == 'completed':
                        payout_transaction = Transaction.objects.create(
                            user=vendor_order.vendor.user,
                            amount=payout.amount,
                            status='completed',
                            transaction_type='payout',
                            payment_method='bank_transfer',
                            provider=random.choice(["Stripe", "PayPal", "Direct"]),
                            provider_transaction_id=f"PAYOUT-{random.randint(100000, 999999)}",
                            metadata={
                                "payout_id": payout.id,
                                "vendor_order_id": vendor_order.id,
                                "vendor_name": vendor_order.vendor.business_name,
                                "order_number": vendor_order.order.order_number
                            }
                        )

                        # Link transaction to payout
                        payout.transaction = payout_transaction
                        payout.save()

                        self.stdout.write(f"Created payout of {payout.amount} for {vendor_order.vendor.business_name}")

        # Create random refund transactions (for ~5% of orders)
        orders = Order.objects.filter(status='delivered', payment_status='paid')
        for order in random.sample(list(orders), k=min(int(orders.count() * 0.05) + 1, orders.count())):
            refund_amount = (order.total * decimal.Decimal(random.uniform(0.1, 0.5))).quantize(decimal.Decimal('0.01'))

            # Create refund record
            refund = Refund.objects.create(
                order=order,
                amount=refund_amount,
                reason=random.choice([
                    "Item damaged during shipping",
                    "Wrong item received",
                    "Item not as described",
                    "Customer changed mind"
                ]),
                status=random.choice(['pending', 'approved', 'completed']),
                transaction_id=f"REF-{random.randint(100000, 999999)}" if random.choice([True, False]) else None
            )

            # Create transaction for completed refunds
            if refund.status == 'completed':
                refund_transaction = Transaction.objects.create(
                    order=order,
                    user=order.user,
                    amount=refund.amount,
                    status='completed',
                    transaction_type='refund',
                    payment_method=order.payment_method,
                    provider=order.payments.first().provider if order.payments.exists() else "Manual",
                    provider_transaction_id=refund.transaction_id,
                    metadata={
                        "refund_id": refund.id,
                        "order_number": order.order_number,
                        "refund_reason": refund.reason
                    }
                )

                self.stdout.write(f"Created refund of {refund.amount} for order #{order.order_number}")

        self.stdout.write(self.style.SUCCESS(f'Created {Transaction.objects.count()} transactions'))
