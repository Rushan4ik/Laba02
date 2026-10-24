
class StreamStatsError(Exception):
    # Базовое исключение пакета streamstats 
    pass
class UnsupportedFormatError(StreamStatsError):
    pass
    # Формат данных не поддерживается

class InvalidEventError(StreamStatsError):
    pass
    # Событие не прошло валидацию обязательных полей

class InvalidTimestampError(InvalidEventError):
    # Поле timestamp не парсится как ISO8601
    pass

class CliConfigError(StreamStatsError):
    pass
    # Неверная конфигурация Cli




