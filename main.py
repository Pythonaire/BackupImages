from application import init_app
import threading, logging, os, signal, sys

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
stop_event = threading.Event()
basedir = os.getcwd()
app = init_app(basedir)

def signal_handler(signal_received, frame):
    logging.info('Received shutdown signal: %s', signal_received)
    try:
        # Step 1: Signal threads to stop
        stop_event.set()
        logging.info("Thread stop signal sent.")
        # Step 2: Wait for threads to finish
        for thread in FlaskProcess:
            if thread.is_alive():
                thread.join()
        logging.info('Shutdown complete. Exiting.')
        sys.exit(0)       
    except Exception as e:
        logging.error("Error during shutdown: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    FlaskProcess = threading.Thread(target=app.run(debug=False, port=5005, host='0.0.0.0', ssl_context=('static/cert.pem', 'static/key.pem')))
    FlaskProcess.daemon = True
    FlaskProcess.start()
    signal.signal(signal.SIGINT, signal_handler)
