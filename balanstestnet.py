import os
import ccxt
from dotenv import load_dotenv

# --- 1. KONFIGURACJA ---
load_dotenv()

USE_TESTNET = True
FEE_RESERVE = 0.995 # Rezerwa 0.5% na prowizje, aby uniknąć błędu insufficient balance

KEEP_LIST = [
    #'EUR', 'BTC', 'ETH', 'SOL',    # Główne
    #'NEAR', 'RENDER', 'FET', # AI
    #'ONDO', 'PENDLE', 'LINK',# RWA
                       # DePIN
]

# --- 2. INICJALIZACJA GIEŁDY ---
exchange = ccxt.binance({
    'apiKey': os.getenv('TESTNET_BINANCE_API_KEY') if USE_TESTNET else os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('TESTNET_BINANCE_API_SECRET') if USE_TESTNET else os.getenv('BINANCE_API_SECRET'),
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})
if USE_TESTNET: exchange.set_sandbox_mode(True)

def clean_portfolio():
    try:
        print(f"--- CZYSZCZENIE I KONWERSJA NA BTC (Testnet: {USE_TESTNET}) ---")
        exchange.load_markets()
        balance = exchange.fetch_balance()
        
        inventory = {coin: qty for coin, qty in balance['total'].items() if qty > 0}
        ignored_in_first_step = KEEP_LIST + ['USDT', 'BNB']
        
        # KROK 1: Sprzedaż wszystkiego co niechciane
        for coin, qty in inventory.items():
            if coin in ignored_in_first_step:
                continue
            
            sold = False
            for base in ['BTC', 'USDT', 'USDC', 'BNB']:
                symbol = f"{coin}/{base}"
                if symbol in exchange.markets:
                    try:
                        ticker = exchange.fetch_ticker(symbol)
                        if (qty * ticker['last']) > 2:
                            print(f" [!] Sprzedaż {coin} przez {symbol}")
                            amount_prec = exchange.amount_to_precision(symbol, qty)
                            exchange.create_market_sell_order(symbol, amount_prec)
                            sold = True
                            break
                    except Exception:
                        continue

        # KROK 2: Konwersja pozostałego USDT na BTC (Z POPRAWKĄ NA PROWIZJĘ)
        print("\n[!] Sprawdzanie salda USDT do zamiany na BTC...")
        current_balance = exchange.fetch_balance()
        usdt_qty = current_balance['total'].get('USDT', 0)
        
        if usdt_qty > 5:
            symbol = 'BTC/USDT'
            if symbol in exchange.markets:
                try:
                    ticker = exchange.fetch_ticker(symbol)
                    # Obliczamy bezpieczną kwotę do wydania (odejmujemy rezerwę na fee)
                    safe_usdt_amount = usdt_qty * FEE_RESERVE
                    btc_to_buy = safe_usdt_amount / ticker['last']
                    amount_prec = exchange.amount_to_precision(symbol, btc_to_buy)
                    
                    print(f"  -> Zamieniam {safe_usdt_amount:.2f} USDT (z {usdt_qty:.2f}) na BTC...")
                    exchange.create_market_buy_order(symbol, amount_prec)
                    print("  [+] Sukces: USDT zamienione na BTC.")
                except Exception as e:
                    print(f"  [x] Błąd przy zamianie USDT na BTC: {e}")
        else:
            print(f"  [-] Brak wystarczającego salda USDT ({usdt_qty:.2f}).")

        # --- PODSUMOWANIE ---
        print("\n" + "="*40)
        print(" STAN KOŃCOWY PORTFELA")
        print("="*40)
        final_bal = exchange.fetch_balance()
        for coin, qty in final_bal['total'].items():
            if qty > 0.000001 and (coin in KEEP_LIST or coin == 'USDC'):
                print(f"{coin:<10}: {qty:.6f}")
        
        print("="*40)

    except Exception as e:
        print(f"Błąd krytyczny: {e}")

if __name__ == "__main__":
    clean_portfolio()