import React, { useEffect } from 'react';

interface KioskLayoutProps {
  children: React.ReactNode;
  onExitKiosk?: () => void;
  showSettings?: boolean;
}

const KioskLayout: React.FC<KioskLayoutProps> = ({
  children
}) => {
  // Apply default accessibility settings
  useEffect(() => {
    const root = document.documentElement;
    root.style.setProperty('--kiosk-font-scale', '1');
    root.classList.remove('high-contrast');
  }, []);

  const handleInactivityTimeout = () => {
    // Reset to main menu after 5 minutes of inactivity
    setTimeout(() => {
      window.location.reload();
    }, 5 * 60 * 1000);
  };

  // Inactivity timer
  useEffect(() => {
    let inactivityTimer: NodeJS.Timeout;
    
    const resetTimer = () => {
      clearTimeout(inactivityTimer);
      inactivityTimer = setTimeout(handleInactivityTimeout, 5 * 60 * 1000);
    };

    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    events.forEach(event => {
      document.addEventListener(event, resetTimer, true);
    });

    resetTimer();

    return () => {
      clearTimeout(inactivityTimer);
      events.forEach(event => {
        document.removeEventListener(event, resetTimer, true);
      });
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">


      {/* Main Content */}
      <div className="flex-1" style={{ fontSize: `calc(1rem * var(--kiosk-font-scale, 1))` }}>
        {children}
      </div>


    </div>
  );
};

export default KioskLayout;
