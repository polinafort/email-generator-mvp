# Генератор рассылок для маркетолога

Помощник маркетолога. Приложение генерирует готовый Markdown для email-рассылки на основе ЦА, тематики и цели рассылки, культуры компании и бренда

Использована модель Ollama Gemma 2 

# Установка и запуск приложения

## 1) Установите нужное ПО
Git: https://git-scm.com/downloads

Python 3.10+: https://www.python.org/downloads/

При установке на Windows отметьте галочку “Add Python to PATH”.

Ollama: https://ollama.com/download

Скачайте модель (один раз):

```ollama pull gemma2:2b```


## 2) Скачайте проект с GitHub
Откройте терминал и выполните:

```git clone https://github.com/polinafort/email-generator-mvp.git```

```cd email-generator-mvp```

## 3) Создайте виртуальное окружение и установите зависимости

### Windows
```python -m venv .venv```

```.venv\Scripts\activate.bat```

```pip install -r requirements.txt```


### macOS / Linux
```python3 -m venv .venv```

```source .venv/bin/activate```

```pip install -r requirements.txt```

## 4) Запустите приложение
В папке проекта:

```streamlit run app.py```

После запуска откройте в браузере ссылку, которую покажет Streamlit (обычно):

http://localhost:8501

## 5) Частые проблемы

### Не удалось получить ответ от модели
Проверьте, что Ollama запущена и API доступно:

Откройте в браузере: http://localhost:11434 (или http://127.0.0.1:11434)

Должно быть: ollama is running

## 6) Как остановить
В терминале, где запущен Streamlit: нажмите Ctrl + C

Ollama обычно продолжает работать в фоне (это нормально).
