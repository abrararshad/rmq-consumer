# RMQ Consumer
A simple solution for consuming RabbitMQ queues and pass them onto an external service for execution. 
It can run multiple consumers with Python threading. The purpose of this project is to pass queues to a PHP application BUT as we know PHP is meant to timeout or die, there are stability issues with PHP running as a daemon service.


# Apps / Components
It has three key components / apps:

## Consumer 
Connects to RabbitMQ and consumes specified queues. To run,
```
python app.py consumer local true
```

## Frontend
Provides a web-based management, failed jobs can be re-run. It requires MongoDB to store the data.
```
python app.py dash local true
```
## Logger
Kind of real-time logging interface to see consumer's logs, avoiding SSHing into the server.
```
python app.py logger local true
```
Once run its available at ```example.com/logger```. 


In all above `local` is the environment name, it will look for a config file with the same name in `configuration/evs` folder. `true` is the local server mode.

# Configs
Take a [sample.yml](configurations/envs/sample.yml) from ```configuration/evs``` folder and create a new file for an environment such as ```dev_config.yml``` or ```prod_config.yml```

# Installation
``` 
./install.sh 
```

# Todo
Write tests
