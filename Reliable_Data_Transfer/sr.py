import config
import threading
import time
import udt
import util


# Selective Repeat reliable transport protocol.
class SelectiveRepeat:

  NO_PREV_ACK_MSG = "Don't have previous ACK to send, will wait for server to timeout."

  # "msg_handler" is used to deliver messages to application layer
  def __init__(self, local_port, remote_port, msg_handler):
    util.log("Starting up `Selective Repeat` protocol ... ")
    self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
    self.msg_handler = msg_handler
    self.sender_base = 0
    self.next_sequence_number = 0
    # self.set_timer()
    self.window = [b'']*config.WINDOW_SIZE
    self.expected_sequence_number = 0
    self.receiver_last_ack = b''
    self.is_receiver = True
    self.sender_lock = threading.Lock()

    self.sender_buffer = [b'']*config.WINDOW_SIZE
    self.is_ack = [False]*config.WINDOW_SIZE
    self.timer_pkt = [self.set_timer(-1)]*config.WINDOW_SIZE
    self.recv_base = 0
    self.ack_sent = [False]*config.WINDOW_SIZE
    self.recv_buffer = [b'']*config.WINDOW_SIZE

  # Modified to remember which packet's timer expired
  def set_timer(self, sequence_number):
    return threading.Timer((config.TIMEOUT_MSEC/1000.0), self._timeout, {sequence_number: sequence_number})
    

  # "send" is called by application. Return true on success, false otherwise.
  def send(self, msg):
    self.is_receiver = False
    # If sequence number is within the window, packetize and send data
    if self.next_sequence_number < (self.sender_base + config.WINDOW_SIZE):
      self._send_helper(msg)
      return True
    else:
      util.log("Window is full. App data rejected.")
      time.sleep(1)
      return False


  # Helper fn for thread to send the next packet
  def _send_helper(self, msg):
    self.sender_lock.acquire()
    packet = util.make_packet(msg, config.MSG_TYPE_DATA, self.next_sequence_number)
    packet_data = util.extract_data(packet)
    util.log("Sending data: " + util.pkt_to_string(packet_data))
    self.network_layer.send(packet)  
     
    if self.next_sequence_number < self.sender_base + config.WINDOW_SIZE:
      # Finding the index of the packet that we just sent in the window
      packet_num = (self.next_sequence_number - self.sender_base) % config.WINDOW_SIZE

      # Save to buffer in case packet needs to be retransmitted
      self.sender_buffer[packet_num] = packet

      # Setting is_ack to False since packet hasn't been ack'ed yet. 
      self.is_ack[packet_num] = False

      # Start timer for this packet
      self.timer_pkt[packet_num] = self.set_timer(self.next_sequence_number)
      self.timer_pkt[packet_num].start()

      # Increase nextseqnum
      self.next_sequence_number+=1
    
    self.sender_lock.release()
    return


  # "handler" to be called by network layer when packet is ready.
  def handle_arrival_msg(self):
    msg = self.network_layer.recv()
    msg_data = util.extract_data(msg)

    if(msg_data.is_corrupt):
      if(self.is_receiver):
        # if self.expected_sequence_number == 0:
        #   util.log("Packet received is corrupted. " + self.NO_PREV_ACK_MSG)
        #   return
        self.network_layer.send(self.receiver_last_ack)
        util.log("Received corrupted data. Resending ACK: "
                 + util.pkt_to_string(util.extract_data(self.receiver_last_ack)))
      return

    # If ACK message, assume its for sender
    if msg_data.msg_type == config.MSG_TYPE_ACK:
      self.sender_lock.acquire()

      # Find index of packet received 
      packet_num = (msg_data.seq_num - self.sender_base) % config.WINDOW_SIZE

      # Set ack to true
      self.is_ack[packet_num] = True

      # Stop packet timer
      self.timer_pkt[packet_num].cancel()
      self.timer_pkt[packet_num] = self.set_timer(msg_data.seq_num)
      util.log(f"Received ACK with seq # {msg_data.seq_num}: "
                 + util.pkt_to_string(msg_data) + ". Cancelling timer.")

      # If packet at sendbase is ack'ed, move window frame ahead.
      # We can keep moving window frame ahead till we reach the first unack'ed packet.
      try: 
        while self.is_ack[0]:
              self.sender_base+=1
              # Move is_ack ahead by 1 index
              # Add is_ack = False for the last index to maintain size
              self.is_ack = self.is_ack[1:] + [False]

              # Move packet's timer ahead
              self.timer_pkt = self.timer_pkt[1:] + [self.set_timer(-1)]

              # Remove packet from sender buffer
              self.sender_buffer = self.sender_buffer[1:] + [b'']
      except IndexError:
        pass
      self.sender_lock.release()

    # If DATA message, assume its for receiver
    else:
      assert msg_data.msg_type == config.MSG_TYPE_DATA
      util.log("Received DATA: " + util.pkt_to_string(msg_data))

      # ack signal for received packet
      ack_pkt = util.make_packet(b'', config.MSG_TYPE_ACK, msg_data.seq_num)

      # If packet with sequence number in [recv_base, recv_base + N -1] is received
      if msg_data.seq_num in range(self.recv_base, self.recv_base + config.WINDOW_SIZE):
        # Send ACK
        self.network_layer.send(ack_pkt)
        util.log("Sent ACK: " + util.pkt_to_string(util.extract_data(ack_pkt)))

        # Find index of packet received and set sent_ack to True for this packet
        packet_num = (msg_data.seq_num - self.recv_base) % config.WINDOW_SIZE
        self.ack_sent[packet_num] = True
        self.receiver_last_ack = ack_pkt
        
        # Store in buffer
        self.recv_buffer[packet_num] = msg_data.payload

        # If packet at recv_base has been received and ack'ed, move the window frame ahead
        if msg_data.seq_num == self.recv_base:
          while self.ack_sent[0]:
            self.msg_handler(self.recv_buffer[0])
            self.recv_base += 1
            self.ack_sent = self.ack_sent[1:] + [False]
            self.recv_buffer = self.recv_buffer[1:] + [b'']
              
      # If packet with sequence number in [recv_base-N, recv_base-1] is received
      elif msg_data.seq_num in range(self.recv_base-config.WINDOW_SIZE, self.recv_base):
        # Possible ack packet loss - Send ack again so that sender doesn't keep retransmitting
        self.network_layer.send(ack_pkt)
        util.log("Resent ACK: " + util.pkt_to_string(util.extract_data(ack_pkt)))
      
      else:
        return

    return


  # Cleanup resources.
  def shutdown(self):
    if not self.is_receiver: self._wait_for_last_ACK()
    for timer in self.timer_pkt:
      if timer.is_alive(): timer.cancel()
    util.log("Connection shutting down...")
    self.network_layer.shutdown()


  def _wait_for_last_ACK(self):
    while self.sender_base < self.next_sequence_number-1:
      util.log("Waiting for last ACK from receiver with sequence # "
               + str(int(self.next_sequence_number-1)) + ".")
      time.sleep(1)

  # This has been modified to indicate which packet's timer has timed out.
  # For this, we need to edit the set_timer function to remember the sequence num. 
  def _timeout(self, sequence_number):
    util.log(f"Timeout! Resending packets with seq {sequence_number} " +".")
    self.sender_lock.acquire()

    # Find index of packet that was lost within window
    packet_num = (sequence_number - self.sender_base) % config.WINDOW_SIZE
    
    # Reset packet's timer
    self.timer_pkt[packet_num].cancel()
    self.timer_pkt[packet_num] = self.set_timer(sequence_number)
    
    # Retrieve packet from buffer and send
    pkt = self.sender_buffer[packet_num]
    self.network_layer.send(pkt)

    # Start packet's timer
    self.timer_pkt[packet_num].start()
    util.log("Resending packet: " + util.pkt_to_string(util.extract_data(pkt)))
    self.sender_lock.release()
    return
