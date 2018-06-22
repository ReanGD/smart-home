#!/bin/bash

protoc --proto_path=recognition/yandex_api --python_out=recognition/yandex_api recognition/yandex_api/*.proto
protoc --proto_path=protocols/home_assistant --python_out=protocols/home_assistant protocols/home_assistant/*.proto
