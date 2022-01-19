from io import BytesIO
import matplotlib.pyplot as plt
from dataclasses import dataclass


@dataclass
class Graph:
    values: list
    bins: int = 10
    xlabel: str = 'зарплата, рубли'
    ylabel: str = 'Количество вакансий'
    title: str = 'Распределение суммы зарплат от количества вакансий'
    color: str = 'green'

    def __enter__(self):
        max_salary = max(self.values)
        max_val = 950_000
        max_graph_val = max_salary if max_salary < max_val else max_val  # добавлено, так как график более 1млн выглядит странно для многих людей
        hst = plt.hist(self.values, self.bins, (min(self.values), max_graph_val), color=self.color,
                       histtype='bar', rwidth=0.8)
        # x-axis label
        plt.xlabel(self.xlabel)
        # frequency label
        plt.ylabel(self.ylabel)
        # plot title
        plt.title(self.title)
        # function to show the plot

        self.buffer = BytesIO()
        plt.savefig(self.buffer, format='png')
        self.buffer.seek(0)
        return self.buffer

    def __exit__(self, type, value, traceback):
        self.buffer.close()
        plt.close()
