import logging
import csv


def setup_logging(logfile=None, loglevel="INFO"):
    """

    :param logfile:
    :param loglevel:
    :return:
    """

    loglevel = getattr(logging, loglevel)

    logger = logging.getLogger()
    logger.setLevel(loglevel)
    fmt = '%(asctime)s: %(levelname)s: %(filename)s: ' + \
          '%(funcName)s(): %(lineno)d: %(message)s'
    formatter = logging.Formatter(fmt)

    ch = logging.StreamHandler()
    ch.setLevel(loglevel)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if logfile is not None:
        fh = logging.FileHandler(filename=logfile)
        fh.setLevel(loglevel)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

def write_to_csv(data, filename):
    with open(filename, mode="w", encoding='utf-8') as w_file:
        names = ['title',
                 'company',
                 'country',
                 'location',
                 'salary',
                 'source',
                 'link',
                 'date',
                 'company_field',
                 'description',
                 'skills',
                 'job_type']
        file_writer = csv.DictWriter(w_file, delimiter=",",
                                     lineterminator="\r", fieldnames=names)
        file_writer.writeheader()
        file_writer.writerows(data)
    logging.info(f"Data written to file {filename}")
