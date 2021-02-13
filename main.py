# coding=utf-8

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import logging
import redis
import json
import numpy
from scipy.stats import norm

# Тест отправки:
# curl -X POST -H "Content-Type: application/json" -d {'name':'db-server1','execute_times':'24'} http://127.0.0.1:8088

r = redis.StrictRedis(host='stand221.cc.naumen.ru', port=6379, db=10)


class S(BaseHTTPRequestHandler):
    def save_data(self, data):
        r.rpush('db:%s:execute_times' % data['name'], data['execute_times'])
        return

    def get_timeout(self, server_name):
        l_len = r.llen('db:%s:execute_times' % server_name)
        times = r.lrange('db:%s:execute_times' % server_name, 0, (l_len - 1))
        times_int = [int(item) for item in times]
        result = norm.fit_loc_scale(times_int)[0] + (3 * numpy.std(list(times_int)))
        print(result)
        return result

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        post_data = post_data.replace("'", "\"")
        post_data = json.loads(post_data)
        self.save_data(post_data)
        t_out = self.get_timeout(post_data['name'])
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data)

        self._set_response()
        self.wfile.write(t_out)


def run(server_class=HTTPServer, handler_class=S, port=8088):
    logging.basicConfig(level=logging.INFO)
    server_address = ('127.0.0.1', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')


if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
