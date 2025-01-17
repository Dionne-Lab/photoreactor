Welcome to Catalight!
========================================
.. meta::
    :description lang=en:
        A python toolbox for the automation of (photo)catalysis experiments and data analysis. Incorporates MFCs, heaters, light sources, detectors, etc.
    :keywords:
        Python, NKT, automation, catalysis, photocatalysis, chemistry, experiments, Stanford, Dionne, catalight

.. figure:: _static/images/catalight_header_g.png
    :width: 800

The purpose of this project is to share tools developed in the Dionne Lab at Stanford University for automating photocatalysis experiments and data analysis.

If your experimental setup looks anything like this:

.. figure:: _static/images/overview.png
    :width: 800

    D-Lab Hardware Configuration

You might be able to take advantage of our code base to accelerate your experiments!!

**Don't have this exact configuration?**
We've designed catalight with modularity in mind. We want to enable interested labs to develop their own equipment drivers to plug into catalight and reuse as much of our code as possible. Please visit the :doc:`Development Guide <developer_guide>` for more information about customizing catalight for your applications!

.. toctree::
   :maxdepth: 5
   :caption: Introduction:

   intro

.. toctree::
   :maxdepth: 5
   :caption: User Guide:

   user_guide

.. toctree::
   :maxdepth: 5
   :caption: Development Guide:

   developer_guide

.. toctree::
   :maxdepth: 5
   :caption: Examples:

   examples

.. toctree::
   :maxdepth: 5
   :caption: Documentation:

   api
   tests

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
