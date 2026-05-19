# Ditheto Accountants Payroll API (FastAPI Backend)

This is the FastAPI backend for the Ditheto Accountants Payroll and Payslip Generator application. It handles the core business logic for payroll calculations and generates PDF payslips.

## Features

*   **Payroll Calculation:** Calculates PAYE (Pay As You Earn), UIF (Unemployment Insurance Fund), total earnings, total deductions, and net pay based on South African tax regulations.
*   **Payslip Generation:** Generates professional PDF payslips using `reportlab`.
*   **CORS Enabled:** Configured to allow requests from the Vue.js frontend.

## Setup and Installation

1.  **Navigate to the backend directory:**

    ```bash
    cd fastapi_app
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```
    (If `requirements.txt` is not present, you can generate it using `pip freeze > requirements.txt` after installing the necessary packages: `pip install fastapi uvicorn reportlab pydantic`)

## Running the Application

To start the FastAPI server, run the following command from within the `fastapi_app` directory:

```bash
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

*   The API will be accessible at `http://localhost:8002`.
*   The `--reload` flag enables auto-reloading on code changes (useful for development).

## API Endpoints

*   **`POST /calculate-payroll`**
    *   **Description:** Calculates PAYE, UIF, total earnings, total deductions, and net pay.
    *   **Request Body:** `PayrollInput` (JSON object containing employee, company, period, earnings, and deduction details).
    *   **Response Body:** `PayslipData` (JSON object with all calculated financial figures).

*   **`POST /generate-payslip`**
    *   **Description:** Generates a PDF payslip.
    *   **Request Body:** `PayslipData` (JSON object containing all data required for the payslip, typically obtained from `/calculate-payroll`).
    *   **Response Body:** `application/pdf` (binary content of the PDF file).

## Data Models

Refer to `models.py` for the detailed Pydantic data models (`EmployeeDetails`, `CompanyDetails`, `PayrollInput`, `PayslipData`) used for request and response validation.
