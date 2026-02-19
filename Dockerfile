# Używamy lekkiej wersji Pythona
FROM python:3.10-slim

# Ustawiamy folder roboczy wewnątrz obrazu
WORKDIR /app

# Kopiujemy plik z wymaganiami (jeśli go masz) lub instalujemy biblioteki bezpośrednio
RUN pip install --no-cache-dir ccxt python-dotenv

# Kopiujemy Twoje pliki do obrazu
COPY main.py .
COPY .env .

# Komenda uruchamiająca bota (z -u dla natychmiastowych logów w Dockerze)
CMD ["python", "-u", "main.py"]