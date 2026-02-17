# 🚀 Crypto Rebalance Bot (Binance)
Automatyczny bot do rebalancingu portfela kryptowalut, napisany w Pythonie. Bot utrzymuje stałe proporcje portfela (domyślnie 10% na każdą z 10 obsługiwanych par) rozliczane w USDC.

---
## 💎 Główne cechy

- **Multi-pair**: obsługa 10 głównych par (np. BTC, ETH, SOL i inne).
- **Smart Budgeting**: rezerwowanie 1% środków na prowizje giełdowe.
- **Bezpieczny flow**: najpierw sprzedaje nadwyżki, potem kupuje niedobory (uniknięcie braku środków przy zakupach).
- **Logowanie transakcji**: raporty zapisywane do pliku tylko gdy wykonano transakcje.
- **Dopasowanie precyzji (Lot Size)**: automatyczne zaokrąglanie ilości do wymogów Binance.
- **Tryb testowy (Testnet)**: domyślnie skonfigurowane do pracy z Binance Spot Testnet.

---
## 🛠️ Instalacja

1. Sklonuj repozytorium:

```bash
git clone https://github.com/KamilCloudDev/BinanceRebalanceBot.git
cd BinanceRebalanceBot
```

2. Zainstaluj zależności:

```bash
pip install -r requirements.txt
```

3. Stwórz plik `.env` w katalogu głównym i wypełnij danymi:

```env
TESTNET_BINANCE_API_KEY=twoj_klucz_testnet
TESTNET_BINANCE_API_SECRET=twoj_sekret_testnet
BINANCE_API_KEY=twoj_klucz_real
BINANCE_API_SECRET=twoj_sekret_real
USE_TESTNET=True
THRESHOLD=0.01
```

---
## ▶️ Uruchamianie

Domyślnie bot jest skonfigurowany do pracy w trybie testowym (`USE_TESTNET=True`). Uruchom bota poleceniem:

```bash
python main.py
```

W celu przejścia na rynek rzeczywisty ustaw `USE_TESTNET=False` i upewnij się, że używasz poprawnych kluczy produkcyjnych.

---
## ⚙️ Strategia i logika działania

- Bot oblicza całkowitą wartość portfela w USDC.
- Porównuje udział każdej z monet z celem (np. 10%).
- Jeżeli odchylenie przekracza `THRESHOLD` (domyślnie 1%), generowane są transakcje korygujące.
- Kolejność działań: najpierw spłata/nadwyżki (sprzedaż), potem uzupełnianie niedoborów (zakup) — to minimalizuje ryzyko braku środków.

Korzyść: realizuje zyski z aktywów wzrostowych i reinwestuje w przecenione aktywa.

---
## 🧾 Logowanie i bezpieczeństwo

- Wszystkie wykonane transakcje i raporty zapisywane są do `portfolio_log.txt`.
- Zalecane: najpierw testować na Testnet, dopiero potem włączyć środowisko produkcyjne.

---
## ✨ Drobne uwagi implementacyjne

- Bot automatycznie dobiera wielkość zleceń zgodnie z ograniczeniami Binance (lot size, step size).
- Rezerwuje ~1% wartości na pokrycie opłat transakcyjnych.

---
## 👨‍💻 Autor

Stworzone przez KamilCloudDev — https://github.com/KamilCloudDev/BinanceRebalanceBot

---