import asyncio
import urllib.parse
from statistics import mean

import httpx

from config import MY_EMAIL


class Hh:
    base_url = 'https://api.hh.ru/'
    headers = {'HH-User-Agent': f"salary_show <{MY_EMAIL}>"}
    vacancies_url = urllib.parse.urljoin(base_url, 'vacancies')
    currency_data = None

    async def add_currency_data_if_none(self) -> dict:
        if not self.currency_data:
            async with httpx.AsyncClient() as session:
                response = await session.get('https://www.cbr-xml-daily.ru/daily_json.js')
                response.raise_for_status()
                response_data = response.json()
            self.currency_data = {key: val['Value'] / val['Nominal'] for key, val in response_data['Valute'].items()}
            self.currency_data['BYR'] = self.currency_data['BYN']  # in api.hh.ru BYR is BYN from central bank
        return self.currency_data

    async def get_vacancies(self, skill_name: str, page: int, per_page=100, **kwargs) -> dict:
        params = {
            'per_page': per_page,
            'text': skill_name,
            'page': page,
            'only_with_salary': 'true',
            **kwargs
        }
        async with httpx.AsyncClient() as session:
            response = await session.get(self.vacancies_url, params=params, headers=self.headers)
            response.raise_for_status()
            response_data = response.json()
        return response_data

    async def get_salary_normal(self, skill_name: str):
        response_data = await self.get_vacancies(skill_name, page=0)
        # 2000 is constraint for api.hh.ru for without paying
        response_count = response_data['pages'] if response_data['found'] > 2000 else response_data['pages'] + 1
        await self.add_currency_data_if_none()

        salaries = []
        for page in range(response_count):
            request = await self.get_vacancies(skill_name, page=page)
            for req in request['items']:
                salary = req["salary"]
                if salary and self.currency_data.get(salary["currency"]):
                    min_s, max_s = self.convert_salary(salary)
                    salaries.append(round(mean([max_s, min_s])))  # среднее арифметическое
        return salaries

    def convert_salary(self, salary: dict) -> (float, float):
        salary_from = salary['from'] if salary['from'] else salary['to']
        salary_to = salary['to'] if salary['to'] else salary['from']
        if salary['currency'] != 'RUR':
            salary_from *= self.currency_data[salary["currency"]]
            salary_to *= self.currency_data[salary["currency"]]

        if salary['gross']:
            salary_from -= (salary_from * 0.13)
            salary_to -= (salary_to * 0.13)

        return round(salary_from), round(salary_to)

    async def get_best_salaries(self, query_text: str, limit: int = 10):
        """Поиск лучших зарплат"""
        response_data = await self.get_vacancies(query_text, page=0, per_page=limit, order_by='salary_desc')
        await self.add_currency_data_if_none()
        return response_data['items']
