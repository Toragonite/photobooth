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
      {/* Header */}
      <header className="flex justify-between items-center mb-4">
        <div className="w-16">{!hideHomeButton && <HomeButton />}</div>
        <div className="w-16 flex justify-end">
          {!hideLanguageToggle && <LanguageToggle />}
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col">
        <Outlet />
      </main>
    </div>
  );
}
