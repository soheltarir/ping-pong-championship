#!/usr/bin/env bash
while IFS='' read -r line || [[ -n "$line" ]]; do
    IFS=',' read -a input_array <<< "$line"
    echo "Running ${input_array[1]} player process."
    python player_server.py ${input_array[0]} ${input_array[1]} ${input_array[2]} & > player_${input_array[1]}.log &
done < "$1"
