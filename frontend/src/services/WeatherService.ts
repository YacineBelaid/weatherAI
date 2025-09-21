import axios from "axios";
import { WeatherResponse, WeatherQuery } from "../types";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

class WeatherService {
  private static api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
      "Content-Type": "application/json",
    },
  });

  static async askWeather(query: string, userLocation?: string | null): Promise<WeatherResponse> {
    try {
      const response = await this.api.post<WeatherResponse>("/ask", { 
        query,
        user_location: userLocation || null
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response) {
          throw new Error(`Server error: ${error.response.status}`);
        } else if (error.request) {
          throw new Error(
            "No response from server. Please check if the backend is running."
          );
        } else {
          throw new Error(`Request error: ${error.message}`);
        }
      }
      throw new Error("An unexpected error occurred");
    }
  }

  static async healthCheck(): Promise<boolean> {
    try {
      const response = await this.api.get("/health");
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }
}

export default WeatherService;
