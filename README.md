# Multi-Vendor E-Commerce Marketplace

A scalable, feature-rich multivendor e-commerce platform built with Django. This platform enables third-party sellers to list and manage their products while providing a seamless shopping experience for buyers.

## System Architecture

This marketplace is built using Django's MVT (Model-View-Template) architecture with a modular approach for scalability:

- **Frontend**: HTML/CSS/JavaScript with Django templates
- **Backend**: Django 
- **Database**: Configured for MySQL in production, SQLite for development
- **Containerization**: Docker support for easy deployment

## Core Components

The application is organized into the following core modules:

### Accounts Module
- Custom user model supporting both regular customers and vendors
- Profile management including address book functionality
- Authentication with multiple options

### Products Module
- Comprehensive product catalog with categories, attributes, and variants
- Review and Q&A system
- Advanced filtering and search capabilities

### Vendors Module
- Vendor registration and profile management
- Product listing and inventory management
- Sales analytics and reporting

### Cart Module
- Interactive shopping cart with save-for-later functionality
- Real-time price calculations

### Orders Module
- Multi-vendor order processing
- Order tracking and status updates
- Coupon system for discounts

### Payments Module
- Multiple payment method support
- Transaction management
- Vendor payout system

## Features

### For Buyers

- User registration with email, phone, and social login
- Comprehensive product search and filtering
- Shopping cart and wishlist management
- Secure checkout process with multiple payment options
- Order tracking and history
- Product reviews and questions
- Personal address book management

### For Vendors

- Dedicated vendor dashboard
- Product management (add, edit, remove listings)
- Inventory tracking
- Order processing and fulfillment
- Sales analytics and reporting
- Commission rate visibility
- Secure payout system

### For Administrators

- Platform-wide analytics dashboard
- User and vendor management
- Product category/attribute management
- Order oversight and intervention capabilities
- Commission structure configuration
- Coupon and promotion management

## Development Setup

### Prerequisites
- Python 3.12+
- Docker and Docker Compose (optional, for containerized setup)
- Virtual environment tool (recommended)

### Local Setup

1. Clone the repository:
   ```
   git clone https://github.com/indranandjha1993/marketplace.git
   cd marketplace
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```
   cp .env.template .env
   # Edit .env file with your configuration
   ```

5. Apply migrations:
   ```
   python manage.py migrate
   ```
   
6. Create a superuser:
   ```
   docker-compose exec web python manage.py createsuperuser
    ```

7. Seed database with sample data (optional):
   ```
   python manage.py seed_database
   ```

8. Run the development server:
   ```
   python manage.py runserver
   ```

### Docker Setup

1. Build and run using Docker Compose:
   ```
   docker-compose up --build
   ```

2. Access the application at http://localhost:8000

## Testing

Run the test suite:
- Personalized product search with advanced filters
- Detailed product pages with images, videos, descriptions, and reviews
- Shopping cart, wishlist, and secure checkout
- Multiple payment options (credit/debit cards, UPI, wallets, COD)
- Order tracking and efficient returns/refunds mechanism

### For Sellers

- Dedicated vendor dashboards
- Product listing management
- Order management and invoice generation
- Customizable storefronts
- Integrated shipping and logistics support

## Tech Stack

- **Frontend**: Bootstrap, Alpine.js
- **Backend**: Django
- **Database**: MySQL for transactional data, Redis for caching
- **Payment Integration**: Stripe, Razorpay, PayPal
- **Containerization**: Docker
- **Deployment**: Docker Compose, Nginx for reverse proxy
- **Testing**: Pytest, Factory
- **Version Control**: Git
- **Documentation**: Markdown

## Project Structure

```
marketplace/
├── accounts/            # User authentication and profiles
├── cart/                # Shopping cart functionality
├── media/               # User-uploaded content
├── marketplace/         # Project settings
├── orders/              # Order processing
├── payments/            # Payment integration
├── products/            # Product catalog
├── static/              # Static assets
├── templates/           # HTML templates
├── vendors/             # Vendor management
├── .env.template        # Environment variables template
├── docker-compose.yml   # Docker configuration
├── Dockerfile           # Docker build instructions
├── manage.py            # Django management script
├── README.md            # Project documentation
└── requirements.txt     # Python dependencies
```

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a pull request

## License

This project is licensed under the MIT License—see the LICENSE file for details.

## Acknowledgements

- [Django](https://www.djangoproject.com/)
- [Bootstrap](https://getbootstrap.com/)
- [Alpine.js](https://alpinejs.dev/)
- [Stripe](https://stripe.com/)
- [Razorpay](https://razorpay.com/)
