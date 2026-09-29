
import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  CalendarDays,
  ChevronDown,
  Database,
  RefreshCw,
  Search,
  TrendingUp,
  Target,
  AlertTriangle,
} from "lucide-react";

import Loading from "../components/Loading";

const API_URL = "http://127.0.0.1:8000";

function DemandForecast() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [selectedPHC, setSelectedPHC] = useState("ALL");
  const [selectedMedicine, setSelectedMedicine] = useState("ALL");

  const loadForecast = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      const response = await fetch(
        `${API_URL}/api/ml/forecast`
      );

      if (!response.ok) {
        throw new Error("Unable to load demand forecast.");
      }

      const result = await response.json();

      setData(
        Array.isArray(result.data)
          ? result.data
          : []
      );

      setError("");
    } catch (err) {
      console.error(err);
      setError(
        "Unable to connect to the forecasting service."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadForecast();
  }, []);

  const phcs = useMemo(() => {
    return [
      "ALL",
      ...new Set(
        data
          .map((item) => item.phc_id)
          .filter(Boolean)
      ),
    ];
  }, [data]);

  const medicines = useMemo(() => {
    return [
      "ALL",
      ...new Set(
        data
          .map((item) => item.medicine_name)
          .filter(Boolean)
      ),
    ];
  }, [data]);

  const filteredData = useMemo(() => {
    const query = search.trim().toLowerCase();

    return data.filter((item) => {
      const matchesPHC =
        selectedPHC === "ALL" ||
        item.phc_id === selectedPHC;

      const matchesMedicine =
        selectedMedicine === "ALL" ||
        item.medicine_name === selectedMedicine;

      const searchable = [
        item.phc_id,
        item.medicine_id,
        item.medicine_name,
        item.date,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      const matchesSearch =
        !query || searchable.includes(query);

      return (
        matchesPHC &&
        matchesMedicine &&
        matchesSearch
      );
    });
  }, [
    data,
    search,
    selectedPHC,
    selectedMedicine,
  ]);

  const statistics = useMemo(() => {
    if (!filteredData.length) {
      return {
        records: 0,
        averageDemand: 0,
        averagePrediction: 0,
        averageError: 0,
        accuracy: 0,
        maxDemand: 0,
      };
    }

    const actual = filteredData.map(
      (item) => Number(item.daily_demand) || 0
    );

    const predicted = filteredData.map(
      (item) => Number(item.predicted_demand) || 0
    );

    const errors = filteredData.map(
      (item) =>
        Math.abs(
          Number(item.absolute_error) ||
            Math.abs(
              (Number(item.daily_demand) || 0) -
                (Number(item.predicted_demand) || 0)
            )
        )
    );

    const averageDemand =
      actual.reduce((sum, value) => sum + value, 0) /
      actual.length;

    const averagePrediction =
      predicted.reduce((sum, value) => sum + value, 0) /
      predicted.length;

    const averageError =
      errors.reduce((sum, value) => sum + value, 0) /
      errors.length;

    const accuracy =
      averageDemand > 0
        ? Math.max(
            0,
            Math.min(
              100,
              100 -
                (averageError / averageDemand) * 100
            )
          )
        : 0;

    return {
      records: filteredData.length,
      averageDemand,
      averagePrediction,
      averageError,
      accuracy,
      maxDemand: Math.max(...actual),
    };
  }, [filteredData]);

  const formatNumber = (value, decimals = 1) => {
    return Number(value || 0).toLocaleString(
      undefined,
      {
        maximumFractionDigits: decimals,
      }
    );
  };

  const getPredictionStatus = (item) => {
    const actual =
      Number(item.daily_demand) || 0;

    const predicted =
      Number(item.predicted_demand) || 0;

    if (!actual) {
      return "NO BASELINE";
    }

    const difference =
      Math.abs(predicted - actual) / actual;

    if (difference <= 0.1) {
      return "HIGH ACCURACY";
    }

    if (difference <= 0.25) {
      return "ACCEPTABLE";
    }

    return "DEVIATION";
  };

  return (
    <div className="page forecast-page">

      {/* ================================================= */}
      {/* PAGE HEADER */}
      {/* ================================================= */}

      <div className="page-heading">

        <div>
          <span className="eyebrow">
            FEDERATED AI / DEMAND INTELLIGENCE
          </span>

          <h1>Demand Forecast</h1>

          <p>
            Monitor medicine demand predictions generated
            from the federated PHC forecasting pipeline.
          </p>
        </div>

        <button
          className="page-action"
          onClick={() => loadForecast(true)}
          disabled={refreshing}
        >
          <RefreshCw
            size={17}
            className={
              refreshing
                ? "spin"
                : ""
            }
          />

          {refreshing
            ? "Refreshing..."
            : "Refresh Forecast"}
        </button>

      </div>

      {error && (
        <div className="api-error">
          <AlertTriangle size={18} />
          {error}
        </div>
      )}

      {loading ? (
        <Loading />
      ) : (
        <>

          {/* ================================================= */}
          {/* FORECAST STATUS */}
          {/* ================================================= */}

          <section className="forecast-intelligence">

            <div className="forecast-intro">

              <div className="forecast-intro-icon">
                <Activity size={25} />
              </div>

              <div>
                <span className="eyebrow">
                  LIVE MODEL OUTPUT
                </span>

                <h2>
                  Federated demand intelligence
                </h2>

                <p>
                  Forecast observations returned by
                  the backend ML pipeline. The interface
                  updates directly from the API and does
                  not use static forecast values.
                </p>
              </div>

            </div>

            <div className="forecast-status">

              <span className="status-dot" />

              <span>
                Forecast service connected
              </span>

            </div>

          </section>

          {/* ================================================= */}
          {/* STATISTICS */}
          {/* ================================================= */}

          <section className="stats-grid forecast-stats">

            <ForecastStat
              icon={Database}
              label="Forecast Records"
              value={statistics.records}
              suffix=""
              description="Backend prediction observations"
            />

            <ForecastStat
              icon={TrendingUp}
              label="Average Actual Demand"
              value={statistics.averageDemand}
              suffix=""
              description="Observed daily medicine demand"
            />

            <ForecastStat
              icon={Target}
              label="Average Prediction"
              value={statistics.averagePrediction}
              suffix=""
              description="AI predicted daily demand"
            />

            <ForecastStat
              icon={Activity}
              label="Forecast Accuracy"
              value={statistics.accuracy}
              suffix="%"
              description="Derived from prediction error"
            />

          </section>

          {/* ================================================= */}
          {/* FILTER BAR */}
          {/* ================================================= */}

          <section className="forecast-control-panel">

            <div className="control-title">
              <CalendarDays size={19} />

              <div>
                <strong>
                  Forecast Explorer
                </strong>

                <span>
                  Filter and inspect individual
                  prediction observations
                </span>
              </div>
            </div>

            <div className="forecast-controls">

              <div className="search-control">

                <Search size={17} />

                <input
                  type="text"
                  placeholder="Search PHC, medicine or date..."
                  value={search}
                  onChange={(event) =>
                    setSearch(event.target.value)
                  }
                />

              </div>

              <div className="select-control">

                <select
                  value={selectedPHC}
                  onChange={(event) =>
                    setSelectedPHC(
                      event.target.value
                    )
                  }
                >
                  {phcs.map((phc) => (
                    <option
                      key={phc}
                      value={phc}
                    >
                      {phc === "ALL"
                        ? "All PHCs"
                        : phc}
                    </option>
                  ))}
                </select>

                <ChevronDown size={16} />

              </div>

              <div className="select-control">

                <select
                  value={selectedMedicine}
                  onChange={(event) =>
                    setSelectedMedicine(
                      event.target.value
                    )
                  }
                >
                  {medicines.map(
                    (medicine) => (
                      <option
                        key={medicine}
                        value={medicine}
                      >
                        {medicine === "ALL"
                          ? "All Medicines"
                          : medicine}
                      </option>
                    )
                  )}
                </select>

                <ChevronDown size={16} />

              </div>

            </div>

          </section>

          {/* ================================================= */}
          {/* MODEL INSIGHTS */}
          {/* ================================================= */}

          <section className="forecast-insight-grid">

            <div className="intelligence-card">

              <div className="card-topline">

                <span className="eyebrow">
                  MODEL PERFORMANCE
                </span>

                <Target size={19} />

              </div>

              <div className="big-metric">
                {formatNumber(
                  statistics.averageError,
                  2
                )}
              </div>

              <p>
                Average absolute prediction error
                across the currently filtered
                forecasting observations.
              </p>

            </div>

            <div className="intelligence-card">

              <div className="card-topline">

                <span className="eyebrow">
                  DEMAND RANGE
                </span>

                <TrendingUp size={19} />

              </div>

              <div className="big-metric">
                {formatNumber(
                  statistics.maxDemand,
                  0
                )}
              </div>

              <p>
                Highest observed daily demand
                within the current forecast view.
              </p>

            </div>

            <div className="intelligence-card">

              <div className="card-topline">

                <span className="eyebrow">
                  ACTIVE SCOPE
                </span>

                <Database size={19} />

              </div>

              <div className="big-metric">
                {formatNumber(
                  filteredData.length,
                  0
                )}
              </div>

              <p>
                Forecast observations currently
                visible after applying filters.
              </p>

            </div>

          </section>

          {/* ================================================= */}
          {/* FORECAST TABLE */}
          {/* ================================================= */}

          <section className="data-section">

            <div className="section-header">

              <div>
                <span className="eyebrow">
                  AI PREDICTION STREAM
                </span>

                <h2>
                  Medicine demand observations
                </h2>
              </div>

              <span className="result-count">
                {filteredData.length.toLocaleString()} records
              </span>

            </div>

            <div className="table-wrapper">

              <table className="data-table">

                <thead>
                  <tr>
                    <th>Date</th>
                    <th>PHC</th>
                    <th>Medicine</th>
                    <th>Actual Demand</th>
                    <th>AI Prediction</th>
                    <th>Error</th>
                    <th>Status</th>
                  </tr>
                </thead>

                <tbody>

                  {filteredData.length === 0 ? (

                    <tr>
                      <td
                        colSpan="7"
                        className="empty-state"
                      >
                        No forecast records match
                        the selected filters.
                      </td>
                    </tr>

                  ) : (

                    filteredData
                      .slice(0, 100)
                      .map((item, index) => {

                        const actual =
                          Number(
                            item.daily_demand
                          ) || 0;

                        const predicted =
                          Number(
                            item.predicted_demand
                          ) || 0;

                        const absoluteError =
                          Number(
                            item.absolute_error
                          ) ||
                          Math.abs(
                            actual -
                              predicted
                          );

                        const status =
                          getPredictionStatus(
                            item
                          );

                        return (
                          <tr
                            key={`${item.date}-${item.phc_id}-${item.medicine_id}-${index}`}
                          >

                            <td>
                              <div className="date-cell">
                                <CalendarDays
                                  size={15}
                                />
                                {item.date || "—"}
                              </div>
                            </td>

                            <td>
                              <span className="phc-badge">
                                {item.phc_id || "—"}
                              </span>
                            </td>

                            <td>
                              <div className="medicine-cell">

                                <strong>
                                  {item.medicine_name ||
                                    "Unknown medicine"}
                                </strong>

                                <span>
                                  {item.medicine_id ||
                                    "—"}
                                </span>

                              </div>
                            </td>

                            <td>
                              <strong>
                                {formatNumber(
                                  actual,
                                  0
                                )}
                              </strong>
                            </td>

                            <td>
                              <strong className="prediction-value">
                                {formatNumber(
                                  predicted,
                                  0
                                )}
                              </strong>
                            </td>

                            <td>
                              {formatNumber(
                                absoluteError,
                                0
                              )}
                            </td>

                            <td>
                              <span
                                className={`forecast-status status-${status
                                  .toLowerCase()
                                  .replace(
                                    /\s+/g,
                                    "-"
                                  )}`}
                              >
                                {status}
                              </span>
                            </td>

                          </tr>
                        );
                      })

                  )}

                </tbody>

              </table>

            </div>

            {filteredData.length > 100 && (
              <div className="table-footer">

                Showing first 100 records of{" "}
                {filteredData.length.toLocaleString()}
                {" "}matching observations.

              </div>
            )}

          </section>

        </>
      )}

    </div>
  );
}


/* ========================================================= */
/* FORECAST STAT */
/* ========================================================= */

function ForecastStat({
  icon: Icon,
  label,
  value,
  suffix,
  description,
}) {
  const displayValue =
    Number(value || 0).toLocaleString(
      undefined,
      {
        maximumFractionDigits:
          suffix === "%" ? 1 : 1,
      }
    );

  return (
    <div className="forecast-stat-card">

      <div className="forecast-stat-icon">
        <Icon size={20} />
      </div>

      <div className="forecast-stat-content">

        <span>
          {label}
        </span>

        <strong>
          {displayValue}
          {suffix}
        </strong>

        <small>
          {description}
        </small>

      </div>

    </div>
  );
}

export default DemandForecast;