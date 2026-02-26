# E-commerce Intelligence Frontend

Production-grade frontend for AI-powered e-commerce intelligence platform.

## Architecture

Built according to `FRONTEND_ARCHITECTURE.md` and `FRONTEND_ARCHITECTURE_DIAGRAMS.md` specifications.

### Tech Stack

- **Framework**: React 18
- **Build Tool**: Vite 5
- **Routing**: React Router v6
- **State Management**: 
  - React Query (server state)
  - Zustand (client state)
- **HTTP Client**: Axios
- **Real-time**: Socket.IO Client
- **Charts**: Recharts
- **Icons**: Lucide React
- **Styling**: CSS Modules + CSS Variables

## Project Structure

```
src/
├── components/
│   ├── atoms/           # Basic UI elements (Button, Input, etc.)
│   ├── molecules/       # Composite components
│   ├── organisms/       # Complex components (TopBar, SideNav)
│   └── layouts/         # Layout components (AppShell, AuthLayout)
│
├── pages/               # Route pages
│   ├── LoginPage.jsx
│   ├── SignupPage.jsx
│   ├── OverviewPage.jsx
│   ├── IntelligencePage.jsx
│   ├── PricingPage.jsx
│   ├── SentimentPage.jsx
│   ├── ForecastPage.jsx
│   └── SettingsPage.jsx
│
├── contexts/            # React contexts
│   ├── AuthContext.jsx
│   └── ThemeContext.jsx
│
├── lib/                 # Core utilities
│   ├── apiClient.js     # HTTP client with interceptors
│   ├── queryClient.js   # React Query configuration
│   └── websocket.js     # WebSocket manager
│
├── routes/              # Route configuration
│   └── index.jsx
│
├── styles/              # Global styles
│   └── index.css
│
├── App.jsx
└── main.jsx
```

## Getting Started

### Prerequisites

- Node.js 18+ (or 20+ for latest Vite)
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=http://localhost:8000
```

## Features

### Implemented

✅ Authentication (Login/Signup)
✅ Protected routes
✅ App shell layout (TopBar + SideNav)
✅ Theme support (light/dark)
✅ API client with interceptors
✅ React Query setup
✅ WebSocket manager
✅ Responsive design
✅ Overview dashboard (placeholder)
✅ All main pages (placeholders)

### To Be Implemented

- [ ] Intelligence query interface with real-time tracking
- [ ] Pricing analysis with competitor matrix
- [ ] Sentiment analysis with visualizations
- [ ] Demand forecasting with charts
- [ ] Settings page with integrations
- [ ] Amazon Seller API integration UI
- [ ] Real-time WebSocket updates
- [ ] Advanced data visualizations
- [ ] Error boundaries
- [ ] Loading skeletons
- [ ] Toast notifications
- [ ] Command palette (⌘K)

## Development

### Code Style

- Use functional components with hooks
- Follow component hierarchy: atoms → molecules → organisms → pages
- Keep components small and focused
- Use CSS modules for component-specific styles
- Use CSS variables for theming

### State Management

- **Server State**: Use React Query for all API data
- **Client State**: Use Zustand for global UI state
- **Local State**: Use useState/useReducer for component-specific state

### API Integration

All API calls go through the `apiClient` which handles:
- Authentication headers
- Tenant context
- Token refresh
- Error handling
- Request/response interceptors

## Architecture Compliance

This implementation follows the specifications in:
- `FRONTEND_ARCHITECTURE.md` - Detailed architecture document
- `FRONTEND_ARCHITECTURE_DIAGRAMS.md` - Visual architecture diagrams

### Key Architectural Decisions

1. **Component Hierarchy**: Atomic design pattern (atoms → molecules → organisms → pages)
2. **State Management**: Multi-layer approach (server/client/local/derived)
3. **Data Flow**: Unidirectional with React Query caching
4. **Security**: JWT authentication with automatic refresh
5. **Performance**: Code splitting, lazy loading, memoization
6. **Real-time**: WebSocket for live updates

## Deployment

### Production Build

```bash
npm run build
```

Output will be in the `dist/` directory.

### Deployment Targets

- **Vercel**: Recommended (zero-config)
- **Netlify**: Supported
- **CloudFlare Pages**: Supported
- **AWS S3 + CloudFront**: Supported

## Contributing

1. Follow the component structure
2. Use TypeScript types (if migrating to TS)
3. Write tests for critical paths
4. Update documentation

## License

Proprietary - E-commerce Intelligence Platform
