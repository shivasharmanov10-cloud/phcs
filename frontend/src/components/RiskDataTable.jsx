
import {
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  Package,
} from "lucide-react";

function RiskDataTable({ rows = [] }) {
  if (!rows.length) {
    return (
      <div className="empty-state">
        <Package size={28} />

        <h3>No risk records available</h3>

        <p>
          The backend has not returned any
          medicine stock-risk records.
        </p>
      </div>
    );
  }

  const getRiskClass = (risk) => {
    const value = String(risk || "")
      .toLowerCase();

    if (value === "high") return "risk-high";
    if (value === "medium") return "risk-medium";
    return "risk-low";
  };

  const getRiskIcon = (risk) => {
    const value = String(risk || "")
      .toLowerCase();

    if (value === "high") {
      return <AlertTriangle size={15} />;
    }

    if (value === "medium") {
      return <ArrowDown size={15} />;
    }

    return <ArrowUp size={15} />;
  };

  return (
    <div className="risk-table-wrapper">

      <table className="risk-table">

        <thead>
          <tr>
            <th>Date</th>
            <th>PHC</th>
            <th>Medicine</th>
            <th>Stock</th>
            <th>Daily Demand</th>
            <th>Stock Coverage</th>
            <th>Risk</th>
          </tr>
        </thead>

        <tbody>

          {rows.map((row, index) => {

            const stock =
              Number(row.stock_quantity || 0);

            const demand =
              Number(row.daily_demand || 0);

            const stockDays =
              demand > 0
                ? stock / demand
                : null;

            const risk =
              row.risk_level ||
              "LOW";

            return (
              <tr
                key={`${row.date}-${row.phc_id}-${row.medicine_id}-${index}`}
                className="table-row-animated"
              >

                <td>
                  {row.date || "—"}
                </td>

                <td>
                  <span className="phc-badge">
                    {row.phc_id || "—"}
                  </span>
                </td>

                <td>
                  <div className="medicine-cell">

                    <strong>
                      {row.medicine_name ||
                        "Unknown Medicine"}
                    </strong>

                    <small>
                      {row.medicine_id || "—"}
                    </small>

                  </div>
                </td>

                <td>
                  {stock.toLocaleString()}
                </td>

                <td>
                  {demand.toLocaleString()}
                </td>

                <td>
                  {stockDays === null
                    ? "—"
                    : `${stockDays.toFixed(1)} days`}
                </td>

                <td>
                  <span
                    className={`risk-badge ${getRiskClass(
                      risk
                    )}`}
                  >
                    {getRiskIcon(risk)}

                    {String(risk).toUpperCase()}
                  </span>
                </td>

              </tr>
            );
          })}

        </tbody>

      </table>

    </div>
  );
}

export default RiskDataTable;