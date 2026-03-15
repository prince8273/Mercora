import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

function FloatingPaths({ position }) {
  const paths = Array.from({ length: 12 }, (_, i) => ({
    id: i,
    d: `M-${200 - i * 20 * position} -${100 + i * 30}C-${200 - i * 20 * position} -${100 + i * 30} -${100 - i * 20 * position} ${200 - i * 20} ${300 - i * 20 * position} ${400 - i * 30}C${500 - i * 20 * position} ${500 - i * 30} ${600 - i * 20 * position} ${600 - i * 30} ${600 - i * 20 * position} ${600 - i * 30}`,
    width: 1 + i * 0.1,
  }));

  return (
    <div className="absolute inset-0 pointer-events-none">
      <svg
        className="w-full h-full"
        viewBox="0 0 800 600"
        fill="none"
      >
        <defs>
          <linearGradient id={`gradient-${position}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.6" />
            <stop offset="50%" stopColor="#8b5cf6" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.6" />
          </linearGradient>
        </defs>
        {paths.map((path) => (
          <motion.path
            key={path.id}
            d={path.d}
            stroke={`url(#gradient-${position})`}
            strokeWidth={path.width}
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ 
              pathLength: 1,
              opacity: [0, 0.8, 0.3, 0.8, 0.2]
            }}
            transition={{
              pathLength: {
                duration: 8 + path.id * 0.5,
                ease: "easeInOut",
                repeat: Infinity,
                delay: path.id * 0.3
              },
              opacity: {
                duration: 6 + path.id * 0.3,
                ease: "easeInOut", 
                repeat: Infinity,
                repeatType: "reverse",
                delay: path.id * 0.2
              }
            }}
          />
        ))}
      </svg>
    </div>
  );
}

export function BackgroundPaths({ title = "Ecommerce Intelligence" }) {
  const words = title.split(" ");
  const navigate = useNavigate();

  const handleButtonClick = () => {
    navigate('/landing');
  };

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center overflow-hidden bg-slate-900">
      {/* Animated Background Paths */}
      <div className="absolute inset-0">
        <FloatingPaths position={1} />
        <FloatingPaths position={-1} />
      </div>
      
      {/* Content */}
      <div className="relative z-10 container mx-auto px-4 text-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 2 }}
          className="max-w-4xl mx-auto"
        >
          <h1 className="text-5xl sm:text-7xl md:text-8xl font-bold mb-8 tracking-tighter text-white">
            {words.map((word, wordIndex) => (
              <span
                key={wordIndex}
                className="inline-block mr-4 last:mr-0"
              >
                {word.split("").map((letter, letterIndex) => (
                  <motion.span
                    key={`${wordIndex}-${letterIndex}`}
                    initial={{ y: 100, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{
                      delay: wordIndex * 0.1 + letterIndex * 0.03,
                      type: "spring",
                      stiffness: 150,
                      damping: 25,
                    }}
                    className="inline-block"
                  >
                    {letter}
                  </motion.span>
                ))}
              </span>
            ))}
          </h1>
          
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 1.2 }}
            className="inline-block"
          >
            <button
              onClick={handleButtonClick}
              className="group px-8 py-4 bg-white/10 hover:bg-white/20 text-white border border-white/20 rounded-2xl backdrop-blur-sm transition-all duration-300 hover:scale-105"
            >
              <span className="mr-3">Discover Excellence</span>
              <span className="group-hover:translate-x-1 transition-transform duration-300 inline-block">
                →
              </span>
            </button>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}

export default BackgroundPaths;