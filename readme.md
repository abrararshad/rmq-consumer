# RMQ Consumer
A simple solution for consuming RabbitMQ queues and pass them onto an external service for execution. 
It can run multiple consumers with Python threading. The purpose of this project is to pass queues to a PHP application BUT as we know PHP is meant to timeout or die, there are stability issues with PHP running as a daemon service. 

# Related Projects
[facile-it/rabbitmq-consumer](https://github.com/facile-it/rabbitmq-consumer) - It was the closest and a good solution written in GO, but I found its installation a little overwhelming given the tool should work alongside the main application not the other way around. 


# Configs
Take a sample.yml from ```configuration/evs``` folder and create a new file for an environment such as ```dev_config.yml``` or ```prod_config.yml```

# How to run
## First install the dependencies 
``` 
pip install -e . 
```
## And run with dev or any other environment
```
python app.py dev
```

# Todo
Write tests