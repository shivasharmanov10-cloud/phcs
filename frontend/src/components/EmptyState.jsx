
import { Database } from "lucide-react";

function EmptyState({
  message = "No data available.",
}) {
  return (
    <div className="empty-state">

      <Database size={34} />

      <h3>No data found</h3>

      <p>{message}</p>

    </div>
  );
}

export default EmptyState;