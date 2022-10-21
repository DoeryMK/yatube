# yatube

## Социальная сеть блогеров

## **Краткое описание**
Данный проект является учебным. 
Основная цель проекта - получение навыков работы с фремворком Django.
Выполнено покрытие проекта юнит-тестами.

### _Доступные возможности_
* регистрация пользователей
* создание записей
* создание комментариев к существующим записям
* подписка на других авторов

## **Требования**

Django==2.2.16  
mixer==7.1.2  
Pillow==8.3.1  
pytest==6.2.4  
pytest-django==4.4.0  
pytest-pythonpath==0.7.3  
requests==2.26.0  
six==1.16.0  
sorl-thumbnail==12.7.0  
Faker==12.0.1  


## **Запуск проекта**

В консоли выполните следующие команды:

1. Клонировать проект из репозитория
```
git clone git@github.com:DoeryMK/yatube.git
```
или
```
git clone https://github.com/DoeryMK/yatube.git
```
2. Перейти в папку с проектом и создать виртуальное окружение
```
cd <имя папки>
```
```
python -m venv venv
```
или
```
python3 -m venv venv
```
3. Активировать виртуальное окружение
```
source venv/Scripts/activate
```
или
```
source venv/bin/activate
```
4. Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
5. Перейти в папку yatube и выполнить миграции
```
cd yatube
```
```
python manage.py makemigrations
```
или 
```
python3 manage.py makemigrations
```
```
python manage.py migrate
```
или
```
python3 manage.py migrate
```
6. Запустить проект
```
python manage.py runserver
```
или 
```
python3 manage.py runserver
```
