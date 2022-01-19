import asyncio
import urllib.parse
import io

import matplotlib.pyplot as plt
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

    async def get_vacancies(self, skill_name: str, page: int, per_page=100) -> dict:
        params = {
            'per_page': per_page,
            'text': skill_name,
            'page': page,
            'only_with_salary': 'true'
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

        # make async requests to api
        responses_tasks = []
        for page in range(response_count):
            responses_tasks.append(asyncio.gather(self.get_vacancies(skill_name, page=page), return_exceptions=True))
        responses = await asyncio.gather(*responses_tasks, return_exceptions=True)

        salaries = []
        for response_data in responses:
            for req in response_data[0]['items']: # [0] here because asyncio.gather return new list for each task
                salary = req["salary"]
                if salary:
                    min_s, max_s = self.__convert_salary(salary)
                    salaries.append(round((max_s + min_s) / 2))  # среднее арифметическое
        return salaries  # todo add median, moda

    @staticmethod
    def get_graph(values: list, bins: int = 10, xlabel: str = 'зарплата, рубли', ylabel: str = 'Количество вакансий',
                  title: str = 'Распределение суммы зарплат от количества вакансий',
                  color: str = 'green') -> io.BytesIO:
        hst = plt.hist(values, bins, (0, max(values)), color=color,
                       histtype='bar', rwidth=0.8)
        # x-axis label
        plt.xlabel(xlabel)
        # frequency label
        plt.ylabel(ylabel)
        # plot title
        plt.title(title)
        # function to show the plot

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        return buffer  ### you must close buffer if you use it

    def __convert_salary(self, salary: dict) -> (float, float):
        salary_from = salary['from'] if salary['from'] else salary['to']
        salary_to = salary['to'] if salary['to'] else salary['from']
        if salary['currency'] != 'RUR':
            salary_from *= self.currency_data[salary["currency"]]
            salary_to *= self.currency_data[salary["currency"]]

        if salary['gross']:
            salary_from -= (salary_from * 0.13)
            salary_to -= (salary_to * 0.13)

        return salary_from, salary_to

    async def get_best_salaries(self, query_text: str, limit: int = 10):
        """Поиск лучших зарплат"""
        params = {
            'order_by': 'salary_desc',
            'per_page': limit,
            'text': query_text,
            'page': 0,
            'only_with_salary': True
        }
        response_data = await self.get_vacancies(params)
        await self.add_currency_data_if_none()
        for req in response_data['items']:
            min_s, max_s = self.__convert_salary(req['salary'])
            print(req['name'], f'min {min_s:,} max {max_s:,} - {req["alternate_url"]}')
