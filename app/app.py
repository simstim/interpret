#!/usr/bin/env python3

import subprocess as sub

from time import time
from flask import Flask, request, jsonify

from process import process_boxer

# Parameters

# Nonmerge constraints to introduce:
# - samepred: Arguments of a predicate cannot be merged.
# - sameid: arguments of predicates with the same ID cannot be merged.
# - freqpred: Arguments of frequent predicates cannot be merged.
nonmerge = set(['sameid', 'freqpred'])


commands = {'tokenize':
              ['/interpret/ext/candc/bin/t',
               '--stdin'],
            'candc':
              ['/interpret/ext/candc/bin/soap_client',
               '--url', 'localhost:8888'],
            'boxer':
              ['/interpret/ext/candc/bin/boxer',
               '--stdin',
               '--semantics', 'tacitus',
               '--resolve', 'true'],
            'henry':
              []}


def run_commands(cmds, data):
    for cmd in cmds:
        try:
            p = sub.run(commands[cmd], input=data, stdout=sub.PIPE,
                        stderr=sub.PIPE)
            data = p.stdout
        except Exception as e:
            return None, 'Exception communicating with ' + cmd + '\n' + str(e)
    return data.decode(), None


app = Flask(__name__)

@app.route('/parse', methods=['POST'])
def parse():
    data = request.get_json(force=True)['s'].encode() + b'\n'
    out, err = run_commands(['tokenize', 'candc', 'boxer'], data)
    if err:
        return jsonify({'error': err})
    return jsonify({'parse': process_boxer(out, nonmerge)})


@app.route('/interpret', methods=['POST'])
def interpret():
    data = request.get_json(force=True)['s'].encode() + b'\n'

    out, err = run_commands(['tokenize', 'candc', 'boxer'], data)
    if err:
        return jsonify({'error': err})

    parse = process_boxer(out, nonmerge)

    data = parse.encode() + b'\n'
    out, err = run_commands(['henry'], data)
    if err:
        return jsonify({'parse': parse,
                        'error': err})

    return jsonify({'parse': parse,
                    'interpret': out})


if __name__ == '__main__':
    app.run(host='0.0.0.0')
