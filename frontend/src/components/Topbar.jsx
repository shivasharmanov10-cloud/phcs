
import {
  Menu,
  RefreshCw,
} from "lucide-react";

function Topbar({ setMobileMenuOpen }) {
  const refreshPage = () => {
    window.location.reload();
  };

  return (
    <header className="topbar">

      <button
        className="mobile-menu-button"
        onClick={() => setMobileMenuOpen(true)}
      >
        <Menu size={24} />
      </button>

      <div className="topbar-title">
        <span>PHC INTELLIGENCE /</span>
        <strong>ML COMMAND CENTER</strong>
      </div>

      <div className="topbar-actions">

        <div className="live-status">
          <span></span>
          LIVE
        </div>

        <button
          className="refresh-button"
          onClick={refreshPage}
        >
          <RefreshCw size={17} />
          <span>Refresh</span>
        </button>

      </div>

    </header>
  );
}

export default Topbar;