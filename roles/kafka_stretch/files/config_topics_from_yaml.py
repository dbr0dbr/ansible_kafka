#!/bin/python3
import os
import yaml
import config
import logging
import sys

logging.basicConfig(level=logging.INFO, filename='config_topics.log', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

def create_topic(config_topic):
  print(f'create topic {config_topic["name"]}: ', config_topic)
  logging.info(f'create topic {config_topic["name"]}: {config_topic}')
  if 'partitions' in config_topic and "retention.ms" in config_topic:
    os.popen(f'{config.kafka_bin_dir}/kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor {config.default_replication_factor} --partitions {config_topic["partitions"]} --topic {config_topic["name"]} --config retention.ms={config_topic["retention.ms"]}')
  elif 'partitions' in config_topic and not "retention.ms" in config_topic:
    os.popen(f'{config.kafka_bin_dir}/kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor {config.default_replication_factor} --partitions {config_topic["partitions"]} --topic {config_topic["name"]}')
  elif not 'partitions' in config_topic and "retention.ms" in config_topic:
    os.popen(f'{config.kafka_bin_dir}/kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor {config.default_replication_factor} --partitions {config.default_partitions} --topic {config_topic["name"]} --config retention.ms={config_topic["retention.ms"]}')
  elif not 'partitions' in config_topic and not "retention.ms" in config_topic:
    os.popen(f'{config.kafka_bin_dir}/kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor {config.default_replication_factor} --partitions {config.default_partitions} --topic {config_topic["name"]}')
  
def update_topic(config_topic, current_topic):
  set_retention_ms(config_topic, current_topic)
  set_partitions(config_topic, current_topic)

def set_partitions(config_topic, current_topic):
  if 'partitions' in config_topic:
    if config_topic['partitions'] > int(current_topic['PartitionCount']): 
      print(f'set {config_topic["partitions"]} partitions for topic {config_topic["name"]}')
      os.popen(f'{config.kafka_bin_dir}/kafka-topics.sh --bootstrap-server localhost:9092 --alter --topic {config_topic["name"]} --partitions {config_topic["partitions"]}')
      logging.info(f'set {config_topic["partitions"]} partitions for topic {config_topic["name"]}')
    elif config_topic['partitions'] == int(current_topic['PartitionCount']): 
      logging.debug(f'topic {config_topic["name"]} already has {config_topic["partitions"]} partitions')
    else: 
      logging.warn(f'Topic {config_topic["name"]} currently has {current_topic["PartitionCount"]} partitions, which is higher than the requested {config_topic["partitions"]}')
      raise ValueError(f'Topic {config_topic["name"]} currently has {current_topic["PartitionCount"]} partitions, which is higher than the requested {config_topic["partitions"]}')

def set_retention_ms(config_topic, current_topic):
  if 'retention.ms' in config_topic and 'Configs' in current_topic and 'retention.ms' in current_topic['Configs'] and str(config_topic['retention.ms']) == current_topic['Configs']['retention.ms']: 
    logging.debug(f'topic {config_topic["name"]} already has retention.ms={config_topic["retention.ms"]}')
    return
  elif 'retention.ms' not in config_topic and 'Configs' in current_topic and 'retention.ms' in current_topic['Configs'] :
    os.popen(f'{config.kafka_bin_dir}/kafka-configs.sh --bootstrap-server 127.0.0.1:9092  --entity-type topics --entity-name {config_topic["name"]} --alter --delete-config retention.ms') 
    print(f'remove retention.ms from topic {config_topic["name"]}')
    logging.info(f'remove retention.ms from topic {config_topic["name"]}')
  elif 'retention.ms' not in config_topic and (('Configs' in current_topic and not 'retention.ms' in current_topic['Configs']) or not 'Configs' in current_topic): 
    logging.debug(f'topic {config_topic["name"]} already has not set retention.ms')
    return
  else:
    os.popen(f'{config.kafka_bin_dir}/kafka-configs.sh --bootstrap-server 127.0.0.1:9092  --entity-type topics --entity-name {config_topic["name"]} --alter --add-config retention.ms={config_topic["retention.ms"]}') 
    print(f'change retention.ms to {config_topic["retention.ms"]} in topic {config_topic["name"]}')
    logging.info(f'change retention.ms to {config_topic["retention.ms"]} in topic {config_topic["name"]}')

def get_current_topics():
  rez=os.popen(f'{config.kafka_bin_dir}/kafka-topics.sh --describe --zookeeper 127.0.01:2181 |grep PartitionCount').readlines()
  rezult_lines=[line.strip() for line in rez]
  current_topics=[dict(zip(rezult_line.replace(':','').split()[::2],rezult_line.replace(':','').split()[1::2])) for rezult_line in rezult_lines]
  for topic in current_topics:
    if 'Configs' in topic:
      topic['Configs']=dict(zip(topic['Configs'].replace('=',',').split(',')[::2], topic['Configs'].replace('=',',').split(',')[1::2]))
  return current_topics

def get_config_topics():
  try:
    with open("topics_config.yml", 'r') as stream:
      topics_with_prefix=[]
      data=yaml.safe_load(stream)
      config_topics=data['kafkaTopics']
      prefix_list=data['environments']
      logging.debug(f'prefix_list = {prefix_list}')
      validate_config_values(config_topics)
      if not prefix_list:
        return config_topics
      for prefix in prefix_list:
        if prefix == 'default_env':
          for topic in config_topics:
            topics_with_prefix.append(topic)  
        elif ' ' in prefix:
          logging.warn(f'spaces in environments  {prefix}')
          raise ValueError(f'spaces in environments  {prefix}')
        elif prefix != None:
          for topic in config_topics:
            topics_with_prefix.append({k:(f'{prefix}.{v}' if k=='name' else v) for (k,v) in topic.items()})
      return topics_with_prefix
  except yaml.YAMLError:
    logging.warn('cannot parse topics_config.yml')
    raise
  except:
    logging.warn("No such file or directory: 'topics_config.yml'")
    raise

def validate_config_values(config_topics): 
  for config_topic in config_topics:
    if not 'name' in config_topic or config_topic['name'] == None:
      logging.warn(f'name cannot be emty')
      raise ValueError(f'name cannot be emty')
    if config_topic['name'] in config.system_topics:
      logging.warn(f'{config_topic["name"]} is system topic!')
      raise ValueError(f'{config_topic["name"]} is system topic!')
    if "retention.ms" in config_topic:
      if config_topic["retention.ms"] != 0 and not config_topic["retention.ms"]:
        logging.warn(f'empty retention.ms in  {config_topic["name"]}')
        raise ValueError(f'empty retention.ms in  {config_topic["name"]}')
      elif (config_topic["retention.ms"] != -1 and config_topic["retention.ms"] < 0) or not type(config_topic["retention.ms"]) is int:
        logging.warn(f'retention.ms must be int, -1 or >= 0 in topic {config_topic["name"]}')
        raise ValueError(f'retention.ms must be int, -1 or >= 0 in topic {config_topic["name"]}')  
    if 'partitions' in config_topic and (not type(config_topic["partitions"]) is int or config_topic["partitions"] <= 0) :
      logging.warn(f'partitions must be int and  > 0 in topic {config_topic["name"]}')
      raise ValueError(f'partitions must be int and  > 0 in topic {config_topic["name"]}')

logging.info('========================= script running =========================')
config_topics=get_config_topics()
logging.debug(f'config_topics={config_topics}')
current_topics=get_current_topics()
logging.debug(f'current_topics={current_topics}')

for config_topic in config_topics:
  if not str(config_topic['name']) in [current_topic['Topic'] for current_topic in current_topics]:
    create_topic(config_topic)
  else:
    for current_topic in current_topics:
      if current_topic['Topic'] == str(config_topic['name']):
        update_topic(config_topic, current_topic)