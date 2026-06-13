# Digital Pantry Management System for Restaurants

Digital Pantry is a full-stack inventory management application designed to help track stock, process grocery bills, and organize sales data in one place. It combines a Flask-based backend with a React and Vite frontend to provide a workflow for managing pantry items, updating quantities, extracting data from uploaded bills, and reviewing business insights through a clean dashboard experience.

## The Problem

Restaurant kitchens lose significant revenue to inventory errors —
manual stock tracking, missed low-stock alerts, and no visibility
into ingredient consumption patterns.

This system replaces manual pantry management with an automated,
data-driven workflow that tracks stock in real time, deducts
ingredients recipe-by-recipe on every sale, and parses grocery
bills automatically using OCR and NLP.

## Features

- Inventory management for pantry items with stock tracking and quantity updates
- Grocery bill OCR to extract item data from uploaded bill images
- Intelligent ingredient matching to connect extracted text with stored inventory records
- Sales summary import and processing for handling structured sales data
- Dashboard views that surface useful inventory and sales insights
- Dedicated frontend workflows for stock entry, inventory review, and sales management
- Organized backend services for OCR, matching, inventory handling, and sales processing

## Tech Stack

- Backend: Python, Flask, OCR, RapidFuzz
- Database: MySQL
- Frontend: React, Vite, Chart.js, Material UI
