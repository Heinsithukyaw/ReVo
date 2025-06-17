import React, { useState, useEffect } from 'react';
import EnhancedAIChatInterface from './EnhancedAIChatInterface';
import MobileAIChatInterface from './MobileAIChatInterface';

const ResponsiveAIChatInterface = () => {
  const [isMobile, setIsMobile] = useState(false);
  const [windowWidth, setWindowWidth] = useState(0);

  useEffect(() => {
    // Function to check if device is mobile
    const checkIfMobile = () => {
      const width = window.innerWidth;
      setWindowWidth(width);
      
      // Consider mobile if width is less than 768px (tablet breakpoint)
      // or if it's a touch device with small screen
      const isMobileWidth = width < 768;
      const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
      const isSmallTouchDevice = isTouchDevice && width < 1024;
      
      setIsMobile(isMobileWidth || isSmallTouchDevice);
    };

    // Check on mount
    checkIfMobile();

    // Add resize listener
    window.addEventListener('resize', checkIfMobile);

    // Cleanup
    return () => {
      window.removeEventListener('resize', checkIfMobile);
    };
  }, []);

  // Force mobile interface for very small screens
  if (windowWidth > 0 && windowWidth < 640) {
    return <MobileAIChatInterface />;
  }

  // Use mobile interface for touch devices or mobile-sized screens
  if (isMobile) {
    return <MobileAIChatInterface />;
  }

  // Use desktop interface for larger screens
  return <EnhancedAIChatInterface />;
};

export default ResponsiveAIChatInterface;