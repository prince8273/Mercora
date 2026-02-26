# Implementation Plan: CSV Upload Frontend Redesign

## Overview

This plan refactors the DataUpload.jsx component to integrate with the correct backend CSV upload API endpoints (/csv/upload/products, /csv/upload/reviews, /csv/upload/sales). The implementation removes legacy features, adds sales data type support, displays AI analysis results, and updates CSV format examples. This is a frontend-only refactor with no backend modifications.

## Tasks

- [x] 1. Remove legacy code and state variables
  - Remove dataFormat state variable and related UI controls
  - Remove analysisResult, insights, expandedInsights, currentPage, itemsPerPage state variables
  - Remove checkJobStatus, getInventoryAnalysis, getInsights, toggleInsight, handlePageChange, handleItemsPerPageChange functions
  - Remove dashboard stats display UI (total_products, active_products, total_reviews, avg_confidence, total_queries)
  - Remove expandable insights UI and pagination controls
  - Remove Amazon dataset radio option from data type selector
  - Remove JSON file acceptance from file input and file handling logic
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 1.4, 1.5, 1.6_

- [x] 2. Update API endpoint integration
  - [x] 2.1 Update handleUpload function to use /csv/upload/${dataType} endpoint pattern
    - Replace /ingestion/upload/* and /amazon/upload references
    - Construct endpoint as `/csv/upload/${dataType}` where dataType is products, reviews, or sales
    - Ensure FormData construction with file remains unchanged
    - Ensure Content-Type: multipart/form-data header is set
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ]* 2.2 Write unit tests for endpoint mapping
    - Test products dataType maps to /csv/upload/products
    - Test reviews dataType maps to /csv/upload/reviews
    - Test sales dataType maps to /csv/upload/sales
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 3. Add sales data type support
  - [x] 3.1 Add sales radio option to data type selector UI
    - Add radio button with value "sales" and label "Sales Data"
    - Position alongside existing products and reviews options
    - _Requirements: 7.1_

  - [x] 3.2 Add sales CSV format example
    - Create format example showing: product_id, quantity, revenue, date, marketplace columns
    - Include sample data rows matching backend expectations
    - Display when sales data type is selected
    - _Requirements: 7.3_

  - [ ]* 3.3 Write unit tests for sales data type
    - Test sales radio option exists and is selectable
    - Test sales format example displays when sales is selected
    - _Requirements: 7.1, 7.3_

- [x] 4. Update CSV format examples for all data types
  - [x] 4.1 Update products CSV format example
    - Update columns to: sku, name, category, price, currency, marketplace, inventory_level
    - Update sample data to match backend expectations
    - _Requirements: 3.1_

  - [x] 4.2 Update reviews CSV format example
    - Update columns to: product_id, rating, text, source
    - Update sample data to match backend expectations (product_id as UUID)
    - _Requirements: 3.2_

  - [x] 4.3 Implement format example switching logic
    - Update format example display to show correct example based on selected dataType
    - Ensure format updates when dataType selection changes
    - _Requirements: 3.4_

  - [ ]* 4.4 Write unit tests for format examples
    - Test products format displays correct columns
    - Test reviews format displays correct columns
    - Test sales format displays correct columns
    - Test format switches when dataType changes
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 5. Checkpoint - Verify legacy code removal and basic structure
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement AI analysis results display
  - [x] 6.1 Create analysis display section UI
    - Add card-based layout for analysis results
    - Display intent field from response.data.analysis.intent
    - Display confidence score from response.data.analysis.confidence
    - Display agents_used list from response.data.analysis.agents_used
    - Display report text from response.data.analysis.report
    - Use existing CSS classes for consistent styling
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6_

  - [x] 6.2 Add token usage statistics display
    - Display prompt_tokens from response.data.token_usage.prompt_tokens
    - Display completion_tokens from response.data.token_usage.completion_tokens
    - Display total_tokens from response.data.token_usage.total_tokens
    - Format in readable layout within analysis card
    - _Requirements: 2.5_

  - [x] 6.3 Add sales-specific metrics display
    - Display total_revenue from response.data.analysis.total_revenue when dataType is sales
    - Display total_quantity from response.data.analysis.total_quantity when dataType is sales
    - Conditionally render only for sales uploads
    - _Requirements: 7.4, 7.5_

  - [ ]* 6.4 Write unit tests for analysis display
    - Test intent field displays correctly
    - Test confidence score displays correctly
    - Test agents_used list displays correctly
    - Test report text displays correctly
    - Test token usage displays correctly
    - Test sales metrics display only for sales uploads
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 7.4, 7.5_

- [x] 7. Update upload response handling
  - [x] 7.1 Update success message display logic
    - Display products_uploaded count when dataType is products
    - Display reviews_uploaded count when dataType is reviews
    - Display sales_records_uploaded count when dataType is sales
    - Display success message with status from response.data.status
    - Remove references to job_id, records_processed, records_validated, records_rejected
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 7.2 Write unit tests for upload response handling
    - Test products_uploaded displays for products upload
    - Test reviews_uploaded displays for reviews upload
    - Test sales_records_uploaded displays for sales upload
    - Test success message displays when status is 'success'
    - Test legacy fields do not appear in UI
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 8. Implement error handling
  - [x] 8.1 Update error handling in handleUpload catch block
    - Display error detail from err.response?.data?.detail for 400 errors
    - Display authentication error message for 401 errors
    - Display server error message for 500 errors
    - Display connection error message for network errors
    - Use existing error message UI component
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 8.2 Update file validation in handleFileSelect
    - Validate file extension is .csv
    - Display validation error for non-CSV files
    - Reset selectedFile to null on validation failure
    - Clear error state when valid file is selected
    - _Requirements: 5.5_

  - [ ]* 8.3 Write unit tests for error handling
    - Test 400 error displays detail message
    - Test 401 error displays authentication message
    - Test 500 error displays server error message
    - Test network error displays connection message
    - Test non-CSV file displays validation error
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 9. Verify UI/UX consistency
  - [x] 9.1 Verify existing functionality is preserved
    - Test drag-and-drop file upload works
    - Test file selection button works
    - Test upload button shows loading state during upload
    - Verify card-based layout is maintained
    - Verify existing CSS class names are preserved
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 9.2 Write integration tests for UI interactions
    - Test drag-and-drop sets selectedFile correctly
    - Test file input button sets selectedFile correctly
    - Test upload button is disabled when uploading
    - Test CSS classes are present on rendered elements
    - _Requirements: 8.1, 8.2, 8.3, 8.5_

- [ ] 10. Final checkpoint - End-to-end verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- This is a frontend-only refactor - no backend modifications required
- All API endpoints already exist and are functional
- The backend returns AI analysis results that need to be displayed
- Existing UI/UX design and styling should be preserved
- Focus on removing legacy code while adding new analysis display features
