#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import base64
import logging
import sys

import requests

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 10002

logger = logging.getLogger("hr.ttserver.client")


class TTSResponse(object):
    def __init__(self):
        self.response = None
        self.params = {}

    def get_duration(self):
        if self.response:
            return self.response.get("duration", 0)
        return 0

    def write(self, wavfile):
        if self.response:
            data = self.response["data"]
            data = base64.b64decode(data)
            try:
                with open(wavfile, "wb") as f:
                    f.write(data)
                logger.info("Write to file {}".format(wavfile))
                return True
            except Exception as ex:
                logger.error(ex)
                f = None
            finally:
                if f:
                    f.close()
        else:
            logger.error("No data to write")
        return False

    def __repr__(self):
        return "<TTSResponse params {}, duration {}>".format(
            self.params, self.get_duration()
        )


class Client(object):

    VERSION = "v1.0"

    def __init__(self, host=None, port=None, format="wav"):
        self.host = host or DEFAULT_HOST
        self.port = port or DEFAULT_PORT
        self.format = format
        self.root_url = "http://{}:{}/{}".format(self.host, self.port, Client.VERSION)

    def tts(self, text, **kwargs):
        params = {
            "text": text,
            "format": self.format,
        }
        params.update(kwargs)
        timeout = kwargs.get("timeout")
        result = TTSResponse()
        try:
            r = requests.get(
                "{}/tts".format(self.root_url), params=params, timeout=timeout
            )
            if r.status_code == 200:
                response = r.json().get("response")
                result.response = response
                result.params = params
            else:
                logger.error("Error code: {}".format(r.status_code))
        except Exception as ex:
            logger.error("TTS Error {}".format(ex))
        return result

    def asynctts(self, text, callback, **kwargs):
        pass

    def ping(self):
        try:
            r = requests.get("{}/ping".format(self.root_url))
            response = r.json().get("response")
            if response["message"] == "pong":
                return True
        except Exception:
            return False


def test():
    logging.basicConfig(level=logging.INFO)
    client = Client()
    result = client.tts("test", vendor="cereproc", voice="audrey")
    visemes = result.response["visemes"]
    print(visemes)
    result.write("test.wav")
    client.tts(
        "hello hello hello",
        vendor="cereproc",
        voice="katherine",
        emotion="sad",
        chunk_size=512,
        semitones=-2,
    ).write("happy.wav")
    client.tts(
        "hello hello hello", vendor="cereproc", voice="katherine", emotion="sad"
    ).write("sad.wav")
    client.tts(
        "hello hello hello", vendor="cereproc", voice="katherine", emotion="afraid"
    ).write("afraid.wav")
    client.tts(
        "hello hello hello", vendor="cereproc", voice="giles", emotion="happy_tensed"
    ).write("happy_tensed.wav")
    client.tts("hello", vendor="cereproc", voice="giles").write("hello2.wav")
    client.tts(
        'hi<mark name="mark_hello"/>hello', vendor="cereproc", voice="giles"
    ).write("hello3.wav")
    client.tts("你好", vendor="baidu", voice="male", spd=7, pit=9, aa=2).write(
        "hello5.wav"
    )


if __name__ == "__main__":
    import argparse
    import os

    logging.basicConfig(level=logging.INFO)
    # client = Client('dev.itu.head.hr-tools.io', '11002')
    parser = argparse.ArgumentParser(description="play tts")
    parser.add_argument("text")
    parser.add_argument("--vendor", default="acapela")
    parser.add_argument("--voice", default="Ella22k_HQ")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", default=DEFAULT_PORT)
    args = parser.parse_args()
    client = Client(args.host, args.port)
    client.tts(args.text, vendor=args.vendor, voice=args.voice).write("out.wav")
    os.system("aplay out.wav")
