
import { useEffect, useState } from "react";

import Layout from "./components/Layout";

import Dashboard from "./pages/Dashboard";
import MedicineRisk from "./pages/MedicineRisk";
import DemandForecast from "./pages/DemandForecast";
import Redistribution from "./pages/Redistribution";

import "./App.css";

function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [transitionKey, setTransitionKey] = useState(0);

  /*
   * ----------------------------------------------------------
   * PAGE CHANGE
   * ----------------------------------------------------------
   * Every navigation gets a new key so React creates a fresh
   * page transition instead of simply swapping the content.
   */
  const handlePageChange = (page) => {
    if (page === activePage) return;

    setActivePage(page);
    setTransitionKey((current) => current + 1);
  };

  /*
   * ----------------------------------------------------------
   * PAGE TITLE
   * ----------------------------------------------------------
   */
  useEffect(() => {
    const titles = {
      dashboard: "Dashboard | PHC Intelligence",
      risk: "Medicine Risk | PHC Intelligence",
      forecast: "Demand Forecast | PHC Intelligence",
      redistribution: "Redistribution | PHC Intelligence",
    };

    document.title =
      titles[activePage] ||
      "PHC Intelligence";
  }, [activePage]);

  /*
   * ----------------------------------------------------------
   * PAGE RENDERER
   * ----------------------------------------------------------
   */
  const renderPage = () => {
    switch (activePage) {
      case "dashboard":
        return <Dashboard />;

      case "risk":
        return <MedicineRisk />;

      case "forecast":
        return <DemandForecast />;

      case "redistribution":
        return <Redistribution />;

      default:
        return <Dashboard />;
    }
  };

  return (
    <Layout
      activePage={activePage}
      setActivePage={handlePageChange}
    >
      <main
        key={transitionKey}
        className="page-transition"
        data-page={activePage}
      >
        {renderPage()}
      </main>
    </Layout>
  );
}

export default App;