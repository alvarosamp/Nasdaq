import { useEffect, useRef } from 'react';
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Tooltip,
  Legend,
  type ChartTypeRegistry,
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import { CandlestickController, CandlestickElement } from 'chartjs-chart-financial';
import type { ChartData } from '../types';

Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Tooltip,
  Legend,
  CandlestickController,
  CandlestickElement,
);

function buildCandles(data: ChartData) {
  return data.timestamps
    .map((ts, i) => ({
      x: new Date(ts).getTime(),
      o: data.open[i],
      h: data.high[i],
      l: data.low[i],
      c: data.close[i],
    }))
    .filter((c) => c.o !== null && c.h !== null && c.l !== null && c.c !== null) as {
    x: number;
    o: number;
    h: number;
    l: number;
    c: number;
  }[];
}

function buildLinePoints(timestamps: string[], values: (number | null)[]) {
  return timestamps.map((ts, i) => ({ x: new Date(ts).getTime(), y: values[i] }));
}

export function CandlestickChart({ data, symbol }: { data: ChartData; symbol: string }) {
  const priceRef = useRef<HTMLCanvasElement>(null);
  const rsiRef = useRef<HTMLCanvasElement>(null);
  const macdRef = useRef<HTMLCanvasElement>(null);
  const chartsRef = useRef<{ price?: Chart; rsi?: Chart; macd?: Chart }>({});

  useEffect(() => {
    const candles = buildCandles(data);

    if (priceRef.current) {
      chartsRef.current.price?.destroy();
      chartsRef.current.price = new Chart(priceRef.current, {
        type: 'candlestick' as keyof ChartTypeRegistry,
        data: {
          datasets: [
            { label: symbol, data: candles } as never,
            {
              type: 'line',
              label: 'EMA9',
              data: buildLinePoints(data.timestamps, data.ema_fast),
              borderColor: '#16a34a',
              pointRadius: 0,
              borderWidth: 1,
            },
            {
              type: 'line',
              label: 'EMA21',
              data: buildLinePoints(data.timestamps, data.ema_slow),
              borderColor: '#dc2626',
              pointRadius: 0,
              borderWidth: 1,
            },
          ],
        },
        options: { animation: false, scales: { x: { type: 'time' } } },
      });
    }

    if (rsiRef.current) {
      chartsRef.current.rsi?.destroy();
      chartsRef.current.rsi = new Chart(rsiRef.current, {
        type: 'line',
        data: {
          datasets: [
            { label: 'RSI', data: buildLinePoints(data.timestamps, data.rsi), borderColor: '#9333ea', pointRadius: 0 },
          ],
        },
        options: { animation: false, scales: { x: { type: 'time' }, y: { min: 0, max: 100 } } },
      });
    }

    if (macdRef.current) {
      chartsRef.current.macd?.destroy();
      chartsRef.current.macd = new Chart(macdRef.current, {
        type: 'line',
        data: {
          datasets: [
            { label: 'MACD', data: buildLinePoints(data.timestamps, data.macd), borderColor: '#2563eb', pointRadius: 0 },
            {
              label: 'Signal',
              data: buildLinePoints(data.timestamps, data.macd_signal),
              borderColor: '#f59e0b',
              pointRadius: 0,
            },
          ],
        },
        options: { animation: false, scales: { x: { type: 'time' } } },
      });
    }

    return () => {
      chartsRef.current.price?.destroy();
      chartsRef.current.rsi?.destroy();
      chartsRef.current.macd?.destroy();
    };
  }, [data, symbol]);

  return (
    <>
      <canvas ref={priceRef} height={140} />
      <canvas ref={rsiRef} height={80} />
      <canvas ref={macdRef} height={80} />
    </>
  );
}
