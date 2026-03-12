# Clean Code Standards for E-commerce Intelligence Agent

## Core Principles

### 1. Clarity Over Cleverness
- Write code that tells a story
- Prefer explicit over implicit
- Choose descriptive names over comments
- Avoid nested ternary operators
- Use clear conditional structures

### 2. Consistency and Patterns
- Follow established project patterns
- Use consistent naming conventions
- Maintain uniform error handling
- Apply consistent formatting

### 3. Functional Preservation
- Never break existing functionality
- Maintain API contracts
- Preserve data integrity
- Keep backward compatibility

### 4. Maintainability Focus
- Write self-documenting code
- Minimize cognitive load
- Reduce complexity
- Enable easy debugging

## Language-Specific Guidelines

### Python Standards
- Use `function` keyword over lambda for named functions
- Prefer explicit return types with type hints
- Use descriptive variable names
- Follow PEP 8 conventions
- Handle errors explicitly with try/catch blocks

### JavaScript/React Standards
- Use ES modules (import/export)
- Prefer `function` keyword over arrow functions for components
- Use explicit return statements
- Apply consistent prop validation
- Handle async operations properly

## Code Structure Guidelines

### Function Design
```python
# Good: Clear, single responsibility
async def calculate_profit_margin(revenue: float, cost: float) -> float:
    """Calculate profit margin percentage."""
    if revenue <= 0:
        return 0.0
    return ((revenue - cost) / revenue) * 100

# Avoid: Nested ternary, unclear logic
margin = ((r - c) / r * 100) if r > 0 else 0 if c == 0 else -100
```

### Error Handling
```python
# Good: Explicit error handling
try:
    result = await api_call()
    return process_result(result)
except APIError as e:
    logger.error(f"API call failed: {e}")
    raise ServiceError("Unable to fetch data")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### Data Processing
```python
# Good: Clear data transformation
def transform_sales_data(raw_data: List[Dict]) -> List[SalesRecord]:
    """Transform raw API data into SalesRecord objects."""
    records = []
    for item in raw_data:
        if is_valid_sales_item(item):
            record = create_sales_record(item)
            records.append(record)
    return records
```

## Refactoring Priorities

### Recently Modified Files
1. `src/services/data_service.py` - Apply clean code principles
2. Database interaction patterns
3. API response handling
4. Error management

### Focus Areas
- Simplify complex conditional logic
- Extract reusable functions
- Improve error messages
- Add type hints where missing
- Reduce function complexity

## Testing Standards
- Write descriptive test names
- Use property-based testing for data validation
- Test error conditions explicitly
- Maintain test readability

## Documentation Guidelines
- Use docstrings for public functions
- Document complex business logic
- Explain non-obvious decisions
- Keep comments current with code changes

## Performance Considerations
- Profile before optimizing
- Cache expensive operations
- Use appropriate data structures
- Monitor database query performance

## Security Standards
- Validate all inputs
- Use parameterized queries
- Handle sensitive data properly
- Log security events

---

*This document guides code quality improvements while preserving functionality and maintaining project consistency.*