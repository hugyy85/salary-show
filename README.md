# salary-show
Service which show salaries and graphs
To test ,you may open telegram bot https://t.me/show_salary_bot

# Deploy
Необходимо создать и заполнить `.env` файл `cp .env.example .env`

Чтобы запустить
 ```bash
docker-compose -f docker-compose.yml up -d --build 
```
Чтобы остановить
 ```bash
docker-compose -f docker-compose.yml down 
```