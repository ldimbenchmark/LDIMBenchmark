import logging
from typing import Dict, List
import numpy as np
from pandas import DataFrame
from ldimbenchmark.classes import BenchmarkData
from wntr.network import WaterNetworkModel
import pandas as pd


class SimpleBenchmarkData:
    """
    Representation of simplified Benchmark Dataset

    The main differences are:
    - sensors are not separated into single Time series, but are already aligned and in one single DataFrame

    This has the drawback that they are already resampled to the same time interval.
    """

    def __init__(
        self,
        pressures: DataFrame,
        demands: DataFrame,
        flows: DataFrame,
        levels: DataFrame,
        model: WaterNetworkModel,
        dmas: List[str],
    ):
        """
        Initialize the BenchmarkData object.
        """
        self.pressures = pressures
        """Pressures of the System."""
        self.demands = demands
        """Demands of the System."""
        self.flows = flows
        """Flows of the System."""
        self.levels = levels
        """Levels of the System."""
        self.model = model
        """Model of the System (INP)."""
        self.dmas = dmas
        """
        District Metered Areas
        Dictionary with names of the areas as key and list of WN nodes as value.
        """
        self.metadata = {}
        """Metadata of the System. e.g. Metering zones and included sensors."""


def resampleSensors(
    sensors: Dict[str, DataFrame], resample_frequency="1T"
) -> DataFrame:
    """
    Resample all sensors to the same time interval and concatenate them into one single DataFrame

    value_count: The number of values that should be in the resulting DataFrame, if the number of values in sensors is less than value_count,
    the DataFrame will be padded with NaNs
    """

    for sensor_name, sensor_data in sensors.items():
        new_data = sensor_data.resample(resample_frequency).mean()
        if len(new_data) > len(sensor_data):
            logging.warning(
                "Upsampling data, this might result in one off errors later on. Consider settings 'resample_frequency' to a bigger timeframe."
            )
        sensors[sensor_name] = new_data
    return sensors


def concatAndInterpolateSensors(
    sensors: Dict[str, DataFrame],
    should_have_value_count: int = None,
    resample_frequency="1T",
) -> DataFrame:
    """
    Concatenate all sensors to a single DataFrame and interpolate the missing values

    value_count: The number of values that should be in the resulting DataFrame, if the number of values in sensors is less than value_count,
    the DataFrame will be padded with NaNs
    """

    concatenated_sensors = []
    for sensor_name, sensor_data in sensors.items():
        if should_have_value_count is not None:
            # Making sure the DataFrame has the amount of values it should have
            logging.warning(f"SENSOR: {sensor_name}")
            logging.warning(f"MAX VALUES: {should_have_value_count}")
            missing_values_count = should_have_value_count - len(sensor_data)
            logging.warning(f"MISSING VALUES: {missing_values_count}")
            if missing_values_count > 0:
                missing_timedelta = (
                    pd.Timedelta(resample_frequency) * missing_values_count
                )

                missing_dates = pd.DataFrame(
                    index=pd.date_range(
                        sensor_data.iloc[-1].name,
                        sensor_data.iloc[-1].name + missing_timedelta,
                        freq=resample_frequency,
                    )
                )
                missing_dates[0] = np.NaN
                missing_dates.columns = sensor_data.columns
                missing_dates
                sensor_data = sensor_data.combine_first(missing_dates)

        concatenated_sensors.append(sensor_data)

    if len(concatenated_sensors) == 0:
        return pd.DataFrame()

    return pd.concat(
        concatenated_sensors,
        axis=1,
    ).interpolate(limit_direction="both")


def simplifyBenchmarkData(
    data: BenchmarkData, resample_frequency="1T", force_same_length=False
) -> SimpleBenchmarkData:
    """Convert multiple timeseries to one timeseries"""

    resampled_pressures = resampleSensors(data.pressures, resample_frequency)
    resampled_demands = resampleSensors(data.demands, resample_frequency)
    resampled_flows = resampleSensors(data.flows, resample_frequency)
    resampled_levels = resampleSensors(data.levels, resample_frequency)

    if force_same_length:
        max_values = 0
        for datasets in [
            resampled_pressures,
            resampled_demands,
            resampled_flows,
            resampled_levels,
        ]:
            for key in datasets.keys():
                max_values = max(max_values, len(datasets[key]))
    else:
        max_values = None

    return SimpleBenchmarkData(
        pressures=concatAndInterpolateSensors(
            resampled_pressures, max_values, resample_frequency
        ),
        demands=concatAndInterpolateSensors(
            resampled_demands, max_values, resample_frequency
        ),
        flows=concatAndInterpolateSensors(
            resampled_flows, max_values, resample_frequency
        ),
        levels=concatAndInterpolateSensors(
            resampled_levels, max_values, resample_frequency
        ),
        model=data.model,
        dmas=data.dmas,
    )
