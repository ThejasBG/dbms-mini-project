export type Game = {
  id: number;
  title: string;
  description: string;
  genres: string[];
  platforms: string[];
  pricing_model: string;
  cover_url?: string | null;
  created_at?: string;
  review_count?: number;
  average_rating?: number | string | null;
  similarity?: number;
  added_at?: string;
};

export type Review = {
  id: number;
  username: string;
  rating: number;
  body: string;
  is_fictional: boolean;
  created_at: string;
};

export type User = {
  id: number;
  username: string;
  email: string | null;
  role: "player" | "admin";
};

export type GameListResponse = {
  games: Game[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};
