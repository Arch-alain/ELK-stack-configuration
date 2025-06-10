from flask import Flask, request, jsonify, abort
from elasticapm.contrib.flask import ElasticAPM
import logging
import random
import time
import os
import mysql.connector
from mysql.connector import Error
from http import HTTPStatus

app = Flask(__name__)

# Configure logging to file and console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/var/log/flask/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.debug("Flask app starting")

# Configure Elastic APM
app.config['ELASTIC_APM'] = {
    'SERVICE_NAME': os.getenv('ELASTIC_APM_SERVICE_NAME', 'flask-app'),
    'SERVER_URL': os.getenv('ELASTIC_APM_SERVER_URL', 'http://apm-server:8200'),
    'DEBUG': True,
    'CAPTURE_BODY': 'all',
    'CAPTURE_HEADERS': True
}
try:
    apm = ElasticAPM(app)
    logger.debug("Elastic APM initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Elastic APM: {str(e)}")
# Database configuration
DB_CONFIG = {
    'host': 'mysql',
    'database': 'flask_app',
    'user': 'flask_user',
    'password': 'flask_password'
}

def init_db():
    conn=None
    cursor=None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL UNIQUE,
                author VARCHAR(255) NOT NULL
            )
        ''')
        conn.commit()
        logger.debug("MySQL database initialized successfully")
    except Error as e:
        logger.error(f"MySQL initialization failed: {str(e)}")
        raise
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Custom exceptions
class BookNotFoundError(Exception):
    def __init__(self, book_id):
        self.message = f"Book with ID {book_id} not found"
        super().__init__(self.message)

class BookAlreadyRegisteredError(Exception):
    def __init__(self, title):
        self.message = f"Book with title '{title}' already registered"
        super().__init__(self.message)

class InvalidBookIdError(Exception):
    def __init__(self, book_id):
        self.message = f"Invalid book ID: {book_id}"
        super().__init__(self.message)

# Initialize database
init_db()

@app.route('/')
def home():
    logger.info("Home endpoint accessed")
    return {"message": "Welcome to the Flask App"}

@app.route('/success')
def success():
    logger.info("Success endpoint accessed")
    return {"message": "Success"}, 200
@app.route('/bad-request', methods=['POST'])

def bad_request():
    data = request.get_json()
    if not data or 'value' not in data:
        logger.error("Bad request: missing 'value' in JSON")
        abort(400, description="Missing 'value' in JSON")
    logger.info("Bad request endpoint accessed")
    return {"message": "Valid request", "value": data['value']}

@app.route('/error')
def error():
    logger.error("Error endpoint accessed")
    raise Exception("This is a test error")

@app.route('/slow')
def slow():
    duration = random.uniform(1, 5)
    time.sleep(duration)
    logger.info(f"Slow endpoint accessed, slept for {duration} seconds")
    return {"message": f"Slow response after {duration} seconds"}

@app.route('/generate-error')
def generate_error():
    logger.error("Generated test error for alerting")
    return {"message": "Error generated"}, 500

@app.route('/random')
def random_endpoint():
    if random.random() > 0.7:
        logger.error("Random endpoint failed")
        raise Exception("Random failure")
    logger.info("Random endpoint succeeded")
    return {"message": "Random success"}
@app.route('/books', methods=['POST'])
def add_book():
    conn=None
    cursor=None
    try:
        data = request.get_json()
        if not data or 'title' not in data or 'author' not in data:
            logger.error("Invalid book data: missing title or author")
            abort(400, description="Missing title or author")
        title = data['title']
        author = data['author']
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM books WHERE title = %s", (title,))
        if cursor.fetchone():
            raise BookAlreadyRegisteredError(title)
        cursor.execute("INSERT INTO books (title, author) VALUES (%s, %s)", (title, author))
        conn.commit()
        book_id = cursor.lastrowid
        logger.info(f"Book added: ID={book_id}, Title={title}")
        return {"message": "Book added", "id": book_id}, 201
    except BookAlreadyRegisteredError as e:
        logger.error(f"Add book failed: {str(e)}")
        abort(409, description=str(e))
    except Error as e:
        logger.error(f"MySQL error adding book: {str(e)}")
        abort(500, description="Database error")
    except Exception as e:
        logger.error(f"Unexpected error adding book: {str(e)}")
        abort(500, description="Unexpected error")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/books/<book_id>', methods=['GET'])
def get_book(book_id):
    conn=None
    cursor=None 
    try:
        try:
            book_id = int(book_id)
            if book_id <= 0:
                raise ValueError
        except ValueError:
            raise InvalidBookIdError(book_id)
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, author FROM books WHERE id = %s", (book_id,))
        book = cursor.fetchone()
        if not book:
            raise BookNotFoundError(book_id)
        logger.info(f"Book fetched: ID={book_id}, Title={book[1]}")
        return {"id": book[0], "title": book[1], "author": book[2]}, 200
    except BookNotFoundError as e:
        logger.error(f"Get book failed: {str(e)}")
        abort(404, description=str(e))
    except InvalidBookIdError as e:
        logger.error(f"Get book failed: {str(e)}")
        abort(400, description=str(e))
    except Error as e:
        logger.error(f"MySQL error fetching book: {str(e)}")
        abort(500, description="Database error")
    except Exception as e:
        logger.error(f"Unexpected error fetching book: {str(e)}")
        abort(500, description="Unexpected error")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)




# from flask import Flask, request, jsonify, abort
# from elasticapm.contrib.flask import ElasticAPM
# import logging
# import random
# import time
# import os
# import mysql.connector
# from mysql.connector import Error
# from http import HTTPStatus
# import threading
# from datetime import datetime

# app = Flask(__name__)

# # Configure logging to file and console with JSON format for better parsing
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s %(levelname)s %(name)s: %(message)s',
#     handlers=[
#         logging.FileHandler('/var/log/flask/app.log'),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)
# logger.debug("Flask app starting")

# # Configure Elastic APM
# app.config['ELASTIC_APM'] = {
#     'SERVICE_NAME': os.getenv('ELASTIC_APM_SERVICE_NAME', 'flask-app'),
#     'SERVER_URL': os.getenv('ELASTIC_APM_SERVER_URL', 'http://apm-server:8200'),
#     'DEBUG': True,
#     'CAPTURE_BODY': 'all',
#     'CAPTURE_HEADERS': True
# }

# try:
#     apm = ElasticAPM(app)
#     logger.debug("Elastic APM initialized successfully")
# except Exception as e:
#     logger.error(f"Failed to initialize Elastic APM: {str(e)}")

# # Database configuration with connection pooling
# DB_CONFIG = {
#     'host': 'mysql',
#     'database': 'flask_app',
#     'user': 'flask_user',
#     'password': 'flask_password',
#     'pool_name': 'mypool',
#     'pool_size': 5,  # Small pool to simulate exhaustion
#     'pool_reset_session': True,
#     'connect_timeout': 5,
#     'autocommit': True
# }

# # Simulate connection pool
# connection_pool = None
# pool_exhausted = False
# error_count = 0
# last_error_time = None

# def init_db():
#     global connection_pool
#     try:
#         connection_pool = mysql.connector.pooling.MySQLConnectionPool(**DB_CONFIG)
#         conn = connection_pool.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS books (
#                 id INT AUTO_INCREMENT PRIMARY KEY,
#                 title VARCHAR(255) NOT NULL UNIQUE,
#                 author VARCHAR(255) NOT NULL,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS error_log (
#                 id INT AUTO_INCREMENT PRIMARY KEY,
#                 error_type VARCHAR(100),
#                 error_message TEXT,
#                 timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         conn.commit()
#         cursor.close()
#         conn.close()
#         logger.info("MySQL database initialized successfully with connection pool")
#     except Error as e:
#         logger.error(f"MySQL initialization failed: {str(e)}")
#         raise

# def get_db_connection():
#     global error_count, last_error_time, pool_exhausted
    
#     if pool_exhausted:
#         # Simulate pool exhaustion
#         error_count += 1
#         last_error_time = datetime.now()
#         logger.error(f"DATABASE_CONNECTION_ERROR: Connection pool exhausted. Error count: {error_count}")
#         raise mysql.connector.Error("Connection pool exhausted", errno=2003)
    
#     try:
#         return connection_pool.get_connection()
#     except mysql.connector.Error as e:
#         error_count += 1
#         last_error_time = datetime.now()
#         logger.error(f"DATABASE_CONNECTION_ERROR: Failed to get connection from pool: {str(e)}. Error count: {error_count}")
#         raise

# # Custom exceptions
# class BookNotFoundError(Exception):
#     def __init__(self, book_id):
#         self.message = f"Book with ID {book_id} not found"
#         super().__init__(self.message)

# class BookAlreadyRegisteredError(Exception):
#     def __init__(self, title):
#         self.message = f"Book with title '{title}' already registered"
#         super().__init__(self.message)

# class InvalidBookIdError(Exception):
#     def __init__(self, book_id):
#         self.message = f"Invalid book ID: {book_id}"
#         super().__init__(self.message)

# class DatabaseConnectionError(Exception):
#     def __init__(self, message):
#         self.message = f"Database connection error: {message}"
#         super().__init__(self.message)

# # Initialize database
# init_db()

# @app.route('/')
# def home():
#     logger.info("Home endpoint accessed")
#     return {"message": "Welcome to the Flask App", "pool_exhausted": pool_exhausted, "error_count": error_count}

# @app.route('/health')
# def health():
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("SELECT 1")
#         cursor.fetchone()
#         cursor.close()
#         conn.close()
#         logger.info("Health check passed")
#         return {"status": "healthy", "database": "connected"}, 200
#     except Exception as e:
#         logger.error(f"Health check failed: {str(e)}")
#         return {"status": "unhealthy", "database": "disconnected", "error": str(e)}, 503

# @app.route('/simulate-pool-exhaustion', methods=['POST'])
# def simulate_pool_exhaustion():
#     global pool_exhausted
#     pool_exhausted = True
#     logger.warning("SIMULATION: Database connection pool exhaustion enabled")
#     return {"message": "Pool exhaustion simulation enabled"}, 200

# @app.route('/reset-pool', methods=['POST'])
# def reset_pool():
#     global pool_exhausted, error_count
#     pool_exhausted = False
#     error_count = 0
#     logger.info("SIMULATION: Database connection pool reset")
#     return {"message": "Pool exhaustion simulation disabled, errors reset"}, 200

# @app.route('/stress-test', methods=['POST'])
# def stress_test():
#     """Simulate multiple concurrent database operations to trigger connection issues"""
#     def make_request():
#         try:
#             conn = get_db_connection()
#             cursor = conn.cursor()
#             cursor.execute("SELECT COUNT(*) FROM books")
#             result = cursor.fetchone()
#             cursor.close()
#             conn.close()
#             time.sleep(random.uniform(0.1, 0.5))  # Hold connection briefly
#         except Exception as e:
#             logger.error(f"STRESS_TEST_ERROR: {str(e)}")
    
#     # Create multiple threads to exhaust connection pool
#     threads = []
#     for i in range(10):  # More threads than pool size
#         thread = threading.Thread(target=make_request)
#         threads.append(thread)
#         thread.start()
    
#     for thread in threads:
#         thread.join()
    
#     logger.info("Stress test completed")
#     return {"message": "Stress test completed", "error_count": error_count}

# @app.route('/books', methods=['POST'])
# def add_book():
#     conn = None
#     cursor = None
#     try:
#         data = request.get_json()
#         if not data or 'title' not in data or 'author' not in data:
#             logger.error("VALIDATION_ERROR: Invalid book data - missing title or author")
#             abort(400, description="Missing title or author")
        
#         title = data['title']
#         author = data['author']
        
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         cursor.execute("SELECT id FROM books WHERE title = %s", (title,))
#         if cursor.fetchone():
#             raise BookAlreadyRegisteredError(title)
        
#         cursor.execute("INSERT INTO books (title, author) VALUES (%s, %s)", (title, author))
#         conn.commit()
#         book_id = cursor.lastrowid
        
#         logger.info(f"BOOK_CREATED: ID={book_id}, Title={title}, Author={author}")
#         return {"message": "Book added", "id": book_id}, 201
        
#     except BookAlreadyRegisteredError as e:
#         logger.error(f"BUSINESS_LOGIC_ERROR: {str(e)}")
#         abort(409, description=str(e))
#     except mysql.connector.Error as e:
#         logger.error(f"DATABASE_ERROR: Failed to add book - {str(e)}")
#         abort(503, description="Database service unavailable")
#     except Exception as e:
#         logger.error(f"UNEXPECTED_ERROR: Failed to add book - {str(e)}")
#         abort(500, description="Internal server error")
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()

# @app.route('/books/<book_id>', methods=['GET'])
# def get_book(book_id):
#     conn = None
#     cursor = None
#     try:
#         try:
#             book_id = int(book_id)
#             if book_id <= 0:
#                 raise ValueError
#         except ValueError:
#             raise InvalidBookIdError(book_id)
        
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("SELECT id, title, author, created_at FROM books WHERE id = %s", (book_id,))
#         book = cursor.fetchone()
        
#         if not book:
#             raise BookNotFoundError(book_id)
        
#         logger.info(f"BOOK_RETRIEVED: ID={book_id}, Title={book[1]}")
#         return {
#             "id": book[0], 
#             "title": book[1], 
#             "author": book[2], 
#             "created_at": book[3].isoformat() if book[3] else None
#         }, 200
        
#     except BookNotFoundError as e:
#         logger.error(f"RESOURCE_NOT_FOUND: {str(e)}")
#         abort(404, description=str(e))
#     except InvalidBookIdError as e:
#         logger.error(f"VALIDATION_ERROR: {str(e)}")
#         abort(400, description=str(e))
#     except mysql.connector.Error as e:
#         logger.error(f"DATABASE_ERROR: Failed to retrieve book {book_id} - {str(e)}")
#         abort(503, description="Database service unavailable")
#     except Exception as e:
#         logger.error(f"UNEXPECTED_ERROR: Failed to retrieve book {book_id} - {str(e)}")
#         abort(500, description="Internal server error")
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()

# @app.route('/books', methods=['GET'])
# def list_books():
#     conn = None
#     cursor = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("SELECT id, title, author, created_at FROM books ORDER BY created_at DESC")
#         books = cursor.fetchall()
        
#         result = []
#         for book in books:
#             result.append({
#                 "id": book[0],
#                 "title": book[1], 
#                 "author": book[2],
#                 "created_at": book[3].isoformat() if book[3] else None
#             })
        
#         logger.info(f"BOOKS_LISTED: Found {len(result)} books")
#         return {"books": result, "count": len(result)}, 200
        
#     except mysql.connector.Error as e:
#         logger.error(f"DATABASE_ERROR: Failed to list books - {str(e)}")
#         abort(503, description="Database service unavailable")
#     except Exception as e:
#         logger.error(f"UNEXPECTED_ERROR: Failed to list books - {str(e)}")
#         abort(500, description="Internal server error")
#     finally:
#         if conn and conn.is_connected():
#             cursor.close()
#             conn.close()

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)