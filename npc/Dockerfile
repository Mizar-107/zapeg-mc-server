FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY heraldor.py ./
COPY heraldor_director.py ./
COPY heraldor_campaign.py ./
COPY campaign-heraldor.yml ./
CMD ["python", "-u", "heraldor.py"]
