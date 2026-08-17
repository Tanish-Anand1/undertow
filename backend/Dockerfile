FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/app
ENV PORT=7860
EXPOSE 7860
RUN chmod +x start.sh
CMD ["./start.sh"]
