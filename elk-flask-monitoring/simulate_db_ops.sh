#!/bin/bash
echo "Simulating MySQL database operations..."
# Add books
curl -X POST http://localhost:5000/books -H "Content-Type: application/json" -d '{"title":"The Great Gatsby","author":"F. Scott Fitzgerald"}'
curl -X POST http://localhost:5000/books -H "Content-Type: application/json" -d '{"title":"The Great Gatsby","author":"F. Scott Fitzgerald"}' # Duplicate
curl -X POST http://localhost:5000/books -H "Content-Type: application/json" -d '{"author":"No Title"}' # Invalid
# Fetch books
curl http://localhost:5000/books/1
curl http://localhost:5000/books/999 # Not found
curl http://localhost:5000/books/invalid # Invalid ID
# More errors
for i in {1..3}; do
    curl -X POST http://localhost:5000/books -H "Content-Type: application/json" -d '{"title":"The Great Gatsby","author":"F. Scott Fitzgerald"}'
    curl http://localhost:5000/books/999
    curl http://localhost:5000/books/invalid
    sleep 0.1
done
echo "Simulation complete."