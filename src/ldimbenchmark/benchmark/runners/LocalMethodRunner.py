import hashlib
import json
import logging
import os
import time
from typing import Literal, Union
import pandas as pd

import yaml
from ldimbenchmark.benchmark.runners.BaseMethodRunner import MethodRunner
from ldimbenchmark.classes import BenchmarkLeakageResult, LDIMMethodBase
from ldimbenchmark.datasets.classes import Dataset


class LocalMethodRunner(MethodRunner):
    """
    Runner for a local method.

    Leaves the dataset in prisitine state.
    """

    def __init__(
        self,
        detection_method: LDIMMethodBase,
        dataset: Union[Dataset, str],
        hyperparameters: dict = None,
        goal: Literal[
            "assessment", "detection", "identification", "localization", "control"
        ] = "detection",
        stage: Literal["train", "detect"] = "detect",
        method: Literal["offline", "online"] = "offline",
        debug=False,
        resultsFolder=None,
    ):
        """Initialize the LocalMethodRunner.

        Parameters
        ----------
        detection_method : LDIMMethodBase
            The LDIM method object.
        dataset : Union[Dataset, str]
            The dataset object or the path to the dataset.
        hyperparameters : dict, optional
            The hyperparameters for the LDIM object, by default None
        goal : Literal[
            "assessment", "detection", "identification", "localization", "control"
        ], optional
            The goal of the LDIM object, by default "detection"

        stage : Literal["train", "detect"], optional
            The stage of the LDIM object, by default "detect"

        method : Literal["offline", "online"], optional
            The method of the LDIM object, by default "offline"

        debug : bool, optional
            Whether to print debug information, by default False

        resultsFolder : None, optional
            The path to the results folder, by default None

        Raises
        ------
        TypeError
            If the dataset is not of type Dataset or str.
        ValueError
            If the dataset is not of type Dataset or str.
        """

        if hyperparameters is None:
            hyperparameters = {}

        for key in hyperparameters.keys():
            if key.startswith("_"):
                continue
            matching_params = [
                item
                for item in detection_method.metadata["hyperparameters"]
                if item.get("name") == key
            ]
            # Check if name of the supplied param matches with the ones that can be set
            if len(matching_params) == 0:
                raise Exception(
                    f"Hyperparameter {key} is not known to method {detection_method.name}, must be any of {[param['name'] for param in detection_method.metadata['hyperparameters']]}"
                )
            # Check if the type of the supplied param matches with the ones that can be set
            if not isinstance(hyperparameters[key], matching_params[0].get("type")):
                # Skip Float for now: https://github.com/pandas-dev/pandas/issues/50633
                if isinstance(hyperparameters[key], float):
                    pass
                else:
                    raise Exception(
                        f"Hyperparameter {key}: {hyperparameters[key]} is not of the correct type ({type(hyperparameters[key])}) for method {detection_method.name}, must be any of {[param['type'] for param in detection_method.metadata['hyperparameters'] if param['name'] == key]}"
                    )

        hyperparameter_hash = hashlib.md5(
            json.dumps(hyperparameters, sort_keys=True).encode("utf-8")
        ).hexdigest()

        self.id = f"{detection_method.name}_{dataset.id}_{hyperparameter_hash}"
        super().__init__(
            hyperparameters=hyperparameters,
            goal=goal,
            stage=stage,
            method=method,
            resultsFolder=(
                None if resultsFolder == None else os.path.join(resultsFolder, self.id)
            ),
            debug=debug,
        )
        logging.info("Loading Datasets")
        if type(dataset) is str:
            self.dataset = Dataset(dataset)
        else:
            dataset.loadData()
            dataset.loadBenchmarkData()
            self.dataset = dataset
        logging.info("Loading Datasets - FINISH")
        self.detection_method = detection_method

    def run(self):
        logging.info(f"Running {self.id} with params {self.hyperparameters}")
        if not self.resultsFolder and self.debug:
            raise Exception("Debug mode requires a results folder.")
        elif self.debug == True:
            additional_output_path = os.path.join(self.resultsFolder, "debug")
            os.makedirs(additional_output_path, exist_ok=True)
        else:
            additional_output_path = None

        # TODO: test compatibility (stages)
        self.detection_method.init_with_benchmark_params(
            additional_output_path=additional_output_path,
            hyperparameters=self.hyperparameters,
        )
        start = time.time()

        self.detection_method.train(self.dataset.getTrainingBenchmarkData())
        end = time.time()
        time_training = end - start
        logging.info(
            "> Training time for '"
            + self.detection_method.name
            + "': "
            + str(time_training)
        )

        start = time.time()
        detected_leaks = self.detection_method.detect_offline(
            self.dataset.getEvaluationBenchmarkData()
        )

        end = time.time()
        time_detection = end - start
        logging.info(
            "> Detection time for '"
            + self.detection_method.name
            + "': "
            + str(time_detection)
        )

        if self.resultsFolder:
            os.makedirs(self.resultsFolder, exist_ok=True)
            pd.DataFrame(
                detected_leaks,
                columns=list(BenchmarkLeakageResult.__annotations__.keys()),
            ).to_csv(
                os.path.join(self.resultsFolder, "detected_leaks.csv"),
                index=False,
                date_format="%Y-%m-%d %H:%M:%S",
            )
            pd.DataFrame(
                self.dataset.evaluation.leaks,
                columns=list(BenchmarkLeakageResult.__annotations__.keys()),
            ).to_csv(
                os.path.join(self.resultsFolder, "should_have_detected_leaks.csv"),
                index=False,
                date_format="%Y-%m-%d %H:%M:%S",
            )
            pd.DataFrame(
                [
                    {
                        "method": self.detection_method.name,
                        "dataset": self.dataset.name,
                        "dataset_id": self.dataset.id,
                        "hyperparameters": self.hyperparameters,
                        "goal": self.goal,
                        "stage": self.stages,
                        "train_time": time_training,
                        "detect_time": time_detection,
                    }
                ],
            ).to_csv(
                os.path.join(self.resultsFolder, "run_info.csv"),
                index=False,
                date_format="%Y-%m-%d %H:%M:%S",
            )

        return detected_leaks, self.dataset.evaluation.leaks