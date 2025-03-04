import logging
import os
import json

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

class JSONFile():
    def __init__(self, file):
        self.file = file

    def writeJson(self, data):
        with open(self.file, "w") as infile:
            json.dump(data, infile)
            infile.close()

    def readJson(self):
        try:
            with open(self.file, "r") as outfile:
                if os.path.getsize(self.file) != 0:
                    entry = json.load(outfile)
                    outfile.close()
                else:
                    logging.info(f"[Error] JSON File {self.file} is empty")
                    entry = None
        except IOError:
            logging.info("[Error] Couldn't read the JSON-File **")
            entry = None
        return entry