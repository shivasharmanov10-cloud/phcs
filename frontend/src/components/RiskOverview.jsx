
function RiskOverview({ risk }) {
  const high = Number(risk?.high || 0);
  const medium = Number(risk?.medium || 0);
  const low = Number(risk?.low || 0);

  const total = high + medium + low || 1;

  const highPercent =
    ((high / total) * 100).toFixed(0);

  const mediumPercent =
    ((medium / total) * 100).toFixed(0);

  const lowPercent =
    ((low / total) * 100).toFixed(0);

  return (
    <div className="panel">

      <div className="panel-header">

        <div>
          <h2>Medicine Risk Overview</h2>
          <p>
            Current stock intelligence
          </p>
        </div>

      </div>

      <div className="risk-list">

        <div className="risk-row">

          <div className="risk-label">
            <span>High Risk</span>
            <strong>
              {high} ({highPercent}%)
            </strong>
          </div>

          <div className="risk-bar">
            <div
              className="risk-fill high"
              style={{
                width: `${highPercent}%`,
              }}
            />
          </div>

        </div>

        <div className="risk-row">

          <div className="risk-label">
            <span>Medium Risk</span>
            <strong>
              {medium} ({mediumPercent}%)
            </strong>
          </div>

          <div className="risk-bar">
            <div
              className="risk-fill medium"
              style={{
                width: `${mediumPercent}%`,
              }}
            />
          </div>

        </div>

        <div className="risk-row">

          <div className="risk-label">
            <span>Low Risk</span>
            <strong>
              {low} ({lowPercent}%)
            </strong>
          </div>

          <div className="risk-bar">
            <div
              className="risk-fill low"
              style={{
                width: `${lowPercent}%`,
              }}
            />
          </div>

        </div>

      </div>

    </div>
  );
}

export default RiskOverview;