import { Outlet, useLocation } from "react-router-dom";
import { HomeButton } from "../common/HomeButton";
import { LanguageToggle } from "../common/LanguageToggle";

export function Layout() {
  const location = useLocation();

  // Hide home button on printing page and home page
  const hideHomeButton = ["/", "/printing"].includes(location.pathname);

  // Hide language toggle on printing and complete pages
  const hideLanguageToggle = ["/printing", "/complete"].includes(
    location.pathname,
  );

  return (
    <div className="page-container safe-top safe-bottom">
      {/* Header - fixed height, always present */}
      <header className="layout-header flex justify-between items-center">
        <div className="w-16 h-11 flex items-center">
          {!hideHomeButton && <HomeButton />}
        </div>
        <div className="w-16 h-11 flex items-center justify-end">
          {!hideLanguageToggle && <LanguageToggle />}
        </div>
      </header>

      {/* Main content - takes remaining space */}
      <main className="layout-main">
        <Outlet />
      </main>
    </div>
  );
}
