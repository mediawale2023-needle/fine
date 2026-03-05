export default function ScoreGauge({ value, label, size = 100, color = "#059669" }) {
  const percentage = Math.round(value * 100);
  const circumference = 2 * Math.PI * 40;
  const strokeDashoffset = circumference - (value * circumference);

  const getColor = () => {
    if (value >= 0.7) return "#059669"; // green
    if (value >= 0.4) return "#D97706"; // amber
    return "#DC2626"; // red
  };

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} viewBox="0 0 100 100" className="-rotate-90">
        {/* Background circle */}
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke="#F1F5F9"
          strokeWidth="8"
        />
        {/* Progress circle */}
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke={color || getColor()}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center" style={{ width: size, height: size }}>
        <span className="text-2xl font-bold text-slate-900">{percentage}%</span>
      </div>
      {label && (
        <span className="mt-2 text-xs uppercase tracking-wider text-slate-500 font-medium">{label}</span>
      )}
    </div>
  );
}
