
import { Menu, RefreshCw, Wifi } from "lucide-react";

function Header({ activePage, onMenuClick }) {
  return (
    <header className="top-header">
      <div className="header-left">
        <button
          className="menu-button"
          onClick={onMenuClick}
          aria-label="Open navigation"
        >
          <Menu size={22} />
        </button>

        <div>
          <div className="breadcrumb">
            PHC INTELLIGENCE <span>/</span> {activePage.toUpperCase()}
          </div>

          <h2>{activePage}</h2>
        </div>
      </div>

      <div className="header-actions">
        <div className="live-status">
          <span className="live-dot" />
          <Wifi size={15} />
          <span>LIVE</span>
        </div>

        <button className="refresh-button">
          <RefreshCw size={16} />
          <span>Refresh</span>
        </button>
      </div>
    </header>
  );
}

export default Header;