FROM locustio/locust:2.32.4

# Переключаемся на root для установки плагина
USER root
RUN pip3 install locust-plugins

# Возвращаемся к стандартному пользователю (важно для безопасности)
USER locust