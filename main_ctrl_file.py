# -*- coding: utf-8 -*-
"""
Created on Fri Jan  7 16:59:01 2022
Study control file: test main script before the development of a fully integrated GUI

@author: brile
"""
from equipment.sri_gc.gc_control import GC_Connector
from equipment.diode_laser.diode_control import Diode_Laser
from alicat import FlowController, FlowMeter
from experiment_control import Experiment
import numpy as np
import matplotlib.pyplot as plt
import os


def initialize_equipment():
    gc_connector = GC_Connector()
    laser_controller = Diode_Laser()
    MFC_A = FlowController(port='COM8', address='A')
    MFC_B = FlowController(port='COM9', address='B')
    MFC_C = FlowController(port='COM6', address='C')
    MFC_D = FlowMeter(port='COM7', address='D')
    # Heater will be added hear in future

    return (gc_connector, laser_controller, MFC_A, MFC_B, MFC_C, MFC_D)


if __name__ == "__main__":
    eqpt_list = initialize_equipment()
    MFC_A, MFC_B, MFC_C, MFC_D = eqpt_list[2:6] 
    for MFC in [MFC_A, MFC_B, MFC_C, MFC_D]:
        print(MFC.get())
    
    plt.close('all')
    main_fol = (r"C:\\Peak489Win10\\GCDATA\\"
                "20220120_CodeTest")
    os.makedirs(main_fol, exist_ok=True)
    Expt3 = Experiment(eqpt_list)
    Expt3.expt_type = 'flow_sweep'
    Expt3.temp = [273]
    Expt3.gas_type = ['N2', 'Ar', 'N2']
    Expt3.gas_comp = [[0.01, 1-0.06, 0.05]]
    Expt3.tot_flow = list(np.arange(10, 60, 10))
    Expt3.sample_name = '20211221_fakesample'
    Expt3.plot_sweep()
    Expt3.create_dirs(main_fol)
    Expt3.run_experiment()
    print('finished expt3')
