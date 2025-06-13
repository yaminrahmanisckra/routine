# Routine Maker

A Flask-based web application for creating and managing daily routines.

## Features

- User authentication and authorization
- Create and manage daily routines
- Track routine completion
- User-friendly interface

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/routine-maker.git
cd routine-maker
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

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Running the Application

1. Activate the virtual environment if not already activated:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Run the Flask application:
```bash
flask run
```

The application will be available at `http://localhost:5000`

## Project Structure

```
routine-maker/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   └── templates/
├── migrations/
├── venv/
├── .env
├── .gitignore
├── app.py
├── config.py
└── requirements.txt
```

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 