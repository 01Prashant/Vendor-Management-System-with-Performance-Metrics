# Vendor-Management-System-with-Performance-Metrics
**Introduction**

This project is developed using Django and Django REST Framework to provide a comprehensive solution for managing vendor profiles, tracking purchase orders, and evaluating vendor performance metrics.

**Features**


1. Vendor Profile Management

      a. Create, retrieve, update, and delete vendor profiles.

      b. Store vendor information including name, contact details, address, and a unique vendor code.

2. Purchase Order Tracking

      a. Track purchase orders with details like PO number, vendor reference, order date, items, quantity, and status.

      b. Filter purchase orders by vendor.

3. Vendor Performance Evaluation

      a. Calculate performance metrics including on-time delivery rate, quality rating average, response time, and fulfilment rate.

      b. Retrieve performance metrics for a specific vendor.

**Setup Instructions**

To run the project on your system, follow these steps:

1.Clone the Repository:

      git clone https://github.com/01Prashant/Vendor-Management-System-with-Performance-Metrics

2.Install Dependencies:

      cd <project_directory>
      pip install -r requirements.txt

3.Database Setup:

      python manage.py migrate

4.Create Superuser (Optional):

      python manage.py createsuperuser

5.Run the Development Server:

      python manage.py runserver

6. Access the API:

      a. Visit http://localhost:8000/admin/ to access the Django admin interface.

**Additional Notes**

1. Ensure that you have Python and pip installed on your system.
2. Token-based authentication is required to access API endpoints. Please refer to the API documentation for authentication instructions.
3. Follow PEP 8 style guidelines for any modifications or contributions to the project.
