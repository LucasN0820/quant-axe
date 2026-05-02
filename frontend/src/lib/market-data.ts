export type Stock = {
  symbol: string;
  name: string;
  pinyin: string;
  price: number;
  changeRate: number;
  volume: string;
  turnover: string;
  high: number;
  low: number;
  pe: number;
  pb: number;
  roe: string;
  grossMargin: string;
  sentiment: number;
};

export type KlinePoint = {
  date: string;
  open: number;
  close: number;
  low: number;
  high: number;
  volume: number;
};

export const marketIndexes = [
  { name: "上证指数", value: "3128.42", change: 0.46 },
  { name: "深证成指", value: "9821.31", change: -0.18 },
  { name: "创业板指", value: "1964.77", change: 0.72 },
  { name: "科创50", value: "812.05", change: -0.33 },
];

export const stocks: Stock[] = [
  {
    symbol: "600519",
    name: "贵州茅台",
    pinyin: "GZMT",
    price: 1688.35,
    changeRate: 1.28,
    volume: "2.16万手",
    turnover: "36.4亿",
    high: 1702.2,
    low: 1659.8,
    pe: 27.6,
    pb: 8.9,
    roe: "31.4%",
    grossMargin: "91.8%",
    sentiment: 84,
  },
  {
    symbol: "300750",
    name: "宁德时代",
    pinyin: "NDSD",
    price: 219.48,
    changeRate: -0.74,
    volume: "18.8万手",
    turnover: "41.1亿",
    high: 223.3,
    low: 216.1,
    pe: 22.1,
    pb: 4.7,
    roe: "24.7%",
    grossMargin: "22.6%",
    sentiment: 72,
  },
  {
    symbol: "000001",
    name: "平安银行",
    pinyin: "PAYH",
    price: 10.86,
    changeRate: 0.19,
    volume: "75.3万手",
    turnover: "8.2亿",
    high: 10.94,
    low: 10.71,
    pe: 4.8,
    pb: 0.53,
    roe: "10.8%",
    grossMargin: "N/A",
    sentiment: 58,
  },
  {
    symbol: "002415",
    name: "海康威视",
    pinyin: "HKWS",
    price: 33.26,
    changeRate: 2.34,
    volume: "43.6万手",
    turnover: "14.3亿",
    high: 33.7,
    low: 32.1,
    pe: 19.4,
    pb: 3.2,
    roe: "16.6%",
    grossMargin: "44.2%",
    sentiment: 69,
  },
  {
    symbol: "601318",
    name: "中国平安",
    pinyin: "ZGPA",
    price: 45.92,
    changeRate: -1.08,
    volume: "62.9万手",
    turnover: "28.9亿",
    high: 46.8,
    low: 45.5,
    pe: 7.2,
    pb: 0.91,
    roe: "12.1%",
    grossMargin: "N/A",
    sentiment: 61,
  },
  {
    symbol: "688981",
    name: "中芯国际",
    pinyin: "ZXGJ",
    price: 54.18,
    changeRate: 3.15,
    volume: "55.4万手",
    turnover: "29.6亿",
    high: 54.9,
    low: 52.4,
    pe: 88.7,
    pb: 2.8,
    roe: "3.2%",
    grossMargin: "20.5%",
    sentiment: 91,
  },
];

export const newsItems = [
  { time: "09:42", source: "财联社", title: "白酒板块早盘拉升，机构关注春节备货预期" },
  { time: "10:08", source: "证券时报", title: "新能源产业链成交活跃，资金回流高景气赛道" },
  { time: "10:35", source: "交易所公告", title: "多家公司发布回购进展及股东增持计划" },
  { time: "11:12", source: "雪球热议", title: "AI 算力、国产芯片相关话题热度继续升温" },
];

export const hotKeywords = [
  { word: "国产算力", heat: 92 },
  { word: "高股息", heat: 86 },
  { word: "白酒修复", heat: 81 },
  { word: "机器人", heat: 74 },
  { word: "低空经济", heat: 69 },
  { word: "新能源车", heat: 63 },
  { word: "中特估", heat: 57 },
  { word: "半导体", heat: 88 },
];

export const orderBook = {
  asks: [
    ["卖五", 1690.8, 62],
    ["卖四", 1690.2, 48],
    ["卖三", 1689.7, 81],
    ["卖二", 1689.1, 35],
    ["卖一", 1688.8, 96],
  ],
  bids: [
    ["买一", 1688.3, 104],
    ["买二", 1687.9, 72],
    ["买三", 1687.4, 51],
    ["买四", 1686.8, 42],
    ["买五", 1686.2, 66],
  ],
};

export const trades = [
  { time: "11:28:21", price: 1688.35, volume: 12, side: "买入" },
  { time: "11:28:18", price: 1688.1, volume: 8, side: "卖出" },
  { time: "11:28:11", price: 1688.9, volume: 16, side: "买入" },
  { time: "11:27:58", price: 1687.8, volume: 5, side: "卖出" },
  { time: "11:27:49", price: 1688.2, volume: 10, side: "买入" },
];

export function getStock(symbol: string) {
  return stocks.find((stock) => stock.symbol === symbol) ?? stocks[0];
}

export function getKline(symbol: string): KlinePoint[] {
  const seed = Number(symbol.slice(-2)) || 18;
  const base = getStock(symbol).price * 0.94;

  return Array.from({ length: 42 }, (_, index) => {
    const wave = Math.sin((index + seed) / 4) * base * 0.018;
    const drift = index * base * 0.0018;
    const open = base + wave + drift;
    const close = open + Math.cos((index + seed) / 3) * base * 0.012;
    const high = Math.max(open, close) + base * (0.008 + (index % 5) * 0.001);
    const low = Math.min(open, close) - base * (0.007 + (index % 4) * 0.001);
    const date = new Date(2026, 2, 16 + index).toISOString().slice(5, 10);

    return {
      date,
      open: Number(open.toFixed(2)),
      close: Number(close.toFixed(2)),
      low: Number(low.toFixed(2)),
      high: Number(high.toFixed(2)),
      volume: Math.round(8000 + Math.abs(Math.sin(index / 3)) * 22000 + seed * 80),
    };
  });
}
