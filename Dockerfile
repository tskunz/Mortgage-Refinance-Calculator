# Multi-stage Docker build for mortgage calculator
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY mortgage_requirements.txt .
RUN pip install --no-cache-dir --user -r mortgage_requirements.txt

# Production stage
FROM python:3.11-slim

# Install system dependencies for GUI
RUN apt-get update && apt-get install -y \
    python3-tk \
    x11-apps \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 calculator

# Copy installed packages from builder stage
COPY --from=builder /root/.local /home/calculator/.local

# Set working directory
WORKDIR /app

# Copy application files
COPY mortgage_enhanced_calculator.py .
COPY mortgage_refinance_calculator.py .
COPY mortgage_gui_calculator.py .
COPY mortgage_market_data.py .
COPY mortgage_calculator.html .

# Change ownership to calculator user
RUN chown -R calculator:calculator /app

# Switch to non-root user
USER calculator

# Add local bin to PATH
ENV PATH="/home/calculator/.local/bin:${PATH}"

# Expose port for web version if needed
EXPOSE 8000

# Default command - can be overridden
CMD ["python", "mortgage_gui_calculator.py"]