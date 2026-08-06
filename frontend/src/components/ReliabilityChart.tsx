import { useEffect, useRef } from 'react';
import { useTheme } from '../context/ThemeContext';
import {
  Chart,
  BarController,
  BarElement,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
} from 'chart.js';
import type { ReliabilityScoreboard } from '../types';

Chart.register(
  BarController,
  BarElement,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
);

interface ReliabilityChartProps {
  data: ReliabilityScoreboard;
}

export function ReliabilityChart({ data }: ReliabilityChartProps) {
  const { theme } = useTheme();
  const calibrationRef = useRef<HTMLCanvasElement>(null);
  const trendRef = useRef<HTMLCanvasElement>(null);
  const chartsRef = useRef<{ calibration?: Chart; trend?: Chart }>({});

  useEffect(() => {
    const charts = chartsRef.current;
    const isDark = theme === 'dark';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';
    const textColor = isDark ? '#a1a1aa' : '#64748b';
    const predictedColor = isDark ? 'rgba(99, 102, 241, 0.55)' : 'rgba(99, 102, 241, 0.45)';
    const actualColor = isDark ? '#22c55e' : '#16a34a';

    const calibrated = data.calibration.filter((bucket) => bucket.samples > 0);

    if (calibrationRef.current) {
      charts.calibration?.destroy();
      charts.calibration = new Chart(calibrationRef.current, {
        type: 'bar',
        data: {
          labels: calibrated.map((bucket) => `${bucket.label} (n=${bucket.samples})`),
          datasets: [
            {
              label: 'Confiança prevista',
              data: calibrated.map((bucket) => bucket.midpoint_confidence),
              backgroundColor: predictedColor,
            },
            {
              label: 'Acerto real',
              data: calibrated.map((bucket) => bucket.actual_win_rate_pct ?? 0),
              backgroundColor: actualColor,
            },
          ],
        },
        options: {
          animation: false,
          maintainAspectRatio: false,
          scales: {
            x: { grid: { display: false }, ticks: { color: textColor } },
            y: { min: 0, max: 100, grid: { color: gridColor }, ticks: { color: textColor } },
          },
          plugins: { legend: { labels: { color: textColor } } },
        },
      });
    }

    if (trendRef.current) {
      charts.trend?.destroy();
      charts.trend = new Chart(trendRef.current, {
        type: 'line',
        data: {
          labels: data.trend.map((point) => point.period_label),
          datasets: [
            {
              label: 'Taxa de acerto por lote',
              data: data.trend.map((point) => point.win_rate_pct),
              borderColor: actualColor,
              backgroundColor: actualColor,
              tension: 0.25,
              pointRadius: 3,
            },
          ],
        },
        options: {
          animation: false,
          maintainAspectRatio: false,
          scales: {
            x: { grid: { display: false }, ticks: { color: textColor } },
            y: { min: 0, max: 100, grid: { color: gridColor }, ticks: { color: textColor } },
          },
          plugins: { legend: { labels: { color: textColor } } },
        },
      });
    }

    return () => {
      charts.calibration?.destroy();
      charts.trend?.destroy();
    };
  }, [data, theme]);

  if (!data.total_samples) {
    return <p className="muted">Registre algumas leituras e aguarde a checagem de resultado (5 pregões) para o placar aparecer.</p>;
  }

  return (
    <div className="reliability-scoreboard">
      <div className="reliability-summary">
        <span>Amostras checadas</span>
        <strong>{data.total_samples}</strong>
        <span>Acerto geral</span>
        <strong>{data.overall_win_rate_pct}%</strong>
      </div>
      <div className="reliability-charts">
        <div>
          <h3>Calibração: confiança dita x acerto real</h3>
          <canvas ref={calibrationRef} height={160} />
        </div>
        <div>
          <h3>Evolução do acerto (lotes de recomendações)</h3>
          <canvas ref={trendRef} height={160} />
        </div>
      </div>
    </div>
  );
}
