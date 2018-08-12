#!/bin/bash

protoc --proto_path=protocols/yandex         --python_out=protocols/yandex         protocols/yandex/*.proto
protoc --proto_path=protocols/home_assistant --python_out=protocols/home_assistant protocols/home_assistant/*.proto
protoc --proto_path=test/test_proto          --python_out=test/test_proto          test/test_proto/*.proto
