# RMQ Consumer
Takes queues from RabbitMQ and pass their payloads to the external services.

# Configs
Take a sample.yml from ```configuration/evs``` folder and create a new file for an environment such as ```dev_config.yml``` or ```prod_config.yml```

# How to run
## First install the dependencies 
``` 
pip install -e . 
```
## And run with dev environment
```
python app.py dev
```

# Todo
Write tests