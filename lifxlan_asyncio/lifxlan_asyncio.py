import asyncio

from lifxlan import LifxLAN


class AsyncLifxLAN(LifxLAN):
    def __init__(self, *args, loop, **kwargs):
        self.loop = loop
        super().__init__(*args, **kwargs)

    async def get_devices(self):
        async for d in self.discover_devices():
            yield d

    async def discover_devices_sync(self):
        """ Iterate through discover_devices, updating internal lists """
        async for _ in self.discover_devices():
            pass

    async def get_lights(self):
        await self.discover_devices_sync()
        return self.lights

    # more of an internal helper function
    # forces a refresh of the internal list of available devices
    async def discover_devices(self):
        self.lights = []
        self.devices = []
        responses = await self.broadcast_with_resp(GetService, StateService,)
        async for r in responses:
            device = Device(r.target_addr, r.ip_addr, r.service, r.port, self.source_id, self.verbose)
            try:
                if device.is_light():
                    if device.supports_multizone():
                        device = MultiZoneLight(r.target_addr, r.ip_addr, r.service, r.port, self.source_id, self.verbose)
                    elif device.supports_chain():
                        device = TileChain(r.target_addr, r.ip_addr, r.service, r.port, self.source_id, self.verbose)
                    else:
                        device = Light(r.target_addr, r.ip_addr, r.service, r.port, self.source_id, self.verbose)
                    self.lights.append(device)
                    yield device
            except WorkflowException:
                # cheating -- it just so happens that all LIFX devices are lights right now
                device = Light(r.target_addr, r.ip_addr, r.service, r.port, self.source_id, self.verbose)
                self.lights.append(device)
                yield device
        self.devices.append(device)

    async def get_multizone_lights(self):
        multizone_lights = []
        all_lights = await self.get_lights()
        for l in all_lights:
            if l.supports_multizone():
                multizone_lights.append(l)
        return multizone_lights

    async def get_infrared_lights(self):
        infrared_lights = []
        all_lights = await self.get_lights()
        for l in all_lights:
            if l.supports_infrared():
                infrared_lights.append(l)
        return infrared_lights

    async def get_color_lights(self):
        color_lights = []
        all_lights = await self.get_lights()
        for l in all_lights:
            if l.supports_color():
                color_lights.append(l)
        return color_lights

    async def get_tilechain_lights(self):
        chain_lights = []
        all_lights = await self.get_lights()
        for l in all_lights:
            if l.supports_chain():
                chain_lights.append(l)
        return chain_lights

    async def get_device_by_name(self, name):
        device = None
        all_devices = self.get_devices()
        async for d in all_devices:
            if await d.get_label() == name:
                device = d
        if device == None:               # didn't find it?
            await self.discover_devices_sync()      # update list in case it is out of date
            all_devices = self.get_devices()
            async for d in all_devices:            # and try again
                if d.get_label() == name:
                    device = d
        return device

        # takes in list of strings, returns Group of devices
    async def get_devices_by_name(self, names):
        devices = []
        all_devices = self.get_devices()
        async for d in all_devices:
            if d.get_label() in names:
                devices.append(d)
        if len(devices) != len(names):  # didn't find everything?
            await self.discover_devices_sync()     # update list in case it is out of date
            all_devices = self.get_devices()
            async for d in all_devices:       # and try again
                if d.get_label() in names:
                    devices.append(d)
        return Group(devices)

    async def get_devices_by_group(self, group):
        devices = []
        all_devices = self.get_devices()
        async for d in all_devices:
            if d.get_group() == group:
                devices.append(d)
        return Group(devices)

    async def get_devices_by_location(self, location):
        devices = []
        all_devices = self.get_devices()
        async for d in all_devices:
            if d.get_location() == location:
                devices.append(d)
        return Group(devices)

        # returns dict of Light: power_level pairs
    async def get_power_all_lights(self):
        responses = await self.broadcast_with_resp(LightGetPower, LightStatePower)
        power_states = {}
        if self.lights == None:
            await self.discover_devices_sync()
        for light in self.lights:
            for response in responses:
                if light.mac_addr == response.target_addr:
                    power_states[light] = response.power_level
        return power_states

    async def set_power_all_lights(self, power_level, duration=0, rapid=False):
        on = [True, 1, "on", 65535]
        off = [False, 0, "off"]
        try:
            if power_level in on and not rapid:
                await self.broadcast_with_ack(LightSetPower, {"power_level": 65535, "duration": duration})
            elif power_level in on and rapid:
                await self.broadcast_fire_and_forget(LightSetPower, {"power_level": 65535, "duration": duration}, num_repeats=1)
            elif power_level in off and not rapid:
                await self.broadcast_with_ack(LightSetPower, {"power_level": 0, "duration": duration})
            elif power_level in off and rapid:
                await self.broadcast_fire_and_forget(LightSetPower, {"power_level": 0, "duration": duration}, num_repeats=1)
            else:
                raise InvalidParameterException("{} is not a valid power level.".format(power_level))
        except WorkflowException as e:
            raise

    async def get_color_all_lights(self):
        responses = await self.broadcast_with_resp(LightGet, LightState)
        colors = {}
        if self.lights == None:
            await self.discover_devices_sync()
        for light in self.lights:
            for response in responses:
                if light.mac_addr == response.target_addr:
                    colors[light] = response.color
        return colors

    async def set_color_all_lights(self, color, duration=0, rapid=False):
        if len(color) == 4:
            try:
                if rapid:
                    await self.broadcast_fire_and_forget(LightSetColor, {"color": color, "duration": duration}, num_repeats=1)
                else:
                    await self.broadcast_with_ack(LightSetColor, {"color": color, "duration": duration})
            except WorkflowException as e:
                raise
        else:
            raise InvalidParameterException("{} is not a valid color.".format(color))

    async def set_waveform_all_lights(self, is_transient, color, period, cycles, duty_cycle, waveform, rapid=False):
        if len(color) == 4:
            try:
                if rapid:
                    await self.broadcast_fire_and_forget(LightSetWaveform, {"transient": is_transient, "color": color, "period": period, "cycles": cycles, "duty_cycle": duty_cycle, "waveform": waveform}, num_repeats=1)
                else:
                    await self.broadcast_with_ack(LightSetWaveform, {"transient": is_transient, "color": color, "period": period, "cycles": cycles, "duty_cycle": duty_cycle, "waveform": waveform})
            except WorkflowException as e:
                raise
        else:
            raise InvalidParameterException("{} is not a valid color.".format(color))

    async def broadcast_fire_and_forget(self, msg_type, payload={}, timeout_secs=DEFAULT_TIMEOUT, num_repeats=DEFAULT_ATTEMPTS):
        self.initialize_socket(timeout_secs)
        msg = msg_type(BROADCAST_MAC, self.source_id, seq_num=0, payload=payload, ack_requested=False, response_requested=False)
        sent_msg_count = 0
        sleep_interval = 0.05 if num_repeats > 20 else 0
        while(sent_msg_count < num_repeats):
            for ip_addr in UDP_BROADCAST_IP_ADDRS:
                await self.sock.sendto(msg.packed_message, (ip_addr, UDP_BROADCAST_PORT))
            if self.verbose:
                print("SEND: " + str(msg))
            sent_msg_count += 1
            asyncio.sleep(sleep_interval) # Max num of messages device can handle is 20 per second.
        self.close_socket()

    async def broadcast_with_resp(self, msg_type, response_type, payload={}, timeout_secs=DEFAULT_TIMEOUT, max_attempts=DEFAULT_ATTEMPTS):
        self.initialize_socket(timeout_secs)
        if response_type == Acknowledgement:
            msg = msg_type(BROADCAST_MAC, self.source_id, seq_num=0, payload=payload, ack_requested=True, response_requested=False)
        else:
            msg = msg_type(BROADCAST_MAC, self.source_id, seq_num=0, payload=payload, ack_requested=False, response_requested=True)
        responses = []
        addr_seen = []
        num_devices_seen = 0
        attempts = 0
        while (self.num_devices == None or num_devices_seen < self.num_devices) and attempts < max_attempts:
            sent = False
            start_time = time()
            timedout = False
            while (self.num_devices == None or num_devices_seen < self.num_devices) and not timedout:
                if not sent:
                    for ip_addr in UDP_BROADCAST_IP_ADDRS:
                        self.sock.sendto(msg.packed_message, (ip_addr, UDP_BROADCAST_PORT))
                    sent = True
                    if self.verbose:
                        print("SEND: " + str(msg))
                try:
                    data, (ip_addr, port) = self.sock.recvfrom(1024)
                    response = unpack_lifx_message(data)
                    response.ip_addr = ip_addr
                    if self.verbose:
                        print("RECV: " + str(response))
                    if type(response) == response_type and response.source_id == self.source_id:
                        if response.target_addr not in addr_seen and response.target_addr != BROADCAST_MAC:
                            addr_seen.append(response.target_addr)
                            num_devices_seen += 1
                            responses.append(response)
                except timeout:
                    pass
                elapsed_time = time() - start_time
                timedout = True if elapsed_time > timeout_secs else False
            attempts += 1
        self.close_socket()
        return responses

    async def broadcast_with_ack(self, msg_type, payload={}, timeout_secs=DEFAULT_TIMEOUT+0.5, max_attempts=DEFAULT_ATTEMPTS):
        await self.broadcast_with_resp(msg_type, Acknowledgement, payload, timeout_secs, max_attempts)

        # Not currently implemented, although the LIFX LAN protocol supports this kind of workflow natively
    async def broadcast_with_ack_resp(self, msg_type, response_type, payload={}, timeout_secs=DEFAULT_TIMEOUT+0.5, max_attempts=DEFAULT_ATTEMPTS):
        pass

    def initialize_socket(self, timeout):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.sock.settimeout(timeout)
        try:
            self.sock.bind(("", 0))  # allow OS to assign next available source port
        except Exception as err:
            raise WorkflowException("WorkflowException: error {} while trying to open socket".format(str(err)))

    def close_socket(self):
        self.sock.close()


def test():
    pass


if __name__ == "__main__":
    test()
