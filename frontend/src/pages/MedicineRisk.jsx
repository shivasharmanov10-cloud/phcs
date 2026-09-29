
import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  Boxes,
  CalendarDays,
  PackageSearch,
  RefreshCw,
  Search,
  ShieldAlert,
} from "lucide-react";

import Loading from "../components/Loading";

const API_URL = "http://127.0.0.1:8000";

function MedicineRisk() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [sortBy, setSortBy] = useState("risk");

  const loadRiskData = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        `${API_URL}/api/ml/stock-risk`
      );

      if (!response.ok) {
        throw new Error("Unable to load stock-risk data.");
      }

      const result = await response.json();

      setRows(
        Array.isArray(result?.data)
          ? result.data
          : []
      );
    } catch (err) {
      console.error(err);
      setError(
        "Unable to connect to the medicine-risk service."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRiskData();
  }, []);

  const normalizedRows = useMemo(() => {
    return rows.map((row) => ({
      ...row,

      stock: Number(
        row.stock_quantity ?? 0
      ),

      demand: Number(
        row.daily_demand ?? 0
      ),

      received: Number(
        row.received_quantity ?? 0
      ),

      expired: Number(
        row.expired_quantity ?? 0
      ),

      population: Number(
        row.population ?? 0
      ),

      risk: String(
        row.risk_level ?? "UNKNOWN"
      ).toUpperCase(),
    }));
  }, [rows]);

  const filteredRows = useMemo(() => {
    const query = search
      .trim()
      .toLowerCase();

    const result = normalizedRows.filter(
      (row) => {

        const matchesSearch =
          !query ||
          String(row.medicine_name || "")
            .toLowerCase()
            .includes(query) ||
          String(row.medicine_id || "")
            .toLowerCase()
            .includes(query) ||
          String(row.phc_id || "")
            .toLowerCase()
            .includes(query);

        const matchesRisk =
          riskFilter === "ALL" ||
          row.risk === riskFilter;

        return (
          matchesSearch &&
          matchesRisk
        );
      }
    );

    return [...result].sort(
      (a, b) => {

        if (sortBy === "stock") {
          return b.stock - a.stock;
        }

        if (sortBy === "demand") {
          return b.demand - a.demand;
        }

        if (sortBy === "expired") {
          return b.expired - a.expired;
        }

        const priority = {
          CRITICAL: 4,
          HIGH: 3,
          MEDIUM: 2,
          LOW: 1,
        };

        return (
          (priority[b.risk] || 0) -
          (priority[a.risk] || 0)
        );
      }
    );
  }, [
    normalizedRows,
    search,
    riskFilter,
    sortBy,
  ]);

  const statistics = useMemo(() => {

    const critical = normalizedRows.filter(
      (row) => row.risk === "CRITICAL"
    ).length;

    const high = normalizedRows.filter(
      (row) =>
        row.risk === "HIGH"
    ).length;

    const medium = normalizedRows.filter(
      (row) =>
        row.risk === "MEDIUM"
    ).length;

    const low = normalizedRows.filter(
      (row) =>
        row.risk === "LOW"
    ).length;

    const totalStock =
      normalizedRows.reduce(
        (sum, row) =>
          sum + row.stock,
        0
      );

    const totalDemand =
      normalizedRows.reduce(
        (sum, row) =>
          sum + row.demand,
        0
      );

    const totalExpired =
      normalizedRows.reduce(
        (sum, row) =>
          sum + row.expired,
        0
      );

    return {
      critical,
      high,
      medium,
      low,
      totalStock,
      totalDemand,
      totalExpired,
    };

  }, [normalizedRows]);

  const formatNumber = (value) =>
    new Intl.NumberFormat(
      "en-IN"
    ).format(
      Math.round(value || 0)
    );

  const getRiskIcon = (risk) => {

    if (
      risk === "CRITICAL" ||
      risk === "HIGH"
    ) {
      return (
        <AlertTriangle size={17} />
      );
    }

    return (
      <ShieldAlert size={17} />
    );
  };

  if (loading) {
    return <Loading />;
  }

  return (
    <div className="page medicine-risk-page">

      <div className="page-heading">

        <div>

          <span className="eyebrow">
            PHC INTELLIGENCE / INVENTORY RISK
          </span>

          <h1>
            Medicine Risk Intelligence
          </h1>

          <p>
            Monitor medicine availability,
            demand pressure, stock exposure,
            expiry activity and operational
            risk across connected PHCs.
          </p>

        </div>

        <button
          className="action-button"
          onClick={loadRiskData}
        >
          <RefreshCw size={17} />
          Refresh intelligence
        </button>

      </div>

      {error && (
        <div className="api-error">
          <AlertTriangle size={18} />
          {error}
        </div>
      )}

      <section className="stats-grid">

        <div className="stat-card">
          <div className="stat-icon">
            <ShieldAlert size={21} />
          </div>

          <span>Critical</span>

          <strong>
            {statistics.critical}
          </strong>

          <small>
            Immediate inventory attention
          </small>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <AlertTriangle size={21} />
          </div>

          <span>High Risk</span>

          <strong>
            {statistics.high}
          </strong>

          <small>
            Stock-demand pressure detected
          </small>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <Boxes size={21} />
          </div>

          <span>Total Stock</span>

          <strong>
            {formatNumber(
              statistics.totalStock
            )}
          </strong>

          <small>
            Units across analyzed records
          </small>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <ArrowUp size={21} />
          </div>

          <span>Demand Volume</span>

          <strong>
            {formatNumber(
              statistics.totalDemand
            )}
          </strong>

          <small>
            Daily demand represented
          </small>
        </div>

      </section>

      <section className="risk-control-panel">

        <div className="search-box">

          <Search size={18} />

          <input
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value
              )
            }
            placeholder="Search medicine, PHC or medicine ID..."
          />

        </div>

        <select
          value={riskFilter}
          onChange={(event) =>
            setRiskFilter(
              event.target.value
            )
          }
        >
          <option value="ALL">
            All risk levels
          </option>

          <option value="CRITICAL">
            Critical
          </option>

          <option value="HIGH">
            High
          </option>

          <option value="MEDIUM">
            Medium
          </option>

          <option value="LOW">
            Low
          </option>
        </select>

        <select
          value={sortBy}
          onChange={(event) =>
            setSortBy(
              event.target.value
            )
          }
        >
          <option value="risk">
            Sort by risk
          </option>

          <option value="stock">
            Sort by stock
          </option>

          <option value="demand">
            Sort by demand
          </option>

          <option value="expired">
            Sort by expiry
          </option>
        </select>

      </section>

      <section className="data-panel">

        <div className="data-panel-header">

          <div>
            <span className="eyebrow">
              LIVE INVENTORY ANALYSIS
            </span>

            <h2>
              Medicine Risk Register
            </h2>

            <p>
              Showing {filteredRows.length}{" "}
              of {normalizedRows.length}{" "}
              analyzed records.
            </p>
          </div>

          <div className="data-meta">
            <CalendarDays size={16} />
            Backend-generated inventory data
          </div>

        </div>

        {filteredRows.length === 0 ? (

          <div className="empty-state">
            <PackageSearch size={34} />

            <h3>
              No matching records
            </h3>

            <p>
              Try changing the search
              or risk filter.
            </p>
          </div>

        ) : (

          <div className="table-wrapper">

            <table>

              <thead>

                <tr>

                  <th>Medicine</th>

                  <th>PHC</th>

                  <th>Stock</th>

                  <th>Daily demand</th>

                  <th>Received</th>

                  <th>Expired</th>

                  <th>Population</th>

                  <th>Risk</th>

                </tr>

              </thead>

              <tbody>

                {filteredRows.map(
                  (row, index) => (

                    <tr
                      key={`${row.phc_id}-${row.medicine_id}-${row.date}-${index}`}
                    >

                      <td>

                        <div className="medicine-cell">

                          <strong>
                            {row.medicine_name ||
                              "Unknown medicine"}
                          </strong>

                          <span>
                            {row.medicine_id ||
                              "—"}
                          </span>

                        </div>

                      </td>

                      <td>
                        {row.phc_id || "—"}
                      </td>

                      <td>
                        {formatNumber(
                          row.stock
                        )}
                      </td>

                      <td>
                        {formatNumber(
                          row.demand
                        )}
                      </td>

                      <td>
                        {formatNumber(
                          row.received
                        )}
                      </td>

                      <td>

                        <span
                          className={
                            row.expired > 0
                              ? "expiry-warning"
                              : ""
                          }
                        >
                          {formatNumber(
                            row.expired
                          )}
                        </span>

                      </td>

                      <td>
                        {formatNumber(
                          row.population
                        )}
                      </td>

                      <td>

                        <span
                          className={`risk-badge risk-${row.risk.toLowerCase()}`}
                        >
                          {getRiskIcon(
                            row.risk
                          )}

                          {row.risk}
                        </span>

                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        )}

      </section>

      <section className="risk-insight-grid">

        <div className="insight-card">

          <div className="insight-icon">
            <ArrowDown size={19} />
          </div>

          <div>

            <span>
              Expired inventory
            </span>

            <strong>
              {formatNumber(
                statistics.totalExpired
              )}
            </strong>

            <p>
              Expired units represented
              across the current ML
              stock-risk dataset.
            </p>

          </div>

        </div>

        <div className="insight-card">

          <div className="insight-icon">
            <PackageSearch size={19} />
          </div>

          <div>

            <span>
              Risk records analyzed
            </span>

            <strong>
              {formatNumber(
                normalizedRows.length
              )}
            </strong>

            <p>
              Inventory observations
              currently available through
              the backend ML pipeline.
            </p>

          </div>

        </div>

      </section>

    </div>
  );
}

export default MedicineRisk;