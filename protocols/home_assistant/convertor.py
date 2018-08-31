from .protocol_pb2 import SetDeviceState


_DEVICE_ACTION_TO_PROTOBUF = {
    'turn_off': SetDeviceState.TurnOff,
    'turn_on':  SetDeviceState.TurnOn,
}

_DEVICE_TO_PROTOBUF = {
    'light': SetDeviceState.Light,
    'tv':  SetDeviceState.TV,
    'music':  SetDeviceState.Music,
}

_PLACE_TO_PROTOBUF = {
    'hall': SetDeviceState.Hall,
    'kitchen':  SetDeviceState.Kitchen,
    'restroom':  SetDeviceState.Restroom,
    'bathroom': SetDeviceState.Bathroom,
    'livingroom':  SetDeviceState.Livingroom,
    'playroom':  SetDeviceState.Playroom,
    'all': SetDeviceState.All,
    'here': SetDeviceState.Here,
}

_CATEGORY_TO_PROTOBUF = {
    'device_action': _DEVICE_ACTION_TO_PROTOBUF,
    'device': _DEVICE_TO_PROTOBUF,
    'place': _PLACE_TO_PROTOBUF,
}

_TURN_ON_LIGHT_PLACE_TO_IDS = {
    SetDeviceState.Hall: ['switch.hall_switch_right_ceiling_light'],
    SetDeviceState.Kitchen: ['switch.kitchen_left_switch_ceiling_light'],
    SetDeviceState.Restroom: ['switch.restroom_switch_ceiling_light'],
    SetDeviceState.Bathroom: ['switch.bathroom_switch_right_ceiling_light'],
    SetDeviceState.Livingroom: ['switch.livingroom_switch_ceiling_light'],
    SetDeviceState.Playroom: ['switch.playroom_switch_ceiling_light'],
}

_TURN_ON_LIGHT_PLACE_TO_IDS[SetDeviceState.Here] = \
    _TURN_ON_LIGHT_PLACE_TO_IDS[SetDeviceState.Livingroom]

_TURN_ON_LIGHT_PLACE_TO_IDS[SetDeviceState.All] = (
    _TURN_ON_LIGHT_PLACE_TO_IDS[SetDeviceState.Hall] +
    _TURN_ON_LIGHT_PLACE_TO_IDS[SetDeviceState.Kitchen] +
    _TURN_ON_LIGHT_PLACE_TO_IDS[SetDeviceState.Restroom] +
    _TURN_ON_LIGHT_PLACE_TO_IDS[SetDeviceState.Bathroom] +
    _TURN_ON_LIGHT_PLACE_TO_IDS[SetDeviceState.Livingroom] +
    _TURN_ON_LIGHT_PLACE_TO_IDS[SetDeviceState.Playroom])

_TURN_OFF_LIGHT_PLACE_TO_IDS = {
    SetDeviceState.Hall: ['switch.hall_switch_right_ceiling_light'],
    SetDeviceState.Kitchen: ['switch.kitchen_left_switch_ceiling_light',
                             'switch.kitchen_right_switch_backlight'],
    SetDeviceState.Restroom: ['switch.restroom_switch_ceiling_light'],
    SetDeviceState.Bathroom: ['switch.bathroom_switch_right_ceiling_light',
                              'switch.bathroom_switch_left_additional_light'],
    SetDeviceState.Livingroom: ['switch.livingroom_switch_ceiling_light'],
    SetDeviceState.Playroom: ['switch.playroom_switch_ceiling_light'],
}

_TURN_OFF_LIGHT_PLACE_TO_IDS[SetDeviceState.Here] = \
    _TURN_OFF_LIGHT_PLACE_TO_IDS[SetDeviceState.Livingroom]

_TURN_OFF_LIGHT_PLACE_TO_IDS[SetDeviceState.All] = (
    _TURN_OFF_LIGHT_PLACE_TO_IDS[SetDeviceState.Hall] +
    _TURN_OFF_LIGHT_PLACE_TO_IDS[SetDeviceState.Kitchen] +
    _TURN_OFF_LIGHT_PLACE_TO_IDS[SetDeviceState.Restroom] +
    _TURN_OFF_LIGHT_PLACE_TO_IDS[SetDeviceState.Bathroom] +
    _TURN_OFF_LIGHT_PLACE_TO_IDS[SetDeviceState.Livingroom] +
    _TURN_OFF_LIGHT_PLACE_TO_IDS[SetDeviceState.Playroom])


def entity_to_protobuf(category: str, value: str) -> int:
    category_map = _CATEGORY_TO_PROTOBUF.get(category, None)
    if category_map is None:
        raise RuntimeError('Unknown category "{}"'.format(category))

    result = category_map.get(value, None)
    if result is None:
        raise RuntimeError('Unknown value "{}" in category "{}"'.format(value, category))

    return result


def protobuf_to_device_id(device: int, place: int, action: int):
    if device != SetDeviceState.Light:
        raise RuntimeError('Unsupported id: device={}, place={}, action={}'.format(
            device, place, action))

    if action == SetDeviceState.TurnOn:
        convert_map = _TURN_ON_LIGHT_PLACE_TO_IDS
    elif action == SetDeviceState.TurnOff:
        convert_map = _TURN_OFF_LIGHT_PLACE_TO_IDS
    else:
        raise RuntimeError('Unsupported id: device={}, place={}, action={}'.format(
            device, place, action))

    ids = convert_map.get(place, None)
    if ids is None:
        raise RuntimeError('Unsupported id: device={}, place={}, action={}'.format(
            device, place, action))

    return ids
