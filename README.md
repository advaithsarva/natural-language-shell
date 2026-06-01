# NLP to Linux CLI Translator (Dockerized)

This project is a Dockerized command-line application that translates
natural language instructions into Linux CLI commands using the OpenAI API.
The system is designed to be reproducible, secure, and suitable for
educational evaluation.

Destructive operations such as file deletion or disk formatting are
explicitly blocked.

---

## Features

- Natural language to Linux CLI command translation
- Runs entirely inside a Docker container
- Uses OpenAI API for language understanding
- Enforces safety constraints on generated commands
- Supports advanced Linux commands including:
  - sudo
  - grep, awk, sort, wc
  - pipes and redirection
- API keys handled via environment variables (not stored in code)

---

## Prerequisites

Ensure the following are installed:

- Docker Desktop (Windows, macOS, or Linux)
  Verify installation:
  ```bash
  docker --version


## OpenAI API key
Create one at:
https://platform.openai.com/api-keys

Note: API usage requires separate billing from ChatGPT Plus.

## Project Structure
nlpcli/
├── Dockerfile
├── requirements.txt
├── NLPCLI.py
└── README.md

## Build the Docker Image
From the project root directory:

    docker build -t nlcli .


## Expected result:
    Successfully built ...
    Successfully tagged nlcli:latest

## Run the Application

    Pass the OpenAI API key at runtime using an environment variable.

        docker run --rm -e OPENAI_API_KEY=YOUR_API_KEY nlcli --text "list files in the directory"
    
    Expected output:
        ls