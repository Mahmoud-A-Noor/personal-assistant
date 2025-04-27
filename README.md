# Personal Assistant

## Index
- [Features](#features)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [Credentials Setup](#credentials-setup)
- [Qdrant Setup (with API Key or No API Key)](#qdrant-setup-with-api-key-or-no-api-key)
- [License](#license)
- [Contact](#contact)

A professional, modular, and extensible personal assistant project designed to automate tasks, manage information, and integrate with various tools and services.

## Features
- Modular core for easy extension
- Secure credential management
- Integration with external APIs and local tools
- Persistent storage and retrieval

## Getting Started

### Prerequisites
- Python 3.8+
- (Optional) [pipenv](https://pipenv.pypa.io/en/latest/) or [venv](https://docs.python.org/3/library/venv.html)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/personal-assistant.git
   cd personal-assistant
   ```
2. (Optional) Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(```playwright install``` must be run after installing dependencies so agent can interact with the browser)
   *(If `requirements.txt` is missing, install dependencies manually as described in the codebase.)*

### Usage
Run the assistant:
```bash
python main.py
```

## Project Structure
```
core/           # Core logic and base classes
models/         # Data models
qdrant_storage/ # Persistent storage
utils/          # Utility scripts and helpers
tools/          # Integrations and custom tools
main.py         # Entry point
```

## Contributing
We welcome contributions! To get started:
1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

### Contribution Guidelines
- Follow [PEP8](https://pep8.org/) for Python code style
- Write clear commit messages
- Add/update documentation as needed
- Ensure all tests pass before submitting a PR

## Qdrant Setup (with API Key or No API Key)

You can run Qdrant either with API key authentication (recommended for production) or without an API key (suitable for local development/testing).

### With API Key
Run the following command in your project directory:

```bash
docker run -p 6333:6333 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    -e QDRANT__SERVICE__API_KEY="<your_qdrant_api_key>" \
    qdrant/qdrant
```

- Replace `<your_qdrant_api_key>` with your actual API key (which is actually just a long random string).
- This will persist Qdrant data in the `qdrant_storage` folder and expose the service on port 6333.

### Without API Key
For local development or if you do not require authentication, you can run Qdrant without an API key:

```bash
docker run -p 6333:6333 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

- This will start Qdrant without authentication.
- Data will be persisted in the `qdrant_storage` folder and the service will be available on port 6333.

## Credentials Setup

### Google Calendar Integration
To enable calendar operations, you need to add a `credentials.json` file in the base directory of this project.

1. Visit the [Google Cloud Console Credentials Page](https://console.cloud.google.com/apis/credentials).
2. Create an **OAuth 2.0 Client ID**.
3. Download the credentials and rename the file to `credentials.json`.
4. Place `credentials.json` in the root (base) directory of this project.

### Google API Key
To obtain a Google API Key:
1. Go to the [Google Cloud Console Credentials Page](https://console.cloud.google.com/apis/credentials).
2. Click "Create Credentials" and select "API key".
3. Copy the generated API key and add it to your `.env` file as `GOOGLE_API_KEY`.

### Google App Password
If you are using Gmail for email integration, you need to generate an App Password:
1. Enable 2-Step Verification on your Google account.
2. Visit [Google App Passwords](https://myaccount.google.com/apppasswords).
3. Generate an app password for "Mail".
4. Use this password as `EMAIL_PASSWORD` in your `.env` file.

### Gemini API Key
To obtain a Gemini API key:
1. Go to the [Google AI Studio Gemini API page](https://aistudio.google.com/app/apikey).
2. Sign in with your Google account.
3. Create or copy your Gemini API key.
4. Add it to your `.env` file as `GEMINI_API_KEY`.

### Telegram Bot Integration
To obtain your Telegram Bot ID:

1. Open Telegram on your smartphone.
2. Search for the contact **BotFather** (`@BotFather`). This contact is available to all Telegram users.
3. Start a conversation and send the command `/newbot`.
4. Follow the instructions provided by BotFather to create your bot and obtain the bot token (ID).

## License
This project is licensed under the MIT License. See `LICENSE` for details.

## Contact
For questions, suggestions, or support, please open an issue or contact the maintainer at [mahmoudnoor917@gmail.com].
