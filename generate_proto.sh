#!/bin/bash

protoc --proto_path=recognition/yandex_proto --python_out=recognition/yandex_proto recognition/yandex_proto/*.proto
