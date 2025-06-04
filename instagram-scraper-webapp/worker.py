import sys
from rq import Worker, Queue
from redis import Redis
from app import app, db # Assuming app and db are correctly imported from your Flask app
from rq.worker import SimpleWorker # Import SimpleWorker

# Set up Redis connection
redis_connection = Redis(host='localhost', port=6379, db=0)

if __name__ == '__main__':
    # Explicitly use SimpleWorker for compatibility on Windows
    worker_class_to_use = SimpleWorker

    # Create queues
    queues = [Queue('default', connection=redis_connection)]

    # Initialize the worker with NO special timeout arguments
    # This might allow it to start and run the job, but timeouts might not work as expected
    worker = worker_class_to_use(queues, connection=redis_connection)

    # To ensure tasks run within the Flask application context,
    # which is necessary for DB operations, current_user, etc.
    with app.app_context():
        print("Starting RQ worker, listening on queues: default (with Flask app context)...")
        worker.work()