import logging

from pydantic import AnyHttpUrl

from tenint import Connector, Credential, Settings


class TestCredential(Credential):
    prefix: str = 'test'
    name: str = 'Test Credential'
    slug: str = 'test'
    api_key: str
    url: AnyHttpUrl = 'https://httpbin.org/get'


class AppSettings(Settings):
    is_bool: bool = True


log = logging.getLogger('test-connector')
connector = Connector(settings=AppSettings, credentials=[TestCredential])


@connector.job
def main(config: AppSettings):
    log.debug('This is a debug test')
    log.info('this is an info test')
    log.warning('this is a warning')
    log.error('this is an error')
    print('hello world')


if __name__ == '__main__':
    connector.app()
