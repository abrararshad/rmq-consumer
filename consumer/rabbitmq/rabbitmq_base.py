import multiprocessing as mp
import json
import functools
import queue
import pika
from flask import current_app
from rmq.config import RMQConfig
from utils.func import log, log_error


class RabbitMQBase(object):
    new_initialization = False

    '''
    It can be either subscriber or sender
    '''
    role_type = None

    '''
    Key by which we store connection details, each role type will append to it.
    '''
    cache_key = 'RABBIT_MQ_CONNECTION_'
    connection = None
    channel = None

    queue_name = None
    auto_delete = False
    routing_keys = None

    '''
    Default 1, it is decided based on number of logical processors below.
    '''
    jobs_limit = 1

    '''
    30 days - messages expiry time
    '''
    message_ttl = 2.592e+6

    # Pool
    pool = None
    jobs = None
    pool_started = False

    # If not using pool then threads
    threads = []

    config = {}
    credentials = None

    default_host = '/'

    manager = None

    def __init__(self, host=default_host, exchange=None, exchange_type=None):
        self.host = host
        self.exchange = exchange
        self.exchange_type = exchange_type if exchange_type else 'direct'

        self.setup_config()

        self.new_initialization = False

        if not self.role_type or self.role_type not in ['subscriber', 'sender']:
            raise ValueError('Role is invalid: '.format(self.role_type))

        self.cache_key += self.role_type.upper()
        self.jobs = mp.Manager().Queue()

        if self.config['JOBS_LIMIT']:
            self.jobs_limit = int(self.config['JOBS_LIMIT'])
        else:
            """
            Otherwise two jobs per logical processor
            """
            total_cpus = mp.cpu_count()
            self.jobs_limit = (total_cpus - 1 if total_cpus > 1 else total_cpus) * 2

        try:
            self.initialize()
        except ConnectionError as e:
            raise e

    def initialize(self):
        log('Setting up RabbitMQ with key: {}'.format(self.cache_key))
        if self.cache_key in current_app.config and current_app.config[self.cache_key] is not None:
            (connection, channel, queue_name) = current_app.config[self.cache_key]

            # Todo: make sure connection is still valid
            if connection and channel and queue_name:
                self.connection = connection
                self.channel = channel
                self.queue_name = queue_name
            else:
                self.setup_connection()
        else:
            self.setup_connection()

        log("RabbitMQ initialized. Exchange:{} type:{} | Queue:{} | Instance:{}".format(self.exchange,
                                                                                        self.exchange_type,
                                                                                        self.queue_name,
                                                                                        self.new_initialization))

    def setup_connection(self):
        self.new_initialization = True

        try:
            self.credentials = pika.PlainCredentials(self.config['USER'], self.config['PASS'])
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.config['SERVER'], port=self.config['PORT'],
                                          virtual_host=self.host, credentials=self.credentials,
                                          heartbeat=self.config['HEARTBEAT'],
                                          blocked_connection_timeout=self.config['TIMEOUT']))

            self.channel = self.connection.channel()
            self.declare_amq()

            current_app.config[self.cache_key] = self.connection, self.channel, self.queue_name

        except ConnectionError as e:
            log(e)
            raise e

    def declare_amq(self):
        if self.role_type == 'sender':
            self.channel.exchange_declare(
                exchange=self.exchange,
                exchange_type=self.exchange_type,
                durable=True
            )

        self.bind_queue()

    def bind_queue(self):
        if not self.config['ROUTING_KEYS']:
            log('Routing keys are not defined')

        self.routing_keys = self.config['ROUTING_KEYS']

        args = {}
        if self.exchange_type == 'topic':
            args = {
                'x-max-priority': 10
            }

        self.channel.queue_declare(self.queue_name, durable=True, arguments=args, auto_delete=self.auto_delete)

        if self.routing_keys:
            for binding in self.routing_keys:
                self.channel.queue_bind(
                    exchange=self.exchange,
                    queue=self.queue_name,
                    routing_key=binding
                )
                log('Queue:%s bound to key:%s ' % (self.queue_name, binding))

    def send(self, msg_object, routing_key='primary.#', priority=0, close_con=False):
        try:
            msg = json.dumps(msg_object)
            response = self.publish(msg, routing_key, priority)
        except Exception as e:
            log('Reconnecting to RabbitMQ: {}'.format(e))
            self.setup_connection()
            response = self.publish(msg, routing_key, priority)

        log('RabbmitMQ response: ' + str(response))
        if close_con:
            self.close_connection()

    def publish(self, msg, routing_key='primary.#', priority=0):
        log('Publishing on exchange: {} with routing key: {}'.format(self.exchange, routing_key))
        return self.channel.basic_publish(exchange=self.exchange,
                                          routing_key=routing_key,
                                          body=msg,
                                          mandatory=True,
                                          properties=pika.BasicProperties(
                                              delivery_mode=2,  # Persisting messages
                                              priority=priority
                                          ))

    def subscribe(self, callback, with_pool=True, **kwargs):
        log("Subscribing with jobs limit: {}".format(self.jobs_limit))

        on_message_callback = functools.partial(self.message_handler, args=(
            self.connection, self.threads, callback, with_pool, kwargs))

        self.channel.basic_qos(prefetch_count=self.jobs_limit)
        self.channel.basic_consume(queue=self.queue_name,
                                   auto_ack=False,
                                   on_message_callback=on_message_callback)

        log('RabbitMQ subscribed...')

        error = None
        try:
            self.channel.start_consuming()
        except Exception as error:
            log_error('Closing RabbitMQ: {}'.format(str(error)))
            self.channel.stop_consuming()

        if not with_pool:
            # Wait for all to complete
            for thread in self.threads:
                thread.join()

        self.close_connection(error)

    def close_connection(self, error=None):
        if self.connection:
            self.connection.close()

        self.clear_cache()
        raise Exception(error)

    def clear_cache(self):
        current_app.config[self.cache_key] = None

    def message_handler(self, channel, method, properties, body, args):
        (connection, threads, callback, with_pool, extra_args) = args
        delivery_tag = method.delivery_tag
        redelivered = method.redelivered

        if with_pool:
            self.jobs.put((body, delivery_tag, extra_args))

        if with_pool and not self.pool_started:
            self.pool = mp.Pool(self.jobs_limit, self.pool_machine, (callback,))
            self.pool_started = True
            print(self.pool)

        if not with_pool:
            # Implement - https://stackoverflow.com/questions/20886565/using-multiprocessing-process-with-a-maximum-number-of-simultaneous-processes
            # p = mp.Process(target=callback, args=(connection, channel, delivery_tag, body))
            # p.start()
            # threads.append(p)
            callback(channel, method, body, )

    def pool_machine(self, callback):
        log('Inside pool')
        while True:
            try:
                log('Awaiting job')
                job = self.jobs.get()
                (body, delivery_tag, extra_args) = job
                callback(self.channel, delivery_tag, body, extra_args)
                log('Job done!!')
            except queue.Empty:
                # log('Queue empty breaking')
                break
            else:
                pass

        return True

    def setup_config(self):
        self.config = RMQConfig.config['RMQ']
        self.queue_name = self.config['QUEUE']
        self.auto_delete = self.config['AUTO_DELETE']
        if not self.exchange:
            self.exchange = self.config['EXCHANGE']['NAME']
            self.exchange_type = self.config['EXCHANGE']['TYPE']
