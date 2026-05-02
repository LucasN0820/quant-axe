"use client";

import ReactECharts from "echarts-for-react";
import type { KlinePoint } from "@/lib/market-data";

type KlineChartProps = {
  data: KlinePoint[];
};

function movingAverage(dayCount: number, data: KlinePoint[]) {
  return data.map((_, index) => {
    if (index < dayCount - 1) {
      return null;
    }

    const sum = data
      .slice(index - dayCount + 1, index + 1)
      .reduce((total, point) => total + point.close, 0);

    return Number((sum / dayCount).toFixed(2));
  });
}

export function KlineChart({ data }: KlineChartProps) {
  const visibleData = data;
  const option = {
    animation: true,
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "cross" },
      backgroundColor: "rgba(10, 14, 18, 0.92)",
      borderColor: "rgba(148, 163, 184, 0.22)",
      textStyle: { color: "#d9e4ef" },
    },
    legend: {
      top: 4,
      right: 12,
      textStyle: { color: "#8fa2b7" },
      data: ["K线", "MA5", "MA10", "成交量"],
    },
    grid: [
      { left: 48, right: 18, top: 38, height: "58%" },
      { left: 48, right: 18, top: "74%", height: "16%" },
    ],
    xAxis: [
      {
        type: "category",
        data: visibleData.map((point) => point.date),
        boundaryGap: true,
        axisLine: { lineStyle: { color: "rgba(148, 163, 184, 0.24)" } },
        axisLabel: { color: "#6f8196" },
      },
      {
        type: "category",
        gridIndex: 1,
        data: visibleData.map((point) => point.date),
        axisLabel: { show: false },
        axisLine: { lineStyle: { color: "rgba(148, 163, 184, 0.14)" } },
      },
    ],
    yAxis: [
      {
        scale: true,
        splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.10)" } },
        axisLabel: { color: "#6f8196" },
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        splitLine: { show: false },
        axisLabel: { color: "#6f8196" },
      },
    ],
    series: [
      {
        name: "K线",
        type: "candlestick",
        data: visibleData.map((point) => [point.open, point.close, point.low, point.high]),
        itemStyle: {
          color: "#26a69a",
          color0: "#ef5350",
          borderColor: "#26a69a",
          borderColor0: "#ef5350",
        },
      },
      {
        name: "MA5",
        type: "line",
        data: movingAverage(5, visibleData),
        smooth: true,
        symbol: "none",
        lineStyle: { width: 1.6, color: "#f2c94c" },
      },
      {
        name: "MA10",
        type: "line",
        data: movingAverage(10, visibleData),
        smooth: true,
        symbol: "none",
        lineStyle: { width: 1.6, color: "#4dabf7" },
      },
      {
        name: "成交量",
        type: "bar",
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: visibleData.map((point) => point.volume),
        itemStyle: { color: "rgba(70, 211, 165, 0.38)" },
      },
    ],
  };

  return (
    <ReactECharts
      option={option}
      style={{ height: "100%", minHeight: 360, width: "100%" }}
      notMerge
    />
  );
}
