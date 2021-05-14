from enum import Enum

from pandas.tseries.holiday import AbstractHolidayCalendar, Holiday, sunday_to_monday, USMemorialDay, USLaborDay, \
    USThanksgivingDay


class Iso(Enum):
    MISO = 'miso'
    ISONE = 'isone'
    ERCOT = 'ercot'
    PJM = 'pjm'
    SPP = 'spp'
    AESO = 'aeso'
    NYISO = 'nyiso'
    CAISO = 'caiso'


class Block(Enum):
    _7x8 = '7x8'
    _5x16 = '5x16'
    _2x16 = '2x16'
    _7x24 = '7x24'
    _7x16 = '7x16'
    _1x1 = '1x1'
    Wrap = 'wrap'


class Frequency(Enum):
    Daily = 'daily'
    Monthly = 'monthly'
    Hourly = 'hourly'


class NERCHolidayCalendar(AbstractHolidayCalendar):
    """
    Creates a custom holiday calendar based on NERC schedule.
    Defined at https://www.nerc.com/comm/OC/RS%20Agendas%20Highlights%20and%20Minutes%20DL/Additional_Off-peak_Days.pdf
    """

    rules = [
        Holiday('NewYearsDay', month=1, day=1, observance=sunday_to_monday),
        USMemorialDay,
        Holiday('USIndependenceDay', month=7, day=4, observance=sunday_to_monday),
        USLaborDay,
        USThanksgivingDay,
        Holiday('Christmas', month=12, day=25, observance=sunday_to_monday)
    ]