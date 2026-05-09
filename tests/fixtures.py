"""
Test fixture: basic Python project.
"""

SAMPLE_REPO_STRUCTURE = {
    "src/main.py": """
def hello(name):
    '''Say hello to someone.'''
    return f"Hello, {name}!"

def process_data(data):
    '''Process data without validation.'''
    # TODO: Add input validation
    return data.upper()
""",
    "src/auth.py": """
import hashlib

def authenticate(username, password):
    '''Authenticate a user.'''
    # WARNING: Never use SHA256 for passwords!
    hashed = hashlib.sha256(password.encode()).hexdigest()
    return hashed == username

def get_user_from_db(user_id):
    '''Get user from database.'''
    # SQL injection vulnerability!
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query
""",
    "tests/test_main.py": """
import pytest
from src.main import hello, process_data

def test_hello():
    assert hello("World") == "Hello, World!"

def test_process_data():
    assert process_data("hello") == "HELLO"
""",
    "README.md": """
# Sample Project

This is a test project for Bread Crumb.

## Setup
```
pip install -r requirements.txt
```

## Running Tests
```
pytest
```
""",
}
