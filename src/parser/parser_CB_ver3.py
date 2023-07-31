import requests
import xml.etree.ElementTree as ET
import csv
from datetime import date, datetime
import logging

def setup_logging(log_file=None):
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)

def get_currency_exchange_rates(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()

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
        logging.error(f"Ошибка при выполнении запроса: {e}")
        return {}

    except ET.ParseError as e:
        logging.error(f"Ошибка при разборе документа XML: {e}")
        return {}

def save_to_csv(data, file_path):
    try:
        now = datetime.now().strftime("%Y-%m-%d")
        file_path_with_date = f"{file_path}_{now}.csv"

        with open(file_path_with_date, mode='w', newline='', encoding='utf-8') as file:
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

        logging.info(f"Данные успешно сохранены в файл: {file_path_with_date}")

    except IOError as e:
        logging.error(f"Ошибка при сохранении в файл: {e}")

if __name__ == "__main__":
    setup_logging('C:/script/parser.log')

    api_url = "https://www.cbr.ru/scripts/XML_daily.asp"

    data = get_currency_exchange_rates(api_url)

    if data:
        logging.info("Курсы валют ЦБ РФ успешно загружены.")
        save_to_csv(data, "C:/script/currency_rates")
    else:
        logging.error("Не удалось получить данные о курсе валют.")
