#!/bin/bash
echo "Generating errors for Flask app..."
for i in {1..10}; do
    curl -s http://localhost:5000/error > /dev/null 2>&1
    curl -s http://localhost:5000/random > /dev/null
    sleep 0.1
done
echo "Error generation complete."