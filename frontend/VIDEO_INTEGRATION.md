# Video Integration Guide

## Overview
Your custom video `699f54753af92e0806d3f336_11x-hero2-transcode_mp4.mp4` has been successfully integrated into the web application.

## File Location
- **Original**: `E:\Mercora\699f54753af92e0806d3f336_11x-hero2-transcode_mp4.mp4`
- **Web Path**: `/videos/hero-video.mp4`
- **Physical Path**: `frontend/public/videos/hero-video.mp4`

## Integration Points

### 1. ElevenXVideoBackground Component
- **File**: `frontend/src/components/ui/ElevenXVideoBackground.jsx`
- **Usage**: Used in the ModernLandingPage as the hero background
- **Features**: Auto-rotation between videos, fallback support, loading states

### 2. ProfessionalVideoHero Component
- **File**: `frontend/src/components/ui/ProfessionalVideoHero.jsx`
- **Usage**: Alternative hero video component
- **Features**: Professional styling with overlays and status indicators

### 3. CustomVideoPlayer Component
- **File**: `frontend/src/components/ui/CustomVideoPlayer.jsx`
- **Usage**: Reusable video player component
- **Features**: Configurable autoplay, controls, error handling

### 4. VideoDemo Page
- **File**: `frontend/src/pages/VideoDemo.jsx`
- **Route**: `/video-demo`
- **Usage**: Dedicated page to showcase your video

## How to Access

### In the Application
1. **Main Landing Page**: Visit `/modern` - your video plays as the hero background
2. **Video Demo Page**: Visit `/video-demo` - dedicated showcase of your video
3. **Component Usage**: Import and use `CustomVideoPlayer` in any component

### Example Usage
```jsx
import CustomVideoPlayer from '@/components/ui/CustomVideoPlayer';

// Full screen background
<CustomVideoPlayer 
  className="absolute inset-0 w-full h-full"
  autoPlay={true}
  loop={true}
  muted={true}
/>

// With controls
<CustomVideoPlayer 
  className="w-full h-96"
  autoPlay={false}
  controls={true}
  muted={false}
/>
```

## Video Specifications
- **Format**: MP4
- **Size**: ~2.3MB
- **Optimized**: For web playback
- **Fallbacks**: Multiple backup videos for reliability

## Browser Support
- **Primary**: Your custom video loads first
- **Fallback**: Pixabay videos if your video fails
- **Error Handling**: Graceful degradation with poster images

## Performance Notes
- Video is served from the public folder for optimal performance
- Lazy loading and error handling implemented
- Multiple format support for maximum compatibility

## Development
To update or replace the video:
1. Replace `frontend/public/videos/hero-video.mp4`
2. Update poster images if needed
3. Test across different browsers

## Routes
- `/` - Original landing page
- `/modern` - Modern landing with your video background
- `/video-demo` - Dedicated video showcase
- `/demo-beams` - Background beams demo