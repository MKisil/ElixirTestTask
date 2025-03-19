# Elixir Test Task

## Setup 

### 1. Clone repository
```sh
git clone https://github.com/MKisil/ElixirTestTask.git
```

### 2. Navigate to project directory
```sh
cd ElixirTestTask
```

### 3. Install dependencies
Make sure you have `pipenv` installed. If not, install it first:
```sh
pip install pipenv
```
Then install the required dependencies:
```sh
pipenv install
```

### 4. Activate the venv
```sh
pipenv shell
```

### 5. Configure API Key
Before running the application, specify your Gemini API key in `config.ini`:
```ini
[API]
gemini_api_key = YOUR_GEMINI_API_KEY
```

### 6. Run the Application
```sh
streamlit run app.py
```

## Online Version
If you prefer not to set up the project locally, you can access the deployed version at:
[Elixir Test Task](https://elixirtask.mikhailok.me/)


