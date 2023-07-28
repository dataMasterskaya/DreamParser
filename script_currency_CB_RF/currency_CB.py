import requests
import xml.etree.ElementTree as ET
import csv
from datetime import date

def get_currency_exchange_rates(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Проверяем на корректность и отсуствие ошибок

        
        root = ET.fromstring(response.content)

        currency_rates = {}
        for currency in root.findall('Valute'):
            name = currency.find('Name').text
            value = currency.find('Value').text
            nominal = currency.find('Nominal').text
            code = currency.find('CharCode').text
            currency_rates[code] = {
                'name': name,
                'value': value,
                'nominal': nominal,
            }

        return currency_rates

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при выполнении запроса: {e}")
        return None

def save_to_csv(data, file_path):
    try:
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            fieldnames = ['Date', 'Code', 'Name', 'Value', 'Nominal']
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()
            for code, currency_data in data.items():
                writer.writerow({
		    'Date': date.today(),	
                    'Code': code,
                    'Name': currency_data['name'],
                    'Value': currency_data['value'],
                    'Nominal': currency_data['nominal']
                })

        print(f"Данные сохранены в файл: {file_path}")

    except IOError as e:
        print(f"Ошибка при сохранении в файл: {e}")

if __name__ == "__main__":
    api_url = "https://www.cbr.ru/scripts/XML_daily.asp"

    data = get_currency_exchange_rates(api_url)

    if data:
        
        print("Курсы валют ЦБ РФ:")
        for code, currency_data in data.items():
            print(f"{currency_data['name']} ({code}): {currency_data['value']} RUB за {currency_data['nominal']} {currency_data['name']}, {date.today()}")

        # Сохраняем в CSV-файл
        # ЗАМЕНИТЬ НА КОРРЕКТНУЮ ССЫЛКУ ДЛЯ ВЫГРУЗКИ CSV
        save_to_csv(data, r"/content/sample_data/currency_rates.csv")

    else:
        print("Не удалось получить данные о курсе валют.")
