import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line,
  PieChart, Pie, Cell, Sector,
} from 'recharts'

// WOMBAT earth-tone palette for chart series
const CHART_COLORS = [
  '#5c3a1e', '#8b6340', '#c4a882', '#4a7c1f', '#6b9e3f',
  '#2060c0', '#e8a020', '#c0392b', '#9a7a5a',
]

const TIME_RANGES = [
  { label: '7 days', value: 7 },
  { label: '30 days', value: 30 },
  { label: 'All time', value: 0 },
]

// Active shape renderer for the donut chart
function renderActiveShape(props) {
  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill, payload, percent } = props
  return (
    <g>
      <text x={cx} y={cy - 10} textAnchor="middle" fill="#2c1810" fontSize={14} fontWeight={700}>
        {payload.species}
      </text>
      <text x={cx} y={cy + 14} textAnchor="middle" fill="#7a5c3e" fontSize={13}>
        {payload.count} ({(percent * 100).toFixed(1)}%)
      </text>
      <Sector
        cx={cx} cy={cy} innerRadius={innerRadius} outerRadius={outerRadius + 8}
        startAngle={startAngle} endAngle={endAngle} fill={fill}
      />
      <Sector
        cx={cx} cy={cy} innerRadius={outerRadius + 12} outerRadius={outerRadius + 16}
        startAngle={startAngle} endAngle={endAngle} fill={fill}
      />
    </g>
  )
}

export default function Dashboard() {
  const [overview, setOverview] = useState(null)
  const [timeSeries, setTimeSeries] = useState({ data: [], species: [] })
  const [composition, setComposition] = useState([])
  const [activityByHour, setActivityByHour] = useState([])
  const [timeRange, setTimeRange] = useState(7)
  const [activePieIndex, setActivePieIndex] = useState(0)
  const [loading, setLoading] = useState(true)

  // Fetch all stats
  useEffect(() => {
    setLoading(true)
    Promise.all([
      fetch('/api/stats/overview').then(r => r.json()),
      fetch(`/api/stats/species-over-time?days=${timeRange}`).then(r => r.json()),
      fetch('/api/stats/species-composition').then(r => r.json()),
      fetch('/api/stats/activity-by-hour').then(r => r.json()),
    ]).then(([ov, ts, comp, hourly]) => {
      setOverview(ov)
      setTimeSeries(ts)
      setComposition(comp)
      setActivityByHour(hourly)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [timeRange])

  if (loading && !overview) {
    return <p className="empty-state">Loading analytics…</p>
  }

  return (
    <div className="dashboard">
      {/* Quick stats row */}
      {overview && (
        <div className="stats-row">
          <div className="stat-card">
            <span className="stat-value">{overview.total_detections}</span>
            <span className="stat-label">Total detections</span>
          </div>
          <div className="stat-card">
            <span className="stat-value stat-verified">{overview.verified_count}</span>
            <span className="stat-label">Verified</span>
          </div>
          <div className="stat-card">
            <span className="stat-value stat-pending">{overview.pending_count}</span>
            <span className="stat-label">Pending review</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{overview.species_count}</span>
            <span className="stat-label">Species detected</span>
          </div>
        </div>
      )}

      {/* Species over time */}
      <div className="chart-panel">
        <div className="chart-header">
          <h3>Species over time</h3>
          <div className="time-range-tabs">
            {TIME_RANGES.map(({ label, value }) => (
              <button
                key={value}
                className={`filter-tab${timeRange === value ? ' active' : ''}`}
                onClick={() => setTimeRange(value)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        {timeSeries.data.length === 0 ? (
          <p className="chart-empty">No verified detections in this period.</p>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={timeSeries.data} margin={{ top: 8, right: 16, left: -8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e8ddd0" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#9a7a5a' }} tickFormatter={d => d.slice(5)} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#9a7a5a' }} />
              <Tooltip
                contentStyle={{ fontSize: 12, borderColor: '#c4a882', borderRadius: 8 }}
                labelStyle={{ color: '#5c3a1e', fontWeight: 700 }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {timeSeries.species.map((species, i) => (
                <Line
                  key={species}
                  type="monotone"
                  dataKey={species}
                  stroke={CHART_COLORS[i % CHART_COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Species composition + Activity by hour side-by-side */}
      <div className="chart-row">
        {/* Donut */}
        <div className="chart-panel chart-half">
          <h3>Species composition</h3>
          {composition.length === 0 ? (
            <p className="chart-empty">No verified detections yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  activeIndex={activePieIndex}
                  activeShape={renderActiveShape}
                  data={composition}
                  dataKey="count"
                  nameKey="species"
                  cx="50%"
                  cy="50%"
                  innerRadius={65}
                  outerRadius={100}
                  onMouseEnter={(_, index) => setActivePieIndex(index)}
                >
                  {composition.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value, name) => [`${value}`, name]}
                  contentStyle={{ fontSize: 12, borderColor: '#c4a882', borderRadius: 8 }}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Activity by hour */}
        <div className="chart-panel chart-half">
          <h3>Activity by time of day</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={activityByHour} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e8ddd0" />
              <XAxis
                dataKey="hour"
                tick={{ fontSize: 10, fill: '#9a7a5a' }}
                tickFormatter={h => `${h}:00`}
                interval={2}
              />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#9a7a5a' }} />
              <Tooltip
                formatter={(value) => [value, 'Detections']}
                labelFormatter={h => `${h}:00 – ${h}:59`}
                contentStyle={{ fontSize: 12, borderColor: '#c4a882', borderRadius: 8 }}
              />
              <Bar dataKey="count" fill="#8b6340" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
