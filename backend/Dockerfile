FROM public.ecr.aws/lambda/python:3.11

# Copy production requirements first to leverage Docker cache
COPY requirements-prod.txt ./
RUN pip install -r requirements-prod.txt

# Copy application code
# Force rebuild 2026-03-08
COPY . .

# Set the CMD to your handler
CMD ["lambda_handler.handler"]