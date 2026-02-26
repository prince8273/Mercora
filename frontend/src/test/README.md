# Testing Guide

## Overview
This project uses Vitest and React Testing Library for automated testing.

## Running Tests

### Run all tests in watch mode
```bash
npm test
```

### Run tests once (CI mode)
```bash
npm run test:run
```

### Run tests with UI
```bash
npm run test:ui
```

### Run tests with coverage
```bash
npm run test:coverage
```

## Test Structure

```
src/
├── test/
│   ├── setup.js          # Global test setup
│   ├── utils.jsx         # Test utilities and custom render
│   └── README.md         # This file
├── components/
│   └── molecules/
│       └── MetricCard/
│           ├── MetricCard.jsx
│           └── MetricCard.test.jsx
├── features/
│   └── dashboard/
│       └── components/
│           ├── TrendChart.jsx
│           ├── TrendChart.test.jsx
│           ├── AlertPanel.jsx
│           ├── AlertPanel.test.jsx
│           ├── QuickInsights.jsx
│           └── QuickInsights.test.jsx
└── pages/
    ├── OverviewPage.jsx
    └── OverviewPage.test.jsx
```

## Writing Tests

### Component Tests
Test individual components in isolation:

```javascript
import { describe, it, expect } from 'vitest';
import { render, screen } from '../../../test/utils';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent title="Test" />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
});
```

### Integration Tests
Test pages with mocked hooks:

```javascript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../test/utils';
import MyPage from './MyPage';
import * as hooks from '../hooks/useMyHook';

vi.mock('../hooks/useMyHook');

describe('MyPage', () => {
  it('renders with data', () => {
    hooks.useMyHook.mockReturnValue({
      data: { value: 100 },
      isLoading: false,
    });

    render(<MyPage />);
    expect(screen.getByText('100')).toBeInTheDocument();
  });
});
```

## Test Utilities

### Custom Render
Use `renderWithProviders` from `test/utils.jsx` to render components with all necessary providers:

```javascript
import { render } from '../test/utils';

render(<MyComponent />);
// Automatically wrapped with:
// - QueryClientProvider
// - BrowserRouter
// - ThemeProvider
// - AuthProvider
// - ToastProvider
```

### Mocking

#### Mock API Calls
```javascript
vi.mock('../services/apiService', () => ({
  fetchData: vi.fn().mockResolvedValue({ data: [] }),
}));
```

#### Mock Hooks
```javascript
vi.mock('../hooks/useMyHook', () => ({
  useMyHook: vi.fn(),
}));
```

#### Mock Components
```javascript
vi.mock('recharts', () => ({
  LineChart: ({ children }) => <div data-testid="line-chart">{children}</div>,
}));
```

## Best Practices

1. **Test user behavior, not implementation**
   - Use `screen.getByRole`, `screen.getByLabelText`, `screen.getByText`
   - Avoid testing internal state or implementation details

2. **Use data-testid sparingly**
   - Prefer semantic queries (role, label, text)
   - Only use data-testid when no better option exists

3. **Test loading and error states**
   - Always test loading skeletons
   - Always test error messages
   - Test retry functionality

4. **Mock external dependencies**
   - Mock API calls
   - Mock third-party libraries (Recharts, etc.)
   - Mock WebSocket connections

5. **Keep tests focused**
   - One assertion per test when possible
   - Test one thing at a time
   - Use descriptive test names

## Coverage Goals

- Components: 80%+ coverage
- Pages: 70%+ coverage
- Hooks: 80%+ coverage
- Utilities: 90%+ coverage

## Troubleshooting

### Tests fail with "Cannot find module"
- Check import paths
- Ensure file exists
- Check vitest.config.js alias configuration

### Tests timeout
- Increase timeout in vitest.config.js
- Check for infinite loops
- Ensure async operations complete

### Mock not working
- Ensure mock is defined before import
- Use `vi.clearAllMocks()` in beforeEach
- Check mock implementation

## Phase A Test Checklist

### Component-Level Tests
- [x] MetricCard - renders, loading, trends
- [x] TrendChart - renders, types, loading, error
- [x] AlertPanel - renders, dismiss, loading, empty
- [x] QuickInsights - renders, expand, loading, empty

### Integration Tests
- [x] OverviewPage - full page rendering
- [x] OverviewPage - all sections present
- [x] OverviewPage - loading states
- [x] OverviewPage - error states
- [x] OverviewPage - refresh functionality

### Next Steps
- Add tests for Phase B (Intelligence)
- Add tests for Phase C (Pricing)
- Add tests for Phase D (Real-time)
- Add E2E tests with Playwright
