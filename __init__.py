from flask import Flask, request, jsonify, make_response, abort
from flask_limiter import Limiter
from werkzeug.contrib.fixers import ProxyFix
import redis
import yaml
import os
import operator

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

def low_high(thing):
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

    if thing == 'lowest':
       return min_host
    if thing == 'highest':
       return max_host
    if thing == 'all':
        return sorted(join_dicts.items(), key=operator.itemgetter(1))
    if thing == 'total':
        return len(join_dicts)
    if thing == 'available':
        return sorted(lowest_host.items(), key=operator.itemgetter(1))
    if thing == 'unavailable':
        return sorted(maxed_host.items(), key=operator.itemgetter(1))


@app.route('/api/<string:awesome>')
def get_lowest_docker(awesome):
    return str(low_high(awesome))

@app.route('/api/<int:health>/<int:count>', methods=['POST'])
def post_docker_info(health, count):
    ip = request.remote_addr

    if count > min_threshold:
       count = min_threshold

    post_dic = {'health': health, 'count': count}
    list_min = min(post_dic, key=post_dic.get)
    list_max = max(post_dic, key=post_dic.get)
    item_max = post_dic.get(list_max)
    item_min = post_dic.get(list_min)
    final = item_max - item_min

    db.set(ip, final)

    return jsonify(host=ip, cpu_util=health, docker_count=count, score=final, status=200)

@app.errorhandler(400)
def bad_request():
    """400 BAD REQUEST"""
    return make_response(jsonify({"error": "wrong URI"}), 400)

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.debug = True
    app.run()
