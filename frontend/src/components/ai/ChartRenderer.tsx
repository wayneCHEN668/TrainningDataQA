import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { ChartSpec } from "../../types/chat";

interface ChartRendererProps {
  spec: ChartSpec;
}

const CHART_COLORS = [
  "#1ed760",
  "#1db954",
  "#1e88e5",
  "#f59e0b",
  "#f3727f",
  "#9b59b6",
  "#1abc9c",
  "#e67e22",
];

interface RechartsSpec {
  data?: Array<Record<string, unknown>>;
  xKey?: string;
  bars?: Array<{ dataKey: string; name?: string }>;
  lines?: Array<{ dataKey: string; name?: string }>;
  nameKey?: string;
  dataKey?: string;
  [key: string]: unknown;
}

function BarChartView({ data, xKey, bars }: RechartsSpec) {
  const d = (data as Array<Record<string, unknown>>) ?? [];
  const xk = xKey ?? "name";
  const b = bars ?? [];
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={d} margin={{ top: 8, right: 8, left: -8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#333333" />
        <XAxis
          dataKey={xk}
          tick={{ fill: "#ffffff", fontSize: 11 }}
          axisLine={{ stroke: "#333333" }}
          tickLine={{ stroke: "#333333" }}
        />
        <YAxis
          tick={{ fill: "#ffffff", fontSize: 11 }}
          axisLine={{ stroke: "#333333" }}
          tickLine={{ stroke: "#333333" }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1f1f1f",
            border: "1px solid #333333",
            borderRadius: "8px",
            color: "#ffffff",
            fontSize: "12px",
          }}
        />
        <Legend wrapperStyle={{ fontSize: "11px", color: "#b3b3b3" }} />
        {b.map((bar, i) => (
          <Bar
            key={bar.dataKey}
            dataKey={bar.dataKey}
            name={bar.name ?? bar.dataKey}
            fill={CHART_COLORS[i % CHART_COLORS.length]}
            radius={[4, 4, 0, 0]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

function LineChartView({ data, xKey, lines }: RechartsSpec) {
  const d = (data as Array<Record<string, unknown>>) ?? [];
  const xk = xKey ?? "name";
  const l = lines ?? [];
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={d} margin={{ top: 8, right: 8, left: -8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#333333" />
        <XAxis
          dataKey={xk}
          tick={{ fill: "#ffffff", fontSize: 11 }}
          axisLine={{ stroke: "#333333" }}
          tickLine={{ stroke: "#333333" }}
        />
        <YAxis
          tick={{ fill: "#ffffff", fontSize: 11 }}
          axisLine={{ stroke: "#333333" }}
          tickLine={{ stroke: "#333333" }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1f1f1f",
            border: "1px solid #333333",
            borderRadius: "8px",
            color: "#ffffff",
            fontSize: "12px",
          }}
        />
        <Legend wrapperStyle={{ fontSize: "11px", color: "#b3b3b3" }} />
        {l.map((line, i) => (
          <Line
            key={line.dataKey}
            type="monotone"
            dataKey={line.dataKey}
            name={line.name ?? line.dataKey}
            stroke={CHART_COLORS[i % CHART_COLORS.length]}
            strokeWidth={2}
            dot={{ r: 3, fill: CHART_COLORS[i % CHART_COLORS.length] }}
            activeDot={{ r: 5 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

function PieChartView({ data, nameKey, dataKey }: RechartsSpec) {
  const d = (data as Array<Record<string, unknown>>) ?? [];
  const nk = nameKey ?? "name";
  const dk = dataKey ?? "value";
  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart margin={{ top: 8, right: 8, left: -8, bottom: 8 }}>
        <Pie
          data={d}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={110}
          nameKey={nk}
          dataKey={dk}
          paddingAngle={2}
          label={({ name, value }) =>
            `${String(name)} (${value})`
          }
          labelLine={{ stroke: "#6a6a6a" }}
        >
          {d.map((_entry, i) => (
            <Cell
              key={`cell-${i}`}
              fill={CHART_COLORS[i % CHART_COLORS.length]}
            />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: "#1f1f1f",
            border: "1px solid #333333",
            borderRadius: "8px",
            color: "#ffffff",
            fontSize: "12px",
          }}
        />
        <Legend wrapperStyle={{ fontSize: "11px", color: "#b3b3b3" }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function ChartRenderer({ spec }: ChartRendererProps) {
  const rSpec = (spec.rechartsSpec ?? {}) as RechartsSpec;

  switch (spec.chartType) {
    case "bar":
      return <BarChartView {...rSpec} />;
    case "line":
      return <LineChartView {...rSpec} />;
    case "pie":
      return <PieChartView {...rSpec} />;
    default:
      return (
        <div className="flex items-center justify-center h-[280px] bg-bg-card rounded-lg">
          <p className="text-text-subdued text-sm">
            Unknown chart type: {spec.chartType}
          </p>
        </div>
      );
  }
}
