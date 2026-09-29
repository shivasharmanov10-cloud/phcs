
import {
  CheckCircle2,
  Database,
  Search,
  TrendingUp,
  Truck,
} from "lucide-react";

function MLPipeline({
  summary,
}) {
  const anomalies =
    summary?.anomalies ?? 0;

  const recommendations =
    summary?.redistribution_recommendations ??
    0;

  return (
    <div className="panel">

      <div className="panel-header">

        <div>
          <h2>ML Intelligence Pipeline</h2>
          <p>Automated analysis status</p>
        </div>

      </div>

      <div className="pipeline">

        <div className="pipeline-step">

          <div className="pipeline-icon">
            <Database size={18} />
          </div>

          <div>
            <strong>Data ingestion</strong>
            <span>
              PHC medicine data loaded
            </span>
          </div>

          <CheckCircle2 className="pipeline-check" />

        </div>

        <div className="pipeline-line"></div>

        <div className="pipeline-step">

          <div className="pipeline-icon">
            <Search size={18} />
          </div>

          <div>
            <strong>Anomaly detection</strong>
            <span>
              {anomalies} anomalies detected
            </span>
          </div>

          <CheckCircle2 className="pipeline-check" />

        </div>

        <div className="pipeline-line"></div>

        <div className="pipeline-step">

          <div className="pipeline-icon">
            <TrendingUp size={18} />
          </div>

          <div>
            <strong>Demand forecasting</strong>
            <span>
              1632 predictions generated
            </span>
          </div>

          <CheckCircle2 className="pipeline-check" />

        </div>

        <div className="pipeline-line"></div>

        <div className="pipeline-step">

          <div className="pipeline-icon">
            <Truck size={18} />
          </div>

          <div>
            <strong>Redistribution engine</strong>
            <span>
              {recommendations} recommendations
            </span>
          </div>

          <CheckCircle2 className="pipeline-check" />

        </div>

      </div>

    </div>
  );
}

export default MLPipeline;