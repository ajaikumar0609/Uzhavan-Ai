# FP-003 — Weather Agent

**Status:** `PLANNING`
**Sprint:** Sprint-004
**Milestone:** M-06 — Weather Agent
**Owner:** TL Agent

---

## 1. Requirement
Farmers need to know today's weather and the 7-day forecast for their district — before deciding whether to spray, irrigate, or sow. UZHAVAN AI fetches data from Open-Meteo (free, no API key) and gives advisory: "Rain expected tomorrow — don't spray fungicide today, wait until Thursday."

---

## 2. User Story
```
As a Tamil Nadu farmer
I want to see the weather forecast for my district
So that I can plan spraying, irrigation, and sowing around the rain
```

---

## 3. Acceptance Criteria

- [ ] AC-1: Weather card on Home screen shows today: temp (°C), rain (mm), humidity (%), condition icon
- [ ] AC-2: 7-day forecast visible with rain probability per day
- [ ] AC-3: If rain > 5mm expected within 24 hours → Tamil alert: "நாளை மழை எதிர்பார்க்கப்படுகிறது — இன்று பூச்சிக்கொல்லி தெளிக்காதீர்கள்"
- [ ] AC-4: Weather tool available in /chat — farmer can ask "நாளை மழை வருமா?" and get answer from weather data
- [ ] AC-5: Weather cached in Redis for 1 hour (don't hit Open-Meteo on every request)
- [ ] AC-6: If Open-Meteo unreachable → show last cached data with "கடந்த [time] தேதியிட்ட தரவு" label

**Out of Scope (v1):**
- Pest risk index from weather
- Historical rainfall data
- SMS rain alerts

---

## 4. API Contract
```
GET /weather/{district}
Returns: {
  "district":   "Thanjavur",
  "current":    { "temp_c": 32, "rain_mm": 0, "humidity_pct": 75, "condition": "Partly cloudy" },
  "forecast":   [{ "date": "2026-07-08", "rain_mm": 12, "rain_probability": 0.8, ... }, ...],
  "advice":     "நாளை மழை எதிர்பார்க்கப்படுகிறது. பூச்சிக்கொல்லி தெளிப்பை ஒத்திவையுங்கள்.",
  "cached_at":  "2026-07-07T06:00:00Z"
}

Data source: Open-Meteo API (free, no key)
District → lat/lon: From district_profiles table (PostGIS centroids)
```

---

## 5. Database Changes
```
Table:     weather_cache (already in schema)
Migration: None needed
New:       District lat/lon already in district_profiles.geom
```

---

## 6. AI / RAG Changes
```
New tool:  weather_tool(district: str) → WeatherData
           Called by LangGraph when intent = "weather"
           Returns current + forecast + Tamil advisory
LangGraph: Route "weather" intent to weather_tool first, then generate
```

---

## 7. Flutter Screens
```
Modified screens:
  - HomeScreen: Add WeatherCard widget (temp + rain + 7-day strip)
  - ChatScreen: Weather answers rendered normally (no special UI needed)

New widget:
  - WeatherCard: district name + condition icon + temp + rain mm + 3-day mini forecast
  - RainAlertBanner: appears when rain > 5mm in next 24h (yellow background, Tamil text)
```

---

## 8. Tests
```
Integration:
  - test_weather_endpoint_returns_forecast()
  - test_weather_cache_hit_uses_redis()
  - test_weather_cache_miss_calls_open_meteo()
  - test_rain_alert_advisory_generated()
  - test_weather_tool_in_langraph()
Coverage: 70%
```

---

## 9. Security Review
```
Auth required:    No (public endpoint — district is not sensitive)
External API:     Open-Meteo — no API key, GET only, low risk
Redis:            Cache write with TTL 3600s — no user data stored
Rate limit:       10 requests/minute/IP (protect Open-Meteo quota)
```

---

## 10. Documentation
```
README: Weather section added
Changelog: Yes
```

---

## 11. Demo Checklist
```
[ ] Home screen shows Thanjavur weather (Murugan's district)
[ ] 7-day forecast visible
[ ] Rain alert appears when rain expected (use mock data if needed)
[ ] Murugan asks in chat: "நாளை மழை வருமா?" → gets Tamil answer with forecast
[ ] Cache works: 2nd request in 1 hour hits Redis (check response time < 50ms)
[ ] Open-Meteo down: shows cached data with timestamp
```

---

## 12. Release Notes
```
## FP-003 — Weather (v0.4.0)
See the 7-day weather forecast for your district.
Get Tamil advice on when to spray, irrigate, or sow based on rain forecast.
```

---

## Sign-offs

| Agent | Sign-off | Date |
|-------|----------|------|
| PM Agent | [ ] | |
| SA Agent | [ ] | |
| Testing Agent | [ ] | |
| Security Agent | [ ] | |
| Documentation Agent | [ ] | |
| Standards Agent | [ ] | |
| **Master Agent** | [ ] | |
