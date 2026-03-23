import React from 'react';
import { Link } from 'react-router-dom';

const EcommerceLogo = ({ className = "", size = "default", clickable = true }) => {
  const sizeClasses = {
    small: "text-lg gap-1",
    default: "text-2xl gap-2", 
    large: "text-3xl gap-3"
  };

  const iconSizes = {
    small: "w-6 h-6 text-sm",
    default: "w-8 h-8 text-lg",
    large: "w-10 h-10 text-xl"
  };

  const content = (
    <>
      <div className={`bg-white rounded-lg flex items-center justify-center ${iconSizes[size]}`}>
        <span className="text-stone-900 font-bold">E</span>
      </div>
      <span>Ecommerce Intelligence</span>
    </>
  );

  if (!clickable) {
    return (
      <div className={`text-white font-bold flex items-center ${sizeClasses[size]} ${className}`}>
        {content}
      </div>
    );
  }

  return (
    <Link 
      to="/" 
      className={`text-white font-bold flex items-center ${sizeClasses[size]} ${className} no-underline hover:opacity-90 transition-opacity cursor-pointer`}
      style={{ textDecoration: 'none' }}
    >
      {content}
    </Link>
  );
};

export default EcommerceLogo;