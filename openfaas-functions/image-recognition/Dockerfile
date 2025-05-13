FROM openfaas/of-watchdog:0.8.4 as watchdog

FROM python:3.9-slim

COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY handler.py .

# 下载预训练模型权重
RUN python -c "from tensorflow.keras.applications import MobileNetV2; MobileNetV2(weights='imagenet')"

ENV fprocess="python handler.py"
ENV mode="http"
ENV upstream_url="http://127.0.0.1:8080"

EXPOSE 8080

HEALTHCHECK --interval=3s CMD [ -e /tmp/.lock ] || exit 1

CMD ["fwatchdog"] 