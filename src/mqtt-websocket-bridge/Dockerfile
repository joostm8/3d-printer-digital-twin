FROM python:3.12-alpine
RUN pip install paho-mqtt websockets
COPY mqtt_to_ws_server.py /
CMD ["python", "-u", "mqtt_to_ws_server.py"]