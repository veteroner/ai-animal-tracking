"""
Weather Service Integration - Hava Durumu Servisi Entegrasyonu
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


logger = logging.getLogger(__name__)


class WeatherCondition(str, Enum):
    """Hava durumu koşulları"""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    PARTLY_CLOUDY = "partly_cloudy"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    SNOW = "snow"
    STORM = "storm"
    FOG = "fog"
    WINDY = "windy"
    HOT = "hot"
    COLD = "cold"


@dataclass
class WeatherConfig:
    """Hava durumu servisi konfigürasyonu"""
    provider: str = "openweathermap"  # openweathermap, weatherapi, custom
    api_key: str = ""
    base_url: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    location_name: str = ""
    update_interval: int = 1800  # 30 dakika
    units: str = "metric"  # metric, imperial


@dataclass
class WeatherData:
    """Hava durumu verisi"""
    timestamp: datetime
    temperature: float  # Sıcaklık (°C veya °F)
    feels_like: float  # Hissedilen sıcaklık
    humidity: float  # Nem (%)
    pressure: float  # Basınç (hPa)
    wind_speed: float  # Rüzgar hızı (m/s veya mph)
    wind_direction: float  # Rüzgar yönü (derece)
    condition: WeatherCondition
    description: str
    precipitation: float = 0.0  # Yağış (mm)
    uv_index: float = 0.0
    visibility: float = 10.0  # Görüş mesafesi (km)
    
    @property
    def is_extreme(self) -> bool:
        """Aşırı hava koşulu mu"""
        return (
            self.temperature > 35 or
            self.temperature < -10 or
            self.wind_speed > 20 or
            self.condition in [
                WeatherCondition.STORM,
                WeatherCondition.HEAVY_RAIN,
                WeatherCondition.SNOW
            ]
        )
        
    @property
    def heat_stress_risk(self) -> str:
        """Isı stresi riski"""
        # THI (Temperature-Humidity Index) hesaplama
        thi = self.temperature - ((0.55 - 0.0055 * self.humidity) * (self.temperature - 14.5))
        
        if thi >= 79:
            return "critical"
        elif thi >= 72:
            return "high"
        elif thi >= 68:
            return "moderate"
        else:
            return "low"


@dataclass
class ForecastItem:
    """Hava tahmini"""
    datetime: datetime
    temperature_min: float
    temperature_max: float
    humidity: float
    condition: WeatherCondition
    precipitation_probability: float = 0.0
    precipitation_amount: float = 0.0


class WeatherServiceIntegration:
    """Hava durumu servisi entegrasyonu"""
    
    def __init__(self, config: WeatherConfig):
        self.config = config
        self._current_weather: Optional[WeatherData] = None
        self._forecast: List[ForecastItem] = []
        self._last_update: datetime = None
        
        # Provider URL'lerini ayarla
        if not config.base_url:
            self._setup_provider_url()
            
    def _setup_provider_url(self):
        """Provider URL'ini ayarla"""
        if self.config.provider == "openweathermap":
            self.config.base_url = "https://api.openweathermap.org/data/2.5"
        elif self.config.provider == "weatherapi":
            self.config.base_url = "https://api.weatherapi.com/v1"
            
    async def get_current_weather(self, force_update: bool = False) -> Optional[WeatherData]:
        """Güncel hava durumunu al"""
        if not force_update and self._current_weather and self._is_cache_valid():
            return self._current_weather
            
        if not HTTPX_AVAILABLE:
            logger.warning("httpx yüklü değil")
            return self._current_weather
            
        try:
            if self.config.provider == "openweathermap":
                weather = await self._fetch_openweathermap_current()
            elif self.config.provider == "weatherapi":
                weather = await self._fetch_weatherapi_current()
            else:
                weather = await self._fetch_custom_current()
                
            if weather:
                self._current_weather = weather
                self._last_update = datetime.utcnow()
                
            return self._current_weather
            
        except Exception as e:
            logger.error(f"Hava durumu alınamadı: {e}")
            return self._current_weather
            
    async def get_forecast(self, days: int = 5) -> List[ForecastItem]:
        """Hava tahmini al"""
        if not HTTPX_AVAILABLE:
            return self._forecast
            
        try:
            if self.config.provider == "openweathermap":
                forecast = await self._fetch_openweathermap_forecast(days)
            elif self.config.provider == "weatherapi":
                forecast = await self._fetch_weatherapi_forecast(days)
            else:
                forecast = await self._fetch_custom_forecast(days)
                
            if forecast:
                self._forecast = forecast
                
            return self._forecast
            
        except Exception as e:
            logger.error(f"Hava tahmini alınamadı: {e}")
            return self._forecast
            
    async def _fetch_openweathermap_current(self) -> Optional[WeatherData]:
        """OpenWeatherMap'ten güncel hava durumu al"""
        url = f"{self.config.base_url}/weather"
        params = {
            "lat": self.config.latitude,
            "lon": self.config.longitude,
            "appid": self.config.api_key,
            "units": self.config.units
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return WeatherData(
                timestamp=datetime.utcnow(),
                temperature=data['main']['temp'],
                feels_like=data['main']['feels_like'],
                humidity=data['main']['humidity'],
                pressure=data['main']['pressure'],
                wind_speed=data['wind']['speed'],
                wind_direction=data['wind'].get('deg', 0),
                condition=self._map_owm_condition(data['weather'][0]['id']),
                description=data['weather'][0]['description'],
                precipitation=data.get('rain', {}).get('1h', 0) + data.get('snow', {}).get('1h', 0),
                visibility=data.get('visibility', 10000) / 1000
            )
            
    async def _fetch_openweathermap_forecast(self, days: int) -> List[ForecastItem]:
        """OpenWeatherMap'ten hava tahmini al"""
        url = f"{self.config.base_url}/forecast"
        params = {
            "lat": self.config.latitude,
            "lon": self.config.longitude,
            "appid": self.config.api_key,
            "units": self.config.units,
            "cnt": days * 8  # 3 saatlik aralıklarla
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            forecasts = []
            for item in data['list']:
                forecasts.append(ForecastItem(
                    datetime=datetime.fromtimestamp(item['dt']),
                    temperature_min=item['main']['temp_min'],
                    temperature_max=item['main']['temp_max'],
                    humidity=item['main']['humidity'],
                    condition=self._map_owm_condition(item['weather'][0]['id']),
                    precipitation_probability=item.get('pop', 0) * 100,
                    precipitation_amount=item.get('rain', {}).get('3h', 0)
                ))
                
            return forecasts
            
    async def _fetch_weatherapi_current(self) -> Optional[WeatherData]:
        """WeatherAPI'den güncel hava durumu al"""
        url = f"{self.config.base_url}/current.json"
        params = {
            "key": self.config.api_key,
            "q": f"{self.config.latitude},{self.config.longitude}"
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            current = data['current']
            return WeatherData(
                timestamp=datetime.utcnow(),
                temperature=current['temp_c'] if self.config.units == 'metric' else current['temp_f'],
                feels_like=current['feelslike_c'] if self.config.units == 'metric' else current['feelslike_f'],
                humidity=current['humidity'],
                pressure=current['pressure_mb'],
                wind_speed=current['wind_kph'] / 3.6 if self.config.units == 'metric' else current['wind_mph'],
                wind_direction=current['wind_degree'],
                condition=self._map_weatherapi_condition(current['condition']['code']),
                description=current['condition']['text'],
                precipitation=current['precip_mm'],
                uv_index=current['uv'],
                visibility=current['vis_km']
            )
            
    async def _fetch_weatherapi_forecast(self, days: int) -> List[ForecastItem]:
        """WeatherAPI'den hava tahmini al"""
        url = f"{self.config.base_url}/forecast.json"
        params = {
            "key": self.config.api_key,
            "q": f"{self.config.latitude},{self.config.longitude}",
            "days": days
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            forecasts = []
            for day in data['forecast']['forecastday']:
                forecasts.append(ForecastItem(
                    datetime=datetime.fromisoformat(day['date']),
                    temperature_min=day['day']['mintemp_c'] if self.config.units == 'metric' else day['day']['mintemp_f'],
                    temperature_max=day['day']['maxtemp_c'] if self.config.units == 'metric' else day['day']['maxtemp_f'],
                    humidity=day['day']['avghumidity'],
                    condition=self._map_weatherapi_condition(day['day']['condition']['code']),
                    precipitation_probability=day['day'].get('daily_chance_of_rain', 0),
                    precipitation_amount=day['day']['totalprecip_mm']
                ))
                
            return forecasts
            
    async def _fetch_custom_current(self) -> Optional[WeatherData]:
        """Özel API'den hava durumu al"""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.config.base_url}/current",
                headers={"X-API-Key": self.config.api_key}
            )
            response.raise_for_status()
            return self._parse_custom_response(response.json())
            
    async def _fetch_custom_forecast(self, days: int) -> List[ForecastItem]:
        """Özel API'den tahmin al"""
        return []  # Özel implementasyon gerektirir
        
    def _parse_custom_response(self, data: Dict) -> Optional[WeatherData]:
        """Özel API yanıtını parse et"""
        return None  # Özel implementasyon gerektirir
        
    def _map_owm_condition(self, code: int) -> WeatherCondition:
        """OpenWeatherMap kodunu koşula çevir"""
        if code >= 200 and code < 300:
            return WeatherCondition.STORM
        elif code >= 300 and code < 400:
            return WeatherCondition.RAIN
        elif code >= 500 and code < 600:
            if code >= 502:
                return WeatherCondition.HEAVY_RAIN
            return WeatherCondition.RAIN
        elif code >= 600 and code < 700:
            return WeatherCondition.SNOW
        elif code >= 700 and code < 800:
            return WeatherCondition.FOG
        elif code == 800:
            return WeatherCondition.CLEAR
        elif code > 800:
            return WeatherCondition.PARTLY_CLOUDY
        return WeatherCondition.CLEAR
        
    def _map_weatherapi_condition(self, code: int) -> WeatherCondition:
        """WeatherAPI kodunu koşula çevir"""
        clear_codes = [1000]
        cloudy_codes = [1003, 1006, 1009]
        rain_codes = [1063, 1150, 1153, 1180, 1183, 1186, 1189]
        heavy_rain_codes = [1192, 1195, 1240, 1243, 1246]
        snow_codes = [1066, 1114, 1210, 1213, 1216, 1219, 1222, 1225]
        storm_codes = [1087, 1273, 1276, 1279, 1282]
        fog_codes = [1030, 1135, 1147]
        
        if code in clear_codes:
            return WeatherCondition.CLEAR
        elif code in cloudy_codes:
            return WeatherCondition.CLOUDY
        elif code in heavy_rain_codes:
            return WeatherCondition.HEAVY_RAIN
        elif code in rain_codes:
            return WeatherCondition.RAIN
        elif code in snow_codes:
            return WeatherCondition.SNOW
        elif code in storm_codes:
            return WeatherCondition.STORM
        elif code in fog_codes:
            return WeatherCondition.FOG
            
        return WeatherCondition.CLEAR
        
    def _is_cache_valid(self) -> bool:
        """Önbellek geçerli mi"""
        if self._last_update is None:
            return False
            
        elapsed = (datetime.utcnow() - self._last_update).total_seconds()
        return elapsed < self.config.update_interval
        
    def get_animal_comfort_level(self, weather: WeatherData = None) -> Dict[str, Any]:
        """Hayvan konfor seviyesi analizi"""
        if weather is None:
            weather = self._current_weather
            
        if weather is None:
            return {"status": "unknown", "message": "Hava durumu verisi yok"}
            
        heat_risk = weather.heat_stress_risk
        
        result = {
            "temperature": weather.temperature,
            "humidity": weather.humidity,
            "heat_stress_risk": heat_risk,
            "is_extreme": weather.is_extreme,
            "recommendations": []
        }
        
        # Öneriler
        if heat_risk == "critical":
            result["recommendations"].append("Acil soğutma önlemleri alın")
            result["recommendations"].append("Su erişimini artırın")
        elif heat_risk == "high":
            result["recommendations"].append("Gölgelik alan sağlayın")
            result["recommendations"].append("Havalandırmayı artırın")
        
        if weather.temperature < 5:
            result["recommendations"].append("Barınak sıcaklığını kontrol edin")
            
        if weather.wind_speed > 15:
            result["recommendations"].append("Rüzgar koruması sağlayın")
            
        return result
