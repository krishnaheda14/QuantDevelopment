"""Binance WebSocket client for real-time tick data ingestion."""
import asyncio
import json
import logging
import time
from typing import Callable, Optional
import websockets
from websockets.exceptions import WebSocketException

logger = logging.getLogger(__name__)


class BinanceWebSocketClient:
    """
    Connects to Binance WebSocket streams and ingests real-time tick data.
    Implements reconnection logic with exponential backoff.
    """
    
    def __init__(self, symbols: list, base_url: str, callback: Callable, mode: str = "combined"):
        self.symbols = symbols
        self.base_url = base_url.rstrip('/')
        self.callback = callback
        self.mode = mode  # 'combined' or 'per_symbol'
        self.websocket = None
        self.websockets = {}  # per-symbol websockets when in per_symbol mode
        self.running = False
        self.tick_count = {}
        self.last_tick_ts = {}
        self.reconnect_delay = 1
        self.max_reconnect_delay = 60
        
        for symbol in symbols:
            self.tick_count[symbol] = 0
            self.last_tick_ts[symbol] = 0
    
    def get_stream_url(self) -> str:
        """Build multi-stream URL for all symbols."""
        streams = [f"{symbol.lower()}@trade" for symbol in self.symbols]
        stream_names = "/".join(streams)
        # Combined stream endpoint
        return f"{self.base_url}/stream?streams={stream_names}"

    def get_symbol_url(self, symbol: str) -> str:
        """Return per-symbol websocket URL (futures-style)."""
        return f"{self.base_url}/ws/{symbol.lower()}@trade"
    
    async def connect(self):
        """Establish WebSocket connection."""
        # Single combined connection
        url = self.get_stream_url()
        logger.info(f"Connecting to Binance WebSocket (combined): {url}")

        try:
            self.websocket = await websockets.connect(url, ping_interval=20)
            logger.info("✅ WebSocket connected successfully (combined)")
            self.reconnect_delay = 1  # Reset delay on successful connection
            return True
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed (combined): {e}")
            return False

    async def connect_symbol(self, symbol: str):
        """Connect a single-symbol websocket (per_symbol mode)."""
        url = self.get_symbol_url(symbol)
        logger.info(f"Connecting to Binance WebSocket (symbol): {url}")

        try:
            ws = await websockets.connect(url, ping_interval=20)
            logger.info(f"✅ WebSocket connected for {symbol}")
            self.reconnect_delay = 1
            self.websockets[symbol] = ws
            return True
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed for {symbol}: {e}")
            return False
    
    async def handle_message(self, message: str):
        """Parse and process incoming tick data."""
        try:
            data = json.loads(message)
            
            if "stream" in data and "data" in data:
                stream_name = data["stream"]
                tick_data = data["data"]
                
                # Extract symbol from stream name (e.g., "btcusdt@trade" -> "BTCUSDT")
                symbol = stream_name.split("@")[0].upper()
                
                # Parse tick
                parsed_tick = {
                    "symbol": symbol,
                    "price": float(tick_data["p"]),
                    "quantity": float(tick_data["q"]),
                    "timestamp": int(tick_data["T"]),  # Trade time
                    "trade_id": int(tick_data["t"]),
                    "is_buyer_maker": tick_data["m"]
                }
                
                # Update stats
                self.tick_count[symbol] = self.tick_count.get(symbol, 0) + 1
                # record last tick timestamp (ms)
                try:
                    self.last_tick_ts[symbol] = int(parsed_tick.get("timestamp", int(time.time() * 1000)))
                except Exception:
                    self.last_tick_ts[symbol] = int(time.time() * 1000)
                
                # Debug log (sample every 100 ticks)
                if self.tick_count[symbol] % 100 == 0:
                    logger.debug(
                        f"[{symbol}] Tick #{self.tick_count[symbol]}: "
                        f"Price={parsed_tick['price']:.2f}, Qty={parsed_tick['quantity']:.4f}"
                    )
                
                # Send to callback (e.g., Redis publisher)
                await self.callback(parsed_tick)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def run(self):
        """Main event loop with reconnection logic."""
        self.running = True
        if self.mode == "combined":
            while self.running:
                # Safe check for connection state
                needs_connect = False
                try:
                    if not self.websocket:
                        needs_connect = True
                    elif hasattr(self.websocket, 'closed'):
                        needs_connect = self.websocket.closed
                    else:
                        # Check state attribute for newer websockets
                        state = getattr(self.websocket, 'state', None)
                        needs_connect = str(state) != 'State.OPEN' if state else True
                except Exception:
                    needs_connect = True
                
                if needs_connect:
                    connected = await self.connect()

                    if not connected:
                        logger.warning(f"Reconnecting in {self.reconnect_delay}s...")
                        await asyncio.sleep(self.reconnect_delay)
                        self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
                        continue

                try:
                    async for message in self.websocket:
                        await self.handle_message(message)

                except WebSocketException as e:
                    logger.error(f"WebSocket error: {e}")
                    await asyncio.sleep(self.reconnect_delay)

                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    await asyncio.sleep(self.reconnect_delay)

        else:
            # per_symbol mode: spawn a task per symbol, each with its own loop
            tasks = []
            for symbol in self.symbols:
                tasks.append(asyncio.create_task(self._run_symbol_loop(symbol)))

            try:
                await asyncio.gather(*tasks)
            except asyncio.CancelledError:
                for t in tasks:
                    t.cancel()
                raise
    
    def stop(self):
        """Stop the WebSocket client."""
        logger.info("Stopping WebSocket client...")
        self.running = False
        # Close per-symbol websockets
        for sym, ws in getattr(self, 'websockets', {}).items():
            try:
                asyncio.create_task(ws.close())
            except Exception:
                pass
    
    def get_stats(self) -> dict:
        """Return connection statistics."""
        stats = {
            "mode": self.mode,
            "symbols": self.symbols,
            "tick_counts": self.tick_count,
            "total_ticks": sum(self.tick_count.values())
        }

        if self.mode == "combined":
            # Improved connection heuristics: try multiple attributes from the
            # underlying websocket implementation, and fall back to a "recent
            # tick" heuristic (if we have received ticks in the last 10s).
            try:
                connected = False
                if self.websocket:
                    # common properties across websocket libs
                    if hasattr(self.websocket, 'open'):
                        try:
                            connected = bool(getattr(self.websocket, 'open'))
                        except Exception:
                            connected = False
                    elif hasattr(self.websocket, 'closed'):
                        try:
                            connected = not bool(getattr(self.websocket, 'closed'))
                        except Exception:
                            connected = False
                    else:
                        # Try 'state' string if present
                        st = getattr(self.websocket, 'state', None)
                        try:
                            connected = str(st).upper().find('OPEN') != -1
                        except Exception:
                            connected = False

                # recent-tick heuristic: if any symbol had a tick in last 10s,
                # treat client as connected (helpful when underlying library
                # doesn't expose a consistent 'open/closed' API)
                try:
                    now_ms = int(time.time() * 1000)
                    recent = any((now_ms - int(self.last_tick_ts.get(s, 0))) < 10_000 for s in self.symbols)
                except Exception:
                    recent = False

                stats["connected"] = bool(connected or recent)
                if not stats["connected"]:
                    stats.setdefault("notes", []).append("No active socket flag; using recent-tick heuristic")
            except Exception as e:
                logger.debug(f"Error checking websocket state: {e}")
                stats["connected"] = False
                stats["connection_error"] = str(e)
        else:
            stats["connected_per_symbol"] = {}
            for s in self.symbols:
                try:
                    if s in self.websockets:
                        ws = self.websockets[s]
                        # infer per-symbol connection state from available attrs
                        connected = False
                        if hasattr(ws, 'open'):
                            try:
                                connected = bool(getattr(ws, 'open'))
                            except Exception:
                                connected = False
                        elif hasattr(ws, 'closed'):
                            try:
                                connected = not bool(getattr(ws, 'closed'))
                            except Exception:
                                connected = False
                        else:
                            st = getattr(ws, 'state', None)
                            try:
                                connected = str(st).upper().find('OPEN') != -1
                            except Exception:
                                connected = False

                        # fallback to recent tick timestamp for that symbol
                        try:
                            now_ms = int(time.time() * 1000)
                            last_ts = int(self.last_tick_ts.get(s.upper(), 0) or self.last_tick_ts.get(s, 0) or 0)
                            recent_symbol = (now_ms - last_ts) < 10_000
                        except Exception:
                            recent_symbol = False

                        stats["connected_per_symbol"][s] = bool(connected or recent_symbol)
                    else:
                        stats["connected_per_symbol"][s] = False
                except Exception:
                    stats["connected_per_symbol"][s] = False

        return stats

    async def _run_symbol_loop(self, symbol: str):
        """Run connect/read loop for a single symbol websocket."""
        delay = self.reconnect_delay
        while self.running:
            try:
                connected = await self.connect_symbol(symbol)
                if not connected:
                    logger.warning(f"Reconnecting {symbol} in {delay}s...")
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, self.max_reconnect_delay)
                    continue

                ws = self.websockets.get(symbol)
                async for message in ws:
                    # per-symbol messages for futures are raw trade objects
                    try:
                        data = json.loads(message)
                        # For per-symbol, message is the trade data object
                        tick_data = data
                        parsed_tick = {
                            "symbol": symbol.upper(),
                            "price": float(tick_data.get("p", tick_data.get("price", 0))),
                            "quantity": float(tick_data.get("q", tick_data.get("qty", 0))),
                            "timestamp": int(tick_data.get("T", tick_data.get("E", time.time() * 1000))),
                            "trade_id": int(tick_data.get("t", 0)),
                            "is_buyer_maker": tick_data.get("m", False)
                        }

                        self.tick_count[symbol.upper()] = self.tick_count.get(symbol.upper(), 0) + 1
                        # update last tick ts for symbol
                        try:
                            self.last_tick_ts[symbol.upper()] = int(parsed_tick.get("timestamp", int(time.time() * 1000)))
                        except Exception:
                            self.last_tick_ts[symbol.upper()] = int(time.time() * 1000)
                        await self.callback(parsed_tick)
                    except Exception as e:
                        logger.error(f"Error parsing per-symbol message for {symbol}: {e}")

            except WebSocketException as e:
                logger.error(f"WebSocket error for {symbol}: {e}")
                await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"Unexpected error in per-symbol loop for {symbol}: {e}")
                await asyncio.sleep(delay)


async def test_websocket():
    """Test function to validate WebSocket connection."""
    async def print_tick(tick):
        print(f"Received: {tick['symbol']} @ {tick['price']}")
    
    client = BinanceWebSocketClient(
        symbols=["BTCUSDT"],
        base_url="wss://stream.binance.com:9443/ws",
        callback=print_tick
    )
    
    try:
        await asyncio.wait_for(client.run(), timeout=10)
    except asyncio.TimeoutError:
        print("Test completed")
        print(f"Stats: {client.get_stats()}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_websocket())
