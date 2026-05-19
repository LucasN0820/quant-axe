"use client";

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

export function KlineChart({ data }: KlineChartProps) {
  const visibleData = data;
  const start = visibleData.length > 80 ? 45 : 0;
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
        borderColor: "rgba(148, 163, 184, 0.18)",
        fillerColor: "rgba(70, 211, 165, 0.16)",
        handleStyle: {
          color: "#46d3a5",
          borderColor: "#46d3a5",
        },
        moveHandleStyle: {
          color: "rgba(70, 211, 165, 0.35)",
        },
        dataBackground: {
          lineStyle: { color: "rgba(148, 163, 184, 0.24)" },
          areaStyle: { color: "rgba(148, 163, 184, 0.08)" },
        },
        selectedDataBackground: {
          lineStyle: { color: "rgba(70, 211, 165, 0.38)" },
          areaStyle: { color: "rgba(70, 211, 165, 0.12)" },
        },
        textStyle: { color: "#6f8196" },
      },
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
