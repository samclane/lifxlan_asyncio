import asyncio
import logging

import lifxlan

from lifxlan_asyncio.async_helpers import run_async


async def get_broadcast_addrs(loop=asyncio.get_event_loop()):
    return await run_async(loop, lifxlan.get_broadcast_addrs)

UDP_BROADCAST_IP_ADDRS = await get_broadcast_addrs()
UDP_BROADCAST_PORT = lifxlan.UDP_BROADCAST_PORT


class AsyncDevice(lifxlan.Device):
    async def refresh(self):
        self.label = await self.get_label()
        self.location = await self.get_location()
        self.group = await self.get_group()
        self.power_level = await self.get_power()
        self.host_firmware_build_timestamp, self.host_firmware_version = await self.get_host_firmware_tuple()
        self.wifi_firmware_build_timestamp, self.wifi_firmware_version = await self.get_wifi_firmware_tuple()
        self.vendor, self.product, self.version = await self.get_version_tuple()
        self.product_name = await self.get_product_name()
        self.product_features = await self.get_product_features()

    async def get_label(self):
        try:
            response = await self.req_with_resp(GetLabel, StateLabel)
            self.label = response.label.encode('utf-8')
            if type(self.label).__name__ == 'bytes': # Python 3
                self.label = self.label.decode('utf-8')
        except:
            raise
        return self.label

    async def get_location(self):
        try:
            response = await self.req_with_resp(GetLocation, StateLocation)
            self.location = response.label.encode('utf-8')
            if type(self.location).__name__ == 'bytes': # Python 3
                self.location = self.location.decode('utf-8')
        except:
            raise
        return self.location

    async def get_group(self):
        try:
            response = await self.req_with_resp(GetGroup, StateGroup)
            self.group = response.label.encode('utf-8')
            if type(self.group).__name__ == 'bytes': # Python 3
                self.group = self.group.decode('utf-8')
        except:
            raise
        return self.group

    async def set_label(self, label):
        if len(label) > 32:
            label = label[:32]
        await self.req_with_ack(SetLabel, {"label": label})

    async def get_power(self):
        try:
            response = await self.req_with_resp(GetPower, StatePower)
            self.power_level = response.power_level
        except:
            raise
        return self.power_level

    async def set_power(self, power, rapid=False):
        on = [True, 1, "on"]
        off = [False, 0, "off"]
        if power in on and not rapid:
            success = await self.req_with_ack(SetPower, {"power_level": 65535})
        elif power in off and not rapid:
            success = await self.req_with_ack(SetPower, {"power_level": 0})
        elif power in on and rapid:
            success = await self.fire_and_forget(SetPower, {"power_level": 65535})
        elif power in off and rapid:
            success = await self.fire_and_forget(SetPower, {"power_level": 0})
        else:
            logging.warning("Invalid power settings")
            success = False
        return success

    async def get_host_firmware_tuple(self):
        build = None
        version = None
        try:
            response = await self.req_with_resp(GetHostFirmware, StateHostFirmware)
            build = response.build
            version = float(str(str(response.version >> 16) + "." + str(response.version & 0xff)))
        except:
            raise
        return build, version

    async def get_host_firmware_build_timestamp(self):
        self.host_firmware_build_timestamp, self.host_firmware_version = await self.get_host_firmware_tuple()
        return self.host_firmware_build_timestamp

    async def get_host_firmware_version(self):
        self.host_firmware_build_timestamp, self.host_firmware_version = await self.get_host_firmware_tuple()
        return self.host_firmware_version

    async def get_wifi_info_tuple(self):
        signal = None
        tx = None
        rx = None
        try:
            response = await self.req_with_resp(GetWifiInfo, StateWifiInfo)
            signal = response.signal
            tx = response.tx
            rx = response.rx
        except:
            raise
        return signal, tx, rx

    async def get_wifi_signal_mw(self):
        signal, tx, rx = await self.get_wifi_info_tuple()
        return signal

    async def get_wifi_tx_bytes(self):
        signal, tx, rx = await self.get_wifi_info_tuple()
        return tx

    async def get_wifi_rx_bytes(self):
        signal, tx, rx = await self.get_wifi_info_tuple()
        return rx

    async def get_wifi_firmware_tuple(self):
        build = None
        version = None
        try:
            response = await self.req_with_resp(GetWifiFirmware, StateWifiFirmware)
            build = response.build
            version = float(str(str(response.version >> 16) + "." + str(response.version & 0xff)))
        except:
            raise
        return build, version

    async def get_wifi_firmware_build_timestamp(self):
        self.wifi_firmware_build_timestamp, self.wifi_firmware_version = await self.get_wifi_firmware_tuple()
        return self.wifi_firmware_build_timestamp

    async def get_wifi_firmware_version(self):
        self.wifi_firmware_build_timestamp, self.wifi_firmware_version = await self.get_wifi_firmware_tuple()
        return self.wifi_firmware_version

    async def get_version_tuple(self):
        vendor = None
        product = None
        version = None
        try:
            response = await self.req_with_resp(GetVersion, StateVersion)
            vendor = response.vendor
            product = response.product
            version = response.version
        except:
            raise
        return vendor, product, version

    async def get_product_name(self):
        product_name = None
        if self.product == None:
            self.vendor, self.product, self.version = await self.get_version_tuple()
        if self.product in product_map:
            product_name = product_map[self.product]
        return product_name

    async def get_product_features(self):
        product_features = None
        if self.product == None:
            self.vendor, self.product, self.version = await self.get_version_tuple()
        if self.product in product_map:
            product_features = features_map[self.product]
        return product_features

    async def get_vendor(self):
        self.vendor, self.product, self.version = await self.get_version_tuple()
        return self.vendor

    async def get_product(self):
        self.vendor, self.product, self.version = await self.get_version_tuple()
        return self.product

    async def get_version(self):
        self.vendor, self.product, self.version = await self.get_version_tuple()
        return self.version

    async def get_location_tuple(self):
        label = None
        updated_at = None
        try:
            response = await self.req_with_resp(GetLocation, StateLocation)
            self.location = response.location
            label = response.label
            updated_at = response.updated_at
        except:
            raise
        return self.location, label, updated_at

    async def get_location_label(self):
        self.location, label, updated_at = await self.get_location_tuple()
        return label

    async def get_location_updated_at(self):
        self.location, label, updated_at = await self.get_location_tuple()
        return updated_at

    async def get_group_tuple(self):
        try:
            response = await self.req_with_resp(GetGroup, StateGroup)
            self.group = response.group
            label = response.label
            updated_at = response.updated_at
        except:
            raise
        return self.group, label, updated_at

    async def get_group_label(self):
        self.group, label, updated_at = await self.get_group_tuple()
        return label

    async def get_group_updated_at(self):
        self.group, label, updated_at = await self.get_group_tuple()
        return updated_at

    async def get_info_tuple(self):
        time = None
        uptime = None
        downtime = None
        try:
            response = await self.req_with_resp(GetInfo, StateInfo)
            time = response.time
            uptime = response.uptime
            downtime = response.downtime
        except:
            raise
        return time, uptime, downtime

    async def get_time(self):
        time, uptime, downtime = await self.get_info_tuple()
        return time

    async def get_uptime(self):
        time, uptime, downtime = await self.get_info_tuple()
        return uptime

    async def get_downtime(self):
        time, uptime, downtime = await self.get_info_tuple()
        return downtime

    async def is_light(self):
        if self.product == None:
            self.vendor, self.product, self.version = await self.get_version_tuple()
        return self.product in light_products

    async def supports_color(self):
        if self.product_features == None:
            self.product_features = await self.get_product_features()
        return self.product_features['color']

    async def supports_temperature(self):
        if self.product_features == None:
            self.product_features = await self.get_product_features()
        return self.product_features['temperature']

    async def supports_multizone(self):
        if self.product_features == None:
            self.product_features = await self.get_product_features()
        return self.product_features['multizone']

    async def supports_infrared(self):
        if self.product_features == None:
            self.product_features = await self.get_product_features()
        return self.product_features['infrared']

    async def supports_chain(self):
        if self.product_features == None:
            self.product_features = await self.get_product_features()
        return self.product_features['chain']

    async def device_radio_str(self, indent):
        signal, tx, rx = await self.get_wifi_info_tuple()
        s = "Wifi Signal Strength (mW): {}\n".format(signal)
        s += indent + "Wifi TX (bytes): {}\n".format(tx)
        s += indent + "Wifi RX (bytes): {}\n".format(rx)
        return s

    def __str__(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.refresh())
        indent = "  "
        s = self.device_characteristics_str(indent)
        s += indent + self.device_firmware_str(indent)
        s += indent + self.device_product_str(indent)
        s += indent + self.device_time_str(indent)
        s += indent + loop.run_until_complete(self.device_radio_str(indent))
        return s

    # Don't wait for Acks or Responses, just send the same message repeatedly as fast as possible
    async def fire_and_forget(self, msg_type, payload={}, timeout_secs=DEFAULT_TIMEOUT, num_repeats=DEFAULT_ATTEMPTS):
        socket_id = self.initialize_socket(timeout_secs)
        sock = self.socket_table[socket_id]
        msg = msg_type(self.mac_addr, self.source_id, seq_num=0, payload=payload, ack_requested=False, response_requested=False)
        sent_msg_count = 0
        sleep_interval = 0.05 if num_repeats > 20 else 0
        while(sent_msg_count < num_repeats):
            if self.ip_addr:
                sock.sendto(msg.packed_message, (self.ip_addr, self.port))
            else:
                for ip_addr in UDP_BROADCAST_IP_ADDRS:
                    sock.sendto(msg.packed_message, (ip_addr, self.port))
            if self.verbose:
                print("SEND: " + str(msg))
            sent_msg_count += 1
            await asyncio.sleep(sleep_interval)  # Max num of messages device can handle is 20 per second.
        await self.close_socket(socket_id)

    # Usually used for Set messages
    async def req_with_ack(self, msg_type, payload, timeout_secs=DEFAULT_TIMEOUT, max_attempts=DEFAULT_ATTEMPTS):
        await self.req_with_resp(msg_type, Acknowledgement, payload, timeout_secs, max_attempts)

    # Usually used for Get messages, or for state confirmation after Set (hence the optional payload)
    async def req_with_resp(self, msg_type, response_type, payload={}, timeout_secs=DEFAULT_TIMEOUT, max_attempts=DEFAULT_ATTEMPTS):
        # Need to put error checking here for aguments
        if type(response_type) != type([]):
            response_type = [response_type]
        success = False
        device_response = None
        socket_id = self.initialize_socket(timeout_secs)
        sock = self.socket_table[socket_id]
        if len(response_type) == 1 and Acknowledgement in response_type:
            msg = msg_type(self.mac_addr, self.source_id, seq_num=0, payload=payload, ack_requested=True, response_requested=False)
        else:
            msg = msg_type(self.mac_addr, self.source_id, seq_num=0, payload=payload, ack_requested=False, response_requested=True)
        response_seen = False
        attempts = 0
        while not response_seen and attempts < max_attempts:
            sent = False
            start_time = time()
            timedout = False
            while not response_seen and not timedout:
                if not sent:
                    if self.ip_addr:
                        sock.sendto(msg.packed_message, (self.ip_addr, self.port))
                    else:
                        for ip_addr in UDP_BROADCAST_IP_ADDRS:
                            sock.sendto(msg.packed_message, (ip_addr, self.port))
                    sent = True
                    if self.verbose:
                        print("SEND: " + str(msg))
                try:
                    data, (ip_addr, port) = sock.recvfrom(1024)
                    response = unpack_lifx_message(data)
                    if self.verbose:
                        print("RECV: " + str(response))
                    if type(response) in response_type:
                        if response.source_id == self.source_id and (response.target_addr == self.mac_addr or response.target_addr == BROADCAST_MAC):
                            response_seen = True
                            device_response = response
                            self.ip_addr = ip_addr
                            success = True
                except timeout:
                    pass
                elapsed_time = time() - start_time
                timedout = True if elapsed_time > timeout_secs else False
            attempts += 1
        if not success:
            await self.close_socket(socket_id)
            raise WorkflowException("WorkflowException: Did not receive {} from {} (Name: {}) in response to {}".format(str(response_type), str(self.mac_addr), str(self.label), str(msg_type)))
        else:
            await self.close_socket(socket_id)
        return device_response

        # Not currently implemented, although the LIFX LAN protocol supports this kind of workflow natively
    async def req_with_ack_resp(self, msg_type, response_type, payload, timeout_secs=DEFAULT_TIMEOUT, max_attempts=DEFAULT_ATTEMPTS):
        pass

    async def initialize_socket(self, timeout):
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        sock.settimeout(timeout)
        try:
            sock.bind(("", 0))  # allow OS to assign next available source port
            socket_id = self.socket_counter
            self.socket_table[socket_id] = sock
            self.socket_counter += 1
            return socket_id
        except Exception as err:
            raise WorkflowException("WorkflowException: error {} while trying to open socket".format(str(err)))

    async def close_socket(self, socket_id):
        sock = self.socket_table.pop(socket_id, None)
        if sock != None:
            sock.close()

def nanosec_to_hours(ns):
    return ns/(1000000000.0*60*60)