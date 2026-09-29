
import { useEffect, useMemo, useState } from "react";

import {
  ArrowRight,
  Boxes,
  Building2,
  CheckCircle2,
  ChevronDown,
  Clock3,
  MapPin,
  Package,
  RefreshCw,
  Search,
  Truck,
  AlertTriangle,
} from "lucide-react";

function Redistribution() {
  const API_URL = "http://127.0.0.1:8000";

  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [selectedMedicine, setSelectedMedicine] = useState("all");
  const [selectedSource, setSelectedSource] = useState("all");
  const [selectedDestination, setSelectedDestination] =
    useState("all");

  const loadRedistribution = async (showRefresh = false) => {
    try {
      if (showRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      const response = await fetch(
        `${API_URL}/api/ml/redistribution`
      );

      if (!response.ok) {
        throw new Error(
          `Redistribution API returned ${response.status}`
        );
      }

      const result = await response.json();

      const rows = Array.isArray(result?.data)
        ? result.data
        : [];

      setRecommendations(rows);
      setError("");
    } catch (err) {
      console.error(
        "Redistribution loading error:",
        err
      );

      setError(
        "Unable to load redistribution recommendations from the AI backend."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadRedistribution();
  }, []);

  // ---------------------------------------------------------
  // DYNAMIC FILTER OPTIONS
  // ---------------------------------------------------------

  const medicines = useMemo(() => {
    return [
      ...new Set(
        recommendations
          .map((item) => item.medicine_name)
          .filter(Boolean)
      ),
    ].sort();
  }, [recommendations]);

  const sourcePHCs = useMemo(() => {
    return [
      ...new Set(
        recommendations
          .map((item) => item.source_phc)
          .filter(Boolean)
      ),
    ].sort();
  }, [recommendations]);

  const destinationPHCs = useMemo(() => {
    return [
      ...new Set(
        recommendations
          .map((item) => item.destination_phc)
          .filter(Boolean)
      ),
    ].sort();
  }, [recommendations]);

  // ---------------------------------------------------------
  // FILTERED DATA
  // ---------------------------------------------------------

  const filteredRecommendations = useMemo(() => {
    const query = search.trim().toLowerCase();

    return recommendations.filter((item) => {
      const searchableText = [
        item.medicine_id,
        item.medicine_name,
        item.source_phc,
        item.destination_phc,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      const matchesSearch =
        !query ||
        searchableText.includes(query);

      const matchesMedicine =
        selectedMedicine === "all" ||
        item.medicine_name === selectedMedicine;

      const matchesSource =
        selectedSource === "all" ||
        item.source_phc === selectedSource;

      const matchesDestination =
        selectedDestination === "all" ||
        item.destination_phc ===
          selectedDestination;

      return (
        matchesSearch &&
        matchesMedicine &&
        matchesSource &&
        matchesDestination
      );
    });
  }, [
    recommendations,
    search,
    selectedMedicine,
    selectedSource,
    selectedDestination,
  ]);

  // ---------------------------------------------------------
  // DYNAMIC SUMMARY
  // ---------------------------------------------------------

  const summary = useMemo(() => {
    let totalTransfer = 0;
    let totalSourceSurplus = 0;
    let totalDestinationNeed = 0;

    filteredRecommendations.forEach((item) => {
      totalTransfer += Number(
        item.transfer_quantity ||
          item.recommended_transfer_quantity ||
          item.quantity ||
          0
      );

      totalSourceSurplus += Number(
        item.source_surplus || 0
      );

      totalDestinationNeed += Number(
        item.destination_shortage ||
          item.destination_need ||
          item.destination_demand ||
          0
      );
    });

    return {
      recommendations:
        filteredRecommendations.length,

      totalTransfer,

      totalSourceSurplus,

      totalDestinationNeed,
    };
  }, [filteredRecommendations]);

  // ---------------------------------------------------------
  // HELPERS
  // ---------------------------------------------------------

  const getTransferQuantity = (item) => {
    return Number(
      item.transfer_quantity ||
        item.recommended_transfer_quantity ||
        item.quantity ||
        0
    );
  };

  const getSourceStock = (item) => {
    return Number(
      item.source_stock || 0
    );
  };

  const getDestinationStock = (item) => {
    return Number(
      item.destination_stock || 0
    );
  };

  const getSourceSurplus = (item) => {
    return Number(
      item.source_surplus || 0
    );
  };

  const getDestinationNeed = (item) => {
    return Number(
      item.destination_shortage ||
        item.destination_need ||
        item.destination_demand ||
        0
    );
  };

  // ---------------------------------------------------------
  // LOADING STATE
  // ---------------------------------------------------------

  if (loading) {
    return (
      <div className="page">
        <div className="page-heading">
          <div>
            <span className="eyebrow">
              AI LOGISTICS / REDISTRIBUTION
            </span>

            <h1>Redistribution Network</h1>

            <p>
              Loading medicine movement
              recommendations from the federated
              intelligence pipeline.
            </p>
          </div>
        </div>

        <div className="loading-panel">
          <RefreshCw
            size={28}
            className="loading-spinner"
          />

          <h3>
            Loading redistribution intelligence
          </h3>

          <p>
            Fetching the latest recommendations
            from the healthcare network.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="page redistribution-page">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div className="page-heading">

        <div>
          <span className="eyebrow">
            AI LOGISTICS / REDISTRIBUTION
          </span>

          <h1>
            Medicine Redistribution Network
          </h1>

          <p>
            AI-generated movement recommendations
            connecting surplus medicine with PHCs
            experiencing supply pressure.
          </p>
        </div>

        <button
          className="refresh-button"
          onClick={() => loadRedistribution(true)}
          disabled={refreshing}
        >
          <RefreshCw
            size={17}
            className={
              refreshing
                ? "loading-spinner"
                : ""
            }
          />

          {refreshing
            ? "Refreshing..."
            : "Refresh intelligence"}
        </button>
      </div>

      {/* =====================================================
          ERROR
      ===================================================== */}

      {error && (
        <div className="api-error">
          <AlertTriangle size={18} />

          <div>
            <strong>
              Redistribution service unavailable
            </strong>

            <p>{error}</p>
          </div>
        </div>
      )}

      {/* =====================================================
          NETWORK STATUS
      ===================================================== */}

      <section className="intelligence-banner">

        <div className="intelligence-banner-icon">
          <Truck size={25} />
        </div>

        <div>
          <span className="eyebrow">
            FEDERATED SUPPLY INTELLIGENCE
          </span>

          <h2>
            {summary.recommendations > 0
              ? "Active redistribution opportunities detected"
              : "No active redistribution opportunities"}
          </h2>

          <p>
            Recommendations shown below are loaded
            directly from the backend ML pipeline.
            The interface does not generate or
            hard-code transfer decisions.
          </p>
        </div>

        <div className="network-status">
          <CheckCircle2 size={18} />

          <span>
            Backend connected
          </span>
        </div>
      </section>

      {/* =====================================================
          STAT CARDS
      ===================================================== */}

      <section className="stats-grid">

        <div className="stat-card">
          <div className="stat-card-icon">
            <Truck size={21} />
          </div>

          <span className="stat-label">
            Active Recommendations
          </span>

          <strong className="stat-value">
            {summary.recommendations}
          </strong>

          <small>
            AI-generated transfer routes
          </small>
        </div>

        <div className="stat-card">
          <div className="stat-card-icon">
            <Package size={21} />
          </div>

          <span className="stat-label">
            Transfer Quantity
          </span>

          <strong className="stat-value">
            {summary.totalTransfer.toLocaleString()}
          </strong>

          <small>
            Units across filtered routes
          </small>
        </div>

        <div className="stat-card">
          <div className="stat-card-icon">
            <Boxes size={21} />
          </div>

          <span className="stat-label">
            Source Surplus
          </span>

          <strong className="stat-value">
            {summary.totalSourceSurplus.toLocaleString()}
          </strong>

          <small>
            Units available for balancing
          </small>
        </div>

        <div className="stat-card">
          <div className="stat-card-icon">
            <AlertTriangle size={21} />
          </div>

          <span className="stat-label">
            Destination Need
          </span>

          <strong className="stat-value">
            {summary.totalDestinationNeed.toLocaleString()}
          </strong>

          <small>
            Units represented by current data
          </small>
        </div>

      </section>

      {/* =====================================================
          FILTERS
      ===================================================== */}

      <section className="data-panel">

        <div className="section-header">

          <div>
            <span className="eyebrow">
              NETWORK FILTERS
            </span>

            <h2>
              Redistribution routes
            </h2>

            <p>
              Search and filter the recommendations
              returned by the ML backend.
            </p>
          </div>

          <div className="record-count">
            {filteredRecommendations.length}
            {" "}
            matching records
          </div>

        </div>

        <div className="filter-grid">

          <div className="search-field">

            <Search size={17} />

            <input
              type="text"
              placeholder="Search medicine or PHC..."
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
            />

          </div>

          <label className="select-field">
            <span>Medicine</span>

            <div>
              <select
                value={selectedMedicine}
                onChange={(event) =>
                  setSelectedMedicine(
                    event.target.value
                  )
                }
              >
                <option value="all">
                  All medicines
                </option>

                {medicines.map((medicine) => (
                  <option
                    key={medicine}
                    value={medicine}
                  >
                    {medicine}
                  </option>
                ))}
              </select>

              <ChevronDown size={15} />
            </div>
          </label>

          <label className="select-field">
            <span>Source PHC</span>

            <div>
              <select
                value={selectedSource}
                onChange={(event) =>
                  setSelectedSource(
                    event.target.value
                  )
                }
              >
                <option value="all">
                  All source PHCs
                </option>

                {sourcePHCs.map((phc) => (
                  <option
                    key={phc}
                    value={phc}
                  >
                    {phc}
                  </option>
                ))}
              </select>

              <ChevronDown size={15} />
            </div>
          </label>

          <label className="select-field">
            <span>Destination PHC</span>

            <div>
              <select
                value={selectedDestination}
                onChange={(event) =>
                  setSelectedDestination(
                    event.target.value
                  )
                }
              >
                <option value="all">
                  All destination PHCs
                </option>

                {destinationPHCs.map((phc) => (
                  <option
                    key={phc}
                    value={phc}
                  >
                    {phc}
                  </option>
                ))}
              </select>

              <ChevronDown size={15} />
            </div>
          </label>

        </div>

      </section>

      {/* =====================================================
          EMPTY STATE
      ===================================================== */}

      {filteredRecommendations.length === 0 ? (
        <section className="empty-state">

          <Package size={42} />

          <h2>
            No redistribution routes found
          </h2>

          <p>
            The backend returned no records matching
            the current filters.
          </p>

          <button
            onClick={() => {
              setSearch("");
              setSelectedMedicine("all");
              setSelectedSource("all");
              setSelectedDestination("all");
            }}
          >
            Clear filters
          </button>

        </section>
      ) : (

        /* ===================================================
           RECOMMENDATION CARDS
           =================================================== */

        <section className="redistribution-list">

          {filteredRecommendations.map(
            (item, index) => {

              const transfer =
                getTransferQuantity(item);

              const sourceStock =
                getSourceStock(item);

              const destinationStock =
                getDestinationStock(item);

              const sourceSurplus =
                getSourceSurplus(item);

              const destinationNeed =
                getDestinationNeed(item);

              return (
                <article
                  className="redistribution-card"
                  key={`${item.medicine_id || "medicine"}-${
                    item.source_phc || "source"
                  }-${
                    item.destination_phc ||
                    "destination"
                  }-${index}`}
                >

                  {/* TOP */}

                  <div className="redistribution-card-top">

                    <div className="medicine-identity">

                      <div className="medicine-icon">
                        <Package size={21} />
                      </div>

                      <div>
                        <span className="medicine-id">
                          {item.medicine_id ||
                            "Medicine"}
                        </span>

                        <h3>
                          {item.medicine_name ||
                            "Unnamed medicine"}
                        </h3>
                      </div>

                    </div>

                    <div className="recommendation-status">
                      <CheckCircle2 size={16} />

                      AI recommendation
                    </div>

                  </div>

                  {/* ROUTE */}

                  <div className="route-container">

                    <div className="route-node source">

                      <span className="route-label">
                        SOURCE PHC
                      </span>

                      <div className="route-location">
                        <Building2 size={19} />

                        <strong>
                          {item.source_phc ||
                            "Unknown"}
                        </strong>
                      </div>

                      <div className="route-metric">
                        <span>
                          Current stock
                        </span>

                        <strong>
                          {sourceStock.toLocaleString()}
                        </strong>
                      </div>

                      <div className="route-metric">
                        <span>
                          Available surplus
                        </span>

                        <strong>
                          {sourceSurplus.toLocaleString()}
                        </strong>
                      </div>

                    </div>

                    <div className="route-arrow">

                      <div className="route-arrow-line" />

                      <div className="route-arrow-icon">
                        <ArrowRight size={21} />
                      </div>

                      <span>
                        {transfer.toLocaleString()}
                        {" "}
                        units
                      </span>

                    </div>

                    <div className="route-node destination">

                      <span className="route-label">
                        DESTINATION PHC
                      </span>

                      <div className="route-location">
                        <MapPin size={19} />

                        <strong>
                          {item.destination_phc ||
                            "Unknown"}
                        </strong>
                      </div>

                      <div className="route-metric">
                        <span>
                          Current stock
                        </span>

                        <strong>
                          {destinationStock.toLocaleString()}
                        </strong>
                      </div>

                      <div className="route-metric">
                        <span>
                          Estimated need
                        </span>

                        <strong>
                          {destinationNeed.toLocaleString()}
                        </strong>
                      </div>

                    </div>

                  </div>

                  {/* BOTTOM */}

                  <div className="redistribution-card-footer">

                    <div>
                      <Clock3 size={15} />

                      <span>
                        Recommendation generated
                        by ML pipeline
                      </span>
                    </div>

                    <div className="transfer-quantity">

                      <span>
                        Recommended transfer
                      </span>

                      <strong>
                        {transfer.toLocaleString()}
                        {" "}
                        units
                      </strong>

                    </div>

                  </div>

                </article>
              );
            }
          )}

        </section>
      )}

    </div>
  );
}

export default Redistribution;