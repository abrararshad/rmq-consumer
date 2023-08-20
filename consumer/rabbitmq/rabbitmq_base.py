from flask import current_app
import multiprocessing as mp
import sys
import json
import functools
import queue
import pika
import threading

error_queue = mp.Queue()


class RabbitMQRejectionThresholdError(Exception):
    pass


class RabbitMQSubscribeError(Exception):
    pass


ERRORS_THRESHOLD_REACHED = False
ERRORS_THRESHOLD_LIMIT = 25


def error_monitor_thread_callback():
    global ERRORS_THRESHOLD_REACHED
    global ERRORS_THRESHOLD_LIMIT

    fatal_error_count = 0
    while True:
        if not error_queue.empty():
            # get count of total errors in queue
            error_count = error_queue.qsize()
            if error_count >= ERRORS_THRESHOLD_LIMIT:
                ERRORS_THRESHOLD_REACHED = True
                break
            else:
                ERRORS_THRESHOLD_REACHED = False


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

    logger = None

    def __init__(self, host=default_host, exchange=None, exchange_type=None, logger=None):
        self.logger = logger
        self.host = host
        self.exchange = exchange
        self.exchange_type = exchange_type if exchange_type else 'direct'

        self.setup_config()

        if self.config['ERRORS_THRESHOLD_LIMIT']:
            global ERRORS_THRESHOLD_LIMIT
            ERRORS_THRESHOLD_LIMIT = int(self.config['ERRORS_THRESHOLD_LIMIT'])

        self.new_initialization = False

        if not self.role_type or self.role_type not in ['subscriber', 'sender']:
            raise ValueError('Role is invalid: '.format(self.role_type))

        self.cache_key += self.role_type.upper()
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

    def log(self, msg):
        if self.logger:
            self.logger(msg)
        else:
            print(msg)

    def initialize(self):
        self.log('Setting up RabbitMQ with key: {}'.format(self.cache_key))

        cached_connection_info = current_app.config.get(self.cache_key)
        if cached_connection_info:
            (cached_connection, cached_channel, cached_queue_name) = cached_connection_info

            if cached_connection and cached_channel and cached_queue_name:
                # Check the validity of the cached connection
                try:
                    cached_channel.basic_publish(
                        exchange='',  # Use the default exchange for lightweight check
                        routing_key='test',  # Use a test routing key or queue name
                        body='test message',
                        properties=pika.BasicProperties(delivery_mode=1)  # Non-persistent message
                    )
                    self.connection = cached_connection
                    self.channel = cached_channel
                    self.queue_name = cached_queue_name
                    self.log("Reusing cached RabbitMQ connection")
                except (pika.exceptions.ConnectionClosed, pika.exceptions.ChannelClosed):
                    pass
                finally:
                    self.log("Cached connection is no longer valid. Re-establishing connection...")
                    self.teardown()
                    self.setup_connection()
            else:
                self.setup_connection()
        else:
            self.setup_connection()

        self.log("RabbitMQ initialized. Exchange:{} type:{} | Queue:{} | Instance:{}".format(
            self.exchange, self.exchange_type, self.queue_name, self.new_initialization))

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
            self.log(e)
            raise e

    def declare_amq(self):
        # if self.role_type == 'sender':
        self.channel.exchange_declare(
            exchange=self.exchange,
            exchange_type=self.exchange_type,
            durable=True
        )

        self.bind_queue()

    def bind_queue(self):
        if 'RMQ_BINDING_KEYS' in current_app.config:
            self.routing_keys = current_app.config['RMQ_BINDING_KEYS']

        if not self.routing_keys:
            self.routing_keys = self.config['ROUTING_KEYS']

        if not self.routing_keys:
            self.log('Routing keys are not defined')

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
                self.log('Queue:%s bound to key:%s ' % (self.queue_name, binding))

    def send(self, msg_object, routing_key='primary.#', priority=0, close_con=False):
        try:
            msg = json.dumps(msg_object)
            response = self.publish(msg, routing_key, priority)
        except Exception as e:
            self.log('Reconnecting to RabbitMQ: {}'.format(e))
            self.setup_connection()
            response = self.publish(msg, routing_key, priority)

        self.log('RabbmitMQ response: ' + str(response))
        if close_con:
            self.teardown()

    def publish(self, msg, routing_key='primary.#', priority=0):
        try:
            self.log('Publishing on exchange: {} with routing key: {}'.format(self.exchange, routing_key))
            return self.channel.basic_publish(exchange=self.exchange,
                                              routing_key=routing_key,
                                              body=msg,
                                              mandatory=True,
                                              properties=pika.BasicProperties(
                                                  delivery_mode=2,  # Persisting messages
                                                  priority=priority
                                              ))
        except pika.exceptions.UnroutableError:
            raise RabbitMQSubscribeError("Message could not be routed to any queue")

    def subscribe(self, callback, with_pool=True, **kwargs):
        self.log("Subscribing with jobs limit: {}".format(self.jobs_limit))

        on_message_callback = functools.partial(self.message_handler, args=(
            self.connection, self.threads, callback, with_pool, kwargs))

        self.channel.basic_qos(prefetch_count=self.jobs_limit)
        self.channel.basic_consume(queue=self.queue_name,
                                   auto_ack=False,
                                   on_message_callback=on_message_callback)

        self.log('RabbitMQ subscribed...')
        self.log_active_children()

        try:
            # Start the error monitoring thread
            error_monitor_thread = threading.Thread(target=error_monitor_thread_callback)
            error_monitor_thread.start()
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.log('Consumer stopped by user')
        except Exception as error:
            self.log('Error occurred: {}'.format(str(error)))
            raise error
        finally:
            self.shutdown(with_pool)

    def shutdown(self, with_pool=True):
        try:
            self.channel.stop_consuming()
            if not with_pool:
                self.close_threads()

            if with_pool:
                self.close_pool()
        except Exception as e:
            self.log(e)

        self.teardown()
        self.log_active_children()

    def teardown(self):
        self.close_channel()
        self.close_connection()
        self.clear_cache()

    def close_connection(self):
        if self.connection:
            self.connection.close()

        self.connection = None

    def close_channel(self):
        if self.channel:
            self.channel.close()
            self.channel = None

    def close_pool(self):
        self.log('About to close the pool')
        if self.pool_started:
            try:
                self.pool.close()
                self.pool.join()
            except Exception as e:
                self.log(e)

        self.pool = None
        self.jobs = []

    def close_threads(self):
        try:
            for thread in self.threads:
                thread.join()
                # thread.close()
        except Exception as e:
            self.log('Error closing threads: {}'.format(e))

        self.threads = []

    def log_active_children(self):
        self.log(f'Active childs: {len(mp.active_children())}')

    def clear_cache(self):
        current_app.config[self.cache_key] = None

    def message_handler(self, channel, method, properties, body, args):
        global ERRORS_THRESHOLD_REACHED
        global ERRORS_THRESHOLD_LIMIT

        if ERRORS_THRESHOLD_REACHED:
            raise RabbitMQRejectionThresholdError(f'Rejection threshold reached {ERRORS_THRESHOLD_LIMIT}')

        (connection, threads, callback, with_pool, extra_args) = args
        delivery_tag = method.delivery_tag
        redelivered = method.redelivered

        self.log('Inside message handler')

        if with_pool and not self.pool_started:
            self.jobs = mp.Manager().Queue()

        if with_pool:
            self.jobs.put((body, delivery_tag, extra_args))

        if with_pool and not self.pool_started:
            self.pool = mp.Pool(self.jobs_limit, self.pool_machine, (callback,), 1)
            self.pool_started = True

        if not with_pool:
            # Implement - https://stackoverflow.com/questions/20886565/using-multiprocessing-process-with-a-maximum-number-of-simultaneous-processes
            num_child = len(mp.active_children()) + 1
            p = mp.Process(target=callback, args=(channel, delivery_tag, body, extra_args),
                           name=f"proc_{num_child}_{delivery_tag}")

            p.start()
            threads.append(p)

    def pool_machine(self, callback):
        self.log('Inside pool')
        while True:
            try:
                self.log('Awaiting job')
                job = self.jobs.get()
                (body, delivery_tag, extra_args) = job
                try:
                    callback(self.channel, delivery_tag, body, extra_args)
                except Exception as e:
                    log('Callback error occurred: {}'.format(str(e)))

                self.log('Job done!!')
                sys.exit(0)
            except queue.Empty:
                break
            else:
                pass

        return True

    def setup_config(self):
        self.config = current_app.config['RMQ']
        self.queue_name = self.config['QUEUE']
        self.auto_delete = self.config['AUTO_DELETE']
        if not self.exchange:
            self.exchange = self.config['EXCHANGE']['NAME']
            self.exchange_type = self.config['EXCHANGE']['TYPE']
