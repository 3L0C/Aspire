# Aspire: Goal-Tracking App

Aspire is a comprehensive goal-tracking web application built on Goal-Setting Theory (GST) principles. Unlike conventional to-do applications that simply track tasks, Aspire connects daily actions to long-term objectives, helping users understand how their incremental efforts contribute to broader ambitions.

## Features

- **Goal Hierarchy**: Create and manage long-term goals, short-term goals, and milestones
- **Task Management**: Track daily tasks and connect them to your broader goals
- **Analytics Dashboard**: Visualize your progress with charts and statistics
- **Goal Network Visualization**: See how your goals and tasks interconnect
- **Data Import/Export**: Backup and transfer your goal data between systems
- **Responsive Design**: Works on both desktop and mobile browsers

## Technology Stack

- **Backend**: Python with Flask framework
- **Database**: SQLAlchemy ORM with SQLite (configurable for other databases)
- **Frontend**: Bootstrap, Chart.js, JavaScript
- **Authentication**: Flask-Login
- **Form Handling**: WTForms
- **Testing**: Pytest

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for cloning the repository)

## Self-Hosting Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/3L0C/Aspire
cd aspire
```

Or download and extract the ZIP file from the project's releases page.

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

On Windows:
```bash
venv\Scripts\activate
```

On macOS and Linux:
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory with the following content:

```
SECRET_KEY=your-secure-random-key-change-this-in-production
DATABASE_URL=sqlite:///aspire.db
```

You can generate a secure random key using Python:

```bash
python -c "import secrets; print(secrets.token_hex(16))"
```

### 6. Run the Application

```bash
python run.py
```

The application will be available at `http://127.0.0.1:5000/`.

### 7. Create an Admin User (Optional)

The first user you register will be automatically created. You can register at `http://127.0.0.1:5000/register`.

## Production Deployment

For production environments, consider the following:

### Using a Production Database

Update the `DATABASE_URL` in your `.env` file:

```
# PostgreSQL
DATABASE_URL=postgresql://username:password@localhost/aspire

# MySQL
DATABASE_URL=mysql://username:password@localhost/aspire
```

### Using a WSGI Server

Install Gunicorn:

```bash
pip install gunicorn
```

Run with Gunicorn:

```bash
gunicorn 'app:create_app()'
```

### Setting Up with Nginx

Here's a basic Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Project Structure

```
aspire/
├── app/                    # Main application package
│   ├── __init__.py         # Application factory
│   ├── analytics/          # Analytics processing
│   ├── data/               # Data models
│   ├── presentation/       # Route handlers and views
│   ├── services/           # Application services
│   ├── static/             # Static files (CSS, JS)
│   └── templates/          # Jinja2 templates
├── tests/                  # Test suite
├── .env                    # Environment variables (create this)
├── run.py                  # Application entry point
└── requirements.txt        # Dependencies
```

## Usage

1. **Register/Login**: Create an account or log in to an existing one
2. **Create Goals**: Start by defining your long-term goals
3. **Add Tasks**: Create daily tasks and link them to your goals
4. **Track Progress**: As you complete tasks, your goal progress updates automatically
5. **Analyze Performance**: Use the analytics dashboard to track your achievements

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Goal-Setting Theory by Edwin Locke and Gary Latham
- Flask and its extensions
- Bootstrap for responsive design
- Chart.js for data visualization
