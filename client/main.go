package main

import (
    "fmt"
    "net/http"
    "net"
    "time"
    "io/ioutil"
    "strings"
    "strconv"
    "github.com/spf13/viper"
    "github.com/shirou/gopsutil/mem"
    "github.com/shirou/gopsutil/disk"
    "github.com/shirou/gopsutil/host"
    "github.com/fsouza/go-dockerclient"
)

// HTTP client timeout
var timeout = time.Duration(300 * time.Millisecond)

func dialTimeout(network, addr string) (net.Conn, error) {
    return net.DialTimeout(network, addr, timeout)
}

func main() {

  for {

    // Docker client remote API
    endpoint := "unix:///var/run/docker.sock"
    dockerClient, _ := docker.NewClient(endpoint)

    // Configuration file settings using key-value
    viper.SetConfigName("docker-balancer")
    viper.AddConfigPath("/opt/docker-balancer/conf")
    err := viper.ReadInConfig()
    if err != nil {
       fmt.Println("No Configuration File Using DEFAULTS")
    }

    // Default settings if no config file is supplied
    viper.SetDefault("docker_balancer", "localhost")
    viper.SetDefault("docker_balancer_port", "8888")
    viper.SetDefault("interval", "300")
    viper.SetDefault("username", "undef")
    viper.SetDefault("password", "undef")

    docker_balancer := viper.GetString("docker_balancer")
    docker_balancer_port := viper.GetString("docker_balancer_port")
    interval := viper.GetInt("interval")
    username := viper.GetString("username")
    password := viper.GetString("password")

    transport := http.Transport{
       Dial: dialTimeout,
    }

    client := http.Client{
       Transport: &transport,
    }

    v, _ := mem.VirtualMemory()
    k, _ := disk.DiskUsage("/")
    h, _ := host.HostInfo()
    memusedprctConv := strconv.FormatFloat(v.UsedPercent, 'f', 6, 64)
    memusedprct := strings.Split(memusedprctConv, ".")[0]
    diskusedprctConv := strconv.FormatFloat(k.UsedPercent, 'f', 6, 64)
    diskusedprct := strings.Split(diskusedprctConv, ".")[0]

    timeN := time.Now()
    dateStamp := fmt.Sprintf("%d-%02d-%02dT%02d:%02d:%02d", timeN.Year(), timeN.Month(), timeN.Day(), timeN.Hour(), timeN.Minute(), timeN.Second())

    if err != nil {
       fmt.Println(err.Error())
    }

    containers, _ := dockerClient.ListContainers(docker.ListContainersOptions{All: false})
    dockerCount := 0

    for container := range containers {
        _ = container
        dockerCount += 1
    }

    dockerConv := strconv.Itoa(dockerCount)
    fmt.Sprintf(dockerConv)

    // docker-balancer endpoint and request
    docker_balancer_url := "http://" + docker_balancer + ":" + docker_balancer_port

    docker_balancer_request := "http://" + docker_balancer + ":" + docker_balancer_port + "/api/" + memusedprct + "/" + dockerConv + "/" + diskusedprct

    balancerResponse, err := client.Get(docker_balancer_url)
    if balancerResponse != nil {
       if err != nil {
          fmt.Println(err.Error())
          return
       }

        // Check to see if docker-balancer server is up
       fmt.Println(dateStamp, h.Hostname, "INFO docker-balancer request:", docker_balancer_request)
       reqPost, err := http.NewRequest("POST", docker_balancer_request, nil)
       if password != "undef" {
          reqPost.SetBasicAuth(username, password)
       }

       clientReq := &http.Client{}
       respPost, err := clientReq.Do(reqPost)
       if err != nil {
          fmt.Println(err.Error())
       }
       defer respPost.Body.Close()
       fmt.Println(dateStamp, h.Hostname, "POST docker-balancer status:", respPost.Status)
       postBody, _ := ioutil.ReadAll(respPost.Body)
       fmt.Println(dateStamp, h.Hostname, "POST response body:", string(postBody))
    } else {
       fmt.Println(dateStamp, h.Hostname, "FAIL unable to connect to docker-balancer endpoint:", "http://" + docker_balancer + ":" + docker_balancer_port)
    }

       // Sleep time for, for loop
       time.Sleep(time.Duration(interval) * time.Second)
    }
}
