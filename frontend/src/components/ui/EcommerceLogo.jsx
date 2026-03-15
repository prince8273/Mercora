import React from 'react';

const EcommerceLogo = ({ className = "", size = "default" }) => {
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

  return (
    <div className={`text-white font-bold flex items-center ${sizeClasses[size]} ${className}`}>
      <div className={`bg-white rounded-lg flex items-center justify-center ${iconSizes[size]}`}>
        <span className="text-stone-900 font-bold">E</span>
      </div>
      <span>Ecommerce Intelligence</span>
    </div>
  );
};

export default EcommerceLogo;