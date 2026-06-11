# Makefile for World Cup 2026 Prediction System

# Variables
VENV = venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip
N = 1 # Default number of matches to predict for predict-next

.PHONY: help install status predict-next predict-all reset app verify clean

help:
	@echo "======================================================================"
	@echo "               World Cup 2026 Prediction Makefile                    "
	@echo "======================================================================"
	@echo "Available commands:"
	@echo "  make install      - Create venv and install python dependencies"
	@echo "  make status       - View current tournament standings and bracket state"
	@echo "  make predict-next - Predict the next match (use N=X to predict X matches)"
	@echo "                      Example: make predict-next N=5"
	@echo "  make predict-all  - Predict the entire tournament schedule"
	@echo "  make reset        - Reset predictions and clean the tournament state"
	@echo "  make app          - Launch the interactive Plotly Dash dashboard"
	@echo "  make html         - Generate a standalone interactive HTML results report"
	@echo "  make verify       - Run the mock bracket simulation verification test"
	@echo "  make clean        - Delete pycache, venv, and reset prediction state"
	@echo "======================================================================"

# Target to create the virtual environment and install dependencies
$(VENV)/bin/activate: requirements.txt
	@echo "Creating virtual environment in $(VENV)/..."
	python3 -m venv $(VENV)
	@echo "Upgrading pip..."
	$(PIP) install --upgrade pip
	@echo "Installing dependencies in virtual environment..."
	$(PIP) install -r requirements.txt
	@touch $(VENV)/bin/activate

install: $(VENV)/bin/activate
	@echo "Virtual environment and dependencies are ready!"

status: $(VENV)/bin/activate
	$(PYTHON) run.py --status

predict-next: $(VENV)/bin/activate
	$(PYTHON) run.py --predict-next $(N)

predict-all: $(VENV)/bin/activate
	$(PYTHON) run.py --predict-all

reset: $(VENV)/bin/activate
	$(PYTHON) run.py --reset

app: $(VENV)/bin/activate
	@echo "Starting dashboard app at http://localhost:8050 ..."
	$(PYTHON) app.py

html: $(VENV)/bin/activate
	@echo "Generating interactive results.html report..."
	$(PYTHON) generate_html.py

verify: $(VENV)/bin/activate
	$(PYTHON) verify_bracket.py

clean:
	@echo "Resetting predictions and state..."
	@if [ -f "$(VENV)/bin/python3" ]; then $(PYTHON) run.py --reset 2>/dev/null || true; fi
	@echo "Removing virtual environment and cache files..."
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
