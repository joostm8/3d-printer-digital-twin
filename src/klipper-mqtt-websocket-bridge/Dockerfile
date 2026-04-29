FROM python:3.12-alpine
RUN pip install paho-mqtt websockets
COPY klipper_mqtt_to_ws_server.py /
CMD ["python", "-u", "klipper_mqtt_to_ws_server.py"]