"use client";

import { useEffect, useMemo, useState } from "react";
import ReactECharts from "echarts-for-react";
import type { KlinePoint } from "@/lib/market-types";

type KlineChartProps = {
  data: KlinePoint[];
};

function movingAverage(dayCount: number, data: KlinePoint[]) {
  return data.map((_, index) => {
    const start = Math.max(0, index - dayCount + 1);
    const window = data.slice(start, index + 1);

    const sum = window.reduce((total, point) => total + point.close, 0);

    return Number((sum / window.length).toFixed(2));
  });
}

function readChartTheme() {
  if (typeof window === "undefined") {
    return {
      foreground: "#141413",
      muted: "#87867f",
      border: "#dedcd1",
      surface: "#ffffff",
      accent: "#c96442",
      down: "#2f7f68",
    };
  }

  const styles = window.getComputedStyle(document.documentElement);
  return {
    foreground: styles.getPropertyValue("--foreground").trim() || "#141413",
    muted: styles.getPropertyValue("--muted").trim() || "#87867f",
    border: styles.getPropertyValue("--border").trim() || "#dedcd1",
    surface: styles.getPropertyValue("--surface").trim() || "#ffffff",
    accent: styles.getPropertyValue("--accent").trim() || "#c96442",
    down: styles.getPropertyValue("--chart-down").trim() || "#2f7f68",
  };
}

export function KlineChart({ data }: KlineChartProps) {
  const [chartTheme, setChartTheme] = useState(readChartTheme);
  const visibleData = data;
  const start = visibleData.length > 80 ? 45 : 0;

  useEffect(() => {
    const syncChartTheme = () => setChartTheme(readChartTheme());
    const frame = window.requestAnimationFrame(syncChartTheme);
    const observer = new MutationObserver(syncChartTheme);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
    return () => {
      window.cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, []);

  const option = useMemo(() => ({
    animation: true,
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "cross" },
      backgroundColor: chartTheme.surface,
      borderColor: chartTheme.border,
      textStyle: { color: chartTheme.foreground },
    },
    legend: {
      top: 4,
      right: 12,
      textStyle: { color: chartTheme.muted },
      data: ["K线", "MA5", "MA10", "成交量"],
    },
    grid: [
      { left: 48, right: 18, top: 38, height: "54%" },
      { left: 48, right: 18, top: "71%", height: "14%" },
    ],
    dataZoom: [
      {
        type: "inside",
        xAxisIndex: [0, 1],
        start,
        end: 100,
        minSpan: 8,
        zoomOnMouseWheel: true,
        moveOnMouseMove: true,
        moveOnMouseWheel: true,
      },
      {
        type: "slider",
        xAxisIndex: [0, 1],
        start,
        end: 100,
        minSpan: 8,
        height: 22,
        bottom: 10,
        borderColor: chartTheme.border,
        fillerColor: "rgba(201, 100, 66, 0.16)",
        handleStyle: {
          color: chartTheme.accent,
          borderColor: chartTheme.accent,
        },
        moveHandleStyle: {
          color: "rgba(201, 100, 66, 0.28)",
        },
        dataBackground: {
          lineStyle: { color: chartTheme.border },
          areaStyle: { color: "rgba(135, 134, 127, 0.10)" },
        },
        selectedDataBackground: {
          lineStyle: { color: chartTheme.accent },
          areaStyle: { color: "rgba(201, 100, 66, 0.12)" },
        },
        textStyle: { color: chartTheme.muted },
      },
    ],
    xAxis: [
      {
        type: "category",
        data: visibleData.map((point) => point.date),
        boundaryGap: true,
        axisLine: { lineStyle: { color: chartTheme.border } },
        axisLabel: { color: chartTheme.muted },
      },
      {
        type: "category",
        gridIndex: 1,
        data: visibleData.map((point) => point.date),
        axisLabel: { show: false },
        axisLine: { lineStyle: { color: chartTheme.border } },
      },
    ],
    yAxis: [
      {
        scale: true,
        splitLine: { lineStyle: { color: "rgba(135, 134, 127, 0.16)" } },
        axisLabel: { color: chartTheme.muted },
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        splitLine: { show: false },
        axisLabel: { color: chartTheme.muted },
      },
    ],
    series: [
      {
        name: "K线",
        type: "candlestick",
        data: visibleData.map((point) => [point.open, point.close, point.low, point.high]),
        itemStyle: {
          color: chartTheme.down,
          color0: chartTheme.accent,
          borderColor: chartTheme.down,
          borderColor0: chartTheme.accent,
        },
      },
      {
        name: "MA5",
        type: "line",
        data: movingAverage(5, visibleData),
        smooth: true,
        symbol: "none",
        lineStyle: { width: 1.6, color: "#b86f22" },
      },
      {
        name: "MA10",
        type: "line",
        data: movingAverage(10, visibleData),
        smooth: true,
        symbol: "none",
        lineStyle: { width: 1.6, color: "#629987" },
      },
      {
        name: "成交量",
        type: "bar",
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: visibleData.map((point) => point.volume),
        itemStyle: { color: "rgba(201, 100, 66, 0.32)" },
      },
    ],
  }), [chartTheme, start, visibleData]);

  return (
    <ReactECharts
      option={option}
      style={{ height: "100%", minHeight: 360, width: "100%" }}
      notMerge
    />
  );
}
