export type UniverseBase = "all_a" | "hs300" | "zz500" | "zz1000" | "custom";

export type UniverseFilterType =
  | "st"
  | "suspension"
  | "listed_days"
  | "liquidity"
  | "price"
  | "limit_up_down";

export type UniverseFilter = {
  type: UniverseFilterType;
  min_days?: number;
  min_turnover?: number;
  min_price?: number;
  max_price?: number;
};

export type Universe = {
  id: string;
  name: string;
  base: UniverseBase;
  filters: UniverseFilter[];
  created_at: string;
  updated_at: string;
};

export type UniverseMember = {
  date: string;
  universe_id?: string;
  symbol: string;
  name: string;
  included: boolean;
  excluded_reason?: string | null;
  can_buy: boolean;
  can_sell: boolean;
  flags: string[];
};

export type UniverseListPayload = {
  source: string;
  status: string;
  message?: string;
  data: Universe[];
};

export type UniverseMembersPayload = {
  source: string;
  status: string;
  universe: Universe;
  date: string;
  total: number;
  included: number;
  excluded: number;
  saved?: number;
  message?: string;
  data: UniverseMember[];
};
