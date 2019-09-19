from flask import jsonify


def general(msg):
    data = {
        'status' : '404',
        'body' : msg
    }
    return jsonify(data)