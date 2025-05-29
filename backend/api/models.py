from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    session_id: Optional[str] = None

class PriceData(BaseModel):
    date: str
    timestamp: int
    price: float
    open: float
    high: float
    low: float
    close: float
    volume: float

class CurrentPrice(BaseModel):
    symbol: str
    quote: str
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    spread: Optional[float] = None
    spread_percentage: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    price_24h_ago: Optional[float] = None
    price_change: Optional[float] = None
    price_change_percent: Optional[float] = None
    timestamp: int

class AssetInfo(BaseModel):
    symbol: str
    price: float

class LivePriceData(BaseModel):
    timestamp: int
    time: str
    price: float
    open: float
    high: float
    low: float
    close: float
    volume: float

class UserTrade(BaseModel):
    timestamp: int
    date: str
    price: float
    size: float
    side: str
    direction: str
    fee: float
    pnl: float
    order_id: int
    trade_id: int 