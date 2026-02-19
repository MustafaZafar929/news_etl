FROM python:3.10-slim

# Set the home directory
ENV DAGSTER_HOME=/opt/dagster/dagster_home
RUN mkdir -p $DAGSTER_HOME

WORKDIR /opt/dagster/app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest (though we mostly mount files via volumes)
COPY . .

# Expose the UI port
EXPOSE 3000

# Default command (overridden by docker-compose)
CMD ["dagster", "webserver", "-h", "0.0.0.0", "-p", "3000"]