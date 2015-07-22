"""
Docker Balancer
"""
from flask import Flask, request, jsonify, Response
from flask_limiter import Limiter
from werkzeug.contrib.fixers import ProxyFix
from operator import itemgetter
import redis
import yaml
import json
import os

config_file = os.getcwd() + '/' + 'config.yaml'
config_yaml = yaml.load(file(config_file, 'r'))
min_threshold = int(config_yaml['min_threshold'])
max_threshold = int(config_yaml['max_threshold'])
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
    keys = db.keys('*')

    for key in keys:
        val = int(db.get(key))
        if val >= max_threshold:
            maxed_host[key] = val
        else:
            lowest_host[key] = val

    min_host = min(lowest_host, key=lowest_host.get)
    max_host = max(lowest_host, key=lowest_host.get)
    join_dicts = dict(lowest_host)
    join_dicts.update(maxed_host)

    if service == 'lowest':
        return min_host

    if service == 'highest':
        return max_host

    if service == 'all':
        return str(sorted(join_dicts.items(), key=itemgetter(1)))

    if service == 'total':
        return str(len(join_dicts))

    if service == 'available':
        return str(sorted(lowest_host.items(), key=itemgetter(1)))

    if service == 'available-total':
        return str(len(lowest_host))

    if service == 'unavailable':
        return str(sorted(maxed_host.items(), key=itemgetter(1)))

    if service == 'unavailable-total':
        return str(len(maxed_host))

    if service == 'stats':
        all_array = json.dumps(join_dicts, ensure_ascii=False, sort_keys=True).replace('{', '[').replace('}', ']')
        lowest = min_host
        highest = max_host
        available = json.dumps(lowest_host, ensure_ascii=False, sort_keys=True).replace('{', '[').replace('}', ']')
        available_total = len(lowest_host)
        unavailable = json.dumps(maxed_host, ensure_ascii=False, sort_keys=True).replace('{', '[').replace('}', ']')
        unavailable_total = len(maxed_host)
        total = len(join_dicts)

        return \
        Response(str({"all": all_array, "available": available, "available_total": available_total, "highest": highest, \
        "lowest": lowest, "total": total, "unavailable": unavailable, "unavailable_total": \
        unavailable_total}).replace("',", "',\n").replace("{'", "{\n '").replace("}", '\n}').replace(", '", ", \n '"), \
        mimetype='application/json')

@app.route('/api/<string:service>')
def get_service(service):
    """Route for processing dictionary using service function"""
    return service_func(service)

@app.route('/api/<int:cpu>/<int:count>', methods=['POST'])
def post_docker_info(cpu, count):
    """Post Docker host CPU utilization percent and docker container count"""
    ip = request.remote_addr

    if count > min_threshold:
        count = min_threshold

    post_dic = {'cpu': cpu, 'count': count}
    list_min = min(post_dic, key=post_dic.get)
    list_max = max(post_dic, key=post_dic.get)
    item_max = post_dic.get(list_max)
    item_min = post_dic.get(list_min)
    score = item_max - item_min

    db.set(ip, score)

    return jsonify(docker_host=ip, cpu_percent=cpu, docker_count=count, score=score)


app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run()
