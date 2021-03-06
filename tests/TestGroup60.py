"""These tests fall under Conformance Test-Suite (OF-SWITCH-1.0.0 TestCases).
    Refer Documentation -- Detailed testing methodology 
    <Some of test-cases are directly taken from oftest> """

"Test Suite 5 --> Counters"

import logging

import unittest
import random

from oftest import config
import oftest.controller as controller
import oftest.cstruct as ofp
import oftest.message as message
import oftest.dataplane as dataplane
import oftest.action as action
import oftest.parse as parse
import oftest.base_tests as base_tests
import time

from oftest.testutils import *
from time import sleep
from FuncUtils import*


def port_queues_get(self, queue_stats, port_num):
            result = []
            for qs in queue_stats.stats:
                if qs.port_no != port_num:
                    continue
                result.append(qs.queue_id)
            return result


class Grp60No10(base_tests.SimpleDataPlane):

    """Verify Packet counters per flow are
    incremented by no. of packets received for that flow"""

    def runTest(self):

        logging.info("Running Grp60No10 PktPerFlow test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state      
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Insert any flow")
        logging.info("Sending N Packets matching the flow")
        logging.info("Verify packet counters increment in accordance")
        
        #Create a Match on Ingress flow
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)
       
        #Send Packets matching the flow 
        num_pkts = 5 
        for pkt_cnt in range(num_pkts):
            self.dataplane.send(of_ports[0],str(pkt))
         
        #Verify Recieved Packets/Bytes Per Flow  
        verify_flowstats(self,match,packet_count=num_pkts)


class Grp60No20(base_tests.SimpleDataPlane):

    """Verify Byte counters per flow are
    incremented by no. of  bytes received for that flow"""

    def runTest(self):

        logging.info("Running Grp60No20 BytPerFlow test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state      
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Insert any flow")
        logging.info("Sending N Packets matching the flow")
        logging.info("Verify byte counters increment in accordance")
        
        #Create a Match on Ingress flow
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)
       
        #Send Packets matching the flow 
        num_pkts = 5 
        byte_count = num_pkts*len(str(pkt))
        for pkt_cnt in range(num_pkts):
            self.dataplane.send(of_ports[0],str(pkt))
         
        #Verify Recieved Packets/Bytes Per Flow  
        verify_flowstats(self,match,byte_count=byte_count)


class Grp60No30(base_tests.SimpleDataPlane):
    
    """Verify Duration_sec and Duration_nsec counters per flow varies in accordance with the amount of 
    time the flow was alive"""

    def runTest(self):
        
        logging.info("Running Grp60No30 DurationPerFlow test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        rc = delete_all_flows(self.controller)
        self.assertEqual(rc, 0, "Failed to delete all flows")

        logging.info("Insert any flow")
        logging.info("Send Flow_stats request after n sec intervals")
        logging.info("Verify duration_sec and nsec counters are incrementing in accordance with the life of flow")

        #Create a flow with match on ingress_port
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)
    
        #Create flow_stats request 
        test_timeout = 30
        stat_req = message.flow_stats_request()
        stat_req.match= match
        stat_req.table_id = 0xff
        stat_req.out_port = ofp.OFPP_NONE
        
        flow_stats_gen_ts =  range (10,test_timeout,10)
        
        for ts in range(0,test_timeout):
            if ts in flow_stats_gen_ts:
                response, pkt = self.controller.transact(stat_req)
                
                self.assertTrue(response is not None,"No response to stats request")
                self.assertTrue(len(response.stats) == 1,"Did not receive flow stats reply")
                
                stat = response.stats[0]
                self.assertTrue(stat.duration_sec == ts,"Flow stats reply incorrect")
                logging.info("Duration of flow is " + str(stat.duration_sec) + str(stat.duration_nsec)) 
            
            sleep(1)


class Grp60No50(base_tests.SimpleDataPlane):

    """Verify that rx_packets counter in the Port_Stats reply
        increments when packets are received on a port"""
    
    def runTest(self):

        logging.info("Running Grp60No50 RxPktPerPort test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        # Clear Switch State
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Insert a flow with match on ingress_port")
        logging.info("Send N Packets on an ingress_port P ")
        logging.info("Send Port_Stats Request for Port P , verify recieved packets counters are incrementing in accordance")
        
        #Insert a flow with match on all ingress port
        (pkt, match ) = wildcard_all_except_ingress(self,of_ports)

        # Send Port_Stats request for the ingress port (retrieve old counter state)
        (counter) = get_portstats(self,of_ports[0])

        # Send packets matching the flow
        num_pkts = 5 
        for pkt_cnt in range(num_pkts):
            self.dataplane.send(of_ports[0],str(pkt))

        pkts = num_pkts+counter[0]

        #Verify recieved packet counters 
        verify_portstats(self,of_ports[0],rx_packets=pkts)

class Grp60No60(base_tests.SimpleDataPlane):

    """Verify that tx_packets counter in the Port_Stats reply , increments when packets are transmitted by a port"""
      
    def runTest(self):

        logging.info("Running Grp60No60 TxPktPerPort test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        #Clear switch state
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Insert any flow matching on in_port=ingress_port, action output to egress_port T ")
        logging.info("Send N Packets matching the flow on ingress_port P ")
        logging.info("Send Port_Stats Request for Port T , verify transmitted packets counters are incrementing in accordance")
        
        #Insert a flow with match on all ingress port
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)
        
        # Send Port_Stats request for the ingress port (retrieve old counter state)
        (counter) = get_portstats(self,of_ports[1])
        
        #Send packets matching the flow
        num_pkts = 5
        for pkt_cnt in range(num_pkts):
            self.dataplane.send(of_ports[0],str(pkt))

        pkts = num_pkts+counter[1]
        
        #Verify transmitted_packet counters 
        verify_portstats(self,of_ports[1],tx_packets=pkts)



class Grp60No70(base_tests.SimpleDataPlane):

    """Verify that recieved bytes counter in the Port_Stats reply , increments in accordance with the bytes recieved on a port"""

    def runTest(self):
        
        logging.info("Running Grp60No70 RxBytPerPort test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Insert any flow matching on in_port=ingress_port")
        logging.info("Send N Packets matching the flow on ingress_port P ")
        logging.info("Send Port_Stats Request for Port P , verify recieved bytes counters are incrementing in accordance")
        
        #Insert a flow with match on all ingress port
        (pkt, match ) = wildcard_all_except_ingress(self,of_ports)

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[0])
           
        #Send packets matching the flow.
        num_pkts = 5
        byte_count = num_pkts*len(str(pkt))
        for pkt_cnt in range(num_pkts):
            self.dataplane.send(of_ports[0],str(pkt))

        byt_count = byte_count+counter[2]

        #Verify recieved_bytes counters 
        verify_portstats(self,of_ports[0],rx_byte=byt_count)


class Grp60No80(base_tests.SimpleDataPlane):

    """Verify that trasnsmitted bytes counter in the Port_Stats reply , increments in accordance with the bytes trasmitted by a port"""

    def runTest(self):
        
        logging.info("Running Grp60No80 TxBytPerPort test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Insert any flow matching on in_port=ingress_port,action = output to egress_port T")
        logging.info("Send N Packets matching the flow on ingress_port P ")
        logging.info("Send Port_Stats Request for Port T , verify trasmitted bytes counters are incrementing in accordance")
        
        #Insert a flow with match on all ingress port
        (pkt, match ) = wildcard_all_except_ingress(self,of_ports)

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[1])
        
        #Send packets matching the flow.
        num_pkts = 5
        byte_count = num_pkts*len(str(pkt))
        for pkt_cnt in range(num_pkts):
            self.dataplane.send(of_ports[0],str(pkt))

        byt_count = byte_count+counter[3]
        
        #Verify trasmitted_bytes counters 
        verify_portstats(self,of_ports[1],tx_byte=byt_count)


class Grp60No90(base_tests.SimpleDataPlane):

    """Verify that rx_dropped counters in the Port_Stats reply increments in accordance with the packets dropped by RX"""

    def runTest(self):
        
        logging.info("Running Grp60No90 Rx_Drops test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has rx_dropped count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[0])

        rx_drp = counter[4]
        logging.info("recieved dropped count is :" + str(rx_drp))


class Grp60No100(base_tests.SimpleDataPlane):

    """Verify that tx_dropped counters in the Port_Stats reply increments in accordance with the packets dropped by TX"""

    def runTest(self):
        
        logging.info("Running Grp60No100 Tx_Drops test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has tx_dropped count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[1])
        
        tx_drp = counter[5]
        logging.info("Transmitted dropped count is :" + str(tx_drp))


class Grp60No110(base_tests.SimpleDataPlane):

    """Verify that rx_errors counters in the Port_Stats reply increments in accordance with number of recieved error  
          This is a super-set of more specific receive errors and should be greater than or equal to the sum of all
                  rx_*_err values"""

    def runTest(self):
        
        logging.info("Running Grp60No110 Rx_Errors test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has rx_errors count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[0])

        rx_err = counter[6]    
        logging.info("Recieve Errors count is :" + str(rx_err))


class Grp60No120(base_tests.SimpleDataPlane):

    """Verify that Tx_errors counters in the Port_Stats reply increments in accordance with number of trasmit error"""

    def runTest(self):
        
        logging.info("Running Grp60No120 Tx_Errors test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has Tx_errors count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[0])
        
        tx_err = counter[7]
        logging.info("Trasmit Error count is :" + str(tx_err))


class Grp60No130(base_tests.SimpleDataPlane):

    """Verify that rx_frm_err counters in the Port_Stats reply increments in accordance with the number of frame alignment errors"""

    def runTest(self):
        
        logging.info("Running Grp60No130 Rx_Frame_Err test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has rx_frame_err count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[0])
        
        rx_fr_err = counter[8]
        logging.info("Recieve Frame Errors count is :" + str(rx_fr_err))



class Grp60No140(base_tests.SimpleDataPlane):

    """Verify that rx_over_err counters in the Port_Stats reply increments in accordance with the number of with RX overrun"""

    def runTest(self):
        
        logging.info("Running Grp60No140 Rx_O_Err test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has rx_over_err count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[0])
        
        rx_over_err = counter[9]
        logging.info("Recieve Overrun Errors  count is :" + str(rx_over_err))


class Grp60No150(base_tests.SimpleDataPlane):

    """Verify that rx_crc_err counters in the Port_Stats reply increments in accordance with the number of crc errors"""

    def runTest(self):
        
        logging.info("Running Grp60No150 crc_error test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has rx_crc_err count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[0])

        rx_crc_err = counter[10]   
        logging.info("Recieve CRC Errors  count is :" + str(rx_crc_err))


class Grp60No160(base_tests.SimpleDataPlane):

    """Verify that collisons counters in the Port_Stats reply increments in accordance with the collisions encountered by the switch """

    def runTest(self):
        
        logging.info("Running Grp60No160 Collisions test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Port_Stats Request")
        logging.info("Verify reply has Collisions count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[0])

        collisions = counter[11]
        logging.info("collisions count is :" + str(collisions))


class Grp60No170(base_tests.SimpleDataPlane):

    """Verify that tx_packets in the queue_stats reply increments in accordance with the number of transmitted packets"""
    
    def runTest(self):
        logging.info("Running Grp60No170 TxPktPerQueue test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        # Get queue stats from switch (retrieve current state)
        (queue_stats,p) = get_queuestats(self,ofp.OFPP_ALL,ofp.OFPQ_ALL)
  
        for idx in range(len(of_ports)):
            ingress_port = of_ports[idx]
            egress_port = of_ports[(idx + 1) % len(of_ports)]

            queue_id = port_queues_get(self,queue_stats,egress_port)

            for egress_queue_id in queue_id:

                #Clear switch state
                rv = delete_all_flows(self.controller)
                self.assertEqual(rv, 0, "Failed to delete all flows")

                # Get Queue stats for selected egress queue only
                (qs_before,p) = get_queuestats(self,egress_port,egress_queue_id)

                #Insert a flow with enqueue action to queues configured on egress_port
                (pkt,match) = enqueue(self,ingress_port,egress_port,egress_queue_id)
              
                #Send packet on the ingress_port and verify its received on egress_port
                send_packet(self,pkt,ingress_port,egress_port)
                
                expected_packets = qs_before.stats[0].tx_packets+1

                verify_queuestats(self,egress_port,egress_queue_id,expect_packet=expected_packets)
       

class Grp60No180(base_tests.SimpleDataPlane):

    """Verify that tx_bytes in the queue_stats reply increments in accordance with the number of transmitted bytes"""
    
    def runTest(self):
        logging.info("Running Grp60No180 TxBytPerQueue test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
        
        # Get queue stats from switch (retrieve current state)
        (queue_stats,p) = get_queuestats(self,ofp.OFPP_ALL,ofp.OFPQ_ALL)
  
        for idx in range(len(of_ports)):
            ingress_port = of_ports[idx]
            egress_port = of_ports[(idx + 1) % len(of_ports)]

            queue_id = port_queues_get(self,queue_stats,egress_port)

            for egress_queue_id in queue_id:

                #Clear switch state
                rv = delete_all_flows(self.controller)
                self.assertEqual(rv, 0, "Failed to delete all flows")

                # Get Queue stats for selected egress queue only
                (qs_before,p) = get_queuestats(self,egress_port,egress_queue_id)

                #Insert a flow with enqueue action to queues configured on egress_port
                (pkt,match) = enqueue(self,ingress_port,egress_port,egress_queue_id)
              
                #Send packet on the ingress_port and verify its received on egress_port
                send_packet(self,pkt,ingress_port,egress_port)
                
                expected_bytes = qs_before.stats[0].tx_bytes+len(str(pkt))

                verify_queuestats(self,egress_port,egress_queue_id,expect_byte=expected_bytes)
       
       

class Grp60No190(base_tests.SimpleDataPlane):

    """Verify that tx_errors in the queue_stats reply increments in accordance with the number of packets dropped due to overrun """

    def runTest(self):
        
        logging.info("Running Grp60No190 TxErrorPerQueue test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear switch State        
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Send Queue_Stats Request")
        logging.info("Verify reply has Tramitted Overrun errors count ")

        # Send Port_Stats request for the ingress port (retrieve current counter state)
        (counter) = get_portstats(self,of_ports[0])

        tx_err = counter[12]
        logging.info("Transmit Overrun Error count is :" + str(tx_err))




class Grp60No200(base_tests.SimpleDataPlane):

    """Verify that active_count counter in the Table_Stats reply , increments in accordance with the flows inserted in a table"""

    def runTest(self):

        logging.info("Running Grp60No200 Active Counter test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear Switch state
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Insert any flow matching on in_port=ingress_port,action = output to egress_port T ")
        logging.info("Send Table_Stats, verify active_count counter is incremented in accordance")

        #Insert a flow with match on all ingress port
        (pkt, match ) = wildcard_all_except_ingress(self,of_ports)

        #Generate  Table_Stats
        verify_tablestats(self,expect_active=1)


class Grp60No210(base_tests.SimpleDataPlane):
    
    """Verify that lookup_count and matched_count counter in the Table_Stats reply 
        increments in accordance with the packets looked up and matched with the flows in the table"""

    def runTest(self):

        logging.info("Running Grp60No210 LookupMatchedCount test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        self.assertTrue(len(of_ports) > 1, "Not enough ports for test")
         
        #Clear Switch state
        rv = delete_all_flows(self.controller)
        self.assertEqual(rv, 0, "Failed to delete all flows")

        logging.info("Insert any flow matching on in_port=ingress_port,action = output to egress_port")
        logging.info("Send N packets matching the flow, N' packets not matching the flow")
        logging.info("Send Table_Stats, verify lookup_count = N+N' & matched_count=N ")

        #Get Current Table Stats
        (current_lookedup,current_matched,current_active) = get_tablestats(self)

        #Insert a flow with match on all ingress port
        (pkt, match ) = wildcard_all_except_ingress(self,of_ports)

        #send packet pkt N times (pkt matches the flow)
        num_sends = 5
        for pkt_cnt in range(num_sends):
            self.dataplane.send(of_ports[0],str(pkt))

        #send packet pkt N' (pkt does not match the flow)
        num_sends2 = 5
        for pkt_cnt in range(num_sends):
            self.dataplane.send(of_ports[1],str(pkt))

        new_lookup = num_sends+num_sends2+current_lookedup
        new_matched = num_sends+current_matched

        #Verify lookup_count and matched_count counters.
        verify_tablestats(self,expect_lookup=new_lookup,expect_match=new_matched)


