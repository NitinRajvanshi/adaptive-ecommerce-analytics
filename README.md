Adaptive E-Commerce Analytics & ETL Intelligence Platform

An end-to-end data engineering and business analytics platform that transforms raw e-commerce transaction data into clean, validated data, SQL-driven analytics, business metrics, and actionable business insights through an interactive Streamlit dashboard.

🚀 Live Application

👉 https://adaptive-ecommerce-analytics-h8hs9eoeyoyaqbwqetfgv.streamlit.app/

📌 Project Overview

E-commerce datasets can come from different sources and often contain inconsistent column names, missing values, duplicate records, invalid data, and optional business fields.

This project provides an adaptive analytics pipeline that can accept different e-commerce transaction CSV datasets and automatically process them through:

Raw CSV → Profiling → Schema Detection → Column Mapping → Validation → Cleaning → Transformation → Feature Engineering → SQLite → SQL Analytics → Business Insights → Dashboard

The goal is to build a reusable analytics platform rather than a dashboard that works with only one fixed dataset.

✨ Key Features
📂 Upload raw e-commerce CSV datasets
🔍 Automatic dataset profiling
🧠 Adaptive schema and column detection
🔗 Automatic column mapping with confidence levels
✅ Data validation and quality scoring
🧹 Duplicate and invalid-data handling
⚙️ Data transformation
🛠️ Feature engineering
🗄️ SQLite database integration
📊 SQL-based business analytics
🛍️ Product and category analytics
👥 Customer analytics
🎯 RFM customer segmentation
🌍 Regional analytics
💡 Automated business insight generation
⚡ SQL query and index performance analysis
📥 CSV and Excel exports
📈 Interactive Streamlit dashboard
🌙 Light and Dark mode
🔄 Data Pipeline
Raw E-Commerce CSV
        ↓
File Validation
        ↓
Dataset Profiling
        ↓
Schema Detection
        ↓
Column Mapping
        ↓
Data Validation
        ↓
Data Cleaning
        ↓
Data Transformation
        ↓
Feature Engineering
        ↓
SQLite Database
        ↓
SQL Analytics
        ↓
Business Metrics
        ↓
Business Insights
        ↓
Interactive Dashboard
📊 Analytics & Business Insights

The platform provides analysis across:

Revenue and sales trends
Total orders and quantities
Average Order Value (AOV)
Product performance
Category performance
Customer revenue and order frequency
Repeat customer analysis
RFM customer segmentation
Regional performance
Profit and profit margin
Return analysis
Data-quality metrics
SQL query performance
🛠️ Technology Stack
Category	Technologies
Programming	Python
Data Processing	Pandas, NumPy
Database	SQLite
Database Layer	SQLAlchemy
Analytics	SQL, Python
Visualization	Plotly
Dashboard	Streamlit
Testing	Pytest
Version Control	Git, GitHub
🏗️ Project Structure
adaptive-ecommerce-analytics/
│
├── analytics/
│   ├── customer_analytics.py
│   ├── insights.py
│   ├── metrics.py
│   ├── performance.py
│   ├── product_analytics.py
│   ├── regional_analytics.py
│   ├── segmentation.py
│   └── sql_queries.py
│
├── dashboard/
├── database/
├── etl/
│   ├── cleaner.py
│   ├── column_mapper.py
│   ├── feature_engineering.py
│   ├── loader.py
│   ├── profiler.py
│   ├── schema_detector.py
│   ├── transformer.py
│   └── validator.py
│
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
💻 Run Locally

Clone the repository:

git clone https://github.com/NitinRajvanshi/adaptive-ecommerce-analytics.git
cd adaptive-ecommerce-analytics

Create a virtual environment:

python -m venv .venv

For Windows CMD:

.venv\Scripts\activate.bat

Install dependencies:

pip install -r requirements.txt

Run the application:

streamlit run app.py

Run the test suite:

pytest -q
🎯 Project Objective

The objective of this project is to demonstrate a complete real-world data analytics workflow:

Data Engineering → Data Quality → Database → SQL Analytics → Business Intelligence → Visualization

The platform combines ETL, data validation, schema adaptation, database management, SQL analytics, customer segmentation, performance analysis, and automated business insights into a single application.

👨‍💻 Author

Nitin Rajvanshi

GitHub:
https://github.com/NitinRajvanshi

📄 License

This project is licensed under the MIT License.
