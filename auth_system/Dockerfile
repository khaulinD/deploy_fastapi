FROM python:3.10-slim

WORKDIR .

COPY auth_system/requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .
# Expose the port
EXPOSE 8000

# Copy and execute the initialization script
#COPY db-init.sh /usr/src/app/
#RUN chmod +x /usr/src/app/db-init.sh
#RUN /usr/src/app/db-init.sh


CMD ["uvicorn", "auth_system.application:app", "--host", "0.0.0.0", "--port", "8000"]
#CMD gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000

