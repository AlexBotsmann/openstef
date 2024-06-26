.. comment:
    SPDX-FileCopyrightText: 2017-2023 Contributors to the OpenSTEF project <korte.termijn.prognoses@alliander.com>
    SPDX-License-Identifier: MPL-2.0

.. _user_guides:

Керівництво користувача
=======================

TЦя сторінка містить інструкції та посилання на ресурси, які показують, як можна використовувати OpenSTEF.

Трубопроводи - функціональність високого рівня
----------------------------------------------
OpenSTEF розроблено на основі трубопроводів (див. :ref:`concepts <concepts>` для визначення). Трубопроводи пропонують простий спосіб навчання моделей, генерування прогнозів та оцінювання ефективності прогнозування.


Доступні наступні трубопроводи:

- :mod:`openstef.pipeline.train_model`
- :mod:`openstef.pipeline.create_forecast`
- :mod:`openstef.pipeline.optimize_hyperparameters`
- :mod:`openstef.pipeline.create_component_forecast`
- :mod:`openstef.pipeline.create_basecase_forecast`
- :mod:`openstef.pipeline.train_create_forecast_backtest`

Чудовий спосіб розпочати роботу та ознайомитися з трубопроводами OpenSTEF - це поглянути на
`this GitHub repository that contains an assortment of Jupyter notebook examples <https://github.com/OpenSTEF/openstef-offline-example>`_. Репозиторій
навіть містить приклади даних.

Ви можете запустити кожен приклад блокнота локально без будь-яких налаштувань, окрім `installation of the OpenSTEF package <https://pypi.org/project/openstef/>`_.

Ми рекомендуємо вам ознайомитися з усіма прикладами, але ось список, з якого ви можете почати:

- `How to train a model <https://github.com/OpenSTEF/openstef-offline-example/blob/master/examples/01.%20Train%20a%20model%20using%20high-level%20pipelines.ipynb>`_.
- `How to create a forecast <https://github.com/OpenSTEF/openstef-offline-example/blob/master/examples/04.%20Test_on_difficult_cases.ipynb>`_.
- `How evaluate the performance of model using a backtest  <https://github.com/OpenSTEF/openstef-offline-example/blob/master/examples/02.%20Evaluate%20performance%20using%20Backtest%20Pipeline.ipynb>`_.

Більш детальну інформацію про те, як використовувати та реалізовувати трубопроводи у робочому середовищі, включно з прикладами коду, можна знайти у розділі :ref:`pipeline_user_guide` цієї документації.


Розгортання як повноцінного додатку для прогнозування
----------------------------------------
Якщо ви хочете налаштувати повноцінну програму прогнозування, готову до використання в робочому середовищі з
внутрішнім сховищем даних і графічним інтерфейсом користувача, це
`GitHub repository contains a reference implementation <https://github.com/OpenSTEF/openstef-reference>`_  ви можете використовувати як відправну точку.
Цей приклад реалізації включає бази даних, користувацький інтерфейс та приклади даних.

Більше інформації про те, як може виглядати архітектура такого додатку, можна знайти :ref:`here <application-architecture>`.

.. include:: dashboard.rst
Скріншот операційної панелі, що показує ключові функціональні можливості OpenSTEF. Документацію до інформаційної панелі можна знайти `тут <https://raw.githack.com/OpenSTEF/.github/main/profile/html/openstef_dashboard_doc.html>`_.

Приклади блокнотів Jupyter
--------------------------
Блокноти Jupyter, що демонструють деякі з основних функціональних можливостей OpenSTEF, можна знайти за адресою: https://github.com/OpenSTEF/openstef-offline-example.
