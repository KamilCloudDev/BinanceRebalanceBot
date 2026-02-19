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
CHECK_INTERVAL: int = 5
THRESHOLD: float = 0.01
FEE_MARGIN: float = 0.99     

# ZAKTUALIZOWANA KONFIGURACJA (Możesz tu mieszać pary /USDC i /EUR)
TARGET_PORTFOLIO: Dict[str, float] = {
    'EUR/USDC': 0.10,
    'BTC/USDC': 0.09, 
    'ETH/USDC': 0.09, 
    'SOL/USDC': 0.09,
    'NEAR/USDC': 0.09,
    'RENDER/USDC': 0.09,
    'FET/USDC': 0.09,
    'ONDO/USDC': 0.09,
    'PENDLE/USDC': 0.09,
    'LINK/USDC': 0.09,
    'FIL/USDC': 0.09
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
    print("\n[!] Zamykanie bota... Do zobaczenia!")
    save_log_to_file(f"\n[{time.strftime('%H:%M:%S')}] BOT WYŁĄCZONY.")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

def get_portfolio_status() -> Tuple[float, Dict[str, Any]]:
    balance = exchange.fetch_balance()
    tickers = exchange.fetch_tickers(list(TARGET_PORTFOLIO.keys()))
    
    # Podstawa wyceny portfela (USDC)
    raw_total_value = balance['total'].get('USDC', 0)
    
    # Dodajemy wartość EUR do total_value (jeśli istnieje para EUR/USDC do wyceny)
    if 'EUR' in balance['total'] and balance['total']['EUR'] > 0:
        try:
            eur_price = tickers.get('EUR/USDC', exchange.fetch_ticker('EUR/USDC'))['last']
            raw_total_value += balance['total']['EUR'] * eur_price
        except:
            pass # Jeśli nie ma pary EUR/USDC, total będzie liczony bez EUR (tylko krypto + USDC)

    assets = {}
    for symbol in TARGET_PORTFOLIO:
        coin = symbol.split('/')[0]
        qty = balance['total'].get(coin, 0)
        price = tickers[symbol]['last']
        val = qty * price
        
        # Jeśli coinem jest EUR, nie dodajemy go dwa razy (dodaliśmy wyżej jako gotówkę)
        if coin != 'EUR':
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
        table_output += " Portfel zrównoważony.\n" if not did_rebalance else f" Zmiany: {len(sell_orders)} S, {len(buy_orders)} K.\n"

        print(table_output)
        if is_first_run or did_rebalance:
            save_log_to_file(table_output)
            is_first_run = False 

        # 1. REALIZACJA SPRZEDAŻY
        for symbol, qty in sell_orders:
            qty_prec = exchange.amount_to_precision(symbol, qty)
            msg = f" [!] AKCJA: SPRZEDAŻ {symbol} ({qty_prec})"
            print(msg); save_log_to_file(msg)
            exchange.create_market_sell_order(symbol, qty_prec)
        
        if sell_orders: time.sleep(2)

        # 2. REALIZACJA ZAKUPÓW (Z poprawką na walutę bazową)
        for symbol, needed_val in buy_orders:
            current_bal = exchange.fetch_balance()
            
            # Pobieramy co jest bazą: USDC czy EUR?
            base_currency = symbol.split('/')[1] 
            free_money = current_bal['free'].get(base_currency, 0)
            
            safe_spend = min(needed_val, free_money)
            
            if safe_spend > 10:
                ticker = exchange.fetch_ticker(symbol)
                buy_qty = safe_spend / ticker['last']
                buy_qty_prec = exchange.amount_to_precision(symbol, buy_qty)
                
                msg = f" [+] AKCJA: KUPNO {symbol} za {safe_spend:.2f} {base_currency}"
                print(msg); save_log_to_file(msg)
                exchange.create_market_buy_order(symbol, buy_qty_prec)
            else:
                msg = f" [!] POMINIĘTO {symbol}: Brak {base_currency} (Dostępne: {free_money:.2f})"
                print(msg); save_log_to_file(msg)

    except Exception as e:
        err = f" [BŁĄD]: {str(e)}"
        print(err); save_log_to_file(err)

if __name__ == "__main__":
    print(f"Bot start. Interwał: {CHECK_INTERVAL}s")
    while True:
        rebalance()
        time.sleep(CHECK_INTERVAL)