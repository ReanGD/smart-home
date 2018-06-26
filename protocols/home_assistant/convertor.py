from .protocol_pb2 import SetDeviceState


_device_action_to_protobuf = {
    'turn_off': SetDeviceState.TurnOff,
    'turn_on':  SetDeviceState.TurnOn,
}

_device_to_protobuf = {
    'light': SetDeviceState.Light,
    'tv':  SetDeviceState.TV,
    'music':  SetDeviceState.Music,
}

_place_to_protobuf = {
    'hall': SetDeviceState.Hall,
    'kitchen':  SetDeviceState.Kitchen,
    'toilet':  SetDeviceState.Toilet,
    'bathroom': SetDeviceState.Bathroom,
    'livingroom':  SetDeviceState.Livingroom,
    'playroom':  SetDeviceState.Playroom,
    'all': SetDeviceState.All,
    'here': SetDeviceState.Here,
}

_category_to_protobuf = {
    'device_action': _device_action_to_protobuf,
    'device': _device_to_protobuf,
    'place': _place_to_protobuf,
}

_turn_on_light_place_to_ids = {
    SetDeviceState.Hall: ['switch.hall_switch_right_ceiling_light'],
    SetDeviceState.Kitchen: ['switch.kitchen_left_switch_ceiling_light'],
    SetDeviceState.Toilet: ['switch.toilet_switch_ceiling_light'],
    SetDeviceState.Bathroom: ['switch.bathroom_switch_right_ceiling_light'],
    SetDeviceState.Livingroom: ['switch.livingroom_switch_ceiling_light'],
    SetDeviceState.Playroom: ['switch.playroom_switch_ceiling_light'],
}

_turn_on_light_place_to_ids[SetDeviceState.Here] = \
    _turn_on_light_place_to_ids[SetDeviceState.Livingroom]

_turn_on_light_place_to_ids[SetDeviceState.All] = (
        _turn_on_light_place_to_ids[SetDeviceState.Hall] +
        _turn_on_light_place_to_ids[SetDeviceState.Kitchen] +
        _turn_on_light_place_to_ids[SetDeviceState.Toilet] +
        _turn_on_light_place_to_ids[SetDeviceState.Bathroom] +
        _turn_on_light_place_to_ids[SetDeviceState.Livingroom] +
        _turn_on_light_place_to_ids[SetDeviceState.Playroom])

_turn_off_light_place_to_ids = {
    SetDeviceState.Hall: ['switch.hall_switch_right_ceiling_light'],
    SetDeviceState.Kitchen: ['switch.kitchen_left_switch_ceiling_light',
                             'switch.kitchen_right_switch_backlight'],
    SetDeviceState.Toilet: ['switch.toilet_switch_ceiling_light'],
    SetDeviceState.Bathroom: ['switch.bathroom_switch_right_ceiling_light',
                              'switch.bathroom_switch_left_additional_light'],
    SetDeviceState.Livingroom: ['switch.livingroom_switch_ceiling_light'],
    SetDeviceState.Playroom: ['switch.playroom_switch_ceiling_light'],
}

_turn_off_light_place_to_ids[SetDeviceState.Here] = \
    _turn_off_light_place_to_ids[SetDeviceState.Livingroom]

_turn_off_light_place_to_ids[SetDeviceState.All] = (
        _turn_off_light_place_to_ids[SetDeviceState.Hall] +
        _turn_off_light_place_to_ids[SetDeviceState.Kitchen] +
        _turn_off_light_place_to_ids[SetDeviceState.Toilet] +
        _turn_off_light_place_to_ids[SetDeviceState.Bathroom] +
        _turn_off_light_place_to_ids[SetDeviceState.Livingroom] +
        _turn_off_light_place_to_ids[SetDeviceState.Playroom])


def entity_to_protobuf(category: str, value: str) -> int:
    category_map = _category_to_protobuf.get(category, None)
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
        convert_map = _turn_on_light_place_to_ids
    elif action == SetDeviceState.TurnOff:
        convert_map = _turn_off_light_place_to_ids
    else:
        raise RuntimeError('Unsupported id: device={}, place={}, action={}'.format(
            device, place, action))

    ids = convert_map.get(place, None)
    if ids is None:
        raise RuntimeError('Unsupported id: device={}, place={}, action={}'.format(
            device, place, action))

    return ids
