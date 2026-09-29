
function StatCard({
  icon: Icon,
  label,
  value,
  description,
  variant = "blue",
}) {
  return (
    <div className={`stat-card stat-${variant}`}>

      <div className="stat-card-top">

        <div className="stat-icon">
          <Icon size={21} />
        </div>

        <span>{label}</span>

      </div>

      <div className="stat-value">
        {value}
      </div>

      <div className="stat-description">
        {description}
      </div>

    </div>
  );
}

export default StatCard;