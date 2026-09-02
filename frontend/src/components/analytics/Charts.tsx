import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
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
import { HistoryDataPoint } from "../../types/types";

const COLORS = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];

interface TimeSeriesChartProps {
  data: HistoryDataPoint[];
  dataKeys: Array<{
    key: keyof HistoryDataPoint;
    name: string;
    color: string;
  }>;
  height?: number;
  type?: "line" | "area";
}

export function TimeSeriesChart({ data, dataKeys, height = 200, type = "line" }: TimeSeriesChartProps) {
  if (data.length === 0) return null;

  const formattedData = data.map((d) => ({
    ...d,
    day: `Day ${d.day}`,
  }));

  const Chart = type === "area" ? AreaChart : LineChart;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <Chart data={formattedData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="day" tick={{ fontSize: 10, fill: "#94a3b8" }} />
        <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1e293b",
            border: "1px solid #475569",
            borderRadius: "8px",
            fontSize: "12px",
          }}
        />
        <Legend wrapperStyle={{ fontSize: "11px" }} />
        {dataKeys.map((dk) =>
          type === "area" ? (
            <Area
              key={dk.key as string}
              type="monotone"
              dataKey={dk.key as string}
              name={dk.name}
              stroke={dk.color}
              fill={dk.color}
              fillOpacity={0.2}
            />
          ) : (
            <Line
              key={dk.key as string}
              type="monotone"
              dataKey={dk.key as string}
              name={dk.name}
              stroke={dk.color}
              dot={false}
            />
          )
        )}
      </Chart>
    </ResponsiveContainer>
  );
}

interface BarChartProps {
  data: Array<{ name: string; value: number; color?: string }>;
  height?: number;
  dataKey?: string;
  nameKey?: string;
}

export function SimpleBarChart({ data, height = 200, dataKey = "value", nameKey = "name" }: BarChartProps) {
  if (data.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey={nameKey} tick={{ fontSize: 10, fill: "#94a3b8" }} />
        <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1e293b",
            border: "1px solid #475569",
            borderRadius: "8px",
            fontSize: "12px",
          }}
        />
        <Bar dataKey={dataKey} fill="#3b82f6" radius={[4, 4, 0, 0]}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color || COLORS[index % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

interface DonutChartProps {
  data: Array<{ name: string; value: number }>;
  height?: number;
  colors?: string[];
}

export function DonutChart({ data, height = 200, colors = COLORS }: DonutChartProps) {
  if (data.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={40}
          outerRadius={70}
          paddingAngle={2}
          dataKey="value"
          label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
          labelLine={false}
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: "#1e293b",
            border: "1px solid #475569",
            borderRadius: "8px",
            fontSize: "12px",
          }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
