# docker-balancer

Where should I deploy my containers based on resources?
----------------------------


Based on thresholds defined on average CPU percentage and max number of containers.  Deploy containers to the lowest utilized Docker host.


Getting Started
---------------

**From Docker Host** (agent coming soon)

  `/api/<cpu percent(0-100)>/<docker container count>`

    curl -XPOST http://docker-balance/api/30/10
    {
      "cpu_percent": 70,
      "docker_count": 50,
      "docker_host": "10.162.0.12"
    }

**From anywhere show basic metrics**

*lowest utilized host*

    curl -XGET http://docker-balance/api/lowest
    10.162.0.16

*highest utilized host*

    curl -XGET http://docker-balance/api/highest
    10.162.0.11

*list all docker hosts*

    curl -XGET http://docker-balance/api/all
    ['10.162.0.10', '10.162.0.11', '10.162.0.12', '10.162.0.13', '10.162.0.14', '10.162.0.15', '10.162.0.16', '10.162.0.17', '10.162.0.18']

*total of all docker hosts*

		curl -XGET http://docker-balance/api/total
		9

*list available healthy docker hosts*

		curl -XGET http://docker-balance/api/available
		['10.162.0.10', '10.162.0.11', '10.162.0.14', '10.162.0.16', '10.162.0.18']

*available healthy docker hosts total*

		curl -XGET http://docker-balance/api/available-total
		5

*list unavailable unhealthy docker hosts*

		curl -XGET http://docker-balance/api/unavailable
		['10.162.0.12', '10.162.0.13', '10.162.0.15', '10.162.0.17']

*unavailable unhealthy docker hosts total*

		curl -XGET http://docker-balance/api/unavailable-total
		4

**From anywhere show all metrics**

     curl -XGET http://docker-balance/api/stats
     {
        "available": [
           "10.162.0.14",
           "10.162.0.18",
           "10.162.0.16",
           "10.162.0.10",
           "10.162.0.11"
        ],
        "lowest": "10.162.0.16",
        "all": [
           "10.162.0.17",
           "10.162.0.12",
           "10.162.0.11",
           "10.162.0.13",
           "10.162.0.10",
           "10.162.0.14",
           "10.162.0.16",
           "10.162.0.18",
           "10.162.0.15"
        ],
        "total": 9,
        "available_total": 5,
        "highest": "10.162.0.11",
        "unavailable_total": 4,
        "unavailable": {
           "10.162.0.12": "Containers=50",
           "10.162.0.13": "Containers=50",
           "10.162.0.15": "CPU=90",
           "10.162.0.17": "Containers=50"
        }
     }

Install & Run
--------

**Setup Redis http://redis.io/topics/quickstart**

    git clone https://github.com/marshyski/docker-balancer.git
    pip install -r docker-balancer/requirements.txt
    # edit config.yaml to point to Redis Server if not localhost
    cd docker-balancer && bash gunicorn.sh


Configurations
--------------

**config.yaml**

    # Redis host IP, default localhost
    redis_host:

    # Redis host port, default 6379
    redis_port:

    # Redis DB, default 0
	redis_db:

	# Max containers per host, default is 50
	max_container_threshold:

	# Max CPU percent threshold, default is 90
	max_cpu_threshold: '90'

    # API request rate limit for metrics, default is '1 per second'
    # http://flask-limiter.readthedocs.org/en/stable/
    request_limit:


Recommendations
---------------

 1. Have the API not listen on port 80
 2. Create IPTables/FirewallD/Security Group rules to only allow inbound traffic from CIDR or IP Ranges of Docker hosts
 3. Use SSL and Basic Auth in NGINX for the API
 4. If you load balance docker-balance, a Redis cluster will have to be setup.
