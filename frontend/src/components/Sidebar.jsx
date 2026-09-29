
import {
  BarChart3,
  AlertTriangle,
  TrendingUp,
  Truck,
  HeartPulse,
  X,
  Activity,
} from "lucide-react";

function Sidebar({
  activePage,
  setActivePage,
  mobileMenuOpen,
  setMobileMenuOpen,
}) {
  const navigation = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: BarChart3,
    },
    {
      id: "risk",
      label: "Medicine Risk",
      icon: AlertTriangle,
    },
    {
      id: "forecast",
      label: "Demand Forecast",
      icon: TrendingUp,
    },
    {
      id: "redistribution",
      label: "Redistribution",
      icon: Truck,
    },
  ];

  const handleNavigation = (id) => {
    setActivePage(id);
    setMobileMenuOpen(false);
  };

  return (
    <>
      {mobileMenuOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      <aside
        className={`sidebar ${
          mobileMenuOpen ? "sidebar-open" : ""
        }`}
      >

        <div className="sidebar-header">

          <div className="brand-icon">
            <HeartPulse size={24} />
          </div>

          <div>
            <h1>Sehat Saathi</h1>
            <span>Healthcare Intelligence</span>
          </div>

          <button
            className="mobile-close"
            onClick={() => setMobileMenuOpen(false)}
          >
            <X size={22} />
          </button>

        </div>

        <nav className="sidebar-nav">

          {navigation.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.id}
                className={`nav-item ${
                  activePage === item.id
                    ? "nav-item-active"
                    : ""
                }`}
                onClick={() =>
                  handleNavigation(item.id)
                }
              >

                <Icon size={20} />

                <span>{item.label}</span>

                {activePage === item.id && (
                  <span className="nav-arrow">›</span>
                )}

              </button>
            );
          })}

        </nav>

        <div className="sidebar-bottom">

          <div className="system-status">

            <div className="status-dot"></div>

            <div>
              <strong>System Online</strong>
              <span>ML services connected</span>
            </div>

          </div>

          <div className="federated-info">
            <Activity size={16} />
            Federated healthcare intelligence
          </div>

        </div>

      </aside>
    </>
  );
}

export default Sidebar;