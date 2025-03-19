# Multi-Vendor E-Commerce Marketplace

A scalable, feature-rich multi-vendor e-commerce platform built with Django. This platform enables third-party sellers
to list and manage their products while providing a seamless shopping experience for buyers.

## Features

### For Buyers

- User registration with email, phone, and social login
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

## Installation and Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.10 or higher (for local development)

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/indranandjha1993/marketplace.git
   cd marketplace
   ```

2. Create environment variables file:
   ```bash
   cp .env.template .env
   ```
   Edit the `.env` file and set appropriate values.

3. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

4. Create a superuser:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. Access the application:
    - Website: http://localhost:8000
    - Admin panel: http://localhost:8000/admin

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/marketplace.git
   cd marketplace
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create environment variables file:
   ```bash
   cp .env.template .env
   ```
   Edit the `.env` file and set appropriate values.

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Start the development server:
   ```bash
   python manage.py runserver
   ```

8. Access the application:
    - Website: http://localhost:8000
    - Admin panel: http://localhost:8000/admin

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

## Deployment

### Production Deployment

1. Update the `.env` file with production settings:
    - Set `DEBUG=False`
    - Update `ALLOWED_HOSTS` with your domain
    - Configure production database settings
    - Set up email settings
    - Configure payment gateway credentials

2. Set up static and media files storage:
    - For AWS S3, configure the AWS settings in `.env`
    - For local storage, make sure your web server is configured to serve files from the appropriate directories

3. Build and deploy with Docker:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Django](https://www.djangoproject.com/)
- [Bootstrap](https://getbootstrap.com/)
- [Alpine.js](https://alpinejs.dev/)
- [Stripe](https://stripe.com/)
- [Razorpay](https://razorpay.com/)
