# import os
# import logging
import app

app.simulation()
app.analyseV2()

# os.remove('temp/example.html')
# logging.basicConfig(
#     format='%(asctime)s <b>%(message)s</b><br>',
#     datefmt='%H:%M:%S',
#     filename='temp/example.html',
#     level=logging.DEBUG)
# logging.debug('This message should go to the log file')
# logging.info('So should this')
# logging.warning('And this, too')