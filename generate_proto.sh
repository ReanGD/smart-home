#!/bin/bash

protoc --proto_path=recognition/yandex_api --python_out=recognition/yandex_api recognition/yandex_api/*.proto
