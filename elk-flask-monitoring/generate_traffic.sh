#!/bin/bash
echo "Generating traffic for Flask app..."
for i in {1..20}; do
    curl -s http://localhost:5000/ > /dev/null
    curl -s http://localhost:5000/success > /dev/null
    curl -s http://localhost:5000/slow > /dev/null
    curl -s http://localhost:5000/error > /dev/null 2>&1
    curl -s http://localhost:5000/random > /dev/null
    sleep 0.5
done
echo "Traffic generation complete."