# BackgroundBeams Component

A React component that creates animated gradient beams in the background using framer-motion.

## Usage

```tsx
import { BackgroundBeams } from "@/components/ui/background-beams";

export function MyComponent() {
  return (
    <div className="relative h-screen w-full bg-neutral-950">
      <div className="relative z-10">
        {/* Your content here */}
        <h1>Your Content</h1>
      </div>
      <BackgroundBeams />
    </div>
  );
}
```

## Demo

To test the BackgroundBeams component, visit: `/demo-beams`

This will show a complete demo with:
- Dark background (bg-neutral-950)
- Animated gradient beams
- Sample form with Input and Button components
- Proper z-index layering

## Props

- `className?: string` - Optional additional CSS classes

## Features

- 36 animated SVG paths with gradient colors
- Infinite looping animations with random delays
- Responsive design
- TypeScript support
- Tailwind CSS integration

## Dependencies

- framer-motion
- Tailwind CSS
- React 18+