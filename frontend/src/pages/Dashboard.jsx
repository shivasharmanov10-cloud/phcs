
import { useEffect, useMemo, useState } from "react";

import {
  Activity,
  AlertTriangle,
  BrainCircuit,
  Database,
  Factory,
  RefreshCw,
  Server,
  ShieldAlert,
  Truck,
  TrendingDown,
  TrendingUp,
  Users,
} from "lucide-react";

import Loading from "../components/Loading";


const API_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [federated, setFederated] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [risk, setRisk] = useState([]);
  const [redistribution, setRedistribution] = useState([]);
  const [anomalies, setAnomalies] = useState([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadDashboard = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError("");

      const responses = await Promise.all([
        fetch(`${API_URL}/api/ml/summary`),
        fetch(`${API_URL}/api/federated/status`),
        fetch(`${API_URL}/api/ml/forecast`),
        fetch(`${API_URL}/api/ml/stock-risk`),
        fetch(`${API_URL}/api/ml/redistribution`),
        fetch(`${API_URL}/api/ml/anomalies`),
      ]);

      for (const response of responses) {
        if (!response.ok) {
          throw new Error("One or more backend services failed.");
        }
      }

      const [
        summaryData,
        federatedData,
        forecastData,
        riskData,
        redistributionData,
        anomalyData,
      ] = await Promise.all(
        responses.map((response) => response.json())
      );

      setSummary(summaryData);
      setFederated(federatedData);
      setForecast(forecastData.data || []);
      setRisk(riskData.data || []);
      setRedistribution(
        redistributionData.data || []
      );
      setAnomalies(anomalyData.data || []);

    } catch (err) {
      console.error(err);

      setError(
        "Unable to connect to the intelligence backend."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const metrics = useMemo(() => {
    const high =
      Number(summary?.stock_risk?.high || 0);

    const medium =
      Number(summary?.stock_risk?.medium || 0);

    const low =
      Number(summary?.stock_risk?.low || 0);

    const anomalyCount =
      Number(summary?.anomalies || 0);

    const redistributionCount =
      Number(
        summary?.redistribution_recommendations || 0
      );

    const forecastCount =
      forecast.length;

    const participatingPHCs =
      Number(
        federated?.participating_phcs || 0
      );

    const trainingRounds =
      Number(
        federated?.training_rounds || 0
      );

    const validationRMSE =
      Number(
        federated?.latest_round?.validation_rmse || 0
      );

    const validationMAE =
      Number(
        federated?.latest_round?.validation_mae || 0
      );

    return {
      high,
      medium,
      low,
      anomalyCount,
      redistributionCount,
      forecastCount,
      participatingPHCs,
      trainingRounds,
      validationRMSE,
      validationMAE,
    };
  }, [
    summary,
    federated,
    forecast,
  ]);

  const averageActualDemand = useMemo(() => {
    if (!forecast.length) return 0;

    const values = forecast
      .map((item) =>
        Number(item.daily_demand)
      )
      .filter(Number.isFinite);

    if (!values.length) return 0;

    return (
      values.reduce(
        (sum, value) => sum + value,
        0
      ) / values.length
    );
  }, [forecast]);

  const averagePredictedDemand = useMemo(() => {
    if (!forecast.length) return 0;

    const values = forecast
      .map((item) =>
        Number(item.predicted_demand)
      )
      .filter(Number.isFinite);

    if (!values.length) return 0;

    return (
      values.reduce(
        (sum, value) => sum + value,
        0
      ) / values.length
    );
  }, [forecast]);

  const recentForecasts = forecast.slice(0, 8);
  const recentRisk = risk.slice(0, 8);
  const recentAnomalies = anomalies.slice(0, 6);

  if (loading) {
    return <Loading />;
  }

  return (
    <div className="page">

      {/* =================================================
          PAGE HEADER
      ================================================= */}

      <section className="page-heading">

        <div>

          <span className="eyebrow">
            PHC INTELLIGENCE / COMMAND CENTER
          </span>

          <h1>
            Healthcare Intelligence Dashboard
          </h1>

          <p>
            Federated AI monitoring medicine demand,
            inventory risk, anomalies and
            redistribution opportunities across
            participating Primary Health Centres.
          </p>

        </div>

        <button
          className="btn btn-secondary"
          onClick={() => loadDashboard(true)}
          disabled={refreshing}
        >
          <RefreshCw size={15} />

          {refreshing
            ? "Refreshing..."
            : "Refresh Intelligence"}
        </button>

      </section>

      {/* =================================================
          ERROR
      ================================================= */}

      {error && (
        <div className="api-error">
          <AlertTriangle size={18} />
          {error}
        </div>
      )}

      {/* =================================================
          SYSTEM STATUS
      ================================================= */}

      <section className="card">

        <div className="panel-header">

          <div>
            <h2 className="panel-title">
              Intelligence Network Status
            </h2>

            <p className="panel-subtitle">
              Live status of the federated learning
              infrastructure.
            </p>
          </div>

          <span className="status-badge status-live">
            System Active
          </span>

        </div>

        <div className="panel-body">

          <div className="stats-grid">

            <Stat
              icon={Server}
              label="Network Status"
              value={
                federated?.status || "Unknown"
              }
              description="Federated service"
            />

            <Stat
              icon={Factory}
              label="Participating PHCs"
              value={
                metrics.participatingPHCs
              }
              description="Healthcare centres"
            />

            <Stat
              icon={BrainCircuit}
              label="Training Rounds"
              value={
                metrics.trainingRounds
              }
              description="FedAvg rounds completed"
            />

            <Stat
              icon={Database}
              label="Forecast Records"
              value={
                metrics.forecastCount.toLocaleString()
              }
              description="Model predictions"
            />

          </div>

        </div>

      </section>

      {/* =================================================
          PRIMARY KPI GRID
      ================================================= */}

      <section className="stats-grid">

        <Stat
          icon={ShieldAlert}
          label="High Risk Stock"
          value={metrics.high}
          description="Requires operational attention"
          variant="danger"
        />

        <Stat
          icon={Activity}
          label="Detected Anomalies"
          value={
            metrics.anomalyCount.toLocaleString()
          }
          description="Potential inventory irregularities"
          variant="purple"
        />

        <Stat
          icon={Truck}
          label="Redistribution Actions"
          value={
            metrics.redistributionCount
          }
          description="Transfer opportunities"
          variant="orange"
        />

        <Stat
          icon={Users}
          label="Low Risk Inventory"
          value={metrics.low}
          description="Currently stable records"
          variant="success"
        />

      </section>

      {/* =================================================
          MODEL PERFORMANCE
      ================================================= */}

      <section className="dashboard-grid">

        <Panel
          title="Federated Model Performance"
          subtitle="Latest global model validation metrics."
        >

          <div className="metric-grid">

            <Metric
              label="Validation RMSE"
              value={
                metrics.validationRMSE
                  ? metrics.validationRMSE.toFixed(2)
                  : "—"
              }
              icon={TrendingDown}
            />

            <Metric
              label="Validation MAE"
              value={
                metrics.validationMAE
                  ? metrics.validationMAE.toFixed(2)
                  : "—"
              }
              icon={TrendingDown}
            />

            <Metric
              label="Algorithm"
              value={
                federated?.algorithm ||
                "FedAvg"
              }
              icon={BrainCircuit}
            />

            <Metric
              label="Samples Processed"
              value={
                Number(
                  federated?.total_samples || 0
                ).toLocaleString()
              }
              icon={Database}
            />

          </div>

          <div className="model-description">

            <strong>
              Federated learning is active.
            </strong>

            <p>
              PHC-level training data remains
              decentralized while model updates are
              aggregated into the global forecasting
              model.
            </p>

          </div>

        </Panel>

        <Panel
          title="Demand Intelligence"
          subtitle="Actual versus predicted medicine demand."
        >

          <div className="demand-comparison">

            <div>

              <span>
                Average actual demand
              </span>

              <strong>
                {averageActualDemand.toFixed(1)}
              </strong>

              <small>
                units / day
              </small>

            </div>

            <div className="comparison-arrow">
              →
            </div>

            <div>

              <span>
                Average predicted demand
              </span>

              <strong>
                {averagePredictedDemand.toFixed(1)}
              </strong>

              <small>
                units / day
              </small>

            </div>

          </div>

          <div className="forecast-status">

            <Activity size={16} />

            <span>
              Forecast engine processed{" "}
              <strong>
                {metrics.forecastCount.toLocaleString()}
              </strong>{" "}
              prediction records.
            </span>

          </div>

        </Panel>

      </section>

      {/* =================================================
          RISK + ANOMALY
      ================================================= */}

      <section className="dashboard-grid">

        <Panel
          title="Medicine Risk Intelligence"
          subtitle="Latest inventory records requiring monitoring."
        >

          <DataTable
            columns={[
              "Medicine",
              "PHC",
              "Stock",
              "Demand",
              "Risk",
            ]}
            rows={recentRisk.map((item) => [
              item.medicine_name ||
                item.medicine_id ||
                "Unknown",

              item.phc_id || "—",

              item.stock_quantity ?? "—",

              item.daily_demand ?? "—",

              item.risk_level || "—",
            ])}
          />

        </Panel>

        <Panel
          title="Anomaly Monitoring"
          subtitle="Most recent detected irregularities."
        >

          <div className="activity-list">

            {recentAnomalies.length === 0 ? (
              <EmptyState
                text="No anomalies available."
              />
            ) : (
              recentAnomalies.map(
                (item, index) => (
                  <ActivityItem
                    key={`${item.date}-${index}`}
                    icon={AlertTriangle}
                    title={
                      item.medicine_name ||
                      "Medicine anomaly"
                    }
                    description={
                      `${item.phc_id || "Unknown PHC"} • ${
                        item.date || "Unknown date"
                      }`
                    }
                    value={
                      item.anomaly_score ??
                      item.absolute_error ??
                      "Detected"
                    }
                  />
                )
              )
            )}

          </div>

        </Panel>

      </section>

      {/* =================================================
          FORECAST TABLE
      ================================================= */}

      <section className="card">

        <div className="panel-header">

          <div>
            <h2 className="panel-title">
              Latest Demand Forecasts
            </h2>

            <p className="panel-subtitle">
              Recent model predictions across the
              PHC network.
            </p>
          </div>

          <span className="status-badge status-live">
            AI Forecast
          </span>

        </div>

        <DataTable
          columns={[
            "Date",
            "PHC",
            "Medicine",
            "Actual Demand",
            "Predicted",
            "Error",
          ]}
          rows={recentForecasts.map((item) => [
            item.date || "—",

            item.phc_id || "—",

            item.medicine_name ||
              item.medicine_id ||
              "—",

            item.daily_demand ?? "—",

            item.predicted_demand ?? "—",

            item.prediction_error ?? "—",
          ])}
        />

      </section>

      {/* =================================================
          REDISTRIBUTION
      ================================================= */}

      <section className="card">

        <div className="panel-header">

          <div>
            <h2 className="panel-title">
              Redistribution Intelligence
            </h2>

            <p className="panel-subtitle">
              AI-generated opportunities to move
              surplus medicine toward shortage locations.
            </p>
          </div>

          <Truck size={20} />

        </div>

        {redistribution.length === 0 ? (
          <EmptyState
            text="No redistribution recommendations currently available."
          />
        ) : (
          <DataTable
            columns={[
              "Medicine",
              "Source PHC",
              "Destination PHC",
              "Source Stock",
              "Destination Stock",
              "Transfer",
            ]}
            rows={redistribution.map((item) => [
              item.medicine_name ||
                item.medicine_id ||
                "—",

              item.source_phc || "—",

              item.destination_phc || "—",

              item.source_stock ?? "—",

              item.destination_stock ?? "—",

              item.recommended_transfer ??
                item.transfer_quantity ??
                "—",
            ])}
          />
        )}

      </section>

      {/* =================================================
          OPERATIONAL FOOTER
      ================================================= */}

      <section className="card">

        <div className="panel-body">

          <div className="system-footer">

            <div>

              <span className="eyebrow">
                SYSTEM OBSERVABILITY
              </span>

              <h3>
                Federated PHC intelligence
                pipeline is operational.
              </h3>

              <p>
                Demand forecasting, inventory risk,
                anomaly detection and redistribution
                intelligence are connected to the
                backend services.
              </p>

            </div>

            <div className="system-footer-status">

              <span className="status-badge status-live">
                API Online
              </span>

              <span className="status-badge status-live">
                ML Online
              </span>

              <span className="status-badge status-live">
                FedAvg Active
              </span>

            </div>

          </div>

        </div>

      </section>

    </div>
  );
}


/* =========================================================
   SHARED COMPONENTS
========================================================= */

function Stat({
  icon: Icon,
  label,
  value,
  description,
  variant = "blue",
}) {
  return (
    <div className="stat-card">

      <div className={`stat-card-icon ${variant}`}>
        <Icon size={20} />
      </div>

      <div className="stat-card-value">
        {value}
      </div>

      <div className="stat-card-label">
        {label}
      </div>

      <div className="stat-card-description">
        {description}
      </div>

    </div>
  );
}


function Panel({
  title,
  subtitle,
  children,
}) {
  return (
    <section className="panel">

      <div className="panel-header">

        <div>
          <h2 className="panel-title">
            {title}
          </h2>

          <p className="panel-subtitle">
            {subtitle}
          </p>
        </div>

      </div>

      <div className="panel-body">
        {children}
      </div>

    </section>
  );
}


function Metric({
  label,
  value,
  icon: Icon,
}) {
  return (
    <div className="metric-item">

      <div className="metric-icon">
        <Icon size={16} />
      </div>

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}


function DataTable({
  columns,
  rows,
}) {
  return (
    <div className="data-table-wrapper">

      <table className="data-table">

        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>
                {column}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>

          {rows.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
              >
                No data available.
              </td>
            </tr>
          ) : (
            rows.map((row, index) => (
              <tr key={index}>
                {row.map(
                  (value, valueIndex) => (
                    <td key={valueIndex}>
                      {value}
                    </td>
                  )
                )}
              </tr>
            ))
          )}

        </tbody>

      </table>

    </div>
  );
}


function ActivityItem({
  icon: Icon,
  title,
  description,
  value,
}) {
  return (
    <div className="activity-item">

      <div className="activity-icon">
        <Icon size={15} />
      </div>

      <div className="activity-content">

        <strong>
          {title}
        </strong>

        <span>
          {description}
        </span>

      </div>

      <div className="activity-value">
        {value}
      </div>

    </div>
  );
}


function EmptyState({ text }) {
  return (
    <div className="empty-state">
      <Database size={20} />
      <span>{text}</span>
    </div>
  );
}


export default Dashboard;