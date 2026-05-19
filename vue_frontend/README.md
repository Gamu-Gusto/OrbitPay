# Ditheto Accountants Payroll Frontend (Vue.js)

This is the Vue.js frontend for the Ditheto Accountants Payroll and Payslip Generator application. It provides a modern, interactive user interface for inputting payroll details, viewing calculations, and generating payslips.

## Features

*   **Intuitive UI:** A clean and responsive user interface built with Vue.js and Tailwind CSS.
*   **Payroll Input Forms:** Comprehensive forms for employee, company, earnings, and deductions details.
*   **Real-time Calculations:** Displays payroll summary including total earnings, deductions, and net pay.
*   **Payslip Generation:** Integrates with the FastAPI backend to generate and download PDF payslips.
*   **Theme Toggle:** Allows switching between light and dark modes.

## Setup and Installation

1.  **Navigate to the frontend directory:**

    ```bash
    cd vue_frontend
    ```

2.  **Install dependencies:**

    ```bash
    npm install
    ```

## Running the Application

To start the Vue.js development server, run the following command from within the `vue_frontend` directory:

```bash
npm run dev
```

*   The application will typically be accessible at `http://localhost:5173` or `http://localhost:5174` (if port 5173 is in use).
*   Ensure the FastAPI backend is running on `http://localhost:8002` for full functionality.

## Project Structure

*   `src/main.js`: Main entry point for the Vue application.
*   `src/App.vue`: Root Vue component.
*   `src/router/index.js`: Vue Router configuration.
*   `src/views/PayrollView.vue`: The main payroll input and display component.
*   `src/style.css`: Tailwind CSS imports and custom styles.
*   `tailwind.config.js`: Tailwind CSS configuration.
*   `postcss.config.js`: PostCSS configuration.

## Technologies Used

*   Vue.js 3
*   Vite
*   Tailwind CSS
*   Axios (for API communication)
*   Pinia (for state management - though not heavily used in this initial version, it's included for scalability)
*   Vue Router
