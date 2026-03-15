import React from 'react';

const Logo11x = ({ className = "" }) => {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* 11x style logo */}
      <div className="flex items-center">
        <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
          <div className="text-stone-900 font-bold text-lg">11</div>
        </div>
        <div className="text-white text-xl font-bold ml-2">x</div>
      </div>
    </div>
  );
};

export default Logo11x;