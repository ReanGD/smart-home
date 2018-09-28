#!/bin/bash
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

if [ -d "$ROOT_DIR/protocols/yandex" ]; then
	protoc --proto_path=$ROOT_DIR/protocols/yandex         --python_out=$ROOT_DIR/protocols/yandex         $ROOT_DIR/protocols/yandex/*.proto
fi
if [ -d "$ROOT_DIR/protocols/home_assistant" ]; then
    protoc --proto_path=$ROOT_DIR/protocols/home_assistant --python_out=$ROOT_DIR/protocols/home_assistant $ROOT_DIR/protocols/home_assistant/*.proto
fi
if [ -d "$ROOT_DIR/test/test_proto" ]; then
    protoc --proto_path=$ROOT_DIR/test/test_proto          --python_out=$ROOT_DIR/test/test_proto          $ROOT_DIR/test/test_proto/*.proto
fi
