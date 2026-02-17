import os
import time
import signal
import sys
import ccxt
from dotenv import load_dotenv
from typing import Dict, Any, Tuple

# 1. KONFIGURACJA
load_dotenv()

USE_TESTNET: bool = True
CHECK_INTERVAL: int = 600
THRESHOLD: float = 0.01
FEE_MARGIN: float = 0.99     

TARGET_PORTFOLIO: Dict[str, float] = {
    'BTC/USDC': 0.10, 'ETH/USDC': 0.10, 'BNB/USDC': 0.10,
    'SOL/USDC': 0.10, 'ADA/USDC': 0.10, 'XRP/USDC': 0.10,
    'DOT/USDC': 0.10, 'LINK/USDC': 0.10, 'AVAX/USDC': 0.10,
    'POL/USDC': 0.10
}

is_first_run: bool = True

# 2. INICJALIZACJA GIEŁDY
exchange = ccxt.binance({
    'apiKey': os.getenv('TESTNET_BINANCE_API_KEY') if USE_TESTNET else os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('TESTNET_BINANCE_API_SECRET') if USE_TESTNET else os.getenv('BINANCE_API_SECRET'),
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})
if USE_TESTNET: exchange.set_sandbox_mode(True)

def save_log_to_file(content: str) -> None:
    with open("portfolio_log.txt", "a", encoding="utf-8") as f:
        f.write(content + "\n")

def handle_exit(sig, frame):
    """Funkcja wywoływana przy CTRL+C."""
    print("\n[!] Zamykanie bota... Do zobaczenia!")
    save_log_to_file(f"\n[{time.strftime('%H:%M:%S')}] BOT WYŁĄCZONY PRZEZ UŻYTKOWNIKA.")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

def get_portfolio_status() -> Tuple[float, Dict[str, Any]]:
    balance = exchange.fetch_balance()
    tickers = exchange.fetch_tickers(list(TARGET_PORTFOLIO.keys()))
    
    raw_total_value = balance['total'].get('USDC', 0)
    assets = {}
    
    for symbol in TARGET_PORTFOLIO:
        coin = symbol.split('/')[0]
        qty = balance['total'].get(coin, 0)
        price = tickers[symbol]['last']
        val = qty * price
        raw_total_value += val
        assets[symbol] = {'qty': qty, 'price': price, 'value': val}
    
    return raw_total_value, assets

def rebalance() -> None:
    global is_first_run
    try:
        exchange.load_markets()
        raw_total_value, assets = get_portfolio_status()
        operating_value = raw_total_value * FEE_MARGIN
        
        table_output = f"\n{'='*60}\n"
        table_output += f" CZAS: {time.strftime('%Y-%m-%d %H:%M:%S')} | PORTFEL: {raw_total_value:.2f} USDC\n"
        table_output += f"{'PARA':<12} | {'AKTUALNIE':<10} | {'CEL':<10} | {'STATUS'}\n"
        table_output += f"{'-'*60}\n"

        sell_orders = []
        buy_orders = []

        for symbol, target_pct in TARGET_PORTFOLIO.items():
            current_pct = (assets[symbol]['value'] / raw_total_value) if raw_total_value > 0 else 0
            status = "OK"
            
            if current_pct > (target_pct + THRESHOLD):
                status = "NADWYŻKA"
                target_val = operating_value * target_pct
                diff_val = assets[symbol]['value'] - target_val
                if diff_val > 10:
                    sell_orders.append((symbol, diff_val / assets[symbol]['price']))
            
            elif current_pct < (target_pct - THRESHOLD):
                status = "NIEDOBÓR"
                target_val = operating_value * target_pct
                needed_val = target_val - assets[symbol]['value']
                if needed_val > 10:
                    buy_orders.append((symbol, needed_val))

            table_output += f"{symbol:<12} | {current_pct:9.2%} | {target_pct:9.2%} | {status}\n"

        table_output += f"{'-'*60}\n"
        did_rebalance = len(sell_orders) > 0 or len(buy_orders) > 0
        table_output += " Portfel idealnie zrównoważony.\n" if not did_rebalance else f" Wykryto zmiany: {len(sell_orders)} sprzedaży, {len(buy_orders)} zakupów.\n"

        print(table_output)
        if is_first_run or did_rebalance:
            save_log_to_file(table_output)
            is_first_run = False 

        # REALIZACJA
        for symbol, qty in sell_orders:
            qty_prec = exchange.amount_to_precision(symbol, qty)
            msg = f" [!] AKCJA: SPRZEDAŻ {symbol} ({qty_prec})"
            print(msg); save_log_to_file(msg)
            exchange.create_market_sell_order(symbol, qty_prec)
        
        if sell_orders: time.sleep(2)

        for symbol, needed_val in buy_orders:
            current_bal = exchange.fetch_balance()
            free_usdc = current_bal['free'].get('USDC', 0)
            safe_spend = min(needed_val, free_usdc)
            
            if safe_spend > 10:
                ticker = exchange.fetch_ticker(symbol)
                buy_qty = safe_spend / ticker['last']
                buy_qty_prec = exchange.amount_to_precision(symbol, buy_qty)
                msg = f" [+] AKCJA: KUPNO {symbol} za {safe_spend:.2f} USDC"
                print(msg); save_log_to_file(msg)
                exchange.create_market_buy_order(symbol, buy_qty_prec)

    except Exception as e:
        err = f" [BŁĄD]: {str(e)}"
        print(err); save_log_to_file(err)

if __name__ == "__main__":
    print(f"Bot uruchomiony. Interwał: {CHECK_INTERVAL}s")
    while True:
        rebalance()
        time.sleep(CHECK_INTERVAL)