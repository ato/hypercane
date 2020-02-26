import logging

module_logger = logging.getLogger('hypercane.report.imagedata')

def get_managed_session(cache_storage):

    import os
    from urllib.parse import urlparse
    from pymongo import MongoClient
    from requests import Session
    from requests_cache import CachedSession
    from requests_cache.backends import MongoCache
    from mementoembed.sessions import ManagedSession
    from hypercane.version import __useragent__
    # from mementoembed.version import __useragent__

    proxies = None

    http_proxy = os.getenv('HTTP_PROXY')
    https_proxy = os.getenv('HTTPS_PROXY')

    if http_proxy is not None and https_proxy is not None:
        proxies = {
            'http': http_proxy,
            'https': https_proxy
        }
       
    o = urlparse(cache_storage)
    if o.scheme == "mongodb":
        # these requests-cache internals gymnastics are necessary 
        # because it will not create a database with the desired name otherwise
        dbname = o.path.replace('/', '')
        dbconn = MongoClient(cache_storage)
        session = ManagedSession(backend='mongodb')
        session.cache = MongoCache(connection=dbconn, db_name=dbname)
        session.proxies = proxies
        session.headers.update({'User-Agent': __useragent__})
        return session
    else:
        raise RuntimeError("Caching is required for image analysis.")

def generate_image_data(urimdata, cache_storage):

    from mementoembed.imageselection import generate_images_and_scores

    managed_session = get_managed_session(cache_storage)

    imagedata = {}

    module_logger.info("generating image data with MementoEmbed libraries...")

    for urim in urimdata:
        # TODO: cache this information?
        imagedata[urim] = generate_images_and_scores(urim, managed_session)

    return imagedata

def rank_images(imagedata):

    imageranking = []

    for urim in imagedata:
        module_logger.info("processing images for URI-M {}".format(urim))
        for image_urim in imagedata[urim]:

            module_logger.info("processing image at {}".format(image_urim))

            module_logger.info("image data: {}".format(imagedata[urim][image_urim]))

            if 'colorcount' in imagedata[urim][image_urim]:

                colorcount = float(imagedata[urim][image_urim]['colorcount'])
                ratio = float(imagedata[urim][image_urim]['ratio width/height'])
                noverN = float(imagedata[urim][image_urim]['n']) / float(imagedata[urim][image_urim]['N'])

                module_logger.info("report for image {}:\n  colorcount: {}\n  ratio width/height: {}\n  n/N: {}\n".format(
                    image_urim, colorcount, ratio, noverN
                ))

                imageranking.append(
                    ( 
                        colorcount,
                        1 / ratio,
                        noverN,
                        image_urim
                    )
                )

    return imageranking