PYTHON_PATH ?=
VENV = .venv
UV_INSTALLER = uv-installer-latest.exe
UV_DOWNLOAD_URL = https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.exe
EVOLUTION_ZIP = external-services/evolution-api-2.3.6.zip
EVOLUTION_DIR = external-services/evolution-api-2.3.6/

ifeq ($(OS),Windows_NT)
    RM = rmdir /s /q
    PYTHON_DEFAULT = python
    PIP = $(VENV)\Scripts\pip
    PYTHON_VENV = $(VENV)\Scripts\python
    UV = uv.exe
    NULL_OUTPUT = >nul 2>&1
    WHICH = where
    UNZIP_CMD = tar -xf
    DOCKER_COMPOSE = docker compose
    EVOLUTION_ZIP_WIN = external-services\evolution-api-2.3.6.zip
    EVOLUTION_DIR_WIN = external-services\evolution-api-2.3.6
else
    RM = rm -rf
    PYTHON_DEFAULT = python3
    PIP = $(VENV)/bin/pip
    PYTHON_VENV = $(VENV)/bin/python
    UV ?= $(HOME)/.local/bin/uv
    NULL_OUTPUT = >/dev/null 2>&1
    WHICH = which
    UNZIP_CMD = unzip -q
    DOCKER_COMPOSE = docker compose
    EVOLUTION_ZIP_WIN = $(EVOLUTION_ZIP)
    EVOLUTION_DIR_WIN = $(EVOLUTION_DIR)
endif

.PHONY: setup run clean check-uv install-uv check-python create-venv install-deps

check-uv:
	@echo "Checking UV installation..."
ifeq ($(OS),Windows_NT)
	@$(WHICH) $(UV) $(NULL_OUTPUT) || (echo UV not found. Installing... && $(MAKE) install-uv)
else
	@command -v uv $(NULL_OUTPUT) || command -v $(UV) $(NULL_OUTPUT) || \
		(echo "UV not found. Installing..." && $(MAKE) install-uv)
endif

install-uv:
	@echo "Installing UV..."
ifeq ($(OS),Windows_NT)
	@curl -Lo $(UV_INSTALLER) $(UV_DOWNLOAD_URL)
	@$(UV_INSTALLER) /quiet
	@del $(UV_INSTALLER)
else
	@curl -LsSf https://astral.sh/uv/install.sh | sh
	@echo 'export PATH="$$HOME/.local/bin:$$PATH"' >> ~/.bashrc || true
	@echo 'export PATH="$$HOME/.local/bin:$$PATH"' >> ~/.zshrc || true
endif
	@echo "UV successfully installed!"

check-python:
	@echo Checking Python...
ifeq ($(OS),Windows_NT)
	@if "$(PYTHON_PATH)" NEQ "" ( \
		if exist "$(PYTHON_PATH)" ( \
			echo Using provided Python path: $(PYTHON_PATH) && \
			"$(PYTHON_PATH)" --version \
		) else ( \
			echo ERROR: Provided PYTHON_PATH '$(PYTHON_PATH)' not found! && exit /b 1 \
		) \
	) else ( \
		$(WHICH) python $(NULL_OUTPUT) && (python --version) || (echo Python not found in PATH) \
	)
else
	@if [ -n "$(PYTHON_PATH)" ]; then \
		if [ -x "$(PYTHON_PATH)" ]; then \
			echo "Using provided Python path: $(PYTHON_PATH)"; \
			"$(PYTHON_PATH)" --version; \
		else \
			echo "ERROR: Provided PYTHON_PATH '$(PYTHON_PATH)' not found or not executable."; \
			exit 1; \
		fi \
	else \
		$(WHICH) $(PYTHON_DEFAULT) $(NULL_OUTPUT) && $(PYTHON_DEFAULT) --version || echo "Python not found in PATH"; \
	fi
endif

create-venv: check-uv
	@echo Checking if virtual environment exists...
ifeq ($(OS),Windows_NT)
	@if exist $(VENV) $(RM) $(VENV)
	@echo Creating virtual environment...
	@if "$(PYTHON_PATH)" NEQ "" ( \
		if exist "$(PYTHON_PATH)" ( \
			echo Using provided Python path: $(PYTHON_PATH) && \
			$(UV) venv $(VENV) --python "$(PYTHON_PATH)" --link-mode=copy \
		) else ( \
			echo ERROR: PYTHON_PATH '$(PYTHON_PATH)' not found! && exit /b 1 \
		) \
	) else ( \
		echo Creating virtual environment using project configuration... && \
		$(UV) venv $(VENV) --link-mode=copy \
	)
else
	@if [ -d $(VENV) ]; then $(RM) $(VENV); fi
	@echo "Creating virtual environment..."
	@if [ -n "$(PYTHON_PATH)" ]; then \
		$(UV) venv $(VENV) --python "$(PYTHON_PATH)" --link-mode=copy; \
	else \
		$(UV) venv $(VENV) --link-mode=copy; \
	fi
endif

install-deps: create-venv
	@echo Installing dependencies...
ifeq ($(OS),Windows_NT)
	@if exist requirements.txt ( \
		$(UV) pip install -r requirements.txt --link-mode=copy \
	) else if exist pyproject.toml ( \
		$(UV) sync --link-mode=copy \
	) else ( \
		echo No requirements.txt or pyproject.toml found. Skipping dependency installation. \
	)
else
	@if [ -f requirements.txt ]; then \
		$(UV) pip install -r requirements.txt --link-mode=copy; \
	elif [ -f pyproject.toml ]; then \
		$(UV) sync --link-mode=copy; \
	else \
		echo "No requirements.txt or pyproject.toml found. Skipping dependency installation."; \
	fi
endif
	@echo Dependencies installed successfully!

setup: install-deps
	@echo Setup completed!

run:
	@$(PYTHON_VENV) main.py

clean:
ifeq ($(OS),Windows_NT)
	@if exist $(VENV) rmdir /s /q $(VENV)
else
	@rm -rf $(VENV)
endif
	@echo Virtual environment removed!


evolution-setup:
	@echo "Setting up Evolution API..."
ifeq ($(OS),Windows_NT)
	@if not exist "$(EVOLUTION_ZIP_WIN)" ( \
		echo ERROR: $(EVOLUTION_ZIP) not found! && exit /b 1 \
	)
	@if exist "$(EVOLUTION_DIR_WIN)" $(RM) "$(EVOLUTION_DIR_WIN)"
	@echo Extracting $(EVOLUTION_ZIP)...
	@powershell -Command "Expand-Archive -Path '$(EVOLUTION_ZIP)' -DestinationPath 'external-services' -Force"
else
	@if [ ! -f $(EVOLUTION_ZIP) ]; then \
		echo "ERROR: $(EVOLUTION_ZIP) not found!"; \
		exit 1; \
	fi
	@if [ -d $(EVOLUTION_DIR) ]; then $(RM) $(EVOLUTION_DIR); fi
	@echo "Extracting $(EVOLUTION_ZIP)..."
	@$(UNZIP_CMD) $(EVOLUTION_ZIP) -d external-services
endif
	@echo "Evolution API extracted successfully!"

evolution-start: evolution-setup
	@echo "Starting Evolution API with Docker Compose..."
ifeq ($(OS),Windows_NT)
	@cd $(EVOLUTION_DIR) && $(DOCKER_COMPOSE) up -d
else
	@cd $(EVOLUTION_DIR) && $(DOCKER_COMPOSE) up -d
endif
	@echo "Evolution API started successfully!"

evolution-stop:
	@echo "Stopping Evolution API..."
ifeq ($(OS),Windows_NT)
	@if exist $(EVOLUTION_DIR) ( \
		cd $(EVOLUTION_DIR) && $(DOCKER_COMPOSE) down \
	) else ( \
		echo ERROR: $(EVOLUTION_DIR) not found! && exit /b 1 \
	)
else
	@if [ -d $(EVOLUTION_DIR) ]; then \
		cd $(EVOLUTION_DIR) && $(DOCKER_COMPOSE) down; \
	else \
		echo "ERROR: $(EVOLUTION_DIR) not found!"; \
		exit 1; \
	fi
endif
	@echo "Evolution API stopped successfully!"

evolution-clean:
	@echo "Cleaning Evolution API..."
ifeq ($(OS),Windows_NT)
	@if exist $(EVOLUTION_DIR) ( \
		cd $(EVOLUTION_DIR) && $(DOCKER_COMPOSE) down -v \
	)
	@if exist $(EVOLUTION_DIR) $(RM) $(EVOLUTION_DIR)
else
	@if [ -d $(EVOLUTION_DIR) ]; then \
		cd $(EVOLUTION_DIR) && $(DOCKER_COMPOSE) down -v; \
		$(RM) $(EVOLUTION_DIR); \
	fi
endif
	@echo "Evolution API cleaned successfully!"