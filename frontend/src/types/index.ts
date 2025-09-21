export interface WeatherResponse {
  response: string;
  status: string;
  parsed_query: {
    original_query: string;
    intent: string;
    location?: string;
    confidence: number;
    processing_method: string;
  };
  weather_data?: {
    location: string;
    temperature?: string;
    condition?: string;
    source: string;
    success: boolean;
    error?: string;
  };
  processing_method: string;
  requires_location?: boolean;
  suggested_actions?: string[];
}

export interface WeatherQuery {
  query: string;
  user_location?: string | null;
  chat_history?: Array<{ role: string; content: string }>;
}
