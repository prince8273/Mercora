# Requirements Document

## Introduction

This feature redesigns the frontend CSV upload functionality to properly integrate with the existing backend /csv API endpoints. The backend provides AI-powered analysis using the LLM reasoning engine for products, reviews, and sales data. The current frontend DataUpload.jsx component uses incorrect endpoints (/ingestion/upload/* and /amazon/upload) that do not exist. This redesign will update the frontend to use the correct /csv/* endpoints while maintaining the existing UI/UX design.

## Glossary

- **DataUpload_Component**: The React component (DataUpload.jsx) responsible for CSV file upload and analysis display
- **CSV_Upload_API**: The backend API endpoints at /csv/upload/products, /csv/upload/reviews, and /csv/upload/sales
- **LLM_Analysis**: AI-powered analysis results returned by the backend including intent, confidence, agents used, report, and token usage
- **Upload_Response**: The JSON response from the backend containing status, upload counts, analysis data, and token usage
- **Data_Type**: The category of CSV data being uploaded (products, reviews, or sales)
- **Format_Example**: Sample CSV structure showing required columns for each data type

## Requirements

### Requirement 1: Update API Endpoint Integration

**User Story:** As a developer, I want the frontend to use the correct backend endpoints, so that CSV uploads work properly with the existing API

#### Acceptance Criteria

1. THE DataUpload_Component SHALL send product CSV uploads to /csv/upload/products
2. THE DataUpload_Component SHALL send review CSV uploads to /csv/upload/reviews
3. THE DataUpload_Component SHALL send sales CSV uploads to /csv/upload/sales
4. THE DataUpload_Component SHALL remove all references to /ingestion/upload/* endpoints
5. THE DataUpload_Component SHALL remove all references to /amazon/upload endpoints
6. THE DataUpload_Component SHALL remove the Amazon dataset format option from the UI

### Requirement 2: Display AI Analysis Results

**User Story:** As a user, I want to see AI-powered analysis insights from my CSV uploads, so that I can understand the data patterns and recommendations

#### Acceptance Criteria

1. WHEN an Upload_Response is received, THE DataUpload_Component SHALL display the analysis intent field
2. WHEN an Upload_Response is received, THE DataUpload_Component SHALL display the analysis confidence score
3. WHEN an Upload_Response is received, THE DataUpload_Component SHALL display the list of agents used
4. WHEN an Upload_Response is received, THE DataUpload_Component SHALL display the analysis report text
5. WHEN an Upload_Response is received, THE DataUpload_Component SHALL display the token usage statistics
6. THE DataUpload_Component SHALL format the LLM_Analysis data in a readable card-based layout

### Requirement 3: Provide CSV Format Examples

**User Story:** As a user, I want to see the correct CSV format for each data type, so that I can prepare my files correctly

#### Acceptance Criteria

1. THE DataUpload_Component SHALL display a Format_Example for products CSV with columns: sku, name, category, price, currency, marketplace, inventory_level
2. THE DataUpload_Component SHALL display a Format_Example for reviews CSV with columns: product_id, rating, text, source
3. THE DataUpload_Component SHALL display a Format_Example for sales CSV with columns: product_id, quantity, revenue, date, marketplace
4. WHEN the Data_Type selection changes, THE DataUpload_Component SHALL update the visible Format_Example to match the selected type

### Requirement 4: Handle Upload Responses

**User Story:** As a user, I want to see clear feedback about my upload status, so that I know if the operation succeeded or failed

#### Acceptance Criteria

1. WHEN a product upload succeeds, THE DataUpload_Component SHALL display the products_uploaded count from the Upload_Response
2. WHEN a review upload succeeds, THE DataUpload_Component SHALL display the reviews_uploaded count from the Upload_Response
3. WHEN a sales upload succeeds, THE DataUpload_Component SHALL display the sales_records_uploaded count from the Upload_Response
4. WHEN an upload succeeds, THE DataUpload_Component SHALL display a success message with status information
5. THE DataUpload_Component SHALL remove references to job_id, records_processed, records_validated, and records_rejected fields

### Requirement 5: Implement Error Handling

**User Story:** As a user, I want to see clear error messages when uploads fail, so that I can fix issues and retry

#### Acceptance Criteria

1. WHEN the backend returns a 400 error, THE DataUpload_Component SHALL display the error detail message
2. WHEN the backend returns a 401 error, THE DataUpload_Component SHALL display an authentication error message
3. WHEN the backend returns a 500 error, THE DataUpload_Component SHALL display a server error message
4. WHEN a network error occurs, THE DataUpload_Component SHALL display a connection error message
5. IF a non-CSV file is selected, THEN THE DataUpload_Component SHALL display a validation error before upload

### Requirement 6: Remove Legacy Features

**User Story:** As a developer, I want to remove unused code and features, so that the codebase is clean and maintainable

#### Acceptance Criteria

1. THE DataUpload_Component SHALL remove the dataFormat state variable and related UI controls
2. THE DataUpload_Component SHALL remove the checkJobStatus function
3. THE DataUpload_Component SHALL remove the getInventoryAnalysis function
4. THE DataUpload_Component SHALL remove the getInsights function
5. THE DataUpload_Component SHALL remove JSON file upload support
6. THE DataUpload_Component SHALL remove the analysisResult state and related dashboard stats display
7. THE DataUpload_Component SHALL remove the insights state and expandable insights UI

### Requirement 7: Add Sales Data Type Support

**User Story:** As a user, I want to upload sales data CSV files, so that I can get demand forecast analysis

#### Acceptance Criteria

1. THE DataUpload_Component SHALL add a sales radio option to the data type selector
2. WHEN sales data type is selected, THE DataUpload_Component SHALL use the /csv/upload/sales endpoint
3. WHEN sales data type is selected, THE DataUpload_Component SHALL display the sales Format_Example
4. WHEN a sales upload succeeds, THE DataUpload_Component SHALL display total_revenue from the Upload_Response
5. WHEN a sales upload succeeds, THE DataUpload_Component SHALL display total_quantity from the Upload_Response

### Requirement 8: Maintain UI/UX Consistency

**User Story:** As a user, I want the upload interface to remain familiar and easy to use, so that I can continue my workflow without relearning

#### Acceptance Criteria

1. THE DataUpload_Component SHALL preserve the existing drag-and-drop file upload functionality
2. THE DataUpload_Component SHALL preserve the existing file selection button
3. THE DataUpload_Component SHALL preserve the existing upload button with loading state
4. THE DataUpload_Component SHALL preserve the existing card-based layout design
5. THE DataUpload_Component SHALL preserve the existing CSS styling and class names
