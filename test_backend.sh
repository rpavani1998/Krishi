#!/bin/bash
curl -X POST "http://localhost:8000/api/v1/harvest/decision" \
     -H "Content-Type: application/json" \
     -d '{
           "crop": "Tomato",
           "quantity": 50,
           "location": "Madanapalle",
           "latitude": 13.55,
           "longitude": 78.50,
           "harvest_date": "2023-10-27",
           "storage_condition": "open"
         }'
