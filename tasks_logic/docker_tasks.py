import subprocess

import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.results.backends.redis import RedisBackend
from dramatiq.results import Results

from os import environ

import pika

creds = pika.PlainCredentials(environ.get("BROKER_USERNAME", "Riven"),
                              environ.get("BROKER_PASSWORD", "testpassword"))
if environ.get("debug", True):
    # local testing env #
    rabbitmq_broker = RabbitmqBroker(host="127.0.0.1", credentials=creds)
    redis_backend = RedisBackend(host="127.0.0.1")
else:
    # docker network env #
    rabbitmq_broker = RabbitmqBroker(host="rabbitmq")
    redis_backend = RedisBackend(host="redis")


dramatiq.set_broker(rabbitmq_broker)
rabbitmq_broker.add_middleware(Results(backend=redis_backend))

@dramatiq.actor
def print_result(message_data, result):
    print(f"The result of message {message_data['message_id']} was {result}.")


@dramatiq.actor
def print_error(message_data, exception_data):
    print(f"Message {message_data['message_id']} failed:")
    print(f"  * type: {exception_data['type']}")
    print(f"  * message: {exception_data['message']!r}")


@dramatiq.actor(store_results=True)
def build_docker_instance(*args, **kwargs): #args - dramatiq bypass
    build_command = ["docker", "build", ".", "-f",
                     f"{kwargs['full_path'] + '/' if kwargs['full_path'][-1:] != '/' else kwargs['full_path'] + ''}{kwargs['dockerfile']}",
                     "-t", kwargs['service_name']]
    # dramatiq error will NULL return bypass #
    output = ""
    try:
        output += subprocess.check_output(build_command, stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        output += e.output.decode()
    return output


@dramatiq.actor(store_results=True)
def run_docker_instance(*args, **kwargs): #args - dramatiq bypass
    run_command = ['docker', 'run', '-p', f"{kwargs['service_port']}:{kwargs['service_port']}", '-t', kwargs['service_name']]
    output = ""
    try:
        output += subprocess.check_output(run_command, stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        output += e.output.decode()
    return output


if __name__ == '__main__':
    print(build_docker_instance(full_path="/Users/d.saschenko/PycharmProjects/diplomSiem/internal/Services/anotherService",
                          dockerfile="Dockerfile", service_name="testname"))
    print(run_docker_instance(service_name="testname", port="5432"))