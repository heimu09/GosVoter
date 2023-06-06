import uuid
from os.path import splitext

def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return f'journalists_certificate/{filename}'
