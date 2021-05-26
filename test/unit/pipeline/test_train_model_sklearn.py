# SPDX-FileCopyrightText: 2017-2021 Alliander N.V. <korte.termijn.prognoses@alliander.com> # noqa E501>
#
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime, timedelta
import unittest
from unittest.mock import MagicMock, patch
from test.utils import TestData
from test.utils import BaseTestCase

import pandas as pd

from openstf.pipeline.train_model_sklearn import (
    train_model_pipeline,
    split_data_train_validation_test,
)


# define constants

PJ = TestData.get_prediction_job(pid=307)
XGB_HYPER_PARAMS = {
    "subsample": 0.9,
    "min_child_weight": 4,
    "max_depth": 8,
    "gamma": 0.5,
    "colsample_bytree": 0.85,
    "eta": 0.1,
    "training_period_days": 90,
}


class TestTrainModel(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.pj = TestData.get_prediction_job(pid=307)
        datetime_start = datetime.utcnow() - timedelta(days=90)
        datetime_end = datetime.utcnow()
        self.data_table = TestData.load("input_data_train.pickle").head(8641)
        self.data = pd.DataFrame(
            index=pd.date_range(datetime_start, datetime_end, freq="15T")
        )

        self.train_input = TestData.load("reference_sets/307-train-data.csv")
        self.pj["feature_names"] = self.train_input.columns[
            1:
        ]  # first column is not a feature

    def test_split_data_train_validation_test(self):
        train_data, validation_data, test_data = split_data_train_validation_test(
            self.data, period_sampling=False
        )
        self.assertEqual(len(train_data), 7345)
        self.assertEqual(len(validation_data), 1297)
        self.assertEqual(len(test_data), 1)

    def test_split_data_train_validation_test_period(self):
        train_data, validation_data, test_data = split_data_train_validation_test(
            self.data, period_sampling=True
        )
        self.assertEqual(len(train_data), 7345)
        self.assertEqual(len(validation_data), 1296)
        self.assertEqual(len(test_data), 1)

    def test_train_pipeline_happy(self):
        """Test if happy flow of the train pipeline

        The input data should not contain features (e.g. T-7d),
        but it can/should include predictors (e.g. weather data)"""

        # Run the this should return a model and report
        with self.assertLogs() as captured:
            model, report = train_model_pipeline(
                pj=self.pj,
                input_data=self.train_input,
                # check_old_model_age=False,
                # compare_to_old=False,
            )
        # Check if a new model was stored based on logging
        assert captured.records[-1].getMessage() == "Fitted a new model, not yet stored"
        assert str(type(model)) == "<class 'xgboost.sklearn.XGBRegressor'>"
        assert str(report.__class__) == "<class 'openstf.metrics.reporter.Report'>"


if __name__ == "__main__":
    unittest.main()
