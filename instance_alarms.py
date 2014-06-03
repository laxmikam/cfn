# -*- coding: utf-8 -*-
"""
Created on Tue Jun 03 00:55:22 2014

@author: laxmikam
"""
import boto.ec2
import boto.sns
import boto.utils

def check_or_enable_monitoring(v_inst):
     print "Checking or enabling monitoring for "+str(v_inst)  
     try:
           if (i.monitoring_state != 'enabled'):
               print "         Current monitoring state is: "+v_inst.monitoring_state 
               print "         Enabling Detailed Monitoring"
               v_inst.monitor()    
           else:
               print "         Detailed Monitoring enabled"
     except Exception, e:
                print e


def create_alarms(instances_without_alarms):
    print "creating alarms.."
    print "hello"+str(instances_without_alarms)
    try:
        reservations=ec2_conn.get_all_instances(instances_without_alarms)
        for r in reservations:
            instances = r.instances
            for i in instances:
                check_or_enable_monitoring(i)
                v_alarm = i.id+"-status-alarm"
                alarm = boto.ec2.cloudwatch.alarm.MetricAlarm(
                        connection = cw_conn,
                        name = v_alarm,
                        metric = 'CPUUtilization',
                        namespace = 'AWS/EC2',
                        statistic = 'Maximum',
                        comparison = '<',
                        description = 'status check for '+i.tags['Name']+"("+i.id+")",
                        threshold = 0,
                        period = 60,
                        evaluation_periods = 2,
                        dimensions = {'InstanceId':i.id},
                        insufficient_data_actions = sns_topic_map[v_region])
                cw_conn.put_metric_alarm(alarm)
                print v_alarm+" created"
    except Exception, e:
                print e


def delete_alarms(terminated_instances_with_alarm):
    print "deleting alarms.."
    v_alarms_to_be_deleted = []    
    for inst in terminated_instances_with_alarm:
         v_alarm = inst+"-status-alarm"
         v_alarms_to_be_deleted.append(v_alarm)
    print v_alarms_to_be_deleted 
    try:
        alarms_to_be_deleted = cw_conn.describe_alarms(alarm_names=v_alarms_to_be_deleted)
        print alarms_to_be_deleted
        cw_conn.delete_alarms(str(alarms_to_be_deleted))
        print "Deleted alarms: "+str(alarms_to_be_deleted)
    except Exception, e:
                print e     
         

def start():
    print "Starting.."
    # Associating SNS Topic with each region    
    sns_topic_map = {'us-east-1':'arn:aws:sns:us-east-1:487969498688:instance-status',
                     'us-west-1':'arn:aws:sns:us-west-1:487969498688:instance-status'}

    current_instances=[]
    instances_with_alarms=[]

  
    try:
        # Retreiving current region    
        v_region = boto.utils.get_instance_metadata()['placement']['availability-zone'][:-1]
        #v_region = 'us-east-1'
      
        #Initializing connectins to EC2, Cloudatch and SNS
        cw_conn = boto.ec2.cloudwatch.connect_to_region(v_region)
        ec2_conn = boto.ec2.connect_to_region(v_region)
        sns_conn = boto.sns.connect_to_region(v_region)

        #Generating the list of current instances
        reservations = ec2_conn.get_all_reservations()
        for r in reservations:
            instances = r.instances
            for i in instances:
                if (i.state <> 'terminated' ):
                    current_instances.append(str(i.id))
                
        print "current instances"        
        print current_instances

        #Generating the list of current alarms"    
        existing_alarms = cw_conn.describe_alarms()
        for p in existing_alarms:
            inst=p.name[:p.name.find('-status-alarm')]
            instances_with_alarms.append(str(inst))
    
        print "Instances with Alarms"        
        print instances_with_alarms

        # Generating lists to create and delete alarms    
        instances_without_alarms = list(set(current_instances)-set(instances_with_alarms))
        terminated_instances_with_alarm = list(set(instances_with_alarms)-set(current_instances))

        # calling the functions
        print "Instances without Alarms"
        print instances_without_alarms
        print "Terminated instances with Alarms"
        print terminated_instances_with_alarm
        if (instances_without_alarms <> []) :
            print "instances_without_alarms"
            create_alarms(instances_without_alarms)    
        if (terminated_instances_with_alarm <> []):
            print "terminated_instances_with_alarm"
            #delete_alarms(terminated_instances_with_alarm)    
    except Exception, e:
                print e     
    
    
    
if __name__ == "__main__":  start()    
