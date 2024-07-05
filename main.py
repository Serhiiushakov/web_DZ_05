import aiohttp  # для асинхронних HTTP-запитів
import asyncio  # для асинхронного програмування
import platform  # для роботи зі специфікаціями платформи (операційної системи)
import sys  # для роботи з системними параметрами та аргументами командного рядка
import ssl  # для роботи з SSL
import certifi  # для управління кореневими сертифікатами

from datetime import datetime, timedelta  # для роботи з датами і часом
from typing import List, Dict  # для анотацій типів даних

API_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date="


class CurrencyFetcher:
    def __init__(self, days: int):
        self.days = days

    # Асинхронний метод для отримання курсів валют на задану дату
    async def fetch_rates(self, date: str) -> Dict:
        # Створюємо SSL-контекст з сертифікатами, що дозволяє перевіряти достовірність сервера
        ssl_context = ssl.create_default_context(cafile=certifi.where())

        # Створюємо TCP-коннектор для з'єднання з сервером за допомогою aiohttp
        connector = aiohttp.TCPConnector(ssl=ssl_context)

        # Встановлюємо з'єднання з сервером за допомогою aiohttp.ClientSession
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                # Виконуємо GET-запит до API банку за вказаною датою
                async with session.get(API_URL + date) as response:
                    if response.status == 200:
                        data = await response.json()  # Отримуємо дані у форматі JSON
                        return self.parse_rates(data)  # Парсимо отримані дані
                    else:
                        print(
                            f"Error fetching data for {date}: {response.status}")  # Виводимо помилку, якщо статус не 200
                        return {}
            except aiohttp.ClientError as e:
                print(f"Network error: {e}")  # Виводимо помилку, якщо виникла мережева проблема
                return {}

    # Метод для парсингу отриманих даних про курси валют
    def parse_rates(self, data: Dict) -> Dict:
        rates = {'EUR': {}, 'USD': {}}  # Словник для зберігання курсів EUR і USD
        for rate in data.get('exchangeRate', []):
            if rate.get('currency') in rates:
                rates[rate['currency']] = {
                    'sale': rate.get('saleRate'),  # Курс продажу
                    'purchase': rate.get('purchaseRate')  # Курс покупки
                }
        return {data[
                    'date']: rates}  # Повертаємо результат у форматі {дата: {EUR: {sale, purchase}, USD: {sale, purchase}}}

    # Асинхронний метод для отримання курсів валют за останні декілька днів
    async def fetch_last_days_rates(self) -> List[Dict]:
        tasks = []
        for i in range(self.days):
            date = (datetime.now() - timedelta(days=i)).strftime('%d.%m.%Y')  # Обчислюємо дату для кожного з днів
            tasks.append(self.fetch_rates(date))  # Додаємо завдання для отримання курсів на певну дату
        results = await asyncio.gather(*tasks)  # Виконуємо всі завдання паралельно
        return [result for result in results if result]  # Повертаємо результати, які не є пустими


def main():
    if len(sys.argv) != 2:
        print("Usage: py .\\main.py <number_of_days>")  # Інформація про використання програми
        return

    try:
        days = int(sys.argv[1])  # Отримуємо кількість днів з аргументів командного рядка
        if days > 10:
            print("Error: Maximum number of days is 10")  # Перевірка на обмеження не більше 10 днів
            return
    except ValueError:
        print("Error: Invalid number of days")  # Обробка помилки, якщо введено некоректні дані
        return

    fetcher = CurrencyFetcher(days)  # Створюємо об'єкт для отримання курсів валют

    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # Встановлюємо політику для Windows

    results = asyncio.run(fetcher.fetch_last_days_rates())  # Запускаємо асинхронну функцію отримання курсів
    print(results)  # Виводимо результати на екран


if __name__ == "__main__":
    main()


 #    виклик з терміналу
 #    py .\main.py 2


#  Результат 04.07.2024
#(.venv) PS D:\Visual_Studio_Code\pythonProject_web_dz_5> py .\main.py 2
# [{'04.07.2024': {'EUR': {'sale': 44.2, 'purchase': 43.2}, 'USD': {'sale': 41.0, 'purchase': 40.4}}}, {'03.07.2024': {'EUR': {'sale': 44.2, 'purchase': 43.2}, 'USD': {'sale': 41.0, 'purchase': 40.4}}}]

