import paho.mqtt.client as mqtt
import logging
from time import sleep
from apscheduler.schedulers.background import BackgroundScheduler
import configparser
import sys

import subprocess

process_name = "emoncms_mqtt.php"
command = f"ps aux | grep '{process_name}' | awk '{{print $6}}'"


# Clean-up
def cleanup():
    global running
    logger.info("Clean-up")
    sched.remove_all_jobs()
    sched.shutdown(wait=False)
    running = False

# Getting config
config = configparser.ConfigParser()
config.read('config.ini')

# Debug setup
loglevel = config["General"]["loglevel"]
number_of_inputs = int(config["General"]["num_inputs"])

# EmonMQTT setup
username =      config['emonMQTT']['username']
password =      config['emonMQTT']['password']
emonhost =      config['emonMQTT']['host']
emonMQTTport =  int(config['emonMQTT']['port'])

# Logging setup
logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
       '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(loglevel)

# MQTT/emoncms connection
client = mqtt.Client("TestingMQTT")
client.username_pw_set(username, password)
client.connect(emonhost, port=emonMQTTport, keepalive=60)

# Job
def job():
    try:
        #client.publish("emon/TestingMQTT/value1", 1234)
        

        output = subprocess.check_output(command, shell=True, text=True)
        memory_usage_kb = output.splitlines()[0]
        

        for i in range(number_of_inputs):
            client.publish("emon/TestingMQTT/memory{}".format(i), int(memory_usage_kb))



        logger.info("Published, memory usage: {}".format(memory_usage_kb))
    except Exception as error:
        logger.error("{}".format(error))
        cleanup()

# Setup job every 10 seconds
sched = BackgroundScheduler(daemon=True)
sched.add_job(job, 'cron', second='0-59/10', id='testmqtt_job')

# Schedule/start job 
sched.start()

running = True

# Loop and clean-up
try:
        while running:
            sleep(10)
except KeyboardInterrupt:
    logger.info("Quiting")
    cleanup()
