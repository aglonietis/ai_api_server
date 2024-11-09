# Instructions

## Requirements

You need Docker and Docker Compose

## Initialization

Start the project up by running:

```
docker compose up
```

If you have 8000 port already used then

Copy .env.example to .env and edit the API_PORT

Llama Model safe tensors file has been excluded

Can be downloaded again and moved into the folder with:

```
hugginface-cli login
huggingface-cli download meta-llama/Llama-3.2-1B-Instruct --local-dir app/models/Llama-3.2-1B-Instruct


```

