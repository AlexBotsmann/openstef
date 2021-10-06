# SPDX-FileCopyrightText: 2017-2021 Alliander N.V. <korte.termijn.prognoses@alliander.com> # noqa E501>
#
# SPDX-License-Identifier: MPL-2.0
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

import joblib
import mlflow
import pytz
import structlog
from mlflow.tracking import MlflowClient
from sklearn.base import RegressorMixin

from openstf.metrics.reporter import Report
from openstf_dbc.services.prediction_job import PredictionJobDataClass

MODEL_FILENAME = "model.joblib"
FOLDER_DATETIME_FORMAT = "%Y%m%d%H%M%S"
MODEL_ID_SEP = "-"


class AbstractSerializer(ABC):
    def __init__(self, trained_models_folder: Union[Path, str]) -> None:
        """

        Returns:
            object:
        """
        self.mlflow_folder = os.path.join(trained_models_folder, "mlruns")
        self.logger = structlog.get_logger(self.__class__.__name__)
        self.trained_models_folder = trained_models_folder

    @abstractmethod
    def save_model(self, model: RegressorMixin) -> None:
        """Persists trained sklearn compatible model

        Args:
            model: Trained sklearn compatible model object
        """
        self.logger.error("This is an abstract method!")

    @abstractmethod
    def load_model(self) -> RegressorMixin:
        """Loads model that has been trained earlier

        Returns: Trained sklearn compatible model object

        """
        self.logger.error("This is an abstract method!")


class PersistentStorageSerializer(AbstractSerializer):
    def save_model_old(
            self,
            model: RegressorMixin,
            pid: Optional[Union[int, str]] = None,
            model_id: Optional[str] = None,
    ) -> str:
        """Save sklearn compatible model to persistent storage.

            Either a pid or a model_id should be given. If a pid is given the model_id
            will be generated.

        Args:
            model: Trained sklearn compatible model object.
            pid: Prediction job id. Defaults to None.
            model_id: Model id. Defaults to None.

        Returns:
            str: Model id of the saved model.
        """

        if pid is None and model_id is None:
            raise ValueError("Need to supply either a pid or a model_id")

        if pid is not None and model_id is not None:
            raise ValueError("Cannot supply both a pid and a model_id")

        if pid is not None:
            model_id = self.generate_model_id(pid)

        model_folder = self.convert_model_id_into_model_folder(model_id)

        # Create save path if necessary
        model_folder.mkdir(parents=True, exist_ok=True)

        model_path = model_folder / MODEL_FILENAME

        # Save model
        self.save_model_to_path(model_path, model)
        self.logger.info(f"Saved model to {model_path}")

        return model_id

    def save_model(
            self,
            model: RegressorMixin,
            pj: Union[dict, PredictionJobDataClass],
            report:  Report,
    ):
        """Save sklearn compatible model to persistent storage with MLflow.

                Either a pid or a model_id should be given. If a pid is given the model_id
                will be generated.

            Args:
                model: Trained sklearn compatible model object.
                pj: Prediction job.
                report: Report object.

        """
        model_type = pj["model"]
        pid = pj['id']
        mlflow.set_tracking_uri(self.mlflow_folder)
        client = MlflowClient()
        mlflow.set_experiment(str(pid))
        experiment_id = client.get_experiment_by_name(str(pid)).experiment_id
        # return the latest run of the model
        pref_run = mlflow.search_runs(experiment_id, filter_string=f"tag.mlflow.runName = '{pj['model']}'",
                                      max_results=1, )
        try:
            pref_run_id = str(pref_run["run_id"][0])
        except KeyError:
            self.logger.info("No previous model found in MLflow")
            pref_run_id = None
        with mlflow.start_run(run_name=model_type):
            mlflow.set_tag("phase", "training")
            mlflow.set_tag("Previous_version_id", pref_run_id)
            mlflow.set_tag("model_type", model_type)
            mlflow.set_tag("prediction_job", pid)
            mlflow.log_metrics(report.metrics)
            mlflow.log_params(model.get_params())
            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="model",
                signature=report.signature,
            )
            mlflow.log_figure(report.feature_importance_figure,
                              f"{pid}_{model_type}_feature_importance.png")
            try:
                mlflow.log_figure(report.data_series_figures,
                                  f"{pid}_{model_type}_data_series.png")
            except Exception:
                self.logger.warning("Couldn't log data series figure")

    def load_model(self, pid: Optional[Union[int, str]] = None, model_id: Optional[str] = None) -> RegressorMixin:
        """Load sklearn compatible model from persistent storage.

                    Either a pid or a model_id should be given. If a pid is given the most
                    recent model for that pid will be loaded.

                Args:
                    pid (Optional[Union[int, str]], optional): Prediction job id. Defaults to None.
                    model_id (Optional[str], optional): Model id. Defaults to None. Used when MLflow didn't work.

                Raises:
                    AttributeError: when there is no experiment with pid in MLflow
                    KeyError: when there is no model in MLflow

                Returns:
                    RegressorMixin: Loaded model
                """
        try:
            client = MlflowClient()
            experiment_id = client.get_experiment_by_name(str(pid)).experiment_id
            # return the latest run of the model
            latest_run = mlflow.search_runs(experiment_id,
                                            max_results=1,
                                            ).iloc[0]
            loaded_model = mlflow.sklearn.load_model(latest_run.artifact_uri)
            # Add model age to model object
            loaded_model.age = self._determine_model_age_from_MLflow_run(latest_run)
            loaded_model.path = os.path.join(latest_run.artifact_uri, "model")
            self.logger.info("Model successfully loaded with MLflow")
            return loaded_model
        # AttributeError will occur when there is no experiment with pid in MLflow
        except AttributeError:
            return self.load_model_no_mlflow(pid, model_id)
        # KeyError will occur when there is no model in MLflow
        except KeyError:
            return self.load_model_no_mlflow(pid, model_id)

    def load_model_no_mlflow(
            self, pid: Optional[Union[int, str]] = None, model_id: Optional[str] = None
    ) -> RegressorMixin:
        """Load sklearn compatible model from persistent storage.

            Either a pid or a model_id should be given. If a pid is given the most
            recent model for that pid will be loaded.

        Args:
            pid (Optional[Union[int, str]], optional): Prediction job id. Defaults to None.
            model_id (Optional[str], optional): Model id. Defaults to None.

        Raises:
            ValueError: When both or none of pid and model_id are given.
            FileNotFoundError: When the model does not exist

        Returns:
            RegressorMixin: Loaded model
        """
        self.logger.warning("Couldn't load with MLflow, trying another way", pid=pid)
        if pid is None and model_id is None:
            raise ValueError("Need to supply either a pid or a model_id")

        if pid is not None and model_id is not None:
            raise ValueError("Cannot supply both a pid and a model_id")

        if pid is not None:
            model_path = self.find_most_recent_model_path(pid)
        elif model_id is not None:
            model_path = self.convert_model_id_into_model_path(model_id)

        if model_path is None:
            msg = f"No (most recent) model found"
            self.logger.error(msg)
            raise FileNotFoundError(msg)

        if model_path.is_file() is False:
            msg = f"model_path is not a file ({model_path})"
            self.logger.error(msg)
            raise FileNotFoundError(msg)

        return self.load_model_from_path(model_path)

    def save_model_to_path(self, model_path, model):
        joblib.dump(model, model_path)

    def load_model_from_path(self, model_path):
        # Load most recent model from disk
        try:
            self.logger.debug(f"Trying to load model from: {model_path}")
            loaded_model = joblib.load(model_path)
        except Exception as e:
            self.logger.error("Could not load most recent model!", exception=str(e))
            raise FileNotFoundError("Could not load model from the model file!")

        # exctract model age
        model_age_in_days = float("inf")  # In case no model is loaded,
        # we still need to provide an age
        if loaded_model is not None:
            model_age_in_days = self._determine_model_age_from_path(model_path)

        # Add model age to model object
        loaded_model.age = model_age_in_days
        loaded_model.path = model_path

        return loaded_model

    def determine_model_age_from_pid(self, pid: int) -> float:
        """Determine model age in days of most recent model for a given pid.
        If no previous model is found, float(Inf) is returned

        Args:
            pid: int

        Returns:
            float: model age in days"""
        model_path = self.find_most_recent_model_path(pid)
        if model_path is not None:
            model_age_days = self._determine_model_age_from_path(model_path)
        else:
            model_age_days = float("Inf")
        return model_age_days

    def _determine_model_age_from_path(self, model_path: Path) -> float:
        """Determines how many days ago a model is trained base on the folder name.

        Args:
            model_location: pathlib.Path: Path to the model folder

        Returns: Number of days since training of the model

        """

        # Location is of this format: TRAINED_MODELS_FOLDER/<pid>/<YYYYMMDDHHMMSS>/
        datetime_string = model_path.parent.name

        # Convert string to datetime object
        try:
            model_datetime = datetime.strptime(datetime_string, FOLDER_DATETIME_FORMAT)
        except Exception as e:
            self.logger.warning(
                "Could not parse model folder name to determine model age. Returning infinite age!",
                exception=e,
                folder_name=datetime_string,
            )
            return float("inf")  # Return fallback age

        # Get time difference between now and training in days
        model_age_days = (datetime.utcnow() - model_datetime).days

        return model_age_days

    def _determine_model_age_from_MLflow_run(self, run):

        model_datetime = run.end_time.to_pydatetime()
        model_datetime = model_datetime.replace(tzinfo=None)
        model_age_days = (datetime.utcnow() - model_datetime).days

        return model_age_days


    def find_model_folders(
            self, pid: Union[int, str], ascending: Optional[bool] = False
    ) -> List[Path]:
        pid_model_folder = Path(self.trained_models_folder) / f"{pid}"

        # Declare empty list to append folder names
        model_folders = []

        if pid_model_folder.is_dir() is False:
            return model_folders

        for folder in pid_model_folder.iterdir():
            # Skip files, we are looking for folders
            if folder.is_dir() is False:
                continue
            # model folders should start with a 2 (date starts with 2000s)
            if folder.name.startswith("2") is False:
                continue
            # the model folder is only valid when there is a valid model file
            if (folder / MODEL_FILENAME).is_file() is False:
                continue
            model_folders.append(folder)

        model_folders = sorted(model_folders, reverse=not ascending)

        return model_folders

    def find_model_paths(
            self,
            pid: Union[int, str],
            limit: Optional[int] = 1,
            ascending: Optional[bool] = False,
    ) -> List[Path]:
        model_paths = [
            f / MODEL_FILENAME for f in self.find_model_folders(pid, ascending)
        ]

        model_paths = model_paths[:limit]

        return model_paths

    def find_most_recent_model_folder(self, pid: Union[int, str]) -> Union[Path, None]:
        """Find the model recent model folder.

            Iterate over the directories in the 'pid' model folder (the top level model
            folder for a specific pid) and find the
            <trained_models_folder>/<pid>/<datetime>

        Args:
            pid (Union[int, str]): Prediction job id.

        Returns:
            Union[pathlib.Path, None]: Path to the most recent model file or None if not
                found.
        """

        model_folders = self.find_model_folders(pid, ascending=False)

        if len(model_folders) == 0:
            return None

        # return the first model folder (ascending order)
        return model_folders[0]

    def find_most_recent_model_path(self, pid: Union[int, str]):
        model_folder = self.find_most_recent_model_folder(pid)
        if model_folder is None:
            return None
        return self.find_most_recent_model_folder(pid) / MODEL_FILENAME

    def convert_model_id_into_model_folder(self, model_id: str):
        """Convert a trained model id into a model folder.

            The model_id should use the following format:
                "<prediction_job_id>/<datetime>"

        Args:
            trained_model_id ([type]): [description]
        """
        base_path = self.trained_models_folder

        prediction_job_id, model_datetime = model_id.split(MODEL_ID_SEP)

        return Path(base_path) / prediction_job_id / model_datetime

    def convert_model_id_into_model_path(self, model_id):
        return self.convert_model_id_into_model_folder(model_id) / MODEL_FILENAME

    def generate_model_id(self, pid: Union[int, str]):
        now = datetime.now(pytz.utc).strftime(FOLDER_DATETIME_FORMAT)
        model_id = f"{pid}{MODEL_ID_SEP}{now}"
        return model_id