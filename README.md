# Adaptive E-Commerce Analytics & ETL Intelligence Platform

An end-to-end data engineering and analytics platform that transforms raw e-commerce transaction data into clean, validated data, business metrics, SQL analytics, and actionable insights through an interactive Streamlit dashboard.

## 🚀 Live Application

[Open the Live Application](https://adaptive-ecommerce-analytics-h8hs9eoveyyoaqbwqetfgv.streamlit.app/)

## 📌 Overview

E-commerce data often comes from different sources and may contain inconsistent column names, missing values, duplicate records, invalid dates, and optional fields.

This project provides an adaptive pipeline that accepts e-commerce transaction CSV files, automatically processes the data, stores it in a database, performs analytics, and generates business insights.

### Data Flow

**Raw CSV → Profiling → Schema Detection → Column Mapping → Validation → Cleaning → Transformation → Feature Engineering → SQLite → SQL Analytics → Business Insights → Dashboard**

## ✨ Features

- Raw CSV dataset upload
- Automatic dataset profiling
- Adaptive schema and column detection
- Column mapping with confidence levels
- Data validation and quality scoring
- Duplicate and invalid-data handling
- Data transformation and feature engineering
- SQLite database integration
- SQL-based analytics
- Product and category analytics
- Customer analytics
- RFM customer segmentation
- Regional analytics
- Automated business insights
- SQL query and index performance analysis
- CSV and Excel exports
- Interactive Streamlit dashboard
- Light and Dark mode

## 📊 Business Analytics

The platform can analyze:

- Revenue and sales trends
- Orders and quantity
- Average Order Value
- Product performance
- Category performance
- Customer behavior
- Repeat customers
- RFM segments
- Regional performance
- Profit and profit margin
- Return analysis
- Data quality
- SQL performance

## 🛠️ Technology Stack

- **Python**
- **Pandas & NumPy**
- **SQLite**
- **SQLAlchemy**
- **SQL**
- **Streamlit**
- **Plotly**
- **Pytest**
- **Git & GitHub**

## 🏗️ Project Structure

```text
adaptive-ecommerce-analytics/
│
├── analytics/
├── dashboard/
├── database/
├── etl/
├── sql/
├── tests/
├── utils/
├── config/
├── data/
│
├── app.py
├── generate_sample_data.py
├── requirements.txt
├── README.md
└── LICENSE
