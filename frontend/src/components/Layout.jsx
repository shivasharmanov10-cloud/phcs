
import { useState } from "react";

import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

function Layout({
  activePage,
  setActivePage,
  children,
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="app-shell">

      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
        mobileMenuOpen={mobileMenuOpen}
        setMobileMenuOpen={setMobileMenuOpen}
      />

      <div className="main-area">

        <Topbar
          setMobileMenuOpen={setMobileMenuOpen}
        />

        <main className="page-container">
          {children}
        </main>

      </div>

    </div>
  );
}

export default Layout;