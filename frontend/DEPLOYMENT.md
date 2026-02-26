# Deployment Guide

## Prerequisites

1. Vercel account
2. Backend API deployed and accessible
3. Environment variables configured

## Vercel Deployment

### 1. Install Vercel CLI (Optional)

```bash
npm install -g vercel
```

### 2. Configure Environment Variables in Vercel

Go to your Vercel project settings and add these environment variables:

**Production:**
- `VITE_API_URL`: Your production API URL (e.g., `https://api.yourdomain.com`)
- `VITE_WS_URL`: Your production WebSocket URL (e.g., `wss://api.yourdomain.com`)
- `VITE_ENV`: `production`

**Optional:**
- `VITE_ANALYTICS_ID`: Your analytics tracking ID
- `VITE_SENTRY_DSN`: Your Sentry DSN for error tracking

### 3. Deploy via Git (Recommended)

1. Push your code to GitHub/GitLab/Bitbucket
2. Import the repository in Vercel
3. Vercel will auto-detect the Vite framework
4. Configure the build settings:
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
5. Add environment variables in Vercel dashboard
6. Deploy!

### 4. Deploy via CLI

```bash
cd frontend
vercel --prod
```

Follow the prompts to configure your deployment.

## Build Locally

To test the production build locally:

```bash
# Build
npm run build

# Preview
npm run preview
```

## Environment-Specific Builds

### Development
```bash
npm run dev
```

### Staging
```bash
npm run build -- --mode staging
```

### Production
```bash
npm run build -- --mode production
```

## Post-Deployment Checklist

- [ ] Verify all pages load correctly
- [ ] Test login/logout functionality
- [ ] Check API integration (dashboard, intelligence, pricing)
- [ ] Verify WebSocket connection (or graceful fallback)
- [ ] Test error boundaries (trigger an error to see fallback)
- [ ] Check browser console for errors
- [ ] Test on mobile devices
- [ ] Verify security headers (use securityheaders.com)
- [ ] Test performance (use Lighthouse)

## Troubleshooting

### Build Fails

1. Check Node.js version (should be 16+)
2. Clear node_modules and reinstall: `rm -rf node_modules && npm install`
3. Check for TypeScript/ESLint errors

### API Connection Issues

1. Verify `VITE_API_URL` is set correctly
2. Check CORS settings on backend
3. Verify backend is accessible from frontend domain

### WebSocket Connection Fails

1. Verify `VITE_WS_URL` is set correctly
2. Check if backend supports WebSocket
3. App should gracefully fall back to polling mode

### 404 on Page Refresh

This is handled by the `vercel.json` rewrites. If you're using a different platform:

**Netlify**: Add `_redirects` file:
```
/*    /index.html   200
```

**Apache**: Add `.htaccess`:
```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /index.html [L]
</IfModule>
```

**Nginx**:
```nginx
location / {
  try_files $uri $uri/ /index.html;
}
```

## Performance Optimization

1. **Enable Compression**: Vercel automatically enables gzip/brotli
2. **CDN**: Vercel Edge Network provides global CDN
3. **Caching**: Static assets are cached for 1 year (see vercel.json)
4. **Code Splitting**: Configured in vite.config.js
5. **Image Optimization**: Use Vercel Image Optimization for images

## Monitoring

### Error Tracking (Optional)

Add Sentry for error tracking:

```bash
npm install @sentry/react
```

Configure in `src/main.jsx`:

```javascript
import * as Sentry from "@sentry/react";

if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.VITE_ENV,
  });
}
```

### Analytics (Optional)

Add Google Analytics or similar:

```javascript
// In src/main.jsx or App.jsx
if (import.meta.env.VITE_ANALYTICS_ID) {
  // Initialize analytics
}
```

## Rollback

If deployment fails, Vercel allows instant rollback:

1. Go to Vercel dashboard
2. Select your project
3. Go to "Deployments"
4. Find the previous working deployment
5. Click "Promote to Production"

## Support

- Vercel Docs: https://vercel.com/docs
- Vite Docs: https://vitejs.dev/guide/
- React Router Docs: https://reactrouter.com/
