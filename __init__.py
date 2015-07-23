"""
Docker Balancer
"""
from flask import Flask, request, jsonify, Response
from flask_limiter import Limiter
from werkzeug.contrib.fixers import ProxyFix
from json import dumps
from os import getcwd
import redis
import yaml

config_file = getcwd() + '/' + 'config.yaml'
config_yaml = yaml.load(file(config_file, 'r'))
max_container_threshold = int(config_yaml['max_container_threshold'])
max_cpu_threshold = int(config_yaml['max_cpu_threshold'])
redis_host = config_yaml['redis_host']
redis_port = config_yaml['redis_port']
redis_db = config_yaml['redis_db']

db = redis.StrictRedis(redis_host, redis_port, redis_db)
app = Flask(__name__)
limiter = Limiter(app)

def service_func(service):
    """Processing dictionary for return to flask route"""
    lowest_host = {}
    maxed_host = {}
    all_hosts = []
    keys = db.keys('*')

    for key in keys:
        value = db.get(key)
        cpu = int(value.split(' ', 1)[0])
        count = int(value.split(' ', 1)[1])
        all_hosts.append(key)

        if cpu >= max_cpu_threshold:
            maxed_host[key] = 'CPU=' + str(cpu)

        if count >= max_container_threshold:
            maxed_host[key] = 'Containers=' + str(count)

        if cpu < max_cpu_threshold and key not in maxed_host:
            lowest_host[key] = cpu

        if count < max_container_threshold and key not in maxed_host:
            lowest_host[key] = count

    min_host = min(lowest_host, key=lowest_host.get)
    max_host = max(lowest_host, key=lowest_host.get)
    join_dicts = dict(lowest_host)
    join_dicts.update(maxed_host)

    if service == 'lowest':
        return min_host

    if service == 'highest':
        return max_host

    if service == 'all':
        return str(sorted(all_hosts))

    if service == 'total':
        return str(len(join_dicts))

    if service == 'available':
        return str(sorted(lowest_host.keys()))

    if service == 'available-total':
        return str(len(lowest_host))

    if service == 'unavailable':
        return str(sorted(maxed_host.keys()))

    if service == 'unavailable-total':
        return str(len(maxed_host))

    if service == 'stats':
        all_array = dumps(all_hosts, ensure_ascii=False, sort_keys=True)
        lowest = min_host
        highest = max_host
        available = dumps(lowest_host.keys(), ensure_ascii=False, sort_keys=True)
        available_total = len(lowest_host)
        unavailable = dumps(maxed_host, ensure_ascii=False, sort_keys=True)
        unavailable_total = len(maxed_host)
        total = len(join_dicts)

        return \
        Response(str({"all": all_array, "available": available, "available_total": available_total, \
        "highest": highest, "lowest": lowest, "total": total, "unavailable": unavailable, "unavailable_total": \
        unavailable_total}).replace("'", '"').replace('"{', '{').replace('}"', '}').replace('",', '",\n')\
        .replace('{"', '{\n "').replace("},", '\n },\n').replace(', "', ', \n "').replace('}}', '\n }\n}')\
        .replace('"["', '[\n "').replace(']",', '\n ],')\
        , mimetype='application/json')

@app.route('/api/<string:service>')
def get_service(service):
    """Route for processing dictionary using service function"""
    return service_func(service)

@app.route('/api/<int:cpu>/<int:count>', methods=['POST'])
def post_docker_info(cpu, count):
    """Post Docker host CPU utilization percent and docker container count"""
    ip_addr = request.remote_addr
    value = "%s %s" % (cpu, count)
    db.set(ip_addr, value)

    return jsonify(docker_host=ip_addr, cpu_percent=cpu, docker_count=count)


app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.debug = True
    app.run()
