"""Currency exchange rate service with real-time data integration."""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.expense import Currency, ExchangeRate, ExchangeRateHistory, SupportedCurrencies
from app.core.config import settings

logger = logging.getLogger(__name__)


class CurrencyService:
    """Service for managing currencies and exchange rates."""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache_duration = timedelta(hours=1)  # Cache rates for 1 hour
    
    async def get_current_rate(self, from_currency: str, to_currency: str = "HKD") -> Optional[Decimal]:
        """Get current exchange rate with caching."""
        if from_currency == to_currency:
            return Decimal("1.0")
        
        # Try to get from cache first
        cached_rate = self._get_cached_rate(from_currency, to_currency)
        if cached_rate:
            return cached_rate
        
        # Fetch from external API
        rate = await self._fetch_external_rate(from_currency, to_currency)
        if rate:
            # Cache the rate
            self._cache_rate(from_currency, to_currency, rate)
            return rate
        
        # Fallback to manual rates
        return self._get_manual_rate(from_currency, to_currency)
    
    def _get_cached_rate(self, from_currency: str, to_currency: str) -> Optional[Decimal]:
        """Get rate from cache if available and not expired."""
        currency = self.db.query(Currency).filter(Currency.code == from_currency).first()
        if not currency:
            return None
        
        cutoff_time = datetime.utcnow() - self.cache_duration
        latest_rate = (
            self.db.query(ExchangeRate)
            .filter(
                ExchangeRate.currency_id == currency.id,
                ExchangeRate.effective_date >= cutoff_time,
                ExchangeRate.is_active == True
            )
            .order_by(desc(ExchangeRate.effective_date))
            .first()
        )
        
        if latest_rate:
            return latest_rate.rate_to_hkd if to_currency == "HKD" else latest_rate.rate_from_hkd
        
        return None
    
    async def _fetch_external_rate(self, from_currency: str, to_currency: str) -> Optional[Decimal]:
        """Fetch exchange rate from external API."""
        try:
            # Use exchangerate-api.com (free tier available)
            url = f"https://v6.exchangerate-api.com/v6/{settings.EXCHANGE_RATE_API_KEY}/pair/{from_currency}/{to_currency}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("result") == "success":
                            rate = Decimal(str(data["conversion_rate"]))
                            logger.info(f"Fetched rate {from_currency}/{to_currency}: {rate}")
                            return rate
        
        except Exception as e:
            logger.error(f"Failed to fetch exchange rate for {from_currency}/{to_currency}: {e}")
        
        return None
    
    def _cache_rate(self, from_currency: str, to_currency: str, rate: Decimal):
        """Cache exchange rate in database."""
        try:
            currency = self.db.query(Currency).filter(Currency.code == from_currency).first()
            if not currency:
                return
            
            # Convert to HKD rate if needed
            rate_to_hkd = rate if to_currency == "HKD" else Decimal("1.0") / rate
            rate_from_hkd = Decimal("1.0") / rate_to_hkd
            
            exchange_rate = ExchangeRate(
                currency_id=currency.id,
                rate_to_hkd=rate_to_hkd,
                rate_from_hkd=rate_from_hkd,
                effective_date=datetime.utcnow(),
                source="api",
                is_active=True
            )
            
            self.db.add(exchange_rate)
            
            # Also add to history
            history = ExchangeRateHistory(
                currency_code=from_currency,
                rate_to_hkd=rate_to_hkd,
                rate_date=datetime.utcnow(),
                source="api"
            )
            self.db.add(history)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to cache exchange rate: {e}")
            self.db.rollback()
    
    def _get_manual_rate(self, from_currency: str, to_currency: str) -> Optional[Decimal]:
        """Get manual/fallback exchange rate."""
        currency = self.db.query(Currency).filter(Currency.code == from_currency).first()
        if not currency:
            return None
        
        latest_rate = (
            self.db.query(ExchangeRate)
            .filter(ExchangeRate.currency_id == currency.id)
            .order_by(desc(ExchangeRate.effective_date))
            .first()
        )
        
        if latest_rate:
            return latest_rate.rate_to_hkd if to_currency == "HKD" else latest_rate.rate_from_hkd
        
        return None
    
    def convert_amount(
        self, 
        amount: Decimal, 
        from_currency: str, 
        to_currency: str = "HKD"
    ) -> Dict:
        """Convert amount between currencies."""
        if from_currency == to_currency:
            return {
                "original_amount": amount,
                "converted_amount": amount,
                "exchange_rate": Decimal("1.0"),
                "from_currency": from_currency,
                "to_currency": to_currency
            }
        
        # Get rate synchronously for now (can be improved to async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        rate = loop.run_until_complete(self.get_current_rate(from_currency, to_currency))
        loop.close()
        
        if not rate:
            raise ValueError(f"Exchange rate not available for {from_currency}/{to_currency}")
        
        converted_amount = amount * rate
        
        return {
            "original_amount": amount,
            "converted_amount": converted_amount.quantize(Decimal("0.01")),
            "exchange_rate": rate,
            "from_currency": from_currency,
            "to_currency": to_currency
        }
    
    def get_supported_currencies(self) -> List[Dict]:
        """Get list of supported currencies."""
        currencies = (
            self.db.query(Currency)
            .filter(Currency.is_active == True)
            .order_by(Currency.code)
            .all()
        )
        
        return [
            {
                "id": currency.id,
                "code": currency.code,
                "name": currency.name,
                "name_chinese": currency.name_chinese,
                "symbol": currency.symbol,
                "is_base_currency": currency.is_base_currency
            }
            for currency in currencies
        ]
    
    async def update_all_rates(self) -> Dict:
        """Update all exchange rates from external sources."""
        results = {"updated": 0, "failed": 0, "errors": []}
        
        currencies = (
            self.db.query(Currency)
            .filter(Currency.is_active == True, Currency.is_base_currency == False)
            .all()
        )
        
        for currency in currencies:
            try:
                rate = await self._fetch_external_rate(currency.code, "HKD")
                if rate:
                    self._cache_rate(currency.code, "HKD", rate)
                    results["updated"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Failed to fetch rate for {currency.code}")
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Error updating {currency.code}: {str(e)}")
        
        return results
    
    def get_rate_history(
        self, 
        currency_code: str, 
        days: int = 30
    ) -> List[Dict]:
        """Get exchange rate history for a currency."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        history = (
            self.db.query(ExchangeRateHistory)
            .filter(
                ExchangeRateHistory.currency_code == currency_code,
                ExchangeRateHistory.rate_date >= cutoff_date
            )
            .order_by(ExchangeRateHistory.rate_date)
            .all()
        )
        
        return [
            {
                "date": record.rate_date.isoformat(),
                "rate": float(record.rate_to_hkd),
                "source": record.source
            }
            for record in history
        ]


def initialize_currencies(db: Session):
    """Initialize default currencies and exchange rates."""
    currencies_data = [
        {
            "code": SupportedCurrencies.HKD,
            "name": "Hong Kong Dollar",
            "name_chinese": "港幣",
            "symbol": "HK$",
            "is_base_currency": True
        },
        {
            "code": SupportedCurrencies.USD,
            "name": "US Dollar",
            "name_chinese": "美元",
            "symbol": "$"
        },
        {
            "code": SupportedCurrencies.RMB,
            "name": "Chinese Yuan (RMB)",
            "name_chinese": "人民幣",
            "symbol": "¥"
        },
        {
            "code": SupportedCurrencies.CNY,
            "name": "Chinese Yuan (CNY)",
            "name_chinese": "人民幣",
            "symbol": "¥"
        },
        {
            "code": SupportedCurrencies.JPY,
            "name": "Japanese Yen",
            "name_chinese": "日元",
            "symbol": "¥"
        },
        {
            "code": SupportedCurrencies.EUR,
            "name": "Euro",
            "name_chinese": "歐元",
            "symbol": "€"
        }
    ]
    
    for currency_data in currencies_data:
        existing = db.query(Currency).filter(Currency.code == currency_data["code"]).first()
        if not existing:
            currency = Currency(**currency_data)
            db.add(currency)
    
    # Add default exchange rates (these will be updated by the service)
    default_rates = [
        {"currency_code": "USD", "rate_to_hkd": Decimal("7.80")},
        {"currency_code": "RMB", "rate_to_hkd": Decimal("1.08")},
        {"currency_code": "CNY", "rate_to_hkd": Decimal("1.08")},
        {"currency_code": "JPY", "rate_to_hkd": Decimal("0.053")},
        {"currency_code": "EUR", "rate_to_hkd": Decimal("8.50")},
    ]
    
    for rate_data in default_rates:
        currency = db.query(Currency).filter(Currency.code == rate_data["currency_code"]).first()
        if currency:
            existing_rate = (
                db.query(ExchangeRate)
                .filter(ExchangeRate.currency_id == currency.id)
                .first()
            )
            if not existing_rate:
                exchange_rate = ExchangeRate(
                    currency_id=currency.id,
                    rate_to_hkd=rate_data["rate_to_hkd"],
                    rate_from_hkd=Decimal("1.0") / rate_data["rate_to_hkd"],
                    effective_date=datetime.utcnow(),
                    source="manual",
                    is_active=True
                )
                db.add(exchange_rate)
    
    try:
        db.commit()
    except Exception as e:
        logger.error(f"Failed to initialize currencies: {e}")
        db.rollback()